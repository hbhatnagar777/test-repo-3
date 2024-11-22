# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HSX Ransomware Protection Validation + Backup
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    cleanup()                       --  Cleans up the test case resources and directories

    tear_down()                     --  Tear down function of this test case
      
    fail_test_case()                --  Prints failure reason, sets the result string

    initialize_mm_entities()        --  Initializes the various Media Management entities, if needed

    run()                           --  run function of this test case
      

Sample input json
"63219": {
            "Nodes": [
              "ma_name_1",
              "ma_name_2",
              "ma_name_3"
            ],
            "NodeUser": "user",
            "NodePassword": "password",
            "ClientName": "clientname" (OPTIONAL)
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
    """Hyperscale test class for HSX Ransomware Protection Validation + Backup"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX Ransomware Protection Validation + Backup"
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
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        
        self.client_name = self.tcinputs.get('ClientName', self.commcell.commserv_name)
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
        # looks like C:\\Automation\\63219\\Testdata\\Data-1Gb
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')
        self.restore_path = self.client_machine.join_path(self.restore_data_path, f"Data-{self.content_gb}Gb")

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def cleanup(self):
        """Cleans up the directories, test case resources and resets ransomware protection"""
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")
        
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
        
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.storage_policy_name)
        
        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})")
            self.cleanup()
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

            # 2. Check if rwp is enabled on all nodes
            self.log.info(f"Checking if ransomware protection is enabled on all nodes")
            for ma in self.mas:
                if not self.rw_helpers[ma].ransomware_protection_status():
                    reason = f"Ransomware protection disabled on {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"Ransomware protection enabled on all nodes")

            # 3. Run the validation suite
            self.log.info(f"Running ransomware protection validation suite")
            result = UnixRansomwareHelper.hsx_rwp_validation_suite(self.mas, self.ma_machines, self.hyperscale_helper, self.rw_helpers)
            if not result:
                reason = "Failed to validate ransomware protection"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified ransomware protection")

            # 4. Take a backup after validation
            # 4a. Create test data
            result = self.options_selector.create_uncompressable_data(self.client_name, self.content_path, self.content_gb, delete_existing=True)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")
            
            # 4b. Initiate backup
            self.initialize_mm_entities()
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed with reason: {job_obj.delay_reason}"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")                       
                        
            # 5. Perform restore here
            self.log.info("Performing Restore")
            self.initialize_mm_entities()
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)
            
            # 6. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

            self.successful = True
            self.log.info(f"Ransomware protection validation successful")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
