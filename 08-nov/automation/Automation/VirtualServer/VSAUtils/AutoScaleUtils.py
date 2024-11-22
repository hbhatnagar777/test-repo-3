# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing operations relating to VSA auto-scale

classes defined:

    class:

             AutoScaleValidation              -  Class for performing auto scale validation

    Methods:

        start_backup_job()                    - Starts the backup job

        monitor_job()                         -  Monitors the backup job for completion

        _prepare_scale_param()                - Prepares a dictionary containing details of vm
                                                in a particular region

        calculate_agents_required()           -  Prepares dictionary contains agents required for each region

        _check_if_proxy_is_marked_for_power_off() - Checks if vm is marked for powered off

        _validate_proxy_status                -  Calculates inactivity time validates accordingly

        update_rpo                            - updates ro details

        post_backup_validation()              - performs post backup validations





"""
import math
import time
from enum import Enum
from cvpysdk.job import Job
from cvpysdk.virtualmachinepolicies import VirtualMachinePolicies
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils.VMHelpers.AzureVM import AzureVM
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName, hypervisor_type


class AutoScaleValidation:
    """ Base class for performing auto scale validation"""

    class ValidationState(Enum):
        """Enum Class for auto scale proxy status"""
        DB_POWER_OFF_PASSED = 1
        PROXY_POWER_OFF_PASSED = 2
        PROXY_DELETED = 3

    def __init__(self, auto_subclient, **kwargs):
        """Initialize AutoScaleValidation object"""
        self.auto_subclient = auto_subclient
        self.backup_job = None
        self.common_utils = CommonUtils(self.auto_subclient.auto_commcell.commcell)
        self.backup_job_monitor_complete = True
        self._auto_scale_policy_properties = None
        self._auto_scale_policy_region_info = {}
        self.data_throughput = 100
        self.rpo = 1440
        self.log = auto_subclient.log
        self.max_wait_period = kwargs.get('max_wait_period', 75)
        self.proxy_region_info = {}
        self.proxy_monitor = {}
        self.backup_job_monitor_complete = False
        self.is_tenant = False
        self.job_monitor_error_string = ""
        self.validator_error_string = ""

    @property
    def auto_scale_policy(self):
        """
        Gets auto scale policy properties
        """
        client_name = self.auto_subclient.auto_vsaclient.vsa_admin_client_name if self.is_tenant else self.auto_subclient.auto_vsaclient.vsa_client_name
        client_id = self.auto_subclient.auto_vsaclient.vsa_admin_client_id if self.is_tenant else self.auto_subclient.auto_vsaclient.vsa_client_id

        if not self._auto_scale_policy_properties:
            policy_name = f"{client_name}_{client_id}_AutoScaleProxyPolicy"
            self._auto_scale_policy_properties = VirtualMachinePolicies(
                self.auto_subclient.auto_commcell.commcell).get(policy_name).properties()
        return self._auto_scale_policy_properties

    @property
    def auto_scale_region_info(self):
        """
        Gets region specific details of auto scale policy
        """
        if not self._auto_scale_policy_region_info:
            region_specific_info = self.auto_scale_policy. \
                get('scaleOption').get('scaleOutParam') \
                .get('regionSpecificInfo')
            for region_info in region_specific_info:
                self._auto_scale_policy_region_info[region_info.pop('regionName')] = region_info
        return self._auto_scale_policy_region_info

    def update_rpo(self, backup_copy=False):
        """
        Updates rpo details
        Args:
            backup_copy (bool): Set ture if rpo needs to be updated for backup copy job
        """
        config_info = self.auto_subclient.get_auto_scale_config_info()
        self.rpo = int(config_info.get('Ida_AutoScaleConfigInfoResp', {}).get('@rpoInMin', 1440))
        self.data_throughput = int(config_info.
                                              get('Ida_AutoScaleConfigInfoResp', {}).
                                              get('@dataThroughputGBPerHour', 100))
        if backup_copy:
            self.rpo = int(config_info.get('Ida_AutoScaleConfigInfoResp', {}).
                           get('@backupCopyRpoInMin', 1440))

    def start_backup_job(self, backup_options):
        """
        Starts the backup on subclient

        Args:
            backup_options:         (object):   object of Backup Options class in options
                                                    helper contains all backup options
        """

        self.update_rpo(backup_options.backup_method != 'REGULAR')
        self.calculate_agents_required()

        backup_job = self.auto_subclient.subclient. \
            backup(backup_options.backup_type,
                   backup_options.run_incr_before_synth,
                   backup_options.incr_level,
                   backup_options.collect_metadata,
                   backup_options.advance_options)
        if backup_options.backup_method == 'REGULAR':
            self.log.info("Started  backup Job : %s", str(backup_job.job_id))
            self.backup_job = backup_job
        else:
            self.log.info("Started snap backup Job : %s", str(backup_job.job_id))
            if not backup_job.wait_for_completion():
                raise Exception("Failed to run backup with \
                error: {0}".format(backup_job.delay_reason))
            if "errors" in backup_job.status:
                raise Exception("Backup Job completed with one or more errors")
            self.log.info("Backup Job %s completed successfully"
                          "Checking if Job type is Expected for job ",
                          str(backup_job.job_id))
            time.sleep(30)
            backup_copy_job_id = self.common_utils.get_backup_copy_job_id(backup_job.job_id)
            backup_copy_job = Job(self.auto_subclient.auto_commcell.commcell, backup_copy_job_id)
            self.log.info("Backup Copy Job {0} :".format(backup_copy_job_id))
            self.backup_job = backup_copy_job

    def monitor_job(self, **kwargs):
        """
        Monitors the backup job for completion

        """
        try:
            if kwargs.get('suspend_and_resume', False):
                wait_count = 5
                while wait_count > 0:
                    if len(self.auto_subclient.auto_commcell.get_vm_management_jobs(self.backup_job.job_id)) > 0:
                        break
                    wait_count -= 1
                    time.sleep(180)
                else:
                    raise Exception("No VMManagment job created for suspend and resume case")
                self.backup_job.pause(True)
                self.log.info(f"Backup Job {self.backup_job.job_id} paused")
                self.wait_for_vm_management_child_jobs_to_complete()
                self.log.info("All VMManagment jobs completed. resuming the backup job.")
                self.backup_job.resume(True)

            if not self.backup_job.wait_for_completion():
                self.backup_job_monitor_complete = True
                raise Exception("Failed to run backup with error: {0}"
                                .format(self.backup_job.delay_reason))
            self.log.info("Job {0} completed successfully".format(self.backup_job.job_id))
            self.backup_job_monitor_complete = True
        except Exception as err:
            self.job_monitor_error_string = err
            self.log.error(err)
            self.backup_job_monitor_complete = True
            raise err

    def _prepare_scale_param(self):
        """
        Prepares a dictionary containing details of vm in a particular region
        """
        vm_region = None
        self.scale_params = dict()
        hypervisor_display_name = self.auto_subclient.auto_vsainstance.vsa_instance.instance_name
        for _vm in self.auto_subclient.vm_list:
            if hypervisor_display_name == hypervisor_type.MICROSOFT_AZURE.value.lower() or hypervisor_display_name == hypervisor_type.AZURE.value.lower():
                vm_region = self.auto_subclient.hvobj.VMs[_vm].vm_info['location']
            elif hypervisor_display_name == hypervisor_type.AMAZON_AWS.value.lower():
                vm_region = self.auto_subclient.hvobj.get_instance_region(_vm)
            if vm_region in self.auto_scale_region_info:
                if vm_region not in self.scale_params:
                    self.scale_params[vm_region] = {'total_vm_count': 0,
                                                    'total_disk_size': 0,
                                                    'existing_agents': 0}
                self.scale_params[vm_region]['total_vm_count'] += 1
                if hypervisor_display_name == hypervisor_type.AMAZON_AWS.value.lower():
                    for vol in self.auto_subclient.hvobj.VMs[_vm].volume_props.values():
                        self.scale_params[vm_region]['total_disk_size'] += vol['size']
                elif hypervisor_display_name == hypervisor_type.MICROSOFT_AZURE.value.lower() or hypervisor_display_name == hypervisor_type.AZURE.value.lower():
                    self.scale_params[vm_region]['total_disk_size'] += \
                        self.auto_subclient.hvobj.VMs[_vm].total_disk_size

        # Calculate existing agent per region
        self.auto_subclient.auto_commcell.commcell.clients.refresh()
        self.auto_subclient.get_proxies()
        for proxy in self.auto_subclient.auto_vsainstance.get_proxy_list():
            proxy = proxy.lower()
            if self.auto_subclient.proxy_obj[proxy][0] \
                    and self.auto_subclient.proxy_obj[proxy][1] in self.scale_params:
                self.scale_params[self.auto_subclient.proxy_obj[proxy][1]]['existing_agents'] += 1

        self.log.info(self.scale_params)

    def _update_proxy_status(self):
        """
        Updates the proxy status by checking backup job status
        """
        self.auto_subclient.auto_commcell.commcell.clients.refresh()
        instance_proxies = self.auto_subclient.auto_vsainstance.get_proxy_list()

        for proxy in set().union(instance_proxies, list(self.proxy_monitor.keys())):
            if proxy not in self.proxy_monitor:
                self.proxy_monitor[proxy] = dict()
                self.auto_subclient.hvobj.update_hosts()
                self.auto_subclient.auto_commcell.commcell.clients.refresh()
                proxy_ip = self.auto_subclient.auto_commcell.get_hostname_for_client(proxy)
                self.proxy_monitor[proxy]['region'] = self.auto_subclient. \
                    hvobj.get_proxy_location(proxy_ip)[1]
                self.proxy_monitor[proxy]['client_id'] = int(self.auto_subclient.auto_commcell.get_client_id(proxy_ip))
                self.proxy_monitor[proxy]['is_auto_proxy'] = True \
                    if 'cvautoproxy' in proxy else False
                if self.proxy_monitor[proxy]['is_auto_proxy']:
                    self.auto_subclient.hvobj.VMs = proxy
                    self.proxy_monitor[proxy]['vmm_job'] = Job(self.auto_subclient.
                                                               auto_commcell.commcell,
                                                               proxy.split('cvautoproxy')[1])
                    self.proxy_monitor[proxy]['vmm_job_is_completed'] = \
                        self.proxy_monitor[proxy]['vmm_job'].is_finished
                    if self.is_tenant:
                        self.auto_subclient.hvobj.switch_to_admin_access()
                        self.auto_subclient.hvobj.VMs[proxy].update_vm_info(force_update=True)
                        print("Switched to admin account and updated")
                    self.proxy_monitor[proxy]['vm_obj'] = self.auto_subclient.hvobj.VMs[proxy]

                    if not self.proxy_monitor[proxy]['region']:
                        self.proxy_monitor[proxy]['region'] = \
                            self.proxy_monitor[proxy]['vm_obj'].vm_info['location']
                self.proxy_monitor[proxy]['assigned_vms'] = list()

            self.proxy_monitor[proxy]['proxy_status'] = 0
            if self.proxy_monitor.get(proxy).get('vmm_job') and not \
                    self.proxy_monitor.get(proxy).get('vmm_job_is_completed'):
                self.proxy_monitor[proxy]['vmm_job_is_completed'] = self.proxy_monitor. \
                    get(proxy).get('vmm_job').is_finished

        for vm_status in self.backup_job.details['jobDetail']['clientStatusInfo']. \
                get('vmStatus', []):
            agent = vm_status.get('Agent')
            if agent and vm_status['vmName'] not in self.proxy_monitor[agent]['assigned_vms']:
                self.proxy_monitor[agent]['assigned_vms'].append(vm_status['vmName'])

            # if proxy is backing up any vm update last active to current time
            if agent and vm_status['Status'] == 2:
                self.proxy_monitor[agent]['proxy_status'] = 1
                self.proxy_monitor[agent]['last_active_time'] = time.time()

            elif agent and vm_status['Status'] == 0 and \
                    self.proxy_monitor[agent]['proxy_status'] != 1:
                self.proxy_monitor[agent]['last_active_time'] = vm_status['BackupEndTime'] if \
                    self.proxy_monitor[agent].get('last_active_time', 0) < vm_status['BackupEndTime'] \
                    else self.proxy_monitor[agent].get('last_active_time', 0)

        for proxy in self.proxy_monitor:
            if self.proxy_monitor[proxy].get('is_auto_proxy', False) and self.proxy_monitor[proxy].get(
                    'vmm_job_is_completed', False) \
                    and self.proxy_monitor[proxy].get('proxy_status', 0) == 0:
                proxy_host_id = self.proxy_monitor[proxy].get('client_id')
                active_jobs = self.get_active_jobs_using_the_cloud_vm(proxy_host_id, [int(self.backup_job.job_id)])
                if active_jobs:
                    self.proxy_monitor[proxy]['proxy_status'] = 1
                    self.proxy_monitor[proxy]['last_active_time'] = time.time()
                    if 'validation_status' in self.proxy_monitor[proxy]:
                        self.proxy_monitor[proxy].pop('validation_status')
                    if 'validation_state' in self.proxy_monitor[proxy]:
                        self.proxy_monitor[proxy].pop('validation_state')

                    self.log.warning(f'proxy {proxy} is being used by jobs {active_jobs}.'
                                     f'Validation may fail or be inaccurate!')

        self.log.info(self.proxy_monitor)

    def calculate_agents_required(self):
        """
        Prepares dictionary contains agents required for each region
        """
        self._prepare_scale_param()

        # calculate agent required per region
        for region, details in self.scale_params.items():
            self.log.info("Calculating agents require for region : {0}".format(region))
            self.log.info(
                "VM Count : {0}, Total Data size GB : {1}, \
                existing agents: {2}".format(details["total_vm_count"],
                                             details['total_disk_size'],
                                             details['existing_agents']))

            single_agent = (self.rpo / 60) * self.data_throughput
            agents_required = min(math.ceil(details['total_disk_size'] / single_agent),
                                  int(details["total_vm_count"]))
            agents_required = min(agents_required,
                                  self.auto_scale_policy.get('scaleOption').
                                  get('scaleOutParam').get('maxVMthreshold'))
            agents_to_be_created = agents_required - details['existing_agents']
            agents_to_be_created = 0 if agents_to_be_created < 0 else agents_to_be_created
            self.log.info("Agents to be created : {0}".format(agents_to_be_created))
            details['agents_required'] = agents_required

    def _check_if_proxy_is_marked_for_power_off(self, proxy):
        """
        Checks if vm is marked for powered off

        Args:
            proxy      (str): name of the proxy

        Returns     (bool): True if vm is marked for power off else False

        """
        proxy_to_poweroff = self.auto_subclient.auto_commcell.get_cloud_vms_to_power_off()
        host_id = [host['HostId'] for host in proxy_to_poweroff]
        if int(self.auto_subclient.auto_commcell.commcell.clients.get(proxy).client_id) in \
                host_id:
            return True
        return False

    def _validate_proxy_status(self, force=False):
        """
        Calculates inactivity time validates accordingly
        Args:
            force   (bool): Set to True for one time validation

        """
        try:
            if not self.proxy_monitor:
                self._update_proxy_status()
            while not self.backup_job_monitor_complete or force:
                if not force:
                    time.sleep(120)
                self._update_proxy_status()
                for proxy, status in self.proxy_monitor.items():
                    self.auto_subclient.hvobj.update_hosts()
                    if status.get('is_auto_proxy') and status.get('vmm_job_is_completed') and not (
                            'validation_status' in status) and \
                            status.get('proxy_status') != 1:
                        if not status.get('vmm_job').status == 'Completed':
                            status['validation_status'] = False
                            continue

                        if 'proxy_power_off_request' not in status:
                            status['proxy_power_off_request'] = False

                        if status.get('proxy_status') == 0 and status.get('last_active_time', None):
                            in_active_time = time.time() - status.get('last_active_time')
                        else:
                            last_active_time = self.backup_job.start_timestamp \
                                if self.backup_job.start_timestamp > self.proxy_monitor. \
                                get(proxy).get('vmm_job').end_timestamp \
                                else self.proxy_monitor.get(proxy).get('vmm_job').end_timestamp

                            in_active_time = time.time() - last_active_time - 5 * 60
                        self.log.info("proxy : {0} inactive since {1} min".
                                      format(proxy, in_active_time / 60))

                        while not status['proxy_power_off_request']:
                            self.log.info(f"Checking if proxy {proxy} is marked for power off")

                            if in_active_time / 60 < 10:
                                if self._check_if_proxy_is_marked_for_power_off(proxy):
                                    self.log.info(f"Proxy {proxy} is marked for power off.")
                                    status['validation_state'] = self.ValidationState.DB_POWER_OFF_PASSED
                                    status['proxy_power_off_request'] = True
                                    break
                                else:
                                    self.log.info(
                                        f"Proxy {proxy} is not marked for power off.Checking for 10 mins of inactivity")
                                    status['proxy_power_off_request'] = False
                                    break

                            else:
                                self.log.info(
                                    f"Proxy {proxy} has not been marked for power off for more than 10 minutes. "
                                    f"Validation Failed")
                                status['validation_status'] = False
                                break

                        if in_active_time / 60 > 65 and \
                                status.get('validation_state', '') != \
                                self.ValidationState.PROXY_DELETED:
                            # check vm is deleted
                            if self.auto_subclient.hvobj.check_vms_exist([proxy]):
                                status['validation_status'] = False
                                self.log.error("Proxy {0} is not deleted after 65 min \
                                of in activity test case".format(proxy))
                                continue
                            self.log.info("Proxy {0} is deleted after 65 \
                            min activity. Validation passed".format(proxy))
                            status['validation_status'] = True

                        # check vm is deleted or powered off
                        elif in_active_time / 60 > 40 and status.get('validation_state', '') \
                                not in [self.ValidationState.PROXY_DELETED,
                                        self.ValidationState.PROXY_POWER_OFF_PASSED]:
                            if not self.auto_subclient.hvobj.check_vms_exist([proxy]):
                                self.log.info("Proxy {0} is deleted after 40 min activity.\
                                              Validation passed.".format(proxy))
                                status['validation_state'] = self.ValidationState.PROXY_DELETED
                                status['validation_status'] = True
                            else:
                                if status['vm_obj'].is_powered_on():
                                    self.log.info("Proxy {0} is not powered off after 40 min activity.\
                                                  Validation failed.".format(proxy))
                                    status['validation_status'] = False
                                    continue

                                self.log.info("Proxy {0} is powered off after 40 min activity.\
                                              Validation passed.".format(proxy))
                                status['validation_state'] = self.ValidationState.PROXY_POWER_OFF_PASSED

                self.log.info(f"Proxy Monitor Status: {self.proxy_monitor}")
                if force:
                    break

        except Exception as err:
            self.validator_error_string = err
            self.log.error(err)
            raise err

    def validate_auto_scale_settings(self, vm_provisioning_options):
        """Validates the configured auto-scale options match input"""
        try:
            auto_scale_policy_properties = self.auto_scale_policy
            if auto_scale_policy_properties['associatedClientGroup']['clientGroupName'] \
                    != vm_provisioning_options['server_group']:
                raise Exception("Server group validation failed. Configured server group"
                                f"{auto_scale_policy_properties['associatedClientGroup']['clientGroupName']}")
            if auto_scale_policy_properties['roleInfo']['name'] \
                    != vm_provisioning_options['iam_role']:
                raise Exception("IAM Role validation failed. Configured IAM Role"
                                f"{auto_scale_policy_properties['roleInfo']['name']}")
            auto_scale_az_info = self.auto_scale_region_info
            if len(auto_scale_az_info) != len(vm_provisioning_options["AZSpecificInfo"]):
                raise Exception("Number of Regions configured validation failed."
                                f"Configured regions {auto_scale_az_info.keys()}")
            for region_info in vm_provisioning_options['AZSpecificInfo']:
                region = region_info["AvailabilityZone"][:-1].lower()
                if region_info['Subnet'] != auto_scale_az_info[region]['subnetName']:
                    raise Exception(f"Subnet validation failed."
                                    f"Configured subnet {auto_scale_az_info[region]['subnetName']}")

                if region_info['VPC'] != auto_scale_az_info[region]['networkName']:
                    raise Exception("VPC Network configuration validation failed."
                                    f"Configured VPC network {auto_scale_az_info[region]['networkName']}")
                if region_info.get('SecurityGroup', None) != auto_scale_az_info[region]. \
                        get('securityGroups', [{}])[0].get('name', None):
                    raise Exception("Network Security group validation failed.Configured group"
                                    f"{auto_scale_az_info[region].get('securityGroups', [])[0].get('name', None)}")
            if vm_provisioning_options.get('CreatePublicIP', False) != auto_scale_policy_properties.get(
                    'isPublicIPSettingsAllowed', False):
                raise Exception("Public IP validation failed.Configured public IP setting"
                                f"{auto_scale_az_info.get('isPublicIPSettingsAllowed', False)}")

        except Exception as exp:
            self.log.error(exp)
            raise Exception(exp)

    def post_backup_validation(self):
        """
        Performs post back up auto scale validations

         Raises:
            Exception
               when auto scale validation fails
        """
        try:
            start_timer = time.time()
            validation_flag = True

            # validate for another 60 min if validation flag is not updated
            # perform validation for a max of 60 min after backup job completes
            self._validate_proxy_status(force=True)
            backup_job_client_status = self.backup_job.details['jobDetail']['clientStatusInfo']['vmStatus']

            while (time.time() - start_timer) / 60 < self.max_wait_period:
                for proxy, status in self.proxy_monitor.items():
                    if status.get('is_auto_proxy') and 'validation_status' not in status:
                        time.sleep(120)
                        self._validate_proxy_status(force=True)
                        break
                else:
                    break

            # final proxy status validation
            # time for resource clean up
            time.sleep(240)
            self.auto_subclient.hvobj.update_hosts()
            validation_flag = self.validate_clean_up_for_failed_job()
            self.auto_subclient.auto_commcell.commcell.clients.refresh()
            for proxy, status in self.proxy_monitor.items():
                self.log.info(self.proxy_monitor)
                if status.get('is_auto_proxy'):
                    self.log.info("Validating proxy : {0}".format(proxy))

                    # VMManagment job completion status
                    if status.get('vmm_job').status != 'Completed':
                        validation_flag = False
                        self.log.error("VMManagment job {0} failed".
                                       format(status.get('vmm_job').job_id))
                        continue

                    auto_scale_vm_validation = status['vm_obj'].AutoScaleVmValidation(status['vm_obj'],
                                                                                      self.auto_scale_region_info)
                    # proxy configuration validation
                    if not auto_scale_vm_validation. \
                            validate_auto_scale_proxy_configuration(autoscale_policy=self.auto_scale_policy):
                        self.log.error("Azure/AWS Proxy Configuration validation failed")

                    # validate if new proxy spawned was assigned at least one vm
                    if int(proxy.split('cvautoproxy')[1]) > int(self.backup_job.job_id) and len(
                            status['assigned_vms']) == 0:
                        self.log.error(
                            "proxy {0} was spawned but no vms were assigned. Validation Failed".format(proxy))
                        validation_flag = False

                    # check if proxy was spawned for region on which source vm were not present
                    if int(int(proxy.split('cvautoproxy')[1]) > int(self.backup_job.job_id)):
                        if status['region'] not in self.scale_params:
                            self.log.error(
                                "proxy was spawned in region {0} though no source vm found in the same region".format(
                                    status['region']))
                            validation_flag = False
                        else:
                            self.scale_params[status['region']]['agents_created'] = \
                                self.scale_params[status['region']].get('agents_created', 0) + 1

                    if 'validation_status' not in status:
                        validation_flag = False
                        self.log.error("Validation flag is not set on proxy {0}. Validation will fail".
                                       format(proxy))

                    elif not status.get('validation_status', False):
                        validation_flag = False
                        self.log.error("Proxy status validation has failed .Please check logs for further info.")
                        continue

                    # resource cleanup validation
                    if not auto_scale_vm_validation. \
                            validate_proxy_resource_cleanup():
                        validation_flag = False

                    if validation_flag and self.auto_subclient.auto_commcell.commcell.clients.has_client(proxy):
                        self.log.error(f"Proxy {proxy} not deleted from Commcell")
                        validation_flag = False

            # validate the number of proxy spawned with estimated number proxies required
            for region, details in self.scale_params.items():
                agents_to_be_created = details.get('agents_required') \
                                       - details.get('existing_agents')
                agents_to_be_created = 0 if agents_to_be_created < 0 else agents_to_be_created
                if agents_to_be_created != details.get('agents_created', 0):
                    self.log.error("Region : {0} : Agents to be created {1} : Agents created {2}".
                                   format(region, agents_to_be_created, details.get('agents_created', 0)))
                    validation_flag = False
            # Validates vm is backed up with agent from same region
            for _vm in backup_job_client_status:
                vm_region = None
                instance_name = self.auto_subclient.auto_vsainstance.vsa_instance.instance_name.lower()

                if instance_name == hypervisor_type.AZURE.value.lower() or instance_name == hypervisor_type.AZURE_V2.value.lower():
                    vm_region = self.auto_subclient.hvobj.VMs[_vm['vmName']].vm_info['location']
                elif instance_name == hypervisor_type.AMAZON_AWS.value.lower():
                    if self.is_tenant:
                        self.auto_subclient.hvobj.switch_to_tenant_access()
                    vm_region = self.auto_subclient.hvobj.get_instance_region(_vm['vmName'])
                if vm_region in self.auto_scale_region_info:
                    proxy_region = self.proxy_monitor[_vm.get('Agent')]['region']
                    if proxy_region != vm_region:
                        validation_flag = False
                        self.log.error(
                            "VM {0} in region {1} was backed up by Agent\
                             {2} in region {3}".format(_vm['vmName'], vm_region, _vm.get('Agent'), proxy_region))

            if not validation_flag:
                self.log.info("one or more validation has failed failed please check logs")
                self.validator_error_string += "one or more validation has failed failed please check logs ;"
                return validation_flag
            self.log.info("Post backup validation passed.")
            return validation_flag

        except Exception as err:
            self.log.error(err)
            raise Exception(err)

    def validate_clean_up_for_failed_job(self):
        """Checks if any VMManagement jobs have failed

        Returns:
            status(bool) : True if no VMManagement job failed else false
        """
        vm_management_jobs = self.auto_subclient.auto_commcell. \
            get_vm_management_jobs(int(self.backup_job.job_id))
        status = True
        self.auto_subclient.auto_commcell.commcell.clients.refresh()
        for vm_management_job in vm_management_jobs:
            if Job(self.auto_subclient.auto_commcell.commcell,
                   vm_management_job).status != 'Completed':
                status = False
                self.validator_error_string += "VMManagement job {0} has failed ;".format(vm_management_job)
                self.log.error("VMManagement job {0} has failed.".format(vm_management_job))
                proxy_name = 'cvautoproxy' + str(vm_management_job)
                if self.proxy_monitor.get(proxy_name, {}).get('vm_obj', None):
                    proxy_obj = self.proxy_monitor.get(proxy_name).get('vm_obj')
                    auto_scale_vm_validation = proxy_obj.AutoScaleVmValidation(proxy_obj,
                                                                               self.auto_scale_region_info)
                    clean_up_status = auto_scale_vm_validation.validate_proxy_resource_cleanup()
                else:
                    hypervisor_types = self.auto_subclient.auto_vsainstance.vsa_instance_name
                    if hypervisor_types == hypervisor_type.MICROSOFT_AZURE.value.lower() or hypervisor_types == hypervisor_type.AZURE.value.lower():
                        clean_up_status = True
                        resource_group = self.auto_scale_policy. \
                            get('esxServers', [{}])[0].get('esxServerName', None)

                        all_resources = self.auto_subclient.hvobj.get_resource_group_resources(resource_group)
                        for resource in all_resources:
                            if proxy_name in resource.get('name', ''):
                                self.log.error("Resource {0} is not cleaned up.".format(resource.get('name')))
                                clean_up_status = False

                if not clean_up_status:
                    self.validator_error_string += "Resource for {0} is not cleaned up ;".format(proxy_name)

                if self.auto_subclient.auto_commcell.commcell.clients.has_client(proxy_name):
                    self.validator_error_string += "Client not deleted from Commcell ;"

        return status

    def wait_for_vm_management_child_jobs_to_complete(self, backup_job=None):
        """Waits until all the VMManagement jobs started by the backup job is complete
           Args:
            backup_job  (Job): Job object of backup job
        Returns:
            status (bool):  True if all VMManagement job completes successfully or
                            if no job was started else returns False

        """
        backup_job = backup_job if backup_job else self.backup_job
        vm_management_jobs = self.auto_subclient.auto_commcell. \
            get_vm_management_jobs(int(backup_job.job_id))
        status = True
        for vm_management_job in vm_management_jobs:
            job = Job(self.auto_subclient.auto_commcell.commcell,
                      vm_management_job)
            if not job.wait_for_completion():
                self.log.warning(f"VMManagement job {vm_management_job} failed.")
                status = False
        return status

    def get_active_jobs_using_the_cloud_vm(self, host_id, skip_jobs=None):
        """Gets the list of active jobs using cloud proxy

        Args:
            host_id   (int): client id of cloud VM
            skip_jobs (list): list of jobs to be skipped
        Returns:
            active_jobs (list) : list of jobs excluding skip_jobs
        """
        jobs_using_the_cloud_vm = self.auto_subclient.auto_commcell.get_cloud_vm_jobs_marked_active_in_db(host_id)
        active_jobs = []
        skip_jobs = [] if not skip_jobs else skip_jobs
        for job_id in jobs_using_the_cloud_vm:
            if job_id not in skip_jobs:
                job = Job(self.auto_subclient.auto_commcell.commcell, job_id)
                if not job.is_finished:
                    active_jobs.append(job_id)
        return active_jobs


class AutoScaleNodeConfiguration:
    """ Base class for performing operations & custom configuration for auto-scale nodes """

    def __init__(self, vsa_obj):
        self.vsa_obj = vsa_obj
        self._node_os = "Unix"
        self._image_path = None
        self._image_type = None
        self._generalize_script = None
        self._image_name = None
        self._gallery_image = None
        self._image_request_id = None
        self.log = self.vsa_obj.log

    @property
    def node_os(self):
        """
        Returns OS of Access  node to be used

        Returns:
            _node_os     (str)  --  Windows / Unix OS of Access node to be used by Autoscale / on-demand provisioning

        """
        return self._node_os

    @node_os.setter
    def node_os(self, value):
        """
        Sets the value for node OS to be used by Autoscale / on-demand provisioning

        Args:
            value   (str)  --  Windows / Unix as OS of Access node to be used by Autoscale / on-demand provisioning

        """
        self._node_os = value

    @property
    def image_path(self):
        """
        Returns full path of image to be used for Access node creation (if custom image being used)

        Returns:
            _image_path     (str)  --  path of image to be used for Access node creation

        """
        if not self._image_path:
            if self.image_type.lower() == "private":
                self._image_path = f"Private/{self.image_name}"

            elif self.image_type.lower() == "public":
                self._image_path = f"Public/commvault/cloud-data-manager/{self.image_name}"

        return self._image_path

    @image_path.setter
    def image_path(self, value):
        """
        Sets full path of image to be used for Access node creation (if custom image being used)

        Args:
            value           (str)   --  path of image to be used for Access node creation (if custom image being used)

        """
        self._image_path = value

    @property
    def gallery_image(self):
        """
        Returns full path of image to be used for Access node creation (if custom image being used)

        Returns:
            _image_path     (str)  --  path of image to be used for Access node creation

        """
        return self._gallery_image

    @gallery_image.setter
    def gallery_image(self, value):
        """
        Sets full path of image to be used for Access node creation (if custom image being used)

        Args:
            value           (str)   --  path of image to be used for Access node creation (if custom image being used)

        """
        self._gallery_image = value

    @property
    def image_type(self):
        """
        Returns path of image to be used for Access node creation (if custom image being used)

        Returns:
            _image_type     (str)  --  type of image to be used for Access node creation

        """
        return self._image_type

    @image_type.setter
    def image_type(self, value):
        """
        Sets type of image to be used for Access node creation (if custom image being used)

        Args:
            value   (str)   --  type of image to be used for Access node creation (if custom image being used)

        """
        self._image_type = value

    @property
    def image_name(self):
        """
        Returns name of image to be used for Access node creation (if custom image being used)

        Returns:
            _image_type     (str)  --  name of image to be used for Access node creation

        """
        return self._image_name

    @image_name.setter
    def image_name(self, value):
        """
        Sets name of image to be used for Access node creation (if custom image being used)

        Args:
            value   (str)   --  name of image to be used for Access node creation (if custom image being used)

        """
        self._image_name = value

    @property
    def generalize_script(self):
        """
        Returns the script to generalize VM before making image out of it

        Returns:
            _generalize_script     (str)  --  script to generalize Azure VM

        """
        if not self._generalize_script:
            if self.node_os.lower() == "windows":
                self._generalize_script = ['C:\\WINDOWS\\system32\\sysprep\\sysprep.exe /generalize /shutdown /oobe']

            elif self.node_os.lower() == "unix":
                self._generalize_script = [
                    'sudo find / -name \".bash_history\" -o -name \".history\" 2>/dev/null',
                    'sudo find / -name \"authorized_keys\" -exec rm -f {} \;',
                    'sudo waagent -deprovision+user -force'
                ]

        return self._generalize_script

    @generalize_script.setter
    def generalize_script(self, value, gallery_image):
        """
        Sets the script to generalize VM before making image out of it

        Args:
            value   (str)   --  script to generalize Azure VM

        """
        self._generalize_script = value

    def get_image_details_from_db(self, image_request_id):
        """ Gets the details for image created with the provided request ID from RecutCenter DB and sets the current
            build Image version

            Returns:
                image_version     (str)  --  Version of image created for the provided request ID
        """
        try:
            from AutomationUtils import config
            from AutomationUtils.database_helper import MSSQL

            req_image_name = {
                "windows": "Azure-AccessNode",
                "unix": "Azure-Linux-AccessNode"
            }

            self.log.info("Collecting Image Details from recut DB")
            config_json = config.get_config()
            db_user = eval('config_json.SQL.Username')
            db_pass = eval('config_json.SQL.Password')

            mssqlcon = MSSQL(server='tcp:webapps-sqlserver.database.windows.net,1433', user=db_user,
                                               password=db_pass, database='RecutAutomation', use_pyodbc=True)

            image_query = f"""
                            DECLARE @return_value NVARCHAR(MAX);
                            EXEC	@return_value=[dbo].[GetRecutRequestProperties]
                            @i_RecutRequestID = {int(image_request_id)},
                            @i_PropertyName = N'OVAHypervisorType'
                        """

            query_result = mssqlcon.execute(image_query)
            images_created = query_result.rows[0][0].split(',')
            self.log.info(f"Found following images list for request id {image_request_id}: {images_created}")

            if req_image_name[self.node_os.lower()] in images_created:
                version_query = f"""
                                    SELECT sValue FROM RecutProperties
                                    WHERE  nRecutRequestID = {image_request_id} 
                                    AND sNAME = '{req_image_name[self.node_os.lower()]}'
                                """
                query_result = mssqlcon.execute(version_query)
                image_version = query_result.rows[0][0]
                self.log.info(f"Found Image version {image_version} created for Windows access node.")

            else:
                raise Exception(f"Images created: {images_created}, has no Azure Windows access node created in this"
                                f" request, not proceeding with the testcase.")

            return image_version

        except Exception as exp:
            raise Exception(f"Failed to fetch Image details: {exp}")

    def update_image_status_db(self, image_request_id, status):
        """ update the status for image creation for provided request ID from RecutCenter DB
        """
        try:
            from AutomationUtils import config
            from AutomationUtils.database_helper import MSSQL

            self.log.info("Setting Image status to recutDB")
            config_json = config.get_config()
            db_user = eval('config_json.SQL.Username')
            db_pass = eval('config_json.SQL.Password')

            mssqlcon = MSSQL(server='tcp:webapps-sqlserver.database.windows.net,1433', user=db_user,
                                               password=db_pass, database='RecutAutomation', use_pyodbc=True)

            update_query = f"""
                            DECLARE @return_value NVARCHAR(MAX);
                            EXEC	@return_value=[dbo].[AddModifyRecutRequestProperties]
                            @i_RecutRequestID = {int(image_request_id)},
                            @i_PropertyName = N'ImageCertification',
                            @i_PropertyValue = N'{status}'
                        """

            query_result = mssqlcon.execute(update_query)
            self.log.info(f"Image status updated in recutDB to {status}")

        except Exception as exp:
            raise Exception(f"Failed to update image status with exception: {exp}")

    def create_managed_image(self, vm_obj):
        """
            Creates Managed image from the Gallery image created with RecutCenter request for OVA creation
            Args:
                vm_obj          (str)   -- azure VM obj for VM deployed from Gallery image
            Returns:
                image_name     (str)    --  name of image created for provided VM
        """
        try:
            generalize_vm_script = self.generalize_script
            vm_obj.run_command(script=generalize_vm_script)
            vm_obj.generalize_vm()

            image_props = {
                "location": self.vsa_obj.region,
                "tags": {
                    "Purpose": "OVA Image",
                    "CreatedBy": "Automation"
                },
                "vm_id": f"/subscriptions/{vm_obj.subscription_id}/resourceGroups/{vm_obj.resource_group_name}/"
                         f"providers/Microsoft.Compute/virtualMachines/{vm_obj.vm_name}",
                "resourceGroup": vm_obj.resource_group_name,
                "image_name": vm_obj.vm_name
            }
            image_name = self.vsa_obj.hvobj.create_image_from_vm(image_props)

            if image_name:
                self._image_path = None
                self._image_type = "Private"
                self._image_name = image_name

        except Exception as exp:
            self.log.error(f"Failed to create Managed image from Gallery Image")
            if vm_obj:
                vm_obj.clean_up()
            raise Exception(f"Failed to create Managed image from Gallery Image with error {exp}")
