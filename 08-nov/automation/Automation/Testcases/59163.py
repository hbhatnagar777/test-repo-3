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

    lock_dc_db() -- locks the DC DB

    verify_logs() -- verifies logs to conclude

    verify_scan()-- verifies scan_type

"""

import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_BASE_PATH
from FileSystem.FSUtils.fshelper import ScanType

"""
Example-
        "59163": {
                                    "AgentName": "",
                                    "ClientName": "",
                                    "TestPath": "",
                                    "StoragePolicyName": "",
                                    "CleanupRun": boolean,
                                    "Username": ",
                                    "Password": ""
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
        self.name = "Scan Switch from DC to other methods when DC DB of a volume is locked"
        self.client_machine = None
        self.drive_letter = None
        self.helper = None
        self.operation_selector = None
        self.test_directory = None

    def setup(self):
        """Setup function of this test case"""
        self.helper = WinFSHelper(self)
        self.client_machine = Machine(self.client)
        self.client_machine.username = self.tcinputs.get("Username")
        self.client_machine.password = self.tcinputs.get("Password")
        self.operation_selector = OptionsSelector(self.commcell)


    def verify_scan(self, job):
        logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                              log_file_name="FileScan.log",
                                                              search_term="ScanType")
        result = re.search(r"ScanType=\[[A-Z]*\]", logs)
        print(result)
        res = result.group(0)[10:12]
        if (res != "DC"):
            self.log.info("DC Scan was failed")
            self.log.info("Scan proceeded with "+ s)
        else:
            self.log.error("DC Scan wasn't failed.")
            raise Exception("DC Scan wasn't failed.")

    def verify_logs(self, job):
        """
            Verifies log details to check if scan proceeded or failed.
            Args:
                  job (job instance) - job instance returned from backup function.
        """
        logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                              log_file_name="FileScan.log",
                                                              search_term="Data Classifier has reported error")
        # If DC failed
        if logs:
            log_error = re.search(r"Data Classifier has reported error [0-9]*", logs)
            if log_error:
                self.log.info(log_error[0])

            # Fetching Scan Type used as DC failed
            logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                                  log_file_name="FileScan.log",
                                                                  search_term="ScanType")
            result = re.search(r"ScanType=\[[A-Z]*\]", logs)
            self.log.info("Scan proceeded with %s ",
                          result[0])

            return

        logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                              log_file_name="FileScan.log",
                                                              search_term="Failed to open/initialize database")

        # If DC failed
        if logs:
            log_error = re.search(r"Failed to open/initialize database", logs)
            if log_error:
                self.log.info(log_error[0])

            # Fetching Scan Type used as DC failed
            logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                                  log_file_name="FileScan.log",
                                                                  search_term="ScanType")
            result = re.search(r"ScanType=\[[A-Z]*\]", logs)
            self.log.info("Scan proceeded with %s ",
                          result[0])

            return

        self.log.info("DC Scan not failed.")

    def lock_dc_db(self):
        """Deletes the DC DB"""
        # if the key does not exists create one otherwise update its value to 0
        client_instance = self.client_machine.instance.split("Instance")[1]
        db_parent_path = self.drive_letter + WIN_DATA_CLASSIFIER_BASE_PATH
        db_path = self.client_machine.join_path(db_parent_path, f"dc_{client_instance}.db")

        self.log.info("Locking the db [%s]", db_path)
        pid = self.client_machine.lock_file(file=db_path, interval=300)

        self.log.info("Successfully completed: DC DB lock operation")

        return pid

    def run(self):
        """Run function of this test case"""
        try:
            # creating testdata
            self.drive_letter = self.operation_selector.get_drive(self.client_machine)
            self.test_directory = self.client_machine.join_path(self.drive_letter, "TestData_DB_LOCK_CHECK")
            if not self.client_machine.check_directory_exists(directory_path=self.test_directory):
                self.client_machine.create_directory(directory_name=self.test_directory)
            if not self.client_machine.generate_test_data(file_path=self.test_directory,
                                                          dirs=2,
                                                          files=1000):
                raise Exception("Failed to generate Test Data")

            self.helper.populate_tc_inputs(self)
            # backup set

            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            # setting subclient content
            subclient_content = [self.test_path]
            self.helper.create_subclient(name="subclient59163",
                                         storage_policy=self.storage_policy,
                                         content=subclient_content,
                                         scan_type=ScanType.OPTIMIZED)

            # creating data
            self.client_machine.generate_test_data(self.test_path, dirs=5, files=10)
            self.log.info("Generating data")

            # Locking DC DB file for 5 mins.
            pid = self.lock_dc_db()
            # make it full not inc
            # Run an INCR job
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup()

            # Fetching log lines: FileScan.log
            self.log.info("Fetching Logs from FileScan.log to verify Scan switch")
            self.verify_scan(job=job[0])

            # unlocking DC DB and restarting services.
            if pid:
                self.client_machine.kill_process(process_id=pid)

            self.client_machine.remove_directory(self.test_directory)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.client_machine.remove_directory(self.test_directory)
