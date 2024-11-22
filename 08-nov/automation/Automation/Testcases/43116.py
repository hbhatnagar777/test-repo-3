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

import random
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.winfshelper import WinFSHelper
from cvpysdk.constants import ApplicationGroup


class TestCase(CVTestCase):
    """Class for executing

    Job Status Control - User Defined Error Decision Rules And Error Threshold Rules To Control Job Status
    This test case will verify basic functionality of job status control i.e. error decision rules on Windows.
    This test case does the following.

    *****************
    SCENARIO 1 BEGINS

        **********************************************
        VERIFICATION OF JOB ERROR DECISION RULE BEGINS
        **********************************************

            01. Enable the following Error Decision Rule.
                    File Pattern
                        All File Pattern - ENABLED
                        User Defined Pattern - N/A
                    System Error Code
                        All Error Codes - DISABLED
                        From Value -  2 To Value - 32
                        Skip from reporting error - DISABLED
                    On Error Mark Job as: COMPLETE

            02. Create a new backupset.
            03. Create a new subclient.
            04. Create a few files with extensions .txt, .exe and .pdf.
            05. Lock a few files having different extension types.

            *******************************************
            VERIFICATION OF JOB STATUS CONDITION BEGINS
            *******************************************

            06. Run a Full backup and suspend it after Scan phase.
            07. Rename a few files, resume the job and let it complete. (Rename is akin to delete)
            08. Ensure that job's status is COMPLETE

            09. CHANGE THE VALUE of On Error Mark Job as: to COMPLETED W/ ERROR.
            10. Run a Full backup and suspend it after Scan phase.
            11. Rename a few files, resume the job and let it complete. (Rename is akin to delete)
            12. Ensure that job's status is COMPLETED W/ ERROR

            13. CHANGE THE VALUE of On Error Mark Job as: to FAILED.
            14. Run a Full backup and suspend it after Scan phase.
            15. Rename a few files, resume the job and let it complete. (Rename is akin to delete)
            16. Ensure that job's status is FAILED.

            *****************************************
            VERIFICATION OF JOB STATUS CONDITION ENDS
            *****************************************

            **************************************************
            VERIFICATION OF SYSTEM ERROR CODE CONDITION BEGINS
            **************************************************

            17. CHANGE THE VALUE of To Value to 3.
            18. Run a Full backup and let it complete.
            19. Ensure that job's status is COMPLETE. Although some files are locked, since error code
                32 doesn't fall in range 2-3, the current value for status i.e. FAILED shouldn't be honored.

            ************************************************
            VERIFICATION OF SYSTEM ERROR CODE CONDITION ENDS
            ************************************************

            ************************************************
            VERIFICATION OF SKIP FROM REPORTING ERROR BEGINS
            ************************************************

            20. CHANGE THE VALUE of All Error Codes to ENABLED.
            21. CHANGE THE VALUE of Skip from reporting error to ENABLED.
            22. Run a Full backup and suspend it after Scan phase.
            23. Rename a few files, resume the job and let it complete. (Rename is akin to delete)
            24. Ensure that job's status is COMPLETE. Although some files are locked and were renamed, all error
                codes must be skipped from being reported. Verify that the entries made to Failures.cvf

            **********************************************
            VERIFICATION OF SKIP FROM REPORTING ERROR ENDS
            **********************************************

            25. CHANGE THE VALUE of Skip from reporting error to DISABLED.
            26. CHANGE THE VALUE of All Error Codes to DISABLED.
            27. CHANGE THE VALUE of To Value to 32.
            28. CHANGE THE VALUE of On Error Mark Job as: to COMPLETED WITH ERROR.
            29. CHANGE THE VALUE of All File Pattern to DISABLED.

            ***********************************
            VERIFICATION OF FILE PATTERN BEGINS
            ***********************************

            30. CHANGE THE VALUE of User Defined Pattern to .txt.
            31. Run a Full backup and let it complete.
            32. Ensure that the job's status is COMPLETED W/ ERROR.
            33. Remove lock on .txt files.
            34. Run a Full backup and let it complete.
            35. Ensure that job's status is COMPLETE though value of On Error Mark Job as: is COMPLETED W/ ERROR.
                This is because the rule should not be honored for locked files whose extension is not .txt.
            36. CHANGE THE VALUE of On Error Mark Job as: to FAILED.
            37. Run a Full backup and let it complete.
            38. Ensure that job's status is COMPLETE though value of On Error Mark Job as: is FAILED.
                This is because the rule should not be honored for locked files whose extension is not .txt.
            39. CHANGE THE VALUE of User Defined Pattern to .pdf.
            40. Run a Full backup and let it complete.
            41. Ensure that job's status is FAILED.

            *********************************
            VERIFICATION OF FILE PATTERN ENDS
            *********************************

        42. Delete the rule.

        ********************************************
        VERIFICATION OF JOB ERROR DECISION RULE ENDS
        ********************************************

    SCENARIO 1 ENDS
    ***************

    *****************
    SCENARIO 2 BEGINS

        ***********************************************
        VERIFICATION OF JOB ERROR THRESHOLD RULE BEGINS
        ***********************************************
            43. Enable the following Error Threshold Rule.
                    Mark job as - COMPLETED W/ ERROR  when
                    Number of failed files is more than - 7
                    Percentage of failed files is  more than - 70
                    Apply threshold when - ALL

            44. Create a new subclient.
            45. Create 100 files.
            46. Lock 7 files.
            47. Run a Full backup and let it complete.
            48. Ensure that the job's status is COMPLETE.
                The reason here is ALL rules should match and none of the rules match.
            49. CHANGE THE VALUE of Apply threshold when to ANY.
            50. Run a Full backup and let it complete.
            51. Ensure that the job's status is COMPLETE.
                The reason here is ANY of the rules should match and none of the rules match.
            52. Lock 1 more file.
            53. Run a Full backup and let it complete.
            54. Ensure that the job's status is COMPLETED W/ ERROR.
                The reason here is ANY of the rules should match and Number of failed files is more than MATCHES.
            55. CHANGE THE VALUE of Apply threshold when to ALL.
            56. Run a Full backup and let it complete.
            57. Ensure that the job's status is COMPLETE.
                The reason here is ALL of the rules should match and Percentage of failed files is  more than DOES NOI MATCH.

        *********************************************
        VERIFICATION OF JOB ERROR THRESHOLD RULE ENDS
        *********************************************

        58. Disable the rule.

    SCENARIO 2 ENDS
    ***************

    *************************************
    VERIFY ENTRIES IN FAILURES.CVF BEGINS
    *************************************

    59. Ensure that the entries in Failures.cvf HAVE
          1. 3 special characters prefixed to the file path.
          2. Error code suffixed to the file path.

    ***********************************
    VERIFY ENTRIES IN FAILURES.CVF ENDS
    ***********************************
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Job Status Control - User Defined Error Decision Rules And Error Threshold Rules To Control Job Status"
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
        self.tmp_path = None
        self.log_line = None
        self.cleanup_run = None
        self.RETAIN_DAYS = None
        self.common_args = None
        self.gen_data_args = None
        self.num_dirs = 0
        self.num_files = 10
        self.file_names = []
        self.file_extns = None
        self.files_to_lock = []
        self.files_to_rename = []
        self.job_mgmt_obj = None
        self.sep = "\n\t\t\t\t\t"
        self.locked_file_pids = {}
        self.app_data = ApplicationGroup.WINDOWS
        self.error_rule_dict = {self.app_data: {'rule_1': {'appGroupName': self.app_data,
                                                           'pattern': "*",
                                                           'all_error_codes': False,
                                                           'from_error_code': 1,
                                                           'to_error_code': 2,
                                                           'job_decision': 0,
                                                           'is_enabled': True,
                                                           'skip_reporting_error': False}
                                                }
                                }

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.helper = WinFSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)
        self.file_names = ['file_.txt', 'file_.exe', 'file_.pdf']  # MUST ACCEPT AS INPUT AND MAKE THIS DEFAULT VALUE
        self.file_extns = [file_name.split('.')[1] for file_name in self.file_names]

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
                    self.log.info(f"\n\n\t\t\t\t**********\n\t\t\t\t{sce_num} BEGINS\n\t\t\t\t{scenario}\n\n")
                else:
                    self.log.info(f"\n\n\t\t\t\tEND OF {sce_num}\n\t\t\t\t**********\n\n")

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
                self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name, self.runid))
                self.common_args = {
                    'name': self.sc_name,
                    'content': self.content,
                    'storage_policy': self.storage_policy}
                self.gen_data_args = {'file_path': self.run_path, 'dirs': self.num_dirs, 'files': self.num_files}

            def lock_files():
                """Lock files as required by this test case.

                Args:

                Returns:
                    None

                Raises:
                    None
                """

                files = self.client_machine.get_test_data_info(data_path=self.run_path, name=True).split("\n")
                self.files_to_lock.clear()
                for file_extn in self.file_extns:
                    self.files_to_lock.extend(random.choices(
                        [file for file in files if file.endswith(file_extn)], k=3))
                for file in self.files_to_lock:
                    pid = self.client_machine.lock_file(file, interval=36000)
                    self.locked_file_pids[file] = pid

            def create_files_with_extensions():
                """Creates files with extensions listed in self.file_extns.

                Args:

                Returns:
                    None

                Raises:
                    None
                """
                for file_name in self.file_names:
                    self.client_machine.generate_test_data(
                        self.run_path, self.num_dirs, self.num_files, custom_file_name=file_name)

            def rename_files_and_resume(backup, count=3):
                """Rename 3 files by default which haven't been locked and then resume the job.

                Args:
                    backup  (obj)   --  Instance of Job.

                    count   (int)   --  Specifies how many files need to be locked.

                Returns:
                    None

                Raises:
                    None
                """

                files = [file for file in
                         self.client_machine.get_test_data_info(data_path=self.run_path, name=True).split("\n")
                         if file[-3:] in self.file_extns or file[-3:] == "ren"]

                self.files_to_rename = random.choices(list(set(files).difference(set(self.files_to_lock))), k=count)
                for file in self.files_to_rename:
                    self.client_machine.rename_file_or_folder(file, ''.join((file, '_ren')))

                backup.resume()
                backup.wait_for_completion()

            def suspend_after_scan(backup):
                """Suspend a backup job after Scan phase.

                Args:
                    backup  (obj)   --  Instance of Job object.

                Returns:
                    None

                Raises:
                    None
                """

                # WAIT TILL BACKUP PHASE BEGINS AND ITS STATUS IS RUNNING OR IF JOB HAS COMPLETED
                while True:
                    if backup.phase.upper() == "BACKUP":
                        backup.pause(wait_for_job_to_pause=True)
                        break

            def check_job_status_raise_exception(job, expected_status):
                """
                Args:
                    job             (obj)   --  Instance of Job

                    expected_status (str)   --  Expected status string

                Returns:
                    None

                Raises:
                    Exception if the observed status does not match up with expected status.

                """
                if job.status.upper() != expected_status.upper():
                    raise Exception(f"Expected Status = {expected_status}, Observed Status = {job.status}")

            self.log.info(self.__doc__)

            self.log.info("03. Create a new backupset")
            self.helper.create_backupset(self.bset_name)

            # *****************
            # SCENARIO 1 BEGINS
            # *****************
            sce_num, scenario = "SCENARIO_1", "VERIFICATION OF JOB ERROR DECISION RULE BEGINS"
            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num)

            self.log.info("01. Enable the Error Decision Rule. (PLEASE REFER ABOVE FOR RULE DETAILS)")
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("02. Create a new backupset.")
            self.helper.create_backupset(self.bset_name)

            self.log.info("03. Create a new subclient.")
            self.helper.create_subclient(**self.common_args)
            # MUST CHECK IF RUNNING ON WINDOWS AND THEN ONLY UPDATE SUBCLIENT, WILL BE DONE IF UNIX SUPPORT IS ADDED.
            self.helper.update_subclient(use_vss={'useVSS': False, 'useVssForAllFilesOptions': 3, 'vssOptions': 2})

            self.log.info("04. Create a few files with extensions .txt, .exe and .pdf.")
            create_files_with_extensions()

            self.log.info("05. Lock a few files having different extension types.")
            lock_files()

            self.log.info("06. Run a Full backup and suspend it after Scan phase.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            suspend_after_scan(full_bkp)

            self.log.info("07. Rename a few files, resume the job and let it complete. (Rename is akin to delete)")
            rename_files_and_resume(backup=full_bkp)

            self.log.info("08. Ensure that job's status is COMPLETED")
            check_job_status_raise_exception(full_bkp, "COMPLETED")

            self.log.info("09. CHANGE THE VALUE of On Error Mark Job as: to COMPLETED W/ ONE OR MORE ERRORS.")
            self.error_rule_dict[self.app_data]['rule_1']['job_decision'] = 1
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("10. Run a Full backup and suspend it after Scan phase.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            suspend_after_scan(full_bkp)

            self.log.info("11. Rename a few files, resume the job and let it complete. (Rename is akin to delete)")
            rename_files_and_resume(backup=full_bkp)

            self.log.info("12. Ensure that job's status is COMPLETED W/ ONE OR MORE ERRORS")
            check_job_status_raise_exception(full_bkp, "COMPLETED W/ ONE OR MORE ERRORS")

            self.log.info("13. CHANGE THE VALUE of On Error Mark Job as: to FAILED.")
            self.error_rule_dict[self.app_data]['rule_1']['job_decision'] = 2
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("14. Run a Full backup and suspend it after Scan phase.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            suspend_after_scan(full_bkp)

            self.log.info("15. Rename a few files, resume the job and let it complete. (Rename is akin to delete)")
            rename_files_and_resume(backup=full_bkp)

            self.log.info("16. Ensure that job's status is FAILED.")
            check_job_status_raise_exception(full_bkp, "FAILED")

            self.log.info("17. CHANGE THE VALUE of To Value to 3.")
            self.error_rule_dict[self.app_data]['rule_1']['to_error_code'] = 3
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("18. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("19. Ensure job's status is COMPLETE. Although some files are locked, since error code 32")
            self.log.info("    doesn't fall in range 2-3, current value for status i.e. FAILED shouldn't be honored.")
            check_job_status_raise_exception(full_bkp, "COMPLETED")

            self.log.info("20. CHANGE THE VALUE of All Error Codes to ENABLED.")
            self.error_rule_dict[self.app_data]['rule_1']['all_error_codes'] = True

            self.log.info("21. CHANGE THE VALUE of Skip from reporting error to ENABLED.")
            self.error_rule_dict[self.app_data]['rule_1']['skip_reporting_error'] = True

            # UPDATING THE ERROR CONTROL RULE
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("22. Run a Full backup and suspend it after Scan phase.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            suspend_after_scan(full_bkp)

            self.log.info("23. Rename a few files, resume the job and let it complete. (Rename is akin to delete)")
            rename_files_and_resume(backup=full_bkp)

            self.log.info("24. Ensure job's status is FAILED and error codes were skipped from being reported.")
            self.log.info("Ensure failed file entries made it to Failures.cvf ->NOT IMPLEMENTED.")
            check_job_status_raise_exception(full_bkp, "FAILED")
            # MIGHT NEED TO FIGURE A WAY TO REVIEW FAILURES.CVF

            self.log.info("25. CHANGE THE VALUE of Skip from reporting error to DISABLED.")
            self.error_rule_dict[self.app_data]['rule_1']['skip_reporting_error'] = False

            self.log.info("26. CHANGE THE VALUE of All Error Codes to DISABLED.")
            self.error_rule_dict[self.app_data]['rule_1']['all_error_codes'] = False

            self.log.info("27. CHANGE THE VALUE of To Value to 32.")
            self.error_rule_dict[self.app_data]['rule_1']['to_error_code'] = 32

            self.log.info("28. CHANGE THE VALUE of On Error Mark Job as: to COMPLETED W/ ONE OR MORE ERRORS.")
            self.error_rule_dict[self.app_data]['rule_1']['job_decision'] = 1

            self.log.info("30. CHANGE THE VALUE of User Defined Pattern to *.txt.")
            self.error_rule_dict[self.app_data]['rule_1']['pattern'] = "*.txt"

            # UPDATING THE ERROR CONTROL RULE
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("31. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            full_bkp.wait_for_completion()

            self.log.info("32. Ensure that the job's status is COMPLETED WITH ONE OR MORE ERRORS.")
            check_job_status_raise_exception(full_bkp, "COMPLETED W/ ONE OR MORE ERRORS")

            self.log.info("33. Remove lock on .txt files.")
            locked_text_files_pids = {file: pid for file,
                                      pid in self.locked_file_pids.items() if file.endswith(".txt")}
            for pid in locked_text_files_pids.values():
                self.client_machine.execute_command(f"Stop-Process -Id {pid}")

            self.log.info("34. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            full_bkp.wait_for_completion()

            self.log.info("35. Ensure status is COMPLETED though value of On Error Mark Job as: is COMPLETED W/ ERROR.")
            self.log.info("    This is because rule shouldn't honored for locked files whose extension is not .txt.")
            check_job_status_raise_exception(full_bkp, "COMPLETED")

            self.log.info("36. CHANGE THE VALUE of On Error Mark Job as: to FAILED.")
            self.error_rule_dict[self.app_data]['rule_1']['job_decision'] = 2
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("37. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            full_bkp.wait_for_completion()

            self.log.info("38. Ensure that job's status is COMPLETE though value of On Error Mark Job as: is FAILED,")
            self.log.info("    since rule shouldn't be honored for locked files whose extension isn't .txt.")
            check_job_status_raise_exception(full_bkp, "COMPLETED")

            self.log.info("39. CHANGE THE VALUE of User Defined Pattern to *.pdf.")
            self.error_rule_dict[self.app_data]['rule_1']['pattern'] = "*.pdf"
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            self.log.info("40. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            full_bkp.wait_for_completion()

            self.log.info("41. Ensure that job's status is FAILED.")
            check_job_status_raise_exception(full_bkp, "FAILED")

            self.log.info("42. Disable the rule.")
            self.error_rule_dict[self.app_data]['rule_1']['is_enabled'] = False
            self.commcell.job_management.error_rules.add_error_rule(self.error_rule_dict)

            # ***************
            # SCENARIO 1 ENDS
            # ***************

            # *****************
            # SCENARIO 2 BEGINS
            # *****************
            """
            sce_num, scenario = "SCENARIO_2", ".............."
            log_scenario_details(sce_num, scenario)
            initialize_scenario_attributes(sce_num)

            self.log.info("43.Enable the following Error Threshold Rule.")
            # LOG RULE DETAILS HERE WHEN FILLING OUT THIS TEST CASE.

            self.log.info("44. Create a new subclient.")
            self.helper.create_subclient(**self.comn_args)

            self.log.info("45. Create 100 files.")
            self.client_machine.generate_test_data(self.run_path, self.num_dirs, files=100)

            self.log.info("46. Lock 7 files.")
            files_to_lock = random.choices(self.client_machine.get_test_data_info(data_path=self.run_path, name=True), k=7)
            self.client_machine.lock_file(file_list=files_to_lock)

            self.log.info("47. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")

            self.log.info("48. Ensure that the job's status is COMPLETE.")
            check_job_status_raise_exception(full_bkp, "COMPLETE")

            self.log.info("    The reason here is ALL rules should match and none of the rules match.")
            self.log.info("49. CHANGE THE VALUE of Apply threshold when to ANY.")

            self.log.info("50. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")

            self.log.info("51. Ensure that the job's status is COMPLETE.")
            self.log.info("    The reason here is ANY of the rules should match and none of the rules match.")
            self.log.info("52. Lock 1 more file.")

            self.log.info("53. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")

            self.log.info("54. Ensure that the job's status is COMPLETED WITH ONE OR MORE ERRORS.")
            self.log.info("    The reason here is ANY of the rules should match and Number of failed files is more than MATCHES.")
            check_job_status_raise_exception(full_bkp, "COMPLETED W/ ONE OR MORE ERRORS")

            self.log.info("55. CHANGE THE VALUE of Apply threshold when to ALL.")

            self.log.info("56. Run a Full backup and let it complete.")
            full_bkp = self.helper.run_backup(backup_level="Full")

            self.log.info("57. Ensure that the job's status is COMPLETE.")
            self.log.info("    The reason here is ALL of the rules should match and Percentage of failed files is  more than DOES NOI MATCH.")
            self.log.info("58. Delete the rule.")
            self.log.info("59. Ensure that the entries in Failures.cvf HAVE")
            self.log.info("1. 3 special characters prefixed to the file path.")
            self.log.info("2. Error code suffixed to the file path.")

            log_scenario_details(sce_num, scenario, beginning=False)
            """
            # ***************
            # SCENARIO 2 ENDS
            # ***************

            # DELETING TEST DATASET & DELETING BACKUPSET

            if self.cleanup_run:
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.bset_name)
            else:
                self.client_machine.remove_directory(self.test_path, self.RETAIN_DAYS)

            # DELETE RULES
            # REMOVE LOCKS

        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED
