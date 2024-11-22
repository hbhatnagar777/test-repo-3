# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Red Hat vm"""

import time
import ipaddress
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils import VirtualServerUtils


class RedHatVM(HypervisorVM):
    """
    This is the main file for all Red Hat VM operations

    Methods:
        _get_vm_info()          -   gets the information about the VM

        get_nic_info()          -   gets IP addresses, MAC addresses, subnet IDs, and NIC names of
                                    VM

        get_vm_guid()           -   gets the GUID of the VM

        get_disk_info()         -   gets names of all disks and total size of disks

        get_status_of_vm()      -   gets the status of VM, e.g. up, down, etc.

        get_os_type()           -   gets the OS type of the VM

        power_off()             -   powers off the VM

        power_on()              -   powers on the VM

        restart_vm()            -   restarts the VM

        delete_vm()             -   deletes the VM

        update_vm_info()        -   updates the VM info
    """

    def __init__(self, Hvobj, vm_name):
        """
        Initialization of RedHat properties

        Args:
            Hvobj               (obj):  Hypervisor Object

            vm_name             (str):  Name of the VM
        """

        super(RedHatVM, self).__init__(Hvobj, vm_name)
        self.hvobj = Hvobj
        self.vm_name = vm_name
        self.guid, self.vm_status, self.os_type, self.ip = (None for _ in range(4))
        self.disk_list, self.ipv4, self.ipv6, self.mac_address, self.nic, self.subnet_ids = ([] for _ in range(6))
        self.total_disk_size, self.disk_count, self.memory, self.no_of_cpu = (0 for _ in range(4))
        self.disk_dict = {}
        self._basic_props_initialized = False
        self.connection = self.hvobj.connection
        self.update_vm_info()

    def _get_vm_info(self):
        """
        Gets all the info about the given VM

        Raises:
            Exception:
                If the vm data cannot be collected from the server
        """

        try:
            self.log.info("Getting all information of VM: {}".format(self.vm_name))
            vms_service = self.connection.system_service().vms_service()
            self.vm_info = vms_service.list(search='name={}'.format(self.vm_name))[0]
            self.vm_service = vms_service.vm_service(self.vm_info.id)
            self.get_vm_guid()
            self.get_status_of_vm()
            self.get_disk_info()
            self.get_nic_info()
            self.get_os_type()
            self._basic_props_initialized = True
        except Exception as err:
            self.log.exception("Exception in _get_vm_info")
            raise Exception(err)

    def get_nic_info(self):
        """
        Gets all IP addresses, MAC addresses, subnet IDs, and NIC names associated with the VM

        Raises:
            Exception:
                If network device information cannot be found
        """

        try:
            self.log.info("Getting the NIC info for VM: {}".format(self.vm_name))
            if (self.ipv4 != [] or self.ipv6 != [] or self.mac_address != [] or self.nic != []
                    or self.subnet_ids != []):
                self.ipv4, self.ipv6, self.mac_address, self.nic, self.subnet_ids = ([] for i in range(5))
            _attempt = 0
            while _attempt < 2:
                devices = self.vm_service.reported_devices_service().list()
                nics = self.vm_service.nics_service().list()
                self.log.info("Getting MACs, IPs, and subnets")
                for device in devices:
                    self.mac_address.append(device.mac.address)
                    if device.ips:
                        for ip in device.ips:
                            if ip.version.value == 'v4':
                                self.ipv4.append(ip.address)
                                if ip.netmask is not None:
                                    network = ipaddress.IPv4Network('{}/{}'.format(ip.address, ip.netmask))
                                    for subnet in network.subnets():
                                        self.subnet_ids.append(subnet)
                            elif ip.version.value == 'v6':
                                self.ipv6.append(ip.address)
                                if ip.netmask is not None:
                                    network = ipaddress.IPv6Network('{}/{}'.format(ip.address, ip.netmask))
                                    for subnet in network.subnets():
                                        self.subnet_ids.append(subnet)
                if self.ipv4:
                    self.ip = self.ipv4[0]
                    _attempt = 2
                else:
                    _attempt = _attempt + 1
                    self.re_add_nic()
                self.log.info("Getting NIC info")
                for nic in nics:
                    self.nic.append(nic.name)
        except Exception as err:
            self.log.exception("Exception in getting IP address")
            raise Exception(err)

    def get_vm_guid(self):
        """
        gets the GUID of VM

        Raises:
            Exception:
                If the GUID cannot be retrieved
        """

        try:
            self.log.info("Getting the guid for VM: {}".format(self.vm_name))
            self.guid = self.vm_info.id

        except Exception as err:
            self.log.exception("Exception in get_vm_guid")
            raise Exception(err)

    def get_disk_info(self):
        """
        gets the names of all attached disks and the total size of disks

        Raises:
            Exception:
                If disk info cannot be found
        """

        try:
            if self.disk_list != [] or self.total_disk_size != 0:
                self.disk_list = []
                self.total_disk_size = 0
            disk_attachments_service = self.vm_service.disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                disk = self.connection.follow_link(disk_attachment.disk)
                self.disk_list.append(disk.name)
                self.disk_dict[disk.id] = disk.name
                self.total_disk_size += VirtualServerUtils.bytesto(disk.provisioned_size, "GB")
        except Exception as err:
            self.log.exception("Exception in getting disk info of vm")
            raise Exception(err)

    def get_status_of_vm(self):
        """
        gets the current status of VM, e.g. up, down

        Raises:
            Exception:
                if the status of the vm cannot be retrieved
        """

        try:
            self.log.info("Getting Power status of VM: {}".format(self.vm_name))
            self.vm_status = self.vm_info.status.value
        except Exception as err:
            self.log.exception("Exception in get_status_of_vm")
            raise Exception(err)

    def get_os_type(self):
        """
        gets the OS type of the boot disk of the VM

        Raises:
            Exception:
                if the OS type of the VM cannot be retrieved
        """

        try:
            self.log.info("Getting the os info for VM: {}".format(self.vm_name))
            self.os_type = self.vm_info.os.type
            self.guest_os = self.vm_info.guest_operating_system.family
        except Exception as err:
            self.log.exception("Exception in Get OS Type")
            raise Exception(err)

    def re_add_nic(self):
        """
        Re adds the network

        Raises:
            Exception:
                If re adding the network gets issue
        """
        try:
            self.log.info("Removing nic of VM: {}".format(self.vm_name))
            nics_service = self.vm_service.nics_service()
            _name = nics_service.list()[0].name
            _id = nics_service.list()[0].id
            _pid = nics_service.list()[0].vnic_profile.id
            self.power_off()
            nics_service.nic_service(_id).remove()
            self.log.info("Removed nic of VM: {}".format(self.vm_name))
            self.log.info("Adding nic of VM: {}".format(self.vm_name))
            import ovirtsdk4.types as rhev_types
            nics_service.add(rhev_types.Nic(
                name=_name,
                vnic_profile=rhev_types.VnicProfile(id=_pid, ), ), )
            self.power_on()
            self.log.info("Added nic of VM: {}".format(self.vm_name))
        except Exception as err:
            self.log.exception("Exception in ere adding network")
            raise Exception(err)

    def power_off(self):
        """
        powers off the VM

        Raises:
            Exception:
                if the VM cannot be powered off
        """

        try:
            if self.vm_service.get().status.name.lower() == 'up':
                self.log.info("Shutting off VM: {}".format(self.vm_name))
                self.vm_service.shutdown()
                time.sleep(300)
            else:
                self.log.info("VM:{} is already powered off".format(self.vm_name))
        except Exception as err:
            self.log("Exception in power off")
            raise Exception(err)

    def power_on(self):
        """
        powers on the VM

        Raises:
            Exception:
                if the VM cannot be powered on
        """

        try:
            if self.vm_service.get().status.name.lower() != 'up':
                self.log.info("Powering on VM: {}".format(self.vm_name))
                self.vm_service.start()
                time.sleep(300)
            else:
                self.log.info("VM:{} is already powered on".format(self.vm_name))

        except Exception as err:
            self.log("Exception in power on")
            raise Exception(err)

    def restart_vm(self):
        """
        restarts the VM

        Raises:
            Exception:
                if the VM cannot be restarted
        """

        try:
            self.log.info("Restarting VM: {}".format(self.vm_name))
            self.vm_service.reboot()
            time.sleep(300)
        except Exception as err:
            self.log("Exception in restart")
            raise Exception(err)

    def delete_vm(self):
        """
        deletes the VM

        Raises:
            Exception:
                if the VM cannot be deleted
        """

        try:
            if self.vm_service.get().status.name.lower() == 'up':
                self.log.info("Powering off VM: {}".format(self.vm_name))
                self.vm_service.stop()
                time.sleep(10)
            self.log.info("Deleting VM: {}".format(self.vm_name))
            self.vm_service.remove()
        except Exception as err:
            self.log("Exception in delete")
            raise Exception(err)

    def clean_up(self):
        """
        Does the cleanup after the testcase.

        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned

        """

        try:
            self.log.info("Deleting VM after restore")
            self.delete_vm()
        except Exception as exp:
            raise Exception("Exception in Cleanup: {}".format(exp))

    def get_otherdetails(self):
        """
        gets the OS type of the boot disk of the VM

        Raises:
            Exception:
                if issue in getting either disk_count, memory or number of cpu
        """

        try:
            self.log.info("Getting the other info for VM: {}".format(self.vm_name))
            self.disk_count = len(self.disk_list)
            self.memory = self.vm_info.memory / 1048576
            self.no_of_cpu = self.vm_info.cpu.topology.cores * self.vm_info.cpu.topology.sockets
        except Exception as err:
            self.log.exception("Exception in get_otherdetails")
            raise Exception(err)

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
        """
        Updates properties of the VM
        Args:
            prop            (str):  can be Basic or All

                                    Basic - updates Basic properties of VM, like GUID, status

                                    All   - updates All the possible properties of the VM

            os_info         (bool):  To fetch os info or not

            force_update    (bool): to refresh all the properties always
                    True : Always collect  properties
                    False: refresh only if properties are not initialized
        Raises:
            Exception:
                if the VM properties cannot be updated
        """

        try:
            if not self._basic_props_initialized or force_update:
                self._get_vm_info()
            if self.vm_info.status.value != 'up':
                self.power_on()
                self._get_vm_info()
            if self.vm_info:
                if os_info or prop == 'All':
                    self.vm_guest_os = self.guest_os
                    self.get_drive_list()
                    self.get_otherdetails()
            else:
                self.log.info("VM info was not collected for this VM")
        except Exception as err:
            self.log.exception("Failed to update the VM properties")
            raise Exception(err)
