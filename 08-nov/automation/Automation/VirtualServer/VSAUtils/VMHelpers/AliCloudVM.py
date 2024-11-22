# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file that does all operations on AliCloud vm

Classes:

AliVm - AliThis is the main file for all  Ali Cloud VM operations


AliVM:

delete_vm()			--	Delete the VM.

power_on()			--	power on the VM.

power_off()         --  power off the VM.

update_vm_info()    --  updates vm information to current state.

get_vm_basic_prop() --  gets the basic properties of the VM like guest os, IP, power state and GUID

snapshots()         --  gets the snapshots of the VM

storage_disks()     --  gets the storage disks of the VM

"""

from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from AutomationUtils import logger


class AliCloudVM(HypervisorVM):
    """
    This is the main file for all  Ali Cloud VM operations
    """

    # pylint: disable=too-many-instance-attributes
    # VM property mandates many attributes.

    def __init__(self, hv_obj, vm_name):
        """

        Args:
            hv_obj   (Object)    -- hypervisor object

            vm_name   (str)    -- name of the vm

        """
        super(AliCloudVM, self).__init__(hv_obj, vm_name)
        self.ali_cloud = hv_obj
        self.vm_name = vm_name.lower()
        self.no_of_cpu = ""
        self.memory = ""
        self.disk_count = 0
        self.region_id = self.ali_cloud.vm_region_map.get(vm_name, None)
        self.instance_id = self.ali_cloud.vm_details.get(vm_name, {}).get("InstanceId", None)
        self.vm_info = None
        self.guid = self.instance_id
        self.guest_os = None
        self.ip = None
        self.disk_dict = dict()
        self.power_state = ""
        self.power_status_on = "Running"
        self.power_status_off = "Stopped"
        self.instance_type = None
        self._get_vm_info()
        self._basic_props_initialized = False
        self.update_vm_info()

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options=None, backup_option=None):
            self.vm = vmobj.vm
            self.vm_name = vmobj.vm.vm_name
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            """all the validation are currently done at commmon level"""
            return True

    def delete_vm(self):
        """
        delete the VM.

        return:
                True - when delete is successful

                False - when delete failed
        """
        delete_instance = {
            "RegionId": self.region_id,
            "InstanceId": self.instance_id
        }
        self.ali_cloud.execute_action("DeleteInstance", delete_instance)
        return True

    def power_on(self):
        """
        power on the VM.

        return:
                True - when power on is successful

        Exception:
                When power on failed

        """
        start_instance = {
            "RegionId": self.region_id,
            "InstanceId": self.instance_id
        }
        self.ali_cloud.execute_action("StartInstance", start_instance)
        return True

    def power_off(self):
        """
        power off the VM.

        return:
                True - when power off is successful

        Exception:
                When power off failed

        """
        stop_instance = {
            "InstanceId": self.instance_id,
            "ForceStop": "true"
        }
        self.ali_cloud.execute_action("StopInstance", stop_instance)
        return True

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
        """
        Updates vm properties to the current state.

        Args:
            prop            (str):   the type of properties to collect from VM

                possible values:
                    Basic - Collect just the basic properties like GUID, Power state, IP and OS
                    All -   Collect all the possible properties of the VM

            os_info         (bool):         If os information needs to be collected

            force_update    (bool):         If the properties have to be refreshed again

        Raises:
            Exception:
                if there is an error while updating the VM properties

        """
        if self.vm_info:
            if not self._basic_props_initialized or force_update:
                self.get_vm_basic_prop(force_update=force_update)
                self._basic_props_initialized = True

            if os_info or prop == 'All':
                if self.power_state == self.power_status_off:
                    self.power_on()
                    self.wait_for_vm_to_boot()
                self._get_vm_info()
                self.get_vm_basic_prop()
                self.vm_guest_os = self.guest_os
                self.instance_type = self.vm_info['InstanceType']
                self.no_of_cpu = self.vm_info['Cpu']
                self.memory = self.vm_info['Memory']
                self.security_groups = self.vm_info['SecurityGroupIds']['SecurityGroupId']
                if self.vm_info['VpcAttributes']:
                    self.network = self.vm_info['VpcAttributes']['VpcId'] + "\\" + self.vm_info[
                        'VpcAttributes']['VSwitchId']
                self.get_drive_list()
            elif prop == 'Basic':
                self.get_vm_basic_prop()
        else:
            raise Exception("The VM properties has not been obtained yet")

    def _get_vm_info(self):
        """
        Get all VM Info related to the given VM.

        Raises:
            Exception:
                if there is an error while getting the VM information

        """
        try:
            self.region_id = None
            self.instance_id = None
            self.log.info("VM information :: Getting all information of VM [%s]", self.vm_name)
            if not self.region_id:
                if not self.ali_cloud.vm_region_map.get(self.vm_name, None):
                    self.ali_cloud.get_all_vms_in_hypervisor()
                self.region_id = self.ali_cloud.vm_region_map[self.vm_name]
                self.instance_id = self.ali_cloud.vm_details[self.vm_name]["InstanceId"]
            else:
                if not self.instance_id:
                    if not self.ali_cloud.vm_region_map.get(self.vm_name, None):
                        self.ali_cloud.get_all_vms_in_hypervisor(self.region_id)
                    self.instance_id = self.ali_cloud.vm_details[self.vm_name]["InstanceId"]
            vm_info = {
                "RegionId": self.region_id,
                "InstanceId": self.instance_id
            }
            self.log.info(vm_info)
            try:
                self.ali_cloud.ali_url = f"https://ecs.{self.region_id}.aliyuncs.com/?"
                self.vm_info = self.ali_cloud.execute_action("DescribeInstanceAttribute", vm_info)
            except Exception as exp:
                self.ali_cloud.get_all_vms_in_hypervisor()
                self._get_vm_info()
            self.log.info(self.vm_info)

        except Exception as err:
            self.log.exception("Exception in get_vm_info")
            raise Exception(err)

    def get_vm_basic_prop(self, force_update=False):
        """
        Gets the basic properties of the VM like GUID, PowerState, GuestOS and IP

        Args:
            force_update    (bool) :   If the properties have to be refreshed again
        Raises:
            Exception:
                if there is an exception with getting the basic properties

        """
        try:
            if not self.vm_info or force_update:
                self._get_vm_info()
            self.guid = self.instance_id = self.vm_info["InstanceId"]
            self.power_state = self.vm_info["Status"]
            self.guest_os = self.ali_cloud.vm_details[self.vm_name]['OSType'].lower()
            self.no_of_cpu = self.vm_info['Cpu']
            self.memory = self.vm_info['Memory']
            if self.vm_info['PublicIpAddress']['IpAddress']:
                self.ip = self.vm_info['PublicIpAddress']['IpAddress'][0]
            else:
                self.ip = self.vm_info['VpcAttributes']['PrivateIpAddress']['IpAddress'][0]

        except Exception as exp:
            self.log.exception("Exception while getting basic properties of VM")
            raise Exception(exp)

    def snapshots(self):
        """
        get snapshots of the vm.
        return:
                Response object which contains a list of snaphosts
        """

        snapshot = {
            "InstanceId": self.instance_id,
            "RegionId": self.region_id
        }
        snapshots = self.ali_cloud.execute_action("DescribeSnapshots", snapshot)
        return snapshots

    def storage_disks(self):
        """
        get storage disks attatched  to the vm.
        return:
                response object containing the list of the storage disks
        """
        action_params = {
            "InstanceId": self.instance_id,
            "RegionId": self.region_id
        }
        disks = self.ali_cloud.execute_action("DescribeDisks", action_params)
        return disks
