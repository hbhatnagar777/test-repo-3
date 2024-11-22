# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for OracleVM vm"""

from time import sleep
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils import VirtualServerUtils


class OracleVMVM(HypervisorVM):
    """
    This is the main file for all Oracle VM operations
    """

    def __init__(self, hvobj, vm_name):
        """
        Initialization of Oracle VM properties

        _get_disk_info()            - Get the name, path and size of the disks available

        _get_nic_info()             - Get the name, IP and MACs of the available NICs

        _get_vm_info()              - Fetches Basic/Advanced VM properties

        update_vm_info()            - Fetch all the properties of vm by calling _get_vm_info()

        _wait_for_job()             - Waits on a job to complete and returns the result

        _do_vm_operation()          - Perform a VM operation requested

        power_off()                 - power off the VM

        power_on()                  - power on the VM

        delete_vm()                 - delete the VM

        """

        super(OracleVMVM, self).__init__(hvobj, vm_name)
        self.hvobj = hvobj
        self.server_name = self.hvobj.server
        self._server_host_name = self.hvobj.server_host_name
        self.vm_name = vm_name
        self._vm_id = self.hvobj.vm_dict[vm_name].split("/")[-1]
        self._base_url = "https://" + self._server_host_name + ":7002/ovm/core/wsapi/rest"
        self.guid = None
        self.ip = None
        self.guest_os = None
        self.host_name = None
        self.disk_path = None
        self.memory = None
        self.disk_list = None
        self.disk_dict = None
        self._vm_state = None
        self.no_of_cpu = None
        self._basic_props_initialized = False
        self.update_vm_info()

    def _get_disk_info(self, vm_disk_mapping_list):
        """
        Get the name, path and size of the disks available
        Args:
            vm_disk_mapping_list    (list):  response of the disk mapping call

        Returns:
            _disks       (list)     List of the disk with Name, Path and Size

        Raises:
            Exception:
                if it fails to get disk info

        """

        _disks = []
        try:
            for disk in vm_disk_mapping_list:
                flag, disk_mapping_info = self.hvobj._make_request("GET", disk["uri"])
                disk_mapping_info = disk_mapping_info.json()
                flag, virtual_disk = self.hvobj._make_request("GET",
                                                              disk_mapping_info["virtualDiskId"][
                                                                  "uri"])
                virtual_disk = virtual_disk.json()
                _vm_disk = {}
                _vm_disk["name"] = virtual_disk.get("name",
                                                    disk_mapping_info["virtualDiskId"]["name"])
                _vm_disk["path"] = virtual_disk.get("path", "")
                _vm_disk["size"] = VirtualServerUtils.bytesto(virtual_disk["size"], "GB")
                _vm_disk["slot"] = disk_mapping_info["diskTarget"]
                _vm_disk["repository"] = virtual_disk["repositoryId"]["name"]
                _disks.append(_vm_disk)
            return _disks
        except Exception as err:
            self.log.exception("An exception occurred in _get_disk_info")
            raise Exception(err)

    def _get_nic_info(self, nics_list):
        """
        Get the name, IP and MACs of the available NICs
        Args:
            nics_list: list if the nics

        Returns:
            _nics           (List)     list of dicts with name, ip and mac address

        Raises:
            Exception:
                if it fails to get nics details

        """

        _nics = []
        try:
            for nic in nics_list:
                flag, nic_response = self.hvobj._make_request("GET", nic["uri"])
                nic_response = nic_response.json()
                _vm_nic = {}
                _vm_nic["name"] = nic_response["name"]
                _vm_nic["macAddress"] = nic_response["macAddress"]
                _vm_nic["ipAddress"] = []
                if len(nic_response["ipAddresses"]) > 0:
                    _ip_addresses = []
                    for ip_address in nic_response["ipAddresses"]:
                        _ip_addresses.append(ip_address["address"])
                    _vm_nic["ipAddress"] = _ip_addresses

                _nics.append(_vm_nic)
            return _nics
        except Exception as err:
            self.log.exception("An exception occurred in _get_nic_info")
            raise Exception(err)

    def _get_server_repos_list(self, server):
        """
        Get server repo list
        Args:
            server          (string):   server name

        Returns:
            repose_under_server     (list): repository list

        """
        _repos_list = self.hvobj._get_server_repositories(server)
        repos_under_server = []
        for repo in _repos_list:
            repos_under_server.append(repo["name"])
        return repos_under_server

    def _get_vm_info(self):
        """
        Fetches Basic/Advanced VM properties

        Returns:
            Sets the VM properties to instance and returns the
                 vm rest call json

        Raises:
            Exception:
                if it fails to get vm info

        """

        _available_servers = self.hvobj.get_servers()
        vm_list = []
        for server_dict in _available_servers:
            vm_list.extend(filter(lambda elem: self.vm_name == elem["name"], server_dict["vmIds"]))
        if len(vm_list) == 0:
            raise Exception("VM with name {0} doesn't exist".format(self.vm_name))
        elif len(vm_list) == 1:
            self._vm_id = vm_list[0]["value"]
        else:
            raise Exception("Multiple VMs exist with name {0}".format(self.vm_name))
        _vm_url = self._base_url + "/Vm/" + self._vm_id
        try:
            self._vm_info = {}
            flag, vm_response = self.hvobj._make_request("GET", _vm_url)
            if flag:
                self._vm_info = vm_response.json()
                self._vm_state = self._vm_info["vmRunState"]
                self.server_name = self._vm_info["serverId"]["name"]
                self.server_repos = self._get_server_repos_list(self.server_name)
                self.guest_os = VirtualServerUtils.get_os_flavor(self._vm_info["osType"])
                self.no_of_cpu = self._vm_info["cpuCount"]
                self.memory = VirtualServerUtils.bytesto(self._vm_info["memory"] * (1024 ** 2),
                                                         "GB")
                self.disks = self._get_disk_info(self._vm_info["vmDiskMappingIds"])
                self.disk_list = [disk["name"] for disk in self.disks]
                self.disk_dict = self.disk_list
                self.disk_count = len(self.disks)
                self.nics = self._get_nic_info(self._vm_info["virtualNicIds"])
                self.ip = self.nics[0]["ipAddress"][0] if \
                    len(self.nics[0]["ipAddress"]) else self.ip
                self.nic_count = len(self.nics)
                self.vm_space = sum(disk["size"] for disk in self.disks)
                self.guid = self._vm_info['id']['value']
                self._basic_props_initialized = True
            return self._vm_info
        except Exception as err:
            self.log.exception("An exception occurred while making a call to {}".format(_vm_url))
            raise Exception(err)

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
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

        Raises:
            Exception:
                if failed to update all the properties of the VM
        """

        try:
            if not self._basic_props_initialized or force_update:
                self._get_vm_info()

            if prop == 'All' and os_info:
                self.vm_guest_os = self.guest_os
                self.get_drive_list()

            elif hasattr(self, prop):
                return getattr(self, prop, None)

        except Exception as err:
            self.log.exception(
                "Failed to Get  the VM Properties of the VM with the exception {0}".format(err)
            )
            raise Exception(err)

    def get_disk_in_controller(self, number, location):
        """
        get the disk associated with controller

        Args:
                number            (int)    - IDE(1:0) 1 is the disk number

                location        (int)    - IDE(1:0) 0 is the location in disk number 1

        Return:
                _disks_at_slots    (str)    - disks in location of args(eg: disk in IDE(1:0))

        Raises:
            Exception:
                if it fails to get disk in controller

        """
        try:
            _disks_at_slots = []
            if number.isdigit() and location.isdigit():
                for disk_slot in range(int(number), int(location) + 1):
                    _index, _disk_dict = VirtualServerUtils.find(self.disks, "slot", disk_slot)
                    if _index != -1:
                        _disks_at_slots.append(_disk_dict["name"])

            return _disks_at_slots

        except Exception as err:
            self.log.exception("Exception in getting disk in controller")
            raise err

    def get_disks_by_repository(self, repository):
        """
        getting disk of the repository

        Args:
            repository          (string):   repository

        Returns:
            _repository_disks       (list):     list of repository disks

        """

        _repository_disks = []
        if repository in self.server_repos:
            for _disk in self.disks:
                if _disk["repository"] == repository:
                    _repository_disks.append(_disk["name"])

        return _repository_disks

    def _wait_for_job(self, job_uri, update_vm_properties=False, pooling_interval=10):
        """
        Waits on a job to complete and returns the result
        Args:
            job_uri: uri for making the job request

            update_vm_properties: when set to True will update the VM properties
                                     after the job is completed

            pooling_interval: job pooling time

        Returns:
            (boolean)  Job Result

        """

        while True:
            sleep(pooling_interval)
            job_request_flag, job_response = self.hvobj._make_request("GET", job_uri)
            job = job_response.json()
            if job['summaryDone']:
                self.log.info(
                    '{name}: {runState}'.format(name=job['name'], runState=job['jobRunState']))
                if job['jobRunState'].upper() == 'FAILURE':
                    raise Exception('Job failed: {error}'.format(error=job['error']))
                elif job['jobRunState'].upper() == 'SUCCESS':
                    if update_vm_properties:
                        self.update_vm_info()
                    return job['done']
                else:
                    break

    def _do_vm_operation(self, operation_type=None, method="PUT", operation_url=None):
        """
        Perform a VM operation requested
        Args:
            operation_type              (string):   type of operation - start, stop, restart

            method                      (string):   REST methods

            operation_url               (string):   overwrites operation_type when provided

        Returns:
                True - when action  is successful

                False -  when action is failed


        """
        if operation_url is not None:
            _vm_operation_url = operation_url
        else:
            _vm_operation_url = "/".join([self._base_url, 'Vm', self._vm_id, operation_type])
        request_flag, operation_response = self.hvobj._make_request(method, _vm_operation_url)
        operation_response = operation_response.json()
        return self._wait_for_job(operation_response["id"]["uri"])

    def power_on(self):
        """
        Power On the VM.

        Returns:
                True - Powering on VM was successful

                False -  Powering on VM failed

        """
        job_result = False
        if self._vm_state.upper() != "RUNNING":
            job_result = self._do_vm_operation("start")
        return job_result

    def power_off(self):
        """
        Power off the VM.

        Return:
                True - Powering off VM was successful

                False -  Powering odd VM fails

        """
        job_result = False
        if self._vm_state.upper != "STOPPED":
            """
            If power on operation ran recently this task will take more than a minute
            """
            job_result = self._do_vm_operation("stop")
        return job_result

    def delete_vm(self):
        """
        Delete the VM.

        Returns:
                True - Deleting of vm is successful

                False -  Deleting of vm fails

        """
        if self._vm_state == "STOPPED":
            _delete_url = "/".join([self._base_url, 'Vm', self._vm_id])
            job_result = self._do_vm_operation(method="DELETE", operation_url=_delete_url)
            return job_result
        else:
            if self.power_off():
                self.delete_vm()

    def restart_vm(self):
        """
        Restart the VM.

        Returns:
                True - Restart of vm is successful

                False -  Restart of vm fails

        """
        if self._vm_state.upper() == "RUNNING":
            """
            If power on operation ran recently this task will take more than a minute
            """
            return self._do_vm_operation("restart")
        else:
            self.log.error("To restart, VM should be in running state. Current state is {}".format(
                self._vm_state))
