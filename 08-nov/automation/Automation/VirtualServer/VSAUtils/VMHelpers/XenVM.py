# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Xen vm"""

import time
import re
from AutomationUtils import machine
from VirtualServer.VSAUtils.VMHelper import HypervisorVM


class XenVM(HypervisorVM):
    """
    This is the main file for all  Vmware VM operations
    """

    def __init__(self, Hvobj, vm_name):
        """
        Initialization of vmware vm properties

        Args:
            Hvobj               (obj):  Hypervisor Object

            vm_name             (str):  Name of the VM
        """
        super(XenVM, self).__init__(Hvobj, vm_name)
        self.host_machine = machine.Machine()
        self.server_name = Hvobj.server_host_name
        self.connection = Hvobj.connection
        self.guid, self.ip, self.guest_os, self.power_state, \
        self.vm_obj, self.memory, self.host, self.disk_dict = (None,) * 8
        self.no_of_cpu, self.disk_count = (0,) * 2
        self._basic_props_initialized = False
        self.update_vm_info()

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False, **kwargs):
        """
        Fetches all the properties of the VM

        Args:
            prop                (str):  Basic - Basic properties of VM like HostName,
                                                especially the properties with which
                                                VM can be added as dynamic content

                                        All   - All the possible properties of the VM

            os_info             (bool): To fetch os info or not

            force_update - to refresh all the properties always
                    True : Always collect  properties
                    False: refresh only if properties are not initialized

            **kwargs            (dict): All key-word arguments to be passed in update_vm_info

        Raises:
            Exception:
                if failed to update all the properties of the VM

        """
        try:
            if not self._basic_props_initialized or force_update:
                self._get_basic_prop()
            if self.power_state != 'Running':
                self.power_on()
                time.sleep(60)
                self._get_basic_prop()
            if os_info or prop == 'All':
                record = self.connection.VM.get_record(self.vm_obj)
                self.memory = int(int(record['memory_static_max']) / 1024 / 1024)
                self.vm_guest_os = self.guest_os
                self.no_of_cpu = int(record['VCPUs_max'])
                self.host = self.connection.host.get_record(record['resident_on'])['name_label']
                self.disk_count = len(self.disk_list)
                self.set_disk_dict()
                self.get_drive_list()

        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def _get_basic_prop(self):
        try:
            all_vms = self.connection.VM.get_all()
            record = None
            for vm in all_vms:
                record = self.connection.VM.get_record(vm)
                if record['name_label'] == self.vm_name:
                    self.vm_obj = vm
                    break
            self.guid = record['uuid']
            self.power_state = record['power_state']
            vgm = self.connection.VM.get_guest_metrics(self.vm_obj)
            os = self.connection.VM_guest_metrics.get_os_version(vgm)
            if 'windows' in os['distro']:
                self.guest_os = 'windows'
            else:
                self.guest_os = 'unix'
            ip = self.connection.VM_guest_metrics.get_networks(vgm)
            try:
                self.ip = ip['0/ipv4/0']
            except KeyError:
                self.ip = ip['1/ipv4/0']
        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def power_on(self):
        """
        Power on the VM.

        Raises:
            Exception:
                When power on failed

        """

        try:
            if self.power_state != 'Running':
                self.log.info("Powering on the vm {} and sleeping for 3 minutes".format(self.vm_name))
                self.connection.VM.start(self.vm_obj, False, True)
                time.sleep(180)
            else:
                self.log.info("VM {} is already running".format(self.vm_name))
            return
        except Exception as exp:
            self.log.exception("Exception in PowerOn")
            raise Exception("Exception in PowerOn:" + str(exp))

    def power_off(self):
        """
        Power off the VM.

        Raises:
            Exception:
                When power off failed

        """

        try:
            if self.power_state != 'Halted':
                self.log.info("powering off {}".format(self.vm_name))
                self.connection.VM.clean_shutdown(self.vm_obj)
                time.sleep(30)
            else:
                self.log.info("{} is already powered off".format(self.vm_name))
            return
        except Exception as exp:
            self.log.exception("Exception in PowerOff")
            raise Exception("Exception in PowerOff:" + str(exp))

    def delete_vm(self):
        """
        Delete the VM.

        Raises:
            Exception:
                When deleting of the vm failed
        """

        try:
            if self.power_state != 'Halted':
                self.connection.VM.hard_shutdown(self.vm_obj)
            self.connection.VM.destroy(self.vm_obj)
            self.log.info("VM: {} is deleted".format(self.vm_name))
        except Exception as exp:
            self.log.exception("Exception in delete_vm {0}".format(exp))
            return False

    def clean_up(self):
        """
        Does the cleanup after the testcase.

        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned

        """

        try:
            self.log.info("Powering off VM after restore")
            self.power_off()
        except Exception as exp:
            raise Exception("Exception in Cleanup: {0}".format(exp))

    @property
    def disk_list(self):
        """
        To fetch the disk in the VM

        Returns:
            _disk_list           (list): List of disk in VM

        """
        _disk_list = []
        record = self.connection.VM.get_record(self.vm_obj)
        for vbds in record['VBDs']:
            vdb = self.connection.VBD.get_record(vbds)
            if vdb['type'] != 'CD':
                vdi = self.connection.VDI.get_record(vdb['VDI'])
                _disk_list.append(vdi['uuid'])
        return _disk_list

    def set_disk_dict(self):
        """
        Fetches disk_dict for disk filtering:
        """
        self.disk_dict = {}
        record = self.connection.VM.get_record(self.vm_obj)
        for vbds in record['VBDs']:
            vdb = self.connection.VBD.get_record(vbds)
            if vdb['type'] != 'CD':
                vdi = self.connection.VDI.get_record(vdb['VDI'])
                sr = self.connection.SR.get_record(vdi['SR'])
                self.disk_dict[vdi['uuid']] = ['/dev/' + vdb['device'], vdi['name_label'],
                                            int(vdb['userdevice']), sr['name_label']]

    def get_datastore_uri_by_pattern(self, disk_path):
        """
        find the disk that matches the disk label

        Args:
                disk_path                  (string):   Device Path to be matched

        Returns:
             _disks                     (list): Disk path

        Raises:
            Exception
                when failed to fetch the disk associated with the disk label
        """
        try:
            _disks = [key for key, value in self.disk_dict.items() if disk_path in value]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disk_by_label : {}".format(err))
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
                      re.findall(_disk_pattern, value[1])]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disk_path_from_pattern : {}".format(err))
            raise Exception(err)

    def get_disk_in_controller(self, disk_position):
        """
        get the disk associated with the virtual device node

        Args:
                disk_position               (string):  singe or multiple disk position
        Return:
                _disks                  (list): Disk path

        Raises:
            Exception:
                if failed to fetch disk path from the virtual device node

        """
        try:
            _disk_position = []
            if re.search(r'\[.*?]', disk_position):
                _range_start = int(re.findall(r"\[([^-]+)", disk_position)[0])
                _range_end = int(re.findall(r"\-([^]]+)", disk_position)[0]) + 1
                disk_ranges = range(_range_start, _range_end)
                for _disk in disk_ranges:
                    _disk_position.append(_disk)
            else:
                _disk_position = [disk_position]
            _disks = [key for key, value in self.disk_dict.items() if value[2] in _disk_position]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disk_in_controller {}".format(err))
            raise Exception(err)

    def get_disks_by_repository(self, storage_name):
        """
        get the disk associated with the storage name

        Args:
            storage_name                  (string) : datastore name

        Returns:
             _disks                     (list): Disk path

        Raises:
            Exception
                when failed to fetch the disk associated with the datastore name
        """
        try:
            _disks = [key for key, value in self.disk_dict.items() if storage_name in value]
            return _disks

        except Exception as err:
            self.log.exception("Exception in get_disks_by_repository : {}".format(err))
            raise Exception(err)
