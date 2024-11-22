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

    create_data_and_update_client() --  Creates data and updates subclient content

"""

import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.winfshelper import FSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_CONFIG_REGKEY


class TestCase(CVTestCase):
    """Class for executing this test case
        This testcase does the following:
            1. Runs a INCR backup
            2. Sets Reg. key. "VolumeFilters"
            3. Again runs an INCR
            4. Verifies the scan type used.
    """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Verifying_VolumeFilters_RegKey"
        self.client_machine = None
        self.helper = None
        self.option_selector = None
        self.drive_letter = None
        self.test_directory = None
        self.tcinputs = {

        }

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client)
        self.helper = FSHelper(self)
        self.option_selector = OptionsSelector(self.commcell)

    def create_data_and_update_client(self):
        """
            Creates test data and updates subclient contents
        """
        self.log.info("creating testdata")
        self.drive_letter = self.option_selector.get_drive(self.client_machine)
        self.test_directory = self.client_machine.join_path(self.drive_letter, f"TestData_{self.name}")
        if not self.client_machine.check_directory_exists(directory_path=self.test_directory):
            self.client_machine.create_directory(directory_name=self.test_directory)

        self.client_machine.generate_test_data(file_path=self.test_directory,
                                               dirs=2,
                                               files=100)

        # setting subclient content
        self.subclient.content = [self.test_directory]

    def run(self):
        """Run function of this test case"""
        try:
            # generate data and update subclient content
            self.create_data_and_update_client()

            # Run an INCR job
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            self.helper.run_backup()

            # Updating Reg keys.
            self.log.info("Updating reg. keys: VolumeFilters")
            if self.client_machine.check_registry_exists(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                         value="VolumeFilters"):
                self.client_machine.update_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                    value="VolumeFilters",
                                                    data=self.drive_letter,
                                                    reg_type="REG_MULTI_SZ")
            else:
                self.client_machine.create_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                    value="VolumeFilters",
                                                    data=self.drive_letter,
                                                    reg_type="REG_MULTI_SZ")

            # Run an INCR job
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup()[0]

            # Verifying that scan type used is Recursive
            scan_type = self.helper.verify_scan_type_used(job.job_id)
            if not scan_type:
                raise Exception("Not Able to Verify Scan Type")

            self.log.info("ScanType used is [%s]", scan_type)
            classic = re.search("CLASSIC", scan_type)
            if classic:
                self.log.info(f"{classic[0]} Scan Type is used. "
                              f"Implies DC DB not available/healthy for {self.drive_letter} volume.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Removes the created directory"""
        self.client_machine.remove_directory(self.test_directory)
        self.client_machine.remove_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                            value="VolumeFilters")
