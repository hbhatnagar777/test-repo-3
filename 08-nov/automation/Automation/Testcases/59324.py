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
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.

"""
import random
import time
from functools import partial

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.windows_machine import WindowsMachine
from FileSystem.FSUtils.winfshelper import WinFSHelper

config_constants = config.get_config()

class TestCase(CVTestCase):
    """Class for executing
    File System Scan Failure Conditions With UNC Path As Content

    This test case covers all possible scenarios in which failure conditions arise during Scan phase.
    This test case does the following.

    01. Create a new Backupset.
    02. Create a new subclient and define content such that it resides on a share.

    SCENARIO 1 BEGINS
    3.01. Create a dataset such that user account being impersonated doesn't have permissions to one of the subfolders.
    3.02. Run a Full backup and let it complete.
    3.03. Ensure the subfolder is added to Failures.cvf and reported as a failed folder/file.
    3.04. Revert the permissions that were modified on the subfolder.
    3.05. Run an Incremental backup.
    3.06. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 1 ENDS

    SCENARIO 2 BEGINS
    4.01. Create the following additional setting under FileSystemAgent on the client.
          Name: mszScanErrorHandling
          Type: MULTISTRING
          Value: 5:ACTION_ADD_TO_SCAN_FAILURES_AND_CONTINUE
    4.02. Run a Full backup.
    4.03. Ensure that the subfolder is added to ScanFailures.cvf and Failures.cvf and reported as a failed folder/file.
    4.04. Remove the additional setting.
    SCENARIO 2 ENDS

    SCENARIO 3 BEGINS
    5.01. Generate a large dataset.
    5.02. Run a Full backup, once Scan starts scanning content run NET STOP SERVER on server.
    5.03. Ensure that Scan phase fails and the job goes to Pending phase.
    5.04. Run the following command on the machine hosting the share.
          NET START SERVER
    5.05. Verify that Scan phase picked up all the files on the share.
    SCENARIO 3 ENDS
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Scan Failure Conditions With UNC Path As Content"
        self.show_to_user = True
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None, "LargeDatasetPath": None}
        self.helper = None
        self.storage_policy = None
        self.slash_format = None
        self.test_path = None
        self.tmp_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.bset_name = None
        self.sc_name = None
        self.content = None
        self.run_path = None
        self.common_args = None
        self.cleanup_run = None
        self.username = None
        self.password = None
        self.share = None
        self.server = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.local_path = None
        self.result_string = None
        self.status = None
        self.get_filescan_log = None

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.helper = WinFSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)
        self.username = config_constants.FileSystem.WINDOWS.TestPathUserName
        self.password = config_constants.FileSystem.WINDOWS.TestPathPassword
        self.impersonate_user = self.tcinputs.get('ImpersonateUser', self.password)
        self.impersonate_password = self.tcinputs.get('ImpersonatePassword', self.password)
        self.share = self.test_path.split("\\")[3]
        self.server = WindowsMachine(self.test_path.split("\\")[2], username=self.username, password=self.password)
        self.local_path = self.server.execute_command(f"Get-SMBShare -Name {self.share} | FT -HideTableHeaders -Property {{$_.Path}}").formatted_output
        self.get_filescan_log = partial(self.helper.get_logs_for_job_from_file, log_file_name="FileScan.log")

    def run(self):
        """Main function for test case execution"""
        try:
            def log_scenario_details(sce_num, beginning=True):
                """Prints scenario details.

                Args:
                    sce_num     (str)   --  Scenario number.

                    scenario    (str)   --  Scenario sequence.

                    beginning   (bool)  --  Determines if we're printing details
                    during the beginning or end of a scenario.

                Returns:
                    None

                Raises:
                    None

                """

                if beginning:
                    self.log.info("**********")
                    self.log.info(f"{sce_num} BEGINS")
                else:
                    self.log.info(f"END OF {sce_num}")
                    self.log.info("**********")

            self.sc_name = '_'.join(("subclient", str(self.id)))
            self.content = [self.slash_format.join((self.test_path, self.sc_name))]
            self.run_path = self.slash_format.join((self.content[0], self.runid))
            self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name, self.runid))
            self.common_args = {'name': self.sc_name,
                                'content': self.content,
                                'storage_policy': self.storage_policy,
                                'impersonate_user': {'username': self.impersonate_user,
                                                     'password': self.impersonate_password}}

            self.log.info("01. Create a new Backupset.")
            self.helper.create_backupset(self.bset_name)

            self.log.info("02. Create a new subclient.")
            self.helper.create_subclient(**self.common_args)

            # *****************
            # SCENARIO 1 BEGINS
            # *****************
            sce_num = "SCENARIO_1"
            log_scenario_details(sce_num)

            self.log.info("3.01. Create a dataset such that the user account being impersonated doesn't have permissions to access one of the subfolders.")
            self.client_machine.generate_test_data(self.run_path, dirs=5, files=5, username=self.impersonate_user, password=self.impersonate_password)

            subfolder = random.choice(self.client_machine.get_folders_in_path(self.run_path))
            self.log.info(f"Denying permissions on {subfolder} to the user being impersonated.")

            # SETTING ICACLS ON THE SERVER USING LOCAL PATH
            # SINCE SETTING PERMISSIONS FROM CLIENT ON REMOTE PATH REQUIRES A BUNCH OF OVERLY COMPLICATED STEPS.
            subfolder_local_path = '\\'.join((self.local_path, subfolder.partition(f"{self.share}\\")[2]))
            self.server.execute_command(f"ICACLS \"{subfolder_local_path}\" /DENY {self.impersonate_user}:`(CI`)`(RX`)")

            self.log.info("3.02. Run a Full backup and let it complete.")
            self.helper.run_backup(backup_level="Full")

            self.log.info("3.03. Ensure subfolder is added to ScanFailures.cvf/Failures.cvf and reported as failed.")
            # REPLACE UNC-NT_ WITH \\ TO ENSURE COMPARISON DOES NOT FAIL.
            failed_items = [i.replace("UNC-NT_", "\\\\").rstrip("\\") for i in self.helper.get_failed_items_in_jr()["Failures.cvf"]]

            if len(failed_items) != 1 or failed_items[0] != subfolder:
                raise Exception("The expected failed item was not found in the collect file Failures.cvf.")

            self.log.info("3.04. Remove the permissions that were set on the subfolder.")
            self.server.execute_command(f"ICACLS '{subfolder_local_path}' /GRANT {self.impersonate_user}:`(CI`)`(RX`)")

            self.log.info("3.05. Run an Incremental backup.")
            self.helper.run_backup_verify(backup_level="Incremental")

            self.log.info("3.06. Restore the data backed up in the previous backup job out of place and verify.")
            self.helper.run_restore_verify(self.slash_format, self.run_path, self.tmp_path, self.runid, in_place=True)

            log_scenario_details(sce_num, beginning=False)
            # ***************
            # SCENARIO 1 ENDS
            # ***************

            # *****************
            # SCENARIO 2 BEGINS
            # *****************
            sce_num = "SCENARIO_2"
            log_scenario_details(sce_num)

            subfolder = random.choice(self.client_machine.get_folders_in_path(self.run_path))
            self.log.info(f"Denying permissions on {subfolder} to the user being impersonated.")

            # SETTING ICACLS ON THE SERVER USING LOCAL PATH
            # SINCE SETTING PERMISSIONS FROM CLIENT ON REMOTE PATH REQUIRES A BUNCH OF OVERLY COMPLICATED STEPS.
            subfolder_local_path = '\\'.join((self.local_path, subfolder.partition(f"{self.share}\\")[2]))
            self.server.execute_command(f"ICACLS \"{subfolder_local_path}\" /DENY {self.impersonate_user}:`(CI`)`(RX`)")

            self.log.info("4.01. Create the following additional setting under FileSystemAgent on the client.")
            self.log.info("Name  : mszScanErrorHandling\tType  : MULTISTRING\tValue : 5:ACTION_ADD_TO_SCAN_FAILURES_AND_CONTINUE")
            self.client_machine.create_registry("FileSystemAgent", "mszScanErrorHandling", "5:ACTION_ADD_TO_SCAN_FAILURES_AND_CONTINUE", "MultiString")

            self.log.info("4.02. Run a Full backup.")
            self.helper.run_backup(backup_level="Full")

            self.log.info("4.03. Ensure subfolder is added to ScanFailures.cvf/Failures.cvf and reported as failed.")
            failures_cvfs = self.helper.get_failed_items_in_jr()
            failures = [item.replace("UNC-NT_", "\\\\").rstrip("\\") for item in failures_cvfs["Failures.cvf"]]
            scan_failures = [item.replace("UNC-NT_", "\\\\").rstrip("\\") for item in failures_cvfs["ScanFailures.cvf"]]

            if len(failures) != 1 or failures[0] != subfolder:
                raise Exception("The expected failed item was not found in the collect file Failures.cvf.")

            if len(scan_failures) != 1 or scan_failures[0] != subfolder:
                raise Exception("The expected failed item was not found in the collect file ScanFailures.cvf.")

            self.log.info("4.04. Remove the additional setting.")
            self.client_machine.remove_registry("FileSystemAgent", "mszScanErrorHandling")

            log_scenario_details(sce_num, beginning=False)
            # ***************
            # SCENARIO 2 ENDS
            # ***************

            # *****************
            # SCENARIO 3 BEGINS
            # *****************
            sce_num = "SCENARIO_3"
            log_scenario_details(sce_num)

            self.log.info("5.01. Set share with large dataset as subclient content.")
            self.helper.update_subclient(content=[self.tcinputs["LargeDatasetPath"]])

            self.log.info("5.02. Run a Full backup, once Scan starts scanning content run NET STOP SERVER on server.")
            full_backup = self.helper.run_backup("Full", wait_to_complete=False)[0]

            while True:
                if self.get_filescan_log(job_id=full_backup.job_id, search_term="CTraverseScanEngine::ProcessWork"):
                    break

            self.log.info("5.04. Run the command Stop-Service SERVER -Force on the server.")
            self.server.execute_command("Stop-Service SERVER -Force")

            while True:
                failure_log_line = self.get_filescan_log(job_id=full_backup.job_id, search_term="Run failed")
                if failure_log_line:
                    self.log.info(f"Confirmed that Scan phase failed from log line \n {failure_log_line}")
                    break

            self.log.info("5.03. Ensure that Scan phase fails and the job goes to Pending phase.")
            self.log.info("5.04. Run the command Start-Service SERVER on the server and wait for job to complete.")
            self.server.execute_command("Start-Service SERVER")
            time.sleep(5)
            full_backup.resume()

            # WAIT TILL BACKUP PHASE BEGINS AND ITS STATUS IS RUNNING OR IF JOB HAS COMPLETED
            while True:
                if full_backup.phase.upper() == "BACKUP":
                    full_backup.pause(wait_for_job_to_pause=True)
                    break

            self.log.info("Killing the job now")
            full_backup.kill()

            self.log.info("5.05. Verify that Scan phase picked up all the files on the share.")
            self.log.info("Comparing the file count printed in FileScan.log with count returned by GCI -R.")
            log_file_count = self.helper.get_no_of_qualified_objects_from_filescan(full_backup)['files']
            machine_file_count = self.client_machine.number_of_items_in_folder(self.tcinputs.get("LargeDatasetPath"), recursive=True, include_only='files')
            if log_file_count != machine_file_count:
                raise Exception(f"Count in FileScan : {log_file_count} != Count by GCI -R {machine_file_count}")

            log_scenario_details(sce_num, beginning=False)
            # ***************
            # SCENARIO 3 ENDS
            # ***************

            if self.cleanup_run:
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.bset_name)

        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        self.client_machine.remove_registry("FileSystemAgent", "mszScanErrorHandling")
