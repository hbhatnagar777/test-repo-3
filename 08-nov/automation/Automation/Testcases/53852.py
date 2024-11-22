# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.

"""

from random import randint
from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import SoftwareCompression
from FileSystem.FSUtils.winfshelper import WinFSHelper


class TestCase(CVTestCase):
    """Class for executing

    File System Extent Level Backup - Pass Management & Other Advanced Cases on Windows
    This test case will verify basic functionality of pass management of extent level backups on Windows.
    This test case will also verify other advanced cases on Windows.
    This test case does the following.

    01. Enable feature by setting bEnableFileExtentBackup (DWORD,1) under FileSystemAgent on client.
    02. Lower threshold by setting mszFileExtentSlabs (REG_MULTI_SZ,101-1024=100) under FileSystemAgent on client.
    03. Create a new backupset.

    SCENARIO 1 BEGINS
    4.01. Create a new subclient.
    4.02. Create one large file that qualifies for extent level backup.
    4.03. Lock the file.
    4.04. Run a full backup and let it complete.
    4.05. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 1 ENDS

    SCENARIO 2 BEGINS
    5.01. Create a new subclient.
    5.02. Create one large file that qualifies for extent level backup.
    5.03. Run full backup and suspend when job is in progress. Modify content and resume.
    5.04. Repeat 5.03 until the maximum number of passes has been met which is 4 by default.
    5.05. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 2 ENDS

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Extent Level Backup - Pass Management on Windows"
        self.show_to_user = True
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.helper = None
        self.storage_policy = None
        self.slash_format = None
        self.test_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.bset_name = None
        self.sc_name = None
        self.content = None
        self.run_path = None
        self.extent_path = None
        self.num_extent_files = None
        self.pause_interval_secs = None
        self.lock_interval_secs = None
        self.tmp_path = None
        self.fsa = None
        self.enable = None
        self.slab = None
        self.slab_val = None
        self.threshold = None
        self.max_passes = None
        self.current_pass = None
        self.log_line = None
        self.attempt_num = None
        self.cleanup_run = None
        self.size_sce1 = None
        self.size_sce2 = None
        self.size_sce3 = None
        self.size_sce4 = None
        self.pid = None
        self.RETAIN_DAYS = None
        self.common_args = None
        self.gen_data_args = None

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.helper = WinFSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)
        self.num_extent_files = int(self.tcinputs.get("NumFiles", 1))
        self.size_sce1 = int(self.tcinputs.get("FileSizeInKBScenario1", 256000))
        self.size_sce2 = int(self.tcinputs.get("FileSizeInKBScenario2", 5242880))
        self.pause_interval_secs = int(self.tcinputs.get("PauseIntervalSecs", randint(8, 10)))
        self.lock_interval_secs = int(self.tcinputs.get("LockIntervalSecs", 600))
        self.max_passes = 4
        self.current_pass = 0
        self.attempt_num = 0
        self.log_line = ""

        if self.client_machine.os_info == "WINDOWS":
            self.fsa = "FileSystemAgent"
            self.enable = "bEnableFileExtentBackup"
            self.slab = "mszFileExtentSlabs"
            self.slab_val = str(self.tcinputs.get("Slab", "101-1024=100"))
            self.threshold = int(self.slab_val.split("-", maxsplit=1)[0]) * 1048576

    def run(self):
        """Main function for test case execution"""
        try:
            def log_scenario_details(sce_num, scenario, beginning=True):
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
                    self.log.info(scenario)
                else:
                    self.log.info(f"END OF {sce_num}")
                    self.log.info("**********")

            def initialize_scenario_attributes(sce_num):
                """Initializes attributes common to scenarios.

                Args:
                    sce_num (str)   --  Scenario number.

                Returns:
                    None

                Raises:
                    None

                """

                self.sc_name = '_'.join(("subclient", str(self.id), sce_num))
                self.content = [self.slash_format.join((self.test_path, self.sc_name))]
                self.run_path = self.slash_format.join((self.content[0], self.runid))
                self.extent_path = self.slash_format.join((self.run_path, extent_files))
                self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name, self.runid))

                self.common_args = {'name': self.sc_name,
                                    'content': self.content,
                                    'storage_policy': self.storage_policy,
                                    'software_compression': SoftwareCompression.OFF.value}

                self.gen_data_args = {'file_path': self.extent_path, 'dirs': 0, 'files': self.num_extent_files}

            self.log.info(self.__doc__)

            self.log.info("01. Disabling bEnableAutoSubclientDirCleanup")
            self.client_machine.create_registry(self.fsa, "bEnableAutoSubclientDirCleanup", 0, "DWord")
            self.log.info(f"02. Enable feature by setting {self.enable} under {self.fsa} on client.")
            self.client_machine.create_registry(self.fsa, self.enable, 1, "DWord")
            self.log.info(f"03. Lowering threshold by setting {self.slab} under {self.fsa} on client.")
            self.client_machine.create_registry(self.fsa, self.slab, self.slab_val, "MultiString")

            self.log.info("04. Create a new backupset")
            self.helper.create_backupset(self.bset_name)

            extent_files, slash_format = "extent_files", self.slash_format

            # *****************
            # SCENARIO 1 BEGINS
            # *****************
            sce_num, scenario = "SCENARIO_1_LOCKED_FILE", "Lock a file -> Full -> Restore and verify"
            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num)

            self.log.info("5.01.  Create a new subclient.")
            self.helper.create_subclient(**self.common_args)

            self.log.info("5.02. Create one large file that qualifies for extent level backup.")
            self.client_machine.generate_test_data(file_size=self.size_sce1, **self.gen_data_args)

            self.log.info("5.03. Lock the file.")
            file_name = self.client_machine.get_files_in_path(self.extent_path)[0]
            self.log.info(f"Locking the file {file_name} for the next {self.lock_interval_secs} seconds")
            self.pid = self.client_machine.lock_file(file_name, interval=self.lock_interval_secs)

            self.log.info("5.04. Run a full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Unlocking the file by stopping the PS Process that has a lock on the file.")
            self.client_machine.kill_process(process_id=self.pid)

            self.log.info("5.05. Restore the data backed up in the previous backup job out of place and verify.")
            self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

            log_scenario_details(sce_num, scenario, beginning=False)

            # ***************
            # SCENARIO 1 ENDS
            # ***************

            # *****************
            # SCENARIO 2 BEGINS
            # *****************
            sce_num, scenario = "SCENARIO_2_PASS_MGMT", "Full (Suspend, Modify, Resume, .....) -> Restore and verify"
            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num)

            self.log.info("6.01. Create a new subclient.")
            self.helper.create_subclient(**self.common_args)

            self.log.info("6.02. Create one large file that qualifies for extent level backup.")
            self.client_machine.generate_test_data(file_size=self.size_sce2, **self.gen_data_args)

            self.log.info("6.03. Run full backup and suspend when job is in progress. Modify content and resume.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]

            self.log.info("6.04. Repeat 6.03 until the maximum number of passes has been met which is 4 by default.")
            while self.current_pass <= self.max_passes:

                # WAIT TILL BACKUP PHASE BEGINS AND ITS STATUS IS RUNNING OR IF JOB HAS COMPLETED
                while True:
                    if full_bkp.phase.upper() == "BACKUP" and full_bkp.status.upper() == "RUNNING":
                        break
                    elif full_bkp.status.upper() == "COMPLETED":
                        raise Exception("Backup job already completed, couldn't verify pass management.")

                self.attempt_num += 1
                search_term = f"-jt {full_bkp.job_id}:7:{self.attempt_num}"

                # WAIT TILL ATTEMPT IS CORRECT. RELYING ONLY LOG LINE TEXT MEANS WE RETURN TRUE DUE TO OLDER ATTEMPTS.
                while True:
                    if self.helper.get_logs_for_job_from_file(full_bkp.job_id, "clBackup.log", search_term):
                        self.log.info(f"Current attempt of backup phase is {self.attempt_num}")
                        break

                # SUSPEND JOB AFTER pause_interval_secs
                self.log.info(f"Job will be suspended {self.pause_interval_secs} seconds from now.")
                sleep(self.pause_interval_secs)
                full_bkp.pause(wait_for_job_to_pause=True)
                self.pause_interval_secs += 5  # INCREMENTING INTERVAL BY 5 SECONDS BASED ON RESULTS OF TESTING.

                # VERIFYING IF THE CopyId IS PERSISTENT, WE CHECK THIS EVERY ATTEMPT.
                copyid, copyid_line = self.helper.get_copyid_for_extent_backup(full_bkp)
                if copyid and (self.helper.is_copyid_persistent(copyid) is False):
                    msg = f"Snap indicated by log line {copyid_line} isn't persistent. Failing the test case."
                    raise Exception(msg)
                elif copyid and (self.helper.is_copyid_persistent(copyid) is True):
                    self.log.info(f"Copy ID is indicated by log line {copyid_line}")
                    break

                # CHECK IF FILE IS PRESENT IN EXTENT COLLECT FILE IN THE VERY FIRST ATTEMPT ONLY
                if self.attempt_num == 1:
                    self.log.info("Ensuring that the large file is present in FileExtentEligibleNumColTot*.cvf")
                    res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                    if not res:
                        raise Exception("Extent level validation failed, failing the test case")

                # GET CURRENT PASS NUMBER
                self.current_pass, self.log_line = self.helper.get_current_extent_level_pass(full_bkp)
                self.log.info(f"Current pass = {self.current_pass} indicated by line {self.log_line}")

                # IF CURRENT PASS IS EQUAL TO MAXIMUM ALLOWED NUMBER OF PASSES OR IF CURRENT PHASE IS ARCHIVE INDEX
                if self.current_pass >= self.max_passes:
                    self.log.info("Reached maximum number of passes.")
                    break
                elif full_bkp.phase.upper() == "ARCHIVE INDEX":
                    self.log.info("Already reached archive index phase.")
                    break

                self.log.info("Modifying the file.")
                self.client_machine.modify_test_data(self.extent_path, modify=True)
                self.log.info("Resuming the backup job.")
                full_bkp.resume()

            self.log.info("Resuming the backup job.")
            full_bkp.resume()
            full_bkp.wait_for_completion()

            self.log.info("6.05. Restore the data backed up in the previous backup job out of place and verify.")
            self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

            log_scenario_details(sce_num, scenario, beginning=False)
            # ***************
            # SCENARIO 2 ENDS
            # ***************


        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        if self.cleanup_run:
            self.client_machine.remove_directory(self.test_path)
            self.instance.backupsets.delete(self.bset_name)
            if self.client_machine.os_info == "WINDOWS":
                remove_msg = f"Removing registry entries {self.enable} and {self.slab} under {self.fsa}"
                self.log.info(remove_msg)
                self.client_machine.remove_registry(self.fsa, self.enable)
                self.client_machine.remove_registry(self.fsa, self.slab)
                if self.pid:
                    stop_process_cmd = f"Stop-Process -Id {self.pid}"
                    self.client_machine.execute_command(stop_process_cmd)
