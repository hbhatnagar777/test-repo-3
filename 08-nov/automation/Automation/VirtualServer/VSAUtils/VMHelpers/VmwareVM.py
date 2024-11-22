# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Does all the Operation for Vmware vm
    VmwareVM:

            _get_vm_host()                  -   Get the host of the VM among the servers list

            _get_vm_info()                  -   Get the particular  information of VM

            _get_disk_list()                -   Gets the disk list opff the VM

            mount_vmdk()                    -   Mount the VMDK and return the drive letter

            un_mount_vmdk()                 -   Unmount the VMDK mounted provided the path

            get_disk_in_controller()       -   get the disk in controller attached

            get_disk_path_from_pattern()   -   get the list of disk from pattern

            power_off()                     -   power off the VM

            power_on()                      -   Power on the VM

            delete_vm()                     -   Delete the VM

            update_vm_info()                -   Updates the VM info

            live_browse_vm_exists()         -   Checks if live vm exists

            live_browse_ds_exists()         -   Checks if live browse Datastrore exists

"""
import requests
import time
import os
import re
import collections
import ipaddress
from AutomationUtils import machine
from AutomationUtils import logger
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from pyVmomi import vim, vmodl, pbm, VmomiSupport, SoapStubAdapter


class VmwareVM(HypervisorVM):
    """
    This is the main file for all  Vmware VM operations
    """

    def __init__(self, hvobj, vm_name, **kwargs):
        """
        Initialization of vmware vm properties

        Args:
            hvobj               (obj):  Hypervisor Object

            vm_name             (str):  Name of the VM
                **kwargs             :  Dict of all key-worded arguments to be passed to update_vm_info
                         vm_boot_skip: (bool): Whether to skip the boot and IP validation - Default: False
        """
        super(VmwareVM, self).__init__(hvobj, vm_name)
        self.host_machine = machine.Machine()
        self.server_name = hvobj.server_host_name
        self.vm_props_file = "GetVMwareProps.ps1"
        self.prop_dict = {
            "server_name": self.server_name,
            "user": self.host_user_name,
            "pwd": self.host_password,
            "vm_name": self.vm_name,
            "extra_args": "$null"
        }
        self.vm_obj, self.guid, self.ip, self.guest_os, self.host_name, self.power_state, \
        self.esx_host, self.tools, self.template, \
        self.network_name, self._disk_count, self._nic_count, self._no_cpu, self._memory = (None,) * 14
        self.nics, self.datastores = ([],) * 2
        self.disk_dict, self._disk_provision_list = ({},) * 2
        self.disk_validation = True
        self._basic_props_initialized = False
        self.guest_credentials = None
        self.workload_host_proxies = []
        self.workload_datastore_proxies = []
        self.no_ip_state = False
        self.tags = collections.defaultdict(list)
        self._storage_policy = None
        vm_boot_skip = kwargs.get('vm_boot_skip', False)
        self.update_vm_info(vm_boot_skip=vm_boot_skip)

    class VmValidation(object):
        def __init__(self, VmValidation_obj, vm_restore_options=None, **kwargs):
            self.vm = VmValidation_obj.vm
            self.vm_name = self.vm.vm_name
            self.hvobj = self.vm.hvobj
            self.vm_restore_options_obj = vm_restore_options
            self.log = logger.get_log()

            self.kwargs_options = kwargs

        def __eq__(self, other):
            """compares the source vm and restored vm"""

            if self.kwargs_options.get('backup_option'):
                power_off_unused_vms = self.kwargs_options['backup_option'].power_off_unused_vms
            else:
                power_off_unused_vms = None
            other.vm.update_vm_info(force_update=True, power_off_unused_vms=power_off_unused_vms)
            if self.vm.nic_count == other.vm.nic_count:
                self.log.info("Network count matched")
            else:
                self.log.error("Network count failed")
                return False
            if self.vm_restore_options_obj.validate_vm_storage_policy:
                self.validate_vm_storage_policy_compliance(self.vm, other.vm)
            if self.vm.disk_validation:
                self.log.debug(
                    'Source vm:{} , disk details: {}'.format(self.vm.vm_name,
                                                             self.vm.get_disk_provision))
                self.log.debug(
                    'Restored vm:{} , disk details: {}'.format(other.vm.vm_name,
                                                               other.vm.get_disk_provision))
                if self.vm_restore_options_obj.disk_option == 'Original':
                    if collections.Counter(
                            list(self.vm.get_disk_provision.values())) != collections.Counter(
                        list(other.vm.get_disk_provision.values())):
                        source_count = collections.Counter(self.vm.get_disk_provision.values())
                        dest_count = collections.Counter(other.vm.get_disk_provision.values())
                        if source_count['Thin'] != dest_count['Thin'] or ((source_count[
                                                                               'Thick Eager Zero'] +
                                                                           source_count[
                                                                               'Thick Lazy Zero']) != (
                                                                                  dest_count[
                                                                                      'Thick Eager Zero'] +
                                                                                  dest_count[
                                                                                      'Thick Lazy Zero'])):
                            self.log.error("Disk type match failed")
                            return False
                elif self.vm_restore_options_obj.disk_option == 'Thin':
                    if not all(_type == self.vm_restore_options_obj.disk_option for _type in
                               other.vm.get_disk_provision.values()):
                        self.log.error("Disk type match failed")
                        return False
                else:
                    for _type in other.vm.get_disk_provision.values():
                        if _type not in ('Thick Eager Zero', 'Thick Lazy Zero'):
                            self.log.error("Disk type match failed")
                            return False
                self.log.info("Disk type matched")
            return True

        def validate_restore_workload(self, proxy_obj):
            """ Restore Proxy Workload Distribution Validation

                   Args :
                        proxy_obj       (dict) : Dictionary with proxy name as key and proxy location tuple as value

                   Raises:
                        Exception:
                                 When Restore Workload Validation fails

            """

            vm_host = self.vm.hvobj.find_vm(self.vm.workload_vm)[1]
            proxy_name = self.vm.proxy_name
            proxy_host = proxy_obj[proxy_name][1]

            if self.vm.workload_host_proxies:
                if proxy_name in self.vm.workload_host_proxies:
                    self.log.info(
                        "Restore Validation successful for "
                        "VM [{0}] ESX host: [{1}] Proxy [{2}] ESX host: [{3}] (Host Match)"
                            .format(self.vm.workload_vm, vm_host, proxy_name, proxy_host))
                else:
                    raise Exception("Failure in Restore Workload validation")
            elif self.vm.workload_datastore_proxies:
                if proxy_name in self.vm.workload_datastore_proxies:
                    self.log.info("Restore Validation successful for VM [{0}] "
                                  "ESX host: [{1}] Proxy [{2}]  ESX host: [{3}] (Datastore Match)"
                                  .format(self.vm.workload_vm, vm_host, proxy_name, proxy_host))
                else:
                    raise Exception("Failure in Restore Workload validation")
            else:
                self.log.info("Restore Validation successful for VM [{0}] "
                              "ESX host: [{1}] Proxy [{2}] ESX host: [{3}] (Any)"
                              .format(self.vm.workload_vm, vm_host, proxy_name, proxy_host))

        def validate_vm_storage_policy_compliance(self, source_obj, restore_obj):
            """
            Validates the Storage Policy compliance of the Restored VM

            Args:
                source_obj (obj) -- Source VM Object

                restore_obj (obj) -- Restored VM Object

            Raises:
               Exception:
                   If validation fails.

            """
            try:
                # Identify the Storage Policies attached to the source and restored VM
                source_vm_storage_policy = source_obj.storage_policy
                dest_vm_storage_policy = restore_obj.storage_policy

                # If Storage Policy is None,
                # then the VM would be attached to the default vCenter policy - Datastore Default
                if not source_vm_storage_policy:
                    source_vm_storage_policy = 'Datastore Default'
                if not dest_vm_storage_policy:
                    dest_vm_storage_policy = 'Datastore Default'

                self.log.info('Storage Policies : Source [{}] Destination [{}]'.format(source_vm_storage_policy,
                                                                                       dest_vm_storage_policy))
                # Check if VM Storage Policy is provided as an input or not
                if self.vm_restore_options_obj._vm_storage_policy:
                    # Compare the input Storage Policy and the destination Storage Policy
                    if self.vm_restore_options_obj._vm_storage_policy == dest_vm_storage_policy:
                        self.log.info(
                            "Success : VM {} restored with Storage Policy [{}]".format(restore_obj.vm_name,
                                                                                     dest_vm_storage_policy))
                    else:
                        raise Exception(
                            "VM {} restored with different Storage Policy. Expected [{}] , but Found [{}]".
                                format(restore_obj.vm_name, self.vm_restore_options_obj._vm_storage_policy,
                                       dest_vm_storage_policy))
                else:
                    # Compare the source Storage Policy and the destination Storage Policy
                    if source_vm_storage_policy == dest_vm_storage_policy:
                        self.log.info(
                            "Success : VM {} restored with Storage Policy [{}]".format(restore_obj.vm_name,
                                                                                     dest_vm_storage_policy))
                    else:
                        raise Exception(
                            "VM {} restored with different Storage Policy. Expected [{}] , but Found [{}]".
                                format(restore_obj.vm_name, self.vm_restore_options_obj._vm_storage_policy,
                                       dest_vm_storage_policy))

                # Check the compliance of the restored VM's datastore with that of the Storage Policy
                compliance_result = source_obj.hvobj.check_vm_storage_policy_compliance(dest_vm_storage_policy,
                                                                                        restore_obj.datastores[0])
                if compliance_result:
                    self.log.info(
                        "VM Storage Policy compliance check passed for VM [{}] Storage Policy [{}] Datastore [{}]".
                            format(restore_obj.vm_name, dest_vm_storage_policy, restore_obj.datastores[0]))

                else:
                    self.log.warning(
                        "VM Storage Policy compliance check failed for VM [{}] Storage Policy [{}] Datastore [{}]".
                            format(restore_obj.vm_name, dest_vm_storage_policy, restore_obj.datastores[0]))
            except Exception as exp:
                self.log.exception('Exception in storage policy compliance validation')
                raise exp

    class VmConversionValidation(object):
        def __init__(self, vmobj, vm_restore_options):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            """compares the restored vm with user inputs"""
            return other.vm.network_name == self.vm_restore_options._network and \
                   other.vm.esx_host == self.vm_restore_options._host and \
                   other.vm.datastore.split(",")[0] == self.vm_restore_options._datastore

    class LiveSyncVmValidation(object):
        def __init__(self, vmobj, schedule, replicationjob=None, live_sync_options=None):
            self.vm = vmobj
            self.schedule = schedule
            self.replicationjob = replicationjob
            self.live_sync_options = live_sync_options
            self.live_sync_direct = False
            if self.live_sync_options:
                self.live_sync_direct = self.live_sync_options.live_sync_direct
                self.live_sync_name = self.live_sync_options.live_sync_name
            self.log = logger.get_log()

        def __eq__(self, other):
            """ validates vm replicated through livesync """
            try:
                if (not self.live_sync_direct) and ('__GX_BACKUP__' not in other.vm.vm.VMSnapshot):
                    self.log.info('snapshot validation failed')
                    return False
                self.log.info('snapshot validation successful')
                config_val = (int(self.vm.vm.no_of_cpu) == int(other.vm.vm.no_of_cpu) and
                              int(self.vm.vm.disk_count) == int(other.vm.vm.disk_count) and
                              int(self.vm.vm.memory) == int(other.vm.vm.memory))
                if self.live_sync_direct:
                    self.vm._validate_snapshot_pruning(self.live_sync_name)
                if not config_val:
                    return False
                return True
            except Exception as err:
                self.log.exception(
                    "Exception at Validating  {0}".format(err))
                raise err

    @property
    def no_of_cpu(self):
        """Returns (int): the number of CPU for the VM"""
        if not self.vm_obj:
            return None
        if self._no_cpu:
            return self._no_cpu
        else:
            return self.vm_obj.summary.config.numCpu

    @no_of_cpu.setter
    def no_of_cpu(self, value):
        """
        Set the number of cpu
        Args:
            value       (int):      number of cpu

        """
        if not value:
            self._no_cpu = self.vm_obj.summary.config.numCpu
        else:
            self._no_cpu = value

    @property
    def memory(self):
        """Returns (float): The memory size in GB"""
        if not self.vm_obj:
            return None
        if self._memory:
            return self._memory
        else:
            return float(self.vm_obj.summary.config.memorySizeMB / 1024)

    @memory.setter
    def memory(self, value):
        """
        Set the size of memory
        Args:
            value       (int):      memory size in GB

        """
        if not value:
            self._memory = float(self.vm_obj.summary.config.memorySizeMB / 1024)
        else:
            self._memory = value

    @property
    def disk_count(self):
        """Returns (int): The number of disks attached to the VM"""
        if not self.vm_obj:
            return 0
        if self._disk_count:
            return self._disk_count
        else:
            return len(self.vm_obj.layout.disk)

    @disk_count.setter
    def disk_count(self, value):
        """
        Set the disk count of the vm
        Args:
            value       (int):      disk count of the vm

        """
        if not value:
            self._disk_count = len(self.vm_obj.layout.disk)
        else:
            self._disk_count = value

    @property
    def disk_list(self):
        """
        To fetch the disk in the VM

        Returns:
            disk_list           (list): List of disk in VM
                                        e.g:[vm1.vmdk]

        """
        _temp_disk_list = {}
        for ds in self.vm_obj.layout.disk:
            _dp = ds.diskFile[0]
            _dn = _dp.split("/")[1]
            _temp_disk_list[_dp] = _dn
        if _temp_disk_list:
            _disk_list = _temp_disk_list.keys()
        else:
            _disk_list = []
        return _disk_list

    @property
    def nic_count(self):
        """Returns (int): The number of NICs attached to the VM"""
        if not self.vm_obj:
            return 0
        if self._nic_count:
            return self._nic_count
        else:
            return len(self.vm_obj.guest.net)

    @nic_count.setter
    def nic_count(self, value):
        """
        Set the nic count of the vm
        Args:
            value       (int):      nic count of the vm

        """
        if not value:
            self._nic_count = len(self.vm_obj.guest.net)
        else:
            self._nic_count = value

    @property
    def rdm_details(self):
        """
        To fetch the disk in the VM

        Returns:
            _rdm_dict           (dict): Dictionary of disks and its details of the disk

        """
        _rdm_dict = {}
        for dev in self.vm_obj.config.hardware.device:
            if isinstance(dev, self.hvobj.vim.vm.device.VirtualDisk):
                f_name = dev.backing.fileName
                disk_mode = dev.backing.diskMode
                if isinstance(dev.backing,
                              self.hvobj.vim.vm.device.VirtualDisk.RawDiskMappingVer1BackingInfo):
                    compatibility_mode = dev.backing.compatibilityMode
                else:
                    compatibility_mode = 'Flat'
                _rdm_dict[f_name] = [f_name, compatibility_mode, disk_mode]
        self.disk_validation = False
        return _rdm_dict

    @property
    def get_disk_provision(self):
        """
        To get the disk provision type
        Returns:
                disk_provision_list            (dict):     Dictionary of disks and their type

        Raises:
            Exception:
                if failed to get the Provision type of the disks
        """
        try:
            if self._disk_provision_list:
                return self._disk_provision_list
            else:
                for dev in self.vm_obj.config.hardware.device:
                    if isinstance(dev, self.hvobj.vim.vm.device.VirtualDisk):
                        if isinstance(dev.backing,
                                      self.hvobj.vim.vm.device.VirtualDisk.RawDiskMappingVer1BackingInfo):
                            _provision = 'Ignore_rdm'
                        else:
                            if dev.backing.thinProvisioned:
                                _provision = 'Thin'
                            else:
                                if dev.backing.eagerlyScrub:
                                    _provision = 'Thick Eager Zero'
                                else:
                                    _provision = 'Thick Lazy Zero'
                        self._disk_provision_list[dev.backing.fileName] = _provision
                return self._disk_provision_list
        except Exception as err:
            self.log.exception("Exception while collecting detail about rdm %s", str(err))
            raise err

    @property
    def get_vm_folder(self):
        """gets the folder name for the vm"""
        # self.log.info("Parent path: {}".format(self.vm_obj.config.files.logDirectory))
        return self.vm_obj.config.files.logDirectory

    @property
    def parent_vm_folder(self):
        """Returns: (str) Gets the parent VM folder name"""
        return self.vm_obj.parent.name

    @property
    def resource_pool_name(self):
        """Returns: (str) Gets the resource pool name of the VM"""
        return self.vm_obj.resourcePool.name

    @property
    def network_names(self):
        """Returns: list(str) the names of all the networks of the VM"""
        return [network.name for network in self.vm_obj.network]

    @property
    def datastore(self):
        """Returns the base datastore of the vm"""
        _datastore = self.get_vm_folder
        _datastore = _datastore[_datastore.find("[") + 1:_datastore.find("]")]
        return _datastore

    @property
    def disk_datastore(self):
        """ Returns (dict)  : VM Disks and associated datastore"""
        disk_datastore_map = {}
        self.get_all_disks_info()
        for disk, info in self.disk_dict.items():
            vmdk_name = disk.split('/')[-1]
            ds_name = info[1]
            disk_datastore_map[vmdk_name.lower()] = ds_name.lower()
        return disk_datastore_map

    @property
    def VMSnapshotTree(self):
        """Return a list of snapshots on the vm"""
        _snaps = list()
        if self.vm_obj.snapshot:
            _snaps.extend(self.snapshot_tree(self.vm_obj.snapshot.rootSnapshotList))
        return _snaps

    @property
    def VMSnapshot(self):
        """Return the snapshot on the vm"""
        _temp_snaps = []
        _snaps = ''
        if self.vm_obj.snapshot:
            _temp_snaps = [snapshot.name for snapshot in self.VMSnapshotTree]
            _snaps = ','.join(_temp_snaps)
        return _snaps

    @property
    def NicName(self):
        _nics = []
        _nic_name = None
        for nic in self.vm_obj.network:
            _nics.append(nic.name)
        _nic_name = ','.join(_nics)
        return _nic_name

    @property
    def guest_ip_rules(self):
        """Returns: (list) The list of IP addresses in the following format:
            {
                "ipAddress": "10.0.0.1",
                "subnetMask": "255.0.0.0",
                "dhcpEnabled": False
            }
        """
        ip_addresses = []
        for nic in self.vm_obj.guest.net:
            if nic.ipConfig is not None and nic.ipConfig.dhcp is not None:
                if ((nic.ipConfig.dhcp.ipv4 is not None and nic.ipConfig.dhcp.ipv4.enable)
                        or (nic.ipConfig.dhcp.ipv6 is not None and nic.ipConfig.dhcp.ipv6.enable)):
                    ip_addresses.append({
                        "ipAddress": "",
                        "subnetMask": "",
                        "dhcpEnabled": True
                    })
                else:
                    for ip in nic.ipConfig.ipAddress:
                        ip_addr = f'{ip.ipAddress}/{ip.prefixLength}'
                        try:
                            ip_address = ipaddress.ip_network(ip_addr, strict=False)
                            ip_addresses.append({
                                "ipAddress": str(ip.ipAddress),
                                "subnetMask": str(ip_address.netmask),
                                "dhcpEnabled": ip.origin == 'dhcp'
                            })
                        except Exception:
                            pass
        return ip_addresses

    @property
    def guest_subnet_mask(self):
        """Returns: (str) the guest subnet mask"""
        ip_preffered = [ip for nic in self.vm_obj.guest.net if nic.ipConfig is not None
                        for ip in nic.ipConfig.ipAddress if ip.state == 'preferred']
        if ip_preffered:
            ip_addr = f'{ip_preffered[0].ipAddress}/{ip_preffered[0].prefixLength}'
            return str(ipaddress.ip_network(ip_addr, strict=False).netmask)
        return None

    @property
    def guest_default_gateways(self):
        """Returns: list(str) the guest default gateway"""
        gateways = []
        for ip_stack in self.vm_obj.guest.ipStack:
            for ip_route in ip_stack.ipRouteConfig.ipRoute:
                if ip_route.gateway.ipAddress:
                    gateways.append(ip_route.gateway.ipAddress)
        return gateways

    @property
    def guest_dhcp_enabled(self):
        """Returns: (bool) True if DHCP field set, False otherwise.
        Note: Can send None values if field not set by hypervisor"""
        ip_preferred = [ip for nic in self.vm_obj.guest.net if nic.ipConfig is not None
                        for ip in nic.ipConfig.ipAddress if ip.state == 'preferred']
        if ip_preferred and ip_preferred[0].origin is not None:
            return ip_preferred[0].origin == 'dhcp'
        return None

    @property
    def guest_hostname(self):
        """Returns: (str) the guest hostname"""
        return self.vm_obj.guest.hostName

    @property
    def guest_dns(self):
        """Returns: list(str) the guest DNS servers"""
        dns_config = []
        for nic in self.vm_obj.guest.ipStack:
            for dns_ip in nic.dnsConfig.ipAddress:
                dns_config.append(dns_ip)
        return dns_config

    @property
    def storage_policy(self):
        """Returns: (str) Storage Policy associated to the VM"""
        if self._storage_policy:
            return self._storage_policy
        else:
            self._storage_policy = self.get_storage_policy()
            return self._storage_policy
    
    def snapshot_tree(self, parent_snapshot):
        """
        Returns: (list) Snapshot tree as a list
        
        Args:
            parent_snapshot : SnapshotTree object

        """
        snapshot_list = []
        for snapshot in parent_snapshot:
            if snapshot.childSnapshotList:
                snapshot_list += self.snapshot_tree(snapshot.childSnapshotList)
            snapshot_list += [snapshot]
        return snapshot_list

    def find_scsi_controller(self, controller_type='VirtualLsiLogicSASController'):
        """Find the associated scsi controller is present in the vm

        Args:
            controller_type  (str)   --  type of scsi controller to look in the vm

        Returns:
            bool    -   boolean value whether the directory exists or not

        """
        _controller_type = f'self.hvobj.vim.vm.device.{controller_type}'
        for dev in self.vm_obj.config.hardware.device:
            if isinstance(dev, eval(_controller_type)):
                return True
        return False

    def get_scsi_controllers(self):
        """
        Function to get SCSI controllers from VM

        Returns:
                scsi_controllers    (list) : List of SCSI controllers
        
        """

        try:
            self.log.info(f"Fetching SCSI controllers info from VM {self.vm_name}.")
            scsi_controllers = []
            for device in self.vm_obj.config.hardware.device:
                if isinstance(device, self.hvobj.vim.vm.device.VirtualSCSIController):
                    scsi_controllers.append(device)
            return scsi_controllers
        except Exception as exp:
            self.log.error(f"Failed with error: {exp}")
            raise exp

    def delete_scsi_controllers(self, scsi_controllers):
        """
        Function to delete extra SCSI controllers from VM
        
        Args:
            scsi_controllers (list[obj]) : VM's SCSI controller list of objects
        
        """

        try:
            self.log.info("Deleting extra SCSI controllers from VM.")
            spec = self.hvobj.vim.vm.ConfigSpec()
            controllers_to_remove = scsi_controllers[1:]

            for controller in controllers_to_remove:
                device_spec = self.hvobj.vim.vm.device.VirtualDeviceSpec()
                device_spec.operation = (
                    self.hvobj.vim.vm.device.VirtualDeviceSpec.Operation.remove
                )
                device_spec.device = controller
                spec.deviceChange.append(device_spec)

            task = self.vm_obj.ReconfigVM_Task(spec)
            task_result = task.info.state

            while task_result == self.hvobj.vim.TaskInfo.State.running:
                task_result = task.info.state
                time.sleep(5)

            if task_result == self.hvobj.vim.TaskInfo.State.success:
                self.log.info("Extra SCSI controllers removed successfully.")
            else:
                raise Exception("Failed to remove extra SCSI controllers.")
        except Exception as exp:
            self.log.error(f"Failed with error: {exp}")
            raise exp

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False, **kwargs):
        """
        Fetches all the properties of the VM

        Args:
            prop                (str):  Basic - Basic properties of VM like HostName,
                                                especially the properties with which
                                                VM can be added as dynamic content

                                        All   - All the possible properties of the VM

            os_info             (bool): To fetch os info or not

            force_update        (bool):  to refresh all the properties always

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
            if self.power_state == 'poweredOff' and self.template:
                self.convert_template_to_vm()
            if os_info or prop == 'All':
                if self.power_state == 'poweredOff' and not kwargs.get(
                        'power_off_unused_vms', None):
                    self.wait_for_vm_to_boot()
                if 'isolated_network' not in kwargs.keys() and not kwargs.get(
                        'power_off_unused_vms'):
                    if not self.no_ip_state:
                        self.vm_guest_os = self.guest_os
                    self.get_drive_list()
                self.esx_host = self.vm_obj.runtime.host.name
                self.tools = self.vm_obj.guest.guestState
                self.nics.clear()
                for nic in self.vm_obj.network:
                    self.nics.append(nic.name)
                self.datastores.clear()
                for ds in self.vm_obj.datastore:
                    self.datastores.append(ds.name)
                self.disk_count = None
                self.nic_count = None
                self.no_of_cpu = None
                self.memory = None
                self._disk_provision_list.clear()
                self._disk_provision_list = self.get_disk_provision
                self.network_name = self.NicName
                self.get_all_disks_info()
        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def is_powered_on(self):
        """returns true if vm is powered else false"""
        self.power_state = self.vm_obj.runtime.powerState
        if self.power_state == 'poweredOn':
            return True
        return False

    def _get_vm_info(self):
        """
        Get the basic or all or specific properties of VM

        Raises:
            Exception:
                if failed to get all the properties of the VM

        """
        try:
            all_vms = self.hvobj.get_content([self.hvobj.vim.VirtualMachine])
            vms = dict(filter(lambda elem: self.vm_name == elem[1], all_vms.items()))
            if len(vms) == 0:
                raise Exception("VM with name {0} doesn't exist".format(self.vm_name))
            elif len(vms) == 1:
                self.vm_obj = next(iter(vms))
            else:
                raise Exception("Multiple VMs exist with name {0}".format(self.vm_name))
            self.guid = self.vm_obj.config.instanceUuid
            self.get_ip()
            self.power_state = self.vm_obj.runtime.powerState
            if 'win' in self.vm_obj.config.guestFullName.lower():
                self.guest_os = 'Windows'
            else:
                self.guest_os = 'Linux'
            self.template = self.vm_obj.config.template
            self._basic_props_initialized = True

        except Exception as err:
            self.log.exception("Failed to Get Basic Properties of the VM: {}".format(self.vm_name))
            raise Exception(err)

    def get_ip(self):
        """
        Fetches the IP of the VM

        Raises:
            Exception:
                When it fails to fetch IP of the vm
        """
        try:
            if self.vm_obj.runtime.powerState == 'poweredOff':
                self.ip = None
            else:
                self.ip = self.vm_obj.summary.guest.ipAddress
                if hasattr(self.vm_obj.guest, 'net'):
                    ip = [ip.ipAddress for nic in self.vm_obj.guest.net if
                          nic.ipConfig is not None and nic.connected
                          for ip in nic.ipConfig.ipAddress if ip.state == 'preferred']
                    if ip:
                        self.ip = ip[0]
                if not VirtualServerUtils.validate_ip(self.ip) and self.vm_name.startswith('del'):
                    self.log.warning("\n########################\n"
                                     "The restored vm didn't got IP. Limited set of operations"
                                     "will be available \n"
                                     "#######################")
                    if not any(True == nic.connected for nic in
                               self.vm_obj.guest.net):
                        self.log.exception("No Network card is attached. Please check full vm restore log")
                    self.log.info("Nic is connected. Not getting IP looks like environment issue."
                                  "Sleeping for 1 minutes for guest tools to come up properly")
                    time.sleep(60)
                    self.no_ip_state = True
        except Exception as err:
            self.log.exception("Failed to Get IP of the VM: {}".format(self.vm_name))
            raise Exception(err)

    def power_on(self):
        """
        Power on the VM.

        Raises:
            Exception:
                When power on failed

        """

        try:
            if self.vm_obj.runtime.powerState in ('poweredOn', 'running'):
                self.log.info("VM {} is already powered ON".format(self.vm_name))
                return
            self.log.info("Powering on the vm {}".format(self.vm_name))
            self.hvobj.wait_for_tasks([self.vm_obj.PowerOn()])
            time.sleep(60)
            self.power_state = self.vm_obj.runtime.powerState

        except Exception as exp:
            raise Exception("Exception in PowerOn:" + str(exp))

    def power_off(self):
        """
        Power off the VM.

        Raises:
            Exception:
                When power off failed

        """

        try:
            def waiting_for_vm_shutdown(vm_obj, timeout_seconds=180):
                seconds_waited = 0
                while seconds_waited < timeout_seconds:
                    seconds_waited += 5
                    time.sleep(5)
                    if vm_obj.runtime.powerState == \
                            self.hvobj.vim.VirtualMachinePowerState.poweredOff:
                        return True
                self.log.error("VM {} is not powered off in the given 3 minutes."
                               "PowerState:".format(self.vm_name, vm_obj.runtime.powerState))
                return False

            if self.vm_obj.runtime.powerState == 'poweredOff':
                self.log.info("VM {} is already powered off".format(self.vm_name))
                return
            self.log.info("Powering off the vm {}".format(self.vm_name))
            self.vm_obj.ShutdownGuest()
            if not waiting_for_vm_shutdown(self.vm_obj):
                raise RuntimeError("Exception in Powering off VM {}".format(self.vm_name))
            self.power_state = self.vm_obj.runtime.powerState

        except Exception as exp:
            raise Exception("Exception in PowerOff:" + str(exp))

    def delete_vm(self):
        """
        Delete the VM.

        Raises:
            Exception:
                When deleting of the vm failed
        """

        try:
            self.log.info("Deleting the vm {}".format(self.vm_name))
            if self.vm_obj.runtime.powerState in ('poweredOn', 'running'):
                self.hvobj.wait_for_tasks([self.vm_obj.PowerOff()])
            self.hvobj.wait_for_tasks([self.vm_obj.Destroy()])

        except Exception as exp:
            self.log.exception("Exception in DeleteVM {0}".format(exp))
            return False

    def convert_vm_to_template(self):
        """
        Convert a vm to template

        Raises:
            Exception:
                if it fails to convert vms to template

        """
        try:
            self.log.info("Converting VM:{} into template".format(self.vm_name))
            if 'poweredOn' in self.vm_obj.runtime.powerState:
                self.power_off()
                time.sleep(60)
            self.vm_obj.MarkAsTemplate()

        except Exception as err:
            self.log.exception("Exception while Converting  vm to template " + str(err))
            raise err

    def convert_template_to_vm(self):
        """
        Convert a template to vm

        Raises:
            Exception:
                if it fails to convert template to vm

        """
        try:
            self._get_vm_info()
            self.log.info("Converting {} into a VM".format(self.vm_name))
            if self.vm_obj.summary.config.template:
                self.vm_obj.MarkAsVirtualMachine(self.vm_obj.runtime.host.parent.resourcePool)
                time.sleep(5)
                self.power_on()
                time.sleep(120)
                self.log.info("Converted {} into a VM Successfully".format(self.vm_name))
            else:
                self.log.Exception("{} is not a template".format(self.vm_name))

        except Exception as err:
            self.log.exception("Exception while Converting  vm to template " + str(err))
            raise err

    def clean_up(self):
        """
        Does the cleanup after the testcase.

        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned

        """

        try:
            self.log.info("Deleting off VMs after restore")
            self.delete_vm()
        except Exception as exp:
            raise Exception("Exception in Cleanup: {0}".format(exp))

    def add_disks(self, disk_size, disk_type='thin'):
        """
        Add disk in the vm
        Args:
            disk_size       (int): Disk size that needs to be added in GB
            disk_type       (string): thin (default)

        Return:
            Status  : True/False
        Raises:
            Exception: if failed to add disk
        """
        try:
            if not isinstance(disk_size, int):
                disk_size = int(disk_size)
            spec = self.hvobj.vim.vm.ConfigSpec()
            unit_number = 0
            for dev in self.vm_obj.config.hardware.device:
                if hasattr(dev.backing, 'fileName'):
                    unit_number = int(dev.unitNumber) + 1
                    if unit_number == 7:
                        unit_number += 1
                    if unit_number >= 16:
                        self.log.error("We don't support this many disks")
                        raise RuntimeError("We don't support this many disks")
                if isinstance(dev, self.hvobj.vim.vm.device.VirtualSCSIController):
                    controller = dev
            dev_changes = []
            new_disk_size = int(disk_size) * 1024 * 1024
            virtual_hdd_spec = self.hvobj.vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.fileOperation = "create"
            virtual_hdd_spec.operation = self.hvobj.vim.vm.device.VirtualDeviceSpec.Operation.add
            virtual_hdd_spec.device = self.hvobj.vim.vm.device.VirtualDisk()
            virtual_hdd_spec.device.backing = self.hvobj.vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == 'thin':
                virtual_hdd_spec.device.backing.thinProvisioned = True
            virtual_hdd_spec.device.backing.diskMode = 'persistent'
            virtual_hdd_spec.device.unitNumber = unit_number
            virtual_hdd_spec.device.capacityInKB = new_disk_size
            virtual_hdd_spec.device.controllerKey = controller.key
            dev_changes.append(virtual_hdd_spec)
            self.log.info("Adding disk of size %s", disk_size)
            spec.deviceChange = dev_changes
            self.hvobj.wait_for_tasks([self.vm_obj.ReconfigVM_Task(spec=spec)])
            self.log.info("%s GB disk added to vm %s", disk_size, self.vm_obj.config.name)

            return True
        except Exception as err:
            self.log.exception("Exception in adding disk to vm")
            raise err

    def delete_disks(self, disk_names=None, ignore=False):
        """
        Delete the disks in the vm

        Args:
            disk_names              (string):   Disk name which needs to be deleted

            ignore                  (bool):     Ignores if the disk is not found


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
                _disk_to_delete = '\w*/del_*'
            disk_found = False
            virtual_hdd_spec = self.hvobj.vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.operation = \
                self.hvobj.vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_hdd_spec.fileOperation = self.hvobj.vim.vm.device.VirtualDeviceSpec. \
                FileOperation.destroy
            spec = self.hvobj.vim.vm.ConfigSpec()
            for dev in self.vm_obj.config.hardware.device:
                if isinstance(dev, self.hvobj.vim.vm.device.VirtualDisk):
                    if re.search(_disk_to_delete,
                                 dev.backing.fileName) or dev.deviceInfo.label == _disk_to_delete:
                        virtual_hdd_spec.device = dev
                        self.log.info("Deleting Disk {}".format(dev.backing.fileName))
                        spec.deviceChange = [virtual_hdd_spec]
                        self.hvobj.wait_for_tasks([self.vm_obj.ReconfigVM_Task(spec=spec)])
                        self.log.info("Disk {} deleted".
                                      format(virtual_hdd_spec.device.backing.fileName))
                        disk_found = True

            if not disk_found:
                self.log.info('Virtual {} could not '
                              'be found. Ignore: {}'.format(_disk_to_delete, ignore))
                if not ignore:
                    raise RuntimeError('Virtual {} could not '
                                       'be found.'.format(_disk_to_delete))
            return True
        except Exception as err:
            self.log.exception("exception in deleting the disk")
            raise err

    def get_all_disks_info(self):
        """
        Gets the disk details for disk filtering

        Raises:
            Exception:
                When it fails to fetch disk disk details
        """
        try:
            self.disk_dict = {}
            for dev in self.vm_obj.config.hardware.device:
                if isinstance(dev, self.hvobj.vim.vm.device.VirtualDisk):
                    _key = dev.key
                    if _key // 32000:
                        _ctr, _id = int(_key % 32000 / 15), _key % 32000 % 15
                        _virtual_device_node = 'NVME ({}:{})'.format(_ctr, _id)
                    elif _key // 16000:
                        _ctr, _id = int(_key % 16000 / 30), _key % 16000 % 30
                        _virtual_device_node = 'SATA ({}:{})'.format(_ctr, _id)
                    elif _key // 2000:
                        _ctr, _id = int(_key % 2000 / 16), _key % 2000 % 16
                        _virtual_device_node = 'SCSI ({}:{})'.format(_ctr, _id)
                    else:
                        _virtual_device_node = None
                    self.disk_dict[
                        dev.backing.fileName] = _virtual_device_node, dev.backing.datastore.name, \
                                                dev.backing.fileName, dev.deviceInfo.label
        except Exception as err:
            self.log.exception("Failed to fetch disk details")
            raise Exception(err)

    def attach_network_adapter(self):
        """
        Attaches network to the vm

        Raises:
            Exception:
                if failed to attache the network

        """
        try:
            for dev in self.vm_obj.config.hardware.device:
                if isinstance(dev, self.hvobj.vim.vm.device.VirtualVmxnet3) or \
                        isinstance(dev, self.hvobj.vim.vm.device.VirtualE1000e):
                    device = dev
                    device.connectable = self.hvobj.vim.vm.device.VirtualDevice.ConnectInfo(
                        connected=True, startConnected=True, allowGuestControl=True)
                    nicspec = self.hvobj.vim.vm.device.VirtualDeviceSpec(device=device)
                    nicspec.operation = self.hvobj.vim.vm.device.VirtualDeviceSpec.Operation.edit
                    config_spec = self.hvobj.vim.vm.ConfigSpec(deviceChange=[nicspec])
                    self.hvobj.wait_for_tasks([self.vm_obj.ReconfigVM_Task(config_spec)])
                    self.log.info("{} attached sucessfully".format(dev.deviceInfo.label))
        except Exception as err:
            self.log.exception("exception in attaching hte network")
            raise err

    def change_num_cpu(self, num_cpu):
        """
        Changes CPU number
        Args:
            num_cpu                     (int): new cpu number

        """
        spec = self.hvobj.vim.vm.ConfigSpec()
        spec.numCPUs = num_cpu
        if self.power_state != 'poweredOff':
            self.power_off()
        self.hvobj.wait_for_tasks([self.vm_obj.ReconfigVM_Task(spec)])

    def change_memory(self, ram_size_gb):
        """
        Changes ram of the vm
        Args:
            ram_size_gb                     (int): new ram of the vm

        Returns:

        """
        spec = self.hvobj.vim.vm.ConfigSpec()
        spec.memoryMB = ram_size_gb * 1024
        if self.power_state != 'poweredOff':
            self.power_off()
        self.hvobj.wait_for_tasks([self.vm_obj.ReconfigVM_Task(spec)])

    def get_vm_tags(self):
        """
        Get's Tag and category of the VM
        Note : VMware's API is messed up. It doesn't have a seperator for categories, but has ',' for tags.
               So we are currently seperating categories by spaces. Ensure that there are no spaces in the category name.

        Raises:
            Exception:
                if failed to fetch tags and category of the vm

        """
        try:
            self.prop_dict["property"] = 'tagsvalidation'
            _ps_path = os.path.join(
                self.utils_path, self.vm_props_file)
            output = self.host_machine.execute_script(_ps_path, self.prop_dict)
            if output.exception:
                self.log.exception(
                    "Cannot get tag and category for the vm {}".format(output.exception))
            tags_names = output.formatted_output.split(";")[0].split("=")[1].strip().split(",")
            tags_category = output.formatted_output.split(";")[1].split("=")[1].strip().split(" ")
            for tag_category, tag_name in zip(tags_category, tags_names):
                self.tags[tag_category].append(tag_name)
        
        except Exception as err:
            self.log.exception("exception in fetching tags and category of the vm")
            raise err

    def assign_tag(self, tag_name, category_name):
        """
        Assigns the tag -> category_name:tag_name to the VM
        If the tag doesn't exist, it will be created

        Args:
            tag_name            (str):  Name of the tag to be added

            category_name       (str):  Name of the category to which the tag belongs
        """
        if self.hvobj.assign_tag_to_vm(tag_name, category_name, self.vm_obj._GetMoId()):
            self.log.info("Tag {}:{} assigned to the VM {}".format(category_name, tag_name, self.vm_name))

    def remove_tag(self, tag_name, category_name):
        """
        Removes the tag -> category_name:tag_name from the VM if it exists

        Args:
            tag_name            (str):  Name of the tag to be removed

            category_name       (str):  Name of the category to which the tag belongs
        """
        if self.hvobj.remove_tag_from_vm(tag_name, category_name, self.vm_obj._GetMoId()):
            self.log.info("Tag {}:{} removed from the VM {}".format(category_name, tag_name, self.vm_name))
    
    def modify_custom_attribute(self, attribute_name, attribute_value):
        """
        Sets the value of an existing custom attribute in the VCenter named 'attribute_name' to 'attribute_value'.

        Args:
            attribute_name          (str):  Name of the custom attribute
            attribute_value         (str):  Value of the custom attribute
        """
        custom_fields_manager = self.hvobj.connection.content.customFieldsManager
        fields = custom_fields_manager.field
        for field in fields:
            if field.name == attribute_name:
                try:
                    custom_fields_manager.SetField(entity=self.vm_obj, key=field.key, value=attribute_value)
                    self.log.info("Custom Attribute {} set to {} for VM {}".format(attribute_name, attribute_value, self.vm_name))
                    return
                except Exception:
                    raise Exception("Failed to set Custom Attribute {} to {} for VM {}".format(attribute_name, attribute_value, self.vm_name))

    def get_custom_attributes(self):
        """
        Gets Custom Attributes of the VM

        Returns: custom_attr                (dict):  custom attributes

        Raises:
            Exception:
                if failed to fetch custom attributes of the VM

        """
        try:
            custom_attributes_id_value = {}

            for field in self.vm_obj.customValue:
                id = field.key
                value = field.value
                custom_attributes_id_value[id] = value

            self.custom_attributes = {} 
            custom_attributes_with_value = {}

            for attr in self.vm_obj.availableField:
                id = attr.key
                name = attr.name
                if custom_attributes_id_value.get(id):
                    self.custom_attributes[name] = custom_attributes_id_value[id]
                    custom_attributes_with_value[name] = custom_attributes_id_value[id]
                else:
                    self.custom_attributes[name] = None
            
            if self.custom_attributes.get("Last Backup"):
                self.custom_attributes.pop("Last Backup")
                custom_attributes_with_value.pop("Last Backup")
            if self.custom_attributes.get("Backup Status"):
                self.custom_attributes.pop("Backup Status")
                custom_attributes_with_value.pop("Backup Status")
            return custom_attributes_with_value

        except Exception as err:
            self.log.exception("Exception in fetching Custom Attributes of the vm")
            raise err
    
    def validate_custom_attributes(self, other_vm, custom_attributes_to_add = dict() , custom_attributes_to_remove = []):
        """
        Validates if
        1. The restored VM has all the custom attributes that the source VM had
        2. The custom attributes that are to be removed are not present in the restored VM
        3. The custom attributes that are to be added are present in the restored VM    

        Args:
            other_vm                        (obj):  VMwareVM object of the other VM(source VM)
            custom_attributes_to_add         (dict): Custom attributes to be added
            custom_attributes_to_remove      (list): Custom attributes to be removed

        Returns:
            (bool)  - True if tags are same else False
        """
        try:
            self.log.info("----- Validating Custom Attributes for restored VM {} with source VM {} -----".format(self.vm_name, other_vm.vm_name))
            source_vm_custom_attributes = other_vm.custom_attributes
            self.get_custom_attributes()
            restore_vm_custom_attributes = self.custom_attributes
            for attribute,value in source_vm_custom_attributes.items():
                if attribute not in restore_vm_custom_attributes:
                    self.log.error("Custom Attribute {} not found in the restored VM".format(attribute))
                    return False
                if attribute in custom_attributes_to_remove:
                    if restore_vm_custom_attributes[attribute] != None:
                        self.log.error("Custom Attribute {} found in the restore VM with value {} which should be removed".format(attribute,restore_vm_custom_attributes[attribute]))
                        return False
                    self.log.info("Custom Attribute {} removed successfully".format(attribute))
                if attribute in custom_attributes_to_add:
                    if restore_vm_custom_attributes[attribute] != custom_attributes_to_add[attribute]:
                        self.log.error("Custom Attrbiute {} found with value {} in the restored VM which should be {}" \
                                       .format(attribute,restore_vm_custom_attributes[attribute],custom_attributes_to_add[attribute]))
                        return False
                    self.log.info("Custom Attribute {} with value {} added successfully".format(attribute,restore_vm_custom_attributes[attribute]))
            self.log.info("Custom Attributes validation successful")
            return True
        except Exception as exp:
            self.log.exception("Exception in Custom Attributes validation")
            raise exp
    
    def validate_tags(self, other_vm, tags_to_add = dict(), tags_to_remove = dict()):
        """
        Validates if
        1. The restored VM has all the tags that the source VM had
        2. Tags that are to be removed are not present in the restored VM
        3. Tags that are to be added are present in the restored VM

        Args:
            other_vm            (obj): VMwareVM object of the other VM(source VM)
            tags_to_add         (dict): Tags to be added
            tags_to_remove      (dict): Tags to be removed
        """
        source_vm_tags = other_vm.tags
        self.get_vm_tags()
        restore_vm_tags = self.tags
        self.log.info("----- Validating Tags for restored VM {} with source VM {} -----".format(self.vm_name, other_vm.vm_name))
        for tag_category in tags_to_add:
            for tag in tags_to_add[tag_category]:
                if tag not in restore_vm_tags.get(tag_category, []):
                    self.log.error("Tag {}: {} is not added to the restored VM".format(tag_category, tag))
                    return False
                self.log.info("Tag {}: {} successfully added to the restored VM".format(tag_category, tag))

        for tag_category in tags_to_remove:
            for tag in tags_to_remove[tag_category]:
                if tag in restore_vm_tags.get(tag_category, []):
                    self.log.error("Tag {}: {} is not removed from the restored VM".format(tag_category, tag))
                    return False
                self.log.info("Tag {}: {} successfully removed from the restored VM".format(tag_category, tag))

        for tag_category in source_vm_tags:
            for tag in source_vm_tags[tag_category]:
                if tag_category in tags_to_remove and tag in tags_to_remove[tag_category]:
                    continue
                if tag_category in tags_to_add and tag in tags_to_add[tag_category]:
                    continue
                if tag not in restore_vm_tags.get(tag_category, []):
                    self.log.error("Tag {}: {} is not present in the restored VM".format(tag_category, tag))
                    return False
        self.log.info("Tags validation successful")
        return True

    def get_vapp_options(self):
        """
        Gets vApp options of the VM

        Returns: vapp_dict                  (dict): vApp options

        Raises:
            Exception:
                if failed to fetch vApp options of the VM
        """
        try:
            container_obj = self.hvobj.get_content([self.hvobj.vim.VirtualMachine])
            vapp = None

            for vm in container_obj:
                if vm.name == self.vm_name:
                    vapp = vm.config.vAppConfig
                    break

            vapp_dict = {}

            vapp_dict.update({'installBootRequired': vapp.installBootRequired})
            vapp_dict.update({'installBootStopDelay': vapp.installBootStopDelay})
            vapp_dict.update({'ovfEnvironmentTransport': sorted(vapp.ovfEnvironmentTransport)})

            ip_assignment = {}
            ip_assignment.update({'supportedAllocationScheme': sorted(vapp.ipAssignment.supportedAllocationScheme)})
            ip_assignment.update({'ipAllocationPolicy': vapp.ipAssignment.ipAllocationPolicy})
            ip_assignment.update({'supportedIpProtocol': sorted(vapp.ipAssignment.supportedIpProtocol)})
            ip_assignment.update({'ipProtocol': vapp.ipAssignment.ipProtocol})
            vapp_dict.update({'ipAssignment': ip_assignment})

            product = {}
            product.update({'key': vapp.product[0].key})
            product.update({'classId': vapp.product[0].classId})
            product.update({'instanceId': vapp.product[0].instanceId})
            product.update({'name': vapp.product[0].name})
            product.update({'vendor': vapp.product[0].vendor})
            product.update({'version': vapp.product[0].version})
            product.update({'fullVersion': vapp.product[0].fullVersion})
            product.update({'vendorUrl': vapp.product[0].vendorUrl})
            product.update({'productUrl': vapp.product[0].productUrl})
            product.update({'appUrl': vapp.product[0].appUrl})
            vapp_dict.update({'product': product})

            vapp_property = {}
            for prop in vapp.property:
                prop_dict = {}

                prop_dict.update({'category': prop.category})
                prop_dict.update({'classId': prop.classId})
                prop_dict.update({'defaultValue': prop.defaultValue})
                prop_dict.update({'description': prop.description})
                prop_dict.update({'dynamicType': prop.dynamicType})
                prop_dict.update({'id': prop.id})
                prop_dict.update({'instanceId': prop.instanceId})
                prop_dict.update({'key': prop.key})
                prop_dict.update({'label': prop.label})
                prop_dict.update({'type': prop.type})
                prop_dict.update({'typeReference': prop.typeReference})
                prop_dict.update({'userConfigurable': prop.userConfigurable})
                prop_dict.update({'value': prop.value})

                vapp_property.update({prop.key: prop_dict})

            vapp_dict.update({'property': vapp_property})

            return vapp_dict

        except Exception as err:
            self.log.exception("Exception in fetching vApp options of the vm")
            raise err

    def get_drs_settings(self):
        """
        Get DRS Settings associated to the VM

        Returns:
            drs_settings_dict        (dict): Dictionary of DRS settings

        Raises:
            Exception:
                if failed to fetch DRS settings of the VM
        """
        def fetch_overrides(cluster_obj):
            """
            Fetches VM Overrides for the VM

            Args:
                cluster_obj        (vim): Cluster object on which the VM is hosted

            Returns:
                overrides_of_vm     (dict): Contains the VM overrides
            """
            overrides = cluster_obj.configurationEx.drsVmConfig
            overrides_of_vm = {}
            for override in overrides:
                if override.key.name == self.vm_name:
                    overrides_of_vm.update({"enabled": override.enabled})
                    overrides_of_vm.update({"behavior": override.behavior})
                    break
            return overrides_of_vm

        def fetch_groups(cluster_obj):
            """
            Fetches VM Groups for the VM

            Args:
                cluster_obj        (vim): Cluster on which the VM is hosted

            Returns:
                concerned_groups     (dict): Contains the groups with backup VM
            """
            groups = cluster_obj.configurationEx.group
            concerned_groups = {}
            for group in groups:
                group_dict = {}
                try:
                    if len(group.vm) > 0:
                        for vm in group.vm:
                            if vm.name == self.vm_name:
                                group_dict.update({"name": group.name})
                                group_dict.update({"uniqueID": group.uniqueID})
                                group_dict.update({"userCreated": group.userCreated})
                                group_vm_list = []
                                for vm1 in group.vm:
                                    group_vm_list.append(vm1.name)
                                group_dict.update({"vm": sorted(group_vm_list)})
                                concerned_groups.update({group.name: group_dict})
                                break
                except AttributeError:
                    pass
            return concerned_groups

        def fetch_rules(cluster_obj, concerned_groups):
            """
            Fetches VM rules for the VM

            Args:
                cluster_obj        (vim): Cluster on which the VM is hosted

                concerned_groups     (dict): Contains the groups with backup VM

            Returns:
                concerned_rules     (dict): Contains the rules associated with backup VM
            """
            rules = cluster_obj.configurationEx.rule
            concerned_rules = {}
            for rule in rules:
                rule_type = fetch_rule_type(rule)
                rule_info = fetch_rules_info(rule, rule_type, concerned_groups)
                if rule_info:
                    concerned_rules.update({rule.name: rule_info})
            return concerned_rules

        def fetch_rules_info(rule, rule_type, concerned_groups):
            """
            Fetches VM Groups for the VM

            Args:
                rule                 (vim): Cluster on which the VM is hosted

                rule_type            (str): Type of rule

                concerned_groups     (dict): Contains the groups with backup VM

            Returns:
                rule_dict            (dict): Contains the info of the passed rule
            """
            rule_dict = {}

            type1 = 'ClusterAffinityOrAntiAffinityRuleSpec'
            type2 = 'ClusterDependencyRuleInfo'
            type3 = 'ClusterVmHostRuleInfo'

            if rule_type == type1:
                vm_list = []
                for vm1 in rule.vm:
                    vm_list.append(vm1.name)
                if self.vm_name in vm_list:
                    rule_dict.update({"vm": sorted(vm_list)})
                else: return None
            elif rule_type == type2:
                if rule.vmGroup in concerned_groups or rule.dependsOnVmGroup in concerned_groups:
                    rule_dict.update({"vmGroup": rule.vmGroup})
                    rule_dict.update({"dependsOnVmGroup": rule.dependsOnVmGroup})
                else: return None
            elif rule_type == type3:
                if rule.vmGroupName in concerned_groups:
                    rule_dict.update({"affineHostGroupName": rule.affineHostGroupName})
                    rule_dict.update({"antiAffineHostGroupName": rule.antiAffineHostGroupName})
                    rule_dict.update({"vmGroupName": rule.vmGroupName})
                else: return None
            else: return None

            rule_dict.update({"enabled": rule.enabled})
            rule_dict.update({"inCompliance": rule.inCompliance})
            rule_dict.update({"key": rule.key})
            rule_dict.update({"mandatory": rule.mandatory})
            rule_dict.update({"name": rule.name})
            rule_dict.update({"status": rule.status})
            rule_dict.update({"userCreated": rule.userCreated})

            return rule_dict

        def fetch_rule_type(rule):
            """
            Get the type of the rule

            Args:
                rule           (vim): Rule

            Returns:
                NameString     (dict): Name of the type of rule
            """
            try:
                rule.vm
                return 'ClusterAffinityOrAntiAffinityRuleSpec'
            except AttributeError:
                pass

            try:
                rule.dependsOnVmGroup
                return 'ClusterDependencyRuleInfo'
            except AttributeError:
                pass

            try:
                rule.affineHostGroupName
                return 'ClusterVmHostRuleInfo'
            except AttributeError:
                pass

            return None

        try:
            container_obj = self.hvobj.get_content([self.hvobj.vim.VirtualMachine])
            cluster_obj = None

            for vm in container_obj:
                if vm.name == self.vm_name:
                    cluster_obj = vm.runtime.host.parent
                    break

            drs_settings_dict = {}
            drs_settings_dict.update({"overrides": fetch_overrides(cluster_obj)})
            concerned_groups = fetch_groups(cluster_obj)
            drs_settings_dict.update({"groups": concerned_groups})
            concerned_rules = fetch_rules(cluster_obj, concerned_groups)
            drs_settings_dict.update({"rules": concerned_rules})

            return drs_settings_dict

        except Exception as err:
            self.log.exception("Exception in fetching DRS Settings for the vm")
            raise err

    def backup_validation(self):
        """
        Updates data neded for backup validation
        Returns:

        """
        self.esx_host = self.vm_obj.runtime.host.name
        self.power_state = self.vm_obj.runtime.powerState
        self.tools = self.vm_obj.guest.guestState

    def get_disk_in_controller(self, controller_detail):
        """
        get the disk associated with the virtual device node

        Args:
                controller_detail           (string):  Details about the virtual device node
        Return:
                _disks                 (list): Disk path

        Raises:
            Exception:
                if failed to fetch disk path from the virtual device node

        """
        try:
            _disks = [key for key, value in self.disk_dict.items() if controller_detail in value]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disk_in_controller {}".format(err))
            raise Exception(err)

    def get_disks_by_repository(self, datastore_name):
        """
        get the disk associated with the datastore name

        Args:
            datastore_name                  (string) : datastore name

        Returns:
             _disks                     (list): Disk path

        Raises:
            Exception
                when failed to fetch the disk associated with the datastore name
        """
        try:
            _disks = [key for key, value in self.disk_dict.items() if datastore_name in value]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disks_by_repository : {}".format(err))
            raise Exception(err)

    def get_disk_path_from_pattern(self, disk_pattern):
        """
        find the disk that matches the disk apttern form disk list

        Args:
                disk_pattern                    (string):   pattern which needs to be matched

        Returns:
             _disks                     (list): Disk path

        Raises:
            Exception
                when failed to fetch the disk associated with the disk pattern
        """
        try:
            rep = {'?': '\w{1}', '!': '^', '*': '.*'}
            rep = dict((re.escape(k), v) for k, v in rep.items())
            pattern = re.compile("|".join(rep.keys()))
            _disk_pattern = pattern.sub(lambda m: rep[re.escape(m.group(0))], disk_pattern)
            _disk_pattern = re.escape(_disk_pattern)
            if _disk_pattern.isalnum():
                _disk_pattern = '^' + _disk_pattern + '$'
            elif _disk_pattern[-1].isalnum():
                _disk_pattern = _disk_pattern + '$'
            _disk_pattern = re.compile(_disk_pattern, re.I)
            _disks = [key for key, value in self.disk_dict.items() if
                      re.findall(_disk_pattern, value[2])]
            return _disks
        except Exception as err:
            self.log.exception("Exception in get_disk_path_from_pattern : {}".format(err))
            raise Exception(err)

    def get_disk_by_label(self, disk_label):
        """
        find the disk that matches the disk label

        Args:
                disk_label                  (string):   Disk label to be matched

        Returns:
             _disk_path                     (list): Disk path

        Raises:
            Exception
                when failed to fetch the disk associated with the disk label
        """
        try:
            _disk_labels = []
            if re.search(r'\[.*?]', disk_label):
                _range_start = int(re.findall(r"\[([^-]+)", disk_label)[0])
                _range_end = int(re.findall(r"\-([^]]+)", disk_label)[0]) + 1
                disk_ranges = range(_range_start, _range_end)
                for _disk in disk_ranges:
                    _disk_labels.append('Hard disk ' + str(_disk))
            else:
                _disk_labels = [disk_label]
            _disks = [key for key, value in self.disk_dict.items() if value[3] in _disk_labels]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disk_by_label : {}".format(err))
            raise Exception(err)

    def _get_snapshots_by_name(self, snap_shots, snap_name='Fresh'):
        """

        Args:
            snap_shots                           (list):   snapshot list of the vm

            snap_name                           (string):   Name of the snap to find

        Returns:
            snap_obj                            (list):     Snapshots found after comparing

        Raises:
            Exception:
                When getting the snapshots hierarchy
        """

        snap_obj = []
        for snap_shot in snap_shots:
            if snap_name:
                if snap_shot.name == snap_name:
                    snap_obj.append(snap_shot)
                else:
                    snap_obj = snap_obj + self._get_snapshots_by_name(
                        snap_shot.childSnapshotList, snap_name)
        return snap_obj

    def create_snap(self, snap_name='Fresh', quiesce=False, dump_memory=False):
        """
        Creating a snapshot of the vm

        Args:
            snap_name                           (string):   Name of the snap to create

            quiesce                             (bool):   Quiesce during snapshot creation

            dump_memory                         (bool):   Taking snapshot of vm memory

        Raises:
            Exception:
                When Creating Snapshot of the vm
        """
        try:
            if quiesce and dump_memory:
                raise Exception("Quiesce and snapshot of vm memory can't be enabled together")
            elif self.vm_obj.runtime.powerState not in ('running', 'poweredOn') and (
                    quiesce or dump_memory):
                self.log.warning(
                    "Quiesce or snapshot of vm memory can't be enabled as the vm is powered off."
                    "Taking snapshot without Quiesce or snapshot of vm memory")
                quiesce = False
                dump_memory = False
            elif self.vm_obj.guest.toolsRunningStatus == 'guestToolsNotRunning' and quiesce:
                self.log.warning(
                    "Quiesce can't be enabled as the guest tools is not running"
                    "Taking snapshot without Quiesce")
                quiesce = False
            snap_description = 'Snapshot taken by automation'
            self.log.info(
                "Creating Snapshot {} on vm:{} with quiese:{}, snapshot of vm memory:{}".format(
                    snap_name, self.vm_name, quiesce, dump_memory))
            self.hvobj.wait_for_tasks(
                [self.vm_obj.CreateSnapshot(snap_name, snap_description, dump_memory, quiesce)])
        except Exception as exp:
            self.log.exception(
                "Exception:{} in Creating snapshot for vm: {}".format(exp, self.vm_name))
            return False

    def revert_snap(self, snap_name='Fresh'):
        """
        Reverts a snapshot of the vm

        Args:
            snap_name                           (string):   Name of the snap to revert to

        Raises:
            Exception:
                When reverting of the snapshot
        """
        try:
            if not self.vm_obj.snapshot:
                raise Exception("There is no Snapshot to revert")
            snap_obj = self._get_snapshots_by_name(self.vm_obj.snapshot.rootSnapshotList, snap_name)
            if len(snap_obj) != 1:
                raise Exception("Multiple or no snaps with name:{}. Can't revert".format(snap_name))
            snap_obj = snap_obj[0].snapshot
            self.log.info("Reverting Snapshot named {} of vm:{}".format(snap_name, self.vm_name))
            self.hvobj.wait_for_tasks([snap_obj.RevertToSnapshot_Task()])
        except Exception as exp:
            self.log.exception(
                "Exception:{} in Reverting snapshot for vm: {}".format(exp, self.vm_name))
            return False

    def delete_snap(self, snap_name='Fresh'):
        """
        Deletes a snapshot of the vm

        Args:
            snap_name                           (string):   Name of the snap to delete

        Raises:
            Exception:
                When deleting of the snapshot
        """
        try:
            if not self.vm_obj.snapshot:
                raise Exception("There is no Snapshot to delete")
            snap_obj = self._get_snapshots_by_name(self.vm_obj.snapshot.rootSnapshotList, snap_name)
            if len(snap_obj) != 1:
                raise Exception("Multiple or no snaps with name:{}. Can't delete".format(snap_name))
            snap_obj = snap_obj[0].snapshot
            self.log.info("Deleting Snapshot named {} of vm:{}".format(snap_name, self.vm_name))
            self.hvobj.wait_for_tasks([snap_obj.RemoveSnapshot_Task(True)])
        except Exception as exp:
            self.log.exception(
                "Exception:{} in deleting snapshot for vm: {}".format(exp, self.vm_name))
            return False

    def delete_all_snap(self):
        """
        Deletes all snapshot of the vm
        Raises:
            Exception:
                When deleting all snapshots of the vm
        """
        try:
            self.log.info("Deleting all Snapshots of vm:{}".format(self.vm_name))
            self.hvobj.wait_for_tasks([self.vm_obj.RemoveAllSnapshots()])
        except Exception as exp:
            self.log.exception(
                "Exception:{} in deleting all snapshots for vm: {}".format(exp, self.vm_name))
            return False

    def mount_vmdk(self, disk_path):
        """
        Mounts a VMDK disk to a target VM via HotAdd

        Args:
                disk_path       (str):   [{Datastore}] {VM Name}/{Filename}.vmdk

        Raise Exception:
                if failed to mount the disk to the target vm

        """

        try:
            virtual_hdd_spec = \
                self.hvobj.vim.vm.device.VirtualDeviceSpec()
            spec = self.hvobj.vim.vm.ConfigSpec()

            unit_number = 0
            for dev in self.vm_obj.config.hardware.device:
                if hasattr(dev.backing, 'fileName'):
                    unit_number = int(dev.unitNumber) + 1
                if isinstance(
                        dev,
                        self.hvobj.vim.vm.device.VirtualSCSIController):
                    controller = dev

            virtual_hdd_spec.operation = \
                self.hvobj.vim.vm.device.VirtualDeviceSpec.Operation.add
            virtual_hdd_spec.device = \
                self.hvobj.vim.vm.device.VirtualDisk()
            virtual_hdd_spec.device.backing = \
                self.hvobj.vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            virtual_hdd_spec.device.backing.diskMode = 'persistent'
            virtual_hdd_spec.device.backing.fileName = disk_path
            virtual_hdd_spec.device.backing.thinProvisioned = True
            virtual_hdd_spec.device.unitNumber = unit_number
            virtual_hdd_spec.device.controllerKey = controller.key

            spec.deviceChange = [virtual_hdd_spec]

            task = self.vm_obj.ReconfigVM_Task(spec=spec)

            answered_id = None

            while task.info.state not in [
                self.hvobj.vim.TaskInfo.State.success,
                self.hvobj.vim.TaskInfo.State.error]:

                if self.vm_obj.runtime.question is not None:

                    if answered_id:
                        continue

                    question_id = self.vm_obj.runtime.question.id
                    choices = self.vm_obj.runtime.question.choice.choiceInfo
                    choice = None
                    for o in choices:
                        if o.summary == "Yes":
                            choice = o.key
                    self.vm_obj.AnswerVM(question_id, choice)
                    answered_id = question_id

        except Exception as err:
            self.log.exception("An error occurred in mounting the VMDK")
            raise Exception(err)

    def unmount_vmdk(self, disk_path):
        """
        Unmounts a VMDK disk from the target VM

        Args:
                disk_path       (str):   [{Datastore}] {VM Name}/{Filename}.vmdk

        Raise Exception:
                if failed to unmount the disk to the target vm

        """
        try:
            hdd_label = self.get_disk_label_from_path(disk_path)

            for dev in self.vm_obj.config.hardware.device:
                if isinstance(dev, self.hvobj.vim.vm.device.VirtualDisk) \
                        and dev.deviceInfo.label == hdd_label:
                    virtual_hdd_device = dev

            virtual_hdd_spec = \
                self.hvobj.vim.vm.device.VirtualDeviceSpec()
            spec = self.hvobj.vim.vm.ConfigSpec()

            virtual_hdd_spec.operation = \
                self.hvobj.vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_hdd_spec.device = virtual_hdd_device

            spec.deviceChange = [virtual_hdd_spec]

            self.hvobj.wait_for_tasks(
                [self.vm_obj.ReconfigVM_Task(spec=spec)])

            self.log.info("Successfully unmounted disk")

        except Exception as err:
            self.log.exception("An error occurred in unmounting the VMDK")
            raise Exception(err)

    def get_disk_label_from_path(self, disk_path):
        """
        Gets the disk label of the required disk

        Args:
                disk_path       (str):   [{Datastore}] {VM Name}/{Filename}.vmdk

        Raise Exception:
                if failed to get label of disk

        """

        try:
            self.get_all_disks_info()
            vm_disks = self.disk_dict
            disk_label = vm_disks[disk_path][-1]
            return disk_label

        except Exception as err:
            self.log.exception("An error occurred in fetching disk label")
            raise Exception(err)

    def verify_vmdks_attached(self, disk_paths):
        """
        Checks whether VMDKs in list are attached to vm

        Args:
                disk_path       (str):   [{Datastore}] {VM Name}/{Filename}.vmdk

        Raise Exception:
                if failed to get label of disk

        """
        try:
            self.get_all_disks_info()
            vm_disks = self.disk_dict
            vm_disk_list = list(vm_disks.keys())

            if all(i in vm_disk_list for i in disk_paths):
                return True
            else:
                return False

        except Exception as err:
            self.log.exception("An error while checking if VMDKs attached to VM")
            raise Exception(err)

    def wait_for_vm_to_boot(self):
        """
        Waits for a VM to start booting by pinging it to see if an IP has been successfully assigned.

        Raise Exception:
                If IP assigned within 10 minutes
        """

        wait = 10

        try:
            while wait:
                self.log.info(
                    'Waiting for 60 seconds for the IP to be generated')
                time.sleep(60)

                try:
                    self.power_on()
                    self.update_vm_info(force_update=True)
                except Exception as exp:
                    self.log.info(exp)

                if self.ip:
                    if VirtualServerUtils.validate_ip(self.ip):
                        self.log.info('IP is generated for VM: {}'.format(self.vm_name))
                        self.no_ip_state = False
                        break
                    elif self.vm_obj.guest.toolsRunningStatus == 'guestToolsNotRunning':
                        self.log.info("VM {} didn't get the IP but guest tools is running.".format(self.vm_name))
                        break
                wait -= 1
            else:
                raise Exception(
                    'Valid IP for VM: {} not generated within 10 minutes '
                    'nor guest tools came up'.format(self.vm_name))

        except Exception as err:
            self.log.exception("An error occurred in fetching VM IP")
            raise Exception(err)

    def customize_ip(self, ip_address, subnet_mask, gateway, dns_servers=None, hostname=None):
        """
        Customize the IP address settings on the VM
        Args:
            ip_address      (str) : The IPv4 address
            subnet_mask     (str) : The IPv4 subnet mask
            gateway         (str) : The IPv4 gateway network address
            dns_servers     (list): List of DNS server IP addresses
            hostname        (str) : The VM computer name to be set
        """
        if not dns_servers:
            dns_servers = self.guest_dns
        if not hostname:
            hostname = self.guest_hostname

        customize_spec = self.hvobj.vim.vm.customization.Specification()

        adapter_mapping = self.hvobj.vim.vm.customization.AdapterMapping()
        adapter_mapping.adapter = self.hvobj.vim.vm.customization.IPSettings()
        adapter_mapping.adapter.ip = self.hvobj.vim.vm.customization.FixedIp()
        adapter_mapping.adapter.ip.ipAddress = ip_address
        adapter_mapping.adapter.subnetMask = subnet_mask
        adapter_mapping.adapter.gateway = gateway
        customize_spec.nicSettingMap = [adapter_mapping]

        global_ip = self.hvobj.vim.vm.customization.GlobalIPSettings()
        global_ip.dnsServerList = dns_servers
        customize_spec.globalIPSettings = global_ip

        if 'win' in self.guest_os.lower():
            hostname_prep = self.hvobj.vim.vm.customization.Sysprep()
            hostname_prep.userData = self.hvobj.vim.vm.customization.UserData()
            hostname_prep.userData.computerName = self.hvobj.vim.vm.customization.FixedName()
            hostname_prep.guiUnattended = self.hvobj.vim.vm.customization.GuiUnattended()
            hostname_prep.identification = self.hvobj.vim.vm.customization.Identification()
            hostname_prep.userData.computerName.name = hostname
            # Currently only support Administrator user
            hostname_prep.userData.fullName = 'Administrator'
            hostname_prep.userData.orgName = self.vm_name
        else:
            hostname_prep = self.hvobj.vim.vm.customization.LinuxPrep()
            hostname_prep.hostName = self.hvobj.vim.vm.customization.FixedName()
            hostname_prep.hostName.name = hostname
        customize_spec.identity = hostname_prep

        self.power_off()
        self.log.info('Customizing the VM %s', self.vm_name)
        task = self.vm_obj.Customize(spec=customize_spec)
        self.hvobj.wait_for_tasks([task])

        self.power_on()

    def authenticate_vm_session(self):
        """Authenticate the VM session by using the username/passwords defined in config"""
        credentials = VirtualServerUtils.get_details_from_config_file(self.guest_os.lower()).split(',')
        incorrect_usernames = []
        for credential in credentials:
            try:
                username = credential.split(':')[0]
                password = VirtualServerUtils.decode_password(credential.split(':')[1])
                creds = self.hvobj.vim.vm.guest.NamePasswordAuthentication(username=username,
                                                                           password=password)
                self.hvobj.connection.content.guestOperationsManager.authManager.ValidateCredentialsInGuest(
                    vm=self.vm_obj,
                    auth=creds,
                )
                self.guest_credentials = creds
                return
            except:
                # Failed authentication attempt
                incorrect_usernames.append(credential.split(':')[0])
        raise Exception("Could not create credentials object for VM! The following user names are "
                        "incorrect: {0}".format(incorrect_usernames))

    def execute_command(self, command):
        """
        Execute command on the guest VM by first sending a temp file, then getting its output
        command (str): The command to execute on guest VM
        """
        # Set the guest VM credentials for performing operations
        if not self.guest_credentials:
            self.authenticate_vm_session()
        file_manager = self.hvobj.connection.content.guestOperationsManager.fileManager
        process_manager = self.hvobj.connection.content.guestOperationsManager.processManager
        try:
            # Create a temp directory, one file for executing command and one for saving output in
            temp_dir = file_manager.CreateTemporaryDirectoryInGuest(vm=self.vm_obj,
                                                                    auth=self.guest_credentials,
                                                                    prefix='cv', suffix='')
            command_file = file_manager.CreateTemporaryFileInGuest(vm=self.vm_obj,
                                                                   auth=self.guest_credentials,
                                                                   prefix='cv',
                                                                   suffix='' if self.guest_os != 'Windows'
                                                                   else '.bat',
                                                                   directoryPath=temp_dir)
            output_file = file_manager.CreateTemporaryFileInGuest(vm=self.vm_obj,
                                                                  auth=self.guest_credentials,
                                                                  prefix='cv', suffix='output',
                                                                  directoryPath=temp_dir)
            # Upload command file to guest VM OS and replace with command file(temporary)
            if self.guest_os == 'Linux':
                file_attributes = self.hvobj.vim.vm.guest.FileManager.PosixFileAttributes(
                    permissions=33133)
            else:
                file_attributes = self.hvobj.vim.vm.guest.FileManager.FileAttributes()
            command_upload_url = file_manager.InitiateFileTransferToGuest(
                vm=self.vm_obj,
                auth=self.guest_credentials,
                guestFilePath=command_file,
                overwrite=True,
                fileAttributes=file_attributes,
                fileSize=len(command)
            )
            # Upload the file to ESX host provided link
            response = requests.put(command_upload_url, data=command, verify=False)
            if not response.ok:
                raise Exception(f'Could not initiate file transfer for executing '
                                f'command with error: {response.text}')
            # Execute the program on the guest VM
            program_path = command_file
            program_arguments = f" > {output_file}"
            execution_spec = self.hvobj.vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=program_path,
                arguments=program_arguments)
            execution_response = process_manager.StartProgramInGuest(vm=self.vm_obj,
                                                                     auth=self.guest_credentials,
                                                                     spec=execution_spec)
            time.sleep(3)
            if not execution_response > 0:
                raise Exception('Execution process did not start')
            # Make sure the program has run and has a valid process ID
            exit_code = \
                process_manager.ListProcessesInGuest(vm=self.vm_obj, auth=self.guest_credentials,
                                                     pids=[execution_response])[0].exitCode
            if exit_code != 0:
                raise Exception(f'Program execution failed with exit code {exit_code}')

            # Download the file from the VM to our machine
            output_download_url = file_manager.InitiateFileTransferFromGuest(self.vm_obj,
                                                                             auth=self.guest_credentials,
                                                                             guestFilePath=output_file)
            output = requests.get(output_download_url.url, verify=False)
            if not output.ok:
                raise Exception(f'Failed to get output file from guest due to error: {output.text}')
            # Access the output of the executed command
            if self.guest_os.lower() == 'windows':
                _output = (output.text.split(command))[1]
            else:
                _output = output.text
            return _output.strip()
        except Exception as _exception:
            self.log.exception(f'Could not execute command on guest VM with error: {_exception}')
        finally:
            if 'temp_dir' in locals():
                file_manager.DeleteDirectoryInGuest(self.vm_obj, auth=self.guest_credentials,
                                                    directoryPath=temp_dir, recursive=True)

    def compute_distribute_workload(self, proxy_obj, workload_vm, job_type='restore', **kwargs):
        """
                Computes host and datastore match proxies for the workload_vm
        Args:
            proxy_obj       (dict): A dictionary of proxy as key and proxy location details as value
            workload_vm     (str): The backed up VM
            job_type        (str): Type of job - backup / restore

        """
        restore_validation_options = kwargs.get('restore_validation_options', None)
        self.workload_vm = workload_vm
        if job_type.lower() == 'restore':
            for proxy in proxy_obj:
                if proxy != workload_vm:
                    if proxy_obj[proxy][1] == restore_validation_options[workload_vm]['host']:
                        self.workload_host_proxies.append(proxy)
                    elif proxy_obj[proxy][2] == restore_validation_options[workload_vm]['datastore']:
                        self.workload_datastore_proxies.append(proxy)

    def get_storage_policy(self):
        """
            Returns:
                Storage Policy associated to the VM
        """
        if self.hvobj.profile_manager is None:
            # Connect to SPBM service endpoint
            self.hvobj.get_pbm_connection()

        try:
            pm_object_type = pbm.ServerObjectRef.ObjectType("virtualMachine")
            vm_obj_ref = pbm.ServerObjectRef(key=self.vm_obj._moId, objectType=pm_object_type)
            profile_ids = self.hvobj.profile_manager.PbmQueryAssociatedProfile(vm_obj_ref)
            if len(profile_ids) > 0:
                profiles = self.hvobj.profile_manager.PbmRetrieveContent(profileIds=profile_ids)
                return profiles[0].name
            else:
                return None
        except Exception as exp:
            self.log.exception('Exception in retrieving the storage policy of the VM')
            raise exp

    class DrValidation(HypervisorVM.DrValidation):
        """class for DR validation"""

        def __init__(self, vmobj, vm_options, **kwargs):
            """ Initializes the DR_validation class
            """
            super().__init__(vmobj, vm_options, **kwargs)

        def validate_cpu_count(self, **kwargs):
            """Validate CPU count to make sure they honor the restore options"""
            if self.vm_options.get('cpuCount') != self.vm.no_of_cpu:
                raise Exception(f"Expected CPU count {self.vm_options.get('cpuCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.no_of_cpu}")

        def validate_memory(self, **kwargs):
            """Validate memory size to make sure it honors the restore options"""
            if self.vm_options.get('memory') != self.vm.memory:
                raise Exception(f"Expected memory size {self.vm_options.get('memory')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.memory}")

        def validate_disk_count(self, **kwargs):
            """Validate the number of disks"""
            if self.vm_options.get('diskCount') != self.vm.disk_count:
                raise Exception(f"Expected disk count: {self.vm_options.get('diskCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.disk_count}")

        def validate_network_adapter(self, **kwargs):
            """Validate the network adapter"""
            if self.vm_options.get('nicCount') != self.vm.nic_count:
                raise Exception(f"Expected NIC count: {self.vm_options.get('nicCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.nic_count}")

        def validate_snapshot(self, integrity_check=False, **kwargs):
            """validate snapshot for sync/failback"""
            if integrity_check:
                if self.INTEGRITY_SNAPSHOT_NAME not in self.vm.VMSnapshot:
                    raise Exception(f"Integrity snapshot: {self.INTEGRITY_SNAPSHOT_NAME}"
                                    f" not observed on VM {self.vm.vm_name}")
                if kwargs.get('job_id'):
                    for snapshot in self.vm.VMSnapshotTree:
                        if (snapshot.name == self.INTEGRITY_SNAPSHOT_NAME
                                and kwargs.get('job_id') in snapshot.description):
                            return
                    raise Exception(f"Integrity snapshot description does not have job ID: {kwargs.get('job_id')}")
            else:
                if self.INTEGRITY_SNAPSHOT_NAME in self.vm.VMSnapshot:
                    raise Exception(f"Integrity snapshot: {self.INTEGRITY_SNAPSHOT_NAME}"
                                    f" observed on VM {self.vm.vm_name}")

            if self.FAILOVER_SNAPSHOT_NAME in self.vm.VMSnapshot:
                raise Exception(f"Failover snapshot: {self.FAILOVER_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}")

        def validate_snapshot_failover(self, **kwargs):
            """valdiates snapshot for failover"""
            if self.INTEGRITY_SNAPSHOT_NAME in self.vm.VMSnapshot:
                raise Exception(f"Integrity snapshot: {self.INTEGRITY_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}"
                                f" even after failover")
            if self.FAILOVER_SNAPSHOT_NAME not in self.vm.VMSnapshot:
                raise Exception(f"Failover snapshot: {self.FAILOVER_SNAPSHOT_NAME} not observed on VM {self.vm.vm_name}"
                                f" after failover")
            if kwargs.get('job_id'):
                for snapshot in self.vm.VMSnapshotTree:
                    if snapshot.name == self.FAILOVER_SNAPSHOT_NAME and kwargs.get('job_id') in snapshot.description:
                        return
                raise Exception(f"Failover snapshot description does not have job ID: {kwargs.get('job_id')}")

        def validate_ip_rules(self, **kwargs):
            """ Validate that the IP rules are applied on VM """
            # Skip IP validation if IP customization is not configured
            if not self.vm_options.get("vmIPAddressOptions"):
                return
            vm_ip_settings = self.vm.guest_ip_rules
            vm_dhcp_count = len([vm_ip for vm_ip in vm_ip_settings if vm_ip.get('dhcpEnabled', False)])

            # The initial DHCP count is for all the NICs that won't be matched at all (no rule for them)
            dhcp_count = len(vm_ip_settings) - len(self.vm_options.get('vmIPAddressOptions', []))
            default_gateways = []
            dns_servers = []

            for ip_dict in self.vm_options.get('vmIPAddressOptions'):
                # If rule is for DHCP, add to DHCP NIC count
                if ip_dict.get('dhcpEnabled', False):
                    dhcp_count += 1
                elif ip_dict.get('ipAddress') and ip_dict.get('subnetMask'):
                    # Match IP rules on the basis of IP address and subnet mask
                    for vm_ip_dict in vm_ip_settings:
                        if ip_dict.get('defaultGateway'):
                            default_gateways += ip_dict.get('defaultGateway', "")
                        if ip_dict.get('dnsServers', []):
                            dns_servers += ip_dict.get('dnsServers', [])
                        # The vm_ip_dict has default value "" and ip_dict has default None,
                        # so matches won't happen unnecessarily
                        if (vm_ip_dict.get('ipAddress', "") == ip_dict.get('ipAddress')
                                and vm_ip_dict.get('subnetMask', "") == ip_dict.get('subnetMask')):
                            # IP rule found here, so we can stop looking for rules
                            break
                    else:
                        # If the IP rule not found on VM, raise exception
                        raise Exception(f"IP rule {ip_dict.get('ipAddress')}/{ip_dict.get('subnetMask')}"
                                        f"not found on VM {self.vm.vm_name}")
            if dhcp_count != vm_dhcp_count:
                self.log.exception(f"Number of DHCP NIC expected: {dhcp_count}, observed: {vm_dhcp_count}"
                                f" on VM {self.vm.vm_name}")

            missing_gateways = set(default_gateways) - set(self.vm.guest_default_gateways)
            missing_dns_servers = set(dns_servers) - set(self.vm.guest_dns)

            if missing_gateways:
                raise Exception(f"Missing default gateways: {missing_gateways} on VM: {self.vm.vm_name}")
            if missing_dns_servers:
                raise Exception(f"Missing DNS servers: {missing_dns_servers} on VM: {self.vm.vm_name}")

        def validate_hostname(self, **kwargs):
            if (self.vm_options.get('computerName')
                    and self.vm_options.get('computerName') != self.vm.guest_hostname):
                raise Exception(f"VM hostname expected: {self.vm_options.get('computerName')}, "
                                f"observed: {self.vm.guest_hostname} on VM: {self.vm.vm_name}")

        def advanced_validation(self, other, **kwargs):
            """Advanced Validation"""
            self.validate_ip_rules()
            self.validate_hostname()

        def validate_no_testboot_snapshot(self, **kwargs):
            """ Validates that the test-boot snapshot generated by job is not present in DR-VM """
            if self.TESTBOOT_SNAPSHOT_NAME in self.vm.VMSnapshot:
                raise Exception(f"Test boot snapshot: {self.TESTBOOT_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}"
                                f" after Test boot job complete")

        def validate_network_connected(self, **kwargs):
            """ Validates that the network is in connected state"""
            pass
