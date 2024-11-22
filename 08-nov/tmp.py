# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Google Cloud vm"""

import socket
import requests
from AutomationUtils import machine
from AutomationUtils import logger
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils import VirtualServerUtils
import re


class GoogleCloudVM(HypervisorVM):
    """
    This is the main file for all Google Cloud VM operations

    Methods:

        _get_vm_info()            -  get the information about the particular VM

        power_off()               -  power off the VM

        power_on()                -  power on the VM

        restart_vm()              -  restarts the VM

        delete_vm()               -  delete the VM

        get_vm_guid()             -  gets the GUID of the VM

        get_nic_info()            -  get all networks attached to that VM

        get_disk_list()           -  gets all the disks attached to the VM

        get_disk_info()           -  get all the disk info of VM

        get_disk_size()           -  gets the total disk size of all disks in VM

        get_status_of_vm()        - get the status of VM like started, stopped

        get_OS_type()             - update the OS type of the VM

        get_subnet_ID()           - Update the subnet_ID for VM

        get_IP_address()          - gets the internal and external IP addresses of the VM

        update_vm_info()          - updates the VM info

    """

    def __init__(self, hvobj, vm_name):
        """
         Initialization of Google Cloud vm properties

         Args:
            vm_name (str)    --  name of the VM for which properties can be fetched

            hvobj   (object)        --  Hypervisor class object for Google Cloud

        """

        super(GoogleCloudVM, self).__init__(hvobj, vm_name)
        self.Hvobj = hvobj
        self.vm_name = vm_name
        self.restore_vm_prefix = 'del'
        if vm_name.startswith(self.restore_vm_prefix):
            self.project_name = self.Hvobj.restore_project
            self.zone_name = self.Hvobj.get_vm_zone(vm_name, self.project_name)
            self.custom_metadata_in_vm = self.Hvobj.get_vm_custom_metadata(vm_name, self.project_name)
            self.service_account_in_vm = self.Hvobj.get_vm_service_account(vm_name, self.project_name)
        else:
            self.zone_name = self.Hvobj.get_vm_zone(vm_name)
            self.project_name = self.Hvobj.project
            self.custom_metadata_in_vm = self.Hvobj.get_vm_custom_metadata(vm_name)
            self.service_account_in_vm = self.Hvobj.get_vm_service_account(vm_name)
        self.access_token = self.Hvobj.access_token
        self.log.info("access info: {0}".format(self.access_token))
        self._vm_info = {}
        self.nic = []
        self.subnet = []
        self.disk_list = []
        self.ip = None
        self.disk_dict = {}
        self.internal_IPs = []
        self.external_IPs = []
        self._external_ip_enabled_dict = {}
        self.subnet_IDs = []
        self.log = logger.get_log()
        self.google_session = requests.Session()
        self._basic_props_initialized = False
        self._get_vm_info()
        self.update_vm_info()
        self.workload_vm = None
        self.workload_vm_zone = None
        self.workload_zone_proxy = []
        self.workload_region_proxy = []
        self.restore_vm_prefix = 'del'
        self.replica_zone = self.Hvobj.replica_zone
        self.vm_custom_metadata = self.Hvobj.vm_custom_metadata
        self.public_reserved_ip = self.Hvobj.public_reserved_ip
        self.private_reserved_ip = self.Hvobj.private_reserved_ip
        self.vm_service_account = self.Hvobj.vm_service_account
        self._disk_type = None
        self._repl_zone = None

    class BackupValidation(object):
        def __init__(self, vm_obj, backup_option):
            self.vm = vm_obj
            self.backup_option = backup_option
            self.backup_job = self.backup_option.backup_job
            self.log = logger.get_log()

        def validate(self):
            """Validates the post backup validation"""
            # Snapshot pruning validation
            self.log.info("Post backup validations for Google Cloud")
            if self.vm.Hvobj.check_snapshot_pruning(f'gx-backup-{self.backup_option.backup_job.job_id}'):
                self.log.info(
                    "Google Cloud snapshot pruning validation successful")
            else:
                raise Exception("Google Cloud snapshot pruning validation failed")

            # Disk pruning validation
            if self.vm.Hvobj.check_disk_pruning(f'gx-backup-{self.backup_option.backup_job.job_id}'):
                self.log.info(
                    "Google Cloud disk pruning validation successful")
            else:
                raise Exception("Google Cloud disk pruning validation failed")

        def validate_workload(self, proxy_obj):
            """
            Does the validation of the backup workload Distribution

            Args:
                proxy_obj  : A dictionary of proxy name as the key and proxy location as value

            Raises:
                Exception:
                    When Workload distribution fails
            """
            if proxy_obj:
                vm_zone = self.vm.hvobj.VMs[self.vm.workload_vm].zone_name
                prxy_name = self.vm.proxy_name
                proxy_zone = proxy_obj[prxy_name][1]
                if self.vm.workload_zone_proxy:
                    if prxy_name in self.vm.workload_zone_proxy:
                        self.log.info("Backup Validation successful for VM {} loc: {} Proxy {} loc: {}, (Zone Match)"
                                      .format(self.vm.workload_vm, vm_zone, prxy_name, proxy_zone))
                    else:
                        raise Exception("Failure in Backup Workload validation")
                elif self.vm.workload_region_proxy:
                    if prxy_name in self.vm.workload_region_proxy:
                        self.log.info("Backup Validation successful for VM {} loc: {} Proxy {} loc: {}, (Region Match)"
                                      .format(self.vm.workload_vm, vm_zone, prxy_name, proxy_zone))
                    else:
                        raise Exception("Failure in Backup Workload validation")
                else:
                    self.log.info("Backup Validation successful for VM {} loc: {} Proxy {} loc: {}, (Any)"
                                  .format(self.vm.workload_vm, vm_zone, prxy_name, proxy_zone))

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options, **kwargs):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.restore_job = self.vm_restore_options.restore_job
            self.log = logger.get_log()

        def __eq__(self, other):
            """compares the source vm and restored vm"""
            try:
                # Disk type validation, pd-standard, pd-ssd, local-ssd etc
                if len(self.vm.vm.disk_dict) != len(other.vm.vm.disk_dict):
                    self.log.info("Disk validation failed")
                    return False
                if self.vm_restore_options.vm_service_account:
                    if self.vm_restore_options.vm_service_account == other.vm.vm.service_account_in_vm["email"]:
                        self.log.info("Passed Service Account is found in restored VM")
                    else:
                        self.log.info("Found a different Service Account{0}".format(
                            other.vm.vm.service_account_in_vm["sa_name"]))
                        return False
                else:
                    if other.vm.vm.service_account_in_vm["displayName"] == "Compute Engine default service account":
                        self.log.info("VM is restored with Compute Engine Default Service Account")
                    else:
                        self.log.info("VM does not have Compute Engine Default service account it is having {0}".format(
                            other.vm.vm.service_account_in_vm["displayName"]
                        ))
                        return False

                if self.vm_restore_options.vm_custom_metadata:
                    custom_metadata_list_temp = [dict(item) for item in self.vm_restore_options.vm_custom_metadata]
                    custom_metadata_list1 = []
                    for metadata in custom_metadata_list_temp:
                        custom_metadata_list1.append(
                            {'key': metadata.get("name", ""), 'value': metadata.get("value", "")})
                    custom_metadata_list2 = other.vm.vm.custom_metadata_in_vm
                    if [i for i in custom_metadata_list1 if i not in custom_metadata_list2] == []:
                        self.log.info("Provided Custom Metadata values are restored successfully")
                    else:
                        self.log.info("Provided Custom Metadata values are not present on restored VM: Failed")
                        return False
                if self.vm.vm.custom_metadata_in_vm:
                    custom_metadata_list1 = self.vm.vm.custom_metadata_in_vm
                    custom_metadata_list2 = other.vm.vm.custom_metadata_in_vm
                    if [i for i in custom_metadata_list1 if i not in custom_metadata_list2] == []:
                        self.log.info("Source and destination custom Metadata values are same")
                    else:
                        self.log.info("Source and destination custom Metadata values are different")
                        return False
                for disk_index in other.vm.vm.disk_dict:
                    disk_type_source = self.vm.vm.disk_dict[disk_index]['type'].split("/")
                    disk_type_dest = other.vm.vm.disk_dict[disk_index]['type'].split("/")
                    if disk_type_source[-1] != disk_type_dest[-1]:
                        self.log.info(f"Disk type validation failed for source disk index: {disk_index}")
                        return False
                    if "regions" in disk_type_source:
                        # Regional disk validation
                        if "regions" not in disk_type_dest:
                            self.log.info(f"Regional disk validation failed for disk: {disk_index}")
                            return False
                        rep_zones_src = self.vm.vm.disk_dict[disk_index]['replicaZones']
                        rep_zones_dest = self.vm.vm.disk_dict[disk_index]['replicaZones']
                        src_zone1 = rep_zones_src[0].split("/")[-1]
                        src_zone2 = rep_zones_src[1].split("/")[-1]
                        dest_zone1 = rep_zones_dest[0].split("/")[-1]
                        dest_zone2 = rep_zones_dest[1].split("/")[-1]
                        if self.vm_restore_options.in_place_overwrite:
                            if dest_zone1 != src_zone1 or dest_zone2 != src_zone2:
                                self.log.info(f"Regional disk validation failed for disk: {disk_index} zone did not "
                                              f"matched")
                                return False
                        else:
                            if self.replica_zone not in [dest_zone1, dest_zone2]:
                                self.log.info(f"Regional disk validation failed for disk: {disk_index} zone did not "
                                              f"matched")
                                return False
                        self.log.info("Regional disk validation successful")
                self.log.info("Disk type validation successful")

                # Public IP validation
                if self.vm.vm.public_ip_enabled != other.vm.vm.public_ip_enabled:
                    self.log.info("Public IP validation failed")
                    return False
                self.log.info("Public IP validation successful")
                #Public reserved IP Validation
                if self.vm.vm.public_reserved_ip:
                    if other.vm.vm.ip != self.vm.vm.public_reserved_ip:
                        self.log.info("Passed public reserved ID is not present on the restored VM")
                        return False
                    else:
                        self.log.info("Passed public reserved Ip address is present on the restored VM")
                #Private reserved IP Validation
                if self.vm.vm.private_reserved_ip:
                    if other.vm.vm.external_IPs != self.vm.vm.private_reserved_ip:
                        self.log.info("Passed private reserved ID is not present on the restored VM")
                        return False
                    else:
                        self.log.info("Passed private reserved Ip address is present on the restored VM")
                # Google cloud multi project restore snapshot pruning validation
                proxy_machine = machine.Machine(machine_name=self.vm_restore_options.proxy_client,
                                                commcell_object=self.vm.vm.Hvobj.commcell)
                if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', proxy_machine.ip_address) == None:
                    proxy_machine_name = socket.getfqdn(proxy_machine.ip_address).split(".")[0]
                else:
                    proxy_machine_name = proxy_machine.ip_address
                proxy_project = self.vm.vm.Hvobj.get_project_by_instance_name(proxy_machine_name)
                if proxy_project != other.vm.vm.project_name:
                    if self.vm.vm.Hvobj.check_snapshot_pruning(
                            f'gx-restore-{self.vm_restore_options.restore_job.job_id}'):
                        self.log.info("Google Cloud restore snapshot pruning successful")
                    else:
                        raise Exception("Google Cloud restore snapshot pruning failed")

                    if self.vm.vm.Hvobj.check_disk_pruning_by_description(proxy_project,
                                                                       self.vm_restore_options.restore_job.job_id):
                        self.log.info("Disk pruning validation successful")
                    else:
                        raise Exception("Disk pruning validation failed")

                return True

            except Exception as exp:
                self.log.exception("Exception in Vm Validation")
                raise Exception("Exception in Vm Validation:" + str(exp))

        def validate_restore_workload(self, proxy_obj):
            """
            Does the validation of the restore workload Distribution

            Args:
                proxy_obj  : A dictionary of proxy name as the key and proxy location as value

            Raises:
                Exception:
                    When Workload distribution fails
                """
            vm_zone = self.vm.workload_vm_zone
            prxy_name = self.vm.hvobj.VMs[self.vm.workload_vm].proxy_name
            proxy_zone = proxy_obj[prxy_name][1]
            if self.vm.workload_zone_proxy:
                if prxy_name in self.vm.workload_zone_proxy:
                    self.log.info("Restore Validation successful for VM {0} loc: {1} Proxy {2} loc: {3}, (Zone Match)"
                                  .format(self.vm.workload_vm, vm_zone, prxy_name, proxy_zone))
                else:
                    raise Exception("Failure in Restore Workload validation")
            elif self.vm.workload_region_proxy:
                if prxy_name in self.vm.workload_region_proxy:
                    self.log.info("Restore Validation successful for VM {0} loc: {1} Proxy {2} loc: {3}, (Region Match)"
                                  .format(self.vm.workload_vm, vm_zone, prxy_name, proxy_zone))
                else:
                    raise Exception("Failure in Restore Workload validation")

            else:
                self.log.info("Restore Validation successful for VM {0} loc: {1} Proxy {2} loc: {3}, (Any)"
                              .format(self.vm.workload_vm, vm_zone, prxy_name, proxy_zone))

    @property
    def nic_count(self):
        """
                To fetch the nic count of the VM
                Returns:
                    nic_count         (Integer): Count of nic
                """
        return len(self.nic)

    @property
    def google_vmurl(self):
        google_vmurl = \
            "https://www.googleapis.com/compute/v1/projects" \
            "/{}/zones/{}/instances/{}/".format(self.project_name, self.zone_name, self.vm_name)

        return google_vmurl

    @property
    def default_headers(self):
        self.Hvobj._headers = {'Authorization': 'Bearer %s' % self.access_token}
        return self.Hvobj._headers

    @property
    def public_ip_enabled(self):
        if self._external_ip_enabled_dict == {}:
            for network_interface in self._vm_info['networkInterfaces']:
                if "accessConfigs" in network_interface and "natIP" in network_interface["accessConfigs"]:
                    if network_interface["accessConfigs"]["natIP"] != "":
                        self._external_ip_enabled_dict[network_interface['name']] = True
                self._external_ip_enabled_dict[network_interface['name']] = False
        return self._external_ip_enabled_dict

    def clean_up(self):
        """
        Clean up the VM and its resources.

        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned

        """
        try:
            if self.vm_name.startswith("del"):
                self.log.info("Deleting Restore VM : {0}".format(self.vm_name))
                self.delete_vm()
            else:
                self.log.info("Powering off VMs after restore{0}".format(self.vm_name))
                self.power_off()

        except Exception as exp:
            self.log.exception("Exception in Cleanup : {0}".format(str(exp)))
            raise Exception("Exception in Cleanup:" + str(exp))

    def _get_vm_info(self):
        """
        Gets all VM info related to the given VM

        Raises:
            Exception:
                If the vm data cannot be collected

        """
        try:
            self.log.info("Getting all information of VM [%s]" % (self.vm_name))
            self._vm_info = False
            vm_infourl = self.google_vmurl
            self.log.info("Google APi url is : '{0}'".format(vm_infourl))
            data = self.Hvobj._execute_google_api(vm_infourl)
            self._vm_info = data
            self.log.info("vm-info in ::393 line {0}".format(self._vm_info))

        except Exception as err:
            self.log.exception("Exception in _get_vm_info : {0}".format(str(err)))
            raise Exception(err)

    def power_on(self):
        """
        Powers on the VM

        Returns:
            ret_code    (bool)      -   True if the VM is powered on

        Raises:
            Exception:
                If the VM cannot be powered on

        """
        try:
            self.log.info("powering on vm [%s]" % (self.vm_name))
            vmurl = self.google_vmurl + "start"
            _ = self.Hvobj._execute_google_api(vmurl, 'post')
            ret_code = True
            return ret_code

        except Exception as err:
            self.log.exception("Exception in power on: {0}".format(str(err)))
            raise Exception(err)

    def power_off(self):
        """
        Powers off the VM

        Returns:
            ret_code    (bool)      -   True if the VM is powered off

        Raises:
            Exception:
                If the VM cannot be powered off

        """
        try:
            self.log.info("powering off vm [%s]" % (self.vm_name))
            vmurl = self.google_vmurl + "stop"
            _ = self.Hvobj._execute_google_api(vmurl, 'post')
            ret_code = True
            return ret_code
        except Exception as err:
            self.log.exception("Exception in power off: {0}".format(str(err)))
            raise Exception(err)

    def restart_vm(self):
        """
        Resets the VM

        Returns:
            ret_code    (bool)      -   True if the VM is reset

        Raises:
            Exception:
                If the VM cannot be reset

        """
        try:
            self.log.info("powering on vm [%s]" % (self.vm_name))
            vmurl = self.google_vmurl + "reset"
            _ = self.Hvobj._execute_google_api(vmurl, 'post')
            ret_code = True
            return ret_code

        except Exception as err:
            self.log.exception("Exception in Restart VM: {0}".format(str(err)))
            raise Exception(err)

    def delete_vm(self):
        """
        Deletes the VM

        Returns:
            ret_code    (bool)      -   True if the VM is deleted

        Raises:
            Exception:
                If the VM cannot be deleted

        """
        try:
            self.log.info("Deleting VM [%s]" % (self.vm_name))
            vmurl = self.google_vmurl
            _ = self.Hvobj._execute_google_api(vmurl, 'delete')
            ret_code = True
            return ret_code

        except Exception as err:
            self.log.exception("Exception in Delete VM: {0}".format(str(err)))
            raise Exception(err)

    def _get_status_of_vm(self):
        """
        gets status of VM, e.g. running, stopped, etc

        Raises:
            Exception:
                if status of vm cannot be found
        """
        try:
            self.log.info("Getting status of VM [%s]" % (self.vm_name))
            vm_infourl = self.google_vmurl
            data = self.Hvobj._execute_google_api(vm_infourl)
            self.vm_state = data['status']

        except Exception as err:
            self.log.exception("Exception in _get_vm_info: {0}".format(str(err)))
            raise Exception(err)

    def _get_nic_info(self):
        """
        Gets all networks attached to VM

        Raises:
            Exception:
                If the nic_info cannot be found
        """
        try:
            self.log.info("Getting the network cards info for VM %s" % self.vm_name)
            data = self._vm_info
            all_nic_info = data["networkInterfaces"]
            if self.nic != []:
                self.nic = []
            for nic in all_nic_info:
                nic_name = nic['network'].rpartition('/')[2]
                self.nic.append(nic_name)

        except Exception as err:
            self.log.exception("Exception in get_nic_info: {0}".format(str(err)))
            raise Exception(err)

    def _get_disk_list(self):
        """
        Gets all the disks attached to VM
        """
        data = self._vm_info
        if self.disk_list != []:
            self.disk_list = []
        for disk in data['disks']:
            disk_name = disk['source'].rpartition('/')[2]
            self.disk_list.append(disk_name)
        self.disk_count = len(self.disk_list)
        return self.disk_list

    def _get_disk_info(self):
        """
        Get all info about disks attached to VM

        Raises:
            Exception:
                If the disk info cannot be found
        """
        try:
            data = self._vm_info
            for disk in data['disks']:
                disk_index = disk["index"]
                disk_info_url = disk['source']
                data = self.Hvobj._execute_google_api(disk_info_url)
                self.disk_dict[disk_index] = data

        except Exception as err:
            self.log.exception("Exception in get_disk_info: {0}".format(str(err)))
            raise Exception(err)

    def _get_disk_size(self):
        """
        gets the total used space of the VM

        Raises:
            Exception:
                If the disk size cannot be determined
        """
        try:

            total_disk_size = 0

            if self.disk_list == []:
                self.get_disk_list()
                self.get_disk_info()

            for index in range(len(self.disk_list)):
                disk_size = int(self.disk_dict[index]['sizeGb'])
                total_disk_size += disk_size

            # for disk in self.disk_list:
            #     disk_size = int(self.disk_dict[disk]['sizeGb'])
            #     total_disk_size += disk_size

            self.vm_size = total_disk_size

        except Exception as err:
            self.log.exception("Exception in get_disk_size: {0}".format(str(err)))
            raise Exception(err)

    def _get_vm_guid(self):
        """
        gets the GUID of VM

        Raises:
            Exception:
                If the guid cannot be retrieved
        """
        try:
            self.log.info("Getting the size information for VM %s" % self.vm_name)
            data = self._vm_info
            self.guid = data['id']

        except Exception as err:
            self.log.exception("Exception in get_vm_guid: {0}".format(str(err)))
            raise Exception(err)

    def _get_IP_address(self):
        """
        gets the internal and external  (if it has one) IPs of the VM

        Raises:
            Exception:
                if the ip information cannot be retrieved
        """

        try:
            data = self._vm_info
            for internal in data['networkInterfaces']:
                self.ip = internal['networkIP']
                if 'accessConfigs' in internal:
                    for external in internal['accessConfigs']:
                        if 'natIP' in external:
                            self.ip = external['natIP']
                        else:
                            self.external_IPs = None
                else:
                    self.external_IPs = None

        except Exception as err:
            self.log.exception("Exception in get_vm_ips: {0}".format(str(err)))
            raise Exception(err)

    def _get_OS_type(self):
        """
        Updates the OS type

        Raises:
            Exception:
                if the os type cannot be retrieved
        """
        try:
            self.log.info("Getting the os disk info for VM %s" % self.vm_name)
            data = self._vm_info['disks'][0]['licenses'][0]
            disk_os = data.rpartition('/')[2]
            if "windows" in disk_os:
                self.guest_os = "windows"
            # include for unix VMs also
            self.log.info("OS type is : %s" % self.guest_os)

        except Exception as err:
            self.log.exception("Exception in GetOSType: {0}".format(str(err)))
            raise Exception(err)

    def _get_subnet_ID(self):
        """
        Update the subnet ID for VM

        Raises:
            Exception:
                if the subent id cannot be colelcted
        """
        try:
            data = self._vm_info
            if self.subnet_IDs != []:
                self.subnet_IDs = []
            for network in data['networkInterfaces']:
                subnet_url = network['subnetwork']
                subnet_data = self.Hvobj._execute_google_api(subnet_url)
                self.subnet_IDs.append(subnet_data['ipCidrRange'])

        except Exception as err:
            self.log.exception("Exception in GetSubnetID: {0}".format(str(err)))
            raise Exception(err)

    def _get_cpu_memory(self):
        data = self.Hvobj._execute_google_api(self.google_vmurl)
        machine_type = data['machineType'].rpartition('/')[2]
        if 'custom' in machine_type:
            self.no_of_cpu = machine_type.split('-')[1]
            self.memory = int(machine_type.split('-')[2]) / 1024
        else:
            machine_info = self.Hvobj._execute_google_api(data["machineType"])
            cpu_info = machine_info['description'].split(",")
            for cpu in cpu_info:
                if "vCPU" in cpu:
                    cpu_info = cpu.split()[0]
                    break
            self.no_of_cpu = int(cpu_info)
            self.memory = machine_info['memoryMb'] / 1024

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
        """
        fetches properties of the VM
        Args:
            prop                (str):  Basic - Basic properties of VM like HostName,
                                                especially the properties with which
                                                VM can be added as dynamic content

                                        All   - All the possible properties of the VM

            os_info             (bool): To fetch os info or not

            force_update - to refresh all the properties always
                    True : ALways collect  properties
                    False: refresh only if properties are not initialized

        Raises:
            Exception:
                if failed to update all the properties of the VM
        """
        try:
            self.power_on()
            if self._vm_info:
                if not self._basic_props_initialized or force_update:
                    self._get_vm_guid()
                    self._get_disk_list()
                    self._get_disk_info()
                    self._get_disk_size()
                    self._get_status_of_vm()
                    self._get_cpu_memory()
                    self._get_IP_address()
                    self._get_nic_info()
                if prop == 'All':
                    self._get_IP_address()
                    self._get_nic_info()
                    self._get_subnet_ID()
                    self._get_OS_type()
                    self.vm_guest_os = self.guest_os
                    self.get_drive_list()
                    self._get_disk_list()
                    self._get_disk_info()
            else:
                self.log.info("VM info was not collected for this VM")
        except Exception as err:
            self.log.exception("Failed to update the VM Properties: {0}".format(str(err)))
            raise Exception(err)

    def compute_distribute_workload(self, proxy_obj, vm, **kwargs):
        """
        compares the location of proxy and vm then creates two list matching zone and region
        Args:
            proxy_obj     (dict)           :  A dictionary of proxy as key and proxy object as value

            vm            (str) : The source vm name
        """
        self.workload_vm = kwargs.get("restore_vm")
        vm_dict = self.hvobj.vm_id_dict
        flag = 0
        for project in vm_dict:
            for vm_info in vm_dict[project]:
                if vm_info[0] == self.workload_vm:
                    vm_zone = vm_info[2]
                    flag = 1
                    break
            if flag:
                break
        self.workload_vm_zone = vm_zone
        for proxy in proxy_obj:
            if proxy != self.workload_vm:
                if proxy_obj[proxy][1] == vm_zone:
                    self.workload_zone_proxy.append(proxy)
                elif proxy_obj[proxy][0] == vm_zone[:-2]:
                    self.workload_region_proxy.append(proxy)

    def _set_credentials(self, os_name):
        """
        set the credentials for VM by reading the config INI file.
        Overridden because root login is not possible in out of place restored AWS instance.
        """

        # first try root credentials

        if not os_name:
            os_name = self.get_os_name(self.vm_hostname)
            self.guest_os = os_name
            # os_name = "windows"
        if os_name.lower() == "windows":
            sections = VirtualServerUtils.get_details_from_config_file(os_name.lower())
            user_list = sections.split(",")
            incorrect_usernames = []
            for each_user in user_list:
                self.user_name = each_user.split(":")[0]
                self.password = VirtualServerUtils.decode_password(each_user.split(":")[1])
                try:
                    vm_machine = machine.Machine(self.vm_hostname,
                                                 username=self.user_name,
                                                 password=self.password)
                    if vm_machine:
                        self.machine = vm_machine
                        return
                except:
                    incorrect_usernames.append(each_user.split(":")[0])
            self.log.exception("Could not create Machine object for machine : '{0}'! "
                               "The following user names are incorrect: {1}"
                               .format(self.vm_hostname, incorrect_usernames))

        # if root user doesn't work (for Linux only), try root1 or any other user with key
        # Pass the RSA key in the keys field in the config.json file
        else:
            sections = VirtualServerUtils.get_details_from_config_file('gcp_linux')
            user_list = sections.split(",")
            keys = VirtualServerUtils.get_details_from_config_file('gcp_linux', 'keys')
            key_list = keys.split(",")
            incorrect_usernames = []
            for each_user in user_list:
                self.user_name = each_user.split(":")[0]
                self.password = each_user.split(":")[1]
                # self.key_filename = key_list
                try:
                    run_as_sudo = self.user_name == "root1"
                    vm_machine = machine.Machine(self.vm_hostname, username=self.user_name,
                                                 password=self.password, key_filename=key_list,
                                                 run_as_sudo = run_as_sudo)
                    if vm_machine:
                        self.machine = vm_machine
                        return
                except:
                    incorrect_usernames.append((each_user.split(":")[0]))

            self.log.exception("Could not create Machine object for machine : '{0}'! "
                               "The following user names are incorrect: {1}"
                               .format(self.vm_hostname, incorrect_usernames))
