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
from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.winfshelper import WinFSHelper

class TestCase(CVTestCase):
    """Class for executing

    File System Failed Files & Folders - Basic Acceptance on Windows
    This test case will verify the basic functionality of the failure handling mechanisms on Windows.

    SCENARIOS
    01. Open handles -> Full -> Restore -> Incr.
    02. Disable VSS Service on the client machine -> Open handles -> Full -> Close handles
    03. Open handles -> Full (Suspend and resume after VSS snap is taken) -> Restore
    04. Disable Use VSS for subclient -> Open handles -> Full -> Close handles -> Incr. -> Restore
    05. Disable Use VSS for subclient -> Open handles -> Full -> Incr. -> Synth. Full -> Close handles -> Incr. -> Restore

    This test case does the following.

    01. Create a new backupset.

    SCENARIO 1 BEGINS
    02.01. Create a new subclient with Use VSS ENABLED for locked files only.
    02.02. Generate test data and opening handles to lock the files in various methods.
    02.03. Open the handles to lock files.
    02.04. Run a Full backup and let it complete.
    02.05. Close the handles.
    02.06. Restore the data backed up in the previous backup job out of place and verify.
    02.07. Run an Incremental Backup and verify that it completes in Scan phase.
    SCENARIO 1 ENDS

    SCENARIO 2 BEGINS
    03.01. Shutting down the VSS Service on the client.
    03.02. Create a new subclient with Use VSS ENABLED for locked files only.
    03.03. Generate test data.
    03.04. Open the handles to lock files.
    03.05. Run a Full Backup and let it complete.
    03.06. Close the handles.
    03.07. Starting the VSS Service on the client.
    SCENARIO 2 ENDS

    SCENARIO 3 BEGINS
    04.01. Create a new subclient with Use VSS ENABLED for locked files only.
    04.02. Generate test data.
    04.03. Open the handles to lock files.
    04.04. Run a Full Backup and suspend it after the VSS snap for failed files is created.
    04.05. Restore data from the latest cycle out of place and verify.
    04.06. Close the handles.
    SCENARIO 3 ENDS

    SCENARIO 4 BEGINS
    05.01. Create a new subclient with Use VSS DISABLED.
    05.02. Generate test data.
    05.03. Open the handles to lock files.
    05.04. Run a Full Backup and let it complete.
    05.05. Close the handles.
    05.06. Run an Incremental Backup and let it complete.
    SCENARIO 4 ENDS

    SCENARIO 5 BEGINS
    06.01. Create a new subclient with Use VSS DISABLED.
    06.02. Generate test data.
    05.02. Open the handles to lock files.
    06.03. Run a Full Backup and let it complete.
    06.04. Run an Incremental Backup and let it complete.
    06.05. Run a Synthetic Full backup and let it complete.
    06.06. Run an Incremental Backup and let it complete.
    06.07. Restore the data backed up out of place and verify.
    06.08. Close the handles.
    SCENARIO 5 ENDS
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Failed Files & Folders - Basic Acceptance on Windows"
        self.show_to_user = True
        self.tcinputs = {"TestPathList": None, "StoragePolicyName": None}
        self.helper = None
        self.storage_policy = None
        self.bset_name = None
        self.num_files = None
        self.lock_interval_secs = None
        self.common_args = None
        self.common_gen_data_args = None
        self.file_size = None
        self.slash_format = None
        self.test_path_list = None
        self.contents = []
        self.run_paths = []
        self.excl_read_paths = []
        self.shared_rw_paths = []
        self.no_lock_paths = []
        self.file_list = []
        self.handles = []
        self.tmp_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.sc_name = None
        self.nl = None
        self.lock_interval = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.helper = WinFSHelper(self)
        self.helper.populate_tc_inputs(self)
        # THE FOLLOWING CHANGE WAS MADE AS PART OF MR 260971
        if isinstance(self.test_path_list, str):
            self.test_path_list = self.test_path_list.split(",")
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)
        self.num_files = int(self.tcinputs.get("NumFiles", 10))
        self.file_size = int(self.tcinputs.get("FileSizeInKB", 10240))
        self.lock_interval = int(self.tcinputs.get("LockIntervalSecs", 600))
        self.nl = "".join(("\n", "\t"*14, "       "))

        self.log.info("Starting the VSS Service during setup()")
        self.client_machine.execute_command("Set-Service VSS -StartUpType Automatic")
        self.client_machine.execute_command("Start-Service VSS")

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

            def initialize_scenario_attributes(sce_num, scenario):
                """Initializes attributes common to scenarios.

                Args:
                    sce_num (str)   --  Scenario number.

                Returns:
                    None

                Raises:
                    None

                """
                self.sc_name = '_'.join(("subclient", str(self.id), sce_num))

                self.run_paths.clear()
                self.excl_read_paths.clear()
                self.shared_rw_paths.clear()
                self.no_lock_paths.clear()
                self.contents.clear()

                for test_path in self.test_path_list:
                    content = self.slash_format.join((test_path, self.sc_name))
                    self.contents.append(content)
                    self.run_paths.append(self.slash_format.join((content, self.runid)))

                # self.tmp_path IS THE DESTINATION PATH FOR THE RESTORE.
                self.tmp_path = self.slash_format.join((self.test_path_list[0], "tmp", self.sc_name, self.runid))

                # ARGUMENTS COMMON TO ALL SCENARIOS
                self.common_args = {'name': self.sc_name,
                                    'content': self.contents,
                                    'storage_policy': self.storage_policy,
                                    'allow_multiple_readers': True,
                                    'description': scenario}

                self.common_gen_data_args = {'file_size': self.file_size, 'dirs': 0, 'files': self.num_files}

                i = 1  # HELPS DIFFERENTIATE THE PATHS ON DIFFERENT VOLUMES
                for run_path in self.run_paths:
                    # <run_path>_excl_read --> FILE HANDLE --> READ ACCESS & NO SHARING
                    self.excl_read_paths.append(self.slash_format.join((run_path, "_".join(("excl_read", str(i))))))

                    # <run_path>_shared_rw --> FILE HANDLE --> READ & WRITE & READ & WRITE SHARING
                    self.shared_rw_paths.append(self.slash_format.join((run_path, "_".join(("shared_rw", str(i))))))

                    # <run_path>_no_lock   --> FILE HANDLE --> NO HANDLE
                    self.no_lock_paths.append(self.slash_format.join((run_path, "_".join(("no_lock", str(i))))))

                    i += 1

            def file_handle(op_type):
                """Opens excl. read & shared read write handle on files.Written to reduce number of lines in test case.

                Args:
                    op_type (str)   --  Specifies type of operation to perform. Accepted values are "open", "close".

                Returns:
                    None

                Raises:
                    None

                """
                if op_type.lower() == "open":

                    self.file_list.clear()
                    self.log.info(f"Exclusive read handle on files under{self.nl}{self.nl.join((self.excl_read_paths))}")
                    for read_path in self.excl_read_paths:
                        self.file_list.extend(self.client_machine.get_files_in_path(read_path))
                    self.handles.extend(self.client_machine.lock_file(file_list=self.file_list, interval=self.lock_interval))

                    self.file_list.clear()
                    self.log.info(f"Shared read write handle on files under{self.nl}{self.nl.join((self.shared_rw_paths))}")
                    for shared_rw_path in self.shared_rw_paths:
                        self.file_list.extend(self.client_machine.get_files_in_path(shared_rw_path))
                    self.handles.extend(self.client_machine.lock_file(file_list=self.file_list, interval=self.lock_interval, shared_read_write=True))
                    
                elif op_type.lower() == "close":

                    for handle in self.handles:
                        self.client_machine.execute_command(f"Stop-Process -Id {handle}")
                    self.handles.clear()

            def return_expected_failed_items():
                """Returns list of expected failed items.

                Args:
                    None

                Returns:
                    list    -   List of failed items.

                Raises:
                    None

                """

                expected = list()
                for path in self.excl_read_paths + self.shared_rw_paths:
                    expected.extend(self.client_machine.get_files_in_path(path))

                return expected

            def generate_test_data():
                """Generates the test data, this step is common to all the scenarios.

                Args:
                    None

                Returns:
                    None

                Raises:
                    None

                """
                for path in self.excl_read_paths + self.shared_rw_paths + self.no_lock_paths:
                    self.client_machine.generate_test_data(file_path=path, **self.common_gen_data_args)

            self.log.info(self.__doc__)
            self.log.info("01. Create a new backupset")
            self.helper.create_backupset(self.bset_name)
            # *****************
            # SCENARIO 1 BEGINS
            # *****************
            sce_num = "SCENARIO_1"
            scenario = "Open handles -> Full -> Restore -> Incr."

            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num, scenario)

            self.log.info("02.01. Create a new subclient with Use VSS ENABLED for locked files only.")
            self.helper.create_subclient(**self.common_args)

            self.log.info("02.02. Generate test data and opening handles to lock the files in various methods.")
            generate_test_data()

            self.log.info("02.03. Open the following handles.")
            file_handle("open")

            self.log.info("02.04. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Verify the entries in FailedFileRetryCollect.cvf.")
            ffr_cvf = self.helper.get_failed_items_in_jr()["FailedFileRetryCollect.cvf"]
            expected = return_expected_failed_items()

            if not self.helper.compare_lists(ffr_cvf, expected, sort_list=True):
                msg = "Entries in FailedFileRetryCollect.cvf didn't match up with the expected entries."
                raise Exception(msg)

            if not full_bkp.summary['totalFailedFiles'] == 0:
                msg = f"Failed file count = {full_bkp.summary['totalFailedFiles']} , Expected count = 0"
                raise Exception(msg)

            self.log.info("02.05. Close the handles.")
            file_handle("close")
            self.handles.clear()

            self.log.info("02.06. Restore the data backed up in the previous backup job out of place and verify.")
            self.helper.run_restore_verify(self.slash_format, self.run_paths, self.tmp_path, self.runid, full_bkp)

            self.log.info("02.07. Run an Incremental Backup and verify that it completes in Scan phase.")
            self.helper.run_backup_verify(backup_level="Incremental", scan_marking=True)

            self.log.info("Ensure that FailedFileRetryCollect.cvf and Failures.cvf are empty.")
            failed_files_dict = self.helper.get_failed_items_in_jr()
            if len(failed_files_dict["Failures.cvf"]) > 0 or len(failed_files_dict["FailedFileRetryCollect.cvf"]) > 0:
                msg = "Entries in Failures.cvf or FailedFileRetryCollect.cvf weren't cleared by Incremental backup."
                raise Exception(msg)
            # ***************
            # SCENARIO 1 ENDS
            # ***************

            # *****************
            # SCENARIO 2 BEGINS
            # *****************
            sce_num = "SCENARIO_2"
            scenario = f"Disable VSS Service on the client machine -> Open handles -> Full -> Close handles"

            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num, scenario)

            self.log.info("03.01. Shutting down the VSS Service on the client.")
            self.client_machine.execute_command("Stop-Service VSS")
            self.client_machine.execute_command("Set-Service VSS -StartUpType Disabled")

            self.log.info("03.02. Create a new subclient with Use VSS ENABLED for locked files only.")
            self.helper.create_subclient(**self.common_args)

            self.log.info("03.03. Generate test data.")
            generate_test_data()

            self.log.info("03.04. Open the following handles.")
            file_handle("open")

            self.log.info("03.05. Run a Full Backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("03.06. Close the handles.")
            file_handle("close")

            self.log.info("Ensure that FailedFileRetryCollect.cvf and Failures.cvf contain the failed items.")
            failed_files = self.helper.get_failed_items_in_jr()
            expected = return_expected_failed_items()

            msg = "Entries in {file_name} didn't match up with the expected entries."
            if not self.helper.compare_lists(failed_files["FailedFileRetryCollect.cvf"], expected, sort_list=True):
                raise Exception(msg.format(file_name="FailedFileRetryCollect.cvf"))

            if not self.helper.compare_lists(failed_files["Failures.cvf"], expected, sort_list=True):
                raise Exception(msg.format(file_name="Failures.cvf"))

            # CHECKING FAILED FILE COUNT FOR JOB
            if not full_bkp.summary['totalFailedFiles'] == len(expected):
                msg = f"Failed file count = {full_bkp.summary['totalFailedFiles']} , Expected count = {len(expected)}"
                raise Exception(msg)

            self.log.info("03.07. Starting the VSS Service on the client.")
            self.client_machine.execute_command("Set-Service VSS -StartUpType Automatic")
            self.client_machine.execute_command("Start-Service VSS")
            # ***************
            # SCENARIO 2 ENDS
            # ***************

            # *****************
            # SCENARIO 3 BEGINS
            # *****************
            sce_num = "SCENARIO_3"
            scenario = f"Open handles -> Full (Suspend and resume after VSS snap is taken) -> Restore"

            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num, scenario)

            self.log.info("04.01. Create a new subclient with Use VSS ENABLED for locked files only.")
            self.helper.create_subclient(**self.common_args)

            self.log.info("04.02. Generate test data.")
            generate_test_data()

            self.log.info("04.03. Open the following handles.")
            file_handle("open")

            self.log.info("04.04. Run a Full Backup and suspend it after the VSS snap for failed files is created.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]

            # WAIT TILL BACKUP PHASE BEGINS AND ITS STATUS IS RUNNING OR IF JOB HAS COMPLETED
            while True:
                if ((full_bkp.phase).upper() == "BACKUP" and (full_bkp.status).upper() == "RUNNING"):
                    break

            # WAIT FOR BACKUP OF FailedFileRetryCollect.cvf TO BEGIN
            search_term = "Currently backing up failed file retry collect file"
            while True:
                log_line = self.helper.get_logs_for_job_from_file(full_bkp.job_id, "clBackup.log", search_term)
                if log_line:
                    self.log.info(f"FailedFileRetryCollect.cvf backup has begun indicated by log line {log_line}")
                    break

            self.log.info("Suspending the backup job in 5 seconds.")
            sleep(5)
            full_bkp.pause(wait_for_job_to_pause=True)

            self.log.info("Resuming the job in 10 seconds and waiting for it to complete.")
            sleep(10)
            full_bkp.resume()
            full_bkp.wait_for_completion()

            self.log.info("04.05. Close the handles.")
            file_handle("close")
            self.handles.clear()

            self.log.info("04.06. Restore data from the latest cycle out of place and verify.")
            self.helper.run_restore_verify(self.slash_format, self.run_paths, self.tmp_path, self.runid, full_bkp)
            # ***************
            # SCENARIO 3 ENDS
            # ***************

            # *****************
            # SCENARIO 4 BEGINS
            # *****************
            sce_num = "SCENARIO_4"
            scenario = "Disable Use VSS for subclient -> Open handles -> Full -> Close handles -> Incr. -> Restore"

            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num, scenario)

            self.log.info("05.01. Create a new subclient with Use VSS DISABLED.")
            self.helper.create_subclient(**self.common_args)
            self.helper.update_subclient(use_vss={'useVSS': False, 'useVssForAllFilesOptions': 3, 'vssOptions': 2})

            self.log.info("05.02. Generate test data.")
            generate_test_data()

            self.log.info("05.03. Open the following handles.")
            file_handle("open")

            self.log.info("05.04. Run a Full Backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("05.05. Close the handles.")
            file_handle("close")

            self.log.info("Ensure that Failures.cvf contains the failed items.")
            failed_files = self.helper.get_failed_items_in_jr()
            expected = return_expected_failed_items()

            if not self.helper.compare_lists(failed_files["Failures.cvf"], expected, sort_list=True):
                msg = "Entries in Failures.cvf didn't match up with the expected entries."
                raise Exception(msg)

            # CHECKING FAILED FILE COUNT FOR FULL BACKUP JOB
            if not full_bkp.summary['totalFailedFiles'] == len(expected):
                msg = f"Failed file count = {full_bkp.summary['totalFailedFiles']} , Expected count = {len(expected)}"
                raise Exception(msg)

            self.log.info("05.06. Run an Incremental Backup and let it complete.")
            incr_bkp = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Ensure that Failures.cvf has now been cleared of failed items.")
            failures = self.helper.get_failed_items_in_jr()["Failures.cvf"]
            expected = list()  # WE DO NOT EXPECT ANY FAILED ITEMS SINCE HANDLES HAVE BEEN CLOSED.

            if not self.helper.compare_lists(failures, expected, sort_list=True):
                msg = "Entries in Failures.cvf didn't match up with the expected entries."
                raise Exception(msg)

            # CHECKING FAILED FILE COUNT FOR JOB
            if not incr_bkp.summary['totalFailedFiles'] == len(expected):
                msg = f"Failed file count = {incr_bkp.summary['totalFailedFiles']} , Expected count = {len(expected)}"
                raise Exception(msg)
            # ***************
            # SCENARIO 4 ENDS
            # ***************

            # *****************
            # SCENARIO 5 BEGINS
            # *****************
            sce_num = "SCENARIO_5"
            scenario = "Disable Use VSS for subclient -> Open handles -> Full -> Incr. -> Synth. Full -> Close handles -> Incr. -> Restore"

            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num, scenario)

            self.log.info("06.01. Create a new subclient with Use VSS DISABLED.")
            self.helper.create_subclient(**self.common_args)
            self.helper.update_subclient(use_vss={'useVSS': False, 'useVssForAllFilesOptions': 3, 'vssOptions': 2})

            self.log.info("06.02. Generate test data.")
            generate_test_data()

            self.log.info("06.02. Open the following handles.")
            file_handle("open")

            self.log.info("06.03. Run a Full Backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Ensure that Failures.cvf contains the failed items.")
            failures = self.helper.get_failed_items_in_jr()["Failures.cvf"]
            expected = return_expected_failed_items()

            if not self.helper.compare_lists(failures, expected, sort_list=True):
                msg = "Entries in Failures.cvf didn't match up with the expected entries."
                raise Exception(msg)

            if not full_bkp.summary['totalFailedFiles'] == len(expected):
                msg = f"Failed file count = {full_bkp.summary['totalFailedFiles']} , Expected count = {len(expected)}"
                raise Exception(msg)

            self.log.info("06.04. Run an Incremental Backup and let it complete.")
            incr_bkp = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Ensure that Failures.cvf contains the failed items.")
            failed_files, expected = self.helper.get_failed_items_in_jr(), list()
            for path in self.excl_read_paths + self.shared_rw_paths:
                expected.extend(self.client_machine.get_files_in_path(path))

            if not full_bkp.summary['totalFailedFiles'] == len(expected):
                msg = f"Failed file count = {full_bkp.summary['totalFailedFiles']} , Expected count = {len(expected)}"
                raise Exception(msg)

            # CHECKING FAILED FILE COUNT FOR JOB
            if not incr_bkp.summary['totalFailedFiles'] == len(expected):
                msg = f"Failed file count = {incr_bkp.summary['totalFailedFiles']} , Expected count = {len(expected)}"
                raise Exception(msg)

            self.log.info("06.05. Run a Synthetic Full backup and let it complete.")
            self.helper.run_backup(backup_level="Synthetic_full")

            self.log.info("Enabling Use VSS for the subclient.")
            self.helper.update_subclient(use_vss={'useVSS': True, 'useVssForAllFilesOptions': 3, 'vssOptions': 2})

            self.log.info("06.06. Close the handles.")
            file_handle("close")

            self.log.info("06.07. Run an Incremental Backup and let it complete.")
            self.helper.run_backup(backup_level="Incremental")

            self.log.info("06.08. Restore the data backed up out of place and verify.")
            self.helper.run_restore_verify(self.slash_format, self.run_paths, self.tmp_path, self.runid)
            # ***************
            # SCENARIO 5 ENDS
            # ***************

        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

            self.log.info("Closing All Handles since an exception was raised.")
            file_handle("close")

    def tear_down(self):
        self.log.info("Starting the VSS Service as part of tear_down")
        self.client_machine.execute_command("Set-Service VSS -StartUpType Automatic")
        self.client_machine.execute_command("Start-Service VSS")

        self.log.info("Closing All Handles as part of tear_down")
        for handle in self.handles:
            self.client.execute_command(f"Stop-Process -Id {handle}")
