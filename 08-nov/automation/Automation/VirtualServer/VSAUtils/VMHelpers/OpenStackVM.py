# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Openstack vm"""

import os
import re
import socket
from AutomationUtils.pyping import ping
from AutomationUtils import machine
from AutomationUtils import logger
from VirtualServer.VSAUtils import OpenStackWrapper
from VirtualServer.VSAUtils.VMHelper import HypervisorVM


class OpenStackVM(HypervisorVM):
    """
    This class will have all OpenStack VM operations methods
    """

    def __init__(self, hvobj, vm_name):
        """
        Initialization of openstack vm properties

        Args:
            hvobj               (obj):  Hypervisor Object

            vm_name             (str):  Name of the VM
        """
        super(OpenStackVM, self).__init__(hvobj, vm_name)
        self.server_name = hvobj.server_host_name

        self.prop_dict = {
            "server_name": self.server_name,
            "user": self.host_user_name,
            "pwd": self.host_password,
            "vm_name": self.vm_name,
            "extra_args": "$null"
        }

        self.operation_dict = {
            "server_name": self.server_name,
            "user": self.host_user_name,
            "pwd": self.host_password,
            "vm_name": self.vm_name,
            "vm_user": self.user_name,
            "vm_pass": self.password,
            "property": "$null",
            "extra_args": "$null"
        }
        # self.OpenStackHandler = OpenStackWrapper.OpenStackVMops(self.server_name,self.host_user_name,
        # self.host_password)
        self.GUID = None
        self.ip = None
        self.GuestOS = None
        self.HostName = None
        self._disk_list = None
        self.disk_dict = None
        self.DiskPath = None

        # self.Memory = None
        # self.VMSpace = None
        # self.machine    = machine.Machine(vm_name,username=self.user_name,password=self.password)
        self.host_machine = self.hvobj.host_machine
        self.update_vm_info()
        self.project = None

        # self.AZ         = None

    # @property
    # def getAvailabilityZone(self):
    #     """
    #     This method gets teh AZ for the instance in openstack
    #     :return: AZ in string
    #     """
    #     try:
    #         return self.AZ
    #
    #     except Exception as err:
    #         self.log.exception("Exception occured in getAvailbilityZone() ".format(str(err)))
    #
    #
    # @getAvailabilityZone.setter
    # def getAvailabilityZone(self, az):
    #     """
    #     Sets AZ for the instance
    #     :param az: Availbility zone for the instance in string
    #     :return: None or exception
    #     """
    #     try:
    #         self.AZ = az
    #     except Exception as err:
    #         self.log.exception("Exception occured in setter getAvailabilityZone() ".format(str(err)))
    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options, **kwargs):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.restore_job = self.vm_restore_options.restore_job
            self.log = logger.get_log()

        def __eq__(self, other):
            """compares the source vm and restored vm"""
            config_val = (
                    self.vm.vm._disk_list == other.vm.vm._disk_list and
                    self.vm.vm.disk_list[0]['name'] == other.vm.vm.disk_list[0]['name'] and
                    self.vm.vm.volumelist[0]['volume_type'] == other.vm.vm.volumelist[0]['volume_type'] and
                    self.vm.vm.volumelist[0]['name'] == other.vm.vm.volumelist[0]['name'] and
                    self.vm.vm.volumelist[0]['size'] == other.vm.vm.volumelist[0]['size'] and
                    self.vm.vm._drives == other.vm.vm._drives and
                    self.vm.vm.disk_list[0]['size'] == other.vm.vm.disk_list[0]['size'] and
                    self.vm.vm.vcpus == other.vm.vm.vcpus and
                    self.vm.vm.vmflavor == other.vm.vm.vmflavor and
                    self.vm.vm.ram == other.vm.vm.ram

            )
            self.vm.vm.verify_if_volumes_attached(other)
            self.vm.vm.verify_if_snap_attached()
            if config_val:
                return True

    def verify_if_volumes_attached(self, restore_obj):
        """
        Validates if volumes are detached after backup
        Args:Jobidlist and instanceName
        return: VolumeList
            """
        try:
            self.hvobj.OpenStackHandler.projectName = self.hvobj.OpenStackHandler.DEFAULT_PROJECT
            uuid = self.hvobj.OpenStackHandler.get_uuid(restore_obj.vm.vm.host_machine)
            volumeList = self.hvobj.OpenStackHandler.get_volume_attachments(uuid)
            # clean up validation
            if volumeList != []:
                for volume_details in volumeList:
                    if self.backup_job.job_id in volume_details:
                        self.log.error(
                            "Exception in detaching volume attachment to proxy after backup" + str(volumeList))
                        raise Exception
            self.log.info("Volumes detacahed for proxy validation is  successful")
        except Exception as err:
            self.log.exception("Exception in detaching volume attachment to proxy after backup" + str(volumeList))
            raise Exception

    def verify_if_snapshots_and_volume_attached(self):
        """
        Validates if volumes and snapshots are detached after backup in proxy
        return: VolumeList
            """
        try:
            self.hvobj.OpenStackHandler.projectName = self.hvobj.OpenStackHandler.DEFAULT_PROJECT
            uuid = self.hvobj.OpenStackHandler.get_uuid(self.hvobj.host_machine)
            volumeList = self.hvobj.OpenStackHandler.get_volume_attachments(uuid)
            # clean up validation for volume list
            if volumeList != []:
                for volume_details in volumeList:
                    if self.backup_job.job_id in volume_details:
                        self.log.error(
                            "Exception in detaching volume attachment to proxy after backup" + str(volumeList))
                        raise Exception
            self.log.info("Volumes detached for proxy validation is successful")
            # clean up validation for snapshots
            snap_list = self.hvobj.OpenStackHandler.get_listsnapshot()
            if snap_list != []:
                for snap_details in snap_list:
                    if self.backup_job.job_id in snap_details:
                        self.log.error("Exception in detaching snap to proxy after backup" + str(snap_list))
                        raise Exception
            self.log.info("Snaps deleted for proxy validation is  successful")
        except Exception as err:
            self.log.exception("Exception in detaching volume attachments and snapshots to proxy after backup/restore")
            raise Exception

    def verify_if_snap_attached(self):
        """
        Validates if snaps are detached after backup
        return: Snaplist
        """
        try:
            snap_list = self.hvobj.OpenStackHandler.get_listsnapshot()
            if snap_list != []:
                for snap_details in snap_list:
                    if self.backup_job.job_id in snap_details:
                        self.log.error("Exception in detaching snap to proxy after backup" + str(snap_list))
                        raise Exception
            self.log.info("snaps deleted for proxy validation is  successful")
        except Exception as err:
            self.log.exception("Exception in detaching snaps attachment to proxy after backup" + str(snap_list))
            raise Exception

    def attach_volume_validation(self, attach_volume_restore_options, source_volume_details,
                                 destination_volume_details):
        """
                perform Attach Volume to existing instance restore validation for specific Openstack subclient

                Args:
                        attach_volume_restore_options    (object):   represent options that are currently set
                                                            when performing the attach volume restore

                        msg                     (string):  Log line to be printed

                Exception:
                                if job fails
                                if validation fails

        """
        try:

            project_name_restore = attach_volume_restore_options.datacenter
            self.log.info("Project name is %s", project_name_restore)
            for each_vol_source in source_volume_details:
                for each_vol_destination in destination_volume_details:
                    if each_vol_source['name'] == each_vol_destination['name']:
                        self.log.info("The name of the volume in the destination is : %s", each_vol_destination['name'])
                        indexValue = destination_volume_details.index(each_vol_destination)

                destination_vol_status = destination_volume_details[indexValue]['status']
                self.log.info("The status of the attached volume is %s", destination_vol_status)
                destination_vol_size = destination_volume_details[indexValue]['size']
                self.log.info("The size of the attached volume in destination VM is %s", destination_vol_size)
                if each_vol_source['size'] == destination_vol_size:
                    self.log.info("Source volume size matches destination volume size")
                else:
                    self.log.error("ERROR: Source volume size mismatch with destination volume size")

                self.log.info("Checking volume details and accessibility to the VM where volume is restored...")
                ips = self.hvobj.OpenStackHandler.get_all_ips(attach_volume_restore_options.dest_vm_guid)
                ip = ips['private_network'][1]['addr']
                response = os.system('ping {}'.format(ip))
                if (each_vol_source['volume_type'] == destination_volume_details[indexValue]['volume_type'] and
                        response == 0):
                    self.log.info("Data Integrity on the restored volume and accessibility to the"
                                  " instance its been attached is a SUCCESS ")
                else:
                    self.log.error("ERROR: Data Integrity on the restored volume and accessibility to the"
                                   " instance its been attached is a FAILURE ")
                destination_vol_boot = destination_volume_details[indexValue]['bootable']
                destination_vol_load = destination_volume_details[indexValue]['_loaded']
                if (bool(destination_vol_boot) and destination_vol_load):
                    self.log.info("The source volume attached is intact after restore")
                else:
                    self.log.error("ERROR: The source volume is not intact after restore")
        except Exception as err:
            self.log.exception("Attach Volume to existing instance Restore Validation failed. please check logs")
            raise Exception(
                "Attach Volume to existing instance Restore Validation failed, please check agent logs {0}".format(err))

    def update_vm_info(self, prop='Basic', os_info=True, force_update=False):
        """
        Fetches all the properties of the VM

        Args:
            prop                (str):  Basic - Basic properties of VM like HostName,
                                                especially the properties with which
                                                VM can be added as dynamic content

                                        All   - All the possible properties of the VM

            os_info             (bool): To fetch os info or not

        Raises:
            Exception:
                if failed to update all the properties of the VM

        """
        try:
            # Fetch basic props of the instance
            self._get_vm_info(prop)

            if os_info or prop == 'All':
                # Update attached volumes list to the instance
                self.get_volume_list()
                # update IP address
                if force_update:
                    self.get_pingableIP(force=True)
                else:
                    self.get_pingableIP()
                # Update machine object
                if not (self.ip):  # Before calling machine, make sure instance has atleast one external ip
                    # for communication
                    self.get_pingableIP(force=True)
                try:
                    if (socket.gethostbyname(self.vm_name)):
                        self.machine = machine.Machine(machine_name=self.vm_name, commcell_object=None, \
                                                       username=self.user_name, password=self.password)
                except:
                    self.machine = machine.Machine(machine_name=self.ip, commcell_object=None, \
                                                   username=self.user_name, password=self.password)
                # update vCPUs and diskcount
                # setattr(self,"NoofCPU",0)
                self.get_advprops()
                # Get drive list
                self.get_drive_list()

        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def _get_vm_info(self, prop, extra_args="$null"):
        """
        Get the basic or all or specific properties of VM

        Args:
                prop                (str):  basic, All or specific property like Memory

                extra_args          (str):  Extra arguments needed for property listed by ","

        Raises:
            Exception:
                if failed to get all the properties of the VM

        """
        try:

            self.log.info(
                "Collecting all the VM properties for VM %s" % self.vm_name)

            self.prop_dict["property"] = prop
            self.prop_dict["extra_args"] = extra_args
            # Get UUID for the VM
            _uuid = self.hvobj.OpenStackHandler.get_uuid(self.vm_name)
            self.guid = _uuid

            # Update the vCPUS

            if not (self.ip):  # Before calling machine, make sure instance has atleast one external ip
                # for communication
                self.get_pingableIP(force=True)
            # Get the OStype
            self.GuestOS = self.hvobj.OpenStackHandler.get_os_type(self.vm_name)
            # update the OS, currently hardcoded until we find out solution to find VM OS type
            setattr(self, "vm_guest_os", self.GuestOS)

            # Update the disk list
            vollist = self.hvobj.OpenStackHandler.get_volume_attachments(_uuid)
            self.disks = self._get_disk_info(vollist)
            self.DiskList = self.disks
            self.disk_list = self.DiskList
            self._disk_list = [disk["name"] for disk in self.disks]
            self.disk_dict = self._disk_list
            self.disks_count = len(self.disks)

            # Update all the properties of the VM
            if (_uuid):
                output = self.hvobj.OpenStackHandler.get_instance_details(_uuid)
                for _server in output["servers"]:
                    for _key in _server.keys():
                        setattr(self, _key, _server[_key])
                        if ('OS-EXT-AZ' in _key):
                            # self.getAvailabilityZone = _listofInstances[0][_key]
                            setattr(self, "AZ", _server[_key])

        except Exception as err:
            self.log.exception("Failed to Get all the VM Properties of the VM")
            raise Exception(err)

    def get_ipaddress(self):
        """
        get_ipaddress() return the ip address from address::privatenetwor::ipaddress

        :return: ip address in str format
        """
        try:
            self.log.info("Collecting IP address from networkdetails for the server {0}".format(self.vm_name))
            setattr(self, "addresses", self.hvobj.OpenStackHandler.get_all_ips(self.guid)["private_network"])
        except Exception as err:
            self.log.exception("Exception: exception occured in get_ipaddress() ".format(str(err)))

    def get_advprops(self):
        """
        get_advprops() return the vCPU, RAM detail etc

        return: dictionary of vCPU, RAM, attached volumes etc
        """
        try:
            self.log.info("Collecting advanced props for the server {0}".format(self.vm_name))
            # Update the vCPUS
            self.vcpus = self.hvobj.OpenStackHandler.get_vcpus(self.vm_name)
            # Update Ram
            self.ram = self.hvobj.OpenStackHandler.get_ram(self.vm_name)
            # Update the flavor of VM
            self.vmflavor = self.hvobj.OpenStackHandler.get_vmflavor(self.vm_name)
            setattr(self, "no_of_cpu", 0)
            setattr(self, "disk_count", 0)
            setattr(self, "memory", 0)
        except Exception as err:
            self.log.exception("Exception: exception occured in get_ipaddress() ".format(str(err)))

    def get_pingableIP(self, force=False):
        """
        get_pingableIP() will ping each IP address and gets the IP which is pingable
        force = True will associate available floatinip when instance fond to have valid ip
        return: return the IPaddress (str)
        """
        try:
            self.log.info("Getting all IP addresses avalaible for the instance")
            self.get_ipaddress()
            if (len(self.addresses) > 0):
                for _addr in self.addresses:
                    pingObj = ping(_addr["addr"])
                    if (pingObj.packet_lost <= 1):
                        self.ip = _addr["addr"]
                        # self.IP = _addr["addr"]
            if (self.ip == None):
                if (force):
                    _newip = None
                    tenant_id = self.hvobj.OpenStackHandler.get_tenant()
                    if (tenant_id == None):
                        raise Exception("Error tenant id can't be empty")
                    self.log.info("Assinging new external ip address")
                    _list_of_ips = self.hvobj.OpenStackHandler.get_floating_ips()
                    for _float_ip in _list_of_ips["floatingips"]:
                        if _float_ip["status"] == "DOWN" and _float_ip["port_id"] == None and _float_ip[
                            "tenant_id"] == tenant_id:
                            _newip = _float_ip
                            break
                    if _newip != None:
                        assigned_floating_ip = self.hvobj.OpenStackHandler.associate_floating_ips(self.GUID, _newip)
                        if assigned_floating_ip != None:
                            self.ip = assigned_floating_ip
                            self.log.info("New IP found and assigned %s", _newip)
                    else:
                        self.log.error("No valid floating ip found, validation may fail")
            # else:
            #     self.log.error("Error: No vaild  ip found for the server {0}, validation may be skipped".format(self.GUID))
        except Exception as err:
            self.log.exception("Exception: exception occured in get_pingableIP() ".format(str(err)))

    def get_volume_list(self):
        """
        Getvolumelist() gets the all attached volumes details to the server
        return: returns the list of dictionary of volume details
        """
        try:
            self.log.info("Getting all attached volumes for the instance")
            _vollist = self.hvobj.OpenStackHandler.get_volume_attachments(self.guid)
            if (len(_vollist) > 0):
                self.volumelist = _vollist
            else:
                self.log.error("Error: No vaild  attached volumes found for the server {0}".format(self.GUID))
        except Exception as err:
            self.log.exception("Exception: exception occured in get_volume_list() ".format(str(err)))

    def power_on(self):
        """
        Power on the VM.

        Raises:
            Exception:
                When power on failed

        """

        try:

            _powerstate = self.hvobj.OpenStackHandler.poweron_instance(self.GUID)

            if _powerstate:
                return
            self.log.error("The error occurred ")
            raise Exception("Exception in PowerOn")

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

            _powerstate = self.hvobj.OpenStackHandler.poweroff_instance(self.GUID)

            if _powerstate:
                return
            self.log.error("The error occurred ")
            raise Exception("Exception in PowerOff")

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

            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["operation"] = "Delete"
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)

            _stdout = output.output
            if "Success" in _stdout:
                return
            self.log.error("The error occurred {0}".format(_stdout))
            raise Exception("Exception in deleting the vm")

        except Exception as exp:
            self.log.exception("Exception in DeleteVM {0}".format(exp))
            return False

    def get_disk_in_controller(self, controller_type, number, location):
        """
        get the disk associated with controller

        Args:
                controller_type         (str):  IDE/SCSI

                number                  (int):  IDE(1:0) 1 is the disk number

                location                (int):  IDE(1:0) 0 is the location in disk number 1

        Returns:
                DiskType                (str):  disks in location of args(eg: disk in IDE(1:0))

        Raises:
            Exception:
                When there is an error in getting disks in the controller
        """
        try:
            _extr_args = "%s,%s,%s" % (controller_type, number, location)
            self._get_vm_info("DiskType", _extr_args)
            return self.DiskType

        except Exception as exp:
            self.log.exception("Exception in get_disk_in_controller")
            raise exp

    def get_disk_path_from_pattern(self, disk_pattern):
        """
        Find the disk that matches the disk pattern form disk list

        Args:
                disk_pattern            (str):  pattern which needs to be matched

        Returns:
                each_disk               (str):  the disk that matches the pattern

        Raises:
            Exception:
                When issues while getting disk path from the pattern passed
        """
        try:
            _disk_name = os.path.basename(disk_pattern)
            for each_disk in self.DiskList:
                _vm_disk_name = os.path.basename(each_disk)
                if _vm_disk_name == _disk_name:
                    self.log.info("Found the Disk to be filtered in the VM")
                    return each_disk

        except Exception as exp:
            self.log.exception("Exception in get_disk_path_from_pattern")
            raise exp

    def live_browse_vm_exists(self, _vm, vsa_restore_job):
        """
        Check the VM mounted during live browse is present or not

        Args:
            _vm                 (str):  Name of the vm which is mounted

            vsa_backup_job      (int):  File level restore job

        Returns:
            True    :       If the VM exists

            False   :       If the VM doesn't exists

        Raises:
            Exception:
                issues when not able to check if the live vm exists
        """
        try:
            vmname = _vm + "_" + str(vsa_restore_job) + "_GX_BACKUP"
            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["vm_name"] = vmname
            self.operation_dict["property"] = "VMExists"
            output = self.host_machine._execute_script(_ps_path, self.operation_dict)
            _stdout = output.output
            if "True" in _stdout:
                return True
            else:
                return False

        except Exception as err:
            self.log.exception(
                "Exception while vm existence check " + str(err))
            raise err

    def live_browse_ds_exists(self, _dslist):
        """
        Check the DS mounted during live browse is present or not

        Args:
            _dslist             (list):  List of DS which is mounted

        Returns:
            True    :       If the DS exists

            False   :       If the DS doesn't exists

        Raises:
            Exception:
                issues when not able to check if the live browse ds exists
        """
        try:
            _ps_path = os.path.join(self.utils_path, self.vm_operation_file)
            self.operation_dict["property"] = "DSExists"
            _failures = 0
            for _ds in _dslist:
                self.operation_dict["vm_name"] = _ds
                output = self.host_machine._execute_script(_ps_path, self.operation_dict)
                _stdout = output.output
                if _stdout != "False":
                    _failures += 1
            if _failures != 0:
                return True
            else:
                return False

        except Exception as err:
            self.log.exception(
                "Exception while DS existence check " + str(err))
            raise err

    def _get_disk_info(self, volume_list):
        """
        Get the name, path and size of the disks available
        Args:
            volume_list:  response of the volume_attachments()

        Returns: (list)     List of the disk with Name, Path and Size

        """

        _disks = []
        try:
            voldetails = self.hvobj.OpenStackHandler.get_volume_detail()
            for disk in volume_list:
                _vm_disk = {}
                for vol in voldetails:
                    if (disk["id"] == vol["id"]):
                        _vm_disk["volumeId"] = vol["id"]
                        _vm_disk["attachments"] = vol["attachments"]
                        _vm_disk["name"] = vol["name"]
                        _vm_disk["size"] = vol["size"]
                        _vm_disk["volume_type"] = vol["volume_type"]
                        _vm_disk["availability_zone"] = vol["availability_zone"]

                _disks.append(_vm_disk)
            return _disks
        except Exception as err:
            self.log.exception("An exception occurred in _get_disk_info")
            raise Exception(err)

    def get_drive_list(self, drives=None):

        """
        Returns the drive list for the VM
        """
        try:
            if self.GuestOS == "Windows":
                # get the list
                storage_details = self.hvobj.OpenStackHandler.get_drive_details(vmObj=self)
                _temp_drive_letter = {}
                _drive_regex = "^[a-zA-Z]$"
                for _drive in storage_details:
                    if re.match(_drive_regex, _drive[0]):
                        _driveletter = _drive[0] + ":"
                        _temp_drive_letter[_drive[0]] = _driveletter
                    # del _temp_drive_letter['D']

            else:
                index = 1
                _temp_drive_letter = {}
                storage_details = self.machine.get_storage_details()
                for _drive, _volume in storage_details.items():
                    if "/dev/vd" in _drive:
                        _temp_drive_letter["MountDir-" + str(index)] = _volume["mountpoint"]
                        index = index + 1

                    if "dev/mapper" in _drive:
                        _volume_name = _drive.split("/")[-1]
                        _temp_drive_letter[_volume_name] = _volume["mountpoint"]

            self._drive_list = _temp_drive_letter
            self._drives = _temp_drive_letter
            if not self._drive_list:
                raise Exception("Failed to Get Volume Details for the VM")

        except Exception as err:
            self.log.exception(
                "An Exception Occurred in Getting the Volume Info for the VM {0}".format(err))
            self._drive_list = []
            return False

    def copy_test_data_to_each_volume(self, _drive, backup_folder, _test_data_path):
        """
        copy testdata to each volume in the vm provided


        Args:
                _drive              (str)  -  Drive letter where data needs to be copied

                _test_data_path     (str) - path where testdata needs to be generated

                backup_folder       (str)  - name of the folder to be backed up

        Exception:

                if fails to generate testdata

                if fails to copy testdata

        """

        try:

            self.log.info("creating test data directory %s" % _test_data_path)

            # initializing prerequisites
            _failed_file_list = []

            # create Base dir
            _dest_base_path = self.machine.join_path(_drive, backup_folder, "TestData", self.hvobj.timestamp)
            if not self.machine.check_directory_exists(_dest_base_path):
                _create_dir = self.machine.create_directory(_dest_base_path)
                if not _create_dir:
                    _failed_file_list.append(_dest_base_path)

            self.log.info("Copying testdata to volume {0}".format(_drive))
            self.machine.copy_from_local(_test_data_path, _dest_base_path)


        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying test data to Vm  ")
            raise err