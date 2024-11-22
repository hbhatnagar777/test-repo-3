# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case

    set_db_path()       --  sets the Data Classification DB path for the drive

    delete_dc_db()      --  Deletes the Data Classification DB

    is_dc_db_created()  --  Checks if the Data Classification DB is exists

    is_db_updated()     --  verifies that new contents are added Data Classification DB

"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_CONFIG_REGKEY, WIN_DATA_CLASSIFIER_BASE_PATH
from FileSystem.FSUtils.fshelper import ScanType

"""
Example Json-
        "59159": {
                                    "AgentName": "",
                                    "ClientName": "",
                                    "TestPath": "",
                                    "StoragePolicyName": "",
                                    "CleanupRun":						
                    },


"""
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
        self.name = "Data Classification DB creation and content population for a new volume"
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.client_machine = None
        self.helper = None
        self.drive_letter = None
        self.db_path = None
        self.operation_selector = None
        self.test_directory = None
        self.cleanup_run = None

    def setup(self):
        """Setup function of this test case"""
        self.helper = WinFSHelper(self)
        self.client_machine = Machine(self.client)
        self.operation_selector = OptionsSelector(self.commcell)

    def set_db_path(self):
        """Sets Db path for the self.drive_letter volume."""
        client_instance = self.client_machine.instance.split("Instance")[1]
        db_parent_path = self.drive_letter + WIN_DATA_CLASSIFIER_BASE_PATH
        self.db_path = self.client_machine.join_path(db_parent_path, f"dc_{client_instance}.db")

    def delete_dc_db(self):
        """Deletes the DC DB"""

        guid_path = self.client_machine.join_path(WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                  self.helper.get_volume_guid(drive_letter=self.drive_letter[0]))

        # if the key does not exists create one otherwise update its value to 0
        if not self.client_machine.check_file_exists(self.db_path):
            self.log.info("DC DB does not exists. Skipping DC DB deletion operation.")
            return

        self.log.info("Updating Registry keys and Restarting CommVault Services")

        self.client_machine.update_registry(key="Cvd",
                                                value="nStartDataClassifier",
                                                data=0,
                                                reg_type="DWord")
        self.client.restart_services()
        temp = 0
        while(temp<10):
            try:
                self.client_machine = Machine(self.client)
            except Exception:
                temp = temp+1
                continue
            else:
                break

        self.log.info("Restarted CommVault Services")

        self.client_machine.delete_file(self.db_path)

        self.log.info("Removing guid Reg. Key path [%s]]", guid_path)
        if self.client_machine.check_registry_exists(key=guid_path):
            self.client_machine.remove_registry(key=guid_path)

        self.log.info("Updating Registry keys and restarting services")
        self.client_machine.remove_registry(key="Cvd", value="nStartDataClassifier")
        self.client.restart_services()
        temp1 = 0
        while (temp1 < 10):
            try:
                self.client_machine = Machine(self.client)
            except Exception:
                temp1 = temp1 + 1
                continue
            else:
                break
        self.log.info("Successfully completed: DC DB delete operation")

    def is_dc_db_created(self):
        """
            Checks if DC DB created or not

            Raises:
                Exception - if DC DB is not created
        """
        self.log.info("Checking if DC DB created")
        if self.client_machine.check_file_exists(self.db_path):
            self.log.info("The DC DB is created successfully after backup job")
        else:
            raise Exception("Failed to re-create the DC DB job during Backup job")

    def is_db_updated(self, job):
        """
            Checks if DC DB is updated or not
            Args:
                job     (str)   --  job ID of recent backup

            Raises:
                Exception - If DC DB is not updated
        """
        self.log.info("Checking if DC DB updated with new content")
        result = self.helper.get_no_of_qualified_objects_from_filescan(job)
        if result and int(result['total']) > 0:
            self.log.info("New contents are updated in DC DB")
        else:
            raise Exception("Failed to update new contents in DC DB")

    def run(self):
        """Run function of this test case"""
        try:
            # save drive letter for content
            # and set db_path that drive
            self.helper.populate_tc_inputs(self)
            self.drive_letter = self.operation_selector.get_drive(self.client_machine)
            self.test_directory = self.client_machine.join_path(self.drive_letter, "TestData_DB_POP_CHECK")
            if not self.client_machine.check_directory_exists(directory_path=self.test_directory):
                self.client_machine.create_directory(directory_name=self.test_directory)
            if not self.client_machine.generate_test_data(file_path=self.test_directory,
                                                          dirs=1,
                                                          files=100):
                raise Exception("Failed to generate Test Data")

            self.set_db_path()

            # Deleting the DC DB
            self.delete_dc_db()

            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            # setting subclient content
            subclient_content = [self.test_directory]
            self.helper.create_subclient(name="subclient59159",
                                         storage_policy=self.storage_policy,
                                         content=subclient_content,
                                         scan_type=ScanType.OPTIMIZED)

            # Run FULL backup
            self.log.info("Running Full backup job on subclient [%s]", self.subclient.subclient_name)
            self.helper.run_backup(backup_level="Full")

            # --------------
            # Check if DB created or not?
            self.is_dc_db_created()

            # Delete the DC DB
            self.delete_dc_db()

            # Adding new content to path
            self.log.info("Adding New files to content path")
            new_path = self.client_machine.join_path(self.test_directory, "NewContent.txt")
            self.client_machine.create_file(file_path=new_path,
                                            content="New Content Added before INCR job")
            self.log.info("Successfully added New files to content path")

            # Run INCREMENTAL job
            self.log.info("Running Incremental backup job on subclient [%s]", self.subclient.subclient_name)
            job = self.helper.run_backup()

            # Ensure the DC DB is created and new contents are added
            self.is_dc_db_created()
            self.is_db_updated(job[0])

            self.client_machine.remove_directory(self.test_directory)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.client_machine.remove_directory(self.test_directory)
