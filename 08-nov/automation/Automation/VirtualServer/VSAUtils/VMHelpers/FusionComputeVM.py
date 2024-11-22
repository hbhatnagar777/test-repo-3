# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Fusion Compute vm"""

from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from AutomationUtils import logger


class FusionComputeVM(HypervisorVM):
    """
    Class for Fusion Compute  VMs
    """

    def __init__(self, hvobj, vm_name):
        """
        Initialization of vmware vm properties

        Args:
            hvobj      (object): Hypervisor class object for Fusion Compute

            vm_name     (string): name of the VM for which properties can be fetched
        """

        super(FusionComputeVM, self).__init__(hvobj, vm_name)
        self.hvobj = hvobj
        self.server_name = self.hvobj.server_host_name
        self.vm_url = 'https://{}:{}{}'.format(self.server_name, self.hvobj.port, self.hvobj.vm_dict[vm_name])

        self.vm_operation = {
            'START_VM': '{}/action/start'.format(self.vm_url),
            'STOP_VM': '{}/action/stop'.format(self.vm_url),
            'RESTART_VM': '{}/action/reboot'.format(self.vm_url),
            'DELETE_VM': '{}/action/delete'.format(self.vm_url)
        }

        self.guid, self.ip, self.guest_os, self.host_name, self.vm_obj, self.disk_path = (None, ) * 6
        self.disk_list = []
        self._basic_props_initialized = False
        self.memory, self.disks, self.disk_count, self.nic_count, self.no_of_cpu, self.vm_space = (0, ) * 6
        self.disk_dict = {}
        self.update_vm_info()

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options, **kwargs):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()
            self.kwargs_options = kwargs

        def __eq__(self, other):
            """compares the source vm and restored vm"""

            if self.vm.vm.nic_count == other.vm.vm.nic_count:
                self.log.info("Network count matched")
            else:
                self.log.error("Network count failed")
                return False
            return True

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False, **kwargs):
        """
        fetches all the properties of the VM

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

        exception:
                if failed to get all the properties of the VM
        """

        try:
            if not self._basic_props_initialized or force_update:
                self._get_vm_info()

            if prop == 'All' or os_info:
                self.vm_guest_os = self.guest_os
                self.no_of_cpu = self.vm_obj['vmConfig']['cpu']['quantity']
                self.nic_count = len(self.vm_obj['vmConfig']['nics'])
                self.disks = self.vm_obj['vmConfig']['disks']
                self.disk_list = [disk['datastoreUrn'] for disk in self.disks]
                self.disk_count = len(self.disks)
                for disk in self.disks:
                    self.disk_dict[disk['diskName']] = disk['volumeUrl']
                self.memory = (self.vm_obj['vmConfig']['memory']['quantityMB']) / 1024
                self.vm_space = self._get_disk_size(self.vm_obj)
                self.get_drive_list()

            elif hasattr(self, prop):
                return getattr(self, prop, None)

        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM with the exception {}".format(err))
            raise Exception(err)

    def _get_vm_info(self):
        """
        get the basic or all or specific properties of VM

        exception:
                if failed to get all the properties of the VM

        """
        try:
            self.log.info(
                "Collecting all the VM properties for VM {}".format(self.vm_name))

            flag, response = self.hvobj.make_request('GET', self.vm_url)
            if flag:
                self.vm_obj = response.json()
                self.power_state = self.vm_obj['status']
                if self.power_state != 'running':
                    self.power_on()
                self.guid = self.vm_obj.get('uuid', self.vm_obj.get('uri'))
                self.ip = self.vm_obj['vmConfig']['nics'][0]['ip']
                self.guest_os = self.vm_obj['osOptions']['osType']
                self.host_name = self.vm_obj['osOptions']['hostname']
                self._basic_props_initialized = True
                return

            raise Exception("failed to get vm info with error {}".format(response.json()))

        except Exception as err:
            self.log.exception(
                "Failed to Get  the VM Properties of the VM with the exception {}".format(err)
            )
            raise Exception(err)

    def _get_disk_size(self, response):
        """
        get the total used space of the VM

        Args:
            response            (dict): response object of VMs API

        Returns:
            disk_space  (float)   : total space occupied by VM in GB

        """

        try:
            _disk_list = response['vmConfig']['disks']
            disk_space = 0
            for disk in _disk_list:
                disk_space += disk['quantityGB']
            return disk_space

        except Exception as err:
            self.log.exception(
                "Failed to Get  the VM disk space of the VM with the exception {}".format(err))
            raise Exception(err)

    def power_on(self):
        """
        power on the VM.

        Returns:
                True - when power on is successful

        Exception:
                When power on failed

        """

        try:
            if self.power_state == 'running':
                self.log.info("VM {} is already powered on".format(self.vm_name))
                return True
            flag, response = self.hvobj.make_request('POST', self.vm_operation['START_VM'])
            if flag:
                _flag = self.hvobj.wait_for_tasks(response.json()['taskUri'])
                if _flag:
                    self.power_state = 'running'
                    return True

            self.log.error("Error occurred while powering on VM {}".format(response.json()))

        except Exception as exp:
            self.log.exception("Exception in PowerOn{}".format(exp))
            return False

    def power_off(self):
        """
        power off the VM.

        Returns:
                True - when power off is successful

        Exception:
                When power off failed

        """

        try:
            if self.power_state == 'stopped':
                self.log.info("VM {} is already powered off".format(self.vm_name))
                return True
            flag, response = self.hvobj.make_request('POST', self.vm_operation['STOP_VM'],
                                                     json={"mode": "safe"})
            if flag:
                _flag = self.hvobj.wait_for_tasks(response.json()['taskUri'])
                if _flag:
                    self.power_state = 'stopped'
                    return True
            self.log.error("Error occurred while powering off VM {}".format(response.json()))

        except Exception as exp:
            self.log.exception("Exception in PowerOff{}".format(exp))
            return False

    def delete_vm(self):
        """
        Delete the VM.

        Returns:
                True - when Delete  is successful

        Exception:
                When deleting of th vm failed

        """

        try:

            flag, response = self.hvobj.make_request('DELETE', self.vm_url)
            if flag:
                _flag = self.hvobj.wait_for_tasks(response.json()['taskUri'])
                if _flag:
                    return True
            self.log.error("Error occurred while deleting on VM {}".format(response.json()))

        except Exception as exp:
            self.log.exception("Exception in Deleting the VM {}".format(exp))
            return False

    def clean_up(self):
        """
        Power off, and delete VM. 
        """

        if self.power_off() and self.delete_vm():
            self.log.info("Successfully cleaned up VM {}.".format(self.vm_name))
        else:
            self.log.exception("Error during clean_up for VM {}".format(self.vm_name))

    def restart_vm(self):
        """
        restart the VM.

        Returns:
                True - when restart  is successful

        Exception:
                When restarting of the vm failed

        """

        try:
            if self.power_state == 'stopped':
                flag, response = self.hvobj.make_request('GET', self.vm_operation['START_VM'])
            else:
                flag, response = self.hvobj.make_request('GET', self.vm_operation['RESTART_VM'],
                                                         json={"mode": "safe"})
            if flag:
                _flag = self.hvobj.wait_for_tasks(response.json()['taskUri'])
                if _flag:
                    self.power_state = 'running'
                    return True
            self.log.error("Error occurred while restarting on VM {}".format(response.json()))

        except Exception as exp:
            self.log.exception("Exception in restarting the VM {}".format(exp))
            return False
