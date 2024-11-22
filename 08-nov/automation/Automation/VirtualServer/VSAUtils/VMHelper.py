# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on VM

classes defined:
    Base class:
        HypervisorVM- Act as base class for all VM operations

    Inherited class:
        HyperVVM - Does all operations on Hyper-V VM

    Methods:

        get_drive_list()    - get all the drive list associated with VM

        power_off()            - power off the VM

        power_on()            -power on the VM

        delete_vm()            - delete the VM

        update_vm_info()    - updates the VM info
    """

import re
from abc import ABCMeta, abstractmethod
from AutomationUtils import logger
from AutomationUtils import machine, config
from AutomationUtils.pyping import ping
from . import VirtualServerUtils
from . import VirtualServerConstants as VSconstant
from importlib import import_module
from inspect import getmembers, isclass, isabstract
import os
import time
from VirtualServer.VSAUtils.VirtualServerUtils import validate_ip, validate_ipv4


class HypervisorVM(object):
    """
    Main class for performing operations on Hyper-V VM
    """
    __metaclass__ = ABCMeta

    def __new__(cls, hvobj, vm_name, **kwargs):
        """
        Initialize VM object based on the Hypervisor of the VM
        """
        instance_type = hvobj.instance_type.lower()
        vm_helper = VSconstant.instance_vmhelper(instance_type)
        hh_module = import_module("VirtualServer.VSAUtils.VMHelpers.{}".format(vm_helper))
        classes = getmembers(hh_module, lambda m: isclass(m) and not isabstract(m))
        for name, _class in classes:
            if issubclass(_class, HypervisorVM) and _class.__module__.rsplit(".", 1)[-1] == vm_helper:
                return object.__new__(_class)

    def __init__(self, hvobj, vm_name, **kwargs):
        """
        Initialize the VM initialization properties
        """
        self.vm_name = vm_name
        self.hvobj = hvobj
        self.commcell = self.hvobj.commcell
        self.server_name = hvobj.server_host_name
        self.host_user_name = hvobj.user_name
        self.host_password = hvobj.password
        self._host_machine = None
        self.log = logger.get_log()
        self.instance_type = hvobj.instance_type
        self.utils_path = VirtualServerUtils.UTILS_PATH
        self.config = config.get_config()
        self.guest_os = None
        self.ip = None
        self._DriveList = None
        self._user_name = None
        self._password = None
        self._drives = None
        self.machine = None
        self._preserve_level = 1
        self.DiskType = None
        self.power_state = ''
        self.DiskList = []
        self.validate_name_tag = None  # attribute used for AWS validation
        self.backup_job = None  # attribute needed  for openstackValidation validation
        self.vm_exist = True  # used for conversion purpose

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options, **kwargs):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.restore_job = self.vm_restore_options.restore_job
            self.log = logger.get_log()
            self.kwargs_options = kwargs

        def __eq__(self, other):
            """compares the source vm and restored vm"""
            return True

    class VmConversionValidation(object):
        def __init__(self, vmobj, vm_restore_options):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            return True

    @property
    def drive_list(self):
        """
        Returns the drive list for the VM. This is read only property
        """
        if self._drives is None:
            self.get_drive_list()
        return self._drives

    @property
    def user_name(self):
        """gets the user name of the Vm prefixed with the vm name to avoid conflict.
        It is a read only attribute"""

        return self._user_name

    @user_name.setter
    def user_name(self, value):
        """sets the username of the vm"""

        self._user_name = value

    @property
    def password(self):
        """gets the user name of the Vm . It is a read only attribute"""

        return self._password

    @password.setter
    def password(self, value):
        """sets the password of the vm"""

        self._password = value

    @property
    def vm_hostname(self):
        """gets the vm hostname as IP (if available or vm name). It is a read only attribute"""

        if self.ip:
            return self.ip

        return self.vm_name

    @property
    def vm_guest_os(self):
        """gets the VM Guest OS . it is read only attribute"""
        return self.machine

    @vm_guest_os.setter
    def vm_guest_os(self, value):
        self._set_credentials(value)

    @property
    def preserve_level(self):
        """gets the default preserve level of Guest OS. it is read only attribute"""
        if self.guest_os.lower() == "windows":
            self._preserve_level = 0
        else:
            self._preserve_level = 1

        return self._preserve_level

    @property
    def host_machine(self):
        """
        Gets the host machine object from the hypervisor
        Returns: the hypervisor host machine object
        """
        if self._host_machine:
            return self._host_machine
        return self.hvobj.machine

    @host_machine.setter
    def host_machine(self, machine_obj):
        """Sets the host machine object on the hypervisor
        Args:
            machine_obj: machine object of the host machine
        """

        self._host_machine = machine_obj

    # just to reduce redirection

    def get_os_name(self, vm_name=None):
        """
        Get the OS Name from the machine name by ping as Hypervisor API gives wrong information
        Returns:
            os_name (str) - os of the VM
        """
        if not vm_name:
            vm_name = self.vm_hostname
        # Extract TTL value form the response.output string.
        _attempt = 0
        while _attempt < 3:
            try:
                self.log.info("Pinging the vm : {}, Attempt no {}".format(vm_name, _attempt))
                response = ping(vm_name)
                ttl = int(re.match(r"(.*)ttl=(\d*) .*",
                                   response.output[2]).group(2))
                break
            except AttributeError:
                _attempt += 1
                if _attempt < 3:
                    self.log.info("Ping failed. for vm {}. Trying after 1 min".format(vm_name))
                    time.sleep(60)
                else:
                    raise AttributeError('Failed to connect to the machine.\nError: "{}"'.format(
                        response.output)
                    )
        if ttl < 256:
            if 64 < ttl <= 128:
                return "Windows"
            else:
                return "Linux"
        else:
            raise ValueError('Got unexpected TTL value.\nTTL value: "{}"'.format(ttl))

    def _set_credentials(self, os_name):
        """
        set the credentials for VM by reading the config INI file
        """

        os_name = self.get_os_name(self.vm_hostname)
        if self.user_name and self.password:
            try:
                vm_machine = machine.Machine(self.vm_hostname,
                                             username=self.user_name,
                                             password=self.password)
                if vm_machine:
                    self.machine = vm_machine
                    return
            except:
                raise Exception("Could not create Machine object! The existing username and "
                                "password are incorrect")

        self.guest_os = os_name
        sections = VirtualServerUtils.get_details_from_config_file(os_name.lower())
        user_list = sections.split(",")
        attempt = 0

        while attempt < 5:
            incorrect_usernames = []

            for each_user in user_list:
                user_name = each_user.split(":")[0]
                password = VirtualServerUtils.decode_password(each_user.split(":")[1])
                try:
                    vm_machine = machine.Machine(self.vm_hostname,
                                                 username=user_name,
                                                 password=password)
                    if vm_machine:
                        self.machine = vm_machine
                        self.user_name = user_name
                        self.password = password
                        return
                except:
                    incorrect_usernames.append(each_user.split(":")[0])
            attempt = attempt + 1
        self.log.exception("Could not create Machine object! The following user names are "
                           "incorrect: {0}".format(incorrect_usernames))

    def get_drive_list(self, drives=None):
        """
        Returns the drive list for the VM
        """
        try:
            _temp_drive_letter = {}
            if hasattr(self, 'no_ip_state') and self.no_ip_state:
                storage_details = self.get_storage_details_no_ip()
            else:
                if self.machine:
                    storage_details = self.machine.get_storage_details()
                else:
                    if self.guest_os:
                        self.vm_guest_os = self.guest_os
                        storage_details = self.machine.get_storage_details()

            if self.guest_os.lower() == "windows":
                _drive_regex = "^[a-zA-Z]$"
                for _drive, _size in storage_details.items():
                    if re.match(_drive_regex, _drive):
                        if drives is None and _size['available'] < 900:
                            continue
                        _drive = _drive + ":"
                        _temp_drive_letter[_drive.split(":")[0]] = _drive

            else:
                temp_dict = {}
                if hasattr(self, 'no_ip_state') and self.no_ip_state:
                    fstab = self.execute_command('cat /etc/fstab')
                    formatted_list = [y.split() for y in (x.strip() for x in fstab.splitlines()) if
                                      y]
                else:
                    fstab = self.machine.execute_command('cat /etc/fstab')
                    if fstab.exception:
                        self.log.error("Exception:{}".format(fstab.exception))
                        raise Exception(
                            "Error in getting Mounted drives of the vm: {}".format(self.vm_name))
                    self.log.info(
                        "complete fstab for vm {0}: {1}".format(self.vm_name, fstab.output))
                    formatted_list = fstab.formatted_output

                    # For str fstab output
                    if type(formatted_list) == str:
                        formatted_list = [formatted_list.split()]

                for mount in formatted_list:
                    if (re.match('/', mount[0])
                        or re.match('UUID=', mount[0], re.I)
                        or re.match('LABEL=', mount[0], re.I)) and not (
                            re.match('/boot', mount[1], re.I)
                            or re.match('/var', mount[1], re.I)
                            or re.match('/usr', mount[1], re.I)
                            or re.match('/tmp', mount[1], re.I)
                            or re.match('/home', mount[1], re.I)
                            or re.match('swap', mount[1], re.I)
                            or re.match('none', mount[1], re.I)):
                        temp_dict[mount[0]] = mount[1]
                self.log.info("Mount points applicable: {}".format(temp_dict))
                _temp_storage = {}
                for _detail in storage_details.values():
                    if isinstance(_detail, dict):
                        _temp_storage[_detail['mountpoint']] = _detail['available']
                self.log.info("Storage of VM {0}: {1}".format(self.vm_name, _temp_storage))
                _index = 0
                for key, val in temp_dict.items():
                    if _temp_storage[val] > 900:
                        if re.match('/dev/sd', key, re.I) or re.match('/dev/xvd', key, re.I):
                            _command = 'blkid ' + key
                            blkid = self.machine.execute_command(_command)
                            if blkid.exception:
                                raise Exception(
                                    "Error in getting UUID of the vm: {}".format(self.vm_name))
                            _temp_drive_letter[
                                '/cvlostandfound/' +
                                re.findall(r'UUID="([^"]*)"', blkid.formatted_output)[0]] = val
                        elif re.match('/dev/mapper', key, re.I):
                            _temp_drive_letter[key.split('dev/mapper/')[1]] = val
                        elif re.match('/dev/VolGroup', key, re.I):
                            _temp_drive_letter['-'.join(key.split("/")[2:])] = val
                        elif re.match('UUID=', key, re.I) and val == "/":
                            _temp_drive_letter["MountDir-2"] = val
                            _index = 3
                        elif re.match('LABEL=', key, re.I) and val == "/":
                            _temp_drive_letter["MountDir-1"] = val
                            _index = 2
                        elif re.match('LABEL=', key, re.I):
                            _temp_drive_letter["MountDir-" + str(_index)] = val
                            _index += 1
                        else:
                            _temp_drive_letter[val] = val
                self.log.info(
                    "Disk and mount point for vm {0}: {1}".format(self.vm_name, _temp_drive_letter))
                del _temp_storage, temp_dict
            self._drives = _temp_drive_letter
            if not self._drives:
                raise Exception("Failed to Get Volume Details for the VM")

        except Exception as err:
            self.log.exception(
                "An Exception Occurred in Getting the Volume Info for the VM {0}".format(err))
            return False

    @abstractmethod
    def power_off(self):
        """
        power off the VM.

        return:
                True - when power off is successfull

        Exception:
                When power off failed

        """
        self.log.info("Power off the VM")

    @abstractmethod
    def power_on(self):
        """
        power on the VM.

        return:
                True - when power on is successful

        Exception:
                When power on failed

        """
        self.log.info("Power on the VM")

    @abstractmethod
    def delete_vm(self):
        """
        power on the VM.

        return:
                True - when delete is successful

                False - when delete failed
        """
        self.log.info("Delete the VM")

    def clean_up(self):
        """
        Clean up the VM resources post restore

        Raises:
             Exception:
                If unable to clean up VM and its resources

        """
        self.log.info("Powering off VMs/Instances after restore")
        self.power_off()

    def find_scsi_controller(self, controller_type=None):
        """Find the associated scsi controller is present in the vm

        Args:
            controller_type  (str)   --  type of scsi controller to look in the vm

        Returns:
            bool    -   boolean value whether the directory exists or not

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    @abstractmethod
    def update_vm_info(self):
        """
        fetches all the properties of the VM

        Args:
                should have code for two possibilties

                Basic - Basic properties of VM like HostName,GUID,Nic
                        especially the properties with which VM can be added as dynamic content

                All   - All the possible properties of the VM

                Set the property VMGuestOS for creating OS Object

                all the property need to be set as class variable

        exception:
                if failed to get all the properties of the VM
        """
        self.log.info("Update the VMinfo of the VM")

    def wait_for_vm_to_boot(self):
        """
        Waits for a VM to start booting by pinging it to see if an IP has been successfully assigned.

        Raise Exception:
                If IP assigned within 10 minutes
        """
        # Wait for IP to be generated
        wait = 10

        try:
            while wait:
                self.log.info(
                    'Waiting for 60 seconds for the IP to be generated')
                time.sleep(60)

                try:
                    self.update_vm_info(prop="All", os_info=True)
                except Exception as exp:
                    self.log.info(exp)

                if self.ip:
                    if validate_ip(self.ip) and validate_ipv4(self.ip):
                        break
                wait -= 1
            else:
                raise Exception(
                    f'Valid IP for VM: {self.vm_name} not generated within 10 minutes')
            self.log.info(f'IP is generated for VM: {self.vm_name}')

        except Exception as err:
            self.log.exception("An error occurred in fetching VM IP")
            raise Exception(err)

    def compare_disks(self, num_threads, multiplier):
        """
            Copies over an executabel to the target machine which will
            do a disk level comparison, and generate logs on the target machine

            Raise Exception:
                    if executable not executed successfully
                    if Disk Comparison fails
        """
        try:
            disk_compare_py = os.path.join(
                self.utils_path, "DiskCompare.py")
            command = '(Get-WmiObject Win32_OperatingSystem).SystemDrive'
            output = self.machine.execute_command(command)

            target_path = output.output.strip() + "\\"

            exe_file = self.host_machine.generate_executable(disk_compare_py)
            self.machine.copy_from_local(exe_file, target_path)
            remote_exe_file_path = None

            retry = 10
            while retry:
                self.log.info(
                    'Waiting for 2 minutes to copy the extent exe folder')
                time.sleep(120)
                _exe_file = os.path.join(target_path, os.path.split(exe_file)[1:][0])

                if self.machine.check_file_exists(_exe_file):
                    remote_exe_file_path = _exe_file
                    break
                else:
                    self.machine.copy_from_local(exe_file, target_path)

                retry -= 1
            else:
                raise Exception("Failed to copy the extent exe folder within 10 tries")

            self.log.info("Waiting 2 minutes before running executable")
            time.sleep(120)

            cmd = "iex " + "\"" + remote_exe_file_path + " -t " \
                  + str(num_threads) + " -m " + str(multiplier) + "\""
            try:
                self.log.info("Executing command {0} on MA Machine".format(cmd))
                output = self.machine.execute_command(cmd)
            except Exception as err:
                self.log.error("Failed to run executable on remote machine")

            # Delete remote executable
            try:
                self.machine.delete_file(remote_exe_file_path)
            except Exception as err:
                self.log.error("An error occurred in deleting file %s", str(err))

            # Delete local executable
            try:
                self.host_machine.delete_file(exe_file)
            except Exception as err:
                self.log.error("An error occurred in deleting file %s", str(err))

            return output.output

        except Exception as err:
            self.log.exception(str(err))
            raise Exception(err)

    def set_disk_props(self, props_dict):
        """
        Runs a PowerShell script which sets disks properties
        such as offline and read-only, can be specified via props_dict

        Raise Exception:
                if script was not run successfully
        """
        try:
            ps_path = os.path.join(self.utils_path, "ToggleDiskReadOnlyOffline.ps1")
            self.update_vm_info('All', True, True)
            output = self.machine.execute_script(ps_path, props_dict)

        except Exception as err:
            self.log.exception("An exception occurred in setting disk properties")
            raise Exception(err)

    def get_os_disk_number(self):
        """
            Gets the disk number of the disk which has the OS installed
        """
        try:
            command = 'gwmi -query "Select * from Win32_DiskPartition WHERE Bootable = True" | foreach { ' \
                      '$_.DiskIndex} '
            self.update_vm_info('All', True, True)
            output = self.machine.execute_command(command)
            os_disk = int(output.output)
            return os_disk

        except Exception as err:
            self.log.exception("An exception occurred in trying to get OS disk number")
            raise Exception(err)

    def get_storage_details_no_ip(self):
        """
        fetches the storage details with total space, free space and drive letter
        of the vms which don't have IP
        Returns:
                    storage_dict    (dict):     storage dict of the vm

        """
        if self.guest_os.lower() == 'windows':
            _storage_details = self.execute_command('powershell Get-PSDrive')
        else:
            _storage_details = self.execute_command('df -Pk')
        storage_dict = self.parse_storage_detail_no_ip(_storage_details)
        return storage_dict

    def parse_storage_detail_no_ip(self, storage_details):
        """
        Parses storage format in the correct dict format to be on par with vms
        where storage was fetched using machine object created using IP
        Args:
                    storage_details (string):       Storage detail of vm in raw string

        Returns:
                    storage_dict    (dict):         storage details in dictionary

        Raises:
            Exception:
                if failed to parse the storage details
        """
        try:
            storage_dict = {
                'total': 0,
                'available': 0
            }
            storage_detail = storage_details.split("\n")
            if self.guest_os.lower() == 'windows':
                for z in storage_detail:
                    z = z.split()
                    try:
                        drive_name = z[0]
                        used_space = round(float(z[1]) * 1024.0, 2)
                        free_space = round(float(z[2]) * 1024.0, 2)
                        total_space = round(free_space + used_space, 2)
                        storage_dict[drive_name] = {
                            'total': total_space,
                            'available': free_space
                        }
                        storage_dict['total'] += total_space
                        storage_dict['available'] += free_space
                    except ValueError:
                        continue
            else:
                for z in storage_detail:
                    z = z.split()
                    try:
                        drive_name = z[0]
                        used_space = round(float(z[2]) / 1024, 2)
                        free_space = round(float(z[3]) / 1024, 2)
                        mount_point = z[5]
                        total_space = round(float(free_space + used_space), 2)
                        storage_dict[drive_name] = {
                            'total': total_space,
                            'available': free_space,
                            'mountpoint': mount_point
                        }
                        storage_dict['total'] += total_space
                        storage_dict['available'] += free_space
                    except ValueError:
                        continue
            return storage_dict
        except Exception as err:
            self.log.exception("An exception occurred in fetching storage details")
            raise Exception(err)

    def calculate_hash_no_ip(self, source_folder):
        """
        Calculates the checksum of the files for the vms which doesn't have IP
        Args:
                            source_folder (string):         testdata folder location

        Returns:
                            hash_result     (set):          set of of file and their checksum

        Raises:
            Exception:
                if failed to calculate checksum of the files
        """
        try:
            if self.guest_os.lower() == 'windows':
                _hash_code = 'powershell -Command "&{Get-FileHash -Algorithm MD5 (get-childItem "' + \
                             source_folder + '\*" -Recurse) | select-object Path, Hash | format-list}"'
                output = self.execute_command(_hash_code)
                output_lines = output.splitlines()
                hash_result = set()
                for _hash in range(0, len(output_lines), 3):
                    hash_tuple = (output_lines[_hash].split(source_folder + "\\")[1],
                                  output_lines[_hash + 1].split(":")[1].strip())
                    hash_result.add(hash_tuple)
            else:
                _hash_code = 'find . -type f -exec md5sum {} +'
                output = self.execute_command(_hash_code)
                output_lines = output.splitlines()
                hash_result = set()
                for _hash in range(len(output_lines)):
                    hash_tuple = (_hash.split()[1].split('./')[1], _hash.split()[0].upper())
                    hash_result.add(hash_tuple)
            return hash_result
        except Exception as err:
            self.log.exception("An exception occurred in fetching checksum")
            raise Exception(err)

    def copy_test_data_to_each_volume(self, _drive, backup_folder, _test_data_path):
        """
        Copy test data to the drive mentioned

        Args:
            _drive              (str):  Drive letter where data needs to be copied

            backup_folder       (str):  name of the folder to be backed up

            _test_data_path     (str):  path where testdata needs to be generated

        Raises:
            Exception:
                if it fails to generate testdata or if fails to copy testdata

        """

        try:

            self.hvobj.timestamp = os.path.basename(os.path.normpath(_test_data_path))
            # create Base dir
            if self.guest_os.lower() in ["linux", "unix"] or self.hvobj.controller.os_info.lower() != 'windows':
                _dest_base_path = self.machine.join_path(_drive, backup_folder, "TestData", self.hvobj.timestamp)
            else:
                _dest_base_path = self.machine.join_path(_drive, backup_folder,
                                                         "TestData")
            if not self.machine.check_directory_exists(_dest_base_path):
                _create_dir = self.machine.create_directory(_dest_base_path)
            self.log.info("Copying testdata to volume {}".format(_drive))
            attempt = 0
            while attempt < 5:
                try:
                    self.machine.copy_from_local(_test_data_path, _dest_base_path)
                    _validation_path = self.machine.join_path(_drive, backup_folder,
                                                              "TestData", self.hvobj.timestamp)
                    if not self.hvobj.controller.compare_folders(self.machine, _test_data_path,
                                                                 _validation_path,
                                                                 ignore_folder=[VSconstant.PROBLEMATIC_TESTDATA_FOLDER]
                                                                 ):
                        self.log.info("Testdata copied and checksum matched successfully on vm {} on {}".
                                      format(self.vm_name, _drive))
                        return
                    raise Exception(VSconstant.constant_log['test_data_copy']%(self.vm_name, _drive))
                except Exception as exp:
                    self.log.exception(exp)
                    self.log.info("testdata copy attempt {}".format(attempt))
                    time.sleep(60)
                    self.machine.remove_directory(_dest_base_path)
                    time.sleep(20)
                    _ = self.machine.create_directory(_dest_base_path)
                    attempt = attempt + 1
            raise Exception(VSconstant.constant_log['test_data_copy']%(self.vm_name, _drive))

        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying test data to Vm  ")
            raise err

    def copy_content_indexing_data(self, _drive, backup_folder):
        """
        copy test data to each volume in the vm provided for content indexing

        Args:
                _drive      (str):   Drive letter where data needs to be copied

                backup_folder(str):  name of the folder to be backed up

        Exception:
                if fails to copy testdata

        """
        try:

            _test_data_path = VirtualServerUtils.get_content_indexing_path(self.hvobj.controller)
            _dest_base_path = os.path.join(_drive, self.machine.os_sep, backup_folder)

            if not self.machine.check_directory_exists(_dest_base_path):
                _create_dir = self.machine.create_directory(_dest_base_path)

            self.log.info("Copying content indexing test data")
            self.machine.copy_from_local(_test_data_path, _dest_base_path)

        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying content indexing data to Vm  ")
            raise err

    def copy_version_file_data(self, version_file_path, drive, file_versions_folder, file_name1, file_name2):
        """
        Copy versions file to the destination machine.

        Args:
                version_file_path       (str) -- Path of versions file in the local machine.

                drive                  (str) -- Drive letter where file needs to be copied in the destination.

                file_versions_folder    (str) -- Folder where versions file resides in destination.

                file_name1              (str) -- The old name for the copied file.

                file_name2              (str) -- The new name which the copied file will be renamed to.

        Raises:
            Exception:
                If fails to copy or rename the versions file.
        """
        try:

            dest_base_path = os.path.join(drive, self.machine.os_sep, file_versions_folder)

            if self.machine.check_directory_exists(dest_base_path):
                self.machine.remove_directory(dest_base_path)
            _create_dir = self.machine.create_directory(dest_base_path)

            self.log.info("Copying version file test data")
            if not self.machine.copy_from_local(version_file_path, dest_base_path):
                raise Exception("Copying from local machine to destination failed.")

            file_name1 = self.machine.join_path(dest_base_path, file_name1)
            file_name2 = self.machine.join_path(dest_base_path, file_name2)
            self.machine.rename_file_or_folder(file_name1, file_name2)

        except Exception as err:
            self.log.exception("An error occurred in  Copying file versions data to Vm ")
            raise err

    class DrValidation(object):
        """Class for DR validation"""
        INTEGRITY_SNAPSHOT_NAME = '__GX_BACKUP__'
        FAILOVER_SNAPSHOT_NAME = '__GX_FAILOVER__'
        TESTBOOT_SNAPSHOT_NAME = '__GX_TESTBOOT__'

        def __init__(self, vmobj, vm_options, **kwargs):
            self.vm = vmobj
            self.vm_options = vm_options
            self.options = kwargs
            self.log = logger.get_log()

        def validate_vm_exists(self):
            """ Validates that the VM exists on hypervisor """
            if not self.vm.hvobj.check_vms_exist([self.vm.vm_name]):
                raise Exception(f"VM [{self.vm.vm_name}] doesn't exist on hypervisor")
        
        def validate_no_vm_exists(self):
            """ Validates that the VM does not exist on hypervisor """
            if self.vm.hvobj.check_vms_exist([self.vm.vm_name]):
                raise Exception(f"VM [{self.vm.vm_name}] exists on hypervisor")            

        def validate_cpu_count(self, **kwargs):
            """Validate CPU counts to make sure they are equal"""
            return True

        def validate_memory(self, **kwargs):
            """Validate the memory size to make sure they are equal"""
            return True

        def validate_disk_count(self, **kwargs):
            """Validate that the number of disks"""
            return True

        def validate_network_adapter(self, **kwargs):
            """Validate the network adapter"""
            return True

        def validate_snapshot(self, **kwargs):
            """Validate the integrity snapshot on the VM"""
            return True

        def validate_snapshot_failover(self, **kwargs):
            """Validate the failover snapshot on the VM"""
            return True

        def validate_dvdf(self, **kwargs):
            """Validate 'deploy VM during failover' VM is ready on hypervisor(only for cloud hypervisors)"""
            return True

        def validate_dvdf_on_failover(self, **kwargs):
            """Validate 'deploy VM during failover' VM is deployed after failover(only for cloud hypervisors)"""
            return True

        def validate_warm_sync(self, **kwargs):
            """Validate warm sync is honoured by not creating VM before failover/after_failback"""
            self.validate_no_vm_exists()

        def advanced_validation(self, other, **kwargs):
            """Hypervisor specific validations"""
            return True
