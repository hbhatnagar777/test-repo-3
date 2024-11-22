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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    update_reg_keys() --  Updates 'DatabaseRebuildControl' registry key

"""

import time
from datetime import datetime
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_CONFIG_REGKEY, WIN_DATA_CLASSIFIER_STATUS_REGKEY
from FileSystem.FSUtils.fshelper import ScanType

"""
Example-
    "59160": {
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
        self.name = "Verifying DatabaseRebuildControl Reg. key. for given drive"
        self.client_machine = None
        self.helper = None
        self.storage_policy = None
        self.option_selector = None
        self.drive_letter = None
        self.test_directory = None
        self.backupset_name = None
        self.is_client_big_data_apps = None
        self.cleanup_run = None
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client)
        self.helper = WinFSHelper(self)
        self.option_selector = OptionsSelector(self.commcell)

    def update_reg_keys(self):
        """
            Updates registry keys on client machine
        """
        volume_guid = self.helper.get_volume_guid(drive_letter=self.drive_letter[0])
        guid_path = self.client_machine.join_path(WIN_DATA_CLASSIFIER_CONFIG_REGKEY, volume_guid)

        if not self.client_machine.check_registry_exists(key=guid_path):
            self.client_machine.create_registry(key=guid_path,
                                                value=None,
                                                data=None,
                                                reg_type='String')

        self.client_machine.create_registry(key=guid_path,
                                            value="DatabaseRebuildControl",
                                            data=3,
                                            reg_type="DWord")

    def run(self):
        """Run function of this test case"""
        try:
            self.helper.populate_tc_inputs(self)

            # updating content and reg keys
            self.log.info("creating testdata, updating registry keys and restarting services")
            self.drive_letter = self.option_selector.get_drive(self.client_machine)
            self.test_directory = self.client_machine.join_path(self.drive_letter, "TestData_DatabaseRebuildControl")
            if not self.client_machine.check_directory_exists(directory_path=self.test_directory):
                self.client_machine.create_directory(directory_name=self.test_directory)
            self.client_machine.generate_test_data(file_path=self.test_directory,
                                                   dirs=2,
                                                   files=1000)

            if self.client_machine.check_registry_exists(key="Cvd", value="nStartDataClassifier"):
                self.client_machine.remove_registry(key="Cvd",
                                                    value="nStartDataClassifier")

            if self.client_machine.check_registry_exists(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY, value="ServiceEnabled"):
                self.client_machine.remove_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                    value="ServiceEnabled")

            self.client.restart_service()

            #backup set

            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            # setting subclient content
            subclient_content = [self.test_directory]
            self.helper.create_subclient(name="subclient59160",
                                         storage_policy=self.storage_policy,
                                         content=subclient_content,
                                         scan_type=ScanType.OPTIMIZED)


            # Run an INCR job
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            self.helper.run_backup()

            # Updating Reg keys.
            time_1 = datetime.now()
            self.log.info("Updating reg. key DatabaseRebuildControl")
            self.update_reg_keys()
            time.sleep(300)

            # Run an INCR job
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup()[0]

            volume_guid = self.helper.get_volume_guid(drive_letter=self.drive_letter[0])
            reg_key = self.client_machine.join_path(WIN_DATA_CLASSIFIER_STATUS_REGKEY,
                                                    volume_guid)
            reg_key_data = self.client_machine.get_registry_value(commvault_key=reg_key,
                                                                  value="StartTime")
            time_2 = datetime.fromtimestamp(int(reg_key_data))

            # verifying DatabaseRebuildControl reg. key effects
            self.log.info("Checking if Database is rebuild triggered.")
            if time_1 < time_2:
                self.log.info("Database Rebuild Triggered")
            else:
                self.log.info("Failed to trigger Database Rebuild")
                raise Exception("Failed to trigger DB Rebuild")

            # checking the type of Scan method Used for INCR backup
            scan_type = self.helper.verify_scan_type_used(job_id=job.job_id)
            if not scan_type:
                raise Exception("Unable to Detect Job Scan type")

            self.log.info("ScanType used is [%s]", scan_type)
            if "DATACLASSIFIER" not in scan_type:
                raise Exception("DATACLASSIFIER Scan Type is not used. Implies DC DB not available/healthy.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Removes the created test directory"""
        self.client_machine.remove_directory(self.test_directory)
