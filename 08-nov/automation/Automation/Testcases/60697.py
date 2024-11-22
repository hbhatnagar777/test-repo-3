# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HSX Ransomware Protection Enablement
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    cleanup()                       --  Cleans up the test case resources and directories

    tear_down()                     --  Tear down function of this test case
      
    fail_test_case()                --  Prints failure reason, sets the result string

    create_test_data()              --  Creates the test data with content_gb size at given path

    initialize_mm_entities()        --  Initializes the various Media Management entities, if needed

    run()                           --  run function of this test case
      

Sample input json
"60697": {
            "Nodes": [
                None,
                None,
                None
            ],
            "NodeUser": None,
            "NodePassword": None,
            "SqlLogin": None, (OPTIONAL)
            "SqlPassword": None, (OPTIONAL)
            "ResetRwp": None (OPTIONAL) (Default False)
        }

"""

from typing import Dict

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.unix_ransomware_helper import UnixRansomwareHelper

class TestCase(CVTestCase):
    """Hyperscale test class for HSX Ransomware Protection Enablement"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX Ransomware Protection Enablement"
        self.result_string = ""
        self.backupset_obj = ""
        self.subclient_obj = ""
        self.client = ""
        self.subclient_name = ""
        self.storage_policy = ""
        self.client_name = ""
        self.mas = []
        self.storage_pool_name = ""
        self.storage_policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.tcinputs = {
            "Nodes": [
            ],
            "NodeUser": None,
            "NodePassword": None,
            # "ResetRwp": None (OPTIONAL) (Default False)
        }
        self.reset_rwp = False
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)

        # MA setup
        self.node_user = self.tcinputs["NodeUser"]
        self.node_password = self.tcinputs["NodePassword"]
        self.mas = self.tcinputs["Nodes"]
        self.ma_machines: Dict[str, UnixMachine] = {}
        self.rw_helpers: Dict[str, UnixRansomwareHelper] = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.node_user, password=self.node_password)
            self.ma_machines[ma_name] = machine
            self.rw_helpers[ma_name] = UnixRansomwareHelper(machine, self.commcell, self.log)

        # Subclient & Storage setup
        self.storage_pool_name = None
        self.policy = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        ma_short_name = self.mas[0].split(".", 1)[0]
        prefix = f"{self.id}_{ma_short_name}_"
        self.backupset_name = f"{prefix}backupset"
        self.subclient_name = f"{prefix}subclient"
        self.storage_policy_name = f"{prefix}policy"
        self.mmhelper_obj = MMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.content_gb = 1
        self.drive = self.options_selector.get_drive(self.client_machine, 2*self.content_gb*1024)

        # Backup and restore paths
        self.test_case_path = self.client_machine.join_path(self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(self.test_case_path, "Testdata")
        self.content_path = self.client_machine.join_path(self.test_data_path, f"Data-{self.content_gb}Gb")
        # looks like C:\\Automation\\60697\\Testdata\\Data-1Gb
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')
        self.restore_path = self.client_machine.join_path(self.restore_data_path, f"Data-{self.content_gb}Gb")

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        # Cleanup required or not
        self.reset_rwp = self.tcinputs.get("ResetRwp",False)

    def cleanup(self):
        """Cleans up the directories, test case resources and resets ransomware protection"""
        
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
        
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.storage_policy_name)
        
        
        for ma in self.mas:
            if not self.rw_helpers[ma].validate_sestatus_when_rwp_disabled():
                self.rw_helpers[ma].pause_protection()
                self.log.info(f"Paused protection for {ma}")
                self.rw_helpers[ma].disable_selinux()
                self.log.info(f"Disabled selinux for {ma}")
            else:
                self.log.info(f"Ransomware disabled for {ma}")

        for ma in self.mas:
            self.rw_helpers[ma].delete_registry_entries()
            self.log.info(f"Deleted regkeys for {ma}")

        for ma in self.mas:
            self.rw_helpers[ma].restore_fstab(self.id)
            self.log.info(f"Restored fstab for {ma}")
        
        # Delete this directory only after restoring fstab
        # because it contains the original backed up fstab file

        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful and self.reset_rwp:
            self.log.info(f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})")
            self.cleanup()
        elif self.successful:
            self.log.info(f"Test case successful")
        else:
            self.log.warning("Not cleaning up as the run was not successful")
            self.status = constants.FAILED
   
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason
    
    def create_test_data(self, path, content_gb):
        """Creates the test data with content_gb size at given path

            Args:

                path        (str)   -- The path where data is to be created

                content_gb  (int)   -- The size of the data in gb

            Returns:

                result      (bool)  -- If data got created

        """
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
        self.client_machine.create_directory(path)
        result = self.mmhelper_obj.create_uncompressable_data(self.client_name, path, content_gb)
        if not result:
            return False
        return True
    
    def initialize_mm_entities(self):
        """
        Initializes the various Media Management entities, if needed
        """
        if self.storage_pool_name is None:
                self.storage_pool_name = self.hyperscale_helper.get_storage_pool_from_media_agents(self.mas)
        
        if self.policy is None:
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.mas[0], self.storage_policy_name)
        
        if self.backupset_obj is None:
            self.backupset_obj = self.mmhelper_obj.configure_backupset()
        
        if self.subclient_obj is None:
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
    
    def run(self):
        """ run function of this test case"""
        try: 

            # 0. Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()

            # 1. Check if storage pool exists over the nodes
            self.log.info(f"Checking if storage pool exists over the nodes: {self.mas}")
            self.storage_pool_name = self.hyperscale_helper.get_storage_pool_from_media_agents(self.mas)
            if not self.storage_pool_name:
                reason = f"Unable to find storage pool over the nodes"
                return self.fail_test_case(reason)
            self.log.info(f"Found the storage pool: {self.storage_pool_name}")

            # 2. Check if rwp is disabled on all nodes
            self.log.info(f"Checking if ransomware protection is disabled on all nodes")
            for ma in self.mas:
                if self.rw_helpers[ma].ransomware_protection_status():
                    reason = f"Ransomware already enabled on {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"Ransomware disabled on all nodes")

            # 3. Check if sRestartCVSecurity should either not exist or set to No
            reg_key = 'sRestartCVSecurity'
            self.log.info(f"Checking if {reg_key} should either not exist or set to No")
            result, identical = self.hyperscale_helper.get_reg_key_values(self.mas, self.ma_machines, [reg_key])
            for value in result[reg_key]:
                if value is None or value == "No":
                    continue
                reason = f"{reg_key} value is {value} instead of None or No"
                return self.fail_test_case(reason)
            self.log.info(f"{reg_key} is either absent or set to No on all nodes")

            # 4. Take a backup before enabling protection
            # 4a. Create test data
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")
            
            # 4b. Initiate backup
            self.initialize_mm_entities()
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed with reason {job_obj.delay_reason}"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            # 5. Enable protection
            # 5a. Backup fstab file
            for ma in self.mas:
                result = self.rw_helpers[ma].backup_fstab(self.id)
                if not result:
                    reason = f"Please fix fstab file on {ma} and rerun the case"
                    return self.fail_test_case(reason)
                self.log.info(f"Backed up fstab on {ma}")
            
            # 5b. Fire the command
            self.log.info(f"Enabling protection on all nodes")
            for ma in self.mas:
                result = self.rw_helpers[ma].hsx_enable_protection(self.hyperscale_helper)
                if not result:
                    reason = f"Couldn't enable protection for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Enable protection successful for {ma}")
            
            # 6. validate sestatus output
            self.log.info(f"Validating sestatus output")
            for ma in self.mas:
                result = self.rw_helpers[ma].validate_sestatus_when_rwp_enabled()
                if not result:
                    reason = f"Failed to validate sestatus for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Validated sestatus for {ma} successfully")
            
            # 7. Check if commmvault and hedvig services are running
            # 7a. Commvault
            self.log.info("Checking if commvault services and processes are up")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(self.mas, self.ma_machines)
            if not result:
                reason = f"Failed to verify if commvault services or processes are up"
                return self.fail_test_case(reason)
            self.log.info("Commvault services and processes are up on all nodes")

            # 7b. Hedvig
            self.log.info("Checking if hedvig services are up")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(self.mas, self.ma_machines)
            if not result:
                reason = f"Failed to verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info("Hedvig services are up on all nodes")
            
            # 8. Validate if taggable script / binaries are running in right context
            # and the running processes having cvbackup_t are authentic
            self.log.info(f"Validating processes on the nodes")
            for ma in self.mas:
                result = self.rw_helpers[ma].hsx_validate_process_label()
                if not result:
                    reason = f"Failed to validate processes on {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully validated processes on {ma}")
            
            # 9. Check context on whitelisted binaries
            self.log.info("Checking context on whitelisted binaries")
            for ma in self.mas:
                result = self.rw_helpers[ma].hsx_validate_context_on_whitelisted_binaries()
                if not result:
                    reason = f"Failed to validate context on whitelisted binaries for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully validated context on whitelisted binaries for {ma}")
            
            # 10. Verify MA registries
            self.log.info("Verifying MA registries")
            expected_protected_mountpaths, reason = UnixRansomwareHelper.hsx_get_expected_protected_mountpaths(self.hyperscale_helper, self.mas, self.ma_machines)
            if not expected_protected_mountpaths:
                return self.fail_test_case(reason)
            result = UnixRansomwareHelper.hsx_validate_registry_entries(self.hyperscale_helper, self.mas, self.ma_machines, expected_protected_mountpaths)
            if not result:
                reason = f"Failed to verify MA registries"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified MA registries for MAs")

            # 11. Check fstab for drive context
            self.log.info("Checking fstab for drive context")
            expected_protected_mountpaths, reason = UnixRansomwareHelper.hsx_get_expected_protected_mountpaths(self.hyperscale_helper, self.mas, self.ma_machines)
            if not expected_protected_mountpaths:
                return self.fail_test_case(reason)
            identical, product_version = self.hyperscale_helper.verify_sp_version_for_media_agents(self.ma_machines)
            if not identical: 
                reason = f"MAs does not have identical versions"
                return self.fail_test_case(reason)
            product_version = product_version[self.mas[0]][0]
            for ma in self.mas:
                result = self.rw_helpers[ma].hsx_validate_fstab(expected_protected_mountpaths, product_version)
                if not result:
                    reason = f"Failed to validate fstab for drive context for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully validated fstab for drive context for {ma}")
            
            # 12. Check protected mount paths
            # 12a. Check whether protected mount paths are mounted
            self.log.info("Checking whether protected mount paths are mounted")
            for ma in self.mas:
                result = self.rw_helpers[ma].hsx_validate_protected_mount_paths_mounted(self.hyperscale_helper)
                if not result:
                    reason = f"Failed to validate whether protected mount paths are mounted for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully validated whether protected mount paths are mounted for {ma}")
            
            # 12b. Check context on protected mount paths
            self.log.info("Checking context on protected mount paths")
            for ma in self.mas:
                result = self.rw_helpers[ma].hsx_validate_context_on_protected_mount_paths()
                if not result:
                    reason = f"Failed to validate context on protected mount paths for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully validated context on protected mount paths for {ma}")
            
            # 13. Check append / write / delete on mount path
            self.log.info("Checking append / write / delete on mount path")
            for ma in self.mas:
                paths = self.rw_helpers[ma].hsx_get_protected_mountpaths()
                for path in paths:
                    result = self.rw_helpers[ma].hyperscale_validate_mountpath_protected(path, self.id)
                    if not result:
                        reason = f"Failed to validate append / write / delete on mount path {path} for {ma}"
                        return self.fail_test_case(reason)
                    self.log.info(f"Successfully validated append / write / delete on mount path {path} for {ma}")
            
            # 14. Perform restore here
            self.log.info("Performing Restore")
            self.initialize_mm_entities()
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)
            
            # 24. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

            self.successful = True
            self.log.info(f"Ransomware protection enablement successful with all verifications")

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
