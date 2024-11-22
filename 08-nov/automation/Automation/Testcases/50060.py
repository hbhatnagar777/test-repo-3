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

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper, CommitCondition


class TestCase(CVTestCase):
    """Class for executing this test case

    Verifying FS Commit for Jobs in Pending State
    We will check the following cases:

    1. FULL (Commit in Pending State) -> INCR. -> Validation -> Restore
    2. FULL (Commit in Pending State) -> INCR. (Commit in Pending State) -> Validation -> INCR. -> Restore
    3. FULL(Commit in Pending State)->INCR.(Commit in Pending State) -> Validation -> SFULL-> INCR -> Restore.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.registry_path = None
        self.registry_value = None
        self.name = "Verifying FS Commit for Jobs in Pending State"
        self.client_machine = None
        self.slash_format = None
        self.test_path = None
        self.dest_path = None
        self.helper = None
        self.backupset_name = None
        self.num_dirs = 1
        self.runid = None
        self.cleanup_run = None
        self.machine = None
        self.num_files = None
        self.file_size_kb = None
        self.threshold = None
        self.RETAIN_DAYS = None
        self.tcinputs = {"StoragePolicyName": None, "TestPath": None}

    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        self.machine = Machine(self.client)
        self.test_path = self.tcinputs["TestPath"]
        self.helper.populate_tc_inputs(self)
        self.num_files = int(self.tcinputs.get("No_of_files", 35))
        self.file_size_kb = int(self.tcinputs.get("File_length", 102400))
        self.threshold = int(self.tcinputs.get("threshold", 3))

    def run(self):
        """Run function of this test case"""
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

                Raises:each in
                    None

                """
                if beginning:
                    self.log.info("**********")
                    self.log.info("%s : %s", scenario_num, scenario)
                else:
                    self.log.info("END OF %s", scenario_num)
                    self.log.info("**********")

            os_sep = self.machine.os_sep
            if self.test_path.endswith(os_sep):
                self.test_path = self.test_path.rstrip(os_sep)
            self.log.info(
                "Create a backupset for the scenarios if not already present."
            )
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=True)
            self.backupset_name = backupset_name

            # ***************
            # SETTING REGISTRY TO DISABLE JR CLEANUP
            # ***************

            self.registry_path = "FileSystemAgent"
            self.registry_value = "bEnableAutoSubclientDirCleanup"
            if self.machine.os_info == "WINDOWS":
                if not self.machine.check_registry_exists(
                    key=self.registry_path, value=self.registry_value
                ):
                    self.machine.create_registry(
                        key=self.registry_path,
                        value=self.registry_value,
                        data=0,
                        reg_type="DWord",
                    )
                    self.log.info("Registry To disable JR cleanup successful")
                else:
                    self.machine.update_registry(
                        key=self.registry_path,
                        value=self.registry_value,
                        data=0,
                        reg_type="DWord",
                    )
                    self.log.info(
                        "Registry exists. Updated to disable JR cleanup successful"
                    )

            elif self.machine.os_info == "UNIX":
                if not self.machine.check_registry_exists(
                    key=self.registry_path, value=self.registry_value
                ):
                    self.machine.create_registry(
                        key=self.registry_path, value=self.registry_value, data=0
                    )
                    self.log.info("Registry To disable JR cleanup successful")
                else:
                    self.machine.update_registry(
                        key=self.registry_path, value=self.registry_value, data=0
                    )
                    self.log.info(
                        "Registry exists. Updated to disable JR cleanup successful"
                    )

            # ***************
            # CASE 1 BEGINS
            # ***************
            scenario_num, scenario_name = (
                "1",
                "FULL (Commit in Pending State) -> " "INCR. -> Validation -> Restore",
            )
            log_scenario_details(scenario_num, scenario_name, beginning=True)
            sc_name = "_".join(("subclient", str(self.id), scenario_num))
            subclient_content = [self.machine.join_path(self.test_path, sc_name)]
            tmp_path = self.machine.join_path(
                self.test_path, "cvauto_tmp", str(self.runid)
            )
            run_path = self.machine.join_path(subclient_content[0], str(self.runid))
            full_con_path = self.machine.join_path(run_path, "full" + scenario_num)
            inc_con_path = self.machine.join_path(run_path, "inc" + scenario_num)

            self.log.info("1.1 : Create a subclient.")
            self.helper.create_subclient(
                name=sc_name,
                storage_policy=self.tcinputs["StoragePolicyName"],
                content=subclient_content,
                allow_multiple_readers=True,
            )

            self.log.info("1.2 : Add Data for Full Backup.")
            self.client_machine.generate_test_data(
                full_con_path, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("1.3 : Run a Full Backup for Some time.")
            job_1 = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[
                0
            ]

            self.log.info("1.4 : Commit the Backup Job after threshold is reached.")
            self.helper.commit_job(
                job_1, self.threshold, CommitCondition.FILES, timeout=600, pending=True
            )

            self.log.info("1.5 : Add data for the INCREMENTAL Backup")
            self.client_machine.generate_test_data(
                inc_con_path, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("1.6 : Run an INCREMENTAL backup and let it COMPLETE.")
            job_3 = self.helper.run_backup(
                backup_level="Incremental", wait_to_complete=True
            )[0]

            self.log.info(
                f"1.7 : Create the expected commit files for FULL job {job_1.job_id}."
            )
            expected_commit_files = self.helper.create_expected_commit_files(job_1)

            self.log.info("1.8 : Retrieve the commit files prepared by scan.")
            actual_commit_files = self.helper.get_actual_commit_files(job_1)

            self.log.info(
                f"1.10 : Validating commit files for committed job {job_1.job_id}."
            )
            result = self.helper.validate_commit_files(
                expected_commit_files, actual_commit_files, only_cvf=True
            )
            if result == False:
                raise Exception("Validation failed")
            self.log.info("1.10 : Verify by Restore from All Backup")
            self.helper.run_restore_verify(
                os_sep, subclient_content[0], tmp_path, sc_name
            )

            if self.cleanup_run:
                self.client_machine.remove_directory(full_con_path)
                self.client_machine.remove_directory(inc_con_path)
                self.instance.backupsets.delete(self.backupset_name)

            log_scenario_details(scenario_num, scenario_name, beginning=False)
            # ***************
            # CASE 1 ENDS
            # ***************

            # ***************
            # CASE 2 BEGINS
            # ***************
            scenario_num, scenario_name = (
                "2",
                "FULL (Commit in Pending State) -> "
                "INCR. (Commit in Pending State) -> "
                "Validation -> INCR. -> Restore",
            )
            log_scenario_details(scenario_num, scenario_name, beginning=True)
            sc_name = "_".join(("subclient", str(self.id), scenario_num))
            subclient_content = [self.machine.join_path(self.test_path, sc_name)]
            run_path = self.machine.join_path(subclient_content[0], str(self.runid))
            full_con_path = self.machine.join_path(run_path, "full" + scenario_num)
            inc_con_path = self.machine.join_path(run_path, "inc" + scenario_num)
            inc_con_path1 = self.machine.join_path(run_path, "inc" + scenario_num + "1")

            self.log.info(
                "Create a backupset for the scenarios if not already present."
            )
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=True)
            self.backupset_name = backupset_name

            self.log.info("2.1 : Create a subclient.")
            self.helper.create_subclient(
                name=sc_name,
                storage_policy=self.tcinputs["StoragePolicyName"],
                content=subclient_content,
                allow_multiple_readers=True,
            )

            self.log.info("2.2 : Add Data for Full Backup.")
            self.client_machine.generate_test_data(
                full_con_path, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("2.3 : Run a Full Backup for Some time.")
            job_1 = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[
                0
            ]

            self.log.info("2.4 : Commit the Backup Job after threshold is reached.")
            self.helper.commit_job(
                job_1, self.threshold, CommitCondition.FILES, timeout=600, pending=True
            )

            self.log.info("2.5 : Add data for the INCREMENTAL Backup-COMMIT")
            self.client_machine.generate_test_data(
                inc_con_path, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("2.6 : Run an INCREMENTAL backup and let it COMMIT as well.")
            job_3 = self.helper.run_backup(
                backup_level="Incremental", wait_to_complete=False
            )[0]

            self.log.info("2.7 : Commit the Backup Job after threshold is reached.")
            self.helper.commit_job(
                job_3, self.threshold, CommitCondition.FILES, timeout=600, pending=True
            )

            self.log.info(
                f"2.8 : Create expected commit files for FULL job {job_1.job_id}."
            )
            expected_commit_files = self.helper.create_expected_commit_files(job_1)

            self.log.info(
                "2.9 : Retrieve the commit files prepared by scan for FULL job."
            )
            actual_commit_files = self.helper.get_actual_commit_files(job_1)

            self.log.info(
                f"2.10 : Validating commit files for committed job {job_1.job_id}."
            )
            result = self.helper.validate_commit_files(
                expected_commit_files, actual_commit_files, only_cvf=True
            )
            if result == False:
                raise Exception("Validation failed")

            self.log.info("2.11 : Add data for the INCREMENTAL Backup-COMPLETE")
            self.client_machine.generate_test_data(
                inc_con_path1, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("2.12 : Run an INCREMENTAL backup and let it COMPLETE.")
            job_4 = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info(
                "2.13 : Checking DCTmp.cvf to DCInc.cvf renaming using expected Commit file"
                "for INC COMPLETE job"
            )
            self.helper.create_expected_commit_files(job_3)

            self.log.info("2.14 : Verify by Restore from All Backups")
            self.helper.run_restore_verify(
                os_sep, subclient_content[0], tmp_path, sc_name
            )

            log_scenario_details(scenario_num, scenario_name, beginning=False)

            if self.cleanup_run:
                self.client_machine.remove_directory(full_con_path)
                self.client_machine.remove_directory(inc_con_path)
                self.client_machine.remove_directory(inc_con_path1)
                self.instance.backupsets.delete(self.backupset_name)
            # ***************
            # CASE 2 ENDS
            # ***************

            # ***************
            # CASE 3 BEGINS
            # ***************
            scenario_num, scenario_name = (
                "3",
                "FULL(Commit in Pending State)->"
                "INCR.(Commit in Pending State) -> "
                "Validation -> SFULL-> INCR -> Restore",
            )
            log_scenario_details(scenario_num, scenario_name, beginning=True)
            sc_name = "_".join(("subclient", str(self.id), scenario_num))
            subclient_content = [self.machine.join_path(self.test_path, sc_name)]
            run_path = self.machine.join_path(subclient_content[0], str(self.runid))
            full_con_path = self.machine.join_path(run_path, "full" + scenario_num)
            inc_con_path = self.machine.join_path(run_path, "inc" + scenario_num)

            self.log.info(
                "Create a backupset for the scenarios if not already present."
            )
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=True)
            self.backupset_name = backupset_name

            self.log.info("3.1 : Create a subclient.")
            self.helper.create_subclient(
                name=sc_name,
                storage_policy=self.tcinputs["StoragePolicyName"],
                content=subclient_content,
                allow_multiple_readers=True,
            )

            self.log.info("3.2 : Add Data for Full Backup.")
            self.client_machine.generate_test_data(
                full_con_path, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("3.3 : Run a Full Backup for Some time.")
            job_1 = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[
                0
            ]

            self.log.info("3.4 : Commit the Backup Job after threshold is reached.")
            self.helper.commit_job(
                job_1, self.threshold, CommitCondition.FILES, timeout=600, pending=True
            )

            self.log.info("3.5 : Add data for the INCREMENTAL Backup-COMMIT")
            self.client_machine.generate_test_data(
                inc_con_path, self.num_dirs, self.num_files, self.file_size_kb
            )

            self.log.info("3.6 : Run an INCREMENTAL backup and let it COMMIT as well.")
            job_3 = self.helper.run_backup(
                backup_level="Incremental", wait_to_complete=False
            )[0]

            self.log.info("3.7 : Commit the Backup Job after threshold is reached.")
            self.helper.commit_job(
                job_3, self.threshold, CommitCondition.FILES, timeout=600, pending=True
            )

            self.log.info(
                f"3.8 : Create expected commit files for FULL job {job_1.job_id}."
            )
            expected_commit_files = self.helper.create_expected_commit_files(job_1)

            self.log.info(
                "3.9 : Retrieve the commit files prepared by scan for Full job."
            )
            actual_commit_files = self.helper.get_actual_commit_files(job_1)

            self.log.info(
                f"3.10 : Validating commit files for committed job {job_1.job_id}."
            )
            result = self.helper.validate_commit_files(
                expected_commit_files, actual_commit_files, only_cvf=True
            )
            if result == False:
                raise Exception("Validation failed")
            self.log.info("3.11 : Run a SYNTHETIC Full Backup and then INCREMENTAL")
            job_4 = self.helper.run_backup(
                backup_level="Synthetic_full",
                incremental_backup=True,
                incremental_level="AFTER_SYNTH",
            )[0]

            self.log.info(
                "3.12 : Checking DCTmp.cvf to DCInc.cvf renaming using expected Commit file"
                "for SYN+INC job"
            )
            self.helper.create_expected_commit_files(job_3)

            self.log.info("3.13 : Verify by Restore from All Backups")
            self.helper.run_restore_verify(
                os_sep, subclient_content[0], tmp_path, sc_name
            )

            log_scenario_details(scenario_num, scenario_name, beginning=False)

            # ***************
            # CASE 3 ENDS
            # ***************

            # DELETING TEST DATASET & DELETING BACKUPSET
            if self.cleanup_run:
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.backupset_name)
                self.machine.remove_registry(
                    key=self.registry_path,
                    value=self.registry_value,
                )
            else:
                self.client_machine.remove_directory(self.test_path, self.RETAIN_DAYS)

        except Exception as exp:
            self.log.error("Failed to execute test case with error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.cleanup_run:
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.backupset_name)
                self.machine.remove_registry(
                    key=self.registry_path,
                    value=self.registry_value,
                )
            else:
                self.client_machine.remove_directory(self.test_path, self.RETAIN_DAYS)
