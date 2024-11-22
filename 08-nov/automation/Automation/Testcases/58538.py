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
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from AutomationUtils.database_helper import MSSQL
import time


class TestCase(CVTestCase):
    """Class for Retention Verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""

        super(TestCase, self).__init__()
        self.name = "Retention Verification"
        self.show_to_user = True
        self.base_folder_path = None
        self.OPHelper = None
        self.sp = None
        self.db = None
        self.sqldb = None
        self.is_nas_turbo_type = False
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully")

        self.log.info("Setting Copy Retention settings")
        self.sp = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicyName'))
        self.sp.get_copy('Primary').copy_retention = (1, 0, 1)

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.sqldb = MSSQL(self.tcinputs.get("SQLServer"), self.tcinputs.get("SQLUserName"),
                           self.tcinputs.get("SQLPassword"), 'CommServ')

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.OPHelper.prepare_turbo_testdata(
            self.base_folder_path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=20 * 1024)
        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=self.base_folder_path)
        self.log.info("Test data generation completed.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.base_folder_path])

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
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
            "enableArchivingWithRules": True
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Generate test data.
        2. Set 1 Day 0 cycles retention settings in StoragePolicy Properties and 1 Day retention setting in SubClient.
        3. Run Archive jobs [1: Backup Data, 2: Stubbing, 3: Backup Stub].
        4. Change the timestamps of all the jobs to 5 days prior to the original in DB.
        5. Run Data aging.
        6. Confirm Recall fails.
        """

        try:
            job_list = self.OPHelper.run_archive(repeats=3)

            for job in job_list:
                orig_start = job.start_timestamp
                orig_end = job.end_timestamp
                mod_start = int(orig_start) - (5 * 24 * 60 * 60)
                mod_end = int(orig_end) - (5 * 24 * 60 * 60)
                self.log.info("Original Start: " + str(orig_start))
                self.log.info("Original End: " + str(orig_end))
                self.log.info("Modified Start: " + str(mod_start))
                self.log.info("Modified End: " + str(mod_end))
                self.log.info("Job Id: " + job.job_id)
                self.sqldb.execute('UPDATE dbo.JMBkpStats SET servStartDate={0}, servEndDate={1} WHERE jobId={2};'
                                   .format(str(mod_start), str(mod_end), str(job.job_id)))

            if self.commcell.run_data_aging().wait_for_completion():
                time.sleep(120)
                self.log.info("Data aging completed. Performing Recall")
            try:
                self.OPHelper.recall(path=self.base_folder_path)
            except Exception:
                self.log.info('Recall failed, Retention policies are working as expected')
            else:
                raise Exception('Recall Succeeded, Retention policies are not working as expected')

            self.log.info('Retention Verification test passed.')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Retention Verification test failed with error: %s.', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
