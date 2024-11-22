# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import re
import time

from Automation.AutomationUtils.cvtestcase import CVTestCase
from Automation.VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from Automation.AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "VSA Azure Best Effort Restore"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False

        self.auto_subclient = None
        self.azure_proxy_name = None
        self.azure_hypervisor = None
        self.azure_proxy_machine_obj = None
        self.registry_keys = None
        self.registry_keys_path = None
        self.log_file_name = None
        self.managed_disk_regex_pattern = None
        self.disk_uri_template = None
        self.unmanaged_disk_regex_pattern = None
        self.blob_uri_template = None
        self.managed_disk_search_term = None
        self.unmanaged_disk_search_term = None
        self.managed_disks = None
        self.unmanaged_disks = None
        self.azure_subscription_id = None
        self.vm_restore_job_id = None

        self.tcinputs = {
            "InstanceName": None,  # Azure Resource Manager
            "AgentName": None,  # Virtual Server
            "ClientName": None,  # Hypervisor
            "BackupsetName": None,  # defaultBackupSet
            "SubclientName": None,  # VM Group
            "BackupType": None,
            "Resourcegroup": None,
            "ResourcegroupLocked": None,  # Resource Group with Read-Only Lock
            "Storageaccount": None
        }

    def setup(self):
        try:
            # bEnableBestEffortRestore is enabled by default, but still settings its value to 1
            self.registry_keys = ["bEnableBestEffortRestore", "bAzureInjectVMCreationFailure"]
            self.registry_keys_path = 'VirtualServer'
            self.log_file_name = 'vsrst.log'
            self.managed_disk_regex_pattern = r"\[[^\]]+\[([^\]]+)\].*\[([^\]]+)\]\]"
            self.managed_disk_search_term = "Restored managed disk"
            self.disk_uri_template = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/disks/{}"
            self.unmanaged_disk_regex_pattern = r"\[([^\]]+)\].*\[([^\]]+)\]\[([^\]]+)\]"
            self.unmanaged_disk_search_term = "Creating Blob"
            self.blob_uri_template = "https://{}.blob.core.windows.net/{}/{}"

            self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
            self.azure_proxy_name = self.auto_subclient.auto_vsainstance.proxy_list[0]
            self.azure_hypervisor = self.auto_subclient.hvobj
            self.azure_subscription_id = self.azure_hypervisor.subscription_id

            self.azure_proxy_machine_obj = Machine(
                machine_name=self.azure_proxy_name,
                commcell_object=self.commcell
            )

        except Exception as exp:
            self.log.error('Setup failed with error')
            self.log.exception(exp)

    def set_registry_keys(self):
        VirtualServerUtils.decorative_log(f"Setting {self.registry_keys} Registry Keys")

        try:
            for registry_key in self.registry_keys:
                # Check if registry key already exists
                if self.azure_proxy_machine_obj.check_registry_exists(self.registry_keys_path, registry_key):
                    # Set the value as 1 for true
                    self.azure_proxy_machine_obj.update_registry(
                        key=self.registry_keys_path,
                        value=registry_key,
                        data='1',
                        reg_type='String'
                    )
                    self.log.info(f"{registry_key} registry key already exists, set it's value to 1")
                else:
                    # Create the key and set the value as 1
                    self.azure_proxy_machine_obj.create_registry(
                        key=self.registry_keys_path,
                        value=registry_key,
                        data='1',
                        reg_type='String'
                    )
                    self.log.info(f"Created {registry_key} registry key and set it's value to 1")
        except Exception as exp:
            self.log.exception(exp)
            raise Exception("Unable to Set Registry Keys")

    def run_backup(self):
        VirtualServerUtils.decorative_log("Running Backup")

        backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
        backup_options.backup_type = self.tcinputs["BackupType"]
        self.auto_subclient.backup(backup_options)
        self.auto_subclient.post_backup_validation(validate_workload=False, skip_snapshot_validation=False)

    def run_vm_restore(self, **kwargs):
        VirtualServerUtils.decorative_log("Running Full VM Out of Place Restore")

        vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_subclient, self)
        vm_restore_options.unconditional_overwrite = True
        vm_restore_options.power_on_after_restore = True

        if kwargs.get("use_locked_rg"):
            # Use a Resource Group with Read-Only Lock to prevent blobs from getting converted to managed disks
            vm_restore_options.Resource_Group = self.tcinputs["ResourcegroupLocked"]

        try:
            self.auto_subclient.virtual_machine_restore(vm_restore_options)
        except Exception as exp:
            pass

        vm_restore_job = vm_restore_options.restore_job
        self.vm_restore_job_id = vm_restore_job.job_id

        self.log.info(f"Restore Job ID = {self.vm_restore_job_id}")

        restore_failed_vm_list = [(self.auto_subclient.vm_restore_prefix + vm_name) for vm_name in
                                  self.auto_subclient.vm_list]
        self.log.info(f"Restore Failed VM List = {restore_failed_vm_list}")

        if "one or more errors" not in vm_restore_job.status:
            raise Exception("VM Creation Did Not Fail")

        self.log.info("VM Creation Failed")

    def check_restored_managed_disks_retained(self):
        VirtualServerUtils.decorative_log("Getting Managed Disk names from Restore Job Log File")

        managed_disk_log_lines = self.azure_proxy_machine_obj.get_logs_for_job_from_file(
            job_id=self.vm_restore_job_id,
            log_file_name=self.log_file_name,
            search_term=self.managed_disk_search_term
        )

        # Has "disk name" and "resource group"
        self.managed_disks = re.findall(self.managed_disk_regex_pattern, managed_disk_log_lines)
        self.log.info(f"Managed Disks = {self.managed_disks}")

        VirtualServerUtils.decorative_log("Checking if Restored Managed Disks are Retained")

        for disk_name, resource_group in self.managed_disks:
            disk_uri = self.disk_uri_template.format(self.azure_subscription_id, resource_group, disk_name)

            if not self.azure_hypervisor.check_disk_exists_in_resource_group(disk_uri):
                raise Exception(
                    f"Managed Disk {disk_name} in Resource Group {resource_group} not retained after VM Creation Failure")

        self.log.info("All Restored Managed Disks are Retained")

    def check_restored_unmanaged_disks_retained(self):
        VirtualServerUtils.decorative_log("Getting Unmanaged Disk names from Restore Job Log File")

        unmanaged_disk_log_lines = self.azure_proxy_machine_obj.get_logs_for_job_from_file(
            job_id=self.vm_restore_job_id,
            log_file_name=self.log_file_name,
            search_term=self.unmanaged_disk_search_term
        )

        # Has "disk name", "storage account", and "container" or (path)
        self.unmanaged_disks = re.findall(self.unmanaged_disk_regex_pattern, unmanaged_disk_log_lines)
        self.log.info(f"Unmanaged Disks = {self.unmanaged_disks}")

        VirtualServerUtils.decorative_log("Checking if Restored Unmanaged Disks are Retained")

        for disk_name, storage_account, path in self.unmanaged_disks:
            blob_uri = self.blob_uri_template.format(storage_account, path, disk_name)

            if not self.azure_hypervisor.check_blob_exists_in_storage_account(blob_uri):
                raise Exception(f"Unmanaged Disk {disk_name} in Storage Account [{storage_account}][{path}] not retained after VM Creation Failure")

        self.log.info("All Restored Unmanaged Disks are Retained")

    def run(self):
        """Run function of this test case"""
        try:
            self.set_registry_keys()
            self.run_backup()
            self.run_vm_restore()
            self.check_restored_managed_disks_retained()
            self.run_vm_restore(use_locked_rg=True)
            self.check_restored_unmanaged_disks_retained()
        except Exception as exp:
            self.log.error('Testcase failed with error')
            self.log.exception(exp)

    def remove_registry_keys(self):
        VirtualServerUtils.decorative_log("Removing Registry Keys")

        for registry_key in self.registry_keys:
            # Check if registry key exists
            if self.azure_proxy_machine_obj.check_registry_exists(self.registry_keys_path, registry_key):
                # Remove the registry key
                self.azure_proxy_machine_obj.remove_registry(
                    key=self.registry_keys_path,
                    value=registry_key
                )
                self.log.info(f"{registry_key} registry key removed")

    def tear_down(self):
        # Remove the registry keys
        if self.azure_proxy_machine_obj:
            self.remove_registry_keys()

        # Clean up Managed and Unmanaged disks that got created during the restore
        if self.managed_disks:
            VirtualServerUtils.decorative_log("Deleting Managed Disks")

            for disk_name, resource_group in self.managed_disks:
                self.azure_hypervisor.delete_disk(disk_name=disk_name, resource_group=resource_group)

        if self.unmanaged_disks:
            VirtualServerUtils.decorative_log("Deleting Unmanaged Disks")

            for disk_name, storage_account, path in self.unmanaged_disks:
                self.azure_hypervisor.delete_disk(disk_name=disk_name, storage_account=storage_account, path=path)
