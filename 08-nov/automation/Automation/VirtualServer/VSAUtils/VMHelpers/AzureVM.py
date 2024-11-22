# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Azure vm

    AzureVM:

            get_drive_list()                -  get the drive list for the VM

            _get_vm_info()                  -  get the information about the particular VM

            get_vm_guid()                   -  gets the GUID of Azure VM

            get_nic_info()                  -  get all network attached to that VM

            get_VM_size()                   -  gets the size of the Azure VM

            get_cores()                     -  get the cores of the VM

            get_Disk_info()                 -  get all the disk info of VM

            get_status_of_vm()              - get the status of VM like started.stopped

            get_OS_type()                   - update the OS type of the VM

            get_subnet_ID()                 - Update the subnet_ID for VM

            get_IP_address()                - gets the IP address of the VM

            update_vm_info()                - updates the VM info

            get_snapshotsonblobs()          - gets all snapshots associate with blobs of VM

            get_disk_snapshots()            - gets all snapshots associated with disks of VM

            get_snapshots()                 - gets all snapshots on blob and disk of VM

            get_bloburi()                   - gets uri of blob associated with VM

            get_publicipid()                - gets id pub;ic id associated with VM

            check_vmsizeof_destination_vm() - Checks destination  vmsize as mentioned in schedule

            validate_storage_account_of_destination_vm() - Checks destination storage account as mentioned in schedule

            validate_region_of_destination_vm()    -  Checks destination vm region is same as mentioned in schedule

            validate_public_ip_config_for_destination_vm()  - Checks if destination vm has public ip if mentioned in schedule

            get_snapshot_jobid()              - Gets the job id of job that created the dik snapshot

            get_nic_details()                 - Gets details of network interface attacked to vm

            get_vm_generation()               - Gets VM Generation

            validate_generation_of_dest_vm()                 - Checks if restored and source VM have same generation

            validate_resource_group_of_destination_vm()                  - Checks if restored vm is in specified resource group

            validate_vm_extensions()                - checks if restored and source VM have same VMExtensions


