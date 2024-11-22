from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Hyperscale test class for File System Backup/Restore validations"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX 3.x File System Backup/Restore validations"
        self.result_string = ""
        self.mas = []
        self.hyperscale_helper = None
        self.tcinputs = {
            "Nodes": [
            ]
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""

        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.tcinputs["Client_name"]
        self.client_machine = Machine(self.client_name, self.commcell)
        
        # MA setup
        self.mas = self.tcinputs["Nodes"]
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")

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
        
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')
        self.restore_path = self.client_machine.join_path(self.restore_data_path, f"Data-{self.content_gb}Gb")

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def cleanup_test_data(self):
        """Clears the test data directory
        """
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

    def cleanup(self):
        """Cleans up the test case resources and directories"""
        
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
        
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.get(self.storage_policy_name).reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.storage_policy_name)

        self.cleanup_test_data()

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
        if self.successful:
            self.log.info(f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})")
            self.cleanup()
        else:
            self.log.warning("Not cleaning up as the run was not successful")
            self.status = constants.FAILED

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


    def backup_and_restore(self):
        """Runs backup and restore jobs and reports whether successful or failed

        Returns:
            
            result, reason          (bool)      --  True if backup and restore completes successfully
                                                    Else False and reason of failure

        """


        # 1. Take full backup
        # 1a. Create test data
        result = self.create_test_data(self.content_path, self.content_gb)
        if not result:
            reason = f"Error while creating test data"
            self.log.error(reason)
            return False, reason
        self.log.info("Created test data")

        # 1b. Initiate backup
        self.initialize_mm_entities()
        job_obj = self.subclient_obj.backup("FULL")
        self.log.info(f"Starting backup job [{job_obj.job_id}]")
        if not job_obj.wait_for_completion():
            reason = f"Backup job [{job_obj.job_id}] has failed with reason {job_obj.delay_reason}"
            self.log.error(reason)
            return False, reason
        self.log.info(f"Backup succeeded. Job status {job_obj.status}")

        # 2. Perform restore
        self.log.info("Performing Restore")
        self.initialize_mm_entities()
        job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
        if not job_obj.wait_for_completion():
            reason = f"Restore job has failed {job_obj.pending_reason}"
            self.log.error(reason)
            return False, reason
        self.log.info("Restore job succeeded. Job status %s", job_obj.status)

        # 3. Verify the restored data
        self.log.info("Verifying the restored data")
        self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

        return True, None


    def run(self):
        """ run function of this test case"""
        try: 
            
            # 0. Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()

            # 1. Perform backup and restore and validate the restored data
            self.log.info(f"Validating backup and restore")
            result, reason = self.backup_and_restore()
            if not result:
                reason += f"Backup and restore failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup and restore validated")

            self.successful = True
            self.log.info(f"File system backup and restore validated successfully")


        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)