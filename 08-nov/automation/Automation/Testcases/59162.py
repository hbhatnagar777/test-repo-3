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

    update_reg_keys() --  updates required  registry keys

    verify_logs() --  verifies logs to conclude

"""

import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_CONFIG_REGKEY


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
        self.name = "Verifying Scan Switch from DC to other methods when DC DB of a volume is not healthy"
        self.client_machine = None
        self.helper = None
        self.tcinputs = {
            "Content": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.helper = WinFSHelper(self)
        self.client_machine = Machine(self.client)

    def update_reg_keys(self):
        """
            Updates registry keys on client machine
            About drive_letter: Assuming Subclient Content starts with drive letter and
            that drive letter is used to do DB operations
        """
        drive_letter = self.subclient.content[0][0]
        guid_path = WIN_DATA_CLASSIFIER_CONFIG_REGKEY + self.helper.get_volume_guid(drive_letter=drive_letter)

        self.log.info("Creating registry keys")
        self.client_machine.create_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                            value="DCScanRetries",
                                            data=1,
                                            reg_type="DWord")

        if not self.client_machine.check_registry_exists(key=guid_path):
            self.client_machine.create_registry(key=guid_path,
                                                value=None,
                                                data=None,
                                                reg_type='String')

        self.client_machine.create_registry(key=guid_path,
                                            value="DatabaseRebuildControl",
                                            data=3,
                                            reg_type="DWord")

    def verify_logs(self, job):
        """
            Verifies log details to check if scan proceeded or failed.
            Args:
                  job (job instance) - job instance returned from backup function.
        """
        logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                              log_file_name="FileScan.log",
                                                              search_term="Optimized scan failed to populate")

        if logs:
            self.log.info("DC Scan Failed, Error: Failed to Populate DB")
            logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                                  log_file_name="FileScan.log",
                                                                  search_term="ScanType")
            result = re.search(r"ScanType=\[[A-Z]*\]", logs)
            self.log.info("Scan proceeded with %s", result[0])

        else:
            self.log.info("DC Scan not failed.")

    def run(self):
        """Run function of this test case"""
        try:
            # setting subclient content
            if isinstance(self.tcinputs.get("Content"), list):
                self.subclient.content = self.tcinputs.get("Content")
            else:
                self.subclient.content = [self.tcinputs.get("Content")]

            # updating reg keys
            self.update_reg_keys()

            # performing INCR backup
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup()

            # verifying logs
            self.log.info("Fetching Logs from FileScan.log to verify Scan switch")
            self.verify_logs(job=job[0])

            # removing any set reg keys.
            self.client_machine.remove_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                value="DCScanRetries")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
