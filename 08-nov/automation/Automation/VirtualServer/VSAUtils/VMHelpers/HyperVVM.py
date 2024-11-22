# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Hyper-V vm"""

import os
import re
import time
import copy
from AutomationUtils import machine
from AutomationUtils import logger
from VirtualServer.VSAUtils.VMHelper import HypervisorVM


class HyperVVM(HypervisorVM):
    """
    This is the main file for all  Hyper-V VM operations
    """

    def __init__(self, hv_obj, vm_name, **kwargs):
        """
        Initialization of hyper-v vm properties

        _get_vm_host()            - get the host of the VM among the servers list

        _get_vm_info()            - get the particular  information of VM

        _get_disk_list()        - gets the disk list opff the VM

        _merge_vhd()            - Merge the VHD with its snapshots

        mount_vhd()                - Mount the Vhd/VHDX and return the drive letter

        un_mount_vhd()            - Unmount the VHD mounted provided the path

        get_disk_in_controller()- get the disk in controller attached

        get_disk_path_from_pattern() - get the list of disk from pattern

        power_off()            - power off the VM

        power_on()            -power on the VM

        delete_vm()            - delete the VM

        update_vm_info()    - updates the VM info


        get_vhdx()         - get type all virtual hard disk




        """

        super(HyperVVM, self).__init__(hv_obj, vm_name)
        self.server_client_name = hv_obj.server_list
        self.serverlist = hv_obj.server_list
        self.vmserver_host_name = self.server_name

        self.vm_props_file = "GetHypervProps.ps1"
        self.vm_operation_file = "HyperVOperation.ps1"

        self.prop_dict = {
            "server_name": self.vmserver_host_name,
            "extra_args": "$null",
            "vm_name": self.vm_name
        }
        self.vmserver_host_name = self.vm_host

        self.host_machine = machine.Machine(
            self.server_client_name, self.commcell)

        self.operation_dict = {
            "server_name": self.vmserver_host_name,
            "extra_args": "$null",
            "vm_name": self.vm_name,
            "vhd_name": "$null"
        }
        self.guid = None
        self.ip = None
        self.guest_os = None
        self.host_name = None
        self._disk_list = None
        self.disk_dict = None
        self.disk_path = None
        self.workload_vm = None
        self.workload_host_proxies = []
        self.workload_csv_owner_proxies = []
        self._basic_props_initialized = False
        if self.vm_exist:
            self.update_vm_info()

    class VmConversionValidation(object):
        def __init__(self, vmobj, vm_restore_options):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            return self.vm_restore_options.network in other.vm.NicName

    class LiveSyncVmValidation(object):
        def __init__(self, vmobj, schedule, replicationjob=None, live_sync_options=None):
            self.vm = vmobj
            self.schedule = schedule
            self.replicationjob = replicationjob
            self.log = logger.get_log()

        def __eq__(self, other):
            """ validates vm replicated through livesync """
            try:
                if '__GX_BACKUP__' not in other.vm.vm.VMSnapshot:
                    self.log.info('snapshot validation failed')
                    return False
                self.log.info('snapshot validation successful')

                config_val = (int(self.vm.vm.no_of_cpu) == int(other.vm.vm.no_of_cpu) and
                              int(self.vm.vm.disk_count) == int(other.vm.vm.disk_count) and
                              int(self.vm.vm.memory) == int(other.vm.vm.memory))
                if not config_val:
                    return False

                # disk type validation
                sourcedisks = self.vm.vm.get_vhdx()
                destdisks = other.vm.vm.get_vhdx()
                for cont in sourcedisks:
                    if cont in destdisks:
                        if sourcedisks[cont][1] != destdisks[cont][1]:
                            self.log.info('Disk type validation failed')
                            return False
                    else:
                        self.log.info("Disk validation failed")
                        return False
                self.log.info('Disk validation successful')

                # network validation
                scheduleprops = self.schedule.virtualServerRstOptions
                schdetails = scheduleprops['diskLevelVMRestoreOption']['advancedRestoreOptions']
                for vmdetails in schdetails:
                    if vmdetails['name'] == self.vm.vm.vm_name:
                        if 'nics' in vmdetails:
                            if vmdetails['nics'][0]['networkName'] not in other.vm.vm.NicName:
                                return False

                return True

            except Exception as err:
                self.log.exception(
                    "Exception at Validating  {0}".format(err))
                raise err

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options, **kwargs):
            self.vm = vmobj
            self.restore_job = None
            self.vm_restore_options = vm_restore_options
            if self.vm_restore_options and self.vm_restore_options.restore_job:
                self.restore_job = self.vm_restore_options.restore_job
            self.log = logger.get_log()

        def __eq__(self, other):
            """compares the source vm and restored vm"""
            sourcedisks = self.vm.vm.get_vhdx()
            destdisks = other.vm.vm.get_vhdx()
            for cont in sourcedisks:
                if cont in destdisks:
                    if sourcedisks[cont][1] != destdisks[cont][1]:
                        self.log.info('Disk type validation failed')
                        return False
            self.log.info('Disk type validation passed')

            if self.vm_restore_options and self.vm_restore_options.in_place_overwrite and \
                    (self.vm.vm.NicName != other.vm.vm.NicName):
                self.log.info("Network Adapter on VM : {0} are {1}".format(
                              other.vm.vm.vm_name, other.vm.vm.NicName))
                self.log.error("Network Adapter validation failed for inplace restore")
                return False
            elif self.vm_restore_options.inputs['network']:
                if self.vm_restore_options.inputs['network'] not in\
                        other.vm.vm.NicName:
                    self.log.info("Network Adapters on VM : {0} are {1}".format(
                                  other.vm.vm.vm_name, other.vm.vm.NicName))
                    self.log.error("Network Adapters validation failed for out of restore restore")
                    return False
            else:
                self.log.info('Network Adapter validation skipped as network option was not provided')
            self.log.info('Network Adapters validation passed')
            return True

        def validate_restore_workload(self, _ ):
            """ Restore Proxy Workload Distribution Validation

                   Args :
                        proxy_obj       (dict) : Dictionary with proxy name as key and proxy location tuple as value

                   Raises:
                        Exception:
                                 When Restore Workload Validation fails

            """
            vm = self.vm.hvobj.VMs[self.vm.workload_vm]
            proxy = vm.proxy_name
            if self.vm.workload_csv_owner_proxies and len(self.vm.workload_csv_owner_proxies) == 1:
                if proxy in self.vm.workload_csv_owner_proxies:
                    self.log.info('VM {} is restored by proxy {} (CSV Owner Match)'.format(self.vm.workload_vm, proxy))
                else:
                    raise Exception('CSV Owner was not picked up as proxy')
            elif self.vm.workload_host_proxies:
                if proxy in self.vm.workload_host_proxies:
                    self.log.info("VM {} is restored by proxy {} (Host Match)".format(self.vm.workload_vm, proxy))
                else:
                    raise Exception('Host Machine was not picked up as a proxy')
            else:
                raise Exception("Expected proxy was not picked up for Restore")

    class BackupValidation(object):
        def __init__(self, vm_obj, backup_option):
            self.vm = vm_obj
            self.backup_option = backup_option
            self.backup_job = self.backup_option.backup_job
            self.log = logger.get_log()

        def validate(self):
            """perform postbackup validation"""

            pass

    class DrValidation(HypervisorVM.DrValidation):
        """class for DR validation"""

        def __init__(self, vmobj, vm_options, **kwargs):
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

            if self.vm_options.get('nicName') in self.vm.NicName or \
                    self.vm_options.get('nicName') == self.vm.NicName:
                return
            raise Exception(f"Expected NIC : {self.vm_options.get('nicName')} not observed on"
                            f" VM {self.vm.vm_name}: {self.vm.NicName}")

        def validate_snapshot(self, integrity_check=False, **kwargs):
            """validate snapshot for sync/failback"""
            if integrity_check:
                if not self.vm.VMSnapshot or self.INTEGRITY_SNAPSHOT_NAME not in self.vm.VMSnapshot:
                    raise Exception(f"Integrity snapshot: {self.INTEGRITY_SNAPSHOT_NAME} "
                                    f"not observed on VM {self.vm.vm_name}")
            else:
                if self.vm.VMSnapshot and self.INTEGRITY_SNAPSHOT_NAME in self.vm.VMSnapshot:
                    raise Exception(f"Integrity snapshot: {self.INTEGRITY_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}")

            if self.vm.VMSnapshot and self.FAILOVER_SNAPSHOT_NAME in self.vm.VMSnapshot:
                raise Exception(f"Failover snapshot: {self.FAILOVER_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}")

        def validate_snapshot_failover(self, **kwargs):
            """valdiates snapshot for failover"""
            # for config version less than 8 , intergrity snapshot will exist in drvm after failover
            if (self.vm.VMSnapshot and self.INTEGRITY_SNAPSHOT_NAME in self.vm.VMSnapshot) \
                    and self.vm_options.get('configVersion') >= 8:
                raise Exception(f"Integrity snapshot: {self.INTEGRITY_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}"
                                f" even after failover")
            if not self.vm.VMSnapshot or self.FAILOVER_SNAPSHOT_NAME not in self.vm.VMSnapshot:
                raise Exception(f"Failover snapshot: {self.FAILOVER_SNAPSHOT_NAME} not observed on VM {self.vm.vm_name}"
                                f" after failover")

        def validate_restore_path(self, **kwargs):
            """validates restore location for Destination VM"""
            disk_path = self.vm_options.get('diskPath')
            # Validation for recovery target restore location
            if (len(disk_path)) == 1:
                for disk_location in self.vm.disk_list:
                    if list(disk_path)[0] not in disk_location:
                        raise Exception(f"Disk path of target : {disk_path[0]} not observed on VM {self.vm.vm_name}"
                                        f" disk path {disk_location}")
            else:
                # Validation of source VM disk paths
                if set(self.vm.disk_list) != set(disk_path):
                    raise Exception(f"VM {self.vm.vm_name} expected: {disk_path} observed: {self.vm.disk_list}")

        def is_failback_supported(self):
            """ Checks if VM config version is greater than or equal to 8. """
            if self.vm_options.get('configVersion') >= 8:
                return True
            else:
                self.log.error(f"VM Configuration version for VM: {self.vm.vm_name} is less than 8."
                               f" Hence Failback is not supported.")
                return False

        def advanced_validation(self, other, **kwargs):
            """Advanced Validation"""
            self.validate_restore_path()

        def validate_no_testboot_snapshot(self, **kwargs):
            """ Validates that the test-boot snapshot generated by job is not present in DR-VM """
            if self.TESTBOOT_SNAPSHOT_NAME in self.vm.VMSnapshot:
                raise Exception(f"Test boot snapshot: {self.TESTBOOT_SNAPSHOT_NAME} observed on VM {self.vm.vm_name}"
                                f" after Test boot job complete")

        def validate_disk_path_deleted(self, **kwargs):
            """ Validate restore folder does not exists in hypervisors"""
            disk_path = self.vm_options.get('diskPath')
            vm_path = str(list(disk_path)[0] + self.vm.host_machine.os_sep + str(self.vm.vm_name))
            if self.vm.host_machine.check_directory_exists(vm_path):
                raise Exception(f"{self.vm.vm_name} - VM disk: {disk_path} exist after vm deletion")

        def validate_warm_sync(self, **kwargs):
            """ Validate Warm sync is applied on hypervisors"""
            # Validate that the VM and restore folder not exists if warm sync is enabled
            super().validate_warm_sync(**kwargs)
            self.validate_disk_path_deleted()

    @property
    def disk_list(self):
        """to fetch the disk in the VM
        Return:
            disk_list   (list)- list of disk in VM
            e.g:[ide0-0-test1.vhdx]
        """
        self.disk_dict = self._get_disk_list
        if self.disk_dict:
            self._disk_list = self.disk_dict.keys()

        else:
            self._disk_list = []

        return self._disk_list

    @property
    def vm_host(self):
        """
        get the Host of the VM

        Return:
            vm_host     (str)- VM Host of the VM
        """
        if not isinstance(self.serverlist, list):
            server_list = [self.serverlist]
        else:
            server_list = self.serverlist

        _vm_host = self._get_vm_host(server_list)
        self.server_client_name = _vm_host
        client = self.commcell.clients.get(_vm_host)
        self.prop_dict["server_name"] = client.client_hostname
        return client.client_hostname

    def recheck_vm_host(self):
        self.vmserver_host_name = self.vm_host
        self.host_machine = machine.Machine(
            self.server_client_name, self.commcell)

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
        """
        fetches all the properties of the VM

        Args:
                should have code for two possibilties

                Basic - Basic properties of VM like HostName,
                            especially the properties with which VM can be added as dynamic content

                All   - All the possible properties of the VM

                os_info - Set the property VMGuestOS for creating OS Object

                force_update - to refresh all the properties always
                    True : ALways collect  properties
                    False: refresh only if properties are not initialized

        exception:
                if failed to get all the properties of the VM
        """

        try:
            if not self._basic_props_initialized or force_update:
                self._get_vm_info(prop)
            if os_info or prop == 'All':
                self._get_vm_info(prop='power_state')
                if self.power_state == 'off':
                    self.power_on()
                    time.sleep(180)
                self._get_vm_info(prop)
                attempt = 0
                while attempt < 5:
                    try:
                        attempt += 1
                        self._get_vm_info(prop="ip")
                        if self.ip is None or self.ip == "":
                            time.sleep(60)
                            continue
                        self.vm_guest_os = self.guest_os
                        self.get_drive_list()
                        break
                    except Exception as update_info_err:
                        self.log.error(update_info_err)
                        time.sleep(60)
                if attempt >= 5:
                    raise Exception("Update vm info Failed")

        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def _get_vm_host(self, server_list):
        """
        from the list of
        """
        try:
            server_name = None
            for _each_server in server_list:
                client = self.commcell.clients.get(_each_server)
                _ps_path = os.path.join(self.utils_path, self.vm_props_file)
                self.prop_dict["server_name"] = client.client_hostname
                self.prop_dict["property"] = "GetAllVM"
                attempt = 0
                while attempt < 5:
                    attempt += 1
                    try:
                        self.log.info("Getting Server Machine object  for %s  attempt: %s", client.client_hostname,
                                      attempt)
                        server_machine = machine.Machine(
                            client, self.commcell)
                        output = server_machine._execute_script(_ps_path, self.prop_dict)
                        _psoutput = output.output
                        _stdout = _psoutput.rsplit("=", 1)[1]
                        _stdout = _stdout.strip()
                        _temp_vm_list = _stdout.split(",")
                    except Exception as err:
                        if attempt < 5:
                            self.log.error("Retrying as following error occurred : %s", str(err))

                        else:
                            self.log.error(err)
                            raise Exception(err)
                    else:
                        break
                for each_vm in _temp_vm_list:
                    if each_vm != "":
                        each_vm = each_vm.strip()
                        if re.match("^[A-Za-z0-9_-]*$", each_vm):
                            if each_vm == self.vm_name:
                                server_name = _each_server
                                break
                            else:
                                continue
                        else:
                            self.log.info(
                                "Unicode VM are not supported for now")

            if not server_name:
                server_name = server_list[0]
                self.log.info("server cannot be identified , it can be a coversion case ")
                self.vm_exist = False

            self.log.info("Server where VM is located is {0}".format(server_name))

            return server_name

        except Exception as err:
            self.log.exception(
                "An exception occurred while getting all Vms from Hypervisor")
            raise Exception(err)

    def _get_vm_info(self, prop, extra_args="$null"):
        """
        get the basic or all or specific properties of VM

        Args:
                prop         -    basic, All or specific property like Memory

                ExtraArgs    - Extra arguments needed for property listed by ","

        exception:
                if failed to get all the properties of the VM

        """
        retry = 0
        while retry < 5:
            try:

                self.log.info(
                    "Collecting all the VM properties for VM %s" % self.vm_name)
                _ps_path = os.path.join(self.utils_path, self.vm_props_file)
                self.prop_dict["property"] = prop
                self.prop_dict["extra_args"] = extra_args
                output = self.host_machine._execute_script(_ps_path, self.prop_dict)
                _stdout = output.output
                self.log.info("output of all vm prop is {0}".format(_stdout))
                if _stdout != "":
                    if ";" in _stdout:
                        stdlines = _stdout.split(';')
                    else:
                        stdlines = [_stdout.strip()]
                    for _each_prop in stdlines:
                        key = _each_prop.split("=")[0]
                        val = _each_prop.split("=")[1]
                        val = val.strip()
                        if val == "":
                            val = None

                        if key == "ip" and val:
                            setattr(self, key, val.split(" ")[0])
                        elif key == 'NicName':
                            setattr(self, "NicName", val.split(',') if val else [])
                        elif key == "nic_count":
                            setattr(self, key, int(val))
                        elif key == "memory":
                            setattr(self, key, float(int(val)/1024))
                        elif key == 'nic':
                            setattr(self, "nic_count", int(val.split(" ")[-1]))
                            setattr(self, "NicName", val[:-len(self.nic_count)-1].split(",") if
                                    val[:-len(self.nic_count) - 1] else [])
                        elif key == "disk_count":
                            setattr(self, key, int(val))
                        elif key == "no_of_disks":
                            setattr(self, key, int(val))
                        elif key == "no_of_cpu":
                            setattr(self, key, int(val))
                        elif key == "config_version":
                            setattr(self, key, float(val))
                        else:
                            setattr(self, key, val)
                self._basic_props_initialized = True
                break
            except Exception as err:
                self.log.exception("Failed to Get all the VM Properties of the VM")
                if self.vm_exist and retry < 4:
                    self.log.info("Failed to get vm info. Retrying..")
                    retry += 1
                    time.sleep(60)
                    continue
                raise Exception(err)

    def get_vhdx(self):
        """
        Gets all controller ,associated hard disk and type of hard disk

        returns :
            Dictionary with key as controller and value is with path of associated disk and type of disk
            ex : {'IDE00' : ['C:\virtualdisk.vhd' , 'Dynamic']}
         exception:
                if failed to get property
        """

        try:
            _ps_path = os.path.join(self.utils_path, self.vm_props_file)
            self.prop_dict["property"] = 'Vhdx'

            output = self.host_machine._execute_script(_ps_path, self.prop_dict)
            _stdout = output.output
            if _stdout != "":
                disk_info = _stdout[0:-1]
                return eval(repr(disk_info)[1:-1])
            else:
                raise Exception("Error while getting disk type details")
        except Exception as err:
            self.log.exception("Failed to Get VDHX popertires")
            raise Exception(err)

    @property
    def _get_disk_list(self):
        """
        get the list of disk in the VM

        Returns:
                _disk_dict : with keys as disk name and value as snapshot associated with diskname

                _diks_dict = {
                        "test1.vhdx":["test1_184BDFE9-1DF5-4097-8BC3-06128C581C42.avhdx",
                        "test1_184BDEF9-1DF5-4097-8BC3-06128C581c82.avhdx"]
                }

        """
        try:
            _disk_dict = {}
            if self.disk_path is None:
                self._get_vm_info('disk_path')

            if self.disk_path is not None:
                if "," in self.disk_path:
                    temp_list = self.disk_path.split(",")

                else:
                    temp_list = [self.disk_path]

                for each_disk_list in temp_list:
                    final_disk = (each_disk_list.split("::")[0]).strip()
                    _temp_disk_list = (each_disk_list.split("::")[1]).strip()
                    if " " in _temp_disk_list:
                        _disk_list = _temp_disk_list.split(" ")
                    else:
                        _disk_list = [_temp_disk_list]

                    _disk_dict[final_disk] = _disk_list

            else:
                self.log.info("Cannot collect Disk  Path information")

            return _disk_dict
        except Exception as err:
            self.log.exception("Failed to Get all the VM Properties of the VM")
            raise Exception(err)

    @property
    def set_no_of_cpu(self):
        """Return the mber cpu set in vm"""
        return self._set_no_of_cpu

    @set_no_of_cpu.setter
    def set_no_of_cpu(self, count):
        """
        set the number of processor for  the VM.

         Args:
                count            (int)    - Number of CPU to be set in VM


        Exception:
                When setting cpu count fails

        """

        try:

            vm_name = self.vm_name

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "SetVmProcessor"
            self.operation_dict["vm_name"] = vm_name
            self.operation_dict["extra_args"] = count
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if "Success" in _stdout:
                self._set_no_of_cpu = count
            else:
                self.log.error("The error occurred %s" % _stdout)
                raise Exception("Exception in setting number of cpu")

        except Exception as err:
            self.log.exception("Exception in setting the processor count of VM {0}".format(err))
            raise err

    def _merge_vhd(self, vhd_name):
        """
        merge all the snapshot disk with base disk

        Args:
                vhd_name (str)    - name of the VHD which all snapshots has to be merged

        Return:
                disk_merge     (bool)    - true when merge is success
                                                          False when Merge fails

                base_vhd_name    (str)- base Vhd Name after merging snapshots

        """
        try:
            disk_merge = True
            do_merge = False
            _base_vhd_name = None

            for each_key in self.disk_dict.keys():
                if (os.path.basename(vhd_name)) == (os.path.basename(each_key)):
                    _base_src_vhd_name = (self.disk_dict[each_key])[-1]
                    _base_vhd_name = os.path.join(os.path.dirname(
                        vhd_name), os.path.basename(_base_src_vhd_name))
                    do_merge = True
                    break

            if do_merge:
                _ps_path = os.path.join(
                    self.utils_path, self.vm_operation_file)
                self.operation_dict["operation"] = "Merge"
                self.operation_dict["extra_args"] = vhd_name, _base_vhd_name
                output = self.host_machine._execute_script(_ps_path, self.operation_dict)
                _stdout = output.output
                if _stdout != 0:
                    self.log.info(
                        "Failed to marge disk but still will try to mount it")
                    disk_merge = False

            else:
                self.log.info(
                    "Cannot find the disk at all please check the browse")
                return False, None

            return disk_merge, _base_vhd_name

        except Exception as err:
            self.log.exception("Failed to Get all the VM Properties of the VM")
            raise Exception(err)

    def mount_vhd(self, vhd_name, destination_client=None):
        """
        Mount the VHD provided

        Args:
                vhd_name            (str)    - vhd name that has to be mounted


                destination_client  (obj)   - client where the disk to be mounted are located

        returns:
                _drive_letter_list    (list)    - List of drive letters that is retuned after mount
                                                        [A:,D:]

                                                        Fasle    - if failed to mount
        """
        try:
            _drive_letter_list = []

            if not destination_client:
                destination_client = self.host_machine

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "MountVHD"
            self.operation_dict["vhd_name"] = vhd_name.strip()
            operation_dict = copy.deepcopy(self.operation_dict)
            operation_dict['server_name'] = destination_client.ip_address
            attempt = 0
            while attempt < 5:
                attempt += 1
                output = destination_client._execute_script(_ps_path, operation_dict)
                _stdout = output.output
                self.log.info("Execute Mount command Response %s", _stdout)
                if "Success" in _stdout:
                    _stdout = _stdout.split("\n")
                    for line in _stdout:
                        if "DriveLetter" in line:
                            _drive_letter = line.split("=")[1]
                            _drive_letter = _drive_letter.strip()
                            if "," in _drive_letter:
                                _temp_drive_letter_list = _drive_letter.split(",")
                            else:
                                _temp_drive_letter_list = [_drive_letter]

                    for each_drive in _temp_drive_letter_list:
                        if each_drive:
                            each_drive = each_drive + ":"
                            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
                            operation_dict["operation"] = "DriveSize"
                            operation_dict["extra_args"] = each_drive
                            output = destination_client._execute_script(_ps_path, operation_dict)
                            _stdout = output.output
                            self.log.info("Execute GetDrive Size for drive  %s : Response %s", each_drive, _stdout)
                            _stdout = _stdout.split("\n")
                            for line in _stdout:
                                if "DriveSize" in line:
                                    size = float(line.split("=")[1])
                                    if size > 600:
                                        _drive_letter_list.append(each_drive)

                    for each_drive in _drive_letter_list:
                        self.log.info("drive letter %s" % each_drive)

                    return _drive_letter_list
                else:
                    self.log.error("The error occurred : attempt {0}  ERROR : {1}".format(attempt, _stdout))
            return False

        except Exception as err:
            self.log.exception("Exception in MountVM")
            raise Exception("Exception in MountVM:{0}".format(err))

    def un_mount_vhd(self, vhd_name, destination_client=None):
        """
        Un-mount the vhd name provided

        args:
                vhd_name : vhd needs to be unmounted

                destination_client  (obj)   - client where the disk to be unmounted are located

        return:
                True    (bool)         - if vhd is unmounted

        Exception:
                if fails to unmount

        """

        try:
            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            if not destination_client:
                destination_client = self.host_machine
            self.operation_dict["operation"] = "UnMountVHD"
            self.operation_dict["vhd_name"] = vhd_name.strip()
            operation_dict = copy.deepcopy(self.operation_dict)
            operation_dict['server_name'] = destination_client.ip_address
            output = destination_client._execute_script(_ps_path, operation_dict)
            _stdout = output.output
            if "Success" in _stdout:
                return True
            else:
                self.log.error("The error occurred %s" % _stdout)
                raise Exception("Exception in UnMountVM")

        except Exception as err:
            self.log.exception("Exception in UnMountVM : %s", err)
            self.log.info("Execute UnMount Response : %s", _stdout)
            raise Exception("Exception in UnMountVM:{0}".format(err))

    def power_on(self):
        """
        power on the VM.

        return:
                True - when power on is successful

        Exception:
                When power on failed

        """

        try:

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "PowerOn"
            attempt = 0
            while attempt < 5:
                attempt = attempt + 1
                output = self.host_machine._execute_script(_ps_path, self.operation_dict)
                _stdout = output.output
                if "Success" in _stdout:
                    return True
                else:
                    time.sleep(60)
                    self.log.error(" Error occurred : %s" % _stdout)
            if "Success" in _stdout:
                return True
            else:
                self.log.error("The error occurred %s" % _stdout)
                raise Exception("Exception in PowerOn")

        except Exception as err:
            self.log.exception("Exception in PowerOn")
            raise Exception("Exception in PowerOn:{0}".format(err))

    def power_off(self):
        """
        power off the VM.

        return:
                True - when power off is successful

        Exception:
                When power off failed

        """

        try:

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "PowerOff"
            attempt = 0
            while attempt < 5:
                attempt = attempt + 1
                output = self.host_machine._execute_script(_ps_path, self.operation_dict)
                _stdout = output.output
                if "Success" in _stdout:
                    return True
                else:
                    time.sleep(60)
                    self.log.error(" Error occurred : %s" % _stdout)

            if "Success" in _stdout:
                return True
            else:
                self.log.error("The error occurred %s" % _stdout)
                raise Exception("Exception in PowerOff")

        except Exception as err:
            self.log.exception("Exception in PowerOff")
            raise Exception("Exception in PowerOff:" + str(err))

    def delete_vm(self, vm_name=None):
        """
        Delete the VM.

        return:
                True - when Delete  is successful
                False -  when delete is failed

        """

        try:

            if vm_name is None:
                vm_name = self.vm_name

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "Delete"
            self.operation_dict["vm_name"] = vm_name
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if "Success" in _stdout:
                return True
            else:
                self.log.error("The error occurred %s" % _stdout)
                return False

        except Exception as err:
            self.log.exception("Exception in DeleteVM {0}".format(err))
            return False

    @property
    def set_memory(self):
        """ return the memory which has set in the vm """
        return self._set_memory

    @set_memory.setter
    def set_memory(self, memory):
        """
        Set Startup Memory of  the VM.

                memory            (int)    -  memory in MB to be set in VM


        Execption:
                when setting memory failed

        """

        try:

            vm_name = self.vm_name

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "SetVmMemory"
            self.operation_dict["vm_name"] = vm_name
            self.operation_dict["extra_args"] = memory
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if "Success" in _stdout:
                self._set_memory = memory
            else:
                self.log.error("The error occurred %s" % _stdout)
                raise Exception("Exception in setting memory")

        except Exception as err:
            self.log.exception("Exception in setting Memory of VM {0}".format(err))
            raise err

    def get_disk_in_controller(self, controller_type, number, location):
        """
        get the disk assocaited with controller

        Args:
                controller_type (str)    - IDE/SCSI

                number            (int)    - IDE(1:0) 1 is the disk number

                location        (int)    - IDE(1:0) 0 is the location in disk number 1

        Return:
                DiskType    (str)    - diks in location of args(eg: disk in IDE(1:0))

        """
        try:
            _extr_args = "%s,%s,%s" % (controller_type, number, location)
            self._get_vm_info("DiskType", _extr_args)
            return self.DiskType

        except Exception as err:
            self.log.exception("Exception in GetDiskInController")
            raise err

    def is_powered_on(self):
        """returns true if vm is powered on else false"""
        self._get_vm_info(prop='power_state')
        if self.power_state == 'running':
            return True
        return False

    def get_disk_path_from_pattern(self, disk_pattern):
        """
        find the disk that matches the disk apttern form disk list

        Args:
                disk_pattern    (str)    - pattern which needs to be matched

        Return:
                eachdisk    (str)        - the disk that matches the pattern
        """
        try:
            _disk_name = os.path.basename(disk_pattern)
            for each_disk in self.DiskList:
                _vm_disk_name = os.path.basename(each_disk)
                if _vm_disk_name == _disk_name:
                    self.log.info("Found the Disk to be filtered in the VM")
                    return each_disk

        except Exception as err:
            self.log.exception("Exception in GetDiskInController")
            raise err

    def migrate_vm(self, vm_name=None):
        """
        Migrate VM to best possible node

        Return:
                NewHost (String) - Hostname the VM migrated to

        Exception:
                An error occurred while checking/creating the registry
        """
        try:
            if vm_name is None:
                vm_name = self.vm_name

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "MigrateVM"
            self.operation_dict["vm_name"] = vm_name
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if "failed" in _stdout:
                self.log.error("The error occurred %s" % _stdout)

        except Exception as err:
            self.log.exception(
                "An error occurred migrating the VM")
            raise err

    def revert_snap(self, snap_name="Fresh"):
        """
        Revert snap of the machine specified
        :param snap_name: name of the snap to be reverted
        :return:
            true - if revert snap succeds
            False - on Failure
        """
        try:
            _ps_path = os.path.join(
                self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "RevertSnap"
            self.operation_dict["extra_args"] = snap_name
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if '0' in _stdout:
                self.log.info("Snapshot revert was successfull")
                return True
            else:
                return False

        except Exception as err:
            self.log.exception("Exception in revert_snap")
            raise err

    def create_snap(self, snap_name="Fresh"):
        """
        Create snap of the machine specified
        :param snap_name: name of the snap to be created
        :return:
            true - if create snap succeds
            False - on Failure
        """
        try:
            _ps_path = os.path.join(
                self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "CreateSnap"
            self.operation_dict["extra_args"] = snap_name
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if '0' in _stdout:
                self.log.info("Snapshot creation was successfull")
                return True
            else:
                return False

        except Exception as err:
            self.log.exception("Exception in Create_snap")
            raise err

    def delete_snap(self, snap_name="Fresh"):
        """
        delete snap of the machine specified
        :param snap_name: name of the snap to be delete
        :return:
            true - if delete snap succeds
            False - on Failure
        """
        try:
            _ps_path = os.path.join(
                self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "DeleteSnap"
            self.operation_dict["extra_args"] = snap_name
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if '0' in _stdout:
                self.log.info("Snapshot deletion  was successfull")
                return True
            else:
                return False

        except Exception as err:
            self.log.exception("Exception in delete_snap")
            raise err

    def get_vm_generation(self):
        """Gets the generation of VM
           Retruns   (str):  generation of vm

        """
        return self.Generation

    def clean_up(self):
        """
        Does the cleanup after the testcase.

        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned

        """

        try:
            self.log.info("Powering off VMs after restore")
            self.power_off()
        except Exception as exp:
            raise Exception("Exception in Cleanup: {0}".format(exp))

    def compute_distribute_workload(self, proxy_obj, workload_vm, job_type='restore', **kwargs):
        """
                Map proxies to workload vm based on host and Cluster owner
        Args:
            proxy_obj       (dict): A dictionary of proxy as key and CSV path owned by the proxy
            workload_vm     (str): The backed up VM
            job_type        (str): Type of job - backup / restore

        """
        restore_path = kwargs.get('restore_validation_options', {}).get('restore_path')
        host_machine = kwargs.get('restore_validation_options', {}).get('host_machine')
        self.workload_vm = workload_vm
        if job_type.lower() == 'restore':
            for proxy in proxy_obj:
                if proxy != workload_vm:
                    if proxy == host_machine:
                        self.workload_host_proxies.append(proxy)

                    for path in proxy_obj[proxy]:
                        if restore_path and proxy not in self.workload_csv_owner_proxies \
                           and path in restore_path:
                            self.workload_csv_owner_proxies.append(proxy)

                        elif proxy not in self.workload_csv_owner_proxies and path in self.disk_path:
                            self.workload_csv_owner_proxies.append(proxy)
