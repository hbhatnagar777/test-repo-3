# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Hyper-V """

import socket
import re
import os
from AutomationUtils import machine
from collections import OrderedDict
from operator import itemgetter
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VirtualServerUtils import validate_ipv4


class HyperVHelper(Hypervisor):
    """
    Main class for performing all operations on Hyperv Hyperviosr

    Methods:
            get_all_vms_in_hypervisor()        - abstract -get all the VMs in HYper-V Host

            compute_free_resources()        - compute the hyperv host and destiantion path
                                                    for perfoming restores

            mount_disk()                    - Mount the Vhd/VHDX and return the drive letter

            un_mount_disk()                    - Unmount the VHD mounted provided the path

            _get_datastore_dict()            - get the list of drives with space in Hyper-V

            _get_datastore_priority_list()    - return the drives in Hyper-V Host in
                                                    increasing order of disk size

            _get_proxy_priority_list()        - returns the proxy associated with that instance in
                                                    increasing order of memory

            _get_required_memory_for_restore()- Sum of Memory of the VM to be restored

            _get_required_diskspace_for_restore()- Sum of disk space of the VM to be restored

             check_vms_exist                            -  Checks VMs exists in severs of hypervisor instance

    """

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine=socket.gethostbyname_ex(socket.gethostname())[2][0],
                 **kwargs):
        """
        Initialize Hyper-V Helper class properties
        """

        super(HyperVHelper, self).__init__(server_host_name,
                                           user_name, password, instance_type, commcell, host_machine)

        self.server_host_machine = self.commcell.clients.get(self.server_host_name)
        self.operation_ps_file = "GetHypervProps.ps1"
        self.disk_extension = [".vhd", ".avhd", ".vhdx", ".avhdx"]
        self.prop_dict = {
            "server_name": self.server_host_name,
            "vm_name": "$null",
            "extra_args": "$null"
        }

        self.operation_dict = {
            "server_name": self.server_host_name,
            "extra_args": "$null",
            "vhd_name": "$null"
        }
        
        self.proxy_machine_obj = {}

    def get_all_vms_in_hypervisor(self, server="", pattern="", c_type=""):
        """
        get all the Vms in Hypervisor

        Args:
                server    (str)    - specific hypervisor Host for which all Vms has to be fetched

                pattern   (str)   - Pattern to fetch the vms

                c_type            (str):  Type of content

        Return:
                Vmlist    (list)    - List of Vms in  in host of Pseudoclient
        """
        try:
            _all_vm_list = []
            if server == "":
                server_list = [self.server_host_name]

            else:
                if isinstance(server, list):
                    server_list = server
                else:
                    server_list = [server]

            for _each_server in server_list:
                _ps_path = os.path.join(
                    self.utils_path, self.operation_ps_file)
                self.prop_dict["server_name"] = _each_server
                self.prop_dict["property"] = "GetAllVM"
                client = self.commcell.clients.get(_each_server)
                server_machine = machine.Machine(
                    client, self.commcell)
                output = server_machine._execute_script(_ps_path, self.prop_dict)
                # _stdout, _stderr = VirtualServerUtils.ExecutePsFile(
                # _ps_path, _each_server, self.user_name, self.password, "", "GetAllVM")

                _stdout = output.output
                _stdout = _stdout.rsplit("=", 1)[1]
                _stdout = _stdout.strip()
                _temp_vm_list = _stdout.split(",")
                for each_vm in _temp_vm_list:
                    if each_vm != "":
                        each_vm = each_vm.strip()
                        if re.match("^[A-Za-z0-9_-]*$", each_vm):
                            _all_vm_list.append(each_vm)
                        else:
                            self.log.info(
                                "Unicode VM are not supported for now")

            return _all_vm_list

        except Exception as err:
            self.log.exception(
                "An exception occurred while getting all Vms from Hypervisor")
            raise Exception(err)

    def check_vms_exist(self, vm_list):
        """

        Check each VM in vm_list exists in Hypervisor VMs Dict

        Args:
            vm_list (list): List of VMs to check

        Returns:
            True (bool): If All VMs are present

            False (bool): If any VM is absent

        """
        if isinstance(vm_list, str):
            vm_list = [vm_list]
        present_vms = self.get_all_vms_in_hypervisor(server=self.server_list)
        present_vms = set(present_vms)
        if (set(vm_list) & set(present_vms)) == set(vm_list):
            return True
        else:
            return False

    def mount_disk(self, vm_obj, _vhdpath, destination_client=None):
        """
        mount the disk and return the drive letter mounted

        vm_obj -         (str)    - Vm helper object of the VM for which disk has to be mounted

        _vhdpath    (str)    - diks path has to be mounted

        destination_client  (obj)   - client where the disk to be mounted are located

        return:
                _drive_letter    (list)    - drive lettter in which disk is mounted

        Exception:
                if disk failed to mount

        """
        try:

            _drive_letter = vm_obj.mount_vhd(_vhdpath, destination_client)
            if not _drive_letter:
                self.log.error("VsHD might be corrupted mouting failed,")
                raise Exception("Cannot Mount the disk")

            else:
                self.log.info("Mounting restored VHD was succesfull")
                self.log.info("Drive letter is %s" % _drive_letter)
                return _drive_letter

        except Exception as err:
            self.log.exception(
                "exception raised in Mounting Disk , cannot proceed")
            raise err

    def un_mount_disk(self, vm_obj, _vhdpath, destination_client=None):
        """
        unmount the disk taht is mounted

         vm_obj -         (str)    - Vm helper object of the VM for which disk has to be unmounted

        _vhdpath    (str)    - diks path has to be unmounted

        destination_client (obj) -  destination_machine object where disk is mounted


        Exception:
                if disk failed to unmount

        """
        try:
            self.log.info("Trying to unmount diks %s" % _vhdpath)
            if not os.path.isdir(_vhdpath):
                self.log.info("VHD file exists...unmounting the file")
                vm_obj.un_mount_vhd(_vhdpath, destination_client)
            else:
                self.log.info(
                    "Mountpath provided for cleanup...checking for vhd files")
                for root, dirs, files in os.walk(_vhdpath):
                    for file in files:
                        filename, ext = os.path.splitext(file)
                        if ((ext == ".vhd") or (ext == ".vhdx") or
                                (ext == ".avhd") or (ext == ".avhdx")):
                            _vhdpath = os.path.join(root, file)
                            self.log.info("Found VHD file... " + _vhdpath)
                            vm_obj.un_mount_vhd(_vhdpath, destination_client)

        except Exception as err:
            self.log.exception(
                "exception raised in UnMounting Disk , cannot proceed")
            raise err

    def get_cluster_storage(self, proxy_ip):
        try:
            if not self.proxy_machine_obj.get(proxy_ip):
                self.proxy_machine_obj[proxy_ip] = machine.Machine(proxy_ip, self.commcell)
            
            # Get path for GetHypervProps.ps1
            _ps_path = os.path.join(
                self.utils_path, self.operation_ps_file)
            proxy_machine = self.proxy_machine_obj[proxy_ip]
            self.prop_dict["server_name"] = proxy_machine.machine_name
            
            # If the hostname in CS is Ip address instead of hostname of machine then fetch hostname.
            if validate_ipv4(proxy_ip):
                self.prop_dict["property"] = "GetHostName"
                proxy_ip = proxy_machine._execute_script(_ps_path, self.prop_dict).formatted_output.split("=", 1)[1]
            
            proxy_ip = proxy_ip.split('.')[0]
            # Get root path for CSV. Example: C:\ClusterStorage
            self.prop_dict["property"] = "GetCSVRootPath"
            path_obj = proxy_machine._execute_script(_ps_path, self.prop_dict)
            root_path = path_obj.formatted_output.split('=', 1)[1]
            
            # Get owner for all CSV Volumes present.
            self.prop_dict["property"] = "GetCSVOwner"
            output = proxy_machine._execute_script(_ps_path, self.prop_dict)
            _std_output = output.formatted_output.split('=', 1)[1]
            _std_output = _std_output.split(",")[:-1]

            cluster_obj = {}
            if len(_std_output) > 0:
                # For each cluster storage get its owner node
                for _stdout in _std_output:
                    _stdout = _stdout.split("+")
                    cluster_obj[_stdout[0]] = [_stdout[1]]

                # Get VolumeFriendlyName for each CSV Volume
                self.prop_dict["property"] = "GetVolumeFriendlyName"
                output = proxy_machine._execute_script(_ps_path, self.prop_dict).formatted_output.split('=', 1)[1]
                _std_output = output.split(',')[:-1]
                # Merge volume friendly name with root path to create actual CSV path . Example : C:\ClusterStorage\Volume1
                for _stdout in _std_output:
                    _stdout = _stdout.split("+")
                    _path = "{}\\{}".format(root_path, _stdout[1])
                    if _path not in cluster_obj[_stdout[0]]:
                        cluster_obj[_stdout[0]].append(_path)
                _volume_list = []
                # Append the CSV path in volume list if it belongs to proxy machine
                for cluster_disk in cluster_obj:
                    if proxy_ip.upper() in cluster_obj[cluster_disk]:
                        _volume_list.append(cluster_obj[cluster_disk][1].strip())

                return _volume_list
            else:
                raise Exception("Cluster Disk not found")

        except Exception as err:
            self.log.exception(
                "Could not fetch Cluster Info"
            )
            raise err


    def _get_datastore_dict(self, proxy, proxy_host_name):
        """
        get the list of datastore in an proxy

        proxy                 (str)    - list of datastores in that
                                            particular proxy would be returned
        proxy_host_name       (str)    - host_name of the proxy

        Return:
                disk_size_dict    (dict)    - with drive as keys and size
                                                    as values in proxy provided
                                                        disk_size_dict = {'proxy-c':14586}

        """
        try:
            if proxy is None:
                proxy = self.server_host_name

            _disk_size_dict = {}

            _ps_path = os.path.join(self.utils_path, self.operation_ps_file)
            self.prop_dict["vm_name"] = proxy_host_name
            self.prop_dict["property"] = "DISKSIZE"
            self.prop_dict["server_name"] = proxy_host_name
            proxy_machine = machine.Machine(proxy, self.commcell)
            output = proxy_machine._execute_script(_ps_path, self.prop_dict)

            _stdout = output.output
            if _stdout:
                _stdout = _stdout.strip()
                _stdout = _stdout.split("=")[1]
                _stdlines = [disk for disk in _stdout.split(",") if disk]
                for _each_disk in _stdlines:
                    _diskname = proxy + "-" + _each_disk.split("-")[0]
                    _disksize = _each_disk.split("-")[1]
                    _disk_size_dict[_diskname] = int(float(_disksize))

            return _disk_size_dict

        except Exception as err:
            self.log.exception("exception raised in GetDatastoreDict Disk ")
            raise err

    def _get_host_memory(self, proxy, proxy_host_name):
        """
        get the free memory in proxy

        Args:

                proxy     (str)    - list of datastores in that particular proxy would be returned

                proxy_host_name       (str)    - host_name of the proxy

        return:
                val     (int)    - free  memory of Host in GB eg:; 3GB

        Exception:
                Raise exception when failed to get Memeory

        """
        try:
            if proxy is None:
                proxy = self.server_host_name

            _ps_path = os.path.join(self.utils_path, self.operation_ps_file)
            self.prop_dict["property"] = "HostMemory"
            self.prop_dict["server_name"] = proxy_host_name
            proxy_machine = machine.Machine(proxy, self.commcell)
            output = proxy_machine._execute_script(_ps_path, self.prop_dict)

            _stdout = output.output
            if _stdout:
                _stdout = _stdout.strip()
                val = int(float(_stdout.split("=")[1]))
                return val

            else:
                raise Exception("Failed to get Memory")

        except Exception as err:
            self.log.exception("exception raised in GetMemory  ")
            raise err

    def _get_host_network(self, proxy, proxy_host_name):
        """
        Get the host network card name

        Args:

                proxy               (str)   - Name of the proxy client

                proxy_host_name     (str)   - Host_name of the proxy

        return:
                str - Network card present in the host machine

        Exception:
                Raise exception when failed to get network card

        """
        try:
            if proxy is None:
                proxy = self.server_host_name

            _ps_path = os.path.join(self.utils_path, self.operation_ps_file)
            self.prop_dict["property"] = "HostNetwork"
            self.prop_dict["server_name"] = proxy_host_name
            proxy_machine = machine.Machine(proxy, self.commcell)
            output = proxy_machine._execute_script(_ps_path, self.prop_dict)

            _stdout = output.output
            if _stdout:
                _stdout = _stdout.strip()
                val = _stdout.split("=")[1]
                return val

            else:
                raise Exception("Failed to get Network")

        except Exception as err:
            self.log.exception("Failed to get Network")
            raise err

    def _get_datastore_priority_list(self, vsa_proxy_list, host_dict):
        """
        From the given list of proxy get all the details of drive and space
                                                                and order them in increasing size

        Args:
                vsa_proxy_list            (list)    - list of proxies which needs to be
                                                                    ordered as per disk size

                host_dict                 (dict)    -dictionary of proxies and their matching host name
        returns:
            _sorted_datastore_dict(dict)    - with disk proxy-drive name as keys and size as values
                                                        _sorted_datastore_dict = {'proxy-c':14586,
                                                                                  'proxy1-D':12456}

        """
        try:
            _datastore_dict = {}
            for _each_proxy in vsa_proxy_list:
                _datastoredict = self._get_datastore_dict(_each_proxy, host_dict[_each_proxy])
                _datastore_dict.update(_datastoredict)
            _sorted_datastore_dict = OrderedDict(sorted(_datastore_dict.items(),
                                                        key=itemgetter(1), reverse=True))
            return _sorted_datastore_dict

        except Exception as err:
            self.log.exception(
                "An Aerror occurred in  GetDatastorePriorityList ")
            raise err

    def _get_proxy_priority_list(self, vsa_proxy_list, host_dict):
        """
        get the free host memory in proxy and arrange them with increarsing order

        Args:
                vsa_proxy_list            (list)    - list of proxies which needs to be
                                                    ordered as per Host Memory

                host_dict                 (dict)    -dictionary of proxies and their matching host name
        returns:
                _sorted_proxy_dict    (dict)    - with disk proxy name as keys and memory as values
                                                                _sorted_proxy_dict = {'proxy':5GB,
                                                                                     'proxy1':4GB}

        """
        try:

            _proxy_dict = {}
            for each_proxy in vsa_proxy_list:
                _proxy_memory = self._get_host_memory(each_proxy, host_dict[each_proxy])
                _proxy_dict[each_proxy] = int(_proxy_memory)

            _sorted_proxy_dict = OrderedDict(sorted(_proxy_dict.items(),
                                                    key=itemgetter(1), reverse=True))
            return _sorted_proxy_dict

        except Exception as err:
            self.log.exception("An Aerror occurred in  GetProxyPriorityList ")
            raise err

    def _get_required_memory_for_restore(self, vm_list):
        """
        sums up all the memory of needs to be restores(passed as VM list)

        Args:
                vm_list    (list)    - list of vm to be restored

        returns:
                sum of total memory of VM to be restored in Gb
        """
        try:

            _vm_total_memory = 0
            for _each_vm in vm_list:
                if self.VMs[_each_vm].guest_os.lower() == "windows":
                    self.VMs[_each_vm].update_vm_info('memory')
                    _vm_memory = self.VMs[_each_vm].memory.strip()
                    _vm_total_memory = _vm_total_memory + int(_vm_memory)

            return _vm_total_memory

        except Exception as err:
            self.log.exception(
                "An Aerror occurred in  _get_required_memory_for_restore ")
            raise err

    def _get_required_diskspace_for_restore(self, vm_list):
        """
        sums up all the disk space of needs to be restores(passed as VM list)

        Args:
                vm_list    (list)    - list of vm to be restored

        returns:
                sum of total disk space of VM to be restored
        """
        try:

            _vm_total_disk_size = 0
            for _each_vm in vm_list:
                if self.VMs[_each_vm].guest_os.lower() == "windows":
                    storage_details = self.VMs[_each_vm].machine.get_storage_details()
                    _vm_total_disk_size += int(storage_details['total'])
            _vm_total_disk_size = int(_vm_total_disk_size / 1024)
            return _vm_total_disk_size

        except Exception as err:
            self.log.exception(
                "An error occurred in  _get_required_diskspace_for_restore ")
            raise err

    def get_disk_in_the_path(self, folder_path, destmachine = None):
        """
         get all the disks in the folder

        Args:
            folder_path     (str)   - path of the folder from which disk needs to be listed
                                        e.g: C:\\CVAutomation

            destmachine      (obj)   - destination machine object

         Returns:
                disk_list   (list)-   list of disks in the folder

        Raises:
            Exception:
                if failed to get the list of files
        """
        try:
            _disk_list = []
            if destmachine:
                output = destmachine.get_files_in_path(folder_path)
            else:
                output = self.machine.get_files_in_path(folder_path)

            for value in output:
                disk_name_with_path = value
                disk_name = os.path.basename(disk_name_with_path)
                if any(re.search(ext, disk_name.lower()) for ext in self.disk_extension):
                    _disk_list.append(disk_name)

            return _disk_list

        except Exception as err:
            self.log.exception(
                "Exception occurred {0} in getting disk list".format(err)
            )

    def compute_free_resources(self, proxy_list, host_dict, vm_list):
        """
        compute the free hosting hypervisor and free space for disk in hypervisor

        Args:
                proxy_list    (list)    -list of proxies from which best proxy has to found

                host_dict     (dict)    -dictionary of proxies and their matching host name

                vm_list        (list) - list of Vms to be restored

        return:
                proxy_name    (str)    - the proxy where restore can be performed

                datastore_name(str)    - datastore where restore has to be performed
        """
        try:

            proxy_name = None
            datastore_name = None
            for each_vm in vm_list:
                self.VMs[each_vm].update_vm_info('All', force_update=True)

            _proxy_priority_dict = self._get_proxy_priority_list(proxy_list, host_dict)
            _datastore_priority_dict = self._get_datastore_priority_list(
                proxy_list, host_dict)
            _total_vm_memory = self._get_required_memory_for_restore(vm_list)
            _total_disk_space = self._get_required_diskspace_for_restore(
                vm_list)

            for each_datastore in _datastore_priority_dict.items():
                if (each_datastore[1]) > _total_disk_space:
                    datastore_name = each_datastore[0].split("-")[-1]
                    proxy_name = each_datastore[0].rsplit("-", 1)[0]
                    network = self._get_host_network(proxy_name, host_dict[proxy_name])
                    self.log.info(
                        "The Datastore %s has more than total disk space in VM" % datastore_name)
                    if _proxy_priority_dict[proxy_name] > _total_vm_memory:
                        self.log.info(
                            "the Proxy %s has higher memory than the total VMs" % proxy_name)
                        break
                    else:
                        continue
                else:
                    continue

            return proxy_name, datastore_name, network

        except Exception as err:
            self.log.exception("An Aerror occurred in  ComputeFreeResources ")
            raise err

    def check_cbt_driver_running(self, proxy_list, host_dict):
        """
        check if CBT driver is running on the hyperv node

        Args:
                proxy_list    (list)    -list of proxies/ hyperv nodes

                host_dict     (dict)    -dictionary of proxies and their matching host name

        Exception:
                If unable to check CBT driver status
        """
        try:
            for each_proxy in proxy_list:
                driver_state = r'cmd.exe /c "sc query cvcbt"'
                proxy_machine = machine.Machine(each_proxy, self.commcell)
                output = proxy_machine.execute_command(driver_state)

                if re.search("RUNNING", output._output):
                    self.log.info("The CVCBT driver is running on proxy {0}".format(each_proxy))
                else:
                    raise Exception("The CVCBT driver is not running on the proxy {0}".format(each_proxy))

        except Exception as err:
            self.log.exception(
                "An error occurred in  checking if CVCBT driver is running  ")
            raise err

    def check_or_set_cbt_registry(self, proxy_list, host_dict, instanceno_dict):
        """
        Check/Set if CBT registry for CBT testing is set on the proxies

        Args:
                proxy_list    (list)    -list of proxies/ hyperv nodes

                host_dict     (dict)    -dictionary of proxies and their matching host name

        Returns:
                CBTStatFolder (String) -Folder path where CBT stats are collected

        Raises:
            Exception:
                An error occurred while checking/creating the registry
        """
        try:
            for each_proxy in proxy_list:
                proxy_machine = machine.Machine(each_proxy, self.commcell)
                proxy_machine.instance = instanceno_dict[each_proxy]
                registry_path = "VirtualServer"
                output = proxy_machine.check_registry_exists(registry_path, "sCVCBTStatsFolder")
                if output:
                    CBTStatFolder = proxy_machine.get_registry_value(registry_path, "sCVCBTStatsFolder")
                else:
                    CBTStatFolder = "C:\\CBTStatus"
                    output = proxy_machine.create_registry(registry_path, "sCVCBTStatsFolder", CBTStatFolder, "String")
                    output = proxy_machine.create_registry(registry_path, "bDumpCVCBTStatsToFile", "00000001", "DWord")
                    output = proxy_machine.create_registry(registry_path, "bDumpCVCBTStats", "00000001", "DWord")

                if not output:
                    raise Exception("An error occured while creating the registry")
                else:
                    self.log.info("Checked and created CBT driver dump stats registry")
            return CBTStatFolder
        except Exception as err:
            self.log.exception(
                "An error occurred while checking/creating the registry  ")
            raise err


    def get_hyperv_default_folder(self, hostname):
        """
        get hyperv default folder for specified host machine

        hostname        (str) - Hostname of the proxy

        """

        host_machine = machine.Machine(hostname, self.commcell)
        _ps_path = os.path.join(self.utils_path, self.operation_ps_file)
        self.prop_dict["server_name"] = hostname
        self.prop_dict["property"] = "GetHyperVDefaultFolder"
        _stdout = host_machine._execute_script(_ps_path, self.prop_dict).formatted_output.split('=', 1)[1]
        return _stdout