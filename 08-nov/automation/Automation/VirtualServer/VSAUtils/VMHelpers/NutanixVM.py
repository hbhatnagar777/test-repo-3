# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Nutanix vm"""

from AutomationUtils import machine
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from AutomationUtils.pyping import ping
import time
import re


class NutanixVM(HypervisorVM):
    """
        This is the main file for all Nutanix VM operations
    """

    def __init__(self, hvobj, vm_name):
        """
        Initialization of AzureRM VM properties

        Args:

            hvobj           (obj):  Hypervisor Object

            vm_name         (str):  Name of the VM

        """
        super(NutanixVM, self).__init__(hvobj, vm_name)
        self.vm_name = vm_name
        self.no_of_cpu = None
        self.power_state = None
        self.memory = None
        self.guid = None
        self.host_uuid = None
        self._basic_props_initialized = False
        self.host_name = None
        self.host_machine = machine.Machine()
        self.nic_count = 0
        self.nic_info = None
        self.disk_count = 0
        self.disk_info = None
        self.disk_dict = {}
        self._disk_list = None
        self.snapshot_count = 0
        self.container_uuid = None
        self.vm_container = None
        self.update_vm_info()

    @property
    def disk_list(self):
        """To fetch the disk in the VM
        Return:
            disk_list   (list)- list of disk in VM
        """
        if self.disk_dict:
            self._disk_list = self.disk_dict

        else:
            self._disk_list = []

        return self._disk_list

    def get_vm_config(self):
        """
        Get all VM Config Information

        Raises:
            Exception:
                if failed to get information about VM
        """
        try:
            vm_info = self.get_vm_info(self.vm_name)
            if vm_info:
                if "uuid" in vm_info:
                    self.guid = vm_info.get("uuid", None)
                    self.power_state = vm_info.get("state", None)
                    self.host_uuid = vm_info.get("hostUuid", None)
                if "config" in vm_info:
                    self.no_of_cpu = vm_info["config"].get("numVcpus", None)
                    self.memory = vm_info["Memory"] = vm_info["config"].get("memoryMb", None)
                    if "vmNics" in vm_info["config"]:
                        self.nic_count = len(vm_info["config"]["vmNics"])
                        self.nic_info = vm_info["config"]["vmNics"]
                    if "vmDisks" in vm_info["config"]:
                        self.disk_count = len(vm_info["config"]["vmDisks"])
                        self.disk_info = vm_info["config"]["vmDisks"]
                        self.disk_dict = self.disk_info
            else:
                self.log.info("vm_info is empty Strange error.")

            snap_info = self.hvobj.get_snap_info(self.guid)
            if snap_info:
                if snap_info["linkList"] != None:
                    self.snapshot_count = len(snap_info["linkList"])

        except Exception as err:
            self.log.exception("Exception in get_vm_config")
            raise Exception(err)

    def get_disk_config(self, force_update=False):
        """
        To fetch the disk in the VM
        Args:
            force_update - to refresh all the properties always
                True : ALways collect  properties
                False: refresh only if properties are not initialized
        Return:
            disk_list   (list)- list of disk in VM
        Raises:
            Exception:
                    if failed to get disk config
        """
        try:
            if force_update:
                vm_info = self.get_vm_info(self.vm_name)

            if vm_info:
                if "config" in vm_info:
                    if "vmDisks" in vm_info["config"]:
                        self.disk_count = len(vm_info["config"]["vmDisks"])
                        self.disk_info = vm_info["config"]["vmDisks"]
                        self.disk_dict = self.disk_info
            else:
                self.log.info("vm_info is empty Strange error.")
        except Exception as err:
            self.log.exception("Exception in get_disk_config")
            raise Exception(err)

    def get_os_type(self):
        """
        Get the OS Type of VM

        Raises:
            Exception:
                    if failed to connect to VM or gets unexpected ttl value
        """
        # Extract TTL value form the response.output string.
        _attempt = 0
        while _attempt < 3:
            try:
                self.log.info("Pinging the vm : {}, Attempt no {}".format(self.ip, _attempt))
                response = ping(self.ip)
                ttl = int(re.match(r"(.*)ttl=(\d*) .*",
                                   response.output[2]).group(2))
                break
            except AttributeError:
                _attempt += 1
                if _attempt < 3:
                    self.log.info("Ping failed. for vm {}. Trying after 1 min".format(self.ip))
                    time.sleep(60)
                else:
                    self.log.exception("Exception in get_os_type")
                    raise AttributeError('Failed to connect to the machine.\nError: "{}"'.format(
                        response.output)
                    )
        if ttl < 256:
            if 64 < ttl <= 128:
                self.guest_os = "windows"
            else:
                self.guest_os = "linux"
        else:
            self.log.exception("Exception in get_os_type")
            raise ValueError('Got unexpected TTL value.\nTTL value: "{}"'.format(ttl))

    def get_vm_info(self, vmname):
        """
        Get all VM information

        Raises:
            Exception:
                if failed to get information about VM
        """
        try:
            vm_info_url = self.hvobj.url + 'vms' + '/?includeVMDiskSizes=true&includeAddressAssignments=true'
            data = self.hvobj.nutanixsession.get(vm_info_url, verify=False).json()
            self.log.info("Dump VMInfoURL: " + vm_info_url)
            vmlist = data["entities"]
            for vm in vmlist:
                if vm["config"]["name"] == vmname:
                    containername = self.get_container_name(
                [vm["config"]["vmDisks"][1]["containerUuid"]])
                    vm['containerName'] = containername[0]
                    self.log.info("Dump VMInfo: " + str(vm))
                    return vm
            return None  # No VMs found
        except Exception as err:
            self.log.exception("Exception in get_vm_info")
            raise Exception(err)


    def get_container_name(self, container_uuid):
        """
        Get container name of the source VM
        Args:
            container_uuid   (list):   id of the container
        Return:
            containerlist    (list):   list of containers of a VM
        Raises:
            Exception:
                if failed to get information about VM
        """
        try:
            containerlist = []
            for index in container_uuid:
                vm_info_url = self.hvobj.v2url + 'storage_containers/' + index
                data = self.hvobj.nutanixsession.get(vm_info_url, verify=False).json()
                self.log.info("Dump VMInfoURL: " + vm_info_url)
                containerlist.append(data["name"])
            return containerlist

        except Exception as err:
            self.log.exception("Exception in get_vm_container_name")
            raise Exception(err)

    def get_snapshot(self):
        """
        Get all the VM snapshot
        Return:
            data - total number of snapshot of a VM

        Raises:
            Exception:
                if failed to get information about VM
        """
        try:
            vm_info_url = self.hvobj.v3url + '/vm_snapshots/list'
            d={"filter":f"entity_uuid=={self.guid}",
                "kind":"vm_snapshot",
                "sort_order":"ASCENDING"}
            data = self.hvobj.nutanixsession.post(vm_info_url, json=d).json()
            self.log.info("Dump VMSnapshotList: " + str(data))
            return data

        except Exception as err:
            self.log.exception("Exception in get_vm_snapshot")
            raise Exception(err)

    def get_nic_info(self):
        """
        Get all VM NIC information

        Raises:
            Exception:
                if failed to get NIC info of corresponding VM
        """
        try:
            for nic in self.nic_info:
                self.nic_uuid = nic['networkUuid']
        except Exception as err:
            self.log.exception("Exception in update_nic_info")
            raise Exception(err)

    def get_vm_hostname(self):
        """
        Get host name where VM is hosted

        Raises:
            Exception:
                if failed to get host name
        """
        try:
            vmhost_url = self.hvobj.url + 'networks/' + self.nic_uuid
            self.log.info("Dump VMHostURL: " + vmhost_url)
            data = self.hvobj.nutanixsession.get(vmhost_url, verify=False)
            response = data.json()
            self.log.info("Dump VMHostURL: " + str(response))
            if data.status_code == 200:
                self.vm_host = response['name']
        except Exception as err:
            self.log.exception("Exception in getting vm hostname")
            raise Exception(err)

    def get_vm_ip(self):
        """
        Get IP address of VM

        Raises:
            Exception:
                if failed to get IP address of corresponding VM
        """
        try:
            retry = 5
            do_retry = True
            ip_url = self.hvobj.v2url + 'vms/' + self.guid + '/nics/'
            self.log.info("Dump IPURL: " + ip_url)
            while retry > 0 and do_retry:
                data = self.hvobj.nutanixsession.get(ip_url, verify=False)
                response = data.json()
                self.log.info("Dump IPURLInfo: " + str(response))
                if data.status_code == 200:
                    network_detail = response["entities"][0]
                    self.ip = network_detail["ip_address"]

                    if self.ip == "0.0.0.0" or self.ip.find("169.") >= 0:
                        do_retry = True
                    else:
                        do_retry = False
                retry = retry - 1
            self.log.info("IP Address:" + str(self.ip))

        except Exception as err:
            self.log.exception("Exception in update_vm_ip")
            raise Exception(err)

    def update_vm_info(self, prop='Basic', os_info=True, force_update=False):
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

         Raises:
            Exception:
                if failed to get all the properties of the VM
        """

        try:
            if not self._basic_props_initialized or force_update:
                self.get_vm_config()
                self.get_nic_info()
                self.get_vm_hostname()
            if os_info or prop == 'All':
                self.change_power_state()
                self.get_vm_ip()
                self.get_os_type()
                self.vm_guest_os = self.guest_os
                self.get_drive_list()

        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def change_power_state(self, operation='on'):
        """
        Change power state of the VM
        Args:
            operation - operation on/off to perform on VM
        Returns:
            True if operation was successful
        Raise:
            Exception: 
                when operation was unsuccessful
        """

        try:
            if self.power_state != operation:
                attempt = 0
                while attempt < 5:
                    attempt += 1
                    power_state_url = self.hvobj.url + f'vms/{self.guid}/set_power_state'
                    data = self.hvobj.nutanixsession.post(power_state_url, json={"transition": operation})
                    if data.status_code == 200:
                        task_uuid = data.json()['taskUuid']
                        task_status_url = self.hvobj.url + f'tasks/{task_uuid}'
                        resp = self.hvobj.nutanixsession.get(task_status_url)
                        __stdout = resp.json()
                        task_status = __stdout["progressStatus"]
                        while task_status.lower() == "running":
                            self.log.info(f'Waiting 60 seconds for VM to power {operation}')
                            time.sleep(60)
                            resp = self.hvobj.nutanixsession.get(task_status_url)
                            __stdout = resp.json()
                            task_status = __stdout['progressStatus']
                        if task_status.lower() in ['succeeded', 'completed']:
                            self.log.info(f"Powered {operation} VM : {self.vm_name}")
                            self.get_vm_config()
                            return True
                        else:
                            exp = __stdout["metaResponse"]["errorDetail"]
                            self.log.error(f'{__stdout["metaResponse"]["error"]} - Error occured while powering {operation} VM:'
                                           f'{exp}')

                    else:
                        exp = data.text
                        self.log.error(f"{data.reason} - Error occurred while powering {operation} VM : {exp}")
                    self.log.info("Retrying after 1 min")
                    time.sleep(60)

                raise Exception(exp)

            else:
                self.log.info(f'VM: {self.vm_name} is already powered {operation}')
                return True

        except Exception as exp:
            self.log.error(f"Error occurred during Power {operation} : {exp}")