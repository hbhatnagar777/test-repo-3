# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Amazon vm"""

import time
from AutomationUtils import machine
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils import VirtualServerUtils
from AutomationUtils import logger
from enum import Enum


class AmazonVM(HypervisorVM):
    """
    This is the main file for all  Amazon VM operations
    """

    # pylint: disable=too-many-instance-attributes
    # VM property mandates many attributes.
    def __init__(self, hvobj, vm_name, **kwargs):
        """
        Initialization of AWS vm properties

        Args:
            hvobj               (obj):  Hypervisor Object

            vm_name             (str):  Name of the VM
        """
        super(AmazonVM, self).__init__(hvobj, vm_name)
        self.host_machine = machine.Machine()
        self.server_name = hvobj.server_host_name
        self.vm_name = vm_name
        self.instance = None
        self._aws_access_key = self.hvobj._aws_access_key
        self._aws_secret_key = self.hvobj._aws_secret_key
        self.aws_region = self.hvobj.aws_region  # TODO: check if this can be removed
        self.instance, self.guid, self.ip, self.guest_os, self.volumes, self._disk_list, self.disk_count, \
        self.no_of_cpu, self.vpc, self.subnet, self.nic, self.ec2_instance_type, \
        self.iam = (None for _ in range(13))
        self.security_groups = []
        self.disk_dict, self.tags, self.volume_tags = ({} for _ in range(3))
        self.memory = 0
        self.iam = None
        self.iam_role_id = None
        self._basic_props_initialized = False
        self.connection = self.hvobj.connection
        self.volume_props = {}
        self.availability_zone = None
        self.kwargs = kwargs
        if self.hvobj.check_vms_exist([self.vm_name]):
            self.update_vm_info()
        # TODO: don't need this right now
        self.workload_host_proxies = []
        self.termination_protection = None
        self.boot_mode = None
        self.vm_tags = None

    class LiveSyncVmValidation(object):
        def __init__(self, vmobj, schedule, replicationjob=None, live_sync_options=None):
            self.vm = vmobj
            self.schedule = schedule
            self.replicationjob = replicationjob
            self.log = logger.get_log()

        def __eq__(self, other):
            """validates livesync replication"""

            config_val = (int(self.vm.vm.no_of_cpu) == int(other.vm.vm.no_of_cpu) and
                          int(self.vm.vm.disk_count) == int(other.vm.vm.disk_count) and
                          int(self.vm.vm.memory) == int(other.vm.vm.memory))
            if not config_val:
                return False

            # network and security group validation
            scheduleprops = self.schedule.virtualServerRstOptions
            schdetails = scheduleprops['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vmdetails in schdetails:
                if vmdetails['name'] == self.vm.vm.vm_name:
                    if 'nics' in vmdetails:
                        if vmdetails['nics'][0]['subnetId'] != other.vm.vm.subnet:
                            return False
                    if 'securityGroups' in vmdetails:
                        if vmdetails['securityGroups'][0]['groupId'] != other.vm.vm.security_groups[0]:
                            return False

            return self.vm.vm.ec2_instance_type == other.vm.vm.ec2_instance_type

    class PowerState(Enum):
        """ Power state code for AWS"""
        pending = 0
        running = 16
        shutting_down = 32
        terminated = 48
        stopping = 64
        stopped = 80

    def _set_credentials(self, os_name):
        """
        set the credentials for VM by reading the config INI file.
        Overridden because root login is not possible in out of place restored AWS instance.
        """

        # first try root credentials
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

        # if root user doesn't work (for Linux only), try ec2-user with key
        sections = VirtualServerUtils.get_details_from_config_file('aws_linux')
        user_list = sections.split(",")
        keys = VirtualServerUtils.get_details_from_config_file('aws_linux', 'keys')
        key_list = keys.split(",")
        incorrect_usernames = []
        for key in key_list:
            if not self.host_machine.check_directory_exists(key):
                self.log.warning("file \"{0}\" not found".format(key))
                key_list.remove(key)
        for each_user in user_list:
            self.user_name = each_user.split(":")[0]
            self.password = each_user.split(":")[1]
            # self.key_filename = key_list
            try:
                run_as_sudo = self.user_name in ["ec2-user", "ubuntu"]
                vm_machine = machine.Machine(self.vm_hostname, username=self.user_name,
                                             password=self.password, key_filename=key_list,
                                             run_as_sudo=run_as_sudo)
                if vm_machine:
                    self.machine = vm_machine
                    return
            except:
                incorrect_usernames.append((each_user.split(":")[0]))

        self.log.exception("Could not create Machine object for machine : '{0}'! "
                           "The following user names are incorrect: {1}"
                           .format(self.vm_hostname, incorrect_usernames))

    def clean_up(self):
        """
        Clean up the VM and ts reources.

        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned

        """

        try:

            self.log.info("Terminating VMs after restore/conversion")
            self.delete_vm()

        except Exception as exp:
            self.log.exception("Exception in Cleanup")
            raise Exception("Exception in Cleanup:" + str(exp))

    def _get_vm_info(self):
        """
        Get the basic or all or specific properties of VM

        Args:
                prop                (str):  basic, All or specific property like Memory

                extra_args          (str):  Extra arguments needed for property listed by ","

        Raises:
            Exception:
                if failed to get all the properties of the VM

        """
        try:
            self.aws_region = self.kwargs.get('region', self.hvobj.kwargs.get('region', None))
            if not self.aws_region:
                self.aws_region = self.hvobj.get_instance_region(self.vm_name)

            _resource = self.connection.resource('ec2', self.aws_region)
            instances = _resource.instances.filter(Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [self.vm_name]
                },
            ],
                                                    DryRun=False)
            count = 0
            for instance in instances:
                if instance.state['Code'] != self.PowerState.terminated.value:
                    count = count + 1
                    if count > 1:
                        self.log.Error('multiple instances with same name')
                        raise Exception('multiple instances with same name')
                    self.guid = instance.id
                    self.power_state = instance.state['Code']
                    if self.power_state == self.PowerState.running.value:
                        self.ip = instance.private_ip_address
                    self.guest_os = instance.platform
                    instance_nic = instance.network_interfaces
                    for nic in instance_nic:
                        self.availability_zone = nic.subnet.availability_zone
                    if not self.guest_os:
                        self.guest_os = 'unix'
                    self.instance = instance
            if count == 0:
                self.log.error('No Instance found by this name : {0}'.format(self.vm_name))
                raise Exception('No Instance found by this name')
            self._basic_props_initialized = True
        except Exception as err:
            self.log.exception("Failed to Get basic info of the instance")
            raise Exception(err)

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False, **kwargs):
        """
        Fetches all the properties of the VM

        Args:
            prop                (str):  Basic - Basic properties of VM like HostName,
                                                especially the properties with which
                                                VM can be added as dynamic content

                                        All   - All the possible properties of the VM

            os_info             (bool): To fetch os info or not

            force_update        (bool): to refresh all the properties always
                    True : Always collect  properties
                    False: refresh only if properties are not initialized

            **kwargs                         : Arbitrary keyword arguments

        Raises:
            Exception:
                if failed to update all the properties of the VM

        """
        try:
            if not self._basic_props_initialized or force_update:
                self._get_vm_info()
                self.set_security_groups()
                self.set_volume_tags()
                self.set_volume_props()
                self.get_other_detail()
                self.disk_count = len(self.disk_list)

            if self.power_state == 48:
                self.log.error(self.vm_name, "has been terminated. Unable to create "
                                             "VMHelper object")
                return

            if os_info or prop == 'All':
                if self.power_state in (0, 32, 64):
                    time.sleep(120)
                if self.power_state == 80:
                    self.power_on()
                    self.ip = self.instance.private_ip_address
                if not kwargs.get('power_off_unused_vms'):
                    self.vm_guest_os = self.guest_os
                    self.get_drive_list()
                self.get_memory()

        except Exception as err:
            self.log.exception("Failed to Get info of the instance")
            raise Exception(err)

    def power_on(self):
        """
        Power on the VM.

        Raises:
            Exception:
                When power on fails or unexpected error code is returned

        """

        try:
            if self.instance.state['Code'] != self.PowerState.terminated.value:
                if self.instance.state['Code'] != self.PowerState.running.value:
                    self.instance.start()
                    self.wait_for_vm_to_boot()
            else:
                self.log.error("Power On failed. Instance has been TERMINATED already")
            if self.instance.state['Code'] != self.PowerState.running.value:
                raise Exception("Instance not powered On")
        except Exception as exp:
            self.log.exception("Exception in PowerOn")
            raise Exception("Exception in PowerOn:" + str(exp))

    def power_off(self):
        """
        Power off the VM.

        Raises:
            Exception:
                When power off fails or unexpected error code is returned

        """

        try:
            if self.instance.state['Code'] != self.PowerState.terminated.value:
                if self.instance.state['Code'] != self.PowerState.stopped.value:
                    self.instance.stop()
                    time.sleep(180)
                    self.log.error("Instance has been powered off successfully")
                else:
                    self.log.error("Instance has been powered off already")
            else:
                self.log.error("Instance has been terminated already")

            if self.instance.state['Code'] != self.PowerState.stopped.value:
                raise Exception("Instance not powered off")
        except Exception as exp:
            self.log.exception("Exception in Power Off")
            raise Exception("Exception in Power Off:" + str(exp))

    def delete_vm(self):
        """
        Terminates the ec2 instance.

        Raises:
            Exception:
                When deleting the instance fails or unexpected error code is returned

        """

        try:
            if self.instance.state['Code'] != self.PowerState.stopped.value:
                if self.instance.state['Code'] == self.PowerState.running.value:
                    self.power_off()
            self.instance.terminate()
            time.sleep(60)
            if self.instance.state['Code'] != self.PowerState.terminated.value:
                raise Exception("Instance not deleted")
        except Exception as exp:
            self.log.exception("Exception in Delete")
            raise Exception("Exception in Delete:" + str(exp))

    @property
    def disk_list(self):
        """
        To fetch the disk in the VM

        Returns:
            disk_list           (list): List of volumes in AWS instance

        """
        try:
            self.volumes = self.instance.volumes.all()
            self._disk_list = [v.id for v in self.volumes]
            if self._disk_list:
                return self._disk_list
            else:
                return []
        except Exception as exp:
            self.log.exception("Exception in getting disk list")
            raise Exception("Exception in getting disk list" + str(exp))

    def set_volume_props(self):
        """
        To set the volume details of the VM

        Returns:
            volume_props           (dict): dict of volumes an their properties in AWS instance

         Raises:
            Exception:
                When disk properties cannot be fetched
        """
        try:
            self.volumes = self.instance.volumes.all()
            for volume in self.volumes:
                self.volume_props[volume.id] = {}
                self.volume_props[volume.id]['type'] = volume.volume_type
                self.volume_props[volume.id]['key'] = volume.kms_key_id
                self.volume_props[volume.id]['iops'] = volume.iops
                self.volume_props[volume.id]['size'] = volume.size
                self.volume_props[volume.id]['throughput'] = volume.throughput
                if volume.tags:
                    for tag in volume.tags:
                        if tag.get('Key', None):
                            if not tag['Value']:
                                self.volume_name = None
                            else:
                                self.volume_name = tag['Value']

                    if self.volume_name:
                        self.volume_props[volume.id]['volume_name'] = self.volume_name

        except Exception as exp:
            self.log.exception("Exception in getting disk properties")
            raise Exception("Exception in getting disk properties" + str(exp))

    def set_security_groups(self):
        """
        Sets the security groups associated with the AWS ec2 instance

        Raises:
            Exception:
                issues when unable to get the security groups
        """
        try:
            if not self.security_groups:
                for sgi in self.instance.security_groups:
                    self.security_groups.append(sgi['GroupId'])
        except Exception as err:
            self.log.exception("Failed to get security groups")
            raise Exception(err)

    def set_volume_tags(self):
        """
        Sets the tags associated with each volume for the instance and stores in a dict with
        each key as the volume id

        Raises:
            Exception:
                issues when unable to get the tags of a volume
        """
        try:
            if not self.volumes:
                self.volumes = self.instance.volumes.all()
            for _vol in self.volumes:
                _resource = self.connection.resource('ec2', self.aws_region)
                volume = _resource.Volume(_vol.id)
                _tag_dict = {}
                if volume.tags:
                    for _v in volume.tags:
                        _key = _v['Key'].strip()
                        if _key:
                            try:
                                _value = _v['Value'].strip()
                            except IndexError:
                                _value = ''
                        _tag_dict[_v['Key'].strip()] = _v['Value'].strip()
                self.volume_tags[_vol.id] = _tag_dict
        except Exception as err:
            self.log.exception("Failed to get volume tags")
            raise Exception(err)

    def get_other_detail(self):
        """
        Sets the tags associated with each volume for the instance and stores in a dict with
        each key as the volume id

        Raises:
            Exception:
                issues when unable to get the tags of a volume
        """
        try:
            self.volumes = self.instance.volumes.all()
            self.vpc = self.instance.vpc.id
            self.subnet = self.instance.subnet.id
            self.nic = self.instance.network_interfaces[0].id
            self.ec2_instance_type = self.instance.instance_type
            self.security_group_name = self.instance.security_groups[0]['GroupName']

            try:
                self.iam = self.instance.iam_instance_profile['Arn']
                self.iam_role_id = self.instance.iam_instance_profile['Id']
            except TypeError as er:
                self.log.info("No IAM role linked to instance , so setting to None")
                self.iam = None
                self.iam_role_id = None

            self.tags = self.instance.tags
            self.no_of_cpu = self.instance.cpu_options['CoreCount']
            for device in self.instance.block_device_mappings:
                self.disk_dict[device['Ebs']['VolumeId']] = device['DeviceName']
        except Exception as err:
            self.log.exception("Failed to get other detail")
            raise Exception(err)

    def get_memory(self):
        """
        Gets the memory of the vm
        Raises:
            Exception:
                issues when unable to get memory of the vm
        """
        try:
            if self.guest_os.lower() == 'windows':
                _output = self.machine.execute_command(
                    'get-ciminstance -class "cim_physicalmemory" | % {$_.Capacity}')
                self.memory = int(_output.formatted_output)/1024/1024/1024
            else:
                _output = self.machine.execute_command('lsmem')
                _memory = None
                if _output.formatted_output:
                    for _data in _output.formatted_output:
                        if len(_data) == 4:
                            if _data[0] == 'Total' and _data[1] == 'online':
                                _memory = _data[3]
                    if _memory[-1] == 'G':
                        self.memory = float(_memory[:-1]) * 1024
                    else:
                        self.memory = float(_memory[:-1])

        except Exception as err:
            self.log.exception("Failed to fetch memory of the vm: {}".format(self.vm_name))
            raise Exception(err)

    def delete_disks(self, disk_names=None, ignore=False):
        """
        Delete the volumes in the instance

        Args:
            disk_names              (string):   volume name which needs to be deleted

            ignore                  (bool):     Ignores if disk is found/not found

        Returns:
            Status                          : True if successful
                                              False if exception
        Raises:
            Exception:
                if failed to delete the disks of the vm
        """
        try:
            if disk_names:
                _disk_to_delete = disk_names
            else:
                _disk_to_delete = 'del_*'
            disk_found = False
            self.set_volume_tags()
            import re
            for volume in self.volumes:
                if re.match(_disk_to_delete, self.volume_tags[volume.id]['Name']):
                    _response = volume.detach_from_instance(
                        Force=True,
                        InstanceId=self.guid,
                        DryRun=False
                    )
                    if _response['State'] != 'detaching':
                        raise Exception('Not able to de attach the volume {}'.format(
                            self.volume_tags[volume.id]['Name']))
                    else:
                        self.log.info("Sleeping for 30 seconds for disk detaching")
                        time.sleep(30)
                        if volume.state != 'available':
                            raise Exception('Not able to detach volume {}'.format(
                                self.volume_tags[volume.id]['Name']))
                    self.log.info('{} De attached'.format(self.volume_tags[volume.id]['Name']))
                    _ = volume.delete(
                        DryRun=False)
                    disk_found = True
            if not disk_found:
                self.log.info('Disk {} could not '
                              'be found. Ignore: {}'.format(_disk_to_delete, ignore))
                if not ignore:
                    raise RuntimeError('Disk {} could not '
                                       'be found.'.format(_disk_to_delete))
            return True
        except Exception as err:
            self.log.exception("exception in deleting the disk")
            raise err

    def is_powered_on(self):
        """Returns: True, if VM is powered on, False otherwise"""
        try:
            # Reload madatory to update the power state
            self.instance.reload()
            return self.instance.state['Code'] == self.PowerState.running.value
        except Exception as err:
            self.log.exception("Exception in checking power status")
            raise err

    def compute_distribute_workload(self, proxy_obj, workload_vm, job_type='restore', **kwargs):
        """
                Computes host and datastore match proxies for the workload_vm
        Args:
            proxy_obj       (dict): A dictionary of proxy as key and proxy location details as value
            workload_vm     (str): The backed up VM
            job_type        (str): Type of job - backup / restore

        """
        restore_validation_options = kwargs.get('restore_validation_options', None)
        self.log.info("Restore validation options")
        self.log.info(restore_validation_options)
        self.workload_vm = workload_vm
        if job_type.lower() == 'restore':
            for proxy in proxy_obj:
                if proxy != workload_vm:
                    self.log.info("Proxy Location")
                    self.log.info(proxy_obj[proxy][1])
                    self.log.info("Workload VM location")
                    self.log.info(restore_validation_options[workload_vm]['data_center'])
                    if proxy_obj[proxy][1] == restore_validation_options[workload_vm]['data_center']:
                        self.workload_host_proxies.append(proxy)
        self.log.info("Workload Host Proxies")
        self.log.info(self.workload_host_proxies)

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options=None, backup_option=None):
            if type(vmobj) == AmazonVM:
                self.vm = vmobj
                self.vm_name = vmobj.vm_name
            else:
                self.vm = vmobj.vm
                self.vm_name = vmobj.vm.vm_name

            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            """compares the source vm and restored vm"""
            try:
                if not self.validate_zone(self, other, self.vm_restore_options):
                    raise Exception("Availability zone mismatch")
                if not self.validate_tags(self, other, self.vm_restore_options):
                    raise Exception("Tags mismatch")
                if not self.validate_instance_type(self, other, self.vm_restore_options):
                    raise Exception("Instance type mismatch")
                if not self.validate_volume_name(self, other, self.vm_restore_options):
                    raise Exception("Volume Name mismatch")
                if not self.validate_volume_tag(source_vm = other, dest_vm = self):
                    raise Exception("Volume tags mismatch")
                if not self.validate_volume_type(self, other, self.vm_restore_options):
                    raise Exception("Volume type mismatch")
                if not self.validate_iops(self, other, self.vm_restore_options):
                    raise Exception("Volume IOPS mismatch")
                if not self.validate_throughput(self, other, self.vm_restore_options):
                    raise Exception("Volume Throughput mismatch")
                if self.vm.iam != other.vm.iam:
                    raise Exception("IAM role mismatch")
                if self.vm_restore_options.aws_vpc_recovery_validation:
                    if not self.aws_vpc_recovery_validation(self, other, self.vm_restore_options):
                        raise Exception("AWS VPC recovery validation failed")
                    return True
                if not self.validate_nic(self, other, self.vm_restore_options):
                    raise Exception("NIC mismatch")
                if not self.validate_volume_key(self, other, self.vm_restore_options):
                    raise Exception("Volume key mismatch")
                if not self.validate_security_group(self, other, self.vm_restore_options):
                    raise Exception("Security group mismatch")
                self.log.info("Validation successful")
                return True
            except Exception as exp:
                self.log.exception("Exception in Vm Validation")
                raise Exception("Exception in Vm Validation:" + str(exp))

        def validate_tags(self, source_vm, dest_vm, vm_restore_options):
            """
            Validates the tags of source and restored instances

            Args:

                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                vm_restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            if not vm_restore_options.vm_tags:
                import copy
                tags1 = copy.deepcopy(source_vm.vm.tags)
                tags2 = copy.deepcopy(dest_vm.vm.tags)
                if not source_vm.vm.validate_name_tag or not dest_vm.vm.validate_name_tag:
                    tags1 = list(filter(lambda i: i['Key'].lower() != 'name', tags1))
                    tags1 = list(filter(lambda i: i['Key'].lower() != '_gx_ami_', tags1))
                    tags2 = list(filter(lambda i: i['Key'].lower() != 'name', tags2))
                tags1 = sorted(tags1, key=lambda i: i['Key'])
                tags2 = sorted(tags2, key=lambda i: i['Key'])
                self.log.info('tags1 :{}'.format(tags1))
                self.log.info('tags2 :{}'.format(tags2))
                return tags1 == tags2
            #In case we add the instance tags from configure restore options then we will compare with input json and restored instance vm tags
            else:
                import copy
                tags1 = copy.deepcopy(vm_restore_options.vm_tags)
                tags1 = [{'Key': d['name'], 'Value': d['value']} for d in tags1]
                tags2 = copy.deepcopy(dest_vm.vm.tags)
                if not source_vm.vm.validate_name_tag or not dest_vm.vm.validate_name_tag:
                    tags1 = list(filter(lambda i: i['Key'].lower() != 'name', tags1))
                    tags1 = list(filter(lambda i: i['Key'].lower() != '_gx_ami_', tags1))
                    tags2 = list(filter(lambda i: i['Key'].lower() != 'name', tags2))
                tags1 = sorted(tags1, key=lambda i: i['Key'])
                tags2 = sorted(tags2, key=lambda i: i['Key'])
                self.log.info('tags1 :{}'.format(tags1))
                self.log.info('tags2 :{}'.format(tags2))

        def validate_volume_tag(self, source_vm, dest_vm):
            """
            validating source_volume tags and destination volume tags

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

            returns:
                (bool)     :True, if the validation is successful

            """
            source_volumes = source_vm.vm.disk_list
            destination_volumes = dest_vm.vm.disk_list

            def get_list_volume_tags(volumes):
                volume_list_tags = {}
                volume_details = {}
                for volume in volumes:
                    volume_details[volume] = self.vm.hvobj.get_volume_details(volume)
                    volume_list_tags[volume] = volume_details[volume]['Volumes'][0]['Tags']
                return volume_list_tags

            source_vol_tags = get_list_volume_tags(source_volumes)
            dest_vol_tags = get_list_volume_tags(destination_volumes)

            def normalize_tags(tags):
                # Sort the list of dictionaries by the 'Key' and then by 'Value' to ensure order
                normalized = {}
                for key in tags:
                    sorted_list = sorted(tags[key], key=lambda x: (x['Key'], x['Value']))
                    normalized[key] = sorted_list
                return normalized

            source_instance_volume_tags = normalize_tags(source_vol_tags)
            destination_instance_volume_tags = normalize_tags(dest_vol_tags)

            # Print normalized dictionaries
            self.log.info("Source Volume Tags :")
            for iteration, (key, value) in enumerate(source_instance_volume_tags.items()):
                self.log.info(f"{key}: {value}")

            self.log.info("Destination Volume Tags :")
            for iteration, (key, value) in enumerate(destination_instance_volume_tags.items()):
                self.log.info(f"{key}: {value}")

            tag_count = 0
            for volume_id in source_instance_volume_tags:
                value = source_instance_volume_tags[volume_id]
                for volume_value in destination_instance_volume_tags:
                    if value == destination_instance_volume_tags[volume_value]:
                        tag_count += 1

            return tag_count == len(destination_instance_volume_tags)

        def validate_zone(self, source_vm, dest_vm, restore_options):
            """
            Validates the availability zone of source and restored instances

            Args:

                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            if restore_options is not None and restore_options.availability_zone is not None:
                if dest_vm.vm.availability_zone == restore_options.availability_zone or restore_options.availability_zone == 'Auto':
                    return True
            else:
                if source_vm.vm.availability_zone == dest_vm.vm.availability_zone:
                    return True
            return False

        def validate_security_group(self, source_vm, dest_vm, restore_options):
            """
            Validates the security groups of the source and restored instances

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            if restore_options is not None and restore_options.security_groups is not None:
                if restore_options.security_groups == "--Auto Select--":
                    return True
                else:
                    if dest_vm.vm.security_groups == restore_options.security_groups:
                        return True

            else:
                if source_vm.vm.security_groups == dest_vm.vm.security_groups:
                    return True
            return False

        def validate_instance_type(self, source_vm, dest_vm, restore_options):
            """
            Validates the instance type of source and restored instance

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            if restore_options is not None and restore_options.ec2_instance_type is not None:
                if restore_options.ec2_instance_type == "Automatic":
                    return True
                else:
                    if dest_vm.vm.ec2_instance_type == restore_options.ec2_instance_type:
                        return True
            else:
                if source_vm.vm.ec2_instance_type == dest_vm.vm.ec2_instance_type:
                    return True
            return False

        def validate_volume_key(self, source_vm, dest_vm, restore_options):
            """
            Validates the volume key of restored instance

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            _source_key_list = []
            _dest_key_list = []
            for _vol in source_vm.vm.volume_props.keys():
                _source_key_list += [source_vm.vm.volume_props[_vol]['key']]
            for _vol in dest_vm.vm.volume_props.keys():
                _dest_key_list += [dest_vm.vm.volume_props[_vol]['key']]
            if not restore_options.restore_validation_options.get('encryptionKey',None):
                if set(_source_key_list) == set(_dest_key_list):
                    return True
                return False
            else:
                for _key in _dest_key_list:
                    if _key != restore_options.restore_validation_options['encryptionKeyArn']:
                        return False
                return True

        def validate_volume_name(self, source_vm, dest_vm, restore_options):
            """
            Validates the volume type of restored instance

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            _dest_list = []
            _source_list = []
            source_volume_name = all('volume_name' in props for props in source_vm.vm.volume_props.values())
            if source_volume_name:
                for _vol in source_vm.vm.volume_props.keys():
                    _source_list += [source_vm.vm.volume_props[_vol]['volume_name']]
                for _vol in dest_vm.vm.volume_props.keys():
                    _dest_list += [dest_vm.vm.volume_props[_vol]['volume_name']]
                if not restore_options.restore_validation_options: #Source Volume has name, Performing OOP Restore without Edit
                    if set(_source_list) == set(_dest_list):
                        return True
                    return False
                else:
                    _source_list = ['Del' + _vol for _vol in
                                    _source_list]  # Source Volume has name, Performing OOP Restore with edit
                    if set(_source_list) == set(_dest_list):
                        return True
                    return False
            else:
                if restore_options.restore_validation_options: #Source Volume Name is empty, Performing OOP Restore with Edit
                    for _vol in source_vm.vm.volume_props.keys():
                        _source_list.append('Del' + _vol)
                    for _vol in dest_vm.vm.volume_props.keys():
                        _dest_list += [dest_vm.vm.volume_props[_vol]['volume_name']]
                    if set(_source_list) == set(_dest_list):
                        return True
                    return False
                else:
                    for _vol in source_vm.vm.volume_props.keys():  #Source Volume Name is empty, Performing OOP Restore without Edit
                        _source_list.append(source_vm.vm.volume_props[_vol].get('volume_name', ''))
                    for _vol in dest_vm.vm.volume_props.keys():
                        _dest_list.append(dest_vm.vm.volume_props[_vol].get('volume_name', ''))
                    if set(_source_list) == set(_dest_list):
                        return True
                    return False

        def validate_volume_type(self, source_vm, dest_vm, restore_options):
            """
            Validates the volume type of restored instance

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            _source_list = []
            _dest_list = []
            for _vol in source_vm.vm.volume_props.keys():
                _source_list += [source_vm.vm.volume_props[_vol]['type']]
            for _vol in dest_vm.vm.volume_props.keys():
                _dest_list += [dest_vm.vm.volume_props[_vol]['type']]
            if not restore_options.restore_validation_options.get('volumetype',None):
                if set(_source_list) == set(_dest_list):
                    return True
                return False
            else:
                for _key in _dest_list:
                    restored_volume_type = restore_options.restore_validation_options['volumetype'].split()[-1].strip('()')
                    if _key != restored_volume_type:
                        return False
                return True

        def validate_iops(self, source_vm, dest_vm, restore_options):
            """
            Validates the IOPS of restored instance

            Args:
                source_vm (object): VM object of the source VM
                dest_vm (object): VM object of the restored VM
                restore_options (object): restore options object

            Returns:
                bool: True if the validation is successful, False otherwise
            """
            source_iops_list = []
            dest_iops_list = []
            for _vol in source_vm.vm.volume_props.keys():
                source_iops_list += [source_vm.vm.volume_props[_vol]['iops']]
            for _vol in dest_vm.vm.volume_props.keys():
                dest_iops_list += [dest_vm.vm.volume_props[_vol]['iops']]
            if not restore_options.restore_validation_options.get('iops',None):
                if set(source_iops_list) == set(dest_iops_list):
                    return True
                return False
            else:
                for _key in dest_iops_list:
                    if str(_key) != restore_options.restore_validation_options['iops']:
                        return False
                return True

        def validate_throughput(self, source_vm, dest_vm, restore_options):
            """
            Validates the throughput of the restored instance

            Args:
                source_vm (object): VM object of the source VM
                dest_vm (object): VM object of the restored VM
                restore_options (object): restore options object

            Returns:
                bool: True if the validation is successful, False otherwise
            """
            source_throughput_list = []
            dest_throughput_list = []
            for _vol in source_vm.vm.volume_props.keys():
                source_throughput_list += [source_vm.vm.volume_props[_vol]['throughput']]
            for _vol in dest_vm.vm.volume_props.keys():
                dest_throughput_list += [dest_vm.vm.volume_props[_vol]['throughput']]
            if not restore_options.restore_validation_options.get('throughput', None):
                if set(source_throughput_list) == set(dest_throughput_list):
                    return True
                return False
            else:
                for _key in dest_throughput_list:
                    if str(_key) != restore_options.restore_validation_options['throughput']:
                        return False
                return True

        def validate_nic(self, source_vm, dest_vm, restore_options):
            """
            Validates the nic of restored instance

            Args:
                source_vm (object)  : VM object of the source VM

                dest_vm (object)    : VM object of the restored VM

                restore_options (object): restore options object

            returns:
                (bool)     :True, if the validation is successful
            """
            if restore_options is not None and restore_options.network is not None:
                if restore_options.network == "New Network Interface":
                    return True
                else:
                    if dest_vm.vm.nic == restore_options.network:
                        return True
            else:
                if restore_options is None or source_vm.vm.nic == dest_vm.vm.nic:
                    return True
            return False

        def validate_restore_workload(self, proxy_obj):
            """ Restore Proxy Workload Distribution Validation

                   Args :
                        proxy_obj       (dict) : Dictionary with proxy name as key and proxy location tuple as value

                   Raises:
                        Exception:
                                 When Restore Workload Validation fails

            """
            instance_region = self.vm.hvobj.get_instance_region(self.vm.workload_vm)[1]
            proxy_name = self.vm.hvobj.VMs[self.vm.workload_vm].proxy_name
            proxy_region = proxy_obj[proxy_name][1]
            if self.vm.workload_host_proxies:
                if proxy_name in self.vm.workload_host_proxies:
                    if instance_region == proxy_region:
                        self.log.info(
                            "Restore Validation successful for "
                            "Instance [{0}] Region: [{1}] Proxy [{2}] Region: [{3}] (Region Match)"
                            .format(self.vm.workload_vm, instance_region, proxy_name, proxy_region))
                else:
                    raise Exception("Failure in Restore Workload validation for Instance [{0}] Region[{1}] "
                                    "Proxy [{2}] Region: [{3}] not part of "
                                    "workload_host_proxies".format(self.vm.workload_vm, instance_region, proxy_name,
                                                                   proxy_region))
            else:
                self.log.info("Restore Validation successful for VM [{0}] "
                              "Region: [{1}] Proxy [{2}] Region: [{3}] (Any)"
                              .format(self.vm.workload_vm, instance_region, proxy_name, proxy_region))

        def aws_vpc_recovery_validation(self, source_vm, dest_vm, restore_options):
            """
            Validates network configurations like VPC, Subnet, Security Groups, NIC, InternetGateways, NATGateways
            EgressOnlyInternetGateways, VPNGateways, TransitGatewayAttachments, TransitGateway in vpc recovery cases

            Args:
                source_vm (object)        : VM object of the source VM

                dest_vm (object)          : VM object of the restored VM

                restore_options (object)  : restore options object

            Returns:
                bool -- True if validation succeeded else raises Exception
            """
            try:
                dest_network = self.vm.hvobj.collect_vpc_network_configuration(dest_vm.vm, dest_vm.vm.aws_region)
                source_network = self.vm.hvobj.collect_vpc_network_configuration(source_vm.vm, source_vm.vm.aws_region)
                network_fields = ['Vpc', 'Subnet', 'Dhcp', 'Nic', 'SecurityGroups', 'InternetGateways', 'NATGateways'
                            'EgressOnlyInternetGateways', 'VPNGateways', 'TransitGatewayAttachments', 'TransitGateway']
                for field in network_fields:
                    if source_network[field] != dest_network[field]:
                        self.log.info(f"{field} validation failed")
                        return False
                if not self.vm.hvobj.verify_prefix_lists(source_vm.vm.aws_region, dest_vm.vm.aws_region,
                                                         restore_options.restore_job_id):
                    self.log.info("Prefix list validation failed")
                    return False
                return True
            except Exception as exp:
                self.log.info("Exception occurred while validating network entities" + str(exp))
                return False

    class AutoScaleVmValidation(object):
        """ Class for auto scale validation  """

        def __init__(self, vm_obj, auto_scale_region_info):
            """ Initializes the AutoScaleVmValidation class
            Args :
              vm_obj :  vm object of auto proxy to be validated
               auto_scale_region_info (dict): dictionary of auto scale configuration


            """
            self.vm = vm_obj
            self.auto_scale_region_info = auto_scale_region_info
            self.log = logger.get_log()

        def validate_proxy_resource_cleanup(self):
            """
            Validates if auto scale proxy resources are cleaned up

            Returns:
                cleanup_status (bool): True if validation is successful else False
            """
            cleanup_status = True

            # Create resources dictionary
            resources = {
                'network_interfaces': [self.vm.nic],
                'volumes': list(self.vm.disk_dict.keys())
            }

            resource_status = self.vm.hvobj.check_resource_exists(region=self.vm.aws_region, **resources)

            for resource_name, resource_ids in resources.items():
                for resource_id in resource_ids:
                    exists = resource_status.get(resource_name, {}).get(resource_id, False)
                    if exists:
                        self.log.error(f"{resource_name.capitalize().replace('_', ' ')} {resource_id} not cleaned up.")
                        cleanup_status = False
                    else:
                        self.log.info(
                            f"{resource_name.capitalize().replace('_', ' ')} {resource_id} has been cleaned up.")

            return cleanup_status

        def validate_auto_scale_proxy_configuration(self, autoscale_policy):
            """
                Validates auto proxy created has the valid configuration

            Args:
                autoscale_policy : Autoscale policy

            Returns:
                config_status (bool): True if validation is successful else False
            """
            config_status = True
            region_config_info = self.auto_scale_region_info.get(self.vm.aws_region)
            iam_role = autoscale_policy.get('roleInfo').get('name', None)
            if self.vm.subnet != region_config_info.get('subnetId'):
                self.log.error("Specified subnet : {0} , subnet proxy is connected : {1} \
                . Validation failed".format(self.vm.nic_details[0].get('subnet_uri'),
                                            region_config_info.get('subnetId')))
                config_status = False

            if region_config_info.get("securityGroups", [{}])[0].get("groupId", None) and \
                    [security_group['groupId'] for security_group in
                     region_config_info.get("securityGroups", [])] != self.vm.security_groups:
                self.log.error(
                    "Specified networkSecurityGroups: {0} , configured networkSecurityGroups: {1}. Validation failed"
                    .format(
                        [security_group['groupId'] for security_group in region_config_info.get("securityGroups", [])],
                        self.vm.security_groups))
                config_status = False

            if iam_role and self.vm.iam.split('/')[-1] \
                    != iam_role:
                self.log.error("Specified IAM Role {0}, configured {1} ,\
                 validation failed".format(iam_role, self.vm.resource_group_name))
                config_status = False

            return config_status

    class DrValidation(HypervisorVM.DrValidation):
        """class for DR validation"""

        def __init__(self, vmobj, vm_options, **kwargs):
            """ Initializes the DR_validation class
            """
            super().__init__(vmobj, vm_options, **kwargs)

        def validate_cpu_count(self, **kwargs):
            """Validate CPU count to make sure they honor the restore options"""
            if self.vm_options.get('instanceType'):
                return
            if self.vm_options.get('cpuCount') != self.vm.no_of_cpu:
                raise Exception(f"Expected CPU count {self.vm_options.get('cpuCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.no_of_cpu}")
            self.log.info("Validated CPU Count")

        def validate_memory(self, **kwargs):
            """Validate memory size to make sure it honors the restore options"""
            if self.vm_options.get('instanceType'):
                return
            if self.vm_options.get('memory') != self.vm.memory:
                raise Exception(f"Expected memory size {self.vm_options.get('memory')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.memory}")
            self.log.info("Validated Memory")

        def validate_disk_count(self, **kwargs):
            """Validate the number of disks"""
            if self.vm_options.get('diskCount') != self.vm.disk_count:
                raise Exception(f"Expected disk count: {self.vm_options.get('diskCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.disk_count}")
            self.log.info("Validated Disk Count")

        def validate_instance_type(self, **kwargs):
            """Validate the instance type"""
            if self.vm_options.get('instanceType') != self.vm.ec2_instance_type:
                raise Exception(f"Expected disk count: {self.vm_options.get('instanceType')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.ec2_instance_type}")
            self.log.info("Validated Instance Type")

        def validate_network_adapter(self, **kwargs):
            """Validate the network adapter"""
            _nic_count = len([self.vm.nic]) if isinstance(self.vm.nic, str) else len(self.vm.nic)
            if self.vm_options.get('nicCount') != _nic_count:
                raise Exception(f"Expected NIC: {self.vm_options.get('nic')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.nic}")
            self.log.info("Validated Network Adapter")

        def validate_availability_zone(self, **kwargs):
            """validate the availability zone"""
            if self.vm_options.get('availability_zone') != self.vm.availability_zone:
                raise Exception(f"Expected availability_zone: {self.vm_options.get('availability_zone')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.availability_zone}")
            self.log.info("Validated Availability Zone")

        def validate_security_groups(self, **kwargs):
            """validate the security groups"""
            security_group_names = [sg.get('GroupName', None)
                                    for sg in self.vm.instance.security_groups]
            if self.vm_options.get('security_groups') != security_group_names:
                raise Exception(f"Expected security_groups: {self.vm_options.get('security_groups')} not observed on"
                                f" VM {self.vm.vm_name}: {security_group_names}")
            self.log.info("Validated Security Groups")

        def validate_vpc(self, **kwargs):
            """validate the vpc"""
            vpc_name_or_id = next((tag.get('Value') for tag in self.vm.instance.vpc.tags if tag.get('Key') == 'Name'), self.vm.instance.vpc.id)
            if self.vm_options.get('vpc') != vpc_name_or_id:
                raise Exception(f"Expected vpc: {self.vm_options.get('vpc')} not observed on"
                                f" VM {self.vm.vm_name}: {vpc_name_or_id}")
            self.log.info("Validated VPC")

        def validate_subnet(self, **kwargs):
            """validate the subnet"""
            subnet_name_or_id = next((tag.get('Value') for tag in self.vm.instance.subnet.tags if tag.get('Key') == 'Name'), self.vm.instance.subnet.id)
            if self.vm_options.get('subnet') != subnet_name_or_id:
                raise Exception(f"Expected subnet: {self.vm_options.get('subnet')} not observed on"
                                f" VM {self.vm.vm_name}: {subnet_name_or_id}")
            self.log.info("Validated Subnet")

        def validate_nic(self, **kwargs):
            """validate the nic"""
            if self.vm_options.get('nic') != 'New Network Interface' and self.vm_options.get('nic') != self.vm.nic:
                raise Exception(f"Expected NIC: {self.vm_options.get('nic')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.nic}")
            self.log.info("Validated NIC")

        def validate_iam_role(self, **kwargs):
            """validate IAM role"""
            if self.vm_options.get('iam_role') and (self.vm_options.get('iam_role') != self.vm.instance.iam_instance_profile.get('Id')):
                raise Exception(f"Expected IAM role : {self.vm_options.get('iam_role')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.instance.iam_instance_profile.get('Id')}")
            self.log.info("Validated IAM role")

        def validate_dependent_resource_cleanup(self, **kwargs):
            """
            Validates if the dependent resources are cleaned up

            Args:
                kwargs:
                    1. volumes (bool) : Volume cleanup validation (default - True)
                    2. network_interfaces (bool) : Network interface cleanup validation (default - True)

            Returns:
                True (bool) : If the provided resources have been cleaned up
            
            Raises:
                Exception:
                    If one or more resources are NOT cleaned up
            """
            # disk_list contains the updated value => Empty
            resources = {
                'volumes': list(self.vm.disk_dict.keys()),
                'network_interfaces': [self.vm.nic]
            }
            resource_status = self.vm.hvobj.check_resource_exists(
                region=self.vm.aws_region, **resources)

            for resource_name in resources.keys():
                if any(resource_status.get(resource_name).values()):
                    dangling_resources = [resource_id for resource_id, status in resource_status.get(
                        resource_name).items() if status == True]
                    raise Exception(
                        f"{resource_name} -> {dangling_resources} is/are NOT cleaned up")
                else:
                    self.log.info(
                        f"{resource_name} -> {list(resource_status.get(resource_name).keys())} have been cleaned up")
            return True

        def validate_warm_sync(self, **kwargs):
            """ Validate Warm sync is applied on hypervisors"""
            super().validate_warm_sync(**kwargs)
            return self.validate_dependent_resource_cleanup() if kwargs.get('dependent_resources_cleanup', False) else True

        def advanced_validation(self, other=None, **kwargs):
            """Advanced Validation"""
            self.validate_availability_zone() if kwargs.get('availability_zone', True) else None
            self.validate_security_groups() if kwargs.get('security_groups', True) else None
            self.validate_vpc() if kwargs.get('vpc', True) else None
            self.validate_subnet() if kwargs.get('subnet', True) else None
            self.validate_nic() if kwargs.get('nic', True) else None
            self.validate_iam_role() if kwargs.get('iam_role', True) else None
            return True

        def validate_dvdf(self, **kwargs):
            """ DVDF validation"""
            vm_provisioned = self.vm.hvobj.check_vms_exist([self.vm.vm_name])
            if vm_provisioned:
                raise Exception(f"VM [{self.vm.vm_name}] exists on hypervisor before failover,"
                                f" even when DVDF is enabled")

        def validate_dvdf_on_failover(self, **kwargs):
            """DVDF validation on Failover"""
            vm_provisioned = self.vm.hvobj.check_vms_exist([self.vm.vm_name])
            if not vm_provisioned:
                raise Exception(f"VM [{self.vm.vm_name}] does NOT exist on hypervisor after failover,"
                                f" when DVDF is enabled")


    class VmConversionValidation:
        def __init__(self, vm_obj, vm_restore_options):
            self.vm = vm_obj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            try:
                # Availability Zone
                if self.vm.availability_zone != self.vm_restore_options.availability_zone:
                    raise Exception("Availability zone mismatch")

                # Security Group
                if self.vm.security_group_name != self.vm_restore_options.security_groups:
                    if self.vm_restore_options.security_groups != "--Auto Select--":
                        raise Exception("Security group mismatch")

                # Instance Type
                if self.vm.ec2_instance_type != self.vm_restore_options.ec2_instance_type:
                    if self.vm_restore_options.ec2_instance_type != "Automatic":
                        raise Exception("Instance type mismatch")

                # Volume Key
                if self.vm_restore_options.restore_validation_options.get('encryptionKey'):
                    _dest_key_list = []
                    for _vol in self.vm.volume_props.keys():
                        _dest_key_list += [self.vm.volume_props[_vol]['key']]
                    for _key in _dest_key_list:
                        if _key != self.vm_restore_options.restore_validation_options['encryptionKeyArn']: ## here each key in the dest_key_list must be equal to the 'encryptionKeyArn' of the source_vm ?
                            raise Exception("Volume key mismatch")

                # Volume Type
                if self.vm_restore_options.restore_validation_options.get('volumetype'):
                    _dest_list = []
                    for _vol in self.vm.volume_props.keys():
                        _dest_list += [self.vm.volume_props[_vol]['type']]
                    for _key in _dest_list:
                        restored_volume_type = self.vm_restore_options.restore_validation_options['volumetype'].split()[-1].strip('()')
                        if _key != restored_volume_type:
                            raise Exception("Volume type mismatch")

                # Volume IOPS
                if self.vm_restore_options.restore_validation_options.get('iops'):
                    _dest_list = []
                    for _vol in self.vm.volume_props.keys():
                        _dest_list += [self.vm.volume_props[_vol]['iops']]
                    for _key in _dest_list:
                        if str(_key) != self.vm_restore_options.restore_validation_options['iops']:
                            raise Exception("Volume IOPS mismatch")

                # Volume Throughput
                if self.vm_restore_options.restore_validation_options.get('throughput'):
                    _dest_list = []
                    for _vol in self.vm.volume_props.keys():
                        _dest_list += [self.vm.volume_props[_vol]['throughput']]
                    for _key in _dest_list:
                        if str(_key) != self.vm_restore_options.restore_validation_options['throughput']:
                            raise Exception("Volume Throughput mismatch")

                # Validate Nic
                if self.vm.nic != self.vm_restore_options.network:
                    if self.vm_restore_options.network != "New Network Interface":
                        raise Exception("NIC mismatch")

                #validate instance boot mode
                if self.vm_restore_options.instance_boot_mode:
                    if self.vm.boot_mode != self.vm_restore_options.instance_boot_mode:
                        raise Exception("Boot Mode Mismatch")


                # Validate Tags
                # For tags Add Logic For Azure TO AWS
                return True
            except Exception as exp:
                self.log.exception("Exception in VM Conversion Validation")
                raise Exception("Exception in VM Conversion Validation: " + str(exp))