"""

import datetime
import json
import os
import re
import time

import xmltodict

from AutomationUtils import logger
from AutomationUtils import machine
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerConstants
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils.VirtualServerConstants import AZURE_RESOURCE_MANAGER_URL
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from VirtualServer.VSAUtils.VirtualServerConstants import RestorePointConstants

class AzureVM(HypervisorVM):
    """
    This is the main file for all AzureRM VM operations
    """

    DISK_SKU_NAMES = {
        "Standard HDD": "Standard_LRS",
        "Standard SSD": "StandardSSD_LRS",
        "Premium SSD": "Premium_LRS"
    }

    def __init__(self, hvobj, vm_name, **kwargs):
        """
        Initialization of AzureRM VM properties

        Args:

            hvobj           (obj):  Hypervisor Object

            vm_name         (str):  Name of the VM
            kwargs          (dict):
                                - resource_group_name : Only to be passed if VM is not deployed
                                                        (will skip update VM info)
                                - storage_account_name: Only to be passed if VM's blobs need to be validated
        """
        import requests
        super(AzureVM, self).__init__(hvobj, vm_name)
        self.azure_baseURL = AZURE_RESOURCE_MANAGER_URL
        self.api_version = "?api-version=2015-06-15"
        self.subscription_id = self.hvobj.subscription_id
        self.app_id = self.hvobj.app_id
        self.xmsdate = None
        self.storage_token = None
        self.tenant_id = self.hvobj.tenant_id
        self.app_password = self.hvobj.app_password
        self.azure_session = requests.Session()
        self.vm_name = vm_name
        self.access_token = self.hvobj.access_token
        self.storage_access_token = None
        self._basic_props_initialized = False
        self.storageaccount_type = None
        self.total_disk_size = 0
        self.vm_operation_file = "AzureOperation.ps1"
        self.resource_group_name = kwargs.get('resource_group_name', self.hvobj.get_resourcegroup_name(self.vm_name))
        self.workload_vm = None
        self.workload_region_proxy = []
        self.vm_files_path = self.resource_group_name
        self.network_name = None
        self.subnet_id = None
        self._vm_info = {}
        self.disk_info = {}
        self.disk_dict = {}
        self.nic_count = 0
        self.vm_state = None
        self.nic = []
        self.nic_id = []
        self.nic_details = []
        self.managed_disk = True
        self._disk_list = None
        self.disk_sku_dict = {}
        self.disk_size_dict = {}
        self.disk_lun_dict = {}
        self.restore_storage_acc = ''
        self.restore_resource_grp = ''
        self.filtered_disks = []
        self.is_encrypted = False
        self.encryption_info = {}
        self.availability_zone = None
        self.tags = None
        self.disk_encryption_info = {}
        self.auto_vm_config = {}
        self.proximity_placement_group = None
        self.security_profile_info = {}
        self.vm_subclientid = None
        self.vm_architecture = None
        self.os_image_info = {}
        self.extensions = []
        self.operation_dict = {
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "client_id": self.app_id,
            "cred_password": self.app_password,
            "vm_name": self.vm_name,
            "property": "$null",
            "extra_args": "$null"
        }
        if not kwargs.get('resource_group_name'):
            self._get_vm_info()
            self.update_vm_info()
            self.region_name = self.vm_info["location"]
        self.kwargs = kwargs

        self.validation_function_map = {
            "disk_option": self.validate_sku,
            "vm_size": self.validate_size_of_destination_vm,
            "region": self.validate_region_of_destination_vm,
            "Storage_account": self.validate_storage_account_of_destination_vm,
            "createPublicIP": self.validate_public_ip_config_of_destination_vm,
            "restoreAsManagedVM": self.validate_disk_type_of_destination_vm,
            "vm_tags": self.tags_validation,
            "disk_encryption_type": self.validate_disk_encryption,
            "extensions": self.validate_vm_extensions,
            "vm_gen": self.validate_generation_of_dest_vm,
            "proximity_placement_group": self.validate_proximity_placement_group,
            "Resource_Group": self.validate_resource_group_of_destination_vm,
            "security_groups": self.validate_nsgs,
            "subnet_id": self.validate_vnet,
            "vm_guid": self.validate_vm_guid,
            "availability_zone": self.validate_availability_zone_of_destination_vm,
            "azure_key_vault": self.validate_vm_encryption
        }

    class BackupValidation(object):
        """ Class for Backup Validation """

        def __init__(self, vm_obj, backup_option):
            """ Initializes the BackupValidation class"""
            self.vm = vm_obj
            self.backup_option = backup_option
            self.backup_job = self.backup_option.backup_job
            self.log = logger.get_log()

        def validate(self):
            """ does the backup validation """
            self.log.info("Performing Post Backup Snapshot Validation on : {0}".format(self.vm.vm_name))
            if not self.backup_job.details['jobDetail']['clientStatusInfo']['vmStatus'][0]['CBTStatus']:
                snap_exists = self.vm.check_disk_snapshots_by_jobid(self.backup_job)[0]
                if snap_exists:
                    self.log.info("Post backup snapshot validation Failed")
                    raise Exception("Post backup snapshot validation Failed")
                self.log.info("snapshot validation successful")

        def validate_workload(self, proxy_obj):
            """
            Does the validation of the backup workload Distribution

            Args:
                proxy_obj  : A dictionary of proxy name as the key and proxy location as value

            Raises:
                Exception:
                    When Workload distribution fails
            """
            if proxy_obj:
                vm_region = self.vm.hvobj.VMs[self.vm.workload_vm].region_name
                prxy_name = self.vm.hvobj.VMs[self.vm.workload_vm].proxy_name
                proxy_region = proxy_obj[prxy_name][1]
                if self.vm.workload_region_proxy:
                    if prxy_name in self.vm.workload_region_proxy:
                        self.log.info(
                            "Backup Validation successful for VM {} loc: {} Proxy {} loc: {}, (Region Match)"
                            .format(self.vm.workload_vm, vm_region, prxy_name, proxy_region))
                    else:
                        raise Exception("Failure in Backup Workload validation")
                else:
                    self.log.info("Backup Validation successful for VM {} loc: {} Proxy {} loc: {}, (Any)"
                                  .format(self.vm.workload_vm, vm_region, prxy_name, proxy_region))
            else:
                raise Exception("Failure in Backup Workload validation. Valid proxy object not passed as parameter.")

    class VmValidation(object):
        """ Class for VM Validation """

        def __init__(self, vmobj, vm_restore_options, **kwargs):
            """ Initializes the VmValidation class"""
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.restore_job = self.vm_restore_options.restore_job
            self.log = logger.get_log()

        def __eq__(self, other):
            """compares the source vm and restored vm"""
            try:
                validation_list = {
                    **VirtualServerConstants.hypervisor_vm_web_restore_option_mapping[self.vm.vm.instance_type],
                    **VirtualServerConstants.preset_hypervisor_vm_restore_options[self.vm.vm.instance_type]
                }

                overall_validation_status = True
                for key in validation_list:
                    if not hasattr(self.vm_restore_options, key):
                        setattr(self.vm_restore_options, key, None)

                    func = other.vm.vm.validation_function_map.get(key)
                    if not func:
                        self.log.error(f"Validation for {key} is missing.")
                        overall_validation_status = False
                        continue
                    if not func(self.vm.vm, other.vm.vm, "Full VM Restore", self.vm_restore_options):
                        overall_validation_status = False

                if not overall_validation_status:
                    self.log.error("VM configuration validation failed. Check logs for details")
                    return False

                self.log.info("VM configuration validation passed.")
                return True

            except Exception as exp:
                self.log.exception("Exception in Vm Validation")
                raise Exception("Exception in Vm Validation:" + str(exp))

        def validate_restore_workload(self, proxy_obj):
            """
                Does the validation of the restore workload Distribution

                Args:
                    proxy_obj  : A dictionary of proxy name as the key and proxy location as value

                Raises:
                    Exception:
                        When Workload distribution fails
            """
            vm_region = self.vm.hvobj.VMs[self.vm.workload_vm].region_name
            prxy_name = self.vm.hvobj.VMs[self.vm.workload_vm].proxy_name
            proxy_region = proxy_obj[prxy_name]
            if self.vm.workload_region_proxy:
                if prxy_name in self.vm.workload_region_proxy:
                    self.log.info(
                        "Restore Validation successful for VM {0} loc: {1} Proxy {2} loc: {3}, (Region Match)"
                                  .format(self.vm.workload_vm, vm_region, prxy_name, proxy_region))
                else:
                    raise Exception("Failure in Restore Workload validation")
            else:
                self.log.info("Restore Validation successful for VM {0} loc: {1} Proxy {2} loc: {3}, (Region Match)"
                              .format(self.vm.workload_vm, vm_region, prxy_name, proxy_region))

    class LiveSyncVmValidation(object):
        """ Class for Livesync Validation """

        def __init__(self, vmobj, schedule, replicationjob, live_sync_options=None):
            """ Initializes the LiveSyncVmValidation class"""
            self.vm = vmobj
            self.schedule = schedule
            self.replicationjob = replicationjob
            self.log = logger.get_log()

        def __eq__(self, other):
            """ performs hypervisor specific LiveSync validation """
            try:
                # Blob snap shot validation
                destsnaps = other.vm.vm.get_snapshotsonblobs()
                startime = self.replicationjob.start_time
                endtime = self.replicationjob.end_time
                for disk in destsnaps:
                    snap_exists = False
                    if len(destsnaps[disk]) <= 1:
                        snap_exists = other.vm.vm.check_snap_exist_intimeinterval(destsnaps[disk],
                                                                                  startime, endtime)
                    else:
                        self.log.error("More than snapshot exist , please check the snapshot tree for this VM ")
                        raise Exception("More than one snapshot exist")

                    if not snap_exists:
                        self.log.info("snapshot validation Failed")
                        return False

                self.log.info("snapshot validation successful")

                if not self.vm.vm.validate_size_of_destination_vm(self.schedule, other.vm.vm):
                    self.log.info("vmSize validation of vm failed")
                    return False

                if not self.vm.vm.validate_region_of_destination_vm(self.schedule, other.vm.vm):
                    self.log.info("region of vm validation of vm failed")
                    return False
                if not self.vm.vm.validate_generation_of_dest_vm(other.vm.vm):
                    self.log.info("VM generation  validation of vm failed")
                    return False
                if not self.vm.vm.validate_storage_account_of_destination_vm(self.schedule, other.vm.vm):
                    self.log.info("storage account  validation of vm failed")
                    return False
                if not self.vm.vm.validate_public_ip_config_of_destination_vm(self.schedule, other.vm.vm):
                    self.log.info("publicip  validation of vm failed")
                    return False
                if not self.vm.vm.validate_disk_type_of_destination_vm(other.vm.vm, other.vm.vm,
                                                                       vm_schedule=self.schedule):
                    self.log.info("Disk Type validation of vm failed")
                    return False
                if not self.vm.vm.validate_resource_group_of_destination_vm(self.schedule, other.vm.vm):
                    self.log.info("Resource Group  validation of vm failed")
                    return False
                return True

            except Exception as exp:
                self.log.exception("Exception in LiveSyncValidation")
                raise Exception("Exception in LiveSyncValidation:" + str(exp))

    class VmConversionValidation(object):
        """ Class for VmConversion Validation """

        def __init__(self, vmobj, vm_restore_options):
            """ Initializes the VmConversionValidation class"""
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):
            """

            Args:
                other (obj): VmConversionValidation object to compare to

            Returns:
                config (bool): Returns true if all parameters match
            """

            validation_list = {
                **VirtualServerConstants.hypervisor_vm_web_restore_option_mapping[other.vm.instance_type],
                **VirtualServerConstants.preset_hypervisor_vm_restore_options[other.vm.instance_type]
            }

            overall_validation_status = True
            for key in validation_list:
                if not hasattr(other.vm_restore_options, key):
                    setattr(other.vm_restore_options, key, None)

                func = other.vm.validation_function_map.get(key)
                if not func:
                    self.log.error(f"Validation for {key} is missing.")
                    overall_validation_status = False
                    continue
                if not func(self.vm, other.vm, "Conversion", self.vm_restore_options):
                    overall_validation_status = False
            return overall_validation_status

    class DrValidation(HypervisorVM.DrValidation):
        """ Class for DR Validation """
        def __init__(self, vmobj, vm_options, **kwargs):
            """ Initializes the DrValidation class"""
            super().__init__(vmobj, vm_options, **kwargs)

        def validate_vm_exists(self):
            """ Validates that the VM exists on hypervisor """
            self.vm.hvobj.collect_all_vm_data()
            return super().validate_vm_exists()

        def validate_no_vm_exists(self):
            """ Validates that the VM does not exist on hypervisor """
            self.vm.hvobj.collect_all_vm_data()
            return super().validate_no_vm_exists()

        def validate_cpu_count(self, **kwargs):
            """CPU count validations for 'Auto' vm size"""
            # If VM size is set in VM options, skip this validation
            if self.vm_options.get('vmSize'):
                return
            # If VM size is 'Auto', validate that the VM size is selected intelligently from source VM's CPU count
            if self.vm.no_of_cpu >= self.vm_options.get('cpuCount'):
                raise Exception(f"Expected CPU count {self.vm_options.get('cpuCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.no_of_cpu}")

        def validate_memory(self, **kwargs):
            """Memory size validations for 'Auto' vm size"""
            # If VM size is set in VM options, skip this validation
            if self.vm_options.get('vmSize'):
                return
            # If VM size is 'Auto', validate that the VM size is selected intelligently from source VM's memory size
            if self.vm.memory >= self.vm_options.get('memory'):
                raise Exception(f"Expected memory size: {self.vm_options.get('memory')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.memory}")

        def validate_disk_count(self, **kwargs):
            """Validates the disk size, SKU and type(managed or unmanaged) matches the VM options"""
            blobs_retained = kwargs.get('blobs_retained')
            if self.vm_options.get('restoreAsManagedVM', False):
                # Perform managed disk validations and skip blob validations
                self.log.info('Performing managed VM disk validations for VM: %s', self.vm.vm_name)
                self.validate_disks(disk_exist_check=True, blob_exist_check=blobs_retained)

            else:
                # Perform blob validations and skip managed disk validations
                self.log.info('Performing unmanaged VM disk validations for VM: %s', self.vm.vm_name)
                self.validate_disks(disk_exist_check=None, blob_exist_check=True)

        def validate_disks(self, **kwargs):
            """
            Validates all the disk parameters and the metadata for them
            Args:
                disk_exist_check (bool or None): When set to True, it will validate that disks exist in resource group
                                                    and are attached to VM
                                                 When set to False, it will validate that disks don't exist
                                                    in resource groups
                                                 When set to None, skip disk checks
                blob_exist_check (bool or None): When set to True, it will validate that all blobs
                                                    exist on storage account
                                                 When set to False, it will validate that all VHDs don't exist
                                                    on storage account
                                                 When set to None, skip blob checks
            """
            disk_exist_check = kwargs.get('disk_exist_check', True)
            blob_exist_check = kwargs.get('blob_exist_check', True)
            if self.vm_options.get('disks'):
                # Create a set of incorrect blobs
                incorrect_blobs = set()

                for disk_name, disk_info in self.vm_options.get('disks', {}).items():
                    expected_disk_uri = disk_info.get('uri')
                    expected_disk_sku = disk_info.get('sku')
                    expected_disk_size = disk_info.get('size')
                    expected_disk_lun = disk_info.get('lun')
                    is_managed = disk_info.get('isManaged', False)

                    if is_managed:
                        if disk_exist_check is None:
                            self.log.info('Skipping disk check validation for VM: %s', self.vm.vm_name)
                        elif disk_exist_check:
                            # Match the observed disk name from the disk LUN number of expected disk
                            if expected_disk_lun not in self.vm.disk_lun_dict:
                                raise Exception(f"Disk LUN [{expected_disk_lun}] not found for VM: [{self.vm.vm_name}]")
                            observed_disk_name = self.vm.disk_lun_dict[expected_disk_lun]
                            observed_disk_uri = self.vm.disk_info.get(observed_disk_name, '')
                            observed_disk_size = self.vm.disk_size_dict.get(observed_disk_name, 0)
                            observed_disk_sku = self.vm.disk_sku_dict.get(expected_disk_lun, {}).get('storageAccountType') if is_managed else None

                            # Perform managed disk validations. i.e Check it exists, size and SKU
                            if expected_disk_uri:
                                if expected_disk_uri == observed_disk_uri:
                                    self.log.info(f"Disk URI remained intact: {expected_disk_uri}")
                                else:
                                    raise Exception(f"Disk URI changed from [{expected_disk_uri}] to [{observed_disk_uri}]")
                                # If disk is managed and disk URI is given, expect same URI to exist
                                # This is done to validate VM's disk after failback
                                if not self.vm.hvobj.check_disk_exists_in_resource_group(expected_disk_uri):
                                    raise Exception(f"Disk: {expected_disk_uri} doesn't exist for [{self.vm.vm_name}]")
                            if expected_disk_size:
                                # If disk size is passed, validate it with expected VM disk size
                                if observed_disk_size == expected_disk_size:
                                    self.log.info(f"Disk size for {expected_disk_uri} is {expected_disk_size}")
                                else:
                                    raise Exception(f"Disk size for [{expected_disk_uri}] changed from {expected_disk_size}"
                                                    f" to {observed_disk_size}")
                            if expected_disk_sku:
                                if expected_disk_sku == observed_disk_sku:
                                    self.log.info(f"Disk SKU remained intact: {disk_name}")
                                else:
                                    raise Exception(f"Disk SKU changed from [{expected_disk_sku}] to [{observed_disk_sku}] for VM: [{self.vm.vm_name}]")
                        else:
                            # Check that disk doesn't exist
                            if expected_disk_uri and self.vm.hvobj.check_disk_exists_in_resource_group(expected_disk_uri):
                                raise Exception(f"Disk {expected_disk_uri} exists even though it shouldn't for "
                                                f"VM: {self.vm.vm_name}")
                        # Perform storage account blob check to make sure it exists if option enabled
                        if blob_exist_check is None:
                            self.log.info('Skipping blob check validation for VM: %s', self.vm.vm_name)
                        # Perform storage account blob check to make sure it exists
                        else:
                            if blob_exist_check:
                                if expected_disk_uri and not self.vm.hvobj.check_blob_exists_in_storage_account(expected_disk_uri):
                                    incorrect_blobs.add(expected_disk_uri)
                            else:
                                # Perform storage account check to make sure blob doesn't exist
                                if expected_disk_uri and self.vm.hvobj.check_blob_exists_in_storage_account(expected_disk_uri):
                                    incorrect_blobs.add(expected_disk_uri)
                    else:
                        if blob_exist_check is None:
                            self.log.info('Skipping blob check validation for VM: %s', self.vm.vm_name)
                        # Perform storage account blob check to make sure it exists
                        elif blob_exist_check:
                            if expected_disk_uri and not self.vm.hvobj.check_blob_exists_in_storage_account(expected_disk_uri):
                                incorrect_blobs.add(expected_disk_uri)
                        else:
                            # Perform storage account check to make sure blob doesn't exist
                            if expected_disk_uri and self.vm.hvobj.check_blob_exists_in_storage_account(expected_disk_uri):
                                incorrect_blobs.add(expected_disk_uri)

                # Check skipped if blob_exist_check=None
                # If any blob exists/doesn't exist when it is expected to, show set of all blobs
                if blob_exist_check is not None and incorrect_blobs:
                    if blob_exist_check:
                        raise Exception(f"Missing blobs: [{incorrect_blobs}] in storage account"
                                        f" for VM: {self.vm.vm_name}")
                    else:
                        raise Exception(f"Blobs: [{incorrect_blobs}] exist in storage account"
                                        f" for VM: {self.vm.vm_name} even when it shouldn't")

        def validate_no_network_adapter(self, **kwargs):
            """ Validates that the network adapter doesn't exist """
            nics = self.vm.hvobj.get_network_interfaces_in_resource_group(self.vm_options.get('resourceGroup'))
            for nic in nics:
                if self.vm.vm_name == nic.get("name"):
                    raise Exception(f"NIC with name [{nic.get('name')}] still exists on hypervisor")

        def validate_network_adapter(self, **kwargs):
            """Validate the network adapter"""
            # Validate that the number of NICs is validated in 2 cases:
            # Validation for source will make sure that the NIC count is maintained before and after failback
            # Validation for destination will make sure there is 1 NIC on DRVM
            if self.vm_options.get('nicCount') != self.vm.nic_count:
                raise Exception(f"Expected NIC count: {self.vm_options.get('nicCount')} not observed on"
                                f" VM {self.vm.vm_name}: {self.vm.nic_count}")

        def validate_dvdf(self, **kwargs):
            """Validate 'deploy VM during failover' VM is ready on hypervisor(only for cloud hypervisors)"""
            self.vm.hvobj.collect_all_vm_data()
            vm_provisioned = self.vm.hvobj.check_vms_exist([self.vm.vm_name])
            if vm_provisioned:
                raise Exception(f"VM [{self.vm.vm_name}] exists on hypervisor before failover,"
                                f" even when DVDF is enabled")
            # Validate that the blobs are present is storage account, skip managed disk validations
            self.validate_disks(disk_exist_check=None, blob_exist_check=True)

        def validate_dvdf_on_failover(self, **kwargs):
            """Validate 'deploy VM during failover' VM is deployed after failover(only for cloud hypervisors)"""
            self.vm.hvobj.collect_all_vm_data()
            vm_provisioned = self.vm.hvobj.check_vms_exist([self.vm.vm_name])
            if not vm_provisioned:
                raise Exception(f"VM [{self.vm.vm_name}] does NOT exist on hypervisor after failover,"
                                f" when DVDF is enabled")

        def validate_warm_sync(self, **kwargs):
            """ Validate Warm sync is applied on hypervisors"""
            # Validate that the VM and blobs don't exist on storage account if warm sync is enabled
            super().validate_warm_sync(**kwargs)
            # No disks or blobs should exist on storage account/resource group
            self.validate_disks(disk_exist_check=False, blob_exist_check=False)
            self.validate_no_network_adapter()

        def validate_resource_group(self, **kwargs):
            """ Validate the resource group of the VM matches the VM options """
            if self.vm.resource_group_name != self.vm_options.get('resourceGroup'):
                raise Exception(f"VM [{self.vm.vm_name}] resource group: {self.vm.resource_group_name},"
                                f" expected: {self.vm_options.get('resourceGroup')}")

        def validate_region(self, **kwargs):
            """ Validates that the region of the VM matches the VM options"""
            if self.vm_options.get('region') and self.vm_options.get('region') != self.vm.region:
                raise Exception(f"VM [{self.vm.vm_name}] region: {self.vm.region},"
                                f" expected: {self.vm_options.get('region')}")

        def validate_availability_zone(self, **kwargs):
            """ Validates that the availability zone of the VM matches the VM options"""
            # Skip validation as availability zone can only be set for managed VMs
            if not self.vm_options.get('restoreAsManagedVM', False):
                return
            vm_sizes_info = self.vm.hvobj.get_all_available_vm_sizes(self.vm.region)
            zones = vm_sizes_info.get((self.vm.vm_size, self.vm.region), {}).get('zones', [])
            # If no availability zones are supported for VM size and region, no availability zone is present
            if not zones and self.vm.availability_zone != 'None':
                raise Exception(f"VM [{self.vm.vm_name}] availability zone: {self.vm.availability_zone},"
                                f" expected: 'None'")
            # If availability zone is set in VM options
            # or taken from Azure source VM
            if self.vm_options.get('availabilityZone'):
                # When availability zone in VM options is supported, expect it to be present on DR VM
                if (str(self.vm_options.get('availabilityZone')) in zones
                        and str(self.vm.availability_zone) != str(self.vm_options.get('availabilityZone'))):
                    raise Exception(f"VM [{self.vm.vm_name}] availability zone: {self.vm.availability_zone},"
                                    f" expected: {self.vm_options.get('availabilityZone')}")
                # when availability zone is not supported, expect it to NOT be set on DR VM
                if (str(self.vm_options.get('availabilityZone')) not in zones
                        and str(self.vm.availability_zone) != 'None'):
                    raise Exception(f"VM [{self.vm.vm_name}] availability zone: {self.vm.availability_zone},"
                                    f" expected: 'None'")
            # In case of 'Auto' and cross-hypervisor/no zone Azure VMs, expect one of the supported zones
            if self.vm_options.get('availabilityZone') is None and str(self.vm.availability_zone) not in zones:
                raise Exception(f"VM [{self.vm.vm_name}] availability zone: {self.vm.availability_zone},"
                                f" expected one of: {zones}")

        def validate_vm_size(self, **kwargs):
            """ Validate that the VM size matches the size in VM options (if set) """
            vm_sizes = [key[0] for key in self.vm.hvobj.get_all_available_vm_sizes(self.vm.region).keys()]
            # If VM size is set in VM options and is supported by the region, expect it to be set on DR VM
            if (self.vm_options.get('vmSize') and self.vm_options.get('vmSize') in vm_sizes
                    and self.vm.vm_size not in self.vm_options.get('vmSize')):
                raise Exception(f"VM [{self.vm.vm_name}] size: {self.vm.vm_size},"
                                f" expected: {self.vm_options.get('vmSize')}")
            # When the size is set as Auto, fallback to CPU and memory size validations
            # but make sure that the VM size is one supported by the region of the VM
            if self.vm_options.get('vmSize') is None and self.vm.vm_size not in vm_sizes:
                raise Exception(f"VM [{self.vm.vm_name}] size: {self.vm.vm_size},"
                                f" not supported in the region {self.vm.region}")

        def validate_vnets(self, **kwargs):
            """ Validate the virtual network of VM matches the VM options """
            # If Vnets are set in VM options, make sure they exist on the VM
            if self.vm_options.get('virtualNetworks'):
                vnets = set([nic.get('subnet_uri') for nic in self.vm.nic_details])
                expected_vnets = set(self.vm_options.get('virtualNetworks'))
                # If more than 1 Vnet is expected, make sure all Vnets match
                if len(expected_vnets) > 1 and expected_vnets != vnets:
                    raise Exception(f"VM [{self.vm.vm_name}] subnets: {vnets},"
                                    f" expected: {expected_vnets}")
                # If only 1 Vnet is to be assigned, make sure one of the expected Vnets exist on the DR VM
                if len(expected_vnets) == 1 and expected_vnets - vnets:
                    raise Exception(f"VM [{self.vm.vm_name}] subnets: {vnets},"
                                    f" expected: {expected_vnets}")
            # If vnet is set as Auto, make sure that the Vnet is picked from the
            # same resource group and region of the DR VM
            if self.vm_options.get('virtualNetworks') is None:
                rg_vnets = set([vnet.get('id') for vnet in self.vm.hvobj
                               .get_all_vnets_in_resource_group(self.vm.resource_group_name)])
                vnets = set([nic.get('subnet_uri') for nic in self.vm.nic_details])
                if vnets - rg_vnets:
                    raise Exception(f"VM [{self.vm.vm_name}] subnets: {vnets},"
                                    f" expected one of the Vnets: {rg_vnets}")

        def validate_nsgs(self, **kwargs):
            """ Validate the list of network security groups matches the VM options """
            # If NSGs are set in VM options, make sure they exist on the VM
            if self.vm_options.get('networkSecurityGroups'):
                nsgs = set([nic.get('nsg_uri') for nic in self.vm.nic_details])
                expected_nsgs = set(self.vm_options.get('networkSecurityGroups'))
                # If more than 1 NSG is expected, make sure all NSGs match
                if len(expected_nsgs) > 1 and expected_nsgs != nsgs:
                    raise Exception(f"VM [{self.vm.vm_name}] NSGs: {nsgs},"
                                    f" expected: {expected_nsgs}")
                # If only 1 NSG is to be assigned, make sure one of the expected NSGs exist on the DR VM
                if len(expected_nsgs) == 1 and expected_nsgs - nsgs:
                    raise Exception(f"VM [{self.vm.vm_name}] NSGs: {nsgs},"
                                    f" expected: {expected_nsgs}")
            # If NSG is set as Auto, make sure that the NSG is picked from the
            # same resource group and region of the DR VM
            if self.vm_options.get('networkSecurityGroups') is None:
                rg_nsgs = set([nsg.get('id')
                               for nsg in self.vm.hvobj.get_all_nsgs_in_resource_group(self.vm.resource_group_name)
                               if nsg.get('location') == self.vm.region])
                nsgs = set([nic.get('nsg_uri') for nic in self.vm.nic_details])
                if nsgs - rg_nsgs:
                    raise Exception(f"VM [{self.vm.vm_name}] NSG: {nsgs},"
                                    f" expected one of the NSGs: {rg_nsgs}")

        def validate_public_ip(self, **kwargs):
            """ Validate that the VM has public IP set, if set in VM options"""
            # Skip public IP validation if not set
            expected_public_ip = sorted(self.vm_options.get('createPublicIp'))
            public_ip = sorted([bool(nic.get('public_ip_uri')) for nic in self.vm.nic_details])
            if expected_public_ip != public_ip:
                raise Exception(f"NICs for VM {self.vm.vm_name} does not have public IP on some NICs")

        def advanced_validation(self, other, **kwargs):
            """Hypervisor specific validations"""
            self.validate_resource_group()
            self.validate_region()
            self.validate_availability_zone()
            self.validate_vm_size()
            self.validate_vnets()
            self.validate_nsgs()
            self.validate_public_ip()

    class AutoScaleVmValidation(object):
        """ Class for auto scale validation  """

        def __init__(self, vm_obj, auto_scale_region_info):
            """ Initializes the AutoScaleVmValidation class
            Args :
              vm_obj :  vm object of auto proxy to be validated
               auto_scale_region_info (dict): dictionary of auto scale configuration


            """
            self.vm = vm_obj
            self.auto_scale_region_info = auto_scale_region_info
            self.log = logger.get_log()

        def validate_proxy_resource_cleanup(self):
            """
                Validates if auto scale proxy resources are cleaned up

            Returns:
                cleanup_status (bool): True if validation is successful else False
            """
            cleanup_status = True
            for nic in self.vm.nic_id:
                if self.vm.hvobj.get_managed_resource_info_by_id(nic)[2] != 404:
                    self.log.error("Network interface {0} not cleaned up . status code {1}".\
                                   format(nic, self.vm.hvobj.get_managed_resource_info_by_id(nic)[2]))
                    cleanup_status = False
            for nic in self.vm.nic_details:
                if nic.get('public_ip_uri', None) and self.vm.hvobj. \
                        get_managed_resource_info_by_id(nic.get('public_ip_uri'))[2] != 404:
                    self.log.error("Public ip address {0} not cleaned up".
                                   format(nic.get('public_ip_uri')))
                    cleanup_status = False
            for disk, disk_id in self.vm.disk_info.items():
                if self.vm.managed_disk:
                    status_code = self.vm.hvobj.get_managed_resource_info_by_id(disk_id)[2]
                else:
                    status_code = self.vm.azure_session.head(disk_id,
                                                             headers=self.vm.get_storage_header('2019-12-12'))

                if status_code != 404:
                    self.log.error("Disk {0} not cleaned up ".format(disk))
                    cleanup_status = False

            return cleanup_status

        def validate_auto_scale_proxy_configuration(self, autoscale_policy):
            """
                Validates auto proxy created has the valid configuration

            Args:
                autoscale_policy : Autoscale policy

            Returns:
                config_status (bool): True if validation is successful else False
            """
            config_status = True
            resource_group = autoscale_policy.get('esxServers', [{}])[0].get('esxServerName', None)
            public_ip_allowed = autoscale_policy.get('isPublicIPSettingsAllowed', False)

            region_config_info = self.auto_scale_region_info.get(self.vm.vm_info['location'])
            if self.vm.nic_details[0].get('subnet_uri') != region_config_info.get('subnetId'):
                self.log.error("Specified subnet : {0} , subnet proxy is connected : {1} \
                . Validation failed".format(self.vm.nic_details[0].get('subnet_uri'),
                                            region_config_info.get('subnetId')))
                config_status = False
            if region_config_info.get("securityGroups", [{}])[0].get("groupId", None) and \
                    region_config_info.get("securityGroups")[0].get("groupId") != \
                    self.vm.nic_details[0].get('nsg_uri', None):
                self.log.error("Specified networkSecurityGroup : {0} ,\
                 configured networkSecurityGroup : {1} . Validation failed".
                               format(region_config_info.get("securityGroups")[0].get("groupId"),
                                      self.vm.nic_details.get('nsg_uri', None)))
                config_status = False

            if resource_group and self.vm.resource_group_name \
                    != resource_group:
                self.log.error("Specified resource group {0}, configured {1} ,\
                 validation failed".format(resource_group,
                                           self.vm.resource_group_name))
                config_status = False

            if public_ip_allowed and \
                    not self.vm.nic_details[0].get("public_ip_uri", None):
                self.log.error(
                    "Public ip configuration is allowed but not configured. Validation failed")
                config_status = False

            return config_status

    @property
    def azure_vmurl(self):
        """
            The azure URL for the VM, for making API calls
        """

        if self.resource_group_name is None:
            self.hvobj.get_resourcegroup_name(self.vm_name)

        azure_vmurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                      "/%s/providers/Microsoft.Compute/virtualMachines" \
                      "/%s" % (self.subscription_id, self.resource_group_name, self.vm_name)
        return azure_vmurl

    @property
    def azure_diskurl(self):
        """
        The azure disk URL for making API calls
        """
        if self.resource_group_name is None:
            self.hvobj.get_resourcegroup_name(self.vm_name)

        azure_diskurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                        "/%s/providers/Microsoft.Compute/disks/" % (self.subscription_id, self.resource_group_name)
        return azure_diskurl

    @property
    def vm_info(self):
        """
            It is used to fetch VM info. This is read only property
        """
        if self._vm_info.get(self.vm_name, {}) == {}:
            self._get_vm_info()
        return self._vm_info[self.vm_name]

    @vm_info.setter
    def vm_info(self, value):
        """
             This is to set vmname for VM info
        """
        self._vm_info[self.vm_name] = value

    @property
    def vm_hostname(self):
        """gets the vm hostname as IP (if available or vm name). It is a read only attribute"""

        if self.vm_name[0:3] == 'del':
            return self.vm_name[3:]
        else:
            return self.vm_name

    @property
    def access_token(self):
        """
            Returns access token for session. This is read only property
        """
        return self.hvobj.access_token

    @access_token.setter
    def access_token(self, token):
        """
            This is to set Access token for current session
        """
        self.hvobj._access_token = token

    @property
    def default_headers(self):
        """
            Returns the default header for making API calls. This is read only property
        """

        self.hvobj._default_headers = {"Content-Type": "application/json",
                                       "Authorization": "Bearer %s" % self.access_token}
        return self.hvobj._default_headers

    @property
    def storage_data(self):
        """
            Returns the default data parameter for making API calls for storage accounts. This is read only property
        """

        self.hvobj._storage_data = {"grant_type": "client_credentials",
                                    "client_id": self.app_id,
                                    "client_secret": self.app_password,
                                    "resource": "https://storage.azure.com"}
        return self.hvobj._storage_data

    @property
    def storage_headers(self):
        """
            Returns the default header for making API calls for storage account. This is read only property
        """

        self.hvobj._storage_headers = {"Authorization": "Bearer %s" % self.storage_token,
                                       "x-ms-date": "%s" % self.xmsdate,
                                       "x-ms-version": "2018-03-28",
                                       "x-ms-delete-snapshots": "include"}
        return self.hvobj._storage_headers

    @property
    def disk_list(self):
        """to fetch the disk in the VM
        Return:
            disk_list   (list)- list of disk in VM

        """
        if self.disk_dict:
            self._disk_list = self.disk_dict.keys()

        else:
            self._disk_list = []

        return self._disk_list

    @property
    def region(self):
        """
        Returns the region of the VM
        """
        return self.vm_info.get('location')

    @property
    def disk_storage_account(self):
        """
        Returns the storage account of the OS disk
        """
        disk_uri = self.disk_dict.get('OsDisk', '')
        return self.hvobj.parse_disk_storage_account(disk_uri)

    @property
    def disk_type(self):
        """
        Returns the disk type if the VM is managed one
        """
        return self.disk_sku_dict.get(-1, {}).get('storageAccountType')

    def _set_credentials(self, os_name):
        """
        set the credentials for VM by reading the config INI file
        """
        machine_obj = machine.Machine(commcell_object=self.commcell)
        try:
            machine_obj.remove_host_file_entry(self.vm_hostname)
        except:
            self.log.error("Soft Error : Error in removing host file entry")
            pass
        machine_obj.add_host_file_entry(self.vm_hostname, self.ip)
        retry = 0
        while retry < 6:
            try:
                self.log.info("Pinging the vm and getting os info Attempt : {0}".format(retry))
                os_name = self.get_os_name(self.vm_hostname)
                break
            except Exception as err:
                self.log.info("OS Info wasn't updated. Trying again")
                if retry == 0 and not self.is_powered_on():
                    self.power_on()
                    time.sleep(150)
                time.sleep(80)
                retry = retry + 1

        if self.user_name and self.password:
            try:
                run_as_sudo = self.user_name.lower() in ['azureuser', 'cvuser']
                vm_machine = machine.Machine(self.vm_hostname,
                                             username=self.user_name,
                                             password=self.password,
                                             run_as_sudo=run_as_sudo
                                             )
                if vm_machine:
                    self.machine = vm_machine
                    return
            except:
                raise Exception("Could not create Machine object! The existing username and "
                                "password are incorrect")

        self.guest_os = os_name
        sections = VirtualServerUtils.get_details_from_config_file(os_name.lower())
        user_list = sections.split(",")
        incorrect_usernames = []
        for each_user in user_list:
            if each_user:
                user_name = each_user.split(":")[0]
                password = VirtualServerUtils.decode_password(each_user.split(":")[1])
                try:
                    run_as_sudo = user_name.lower() in ['azureuser']
                    vm_machine = machine.Machine(self.vm_hostname,
                                                 username=user_name,
                                                 password=password,
                                                 run_as_sudo=run_as_sudo
                                                 )
                    if vm_machine:
                        self.machine = vm_machine
                        self.user_name = user_name
                        self.password = password
                        return
                except:
                    incorrect_usernames.append(each_user.split(":")[0])

        self.log.exception("Could not create Machine object! The following user names are "
                           "incorrect: {0}".format(incorrect_usernames))

    def get_drive_list(self, drives=None):
        """
        Returns the drive list for the VM
        """
        try:
            super(AzureVM, self).get_drive_list()
            if self.guest_os == "Windows":
                if 'D' in self._drives:
                    del self._drives['D']
            if self.guest_os == "Linux":
                if "MountDir-3" in self._drives:
                    del self._drives["MountDir-3"]
                if '/mnt' in self._drives:
                    del self._drives['/mnt']
                if '/mnt/resource' in self._drives:
                    del self._drives['/mnt/resource']

        except Exception as err:
            self.log.exception(
                "An Exception Occurred in Getting the Volume Info for the VM {0}".format(err))
            return False

    def power_on(self):
        """
        Power on the VM.

        Raises:
            Exception:
                When power on fails or unexpected error code is returned

        """
        try:

            self.api_version = "/start?api-version=2018-10-01"

            vm_poweronurl = self.azure_vmurl + self.api_version
            response = self.azure_session.post(vm_poweronurl, headers=self.default_headers, verify=False)
            # data = response.json()

            if response.status_code == 202:
                self.log.info('VMs found and powering on')
                time.sleep(30)

            elif response.status_code == 404:
                self.log.info('No VMs found')

            else:
                self.log.error('Azure response [{0}] Status code [{1}]'.format(
                    response.text, response.status_code))
                raise Exception("VM cannot be started")

        except Exception as exp:
            self.log.exception("Exception in PowerOn")
            raise Exception("Exception in PowerOn:" + str(exp))

    def power_off(self, skip_wait_time=False):
        """
        Deallocate the VM.

        Args:
            skip_wait_time (bool): skips 30 seconds sleep time after power off

        Raises:
            Exception:
                When power off fails or unexpected error code is returned

        """

        try:

            self.api_version = "/deallocate?api-version=2018-10-01"

            vm_poweroffurl = self.azure_vmurl + self.api_version
            response = self.azure_session.post(vm_poweroffurl, headers=self.default_headers, verify=False)

            if response.status_code == 202:
                self.log.info('VMs found and turning off')
                if not skip_wait_time:
                    time.sleep(30)

            elif response.status_code == 404:
                self.log.info('No VMs found')

            else:
                self.log.error('Azure response [{0}] Status code [{1}]'.format(
                    response.text, response.status_code))
                raise Exception("VM cannot be turned off")

        except Exception as exp:
            self.log.exception("Exception in PowerOff")
            raise Exception("Exception in Poweroff:" + str(exp))

    def clean_up_network(self):
        """
                 Clean up NIC

                 Raises:
                     Exception:
                         When cleanup failed or unexpected error code is returned

                 """

        for eachname in self.nic:
            azure_networkurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups/%s/providers/Microsoft.Network/networkInterfaces/%s?api-version=2018-07-01" % (
                self.subscription_id, self.resource_group_name, eachname)
            response = self.azure_session.delete(azure_networkurl, headers=self.default_headers,
                                                 verify=False)

            if response.status_code == 202:
                self.log.info('Network interface %s found and deleting' % eachname)
                time.sleep(120)
                response = self.azure_session.delete(azure_networkurl, headers=self.default_headers,
                                                     verify=False)
                if response.status_code == 204:
                    self.log.info('Network interface deleted')
            elif response.status_code == 204:
                self.log.info('Network interface %s not found' % eachname)

            else:
                self.log.error('Azure response [{0}] Status code [{1}]'.format(
                    response.text, response.status_code))
                raise Exception("Network interface %s cannot be deleted" % eachname)

    def clean_up_disk(self, os_disk_details, skip_os_disk=False):
        """
                 Clean up managed/unmanaged disk

                 Args:
                     os_disk_details (dict): dictionary with disk details

                     skip_os_disk (bool): skips clean-up of os disk

                 Raises:
                     Exception:
                         When cleanup failed or unexpected error code is returned

                 """

        if 'managedDisk' in os_disk_details:

            for each in self.disk_info:
                if skip_os_disk and each == 'OsDisk':
                    self.log.info("Skipping deletion of Os Disk")
                    continue
                azure_datadiskurl = AZURE_RESOURCE_MANAGER_URL + "%s?api-version=2017-03-30" % self.disk_info[
                    each]
                response = self.azure_session.delete(azure_datadiskurl, headers=self.default_headers,
                                                     verify=False)

                if response.status_code == 202:
                    self.log.info('Disk %s found and deleting' % each)

                elif response.status_code == 404:
                    self.log.info('Disk %s not found' % each)

                elif response.status_code == 204:
                    self.log.info('Disk %s not found' % each)

                else:
                    self.log.error('Azure response [{0}] Status code [{1}]'.format(
                        response.text, response.status_code))
                    raise Exception("Disk %s cannot be deleted" % each)

        else:
            # deleting unmanaged disks or blobs
            storage_request = self.azure_session.post(
                "https://login.microsoftonline.com/%s/oauth2/token" % self.tenant_id,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=self.storage_data)
            if storage_request.status_code == 200:
                self.xmsdate = storage_request.headers["Date"]
                self.storage_token = storage_request.json()['access_token']

                for each in self.disk_info:
                    if skip_os_disk and each == 'OsDisk':
                        self.log.info("Skipping deletion os Os Disk")
                        continue
                    response = self.azure_session.delete(self.disk_info[each],
                                                         headers=self.storage_headers)
                    if response.status_code == 202:
                        self.log.info('Disk %s found and deleting' % each)
                    elif response.status_code == 404:
                        self.log.info('Disk %s not found' % each)
                    elif response.status_code == 204:
                        self.log.info('Disk %s not found' % each)
                    else:
                        self.log.error('Azure response [{0}] Status code [{1}]'.format(
                            response.text, response.status_code))
                        raise Exception("Disk %s cannot be deleted" % each)

            else:
                self.log.info('Error in getting authorization token: %s' % json.loads(storage_request.text)[
                    "error_description"])

    def clean_up_snapshots(self, start_time=None):
        """ clean up snapshots on disks of vm from start time to present
        Args:
            start_time(str): GMT in format "yyyy-mm-ddthh mm ss" if not specified
                        all linked snapshots are cleaned up

        Returns:

        """
        try:
            if start_time:
                start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if self.managed_disk:
                snapshots = self.get_disk_snapshots()

                for each_disk in snapshots:
                    if snapshots[each_disk]:
                        for snap in snapshots[each_disk]:
                            if start_time:
                                snap_time = datetime.datetime.strptime(snap['timeCreated'], '%Y-%m-%d %H:%M:%S')
                                if snap_time <= start_time:
                                    continue
                            azure_snapurl = AZURE_RESOURCE_MANAGER_URL + "%s?api-version=2020-06-30" % snap['id']
                            response = self.azure_session.delete(azure_snapurl, headers=self.default_headers,
                                                                 verify=False)

                            if response.status_code not in [202, 200, 204, 404]:
                                self.log.warning("Soft Error : Snapshot %s cannot be deleted" % snap['id'])
                            self.log.info("Snapshot %s  deleted" % snap['id'])
            else:
                snapshots_info = self.get_snapshotsonblobs(get_all_details=True)
                disk_urls = self.get_bloburi()
                for disk in snapshots_info:
                    if snapshots_info[disk]:
                        for snapshot in snapshots_info[disk]:
                            if start_time:
                                stamp = snapshot['Snapshot']
                                timestamp = stamp.split('T')[0] + " " + stamp.split('T')[1].split('.')[0]
                                snap_time = datetime.datetime.strptime(timestamp,
                                                                       '%Y-%m-%d %H:%M:%S')
                                if snap_time <= start_time:
                                    continue
                            snapshot_url = disk_urls[disk] + "?snapshot=" + snapshot['Snapshot']
                            response = self.azure_session.delete(snapshot_url,
                                                                 headers=self.get_storage_header('2020-02-10'))
                            if response.status_code not in [202, 200, 204, 404]:
                                self.log.warning("Soft Error : Snapshot %s cannot be deleted" % snapshot_url)
                            self.log.info("Deleted Snapshot %s deleted" % snapshot_url)

        except Exception as exp:
            self.log.warning("Snapshot cleanup was not successful : %s", exp)

    def get_vm_location(self, resource_group, restored_vm_name):
        """
                Get location of out of place restored VM

                Raises:
                    Exception:
                        When getting response failed or unexpected error code is returned

                Returns:

                    vm location: string

                """
        try:

            self.api_version = "?api-version=2018-10-01"
            azure_restored_vmurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                                   "/%s/providers/Microsoft.Compute/virtualMachines" \
                                   "/%s" % (self.subscription_id, resource_group, restored_vm_name)
            vm_infourl = azure_restored_vmurl + self.api_version
            response = self.azure_session.get(vm_infourl, headers=self.default_headers, verify=False)
            data = response.json()
            return data['location']

        except Exception as exp:
            self.log.exception("Exception in getting restored VM location")
            raise Exception("Exception in getting restored VM location:" + str(exp))

    def clean_up(self, clean_up_disk=True):
        """
        Clean up the VM and ts reources.
        Args:
            clean_up_disk(bool) : Set to false to not delete associated vm disks
                                  default: True
        Raises:
            Exception:
                When cleanup failed or unexpected error code is returned
        """
        try:
            data = self.vm_info
            self.api_version = "?api-version=2018-10-01"
            vm_deleteurl = self.azure_vmurl + self.api_version
            response = self.azure_session.delete(vm_deleteurl, headers=self.default_headers, verify=False)
            if response.status_code == 202:
                self.log.info('VM found and deleting')
                time.sleep(360)
                response = self.azure_session.delete(vm_deleteurl, headers=self.default_headers, verify=False)
                if response.status_code == 204:
                    self.log.info("VM deleted")
            elif response.status_code == 204:
                self.log.info('VM not found')
            elif response.status_code == 404:
                self.log.info('Resource group not found')
            else:
                self.log.error('Azure response [{0}] Status code [{1}]'.format(
                    response.text, response.status_code))
                raise Exception("VM cannot be deleted")
            self.clean_up_network()
            if clean_up_disk:
                os_disk_details = data["properties"]["storageProfile"]["osDisk"]
                self.clean_up_disk(os_disk_details)

        except Exception as exp:
            self.log.exception("Exception in Clenaup")
            raise Exception("Exception in Cleanup:" + str(exp))

    def _get_vm_info(self):
        """
        Get all VM information

        Raises:
            Exception:
                if failed to get information about VM
        """
        try:
            self.log.info(f"Fetching VM info for {self.vm_name}")
            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                self.api_version = "?api-version=2024-03-01"

            vm_infourl = self.azure_vmurl + self.api_version
            response = self.azure_session.get(vm_infourl, headers=self.default_headers, verify=False)
            data = response.json()

            if response.status_code == 200:
                self.vm_info = data

            elif response.status_code == 404:
                self.vm_info = False
                self.log.info("No VMs found")
                # No VMs found

            else:
                self.log.error('Azure response [{0}] Status code [{1}]'.format(
                    response.text, response.status_code))
                raise Exception("VM  data cannot be collected")

        except Exception as err:
            self.log.exception("Exception in get_vm_info")
            raise Exception(err)

    def get_disks_by_repository(self, storage_acc):
        """
        Get Disks by Storage Account [for unmanaged fetching the storage account from blob uri]

        Args:
            storage_acc (str) : Account for which disks are to fetched

        Returns:
            A list of disks in the specified storage account

        Raises:
            Exception
                When issues while getting disks in the given storage account
        """
        try:
            self.log.info("Filtering disks by Storage Account")
            _disk_in_sa = []
            if not self.managed_disk:
                blob_details = self.get_bloburi()
                for disk, blob in blob_details.items():
                    if blob.partition('//')[2].split('.')[0] == storage_acc:
                        if disk in self.disk_dict.get('OsDisk'):
                            self.log.info("Disk Filtered is : {0}".format(disk))
                            _disk_in_sa.append('OsDisk')
                        else:
                            disk_name = [disk for disk, blob_uri in self.disk_dict.items() if blob_uri == blob]
                            self.log.info("Disk Filtered is : {0}".format(disk_name))
                            _disk_in_sa.append(disk_name[0])
            return _disk_in_sa
        except Exception as err:
            self.log.exception("Exception in get_disks_by_repository : {0}".format(err))
            raise Exception(err)

    def get_disk_path_from_pattern(self, disk_pattern):
        """
        Find the disk that matches the disk pattern form disk list

        Args:
                disk_pattern            (str):  pattern which needs to be matched

        Returns:
                matched_disks              (str):  the disk that matches the pattern

        Raises:
            Exception:
                When issues while getting disk path from the pattern passed
        """
        try:
            self.log.info("Filtering disks by Pattern")
            _disk_name = os.path.basename(disk_pattern)
            matched_disks = []

            for each_disk in self.disk_dict:
                _vm_disk_name = os.path.basename(self.disk_dict[each_disk])
                if re.match(_disk_name, _vm_disk_name):
                    self.log.info("Disk Filtered is : {0}".format(_disk_name))
                    matched_disks.append(each_disk)
            return matched_disks

        except Exception as err:
            self.log.exception("Exception in get_disk_path_from_pattern : {0}".format(err))
            raise Exception(err)

    def get_datastore_uri_by_pattern(self, blob_uri_pattern):
        """
        Find the disk that matches the blob uri pattern form disk list

        Args:
                blob_uri_pattern            (str):  pattern which needs to be matched

        Returns:
                matched_disks              (str):  the disk that matches the pattern

        Raises:
            Exception:
                When issues while getting disk path from the pattern passed
        """
        try:
            self.log.info("Filtering disks by Blob URI")
            matched_disks = []
            if not self.managed_disk:
                blob_details = self.get_bloburi()
                for disk, blob in blob_details.items():
                    if re.match(blob_uri_pattern, blob):
                        disk_name = [disk for disk, blob_uri in self.disk_dict.items() if blob_uri == blob]
                        self.log.info("Disk Filtered is : {0}".format(disk_name))
                        matched_disks.append(disk_name[0])
            return matched_disks

        except Exception as err:
            self.log.exception("Exception in get_datastore_uri_by_pattern : {0}".format(err))
            raise Exception(err)

    def get_disks_by_tag(self, tag_name, tag_value):
        """
        Filter disk by tag name and value

        Args:
            tag_name (str) : tag name to be searched
            tag_value (str) : tag value for tag name

        Returns:
                matched_disks (str):  the disk that matches the tag name and value

        Raises:
            Exception:
                When issues while getting disk from the tag and value passed
        """
        try:
            self.log.info("Filtering disks by Tag")
            matched_disks = []
            tag_dict = {}
            for disk_name, disk_val in self.disk_dict.items():
                if self.managed_disk:
                    tag_dict = self.get_tag_for_disk(disk_name)
                else:
                    tag_dict = self.get_metadata_for_disk(disk_val)
                if tag_dict:
                    for tag, value in tag_dict.items():
                        if tag == tag_name and value == tag_value:
                            self.log.info("Disk Filtered is : {0}".format(disk_name))
                            matched_disks.append(disk_name)
            return matched_disks
        except Exception as err:
            self.log.exception("Exception in get_disks_by_tag : {0}".format(err))
            raise Exception(err)

    def _get_disks_by_os_type(self):
        """
        Find the disk that matches the disk type

        Returns:
                matched_disks       (str):  the disk that matches the disk_type

        Raises:
            Exception:
                When issues while getting disk path from the disk type passed
        """
        try:
            self.log.info("Filtering disks by Os Type")
            matched_disks = []
            for disk in self.disk_dict.keys():
                if disk == 'OsDisk':
                    matched_disks.append(disk)
            return matched_disks

        except Exception as err:
            self.log.exception("Exception in get_disks_by_os_type : {0}".format(err))
            raise Exception(err)

    def get_vm_architecture(self):
        """ Retrieves the CPU architecture type of the virtual machine"""
        sku_url = AZURE_RESOURCE_MANAGER_URL + ("/subscriptions/%s/providers/Microsoft.Compute/"
                                                "skus?api-version=2021-07-01"
                                                "&$filter=location eq '%s'") % (self.subscription_id, self.region)
        response = self.azure_session.get(sku_url, headers=self.default_headers, verify=False)
        if response.status_code == 200:
            data = response.json()
            for entry in data['value']:
                if entry.get("resourceType", "") == "virtualMachines" and entry.get("name", "") == self.vm_size:
                    for capabilities in entry.get("capabilities", []):
                        if capabilities.get("name", "") == "CpuArchitectureType":
                            self.vm_architecture = capabilities.get("value")
                            return self.vm_architecture
        self.log.warning("Unable to get vm architecture")

    def get_os_image_reference_info(self):
        """Extracts and stores the OS image reference information from the VM information."""
        self.os_image_info = self.vm_info.get("properties"). \
            get("storageProfile", {}).get("imageReference", {})

    def get_vm_security_profile_info(self):
        """ Extracts and stores the VM security profile information from the VM information."""
        security_profile = self.vm_info.get("properties", {}).get("securityProfile", {})
        self.security_profile_info = {"Type": security_profile.get("securityType", "Standard"),
                                      "secureBootEnabled": security_profile.get("uefiSettings", {}) \
                                          .get("secureBootEnabled", False),
                                      "vTpmEnabled": security_profile.get("uefiSettings", {}) \
                                          .get("vTpmEnabled", False)}

    def get_vm_extensions(self):
        """Extracts and stores the VM extensions information from the VM information."""
        resources = self.vm_info.get("resources", [])
        self.extensions = [resource for resource in resources if resource.get("type", "") ==
                           "Microsoft.Compute/virtualMachines/extensions"]

    def get_auto_vm_config(self):
        """Gets the vm configurations"""
        try:
            auto_vm_config = dict()
            # vm encryption info
            auto_vm_config['vm_encryption_info'] = self.encryption_info
            # Tags
            auto_vm_config["tags"] = {"vm": self.tags}
            auto_vm_config["tags"]["disk"] = {"all": False, "tags_set": False}
            auto_vm_config["tags"]["disk"]["tags_set"] = \
                True if len([disk for disk, info in self.disk_sku_dict.items() if info["tags"]]) >= 1 else False
            auto_vm_config["tags"]["disk"]["all"] = \
                True if len([disk for disk, info in self.disk_sku_dict.items() if info["tags"]]) == self.disk_count else False


            auto_vm_config["tags"]["nic"] = [item.get('tags') for item in self.nic_details][0]

            auto_vm_config["availability_zone"] = self.availability_zone
            # DES
            auto_vm_config["disk_encryption_type"] = {}
            if self.managed_disk:
                for disk in self.disk_encryption_info:
                    auto_vm_config["disk_encryption_type"][disk] = self.disk_encryption_info[disk].get("type", None)
            # PPG
            auto_vm_config["proximity_placement_groups"] = self.proximity_placement_group
            auto_vm_config['generation'] = self.get_vm_generation()
            auto_vm_config["identity"] = self.vm_info.get("identity", {}).get("type", "")
            self.auto_vm_config = auto_vm_config
        except Exception as err:
            self.log.exception("Exception in getting vm configuration details : {0}".format(err))
            raise Exception(err)

    def get_disk_encryption_info(self):
        """Gets encryption info for each disk of managed VM"""
        try:
            if self.managed_disk:
                for disk, disk_id in self.disk_dict.items():
                    encryption_info = self.hvobj.execute_api(
                        'GET', disk_id[1:], self.default_headers)[0]["properties"]["encryption"]
                    self.disk_encryption_info[disk] = encryption_info

        except Exception as err:
            self.log.exception("Exception in getting disk encryption information : {0}".format(err))
            raise Exception(err)

    def get_metadata_for_disk(self, disk_blob):
        """
        Returns the metadata dictionary for the disk
        Args:
            disk_blob (str) : disk name for which metadat are to be fetched

        Returns:
             metadata dictionary with metadata for the disk

        Raises
            Exception:
                    When error in getting metadat for disk
        """
        try:
            header = self.get_storage_header('2019-07-07')
            uri = ""
            metadata_dict = {}
            uri = uri + disk_blob + '?comp=metadata'
            response = self.azure_session.get(uri, headers=header, verify=False)
            if response.status_code == 200:
                headers = response.headers
                for key, val in headers.items():
                    if 'x-ms-meta' in key:
                        metadata_dict[key.split('-')[-1]] = val
            return metadata_dict
        except Exception as err:
            self.log.exception("Exception in get metadata method")
            raise Exception(err)

    def get_tag_for_disk(self, disk_name):
        """
        Returns the tag dictionary for the disk

        Args:
            disk_name (str) : disk name for which tags are to be fetched

        Returns:
             tag dictionary with tags for the disk

        Raises
            Exception:
                    When error in getting tags for disk
        """
        try:
            tag_dict = {}
            if disk_name != 'OsDisk':
                if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                    self.api_version = "?api-version=2019-07-01"
                disk_url = self.azure_diskurl + disk_name + self.api_version
                response = self.azure_session.get(disk_url, headers=self.default_headers,
                                                  verify=False)
                data = response.json()
                tag_dict = {}

                if response.status_code == 200:
                    tag_dict = data.get('tags', {})

                elif response.status_code == 404:
                    self.log.info("There was No VM in Name %s , please check the VM name")

            return tag_dict

        except Exception as err:
            self.log.exception("Exception in get tag details")
            raise Exception(err)

    def get_tag_for_disk_by_id(self, disk_id):
        """
        Returns the tag dictionary of tags for the disk

        Args:
            disk_id (string) : Azure resource ID for the disk for which tags are to be fetched

        Returns:
             tag dictionary with tags for the disk

        Raises
            Exception:
                    When error in getting tags for disk
        """
        try:
            tag_dict = {}
            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                self.api_version = "?api-version=2019-07-01"
            disk_url = AZURE_RESOURCE_MANAGER_URL + disk_id + self.api_version
            response = self.azure_session.get(disk_url, headers=self.default_headers,
                                              verify=False)
            data = response.json()
            tag_dict = {}

            if response.status_code == 200:
                tag_dict = data.get('tags', {})

            elif response.status_code == 404:
                self.log.info("Disk not found, please check the disk with ID: {}".format(disk_id))

            return tag_dict

        except Exception as err:
            self.log.exception("Exception in get tag details")
            raise Exception(err)

    def get_storage_header(self, xmsversion):
        """
        Gets the storage header
        Args:
            xmsversion: x-ms-version

        Returns: header

        """
        self.storage_access_token = self.hvobj.storage_access_token

        curr_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.gmtime())
        curr_time = curr_time + 'GMT'
        header = {
            'Authorization': 'Bearer ' + self.storage_access_token,
            'x-ms-version': xmsversion,
            'Date': curr_time}
        return header

    def check_snapshot_bymetadta_forjob(self, metadata):
        """ Checks if the snapshot exist on vm for the Job
        args:
           metadata (list) : lsit of metadata from db query

        return:
            (bool) : true if snapshot exist else false
        """

        self.log.info("checking snapshots from db")
        self.get_vm_guid()
        job_metadata_forvm = None
        if metadata[0] != '':
            for entry in metadata:
                if self.guid == entry[0]:
                    job_metadata_forvm = entry[1]
        if not job_metadata_forvm:
            return False
        snapshots = eval(job_metadata_forvm.split('|')[8])
        if self.managed_disk:
            for snapshot in snapshots['listManagedSnapshotIDs']:
                if not self.check_disksnapshot_byid(snapshot):
                    return False
        else:
            for snapshot in snapshots['listBlobSnapshotURIs']:
                if not self.check_blobsnapshot_byurl(snapshot):
                    return False
        return True

    def validate_disk_encryption(self, source_vm, dest_vm, method, restore_options, **kwargs):
        if not dest_vm.managed_disk:
            self.log.info("Unmanaged disk skipping disk encryption validation")
            return True
        encryption_types = {
            "(Default) Encryption at-rest with a platform-managed key": "EncryptionAtRestWithPlatformKey",
            "Encryption at-rest with a customer-managed key": "EncryptionAtRestWithCustomerKey",
            "Double encryption with platform-managed and customer-managed keys": "EncryptionAtRestWithPlatformAndCustomerKeys"
        }
        if method == "Full VM Restore":
            if restore_options.in_place or not restore_options.disk_encryption_type or restore_options.disk_encryption_type == "Original":
                for lun_id in source_vm.disk_sku_dict:
                    source_disk_encryption_type = \
                    source_vm.disk_encryption_info.get(source_vm.disk_sku_dict[lun_id].get("name"))['type']
                    dest_disk_encryption_type = \
                    dest_vm.disk_encryption_info.get(dest_vm.disk_sku_dict[lun_id].get("name"))['type']
                    if source_disk_encryption_type != dest_disk_encryption_type:
                        self.log.info(
                            f"disk encryption validation failed. Source type: {source_disk_encryption_type}"
                            f" destination type {dest_disk_encryption_type}")
                        return False
                self.log.info("Disk encryption validation passed")
                return True
            else:
                for disk, value in dest_vm.disk_encryption_info.items():
                    if value["type"] != encryption_types.get(restore_options.disk_encryption_type,
                                                             restore_options.disk_encryption_type):
                        self.log.info(
                            f"disk encryption validation failed. Encryption {value['type']} found but {restore_options.disk_encryption_type} was expected")
                        return False
            self.log.info("Disk encryption validation passed")
            return True
        elif method == "Conversion":
            expected_encryption = encryption_types.get(restore_options.disk_encryption_type,
                                                       restore_options.disk_encryption_type) \
                if restore_options.disk_encryption_type \
                else "EncryptionAtRestWithPlatformKey"
            if expected_encryption == "Original":
                expected_encryption = "EncryptionAtRestWithPlatformKey"
            for disk, value in dest_vm.disk_encryption_info.items():
                if value["type"] != expected_encryption:
                    self.log.info(
                        f"disk encryption validation failed. Encryption {value['type']} found but {expected_encryption} was expected")
                    return False
            self.log.info("Disk encryption validation passed")
            return True
        self.log.info("Disk encryption validation not performed")
        return False

    def validate_sku(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the sku type of the destination

           Args:

                source_vm  (object) : Source vm object
                dest_vm     (object) : destination VM object
                method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                restore_options  (object) : object of vm restore options or Live Sync schedule object

            Returns:
                If destination VM'S sku is not as expected
        """
        if method == "Full VM Restore" or method == "Conversion":
            if source_vm.managed_disk:
                disk_sku_names = {
                    "Standard HDD": "Standard_LRS",
                    "Standard SSD": "StandardSSD_LRS",
                    "Premium SSD": "Premium_LRS"
                }
                for lun, details in dest_vm.disk_sku_dict.items():
                    if restore_options.in_place or restore_options.disk_option == 'Original' and method != "Conversion":
                        storage_account_type = source_vm.disk_sku_dict[lun]['storageAccountType']
                    elif method == "conversion" and restore_options.disk_option == 'Original':
                        storage_account_type = disk_sku_names["Standard HDD"]
                    else:
                        storage_account_type = disk_sku_names[restore_options.disk_option]

                    if not details['storageAccountType'] == storage_account_type:
                        self.log.info("Storage Account of restored  disk not as expected.")
                        return False
            self.log.info("Storage Type Verification of Restored VM disk passed.")
            return True
        self.log.info("Storage Type Verification of Restored VM disk not performed.")
        return False

    def tags_validation(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the tags of vm are restored correctly
            Args:
                source_vm  (object) : Source vm object
                dest_vm     (object) : destination VM object
                method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                restore_options  (object) : object of vm restore options
            Returns:
                True if vm and disk tags are same at source and destination vm
        """
        if method == "Full VM Restore":
            vm_tag_check = True
            disk_tag_check = True
            nic_tag_check = True

            self.log.info('Checking VM Tags')
            source_vm.tags = VirtualServerConstants.filter_cv_tags(source_vm.tags)
            # self.log.info('Source VM Tags: {0}'.format(source_vm.tags))
            # self.log.info('Destination VM Tags: {0}'.format(dest_vm.tags))
            commvault_tag_names = {'Last Backup'}
            source_vm_tag_names = set(source_vm.tags) - commvault_tag_names
            dest_vm_tag_names = set(dest_vm.tags) - commvault_tag_names

            if source_vm_tag_names == dest_vm_tag_names:
                for tag_name in source_vm_tag_names:
                    if source_vm.tags[tag_name] != dest_vm.tags[tag_name]:
                        vm_tag_check = False
                        break
            else:
                vm_tag_check = False

            self.log.info('VM Tags Validation Successful') if vm_tag_check \
                else self.log.info('VM Tags Validation Failed')

            if source_vm.managed_disk:
                self.log.info('Checking Disk Tags')

                source_disk_tags_dict = {disk["name"]: disk["tags"] for disk in source_vm.disk_sku_dict.values()}
                dest_disk_tags_dict = {disk["name"]: disk["tags"] for disk in dest_vm.disk_sku_dict.values()}

                if len(source_disk_tags_dict) == len(dest_disk_tags_dict):
                    for source_disk, dest_disk in zip(source_disk_tags_dict.items(), dest_disk_tags_dict.items()):
                        source_disk_name, source_disk_tags = source_disk
                        dest_disk_name, dest_disk_tags = dest_disk

                        self.log.info(f"Checking Disk {dest_disk_name} against Disk {source_disk_name}")

                        source_disk_tags = VirtualServerConstants.filter_cv_tags(source_disk_tags)
                        dest_disk_tags = VirtualServerConstants.filter_cv_tags(dest_disk_tags)

                        if source_disk_tags == dest_disk_tags:
                            self.log.info(f"Disk Tags Validation Successful for Disk {dest_disk_name}")
                        else:
                            disk_tag_check = False
                            self.log.info(f"Disk Tags Validation Failed for Disk {dest_disk_name}. Tags are not equal")
                            source_disk_tags_set = set(source_disk_tags.items())
                            dest_disk_tags_set = set(dest_disk_tags.items())
                            self.log.info(
                                f"Source Disk Tags Set Difference: {source_disk_tags_set - dest_disk_tags_set}")
                            self.log.info(
                                f"Destination Disk Tags Set Difference: {dest_disk_tags_set - source_disk_tags_set}")

                    if disk_tag_check:
                        self.log.info("Disk Tags Validation Successful")
                    else:
                        self.log.info("Disk Tags Validation Failed")
                else:
                    disk_tag_check = False
                    self.log.info('Disk Tag Validation Failed. Kindly Check Number of Disks Restored')
            else:
                self.log.info('Skipping Disk Tag Validation as Source Disk Type is Unmanaged')
                disk_tag_check = True

            self.log.info('Checking NIC Tags')
            source_nic_tags_dict = [a.get('tags') for a in source_vm.nic_details]
            dest_nic_tags_dict = [a.get('tags') for a in dest_vm.nic_details]
            source_nic_tags_dict = list(map(VirtualServerConstants.filter_cv_tags, source_nic_tags_dict))
            dest_nic_tags_dict = list(map(VirtualServerConstants.filter_cv_tags, dest_nic_tags_dict))
            if source_nic_tags_dict == dest_nic_tags_dict:
                self.log.info('NIC Tags Validation Successful')
                nic_tag_check = True
            else:
                self.log.info('NIC Tags Validation Failed')
                nic_tag_check = False

            return vm_tag_check and disk_tag_check and nic_tag_check

        if method == "Conversion":
            if not self.vm_validate_conv_tags(dest_vm, restore_options):
                self.log.error("VM Tag validation failed")
                return False
            self.log.info("VM Tag validation successful.")
            return True

        self.log.error("Tags validation not performed")
        return False

    def validate_vm_guid(self, source_vm, dest_vm, method, restore_options, **kwargs):
        self.log.info("Validating VMId")
        if method == "Full VM Restore":
            if restore_options.in_place_overwrite and restore_options.is_patch_restore:
                if source_vm.guid == dest_vm.guid:
                    self.log.info("VMId validation passed")
                    return True
                else:
                    self.log.info(
                        f"VMId validation failed. Source VM GUID : {source_vm.guid}, Destination VM {dest_vm.guid}")
                    return False
        self.log.info("VMId validation passed")
        return True

    def validate_vm_extensions(self, source_vm, dest_vm, method, restore_options, **kwargs):
        if method == "Full VM Restore":
            if source_vm.extensions and dest_vm.extensions:
                for idx in range(len(source_vm.extensions)):
                    if source_vm.extensions[idx]["name"] == dest_vm.extensions[idx]["name"]:
                        self.log.info("VM Extensions validation passed")

                    else:
                        self.log.info(
                            f"Extensions validation failed. Source VM Extensions : {source_vm.extensions}, Destination VM Extensions {dest_vm.extensions}")
                        return False
                self.log.info("VM Extensions validation passed")
                return True
            else:
                self.log.info("Skipping VM Extensions validation as method is not Full VM restore")

    def validate_proximity_placement_group(self, source_vm, dest_vm, method, restore_options, **kwargs):
        if method == "Full VM Restore":
            self.log.info("Validating PPG")
            if source_vm.region == dest_vm.region:
                if source_vm.proximity_placement_group == dest_vm.proximity_placement_group:
                    self.log.info('Source Vm PPG {0} \n Destination VM PPG {1}'.format(
                        source_vm.proximity_placement_group, dest_vm.proximity_placement_group))
                    return True
            else:
                if not dest_vm.proximity_placement_group:
                    return True
            self.log.error("PPG validation failed")
            return False
        elif method == "Conversion":
            self.log.warning("Proximity placement for conversion not implemented")
            return True
        self.log.error("Proximity Placement Group validation not performed.")
        return False

    def validate_availability_zone_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """
            Performs restore validation for availability zone

            Args:
                source_vm  (object) : vm object for which destination vm has to be validated
                dest_vm     (object) : destination VM object
                method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                restore_options  (object) : object of vm restore options

            Returns (bool):
                True if validation succeeded for Availability Zone else False

            Raises:
                Exception:
                    if there is any exception in setting the restore options
        """
        expected_zone = restore_options.availability_zone
        actual_zone = dest_vm.availability_zone

        if method == "Full VM Restore":
            if restore_options.in_place or expected_zone == 'Auto':
                if source_vm.availability_zone != actual_zone:
                    self.log.info(
                        f"Availability Zone validation failed. Expected zone: {source_vm.availability_zone}, Actual zone: {actual_zone}")
                    return False
            elif not expected_zone or expected_zone == 'None':
                if actual_zone != 'None':
                    self.log.info(
                        f"Availability Zone validation failed. Expected zone: {expected_zone}, Actual zone: {actual_zone}")
                    return False
            else:
                if int(actual_zone) != int(expected_zone):
                    self.log.info(
                        f"Availability Zone validation failed. Expected zone: {expected_zone}, Actual zone: {actual_zone}")
                    return False
            self.log.info("Availability Zone validation successful.")
            return True
        elif method == "Conversion":
            if not expected_zone or expected_zone in ["None", "Auto"]:
                if actual_zone != 'None':
                    self.log.info(
                        f"Availability Zone validation failed. Expected zone: {expected_zone}, Actual zone: {actual_zone}")
                    return False
            else:
                if str(actual_zone) != str(expected_zone):
                    self.log.info(
                        f"Availability Zone validation failed. Expected zone: {expected_zone}, Actual zone: {actual_zone}")
                    return False
            self.log.info("Availability Zone validation successful.")
            return True
        else:
            self.log.error("Availability zone validation not performed")
            return False

    def validate_vm_encryption(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the destination VM has proper ADE encryption setting as src

            Args:
                source_vm  (object) : Source vm object
                dest_vm     (object) : destination VM object
                method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                restore_options  (object) : object of vm restore options

            Returns:
                If destination VM'S encryption is not as expected
        """
        if method == "Full VM Restore":
            if source_vm.is_encrypted:
                if not dest_vm.is_encrypted:
                    self.log.error("Destination VM not encrypted but source VM is encrypted")
                    return False
                required_keys = ["provisioningState", "typeHandlerVersion", "KeyEncryptionAlgorithm",
                                 "VolumeType", "encryptionKeyName"]

                if not dest_vm.is_encrypted:
                    self.log.info("Destination VM ADE Encryption was not applied successfully")
                    return False

                if restore_options.in_place or (
                        source_vm.encryption_info["location"] == dest_vm.encryption_info["location"] and \
                        not restore_options.azure_key_vault):
                    if not source_vm.encryption_info["keyVaultName"] == dest_vm.encryption_info["keyVaultName"]:
                        self.log.info("Restored VM Encryption Key Vault: {} mismatch with Source: {}".format(
                            source_vm.encryption_info["keyVaultName"], dest_vm.encryption_info["keyVaultName"]))
                        return False
                if (not restore_options.azure_key_vault and source_vm.encryption_info["KekVaultResourceId"]
                        != dest_vm.encryption_info["KekVaultResourceId"]):
                    self.log.info("Restored VM Encryption Key Vault URI: {} mismatch with Source URI: {}".format(
                        source_vm.encryption_info["KekVaultResourceId"], dest_vm.encryption_info["KekVaultResourceId"]))
                    return False
                elif restore_options.azure_key_vault:
                    if source_vm.encryption_info["keyVaultName"] != restore_options.azure_key_vault.split("/")[
                        -1] or \
                            restore_options.azure_key_vault not in dest_vm.encryption_info["KeyVaultResourceId"]:
                        self.log.info(
                            f"Restored VM Encryption Key Vault: {dest_vm.encryption_info['keyVaultName']}"
                            f"does not match selected Key Vault: {restore_options.azure_key_vault}")
                        return False
                res = set(
                    map(lambda key: source_vm.encryption_info[key] == dest_vm.encryption_info[key], required_keys))

                if not (len(res) == 1 and res.pop()):
                    self.log.info("Destination VM encryption ADE not as expected to source")
                    return False
            self.log.info("VM Encryption validation passed.")
            return True
        if method == "Conversion":
            self.log.info("VM encryption validation for conversion not Required")
            return True

        self.log.error("VM Encryption validation is not performed")
        return False

    def check_disksnapshot_byid(self, snapshot_id):
        """ checks if the snapshot on disk exist
        args:
            snapshot_id  (str): id to for snapshot to be checked
        Return :
                (bool) : True if snapshot exist else false
        """
        try:
            azure_url = AZURE_RESOURCE_MANAGER_URL
            snapshot_url = azure_url + snapshot_id + "?api-version=2019-07-01"
            response = self.azure_session.get(snapshot_url, headers=self.default_headers, verify=False)
            if response.status_code == 200:
                return True
            if response.status_code in [204, 404]:
                return False
            else:
                raise Exception("Exception in checking snapshot existence response was not success")
        except Exception as err:
            raise Exception("Exception in checking snapshot existence " + str(err))

    def check_blobsnapshot_byurl(self, snapshot_url):
        """ checks if the snapshot on disk exist
                args:
                    snapshot_id  (str): id to for snapshot to be checked
                Return :
                        (bool) : True if snapshot exist else false
                """
        try:
            header = self.get_storage_header("2017-11-09")
            snapshot_url = snapshot_url.split("?")[0] + "?comp=metadata&" + snapshot_url.split("?")[1]
            response = self.azure_session.get(snapshot_url, headers=header, verify=False)
            if response.status_code == 200:
                return True
            if response.status_code in [204, 404]:
                return False
            else:
                raise Exception("Exception in checking snapshot existence response was not success")
        except Exception as err:
            raise Exception("Exception in checking snapshot existence " + str(err))

    def validate_size_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the destination vm in has the same vm size as mentioned in schedule

                Args:
                    source_vm  (object) : Source vm object
                    dest_vm     (object) : destination VM object
                    method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                    restore_options  (object) : object of vm restore options or Live Sync schedule object
                Returns:
                    If destination VM has vmsize as in schedule else false

               """
        if method == "Live Sync":
            vmdeatils = restore_options.virtualServerRstOptions['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vm in vmdeatils:
                if vm['newName'] == dest_vm.vm_name:
                    if 'vmSize' in vm:
                        self.log.info(' Specified Size : {0}, Destination Size : {1}'.format(
                            str(vm['vmSize']), str(dest_vm.vm_size)))
                        if vm['vmSize'] and dest_vm.vm_size != vm['vmSize'].split(" ")[0]:
                            self.log.info('vmSize validation failed')
                            return False
                        return True
            self.log.error("Failing  validation as property is not populated in Task xml")
            return False
        elif method == "Full VM Restore":
            if restore_options.in_place or not restore_options.vm_size or restore_options.vm_size == "--Auto Select--":
                expected_size = source_vm.vm_size
            else:
                expected_size = restore_options.vm_size
            if dest_vm.vm_size != expected_size:
                self.log.info('VM Size validation failed. Expected Size : {0}, Destination Size : {1}'.format(
                    str(restore_options.vm_size), str(dest_vm.vm_size)))
                return False
            self.log.info("VM size validation passed.")
            return True

        elif method == "Conversion":
            if not restore_options.vm_size or restore_options.vm_size == "--Auto Select--":
                self.log.warning("Conversion vm size validation for auto-select not implemented")
            else:
                if dest_vm.vm_size != restore_options.vm_size:
                    self.log.info('VM Size validation failed. Expected Size : {0}, Destination Size : {1}'.format(
                        str(restore_options.vm_size), str(dest_vm.vm_size)))
                    return False
            self.log.info("VM size validation passed.")
            return True
        self.log.error("Vm size validation is not performed")
        return False

    def validate_disk_type_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """
        Checks if the disk typeof restored vm is as expected
        Args:
            source_vm  (object) : Source vm object
            dest_vm     (object) : destination VM object
            method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
            restore_options  (object) : object of vm restore options or Live Sync schedule object
        Returns:
            True if expected, otherwise False
        """
        if method == "Full VM Restore" or method == "Conversion":
            if restore_options.in_place:
                if dest_vm.managed_disk != source_vm.managed_disk:
                    self.log.info('Disk Type validation failed')
                    return False
            elif dest_vm.managed_disk != restore_options.restoreAsManagedVM:
                self.log.info('Disk Type validation failed')
                return False
            self.log.info("Disk Type validation passed.")
            return True
        elif method == "Live Sync":
            vm_details = restore_options.virtualServerRstOptions['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vm in vm_details:
                if vm['newName'] == dest_vm.vm_name:
                    if 'restoreAsManagedVM' in vm:
                        if vm['restoreAsManagedVM'] and not dest_vm.managed_disk:
                            self.log.info('Disk Type validation failed')
                            return False

                    return True
            self.log.error("Failing  validation as property is not populated in Task xml")
            return False
        self.log.error("Disk type validation is not performed.")
        return False

    def validate_storage_account_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the destination vm uses the same storage account as mentioned in schedule

               Args:
                    source_vm  (object) : Source vm object
                    dest_vm     (object) : destination VM object
                    method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                    restore_options  (object) : object of vm restore options or Live Sync schedule object


               returns     (bool): True If destination VM uses storage account as in schedule else false

        """

        if method == "Live Sync":
            vm_details = restore_options.virtualServerRstOptions['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vm in vm_details:
                if vm['name'] == self.vm_name:
                    if 'Datastore' in vm:
                        dest_stracc = None
                        bloburi = dest_vm.get_bloburi()
                        for disk in bloburi:
                            if bloburi[disk]:
                                dest_stracc = bloburi[disk].split('.')[0].split('//')[1]
                                break
                        if vm['Datastore'] != '' and vm['Datastore'] != dest_stracc:
                            self.log.info(
                                "Validation Failure : Storage Account mismatch Source : {0} Destination : {1}")
                            return False
            return True
        elif method == "Full VM Restore" or method == "Conversion":
            if not dest_vm.managed_disk:
                uri = dest_vm.vm_info['properties']['storageProfile']['osDisk']['vhd']['uri']
                dest_sa = uri.split('//')[1].partition('.')[0]
                if restore_options.in_place:
                    source_uri = source_vm.vm_info['properties']['storageProfile']['osDisk']['vhd']['uri']
                    source_sa = source_uri.split('//')[1].partition('.')[0]
                    if dest_sa != source_sa:
                        self.log.info(
                            'Storage Account validation failed. Expected SA : {0}, Actual SA : {1}'.format(
                                source_vm.restore_storage_acc, dest_sa))
                        return False
                    return True

                else:
                    if dest_sa != restore_options.Storage_account:
                        self.log.info(
                            'Storage Account validation failed. Expected SA : {0}, Actual SA : {1}'.format(
                                restore_options.Storage_account, dest_sa))
                        return False
            self.log.info("Storage Account validation successful.")
            return True

        self.log.error("Storage Account validation is not performed.")
        return False

    def check_snap_exist_intimeinterval(self, list_of_snapshots, start_time, end_time):
        """Checks if list of snapshot has snapshot created between start_time and end_time

        Args:
             list_of_snapshots   (list): list containing string of snapshot creation time

             start_time          (str): start time for interval between which snapshot existence  verified

             end_time           (str):  end time for interval between which snapshot existance has to be verified

        Returns                (bool): True if snapshot exist between time interval esle False

        """
        if not list_of_snapshots:
            return False
        elif len(list_of_snapshots) == 0:
            return False
        else:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            for snap in list_of_snapshots:
                snap_time = datetime.datetime.strptime(snap, '%Y-%m-%d %H:%M:%S')
                if start_time < snap_time < end_time:
                    self.log.info("Snapshot exists with creation"
                                  " time : {0}".format(snap))
                    return True
        return False

    def validate_generation_of_dest_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if destination vm and source vm have same generation

        args:
            source_vm  (object) : Source vm object
            dest_vm     (object) : destination VM object
            method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
            restore_options  (object) : object of vm restore options or Live Sync schedule object
        returns:
            Bool           : True if both source and destination vm have same generation
                            else false

        """
        try:
            if method == "Full VM Restore":
                if source_vm.get_vm_generation() != dest_vm.get_vm_generation():
                    return False
                self.log.info("VM generation validation successful.")
                return True
            elif method == "Conversion":
                if restore_options.source_client_hypervisor.instance_type.lower() \
                        == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                    prefix = restore_options.vm_restore_prefix
                    source_vm_name = dest_vm.vm_name.replace(prefix, '')
                    source_vm = restore_options.source_client_hypervisor.VMs[source_vm_name]
                    if not hasattr(source_vm, "Generation"):
                        source_vm._get_vm_info("Generation")
                    if source_vm.Generation != dest_vm.get_vm_generation()[-1]:
                        return False
                self.log.info("VM generation validation successful.")
                return True

            self.log.error("VM Generation not validated")
            return False
        except Exception as err:
            self.log.exception("Exception in Checking Vm Generation")
            raise Exception(err)

    def validate_region_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the destination vm is in region  as mentioned in schedule

               Args:
                    source_vm  (object) : Source vm object
                    dest_vm     (object) : destination VM object
                    method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                    restore_options  (object) : object of vm restore options or Live Sync schedule object

               returns     (bool): If destination VM has region as excepted

               """

        if method == "Live Sync":
            vm_details = restore_options.virtualServerRstOptions['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vm in vm_details:
                if vm['name'] == self.vm_name:
                    if 'datacenter' in vm:
                        if vm['datacenter'] and vm['datacenter'] != dest_vm.vm_info['location']:
                            return False
            return True
        elif method == "Full VM Restore" or method == "Conversion":
            if (restore_options.in_place or not restore_options.region) and method != "Conversion":
                if source_vm.vm_info['location'] != dest_vm.vm_info['location']:
                    self.log.info('Region validation failed. Expected region : {0}, Actual region : {1}'.format(
                        source_vm.vm_info['location'], dest_vm.vm_info['location']))
                    return False
            else:
                if dest_vm.vm_info['location'] != restore_options.region.replace(" ", "").lower():
                    self.log.info('Region validation failed. Expected region : {0}, Actual region : {1}'.format(
                        restore_options.region, dest_vm.vm_info['location']))
                    return False

            self.log.info("Region validation successful.")
            return True
        self.log.error("Region validation was not performed.")
        return False

    def validate_resource_group_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the destination vm is in resource group as mentioned in schedule
            Args:
                    source_vm  (object) : Source vm object
                    dest_vm     (object) : destination VM object
                    method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                    restore_options  (object) : object of vm restore options or Live Sync schedule object

            returns     (bool): If destination VM has region as in schedule else false

        """
        if method == "Full VM Restore" or method == "Conversion":
            if restore_options.in_place and dest_vm.resource_group_name != source_vm.resource_group_name:
                self.log.error(
                    f"Resource group validation for in-place restore failed. VM is restored to {dest_vm.resource_group_name}.")
                return False
            elif not restore_options.in_place and dest_vm.resource_group_name != restore_options.Resource_Group:
                self.log.error(f"Resource group validation failed. "
                               f"Specified RG : {restore_options.Resource_Group}, Actual RG: {dest_vm.resource_group_name}.")
                return False
            self.log.info("Resource group validation passed.")
            return True
        elif method == 'Live Sync':
            vm_details = restore_options.virtualServerRstOptions['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vm in vm_details:
                if vm['newName'] == dest_vm.vm_name:
                    if 'esxHost' in vm:
                        self.log.info('Specified RG : {0}, Actual RG : {1}'.format(vm['esxHost'],
                                                                                   dest_vm.resource_group_name))
                        if vm['esxHost'] and vm['esxHost'] != dest_vm.resource_group_name:
                            return False
                        return True
            self.log.error("Could validate resource group.")
            return False

        self.log.error("Resource Group validation is not performed")
        return False

    def validate_public_ip_config_of_destination_vm(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """Checks if the destination vm  has the public ip or not if   mentioned in schedule

                Args:
                    source_vm  (object) : Source vm object
                    dest_vm     (object) : destination VM object
                    method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
                    restore_options  (object) : object of vm restore options or Live Sync schedule object

                returns     (bool): If destination VM has publicip created if mentioned  in schedule else false

        """
        if method == 'Live Sync':
            vm_deatils = restore_options.virtualServerRstOptions['diskLevelVMRestoreOption']['advancedRestoreOptions']
            for vm in vm_deatils:
                if vm['newName'] == dest_vm.vm_name:
                    if "createPublicIP" in vm:
                        if vm["createPublicIP"] and not (dest_vm.get_publicipid()):
                            self.log.info('Public IP validation failed')
                            return False
                        return True
            self.log.error("Failing  validation as property is not populated in Task xml")
            return False
        elif method == "Full VM Restore" or method == "Conversion":
            if restore_options.in_place:
                if (source_vm.get_publicipid()) and not (dest_vm.get_publicipid()) or \
                        (dest_vm.get_publicipid()) and not (source_vm.get_publicipid()):
                    self.log.error('Public IP validation failed')
                    return False
            elif restore_options.createPublicIP:
                if not dest_vm.get_publicipid():
                    self.log.error('Public IP validation failed')
                    return False
            else:
                if dest_vm.get_publicipid():
                    self.log.error('Public IP validation failed')
                    return False
            self.log.info("Public IP configuration Successful.")
            return True
        self.log.error("Public IP configuration not validated")
        return False

    def validate_nsgs(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """
        Checks if the destination vm network interface is connected to the right NSG based on restore options

        Args:
            source_vm  (object) : Source vm object
            dest_vm     (object) : destination VM object
            method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
            restore_options  (object) : object of vm restore options or Live Sync schedule object

        returns  (bool): True If destination VM  is attached to right NSG specified else False
        """
        if restore_options.in_place:
            for source_nic in source_vm.nic_details:
                dest_nic = next((d for d in dest_vm.nic_details if d['name'] == source_nic['name']), None)
                if dest_nic and source_nic.get('nsg_uri', "") != dest_nic.get('nsg_uri', ""):
                    self.log.error(f"NSG validation for in-place restore failed. "
                                   f"Source NSG: {source_nic.get('nsg_uri', '')},"
                                   f" Destination NSG: {dest_nic.get('nsg_uri', '')}")
                    return False
            return True
        else:
            if not restore_options.security_groups or restore_options.security_groups == "None":
                for nic in dest_vm.nic_details:
                    if nic.get('nsg_uri', ""):
                        self.log.error(
                            f"NSG validation failed. Selected option"
                            f" 'None' but attached NSG: {nic.get('nsg_uri')}")
                        return False
            elif restore_options.security_groups == "--Auto Select--":
                if method == "Full VM restore" and source_vm.hvobj.subscription_id == dest_vm.hvobj.subscription_id and \
                        source_vm.region == dest_vm.region:
                    source_nsg = source_vm.nic_details[0].get('nsg_uri', "")
                    for dest_vm_nic in dest_vm.nic_details:
                        if dest_vm_nic.get("nsg_uri", "") != source_nsg:
                            self.log.error("NSG validation failed. Selected option."
                                           f"Expected NSG : {source_nsg}, Attached NSG :"
                                           f" {dest_vm_nic.get('nsg_uri', '')}")
                            return False

                else:
                    for nic in dest_vm.nic_details:
                        if nic.get('nsg_uri', ""):
                            self.log.error(
                                f"NSG validation failed. Selected option"
                                f" 'Auto-Select' but attached NSG: {nic.get('nsg_uri')}")
                            return False
            else:
                for nic in dest_vm.nic_details:
                    if nic.get('nsg_uri', "").split("/")[-1] != restore_options.security_groups:
                        self.log.error(
                            f"NSG validation failed. Expected NSG: {restore_options.security_groups}, "
                            f"but found NSG: {nic.get('nsg_uri', '').split('/')[-1]}")
                        return False
            self.log.info("NSG validation successful.")
            return True

        self.log.info("NSG validation not performed")
        return False

    def validate_vnet(self, source_vm, dest_vm, method, restore_options, **kwargs):
        """
        Checks if the destination vm is connected to the right vnet based on restore options

        Args:
            source_vm  (object) : Source vm object
            dest_vm     (object) : destination VM object
            method     (str): Type of restore being performed ("Full VM Restore", "Conversion", "Live Sync")
            restore_options  (object) : object of vm restore options
        returns  (bool): True If destination VM has is attached to right vnet specified else False
        """
        if restore_options.in_place:
            for source_nic in source_vm.nic_details:
                dest_nic = next((nic for nic in dest_vm.nic_details if nic['name'] == source_nic['name']), None)
                if dest_nic and source_nic.get('subnet_uri', "") != dest_nic.get('subnet_uri', ""):
                    self.log.error(f"Subnet validation for in-place restore failed. "
                                   f"Source subnet: {source_nic.get('subnet_uri', '')},"
                                   f" Destination subnet: {dest_nic.get('subnet_uri', '')}")
                    return False
            self.log.info("VNET validation successful.")
            return True
        else:
            if not restore_options.subnet_id or restore_options.subnet_id == "--Auto Select--":
                if method == "Full VM restore" and source_vm.hvobj.subscription_id == dest_vm.hvobj.subscription_id and \
                        source_vm.region == dest_vm.region:
                    source_vnet = source_vm.nic_details[0].get('subnet_uri')
                    for dest_vm_nic in dest_vm.nic_details:
                        if dest_vm_nic.get("subnet_uri", "") != source_vnet:
                            self.log.error(
                                f"Subnet validation for out-of-place restore failed for NIC '{dest_vm_nic['name']}'. "
                                f"Expected subnet: {source_vnet}, Actual subnet: {dest_vm_nic.get('subnet_uri', '')}")
                            return False
                else:
                    expected_vnet_id = dest_vm.hvobj.get_first_virtual_network_id_in_region(dest_vm.region)
                    for dest_vm_nic in dest_vm.nic_details:
                        if dest_vm_nic.get("subnet_uri") != expected_vnet_id:
                            self.log.error(
                                f"Subnet validation for out-of-place restore failed for NIC '{dest_vm_nic['name']}'. "
                                f"Expected subnet: {expected_vnet_id}, "
                                f"Actual subnet: {dest_vm_nic.get('subnet_uri', '')}")
                            return False
                self.log.info("VNET validation successful.")
                return True
            else:
                split_subnet_id = restore_options.subnet_id.split("/")
                if len(split_subnet_id) > 6:
                    expected_vnet = split_subnet_id[-3]
                    expected_subnet = split_subnet_id[-1]
                else:
                    expected_subnet = restore_options.subnet_id.split("\\")[-1]
                    expected_vnet = restore_options.subnet_id.split("\\")[-2]

                for dest_vm_nic in dest_vm.nic_details:
                    actual_vnet = dest_vm_nic.get('subnet_uri').split("/")[-3]
                    actual_subnet = dest_vm_nic.get('subnet_uri').split("/")[-1]

                    if expected_vnet != actual_vnet or expected_subnet != actual_subnet:
                        self.log.error(
                            f"Subnet validation for out-of-place restore failed for NIC '{dest_vm_nic['name']}'. "
                            f"Expected subnet: {expected_vnet + '/' + expected_subnet},"
                            f" Actual subnet: {actual_vnet + '/' + actual_subnet}")
                        return False
                self.log.info("VNET validation successful.")
                return True

            self.log.error("VNET validation is not performed.")
            return False

    def vm_validate_conv_tags(self, dest_vm, restore_options, **kwargs):
        """
        Args:
            other (obj): VmConversionValidation object to compare to
            source_hypervisor_type (string): the source hypervisor type

        Returns:
            true if tags of source vm and destination vm match
        """
        import copy
        if restore_options.source_client_hypervisor.instance_type.lower() != hypervisor_type.AMAZON_AWS.value.lower():
            return True
        prefix = restore_options.vm_restore_prefix
        source_vm_name = dest_vm.vm_name.replace(prefix, '')
        destination_vm_tags = copy.deepcopy(dest_vm.tags)
        source_vm_tags = {}
        for tag in restore_options.source_client_hypervisor.VMs[source_vm_name].tags:
            source_vm_tags[tag['Key']] = tag['Value']

        source_vm_tags = VirtualServerConstants.filter_cv_tags(source_vm_tags)
        config = (destination_vm_tags == source_vm_tags)
        return config and self.vm_validate_conv_disk_tags(dest_vm, restore_options)

    def vm_validate_conv_disk_tags(self, dest_vm, restore_options, **kwargs):

        """
        Args:
            other (obj): VmConversionValidation object to compare to

        Returns:
            true if tags of source disks and destination disks match
        """
        import copy
        prefix = restore_options.vm_restore_prefix
        source_vm_name = dest_vm.vm_name.replace(prefix, '')

        destination_disk_tags_list = copy.deepcopy(dest_vm.disk_tags)
        source_disk_tags_list = copy.deepcopy(
            restore_options.source_client_hypervisor.VMs[source_vm_name].volume_tags)

        if len(list(source_disk_tags_list)) == len(list(destination_disk_tags_list)):
            for disk_number in range(len(list(source_disk_tags_list))):
                destination_disk_tags = copy.deepcopy(list(destination_disk_tags_list.values())[disk_number])
                source_disk_tags = copy.deepcopy(list(source_disk_tags_list.values())[disk_number])
                source_disk_tags = VirtualServerConstants.filter_cv_tags(source_disk_tags)
                if source_disk_tags != destination_disk_tags:
                    return False
        else:
            return False

        return True

    def get_publicipid(self):
        """Gets ID of pubclic IP associated with VM

        Returns : (str)  ID of public IP if present else None

         Raises:
            Exception:
                When getting Public IP ID failed
        """
        try:
            azure_url = f"{AZURE_RESOURCE_MANAGER_URL}/"
            networkinfo = self.vm_info['properties']['networkProfile']['networkInterfaces']
            networkinfourl = None
            for network in networkinfo:
                if network.get('properties', {}).get('primary'):
                    networkinfourl = network['id']
            publicipurl = None
            if networkinfourl:
                azure_diskurl = azure_url + networkinfourl + "?api-version=2018-10-01"
                response = self.azure_session.get(azure_diskurl, headers=self.default_headers, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    networkconfigs = data['properties']['ipConfigurations']
                    dataip = None
                    for networkconfig in networkconfigs:
                        if networkconfig['properties']['primary']:
                            dataip = networkconfig
                            break
                    if dataip:
                        if 'publicIPAddress' in dataip['properties']:
                            publicipurl = dataip['properties']['publicIPAddress']['id']
            return publicipurl
        except Exception as exp:
            self.log.exception("Exception in getting  public ip ID")
            raise Exception("Exception in getting public ip ID:" + str(exp))

    def get_snapshots(self):
        """Gets snapshots associated with the bolbs and disks of VM

            Returns : (dict) dictionary with all snapshots on blobs and disks
        """

        blobs = self.get_snapshotsonblobs()
        disks = self.get_disk_snapshots()
        return {'blobs': blobs, 'disk': disks}

    def get_bloburi(self):
        """ Gets uri of blob associated with all disks of VM

            Returns: (dict)  dictionary with key as disk name and value as blob uri if present else None

             Raises:
            Exception:
                When getting blobruri failed

        """
        try:
            disks = self.disk_dict
            azure_url = f"{AZURE_RESOURCE_MANAGER_URL}/"
            self.blobs = {}
            for disk in disks:
                if 'blob.core' in disks[disk]:
                    diskname = disks[disk].split('/')[-1]
                    self.blobs[diskname] = disks[disk]
                    continue
                azure_diskurl = azure_url + disks[disk] + "?api-version=2017-03-30"
                response = self.azure_session.get(azure_diskurl, headers=self.default_headers, verify=False)
                blob_uri = None
                if response.status_code == 200:
                    data = response.json()
                    if 'sourceUri' in data['properties']['creationData']:
                        blob_uri = data['properties']['creationData']['sourceUri']
                    self.blobs[data['name']] = blob_uri

            return self.blobs

        except Exception as exp:
            self.log.exception("Exception in getting bloburi")
            raise Exception("Exception in getting bloburi:" + str(exp))

    def get_disk_snapshots(self, snapshot_rg=None):
        """ Gets snapshots details associated with disks of a VM
        Args:
            snapshot_rg   (str): Optional, Value for custom Snapshot RG to fetch snapshots

        Returns : (dict) with key as disk name and value as list of dict with with containing name
                of snapshot, time of creation , jobid of job which
                created the snapshot


         Raises:
            Exception:
                When getting snapshot details failed
        """

        try:
            disks = self.disk_dict
            snapshots = {}
            for disk in disks:
                diskname = disks[disk].split('/')[-1]
                snapshots[diskname] = None
                if 'blob.core' in disks[disk]:
                    continue
                snaprg = disks[disk].split('/')[4] if not snapshot_rg else snapshot_rg
                azure_vmurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                              "/%s/providers/Microsoft.Compute/snapshots" % (self.subscription_id, snaprg)
                api_version = '?api-version=2019-07-01'
                azure_snapurl = azure_vmurl + api_version
                response = self.azure_session.get(azure_snapurl, headers=self.default_headers, verify=False)
                if response.status_code == 200:
                    data = response.json()['value']
                    for snap in data:
                        if disks[disk] in snap['properties']['creationData']['sourceResourceId']:
                            if not snapshots[diskname]:
                                snapshots[diskname] = []
                            stamp = snap['properties']['timeCreated']
                            timeofsnap = stamp.split('T')[0] + " " + stamp.split('T')[1].split('.')[0]
                            snapname = snap['name']
                            jobid = self.get_snapshot_jobid(snap['id'])
                            snapshots[diskname].append({'name': snapname, 'timeCreated': timeofsnap, 'JobId': jobid,
                                                       'id': snap['id'], 'snapRG': snaprg})

            return snapshots
        except Exception as exp:
            self.log.exception("Exception in getting snapshots on disks")
            raise Exception("Exception in getting snapshots on disks:" + str(exp))

    def check_disk_snapshots_by_jobid(self, job_obj, all_snap=False, snapshot_rg=None):
        """ Gets snapshots details associated with disks and a job id
        Args:
            job_obj (str): job obj for which snapshot has to be checked.
            all_snap (bool): Whether return all snap details or beak if one snap exist
            snapshot_rg   (str): Optional, Value for custom Snapshot RG to fetch snapshots

        Return:
            snapshot_exists (boolean) : Whether snapshot exists or not
            snapshots (dictionary): dict of snapshots for that particular job

         Raises:
            Exception:
                When getting snapshot details failed
        """

        try:
            if self.managed_disk:
                snapshot_exists, snapshots = self.check_managed_disk_snapshots_by_jobid(job_obj, all_snap,
                                                                                        snapshot_rg)
            else:
                snapshot_exists, snapshots = self.check_unmanaged_disk_snapshots_by_jobid(job_obj, all_snap)

            return snapshot_exists, snapshots

        except Exception as exp:
            self.log.exception("Exception in getting snapshots on disks")
            raise Exception("Exception in getting snapshots on disks:" + str(exp))

    def get_snapshotsonblobs(self, get_all_details=False):
        """Gets time of creation of all snapshots on the blobs associated with VM
            :arg
                get_all_details(bool) : set to True to get dict of all details of snapshots

            Returns:  (dict)  dictionary with key as disk name and value as list containing creation time
                              of all snapshots associated with disk


        """
        try:
            bloburi = self.get_bloburi()
            blobsnapshots = {}
            for disk in bloburi:
                blobsnapshots[disk] = None
                if bloburi[disk]:
                    blobname = bloburi[disk].split('/')[-1]
                    blob_list = bloburi[disk].split('/')
                    uri = ""
                    for i in blob_list[0:3]:
                        uri = uri + i + '/'
                    uri = uri + blob_list[3] + '?restype=container&comp=list&include=snapshots&marker='
                    blobsnapshots[disk] = []
                    marker = ""
                    search_finished = False
                    while not search_finished:
                        header = self.get_storage_header('2017-11-09')
                        url = uri + marker
                        response = self.azure_session.get(url, headers=header, verify=False)
                        if response.status_code == 200:
                            res_dict = xmltodict.parse(response.text)
                            marker = res_dict['EnumerationResults']['NextMarker']
                            if res_dict['EnumerationResults']['Blobs']:
                                blobs = res_dict['EnumerationResults']['Blobs']['Blob']
                                if type(blobs) != list:
                                    blobs = [blobs]
                            for eachblob in blobs:
                                if eachblob['Name'] == blobname and 'Snapshot' in eachblob.keys():
                                    stamp = eachblob['Snapshot']
                                    timeofsnap = stamp.split('T')[0] + " " + stamp.split('T')[1].split('.')[0]
                                    if get_all_details:
                                        if eachblob not in blobsnapshots[disk]:
                                            blobsnapshots[disk].append(eachblob)
                                    else:
                                        if timeofsnap not in blobsnapshots[disk]:
                                            blobsnapshots[disk].append(timeofsnap)
                            if not marker:
                                search_finished = True
                                break
                        else:
                            self.log.error("Error in getting snapshots response "
                                           "not success : status code {0}".format(response.status_code))
                else:
                    blobsnapshots[disk] = None

            return blobsnapshots

        except Exception as exp:
            raise Exception("Execption in getting blob snapshots %s" % exp)

    def get_snapshot_jobid(self, snap_id):
        """Gets the jobid of job that created disk snapshot if snapshot

          Args:
             snap_id    (str): id of the snapshot

         Returns   (int ): JobID of job that created snapshot


        """
        try:
            azure_vmurl = AZURE_RESOURCE_MANAGER_URL
            api_version = '?api-version=2019-07-01'
            azure_snapuri = azure_vmurl + snap_id + api_version
            response = self.azure_session.get(azure_snapuri, headers=self.default_headers, verify=False)
            jobid = None
            if response.status_code == 200:
                snap_info = response.json()
                if 'tags' in snap_info and 'CreatedBy' in snap_info['tags'] and 'Description' in snap_info['tags']:
                    if snap_info['tags']['CreatedBy'] == 'Commvault':
                        if len(snap_info['tags']['Description'].split('_')) > 8:
                            jobid = int(snap_info['tags']['Description'].split('_')[3])
                        elif len(snap_info['tags']['Description'].split(' ')) > 7:
                            jobid = int(snap_info['tags']['Description'].split(' ')[3][1:-1])
                return jobid
        except Exception as err:
            self.log.info("Execption in getting jobID of snapshot %s" % err)

    def get_vm_generation(self):
        """Gets the generation of VM
           Retruns   (str):  generation of vm

        """
        try:
            api_version = "?api-version=2019-12-01"
            azure_vmurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                          "/%s/providers/Microsoft.Compute/virtualMachines" \
                          "/%s/instanceView" % (self.subscription_id, self.resource_group_name, self.vm_name)
            vm_instance_url = azure_vmurl + api_version
            response = self.azure_session.get(vm_instance_url, headers=self.default_headers, verify=False)
            if response.status_code == 200:
                instance_data = response.json()
                if 'hyperVGeneration' in instance_data.keys():
                    return instance_data['hyperVGeneration']
            else:
                raise Exception("Error in getting Genenration of VM response was not successful ")
        except Exception as err:
            raise Exception("Execption in getting vm generation %s" % err)

    def get_vm_tags(self):
        """
        Gets the tags of the VM
        :return: (dict): Dictionary with key as tag keys and value as tag value
        :raise: Exception if failed to get vm tags
        """
        try:
            data = self.vm_info
            self.tags = data.get("tags", {})
            setattr(self, "tags", self.tags)

        except Exception as err:
            self.log.exception("Exception in get_vm_tags")
            raise Exception(err)

    def get_disk_tags(self):
        """
        Gets the tags of the disks associated to the VM

        Returns:
            Dictionary  with keys as the disk and value as a dictionary of tags associated to the disk (dict)

        Raises:
            Exception if failed to get disk tags

        """
        lun_disk_dict = {disk: lun for lun, disk in self.disk_lun_dict.items()}
        if self.managed_disk:
            try:
                for disk_key, disk_id in self.disk_dict.items():
                    self.disk_sku_dict[lun_disk_dict[disk_key]]["tags"] = self.get_tag_for_disk_by_id(disk_id)
            except Exception as err:
                self.log.exception("Exception in get_disk_tags")
                raise Exception(err)

    def get_vm_guid(self):
        """
        Get GUID of particular VM

        Raises:
            Exception:
                if failed to fetch GUID of VM
        """
        try:
            data = self.vm_info
            self.guid = data["properties"]["vmId"]
            setattr(self, "guid", self.guid)

        except Exception as err:
            self.log.exception("Exception in get_vm_guid")
            raise Exception(err)

    def get_nic_info(self):
        """
        Get all network attached to that VM

        Raises:
            Exception:
                    if failed to get network information of VM
        """
        try:

            data = self.vm_info
            nic_names_id = data["properties"]["networkProfile"]["networkInterfaces"]
            nic_names = set(self.nic)
            nic_ids = set(self.nic_id)
            for eachname in nic_names_id:
                nic_id = eachname["id"]
                nic_name = eachname["id"].split("/")[-1]
                nic_names.add(nic_name)
                nic_ids.add(nic_id)

            self.nic = list(nic_names)
            self.nic_id = list(nic_ids)
            self.nic_count = len(nic_names_id)
            setattr(self, "nic_count", self.nic_count)

        except Exception as err:
            self.log.exception("Exception in get_nic_info")
            raise Exception(err)

    def get_nic_details(self):
        """Gets  the type of IP allocation of all the network interfaces of VM

        """
        try:
            azure_vmurl = AZURE_RESOURCE_MANAGER_URL
            api_version = '?api-version=2018-07-01'
            all_nics = self.nic_id
            self.nic_details = []
            for nic_id in all_nics:
                azure_nicuri = azure_vmurl + nic_id + api_version
                response = self.azure_session.get(azure_nicuri, headers=self.default_headers, verify=False)
                if response.status_code == 200:
                    nic_detail = {}
                    data = response.json()
                    nic_detail['name'] = data['name']
                    nic_detail['allocation'] = data['properties']['ipConfigurations'][0]['properties'][
                        'privateIPAllocationMethod']
                    nic_detail['ipconfig_uri'] = data['properties']['ipConfigurations'][0]['id']
                    nic_detail['public_ip_uri'] = (data['properties']['ipConfigurations'][0]['properties']
                                                   .get('publicIPAddress', {}).get('id'))
                    nic_detail['subnet_uri'] = (data['properties']['ipConfigurations'][0]['properties']
                                                .get('subnet', {}).get('id'))
                    nic_detail['nsg_uri'] = data.get('properties', {}).get('networkSecurityGroup', {}).get('id', None)
                    nic_detail['tags'] = data.get('tags', {})
                    self.nic_details.append(nic_detail)
        except Exception:
            self.log.info('Failed to get nic details')

    def get_VM_size(self):
        """
        Get instance size for the VM

        Raises:
            Exception:
                    if failed to get instance size of VM
        """
        try:

            data = self.vm_info
            self.vm_size = data["properties"]["hardwareProfile"]["vmSize"]

        except Exception as err:
            self.log.exception("Exception in get_vm_size")
            raise Exception(err)

    def get_cores(self):
        """
        Get number of CPU, memory of VM

        Raises:
            Exception:
                    if failed to get CPU, memory information of VM
        """
        try:
            if self.vm_size:
                if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                    self.api_version = "?api-version=2018-10-01"
                vm_sizeurl = self.azure_vmurl + "/vmSizes" + self.api_version
                response = self.azure_session.get(vm_sizeurl, headers=self.default_headers, verify=False)
                data = response.json()
                if response.status_code == 200:
                    for eachsize in data["value"]:
                        if eachsize["name"] == self.vm_size:
                            self.no_of_cpu = eachsize["numberOfCores"]
                            _memory = ((eachsize["memoryInMB"]) / 1024)
                            self.memory = _memory

                elif response.status_code == 404:
                    self.log.info("There was No VM in Name %s ,check the VM name" % self.vm_name)
                    self.size_info = False
                    # No VMs found

                else:
                    raise Exception("VM  data cannot be collected")

        except Exception as err:
            self.log.exception("Exception in get_vm_size")
            raise Exception(err)

    def get_Disk_info(self):
        """
        Get disk properties of both OS and data disks of VM

        Raises:
            Exception:
                    if failed to disk information of VM
        """
        try:
            data = self.vm_info
            os_disk_details = data["properties"]["storageProfile"]["osDisk"]
            if 'managedDisk' in os_disk_details:
                self.disk_info["OsDisk"] = os_disk_details["managedDisk"]["id"]
                if "storageAccountType" in os_disk_details["managedDisk"]:
                    self.storageaccount_type = os_disk_details["managedDisk"]["storageAccountType"]
                    self.disk_sku_dict[-1] = {
                        'storageAccountType': os_disk_details["managedDisk"]["storageAccountType"], 'name':'OsDisk'}
                    self.disk_size_dict['OsDisk'] = os_disk_details.get("diskSizeGB", 0)
                    self.disk_lun_dict[-1] = "OsDisk"
                    data_disk_details = data["properties"]["storageProfile"]["dataDisks"]
                    self.total_disk_size = os_disk_details.get("diskSizeGB", 0)
                    for each in data_disk_details:
                        self.disk_info[each["name"]] = each["managedDisk"]["id"]
                        self.disk_sku_dict[each["lun"]] = {
                            'storageAccountType': each.get('managedDisk').get("storageAccountType", None),
                            'name':each['name']}
                        self.disk_size_dict[each["name"]] = each.get("diskSizeGB", 0)
                        self.disk_lun_dict[each["lun"]] = each["name"]
                        self.total_disk_size += each.get("diskSizeGB", 0)
                else:
                    os_disk_info = self.hvobj.get_managed_resource_info_by_id(
                                        os_disk_details["managedDisk"]["id"], '2021-04-01')[0]
                    self.storageaccount_type = os_disk_info['sku']['name']
                    self.disk_sku_dict[-1] = {
                        'storageAccountType': os_disk_info['sku']['name'], 'name':'OsDisk'}
                    self.disk_size_dict['OsDisk'] = os_disk_info.get('properties').get('diskSizeGB', 0)
                    self.disk_lun_dict[-1] = "OsDisk"
                    self.total_disk_size = os_disk_info.get('properties').get('diskSizeGB', 0)
                    data_disk_details = data["properties"]["storageProfile"]["dataDisks"]
                    for each_disk in data_disk_details:
                        self.disk_info[each_disk["name"]] = each_disk["managedDisk"]["id"]
                        data_disk_info = self.hvobj.get_managed_resource_info_by_id(
                                         each_disk["managedDisk"]["id"], '2021-04-01')[0]
                        self.disk_sku_dict[each_disk["lun"]] = {
                            'storageAccountType': data_disk_info.get('sku').get('name'), 'name':each_disk['name']}
                        self.disk_size_dict[each_disk["name"]] = data_disk_info.get('properties').get('diskSizeGB', 0)
                        self.disk_lun_dict[each_disk["lun"]] = each_disk["name"]
                        self.total_disk_size += os_disk_info.get('properties').get('diskSizeGB', 0)
            else:
                self.managed_disk = False
                self.disk_info["OsDisk"] = os_disk_details["vhd"]["uri"]
                self.disk_size_dict["OsDisk"] = os_disk_details.get("diskSizeGB", 0)
                self.disk_lun_dict[-1] = "OsDisk"
                self.total_disk_size = os_disk_details.get("diskSizeGB", 0)
                data_disk_details = data["properties"]["storageProfile"]["dataDisks"]
                for each in data_disk_details:
                    self.disk_info[each["name"]] = each["vhd"]["uri"]
                    self.disk_size_dict[each["name"]] = each.get("diskSizeGB", 0)
                    self.disk_lun_dict[each["lun"]] = each["name"]
                    self.total_disk_size += each.get("diskSizeGB", 0)
            self.disk_dict = self.disk_info
            self.disk_count = len(self.disk_info.keys())

        except Exception as err:
            self.log.exception("Exception in get_disk_info")
            raise Exception(err)

    def get_data_disk_info(self):
        """
        Get data disks details of VM

        Raises:
            Exception:
                    if failed to disk information of VM
        """
        try:

            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                self.api_version = "?api-version=2017-12-01"
            vm_infourl = self.azure_vmurl + self.api_version
            response = self.azure_session.get(vm_infourl, headers=self.default_headers,
                                              verify=False)
            data = response.json()
            data_disk_details = []

            if response.status_code == 200:
                data_disk_details = data["properties"]["storageProfile"]["dataDisks"]

            elif response.status_code == 404:
                self.log.info("There was No VM in Name %s , please check the VM name")

            return data_disk_details

        except Exception as err:
            self.log.exception("Exception in get_data_disk_info")
            raise Exception(err)

    def get_status_of_vm(self):
        """
        Get the status of VM like started.stopped
        possible states = 'VM deallocated', 'VM running', 'VM stopped'

        Raises:
            Exception:
                    if failed to get status of VM
        """
        try:

            body = {}
            vmurl = self.azure_vmurl + "/InstanceView" + self.api_version
            data = self.azure_session.get(vmurl, headers=self.default_headers, verify=False)
            if data.status_code == 200:
                status_data = data.json()
                if "vmAgent" in status_data.keys():
                    self.vm_state = status_data["vmAgent"]["statuses"][0]["displayStatus"]

            elif data.status_code == 404:
                self.log.info("VM Not found")


            else:
                raise Exception("Cannot get the status of VM")

        except Exception as err:
            self.log.exception("Exception in getStatusofVM")
            raise Exception(err)

    def get_OS_type(self):
        """
        Update the OS Type of VM

        Raises:
            Exception:
                    if failed to find OS type of VM
        """

        try:
            data = self.vm_info
            guest_os = data['properties']["storageProfile"]["osDisk"]["osType"]
            setattr(self, "guest_os", guest_os)
            self.log.info("OS type is : %s" % self.guest_os)

        except Exception as err:
            self.log.exception("Exception in GetOSType")
            raise Exception(err)

    def get_subnet_ID(self):
        """
        Update the subnet_ID for VM

        Raises:
            Exception:
                    if failed to find subnet information of VM
        """

        try:

            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                self.api_version = "?api-version=2018-01-01"
            azure_list_nwurl = self.azure_baseURL + "/subscriptions/" + self.subscription_id \
                               + "/providers/Microsoft.Network/networkInterfaces" + self.api_version
            data = self.azure_session.get(azure_list_nwurl, headers=self.default_headers, verify=False)
            if data.status_code == 200:
                _all_nw_data = data.json()
                for each_nw in _all_nw_data["value"]:
                    if each_nw["name"] == self.network_name:
                        ip_config_info = each_nw["properties"]["ipConfigurations"]
                        for each_ip_info in ip_config_info:
                            self.subnetId = each_ip_info["properties"]["subnet"]["id"]
                            break
            else:
                raise Exception("Failed to get network details for the VM")


        except Exception as err:
            self.log.exception("Exception in GetSubnetID")
            raise Exception(err)

    def get_IP_address(self):
        """
        Get the Ip address of the VM

        Raises:
            Exception:
                    if failed to get IP address of VM
        """
        try:
            data = self.vm_info
            self.log.info("VM data : %s" % data)

            nw_interfaces = data['properties']["networkProfile"]["networkInterfaces"]
            for each_network in nw_interfaces:
                nw_interface_value = each_network["id"]

            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                self.api_version = "?api-version=2018-01-01"

            nw_interface_url = self.azure_baseURL + nw_interface_value + self.api_version
            response = self.azure_session.get(nw_interface_url, headers=self.default_headers, verify=False)
            nic_interface_info = response.json()
            # Setting network security group
            nsg = ''
            if "networkSecurityGroup" in nic_interface_info["properties"]:
                nsg = nic_interface_info["properties"]["networkSecurityGroup"]["id"]
            setattr(self, "nsg", nsg)

            ip_config_info = nic_interface_info["properties"]["ipConfigurations"]
            for each_ip_info in ip_config_info:
                vm_vnet_props = each_ip_info["properties"]
                break

            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                self.api_version = "?api-version=2018-01-01"
            else:
                self.api_version = "?api-version=2017-10-01"

            vm_ip = vm_vnet_props["privateIPAddress"]
            setattr(self, "ip", vm_ip)

            self.subnet_id = vm_vnet_props["subnet"]["id"]
            nw_name = nic_interface_info["id"]
            self.network_name = nw_name.split("/")[-1]

            setattr(self, "host_name", vm_ip)

        except Exception as err:
            self.log.exception("Exception in get_vm_ip_address")
            raise Exception(err)

    def get_blobs(self):
        """
        This will only work if storage account of the VM is set in kwargs or this is an unmanaged VM
        Returns the list of blobs present in the storage account.
        """
        try:
            storage_account = self.kwargs.get('storage_account_name', self.disk_storage_account)
            if not storage_account:
                raise Exception("VM's storage account not found")
            return self.hvobj.get_vhds_in_storage_account(storage_account)
        except Exception as err:
            self.log.exception("Exception in get_blobs")
            raise Exception(err)

    def verify_snapshot_rg(self, job_obj, snapshot_rg=None):
        """
        Verify snapshot for managed disk for a backup job in Custom RG

        Args:
             job_obj       (obj): Job object for Backup Job
             snapshot_rg (str): Name of custom RG for snapshot

        Raises:
            Exception:
                if failed to get snapshot information from RG
        """
        try:
            if self.managed_disk:
                self.log.info("Getting snapshots for backup Job")

                snap_exist = False

                #Check snapshot in custom snapshot RG
                if snapshot_rg:
                    custom_rg_snapshots = self.get_disk_snapshots(snapshot_rg)
                    for disk in custom_rg_snapshots:
                        for snap in custom_rg_snapshots[disk]:
                            if snap['JobId'] == int(job_obj.job_id) and snap['snapRG'] == snapshot_rg:
                                self.log.info('Custom snap RG Validation Successful for Snapshot {0} for Disk {1} in '
                                               'custom RG {2}'.format(snap['name'], disk, snapshot_rg))
                                snap_exist = True
                                break
                            else:
                                self.log.error('Custom snap RG Validation failed for Snapshot {0} for Disk {1}'
                                                   ' in RG {2}'.format(snap['name'], disk, snap['snapRG']))
                                raise Exception("Custom snapshot RG Validation Failed, Snap created in Src RG")
                                break

                #If not present in Custom RG or if custom RG not given, check in disk RG
                if not snap_exist or snapshot_rg is None:
                    src_rg_snapshots = self.get_disk_snapshots()

                    for disk in src_rg_snapshots:
                        for snap in src_rg_snapshots[disk]:
                            if snap['JobId'] == int(job_obj.job_id):
                                self.log.info(' Snapshot {0} for Disk {1} present in disk RG {2}'.
                                               format(snap['name'], disk, snap['snapRG']))
                                snap_exist = True

                #If snapshot not present in both disk RG and custom RG
                if not snap_exist:
                    raise Exception("Snapshot not found in Custom or Src RG. CBT disabled or snap deleted from portal")
            else:
                self.log.info("Custom RG validation not applicable for unmanaged VM : {0}".format(self.vm_name))

        except Exception as err:
            self.log.exception("Snapshot RG Validation failed {0}".format(err))
            raise Exception(err)

    def get_encryption_info(self):
        """
        Get encryption properties for disks of VM

        Raises:
            Exception:
                    if failed to get encryption information of VM
        """
        try:
            api_version = "?api-version=2019-12-01"
            azure_vmurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                          "/%s/providers/Microsoft.Compute/virtualMachines" \
                          "/%s/extensions" % (self.subscription_id, self.resource_group_name, self.vm_name)
            vm_extension_url = azure_vmurl + api_version
            response = self.azure_session.get(vm_extension_url, headers=self.default_headers, verify=False)
            if response.status_code == 200:
                data = response.json()
                vm_extensions_info = data["value"]
                for extension in vm_extensions_info:
                    if "AzureDiskEncryption" in extension["properties"]["type"]:
                        required_keys = ["provisioningState", "typeHandlerVersion", "KeyEncryptionAlgorithm",
                                         "VolumeType", "KekVaultResourceId"]
                        self.log.info("VM Encryption Setting: {}".format(extension["properties"]))

                        if extension["properties"]["provisioningState"] == "Succeeded":
                            self.is_encrypted = True
                            self.encryption_info["location"] = extension["location"]

                            for key in required_keys:
                                if key in extension["properties"].keys():
                                    self.encryption_info[key] = extension["properties"][key]

                                elif key in extension["properties"]["settings"].keys():
                                    self.encryption_info[key] = extension["properties"]["settings"][key]

                            # Extract Key & KeyVault Name from KEK URL
                            if len(extension["properties"]["settings"]["KeyEncryptionKeyURL"]) > 0:
                                self.encryption_info["encryptionKeyName"] = re.match(r".*/keys/(.*)/",
                                                    extension["properties"]["settings"]["KeyEncryptionKeyURL"]).group(1)
                                self.encryption_info["keyVaultName"] = re.match(r".*/(.*)$",
                                                    extension["properties"]["settings"]["KeyVaultResourceId"]).group(1)
            else:
                self.log.error("Unable to Fetch Encryption extension Information")

        except Exception as err:
            self.log.exception("Exception in get_encryption_info")
            raise Exception(err)

    def is_powered_on(self):
        """Returns: True, if VM is powered on, False otherwise"""
        self.api_version = '?api-version=2018-10-01'
        vmurl = self.azure_vmurl + "/InstanceView" + self.api_version
        data = self.azure_session.get(vmurl, headers=self.default_headers, verify=False)
        if data.status_code == 200:
            status_data = data.json()
            for status in status_data.get('statuses', []):
                if "powerstate" in status.get('code', '').lower():
                    return 'running' in status.get('code', '').lower()
        return False

    def add_data_disk(self, disk_name, storage_account, disk_size):
        """
        Adds a new data disk to the VM

        Args:
            disk_name (string) : Name of the new data disk
            storage_account (string) : Storage Account name to create the new data_disk in it
            disk_size (string) : Size of the new data disk

        Raises:
            Exception
                When the disk is not created
        """
        if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
            self.api_version = "?api-version=2020-06-01"
        vm_infourl = self.azure_vmurl + self.api_version
        info_response = self.azure_session.get(vm_infourl, headers=self.default_headers,
                                               verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            raise Exception("Error: %s" % status_code)

        vm_info = info_response.json()

        if self.managed_disk:
            self.log.info("disks are managed disks")
            lun = len(vm_info["properties"]["storageProfile"]["dataDisks"])
            new_disk = {
                "lun": lun,
                "name": disk_name,
                "createOption": "Empty",
                "managedDisk": {
                    "storageAccountType": "Standard_LRS"
                },
                "caching": "ReadWrite",
                "diskSizeGB": disk_size
            }
            vm_info["properties"]["storageProfile"]["dataDisks"].append(new_disk)
            updated_vm_info = json.dumps(vm_info)
        else:
            self.log.info("disks are unmanaged disks")
            disk_vhd_uri = "https://{}.blob.core.windows.net/vhds/{}.vhd".format(storage_account, disk_name)
            lun = len(vm_info["properties"]["storageProfile"]["dataDisks"])
            new_disk = {
                "lun": lun,
                "name": disk_name,
                "createOption": "Empty",
                "vhd": {
                    "uri": disk_vhd_uri
                },
                "caching": "ReadWrite",
                "diskSizeGB": disk_size
            }
            vm_info["properties"]["storageProfile"]["dataDisks"].append(new_disk)
            updated_vm_info = json.dumps(vm_info)

        try:
            response = self.azure_session.patch(vm_infourl, data=updated_vm_info, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                self.log.info("Couldn't create and add a new data disk")
                raise Exception("Error: %s" % status_code)
            return response.url.split("azure.com")[1]

        except Exception as err:
            self.log.exception("Failed to create a new data disk")
            raise Exception(err)

    def detach_data_disk(self, disk_name, delete=True):
        """
        Detaches the data disk attached to the VM

        Args:
            disk_name (string) : Name of the data disk to be deleted
            delete  (bool)  :   True if you want to delete the disk else False

        Raises:
            Exception
                When the disk is not deleted
        """
        if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
            self.api_version = "?api-version=2020-06-01"
        vm_infourl = self.azure_vmurl + self.api_version
        info_response = self.azure_session.get(vm_infourl, headers=self.default_headers,
                                               verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            raise Exception("Error: %s" % status_code)

        vm_info = info_response.json()

        # detaching the data disk
        self.log.info("Detaching the data disk")
        data_disks = vm_info["properties"]["storageProfile"]["dataDisks"]
        disk_uri = None
        for each in data_disks:
            if each["name"] == disk_name:
                if "vhd" in each:
                    disk_uri = each["vhd"]["uri"]
                vm_info["properties"]["storageProfile"]["dataDisks"].remove(each)

        updated_vm_info = json.dumps(vm_info)

        try:
            response = self.azure_session.patch(vm_infourl, data=updated_vm_info, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                raise Exception("Error: %s" % status_code)
            self.log.info('Data disk has been ditached successfully')

        except Exception as err:
            self.log.exception("Failed to detach the data disk")
            raise Exception(err)

        # deleting the data disk
        if delete:
            if self.managed_disk:
                self.log.info("deleting the managed disk")
                del_url = self.azure_baseURL + '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/' \
                                               'disks/{}?api-version=2020-06-30'.format(self.subscription_id,
                                                                                        self.resource_group_name,
                                                                                        disk_name)
                try:
                    del_response = self.azure_session.delete(del_url, headers=self.default_headers, verify=False)
                    del_status_code = del_response.status_code
                    if del_status_code != 202 and del_status_code != 200:
                        self.log.info('Cannot delete the disk')
                        raise Exception("Error: %s" % del_status_code)
                    return del_response.url.split("azure.com")[1]
                except Exception as err:
                    self.log.exception("Failed to delete the data disk")
                    raise Exception(err)
            else:
                if disk_uri:
                    self.log.info("deleting the unmanaged disk")
                    del_headers = self.get_storage_header('2019-12-12')
                    try:
                        del_response = self.azure_session.delete(disk_uri, headers=del_headers, verify=False)
                        del_status_code = del_response.status_code
                        if del_status_code != 202 and del_status_code != 200:
                            self.log.info('Cannot delete the blob disk')
                            if del_status_code == 412:
                                self.log.info("There is a lease on the blob and it cannot be deleted")
                                return del_response.status_code
                            raise Exception("Error: %s" % del_status_code)
                        return del_response.url.split("azure.com")[1]
                    except Exception as err:
                        self.log.exception("Failed to delete the data disk")
                        raise Exception(err)
                else:
                    self.log.info("Disk uri not present")
        else:
            self.log.info('Disks are not deleted')

    def delete_snapshots(self):
        """
        Deletes the snapshots of the disks in the VM

        Raises:
            Exception
                When the snapshots are not deleted
        """
        if self.managed_disk:
            self.log.info("Deleting snapshots of a managed disk")
            disks = self.get_disk_snapshots()
            for disk in disks:
                snapshots = disks[disk]
                for snaps in snapshots[0]:
                    snap_name = snaps['name']
                    url = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/snapshots/{}?' \
                          'api-version=2020-06-30'.format(self.subscription_id, self.resource_group_name, snap_name)
                    del_url = self.azure_baseURL + url
                    try:
                        response_del_snapshot = self.azure_session.delete(del_url, headers=self.default_headers,
                                                                          verify=False)
                        del_status_code = response_del_snapshot.status_code
                        if del_status_code != 202 and del_status_code != 200:
                            self.log.info('Cannot delete the disk snapshots')
                            raise Exception("Error: %s" % del_status_code)
                        self.log.info('Snapshots of disk = %s are deleted', snap_name)

                    except Exception as err:
                        self.log.exception("Failed to delete the snapshots")
                        raise Exception(err)
        else:
            self.log.info("Deleting snapshots of an unmanaged disk")
            blob_uri = self.get_bloburi()
            header_del_snapshot = self.get_storage_header('2019-12-12')
            header_del_snapshot['x-ms-delete-snapshots'] = 'only'
            for disk in blob_uri:
                del_url = blob_uri[disk]
                try:
                    response_del_snapshot = self.azure_session.delete(del_url, headers=header_del_snapshot,
                                                                      verify=False)
                    del_status_code = response_del_snapshot.status_code
                    if del_status_code != 202 and del_status_code != 200:
                        self.log.info('Cannot delete the blob snapshots')
                        if del_status_code == 412:
                            self.log.info("There is a lease on the blob and it cannot be deleted")
                            continue
                        raise Exception("Error: %s" % del_status_code)
                    self.log.info('Snapshots of blob = %s are deleted', blob_uri[disk])

                except Exception as err:
                    self.log.exception("Failed to delete the snapshots")
                    raise Exception(err)

    def get_nic_list(self):
        """
        Gets the NICs present in the resource group

        Raises:
            Exception
                When facing issue in getting the NIC list
        """
        nic_listurl = self.azure_baseURL + '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/' \
                                           'networkInterfaces?api-version=2020-07-01'.format(self.subscription_id,
                                                                                             self.resource_group_name)
        info_response = self.azure_session.get(nic_listurl, headers=self.default_headers, verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            raise Exception("Error: %s" % status_code)

        nics = info_response.json()
        nic_list = []
        for each in nics['value']:
            nic_list.append(each.get('name'))
        return nic_list

    def add_nic(self, nic_name):
        """
        Attaches an existing NIC to the VM

        Args:
            nic_name (string) : Name of the NIC

        Raises:
            Exception
                When the NIC is not attached to the VM
        """
        if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
            self.api_version = "?api-version=2020-06-01"
        vm_infourl = self.azure_vmurl + self.api_version
        info_response = self.azure_session.get(vm_infourl, headers=self.default_headers,
                                               verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            raise Exception("Error: %s" % status_code)

        vm_info = info_response.json()
        self.log.info("Getting the nic list and checking if the NIC is present or not")
        nic_list = self.get_nic_list()
        if nic_name not in nic_list:
            subnet_resource = self.subnet_id.split('/')[4]
            subnet_network = self.subnet_id.split('/')[-3]
            subnet_name = self.subnet_id.split('/')[-1]
            self.get_new_network_interface(nic_name, subnet_resource, subnet_network, subnet_name)
        nic_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/networkInterfaces" \
                 "/{}".format(self.subscription_id, self.resource_group_name, nic_name)
        new_nic = {
            "id": nic_id,
            "properties": {
                "primary": "false"
            }
        }
        self.deallocate()
        time.sleep(60)
        vm_nics = vm_info["properties"]["networkProfile"]["networkInterfaces"]
        # making the first NIC primary
        if 'properties' not in vm_nics[0]:
            vm_info["properties"]["networkProfile"]["networkInterfaces"][0]['properties'] = {'primary': 'true'}
        # adding the new NIC
        vm_info["properties"]["networkProfile"]["networkInterfaces"].append(new_nic)
        updated_vm_info = json.dumps(vm_info)
        self.log.info("Attaching the NIC to the VM")
        try:
            response = self.azure_session.patch(vm_infourl, data=updated_vm_info, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                self.log.info("Cannot attach the NIC to the VM")
                raise Exception("Error: %s" % status_code)
            self.power_on()
            time.sleep(60)
            self.update_vm_info('All', True, True)
            return response.url.split("azure.com")[1]

        except Exception as err:
            self.log.exception("Failed to attach the nic")
            raise Exception(err)

    def remove_nic(self, nic_name):
        """
        Detaches a NIC from the VM

        Args:
            nic_name (string) : Name of the NIC

        Raises:
            Exception
                When the NIC is not detached from the VM
        """
        if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
            self.api_version = "?api-version=2020-06-01"
        vm_infourl = self.azure_vmurl + self.api_version
        info_response = self.azure_session.get(vm_infourl, headers=self.default_headers, verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            raise Exception("Error: %s" % status_code)

        self.log.info("Detaching the NIC from the VM")
        self.deallocate()
        time.sleep(60)
        vm_info = info_response.json()
        nic_info = vm_info["properties"]["networkProfile"]["networkInterfaces"]
        for each in nic_info:
            if each["id"].split("/")[-1] == nic_name:
                vm_info["properties"]["networkProfile"]["networkInterfaces"].remove(each)

        updated_vm_info = json.dumps(vm_info)

        try:
            response = self.azure_session.patch(vm_infourl, data=updated_vm_info, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                self.log.info("NIC is not detached")
                raise Exception("Error: %s" % status_code)
            self.power_on()
            time.sleep(60)
            self.update_vm_info('All', True, True)
            return response.url.split("azure.com")[1]

        except Exception as err:
            self.log.exception("Failed to detach the nic")
            raise Exception(err)

    def delete_nic(self, nic_name):
        """
        Deletes the NIC
        Args:
            nic_name (string) : Name of the NIC
        Raises:
            Exception
                When the NIC is not deleted
        """
        nic_list = self.get_nic_list()
        if nic_name not in nic_list:
            self.log.info("The selected nic %s is not present in the resource group", nic_name)
        nic_url = self.azure_baseURL + '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/' \
                                       'networkInterfaces/{}?api-version=2020-07-01'.format(self.subscription_id,
                                                                                            self.resource_group_name,
                                                                                            nic_name)
        try:
            info_response = self.azure_session.delete(nic_url, headers=self.default_headers, verify=False)
            status_code = info_response.status_code
            if status_code != 202 and status_code != 200:
                self.log.info("NIC is not deleted")
                raise Exception("Error: %s" % status_code)
            return info_response.url.split("azure.com")[1]
        except Exception as err:
            self.log.exception("Failed to delete the nic")
            raise Exception(err)

    def make_nic_static(self, nic_name):
        """
        Makes a NIC static

        Args:
            nic_name (string) : Name of the NIC

        Raises:
            Exception
                When the NIC is not made static
        """
        nic_infourl = self.azure_baseURL + "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/" \
                                           "networkInterfaces/{}?api-version=2020-07-01" \
                                           "".format(self.subscription_id, self.resource_group_name, nic_name)
        info_response = self.azure_session.get(nic_infourl, headers=self.default_headers, verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            self.log.info("NIC not present in the resource group")
            raise Exception("Error: %s" % status_code)

        self.log.info("Making the NIC static")
        nic_info = info_response.json()
        ips = nic_info["properties"]["ipConfigurations"]
        for each in ips:
            each["properties"]["privateIPAllocationMethod"] = "Static"

        updated_nic_info = json.dumps(nic_info)

        try:
            response = self.azure_session.put(nic_infourl, data=updated_nic_info, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                self.log.info('Could not make the NIC static')
                raise Exception("Error: %s" % status_code)

            return response.url.split("azure.com")[1]

        except Exception as err:
            self.log.exception("Failed to change the ip state of the nic")
            raise Exception(err)

    def make_nic_dynamic(self, nic_name):
        """
        Makes a NIC dynamic

        Args:
            nic_name (string) : Name of the NIC

        Raises:
            Exception
                When the NIC is not made dynamic
        """
        nic_infourl = self.azure_baseURL + "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/" \
                                           "networkInterfaces/{}?api-version=2020-07-01" \
                                           "".format(self.subscription_id, self.resource_group_name, nic_name)
        info_response = self.azure_session.get(nic_infourl, headers=self.default_headers, verify=False)
        status_code = info_response.status_code
        if status_code != 201 and status_code != 200:
            self.log.info("NIC not present in the resource group")
            raise Exception("Error: %s" % status_code)

        self.log.info("Making the NIC dynamic")
        nic_info = info_response.json()
        ips = nic_info["properties"]["ipConfigurations"]
        for each in ips:
            each["properties"]["privateIPAllocationMethod"] = "Dynamic"

        updated_nic_info = json.dumps(nic_info)

        try:
            response = self.azure_session.put(nic_infourl, data=updated_nic_info, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                self.log.info("Could not make the NIC dynamic")
                raise Exception("Error: %s" % status_code)
            return response.url.split("azure.com")[1]

        except Exception as err:
            self.log.exception("Failed to change the ip state of the given nic")
            raise Exception(err)

    ##Chirag's code
    def get_new_network_interface(self, vm, subnet_resource, subnet_network, subnet_name):
        """

        Creates a new network interface on Azure in the current resource group
        Args :
            vm: Name for the NIC
            subnet_resource: Name of the subnet resource
            subnet_network: Name of the subnet network
            subnet_name: Name of the subnet
        Raises:
            Exception:
                If failed to create new network interface
        """
        nic_url = self.azure_baseURL
        request_url = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/networkInterfaces" \
                      "/{}{}".format(self.subscription_id, self.resource_group_name, vm,
                                     self.api_version)
        nic_url += request_url

        subnet_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks" \
                    "/{}/subnets/{}".format(self.subscription_id, subnet_resource, subnet_network,
                                            subnet_name)

        data = {
            "properties": {
                "enableAcceleratedNetworking": "false",
                "ipConfigurations": [
                    {
                        "name": "ipconfig1",
                        "properties": {
                            "subnet": {
                                "id": "%s" % subnet_id
                            }
                        }
                    }
                ]
            },
            "location": "East US2"
        }

        data = json.dumps(data)

        try:
            response = self.azure_session.put(nic_url, data=data, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                raise Exception("Error: %s" % status_code)

            return response.url.split("azure.com")[1]

        except Exception as err:
            self.log.exception("Failed to create a network interface")
            raise Exception(err)

    def get_availability_zone(self):
        """
                Get Availability Zone for the VM

                Raises:
                    Exception:
                            if failed to get Availability Zone of VM
                """
        try:
            data = self.vm_info
            if "zones" in data:
                self.availability_zone = data["zones"][0]

            else:
                self.availability_zone = 'None'

        except Exception as err:
            self.log.exception("Exception in get_availability_zone")
            raise Exception(err)

    def get_proximity_placement_group(self):
        """

        Get proximity placement group info for the VM

        Raises:
            Exception:
                if failed to get proximity placement group info on the VM

        """
        try:
            data = self.vm_info
            # data2=data["properties"]
            if data.get("properties",{}).get("proximityPlacementGroup"):
                self.proximity_placement_group=data["properties"]["proximityPlacementGroup"]["id"]
            # if "proximityPlacementGroup" in data["properties"]:
            else:
                self.proximity_placement_group=None

        except Exception as err:
            self.log.exception("Exception in get_proximity_placement_group")
            raise Exception(err)

    # Chirag's code
    def create_vm(self, subnet_resource, subnet_network, subnet_name):
        """
        Creates a new VM on Azure int the current resource group
        subnet_resource: Name of the subnet resource
        subnet_network: Name of the subnet network
        subnet_name: Name of the subnet
        Raises:
            Exception:
                If failed to create VM
        """
        new_vm_name = self.vm_name + str(time.time())[-4:]
        api_version = "?api-version=2019-12-01"
        network_interface = self.get_new_network_interface(new_vm_name, subnet_resource,
                                                           subnet_network, subnet_name).split('?')[0]

        create_url = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute" \
                     "/virtualMachines/{}{}".format(self.subscription_id, self.resource_group_name,
                                                    new_vm_name, api_version)

        request_url = self.azure_baseURL + create_url

        data = {
            "location": "East US2",
            "name": "%s" % new_vm_name,
            "properties": {
                "hardwareProfile": {
                    "vmSize": "Standard_B1ls"
                },
                "storageProfile": {
                    "imageReference": {
                        "sku": "18.04-LTS",
                        "publisher": "Canonical",
                        "version": "latest",
                        "offer": "UbuntuServer"
                    },
                    "osDisk": {
                        "caching": "ReadWrite",
                        "managedDisk": {
                            "storageAccountType": "Standard_LRS"
                        },
                        "name": "%s-od" % new_vm_name,
                        "createOption": "FromImage"
                    }
                },
                "osProfile": {
                    "adminUsername": "user",
                    "computerName": "computername",
                    "adminPassword": "password"
                },
                "networkProfile": {
                    "networkInterfaces": [
                        {
                            "id": "%s" % network_interface,
                            "properties": {
                                "primary": "true"
                            }
                        }
                    ]
                }
            }
        }

        data = json.dumps(data)

        try:
            response = self.azure_session.put(request_url, data=data, headers=self.default_headers)

            status_code = response.status_code
            if status_code != 201 and status_code != 200:
                raise Exception("Error: %s" % status_code)

            self.log.info("Successfully created new VM: %s" % new_vm_name)

        except Exception as err:
            self.log.exception("Failed to create a new VM")
            raise Exception(err)

    def attach_disks(self, disk_id_list, init_lun_id=None):
        """
            Attaches the disk provide to the VM
            Args:
                disk_id_list    (list): list of managed disk id or vhd uri
                init_lun_id     (int):  starting lun id at which disk needs to be attached

        """
        request_body = {'location': self.region}
        data_disks = self.vm_info['properties']['storageProfile']['dataDisks']
        if not init_lun_id:
            init_lun_id = len(data_disks) + 2
        for disk in disk_id_list:
            disk_info = {
                "createOption": "Attach",
                "lun": init_lun_id
            }
            if self.managed_disk:
                disk_info["managedDisk"] = {
                    "id": f"{disk}"
                }
            else:
                disk_info["vhd"] = {
                    'uri': f"{disk}"
                }
            init_lun_id += 1
            data_disks.append(disk_info)
        request_body['properties'] = {}
        request_body['properties']['storageProfile'] = {"dataDisks": data_disks}
        self.hvobj.execute_api("PUT", self.vm_info.get('id'),
                               self.default_headers, request_body, api_version='?api-version=2022-11-01')    
        
    def run_command(self, script=[]):
        """
        Runs provided script on the VM using Azure runCommand API

        Args:
            script (list) : list of all lines of command to be executed on the VM

        Raises:
            Exception
                When it fails to run provided command on the VM
        """
        self.api_version = "?api-version=2023-07-01"
        vm_infourl = f"{self.azure_vmurl}/runCommand{self.api_version}"
        command_body = {
            'script': script
        }
        if self.guest_os.lower() == "windows":
            command_body['commandId'] = 'RunPowerShellScript'
        else:
            command_body['commandId'] = 'RunShellScript'

        try:
            self.log.info("Start to run command on VM, powering on VM to exxecute command")
            self.power_on()
            time.sleep(120)

            response = self.azure_session.post(vm_infourl, json=command_body, headers=self.default_headers)

            if response.status_code not in [200, 201, 202]:
                self.log.info("Failed to Run Command on VM")
                raise Exception(f"Failed to Run Command on VM with error: {response.json()}")

            else:
                self.log.info("Command ran successfully on VM, sleeping for 2 min")
                time.sleep(120)

        except Exception as err:
            self.log.exception("Failed to Run Command on VM")
            raise Exception(f"Failed to Run Command on VM with error: {err}")

    def generalize_vm(self):
        """
        Generalize the VM for it to be then converted to image

        Raises:
            Exception
                When it fails to Generalize the VM
        """
        self.api_version = "?api-version=2023-07-01"
        vm_infourl = f"{self.azure_vmurl}/generalize{self.api_version}"

        try:
            self.log.info(f"Started to generalize VM {self.vm_name}, deallocating VM before generalising.")
            self.power_off(skip_wait_time=True)
            time.sleep(200)

            response = self.azure_session.post(vm_infourl, headers=self.default_headers)

            if response.status_code not in [200, 201, 202]:
                self.log.info("Failed to Generalize VM")
                raise Exception(f"Failed to Generalize VM with error: {response.json()}")

            else:
                self.log.info("VM Generalized successfully, sleeping for 1 min")
                time.sleep(60)

        except Exception as err:
            self.log.exception("Failed to Run Generalize VM")
            raise Exception(f"Failed to Generalize VM with error: {err}")

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False, **kwargs):
        """
         fetches all the properties of the VM

         Args:
                 should have code for two possibilties

                 Basic - Basic properties of VM like cores,GUID,disk

                 All   - All the possible properties of the VM

                 Set the property VMGuestOS for creating OS Object

                 fetches some particular specified property

                 force_update - to refresh all the properties always
                    True : ALways collect  properties
                    False: refresh only if properties are not initialized

         Raises:
            Exception:
                 if failed to get all the properties of the VM
         """
        try:
            if self.vm_info:
                self.log.info("VM Info is : {0}".format(self.vm_info))

                if not self._basic_props_initialized or force_update:
                    self._get_vm_info()
                    self.get_vm_guid()
                    self.get_VM_size()
                    self.get_cores()
                    self.get_Disk_info()
                    self.get_status_of_vm()
                    self.get_IP_address()
                    self.get_nic_info()
                    self.get_subnet_ID()
                    self.get_OS_type()
                    self.get_nic_details()
                    self.get_encryption_info()
                    self.get_availability_zone()
                    self.get_vm_tags()
                    self.get_disk_tags()
                    self.get_proximity_placement_group()
                    self.get_disk_encryption_info()
                    self.get_vm_extensions()
                    self.get_vm_security_profile_info()
                    self.get_os_image_reference_info()
                    self.get_vm_architecture()
                    self.get_auto_vm_config()
                    self._basic_props_initialized = True

                if prop == 'All':
                    if not self.is_powered_on():
                        self.power_on()
                        time.sleep(180)
                    self.vm_guest_os = self.guest_os
                    self.get_drive_list()

                elif hasattr(self, prop):
                    return getattr(self, prop, None)

            else:
                self.log.info("VM Info is Empty. Fetching it again")
                self._get_vm_info()
                self._basic_props_initialized = False

        except Exception as err:
            self.log.exception("Failed to Get the VM Properties of the VM")
            raise Exception(err)


    def compute_distribute_workload(self, proxy_obj, workload_vm):
        """
        Prepare list of proxies present in workload_vm region
        Args:
            proxy_obj (dict) : A dictionary of proxy as key and proxy object as value
            workload_vm (string): The backed up VM
        """
        self.workload_vm = workload_vm
        for proxy in proxy_obj:
            if proxy != workload_vm:
                if proxy_obj[proxy] == self.hvobj.VMs[self.workload_vm].region_name:
                    self.workload_region_proxy.append(proxy)

    def get_azure_restorepointcollectionurl(self, restorepoint_Collection_Name, custom_snapshotrg=None):
        """
        The azure restorepoint collection URL for making API calls
        Restore point collection is created under VM resource group if custom resource group is not defined
        Args:
            restorepoint_Collection_Name (string) : Restore point collection name
            custom_snapshotrg (string) : Optional - if custom resource group set at VM group
        Returns:
            azure_restorepoint_collection_url (string) : Azure Url of restore point collection
        """
        if custom_snapshotrg is None:
            custom_snapshotrg = self.resource_group_name
        azure_restorepoint_collection_url = AZURE_RESOURCE_MANAGER_URL + "subscriptions/%s/resourceGroups" \
                                                                         "/%s/providers/Microsoft.Compute/restorePointCollections/%s" % (
                                            self.subscription_id, custom_snapshotrg, restorepoint_Collection_Name)
        return azure_restorepoint_collection_url

    def get_azure_restorepointurl(self, restorepointcollection_name, restorepoint_name, custom_snapshotrg=None):
        """
        The azure restorepoint details URL for making API calls
        Args:
            restorepointcollection_name (string): Restore point collection name
            restorepoint_name (string): Restore point name
            custom_snapshotrg (string): Custom RG set for snapshot/restore point in vmgroup
        Returns:
            azure_restorepoint_url (string) : restore point url
        //Restore point collection is created under VM resource group if custom resource group is not defined
        """
        rpc_url = self.get_azure_restorepointcollectionurl(restorepointcollection_name, custom_snapshotrg)
        azure_restorepoint_url = rpc_url + "/restorePoints/%s" % restorepoint_name
        return azure_restorepoint_url

    def get_RestorePointCollection_Name(self):
        """
        Returns:
            (string) restore point collection name for the VM
        """
        vmgroupid_hex = hex(self.vm_subclientid).split('x')[-1]
        return RestorePointConstants.COLLECTION_STRING.value + self.vm_name + '_' + self.region_name + '_' + vmgroupid_hex

    def get_RestorePointName(self, job_id, backupmethod):
        """
        Get restore point name for job
        Args:
        job_id (string) - child job id of the job in validation
        backupmethod (string) - streaming / snap backup as passed from option

        Return:
        returns (string) - Restore point name for that job
        """
        if backupmethod == "SNAP":
            return RestorePointConstants.SNAP_RESTOREPOINT.value + job_id
        else:
            return RestorePointConstants.STREAMING_RESTOREPOINT.value + job_id

    def get_restorepoints_by_jobid(self, job_obj, backup_method, custom_snapshotrg=None):
        """
        Validates if disk restore points exists for each disk for input job
        Args:
            job_obj (string): job obj for which restore point has to be checked.
            backup_method (string): Whether snap or streaming backup
            custom_snapshotrg   (string): Optional, Value for custom Snapshot RG to fetch snapshots

        Return:
            restorepoint_json (dict) : Returns restore point details for the input job in dict from api response,
                                        if error in api returns None
        """
        try:
            api_version = '?api-version=2023-03-01'
            self.log.info("Getting restore point details based on job id for job {0}".format(job_obj.job_id))
            restorepointcollection_name = self.get_RestorePointCollection_Name()
            restorepoint_name = self.get_RestorePointName(job_obj.job_id, backup_method)
            restorepoint_url = self.get_azure_restorepointurl(restorepointcollection_name, restorepoint_name,
                                                              custom_snapshotrg)
            api_url = restorepoint_url + api_version
            response = self.azure_session.get(api_url, headers=self.default_headers, verify=False)
            if response.status_code == 200:
                restorepoint_json = response.json()
                return restorepoint_json
            else:
                return None

        except Exception as exp:
            self.log.exception("Exception in getting restore point details")
            raise Exception("Exception in getting restore point details:" + str(exp))

    def validate_restorepoint_consistencymode(self, consistencymode, _appConsistentbackupenabled):
        """
        Args:
            consistencymode (string)- consistency mode value from restore point json
            _appConsistentbackupenabled (boolean) - VM group configuration option (Appconsistent/Crash consistent)
        Return:
            No return value as this is soft error and backup will be successful
        """
        try:
            consistency_check = False
            if _appConsistentbackupenabled:
                if self.guest_os.lower() == "windows":
                    if consistencymode == RestorePointConstants.APP_CONSISTENT_WIN.value:
                        consistency_check = True

                elif self.guest_os.lower() == "linux":
                    if consistencymode == RestorePointConstants.APP_CONSISTENT_LINUX.value:
                        consistency_check = True
            else:
                if consistencymode == RestorePointConstants.CRASH_CONSISTENT.value:
                    consistency_check = True

            if consistency_check:
                self.log.info("Consistency mode is {0} and validation is successful".format(consistencymode))
            else:
                self.log.info(
                    "Consistency mode Validation Failed. Consistency mode is {0}, check power state of vm during backup".format(
                        consistencymode))
        except Exception as exp:
            self.log.exception("Exception in validating consistency mode" + str(exp))

    def validate_restorepoints_by_jobid(self, job_obj, backup_method, _appconsistent_backup_enabled,
                                        custom_snapshotrg=None):
        """
        Validates if disk restore points exists for each disk for input job
        Args:
            job_obj (string): job obj for which restore point has to be checked.
            backup_method (string): Whether snap or streaming backup
            _appconsistent_backup_enabled (boolean): VM group configuration option (Appconsistent/Crash consistent)
            custom_snapshotrg   (string): Optional, Value for custom Snapshot RG to fetch snapshots
        Return:
            check_diskrestorepoints (boolean) : True if disk restore points for all disks present in expected RG

        """
        try:
            check_diskrestorepoints = True
            if self.managed_disk:
                disks = self.disk_dict
                diskrestorepoint = {}
                for disk in disks:
                    diskname = disks[disk].split('/')[-1]
                    diskrestorepoint[diskname] = None
                restorepoint_details = self.get_restorepoints_by_jobid(job_obj, backup_method, custom_snapshotrg)
                if restorepoint_details:
                    consistency_mode = restorepoint_details['properties']['consistencyMode']
                    # Validating consistency mode for REstore point
                    self.validate_restorepoint_consistencymode(consistency_mode, _appconsistent_backup_enabled)

                    if custom_snapshotrg is not None:
                        self.log.info(
                            "Restore point is created in custom snapshot resource group: {0}".format(custom_snapshotrg))

                    # Checking os disk restore point
                    osdisk_name = restorepoint_details['properties']['sourceMetadata']['storageProfile']['osDisk'][
                        'name']
                    if osdisk_name in diskrestorepoint.keys():
                        diskrestorepoint[osdisk_name] = True
                    # Checking data disk restore points
                    datadisks_drp = restorepoint_details['properties']['sourceMetadata']['storageProfile']['dataDisks']
                    for each_drp in datadisks_drp:
                        if each_drp['name'] in diskrestorepoint.keys():
                            diskrestorepoint[each_drp.get('name')] = True

                    for each_disk in diskrestorepoint.keys():
                        if diskrestorepoint[each_disk] is None:
                            self.log.info("Disk restore point is not present for disk {0}".format(each_disk))
                            check_diskrestorepoints = False
                else:
                    check_diskrestorepoints = False
                    self.log.info("Restore point details not returned, "
                                  "Probably snapshot based backup or incorrect snapshot rg passed.")
            else:
                self.log.info("REstore points are not supported for unmanaged disks")
            return check_diskrestorepoints

        except Exception as exp:
            self.log.exception("Exception in validating disk restore point details")
            raise Exception("Exception in validating disk restore point:" + str(exp))

    def check_managed_disk_snapshots_by_jobid(self, job_obj, all_snap=False, snapshot_rg=None):
        """ Gets snapshots details associated with disks and a job id
        Args:
            job_obj (string): job obj for which snapshot has to be checked.
            all_snap (boolean): Whether return all snap details or beak if one snap exist
            snapshot_rg   (string): Optional, Value for custom Snapshot RG to fetch snapshots

        Return:
            snapshot_exists (boolean) : Whether snapshot exists or not
            snapshots (dictionary): dict of snapshots for that particular job

         Raises:
            Exception:
                When getting snapshot details failed
        """

        try:

            self.log.info("Getting snapshot details based on job id for job {0}".format(job_obj.job_id))
            disks = self.disk_dict
            snapshot_exists = False
            snapshots = {}
            self.log.info("Managed Disk...")
            for disk in disks:
                # diskname = disks[disk].split('/')[-1]
                snapshots[disk] = None
                if 'blob.core' in disks[disk]:
                    continue
                snaprg = disks[disk].split('/')[4] if not snapshot_rg else snapshot_rg
                azure_vmurl = AZURE_RESOURCE_MANAGER_URL + "/subscriptions/%s/resourceGroups" \
                                                           "/%s/providers/Microsoft.Compute/snapshots" % (
                              self.subscription_id, snaprg)
                api_version = '?api-version=2019-07-01'
                azure_snapurl = azure_vmurl + api_version
                response = self.azure_session.get(azure_snapurl, headers=self.default_headers, verify=False)
                if response.status_code == 200:
                    data = response.json()['value']
                    for snap in data:
                        if disks[disk] in snap['properties']['creationData']['sourceResourceId']:
                            if not snapshots[disk]:
                                snapshots[disk] = False
                            snap_jobid = self.get_snapshot_jobid(snap['id'])
                            if int(job_obj.job_id) == snap_jobid:
                                snapshots[disk] = True
                                snapshot_exists = True
                                self.log.info("Snapshot on disk {0} : {1}".format(disk, snap['id']))
                                if not all_snap:
                                    break

            if all_snap:
                snapshot_exists = True
                for disk in snapshots:
                    if not snapshots[disk]:
                        snapshot_exists = False
                        break
            return snapshot_exists, snapshots
        except Exception as exp:
            self.log.exception("Exception in getting snapshots on disks")
            raise Exception("Exception in getting snapshots on disks:" + str(exp))

    def check_unmanaged_disk_snapshots_by_jobid(self, job_obj, all_snap=False):
        """ Gets blob snapshots details associated with disks and a job id
        Args:
            job_obj (string): job obj for which snapshot has to be checked.
            all_snap (boolean): Whether return all snap details or beak if one snap exist

        Return:
            snapshot_exists (boolean) : Whether snapshot exists or not
            snapshots (dictionary): dict of snapshots for that particular job

         Raises:
            Exception:
                When getting snapshot details failed
        """

        try:
            self.log.info("Getting blob snapshot details based on job id for job {0}".format(job_obj.job_id))
            disks = self.disk_dict
            snapshot_exists = False
            snapshots = {}
            self.log.info("Unmanaged Disk...")
            destsnaps = self.get_snapshotsonblobs()
            startime = job_obj.start_time
            endtime = job_obj.end_time
            for disk in destsnaps:
                for each_disk, value in self.disk_dict.items():
                    if re.match(disk, value.split('/')[-1]):
                        diskname = each_disk
                        snapshots[diskname] = None
                        break
                snapshot_exists = self.check_snap_exist_intimeinterval(destsnaps[disk],
                                                                       startime, endtime)
                if snapshot_exists:
                    self.log.info("snap exists for "
                                  "job {0} on Blob {1} ".format(job_obj.job_id, disk))

                if not snapshot_exists:
                    self.log.info("Snapshot for Job {0} does not exist on blob {1} ".format(job_obj.job_id, disk))
                if not all_snap and snapshot_exists:
                    return snapshot_exists, snapshots
                elif snapshot_exists:
                    snapshots[diskname] = True
            if all_snap:
                snapshot_exists = True
                for disk in snapshots:
                    if not snapshots[disk]:
                        snapshot_exists = False
                        break
            return snapshot_exists, snapshots
        except Exception as exp:
            self.log.exception("Exception in getting snapshots on blobs")
            raise Exception("Exception in getting snapshots on blobs:" + str(exp))

    def validate_cbt_snapshots(self, prev_full_bkp_job_obj, backupmethod, snapshot_rg=None, appConsistentBackup=False):
        """
        Checks if previous full backup job's snapshot/restore point is deleted after incremental job

        Args:
            prev_full_bkp_job_obj  (Job object):   previous job's object
            backupmethod                 (string):   Backup method(streaming/snap) of the job
            snapshot_rg                 (string):   Custom snapshot rg(Optional)
            appConsistentBackup        (Boolean):   Set to True if App consistent is enabled in subclient
                                                    (default : False for Azure)
        Returns:
              Raise exception if previous snapshot exists
        """
        try:

            if appConsistentBackup and self.managed_disk:
                snap_exists = self.get_restorepoints_by_jobid(prev_full_bkp_job_obj, backupmethod, snapshot_rg)
            else:
                snap_exists = self.check_disk_snapshots_by_jobid(prev_full_bkp_job_obj, snapshot_rg)[0]

            if snap_exists:
                self.log.error(
                    "Snapshot/Restore point for previous full job exists after the Incremental job "
                    "for job {0}".format(prev_full_bkp_job_obj.jobid))
                raise Exception(
                    "Snapshot/Restore point for previous full job exists after the Incremental job")
            else:
                self.log.info("Previous incremental Snapshot/Restore point is not present in Portal for VM: {0}".format(
                    self.vm_name))

        except Exception as exp:
            self.log.exception("Exception in getting Snapshot/Restore point details")
            raise Exception("Exception in getting Snapshot/Restore point details : " + str(exp))
