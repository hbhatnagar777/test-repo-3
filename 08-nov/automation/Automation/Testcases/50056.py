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
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, CommitCondition, FSHelper
from FileSystem.FSUtils.winfshelper import WinFSHelper


class TestCase(CVTestCase):
    """Class for executing

    File System Commit - Basic Functionality Scenarios
    This test case will verify the basic functionality of FS commit.
    The following scenarios will be covered as part of this test case.

    1. Full (Commit) -> Incr.
    2. Full -> Incr. (Commit) -> Incr -> Restore & Verify.
    3. Full -> Incr. (Commit) -> Synthetic Full -> Incr.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Commit - Basic Functionality Scenarios"
        self.show_to_user = True
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.helper = None
        self.bset_name = None
        self.storage_policy = None
        self.num_dirs = 1
        self.slash_format = None
        self.test_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.cleanup_run = None
        self.RETAIN_DAYS = None
        self.num_files = None
        self.file_size_kb = None
        self.threshold = None
        self.tmp_path = None
        self.only_dc = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        if self.client.os_info.upper().find("WINDOWS") != -1:
            self.helper = WinFSHelper(self)
        else:
            self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.num_files = int(self.tcinputs.get("NumOfFiles", 10))
        self.file_size_kb = int(self.tcinputs.get("FileSizeInKb", 256000))
        self.threshold = int(self.tcinputs.get("Threshold", 3))
        self.bset_name = "_".join(("backupset", str(self.id)))

    def run(self):
        """Main function for test case execution"""
        try:

            def log_scenario_details(scenario_num, scenario, beginning=True):
                """Prints scenario details.

                Args:
                    scenario_num    (str)   --  Scenario number.

                    scenario        (str)   --  Scenario sequence.

                    beginning       (bool)  --  Determines if we're printing details
                    during the beginning or end of a scenario.

                Returns:
                    None

                Raises:
                    None

                """
                if beginning:
                    self.log.info("**********")
                    self.log.info(f"{scenario_num} : {scenario}")
                else:
                    self.log.info(f"END OF {scenario_num}")
                    self.log.info("**********")

            def num_of_transferred_objects(job):
                """Returns the number of transferred objects for the given job.

                Args:
                    job (obj)   --  Instance of Job

                Returns:
                    int --  Returns the number of transferred objects.

                Raises:
                    None

                """
                return job.details["jobDetail"]["detailInfo"]["numOfObjects"]

            def verify_statistics(job_list):
                """ "Verifies that the cumulative transferred file count and application for the jobs in list is equal
                to the number and size of files on the client.

                Args:
                    job_list    (list)  --  List of instances of Job.

                Returns:
                    None

                Raises:
                    None

                """

                total_num_of_files = len(
                    self.client_machine.get_files_in_path(self.subclient.content[0])
                )
                transferred_count_total, total_folder_size, total_application_size = (
                    0,
                    0,
                    0,
                )
                for job in job_list:
                    transferred_count = num_of_transferred_objects(job)
                    transferred_count_total += transferred_count
                    total_application_size += job.size_of_application
                    self.log.info(
                        f"Transferred count for job {job.job_id} = {transferred_count}"
                    )
                self.log.info(f"Total Transferred Count = {transferred_count_total}")
                self.log.info(
                    f"Number Of Files under {self.subclient.content[0]} = {total_num_of_files}"
                )
                if total_num_of_files == transferred_count_total:
                    self.log.info("Since the numbers match up, statistics are correct.")
                else:
                    self.log.info(
                        "PLEASE CHECK STATISTICS, ITEM COUNT IS INCORRECT !!!"
                    )

                self.log.info(
                    "Verifying the Application Size is more or less equal to the dataset size on client."
                )
                in_bytes = [True] * len(self.subclient.content)
                total_folder_size = int(
                    sum(
                        list(
                            map(
                                self.client_machine.get_folder_size,
                                self.subclient.content,
                                in_bytes,
                            )
                        )
                    )
                )
                if abs(total_application_size - total_folder_size) > 1048576:
                    self.log.info(
                        "PLEASE CHECK STATISTICS, APPLICATION SIZE IS INCORRECT !!!"
                    )

            self.log.info(self.__doc__)

            os_sep = self.slash_format
            test_path = self.test_path
            runid = str(self.runid)
            storage_policy = self.storage_policy

            # actual_commit_files IS THE COMMIT FILES
            # PREPARED BY SCAN FOR THE REFERENCE COMMITTED JOB PARAMETERS.

            # expected_commit_files IS THE COMMIT FILES
            # WE EXPECT SCAN TO HAVE PREPARED BASED ON WHAT WE THINK THE COMMIT PARAMETERS MUST BE.

            for scan_type in ScanType:
                # Skip change journal scan for UNIX
                if (
                self.applicable_os != "WINDOWS"
                    and scan_type.value == ScanType.CHANGEJOURNAL.value
                ):
                    continue
                if (
                    self.applicable_os == "WINDOWS"
                    and scan_type.value == ScanType.CHANGEJOURNAL.value
                ):
                    if self.only_dc:
                        self.log.info("ONLY DC is Selected so skipped CJ ")
                        continue
                # Skip DC if verify_dc is not provided
                if (
                    self.applicable_os != "WINDOWS"
                    and scan_type.value == ScanType.OPTIMIZED.value
                ):
                    if not self.verify_dc:
                        continue

                if scan_type.value == ScanType.RECURSIVE.value:
                    if self.only_dc:
                        self.log.info("ONLY DC is selected skipping recursive")
                        continue

                # *****************
                # SCENARIO 1 BEGINS
                # *****************
                scenario_num, scenario = "SCENARIO_1", "Full (Commit) -> Incr."
                log_scenario_details(scenario_num, scenario)

                sc_name = "_".join(
                    ("subclient", str(self.id), scan_type.name.lower(), scenario_num)
                )
                content = [os_sep.join((test_path, sc_name))]
                run_path = os_sep.join((content[0], runid))
                full_path = os_sep.join((run_path, "full"))
                inc_1_path = os_sep.join((run_path, "inc_1"))

                self.log.info("1.00 : Creating a Backupset")
                self.helper.create_backupset(self.bset_name, delete=self.cleanup_run)

                self.log.info("1.01 : Create a subclient.")
                self.helper.create_subclient(
                    sc_name,
                    storage_policy,
                    content,
                    scan_type=scan_type,
                    allow_multiple_readers=True,
                )

                self.log.info("1.02 : Add data for the FULL backup.")
                self.client_machine.generate_test_data(
                    full_path, self.num_dirs, self.num_files, self.file_size_kb
                )

                self.log.info("1.03 : Run a FULL backup and COMMIT it.")
                job_1 = self.helper.run_backup(
                    backup_level="Full", wait_to_complete=False
                )[0]
                self.helper.commit_job(job_1, self.threshold, CommitCondition.FILES)

                self.log.info(
                    f"1.04 : Create the expected commit files for FULL job {job_1.job_id}."
                )
                expected_commit_files = self.helper.create_expected_commit_files(job_1)

                self.log.info("1.05 : Add new data for the INCREMENTAL.")
                self.client_machine.generate_test_data(
                    inc_1_path, self.num_dirs, self.num_files, self.file_size_kb
                )

                self.log.info("1.06 : Run an INCREMENTAL backup and let it COMPLETE.")
                job_2 = self.helper.run_backup(
                    backup_level="Incremental", wait_to_complete=True
                )[0]

                self.log.info("1.07 : Retrieve the commit files prepared by scan.")
                actual_commit_files = self.helper.get_actual_commit_files(job_1)

                self.log.info(
                    f"1.08 : Validating commit files and for committed job {job_1.job_id}."
                )
                self.helper.validate_commit_files(
                    expected_commit_files, actual_commit_files
                )

                self.log.info(f"1.09 : Verify statistics.")
                verify_statistics([job_1, job_2])
                log_scenario_details(scenario_num, scenario, beginning=False)

                # CLEANUP
                if self.cleanup_run:
                    self.client_machine.remove_directory(full_path)
                    self.client_machine.remove_directory(inc_1_path)
                    self.instance.backupsets.delete(self.bset_name)

                # ***************
                # SCENARIO 1 ENDS
                # ***************

                # *****************
                # SCENARIO 2 BEGINS
                # *****************
                scenario_num, scenario = "SCENARIO_2", "Full -> Incr. (Commit) -> Incr."
                log_scenario_details(scenario_num, scenario)

                sc_name = "_".join(
                    ("subclient", str(self.id), scan_type.name.lower(), scenario_num)
                )
                content = [os_sep.join((test_path, sc_name))]
                run_path = os_sep.join((content[0], runid))
                full_path = os_sep.join((run_path, "full"))
                inc_1_path = os_sep.join((run_path, "inc_1"))
                self.tmp_path = self.slash_format.join(
                    (self.test_path, "cvauto_tmp", sc_name, str(self.runid))
                )

                self.log.info("2.00 : Creating a Backupset")
                self.helper.create_backupset(self.bset_name, delete=self.cleanup_run)

                self.log.info("2.01 : Create a subclient.")
                self.helper.create_subclient(
                    sc_name,
                    storage_policy,
                    content,
                    scan_type=scan_type,
                    allow_multiple_readers=True,
                )

                self.log.info("2.02 : Add data for the FULL backup.")
                self.client_machine.generate_test_data(
                    full_path, self.num_dirs, self.num_files, self.file_size_kb
                )

                self.log.info("2.03 : Run a FULL backup and let it COMPLETE.")
                job_1 = self.helper.run_backup(
                    backup_level="Full", wait_to_complete=True
                )[0]

                self.log.info("2.04 : Add new data for the INCREMENTAL.")
                self.client_machine.generate_test_data(
                    inc_1_path, self.num_dirs, self.num_files, self.file_size_kb
                )

                self.log.info("2.05 : Run an INCREMENTAL backup and COMMIT it.")
                job_2 = self.helper.run_backup(
                    backup_level="Incremental", wait_to_complete=False
                )[0]
                self.helper.commit_job(job_2, self.threshold, CommitCondition.FILES)

                self.log.info(
                    f"2.06 : Create expected commit files for INCREMENTAL job {job_2.job_id}."
                )
                expected_commit_files = self.helper.create_expected_commit_files(job_2)

                self.log.info("2.07 : Run an INCREMENTAL backup and let it COMPLETE.")
                job_3 = self.helper.run_backup(
                    backup_level="Incremental", wait_to_complete=True
                )[0]

                self.log.info("2.08 : Retrieve the commit files prepared by scan.")
                actual_commit_files = self.helper.get_actual_commit_files(job_2)

                self.log.info(
                    f"2.09 : Validating commit files for committed job {job_2.job_id}."
                )
                self.helper.validate_commit_files(
                    expected_commit_files, actual_commit_files
                )

                self.log.info(f"2.10 : Verify statistics.")
                verify_statistics([job_1, job_2, job_3])

                self.log.info(f"2.11 : Run an out of place restore and verify.")
                self.helper.run_restore_verify(
                    self.slash_format, run_path, self.tmp_path, str(self.runid)
                )
                log_scenario_details(scenario_num, scenario, beginning=False)

                # CLEANUP
                if self.cleanup_run:
                    self.client_machine.remove_directory(full_path)
                    self.client_machine.remove_directory(inc_1_path)
                    self.instance.backupsets.delete(self.bset_name)
                # ***************
                # SCENARIO 2 ENDS
                # ***************

                # *****************
                # SCENARIO 3 BEGINS
                # *****************
                scenario_num, scenario = (
                    "SCENARIO_3",
                    "Full -> Incr. (Commit) -> Synthetic Full -> Incr.",
                )
                log_scenario_details(scenario_num, scenario)

                sc_name = "_".join(
                    ("subclient", str(self.id), scan_type.name.lower(), scenario_num)
                )
                content = [os_sep.join((test_path, sc_name))]
                run_path = os_sep.join((content[0], runid))
                full_path = os_sep.join((run_path, "full"))
                inc_1_path = os_sep.join((run_path, "inc_1"))

                self.log.info("3.00 : Creating a Backupset")
                self.helper.create_backupset(self.bset_name, delete=self.cleanup_run)

                self.log.info("3.01 : Create a subclient.")
                self.helper.create_subclient(
                    sc_name,
                    storage_policy,
                    content,
                    scan_type=scan_type,
                    allow_multiple_readers=True,
                )

                self.log.info("3.02 : Add data for the FULL backup.")
                self.client_machine.generate_test_data(
                    full_path, self.num_dirs, self.num_files, self.file_size_kb
                )

                self.log.info("3.03 : Run a FULL backup and let it COMPLETE.")
                self.helper.run_backup(backup_level="Full", wait_to_complete=True)

                self.log.info("3.04 : Add new data for the INCREMENTAL.")
                self.client_machine.generate_test_data(
                    inc_1_path, self.num_dirs, self.num_files, self.file_size_kb
                )

                self.log.info("3.05 : Run an INCREMENTAL backup and COMMIT it.")
                job_2 = self.helper.run_backup(
                    backup_level="Incremental", wait_to_complete=False
                )[0]
                self.helper.commit_job(job_2, self.threshold, CommitCondition.FILES)

                self.log.info(
                    f"3.06 : Create expected commit files for INCREMENTAL job {job_2.job_id}."
                )
                expected_commit_files = self.helper.create_expected_commit_files(job_2)

                self.log.info(
                    "3.07 : Run a INCREMENTAL backup AFTER SYNTHETIC FULL and let it COMPLETE."
                )
                job_3 = self.helper.run_backup(
                    backup_level="Synthetic_full", wait_to_complete=True
                )
                job_4 = self.helper.run_backup(
                    backup_level="Incremental", wait_to_complete=True
                )

                self.log.info("3.08 : Retrieve the commit files prepared by scan.")
                actual_commit_files = self.helper.get_actual_commit_files(job_3[0])

                self.log.info(
                    f"3.09 : Validating commit files for committed job {job_3[0].job_id}"
                )
                self.helper.validate_commit_files(
                    expected_commit_files, actual_commit_files, only_cvf=True
                )

                self.log.info(f"3.10 : Verify statistics.")
                verify_statistics([job_3[0], job_4[0]])

                log_scenario_details(scenario_num, scenario, beginning=False)

                # CLEANUP
                if self.cleanup_run:
                    self.client_machine.remove_directory(full_path)
                    self.client_machine.remove_directory(inc_1_path)
                    self.instance.backupsets.delete(self.bset_name)
                # ***************
                # SCENARIO 3 ENDS
                # ***************

        except Exception as exp:
            error_message = "Failed with error: {}".format(str(exp))
            self.log.error(error_message)
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.cleanup_run:
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.bset_name)
