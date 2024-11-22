# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper, ScanType
from AutomationUtils import constants
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
import datetime
import time


class TestCase(CVTestCase):
    """Class to verify Multiple Copies - Copy with the longest retention retains the job."""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Multiple Copies - Copy with the longest retention retains the job."
        self.base_folder_path = None
        self.OPHelper = None
        self.MAHelper = None
        self.is_nas_turbo_type = False
        self.sp = None
        self.copy1 = None
        self.copy2 = None
        self.primary_copy = None
        self.db = None
        self.sqldb = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "SecondaryCopyLibraryName": None,
            "SecondaryMAName": None,
            "PrimaryMAName": None,
            "PrimaryCopyLibraryName": None,
            "ThirdMAName": None,
            "ThirdCopyLibraryName": None,
            "SQLServer": None,
            "SQLUserName": None,
            "SQLPassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.MAHelper = MMHelper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.sqldb = MSSQL(self.tcinputs.get("SQLServer"), self.tcinputs.get("SQLUserName"),
                           self.tcinputs.get("SQLPassword"), 'CommServ')

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.MAHelper.configure_storage_policy(storage_policy_name=self.tcinputs.get('StoragePolicyName'),
                                               library_name=self.tcinputs.get('PrimaryCopyLibraryName'),
                                               ma_name=self.tcinputs.get('PrimaryMAName'))
        self.sp = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicyName'))

        self.primary_copy = self.sp.get_copy(self.tcinputs.get('PrimaryCopyName', 'Primary'))
        self.primary_copy.copy_retention = (1, 0, 1)

        self.copy1 = self.MAHelper.configure_secondary_copy(
            sec_copy_name=self.tcinputs.get('SecondaryCopyName', 'Copy-2'),
            storage_policy_name=self.tcinputs.get('StoragePolicyName'),
            library_name=self.tcinputs.get('SecondaryCopyLibraryName'),
            ma_name=self.tcinputs.get('SecondaryMAName'))
        self.copy1.copy_retention = (4, 0, 4)

        self.copy2 = self.MAHelper.configure_secondary_copy(sec_copy_name=self.tcinputs.get('ThirdCopyName', 'Copy-3'),
                                                            storage_policy_name=self.tcinputs.get('StoragePolicyName'),
                                                            library_name=self.tcinputs.get('ThirdCopyLibraryName'),
                                                            ma_name=self.tcinputs.get('ThirdMAName'))
        self.copy2.copy_retention = (10, 0, 10)

        self.OPHelper.prepare_turbo_testdata(
            self.base_folder_path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=20 * 1024)
        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=self.base_folder_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.base_folder_path], scan_type=ScanType.RECURSIVE)

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True,
            'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%', '%Audio%']}
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 0

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Configure Primary copy with 1 day, Secondary with 4 days and Third copy with 10 days retention.
        2. Configure subclient retention to be 0 days. 
        3. Run Archiving Job on primary and validate stub creation.
        4. Run Auxcopy job to secondary and third copy. 
        5. Change the job start and end time to 8 days older.
        6. Run data aging job. 
        7. Verify that third copy still contains the jobs.
        8. Run Recall and Validate that file is recalled from third copy.
        9. Change the job start and end time to 13 days older.
        10. Run data aging job. 
        11. Run Recall and Validate that file is not recalled.
        """

        try:
            self.log.info(_desc)
            job_list = self.OPHelper.run_archive(repeats=1)

            time.sleep(100)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            # Commented below lines as Aux copy job is ran automatically now.
            # self.log.info("Start Running Aux Copy")
            # aux_job = self.sp.run_aux_copy(all_copies=True)
            # aux_job.wait_for_completion()
            # self.log.info("Completed Running Aux Copy")

            self.log.info("Changing Job time to prior to 8 days.")
            for job in job_list:
                orig_start = job.start_timestamp
                orig_end = job.end_timestamp
                mod_start = int(orig_start) - (8 * 24 * 60 * 60)
                mod_end = int(orig_end) - (8 * 24 * 60 * 60)
                self.log.info("Original Start: " + str(orig_start))
                self.log.info("Original End: " + str(orig_end))
                self.log.info("Modified Start: " + str(mod_start))
                self.log.info("Modified End: " + str(mod_end))
                self.log.info("Job Id: " + job.job_id)
                self.sqldb.execute('UPDATE dbo.JMBkpStats SET servStartDate={0}, servEndDate={1} WHERE jobId={2};'
                                   .format(str(mod_start), str(mod_end), str(job.job_id)))

            self.commcell.run_data_aging().wait_for_completion()
            time.sleep(600)
            self.log.info("Data aging completed.")

            self.primary_copy.refresh()
            self.copy1.refresh()
            self.copy2.refresh()

            time.sleep(600)

            for job in job_list:
                self.log.info("Validating job " + str(job.job_id))
                if not self.MAHelper.validate_job_prune(copy_id=self.primary_copy.copy_id, job_id=job.job_id):
                    raise Exception(
                        "Primary copy job is not pruned. It is expected to be pruned according to retention rules.")
                if not self.MAHelper.validate_job_prune(copy_id=self.copy1.copy_id, job_id=job.job_id):
                    raise Exception(
                        "Secondary copy job is not pruned. It is expected to be pruned according to retention rules.")
                if self.MAHelper.validate_job_prune(copy_id=self.copy2.copy_id, job_id=job.job_id):
                    raise Exception(
                        "Third copy job is pruned. It is not expected to be pruned according to retention rules.")
                self.log.info("Validated job " + str(job.job_id))

            time.sleep(60)
            try:
                self.OPHelper.recall(org_hashcode=[self.OPHelper.org_hashcode[0]],
                                     path=self.OPHelper.client_machine.join_path(self.base_folder_path,
                                                                                 self.OPHelper.test_file_list[0][
                                                                                     0]))
            finally:
                time.sleep(60)
                self.log.info("Trying another recall.")
                self.OPHelper.recall(org_hashcode=[self.OPHelper.org_hashcode[0]],
                                     path=self.OPHelper.client_machine.join_path(self.base_folder_path,
                                                                                 self.OPHelper.test_file_list[0][
                                                                                     0]))

            self.log.info("Changing Job time to prior to 13 days.")
            for job in job_list:
                orig_start = job.start_timestamp
                orig_end = job.end_timestamp
                mod_start = int(orig_start) - (13 * 24 * 60 * 60)
                mod_end = int(orig_end) - (13 * 24 * 60 * 60)
                self.log.info("Original Start: " + str(orig_start))
                self.log.info("Original End: " + str(orig_end))
                self.log.info("Modified Start: " + str(mod_start))
                self.log.info("Modified End: " + str(mod_end))
                self.log.info("Job Id: " + job.job_id)
                self.sqldb.execute('UPDATE dbo.JMBkpStats SET servStartDate={0}, servEndDate={1} WHERE jobId={2};'
                                   .format(str(mod_start), str(mod_end), str(job.job_id)))

            self.commcell.run_data_aging().wait_for_completion()
            time.sleep(600)
            self.log.info("Data aging completed.")

            self.primary_copy.refresh()
            self.copy1.refresh()
            self.copy2.refresh()

            time.sleep(600)

            for job in job_list:
                self.log.info("Validating job " + str(job.job_id))
                if not self.MAHelper.validate_job_prune(copy_id=self.primary_copy.copy_id, job_id=job.job_id):
                    raise Exception(
                        "Primary copy job is not pruned. It is expected to be pruned according to retention rules.")
                if not self.MAHelper.validate_job_prune(copy_id=self.copy1.copy_id, job_id=job.job_id):
                    raise Exception(
                        "Secondary copy job is not pruned. It is expected to be pruned according to retention rules.")
                if not self.MAHelper.validate_job_prune(copy_id=self.copy2.copy_id, job_id=job.job_id):
                    raise Exception(
                        "Third copy job is not pruned. It is expected to be pruned according to retention rules.")
                self.log.info("Validated job " + str(job.job_id))

            try:
                time.sleep(900)
                self.OPHelper.recall(path=self.base_folder_path)
            except Exception:
                self.log.info('Recall failed, Retention policies are working as expected')
            else:
                raise Exception('Recall Succeeded, Retention policies are not working as expected')

            self.log.info('Multiple Copies - Copy with the longest retention retains the job passed.')

        except Exception as exp:
            self.log.error('Multiple Copies - Copy with the longest retention retains the job  failed with error: %s',
                           exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
