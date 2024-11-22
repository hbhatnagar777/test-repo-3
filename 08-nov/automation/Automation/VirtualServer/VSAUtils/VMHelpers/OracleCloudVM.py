# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Oracle Cloud vm"""

from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils import OracleCloudServices


class OracleCloudVM(HypervisorVM):
    """
    Class for Oracle Cloud  VMs
    """

    def __init__(self, hvobj, vm_name):
        """
         Initialization of Oracle Cloud vm properties

         Args:
            vm_name (str)    --  name of the VM for which properties can be fetched

            hvobj   (object)        --  Hypervisor class object for Oracle Cloud

        """

        super(OracleCloudVM, self).__init__(hvobj, vm_name)
        self.server_name = hvobj.server_host_name
        self.hvobj = hvobj
        self.vm_url = '{0}instance{1}'.format(self.server_name, self.hvobj.vm_dict[vm_name])
        self._vm_operation_services_dict = OracleCloudServices.get_vm_operation_services(
            self.server_name, self.hvobj.vm_dict[vm_name])
        self.guid = None
        self.ip = None
        self.guest_os = None
        self.host_name = None
        self._disk_list = None
        self.disk_path = None
        self.update_vm_info()

    def update_vm_info(self, prop='Basic', os_info=False):
        """
        fetches all the properties of the VM

        Args:
            prop        (str)    --  the basic / all properties of the instace to fetch

            os_info     (bool)          --  True / False to set the Guest OS of the instance

        Raises:
            Exception:
                if failed to get all the properties of the VM

        """

        try:
            self._get_vm_info()
            if os_info or prop == 'All':
                self.vm_guest_os = self.guest_os
                self.get_drive_list()

            elif hasattr(self, prop):
                return getattr(self, prop, None)

        except Exception as err:
            self.log.exception("Failed to Get the VM Properties of the VM with the exception"
                               " {0}".format(err))
            raise Exception(err)

    def _get_vm_info(self):
        """
        get the basic or all or specific properties of VM

        Raises:
            Exception:
                if failed to get all the properties of the VM

        """
        try:
            self.log.info(
                "Collecting all the VM properties for VM %s" % self.vm_name)

            flag, response = self.hvobj._make_request('GET', self.vm_url)
            if flag:
                response_json = response.json()
                self.guid = response_json['uri'].rsplit("/", 1)[-1]
                self.ip = response_json['ip']
                self.guest_os = response_json['platform'].capitalize()
                self.host_name = response_json['hostname']
                self._get_cpu_memory(response_json['shape'])
                self.vm_space = self._get_disk_size()
                return

            raise Exception("failed with error {0}".format(response.json()))

        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM with the"
                               " exception {0}".format(err))
            raise Exception(err)

    def _get_disk_size(self):
        """
        get the total used space of the VM

        Returns:
            vm_disk_size    (int)   --  the total used space of the instance

        Raises:
            Exception:
                if failed to get the disk size of the VM

        """
        try:
            volume_list = []
            vm_disk_size = 0
            instance_name = self.vm_url.split("/instance")[-1]
            url = self.hvobj._vm_services['GET_STORAGE_ATTACHMENTS']
            flag, response = self.hvobj._make_request('GET', url)
            if flag:
                result = response.json()
                for attachment in result['result']:
                    if attachment['state'] == 'attached' and attachment['instance_name'
                    ] == instance_name:
                        volume_list.append(attachment['storage_volume_name'])
                if not volume_list:
                    raise Exception("Something went wrong while obtaining the storage volumes"
                                    " attached to the instance")
                self.disk_count = len(volume_list)
                for volume in volume_list:
                    url = self.hvobj._vm_services['GET_STORAGE_VOLUME'] + volume
                    flag, response = self.hvobj._make_request('GET', url)
                    if flag:
                        result = response.json()
                        vm_disk_size += int(int(result['size']) / (1024 * 1024 * 1024))
            return vm_disk_size

        except Exception as err:
            self.log.exception(
                "Failed to Get  the VM disk space of the VM with the exception {0}".format(err))
            raise Exception(err)

    def power_on(self):
        """
        power on the VM.

        Returns:
                True    --   when power on is successful
                False   --  when the power on fails

        """

        try:

            flag, response = self.hvobj._make_request('GET',
                                                      self._vm_operation_services_dict['START_VM'])
            if flag:
                return True
            else:
                raise Exception("Power on failed")

        except Exception as exp:
            self.log.exception("Exception in PowerOn{0}".format(exp))
            return False

    def power_off(self):
        """
        power off the VM.

        Returns:
                True    --   when power off is successful
                False   --   when the power off fails

        """

        try:

            flag, response = self.hvobj._make_request('GET',
                                                      self._vm_operation_services_dict['STOP_VM'])
            if flag:
                return True
            else:
                raise Exception("Power on failed")

        except Exception as exp:
            self.log.exception("Exception in PowerOff{0}".format(exp))
            return False

    def delete_vm(self):
        """
        Delete the VM.

        Returns:
                True    --   when delete is successful
                False   --   when the delete fails

        """

        try:

            flag, response = self.hvobj._make_request('GET', self.vm_url)
            if flag:
                return True
            else:
                raise Exception("Power on failed")

        except Exception as exp:
            self.log.exception("Exception in Deleting the VM {0}".format(exp))
            return False

    def restart_vm(self):
        """
        restart the VM.

        Returns:
                True    --   when restart is successful
                False   --   when restart fails
        """

        try:

            flag, response = self.hvobj._make_request('GET',
                                                      self._vm_operation_services_dict[
                                                          'RESTART_VM'])
            if flag:
                return True
            else:
                raise Exception("Power on failed")

        except Exception as exp:
            self.log.exception("Exception in restarting the VM {0}".format(exp))
            return False

    def _get_cpu_memory(self, shape):
        """
        Gets the CPU and memory of the given shape

        Args:
            shape   (str)   --  the name of the shape

        Raises:
            Exception:
                if it fails to get the CPU and Memory of the instance

        """
        try:
            url = self.hvobj._vm_services['GET_SHAPES'] + shape
            flag, response = self.hvobj._make_request('GET',
                                                      url)
            if flag:
                result = response.json()
                self.no_of_cpu = int(result['cpus'])
                self.memory = int(result['ram'] / 1024)

        except Exception as exp:
            raise Exception("Error occurred while obtaining CPU and Memory of instance. "
                            "{0}".format(str(exp)))
