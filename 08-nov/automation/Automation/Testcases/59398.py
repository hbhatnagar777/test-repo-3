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
import time


class TestCase(CVTestCase):
    """Class for Job restartability at Scan/Backup/Stub phase"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Job restartability at Scan/Backup/Stub phase"
        self.base_folder_path = None
        self.origin_folder_path = None
        self.is_nas_turbo_type = False
        self.before_mtime = None
        self.OPHelper = None
        self.no_of_files = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.no_of_files = int(self.tcinputs.get("NoOfFiles", 1000))
        self.log.info("Test inputs populated successfully.")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.OPHelper.test_file_list = self.OPHelper.test_file_list = [("test{}.txt".format(i), True) for i in
                                                                       range(self.no_of_files)]

        if self.OPHelper.client_machine.check_directory_exists(self.origin_folder_path):
            self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)

        if len(self.OPHelper.org_hashcode) is not self.no_of_files:
            self.OPHelper.prepare_turbo_testdata(
                self.origin_folder_path,
                self.OPHelper.test_file_list,
                size1=8 * 1024, size2=8 * 1024)
            self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.origin_folder_path], scan_type=ScanType.RECURSIVE)
        update_properties = self.OPHelper.testcase.subclient.properties
        update_properties['fsSubClientProp']['checkArchiveBit'] = True
        self.OPHelper.testcase.subclient.update_properties(update_properties)

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 2,
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
        1. Create Large set of test data.
        2. Start an archive job.
        3. Suspend and Resume the job at Scan Phase.
        4. Suspend and Resume the job at Backup Phase.
        5. Suspend and Resume the job at Stubbing Phase.
        6. Verify that job completes without errors. 
        7. Verify that files are stubbed.
        8. Recall the files and verify checksum. 
        """

        try:

            self.log.info(_desc)
            job = self.OPHelper.run_archive(do_not_wait=True)[0]

            self.log.info("Waiting for scan phase to run.")
            job._wait_for_status("RUNNING")
            self.log.info("Pausing job at scan phase.")
            job.pause(wait_for_job_to_pause=True)
            self.log.info("Job paused at scan phase for 30 seconds")
            time.sleep(30)
            job.resume(wait_for_job_to_resume=True)
            self.log.info("Job Resumed")

            self.log.info("Waiting for backup phase to run.")
            while job.phase.lower() != 'backup':
                time.sleep(3)
            job._wait_for_status("RUNNING")
            self.log.info("Pausing job at backup phase.")
            job.pause(wait_for_job_to_pause=True)
            self.log.info("Job paused at backup phase for 30 seconds")
            time.sleep(30)
            job.resume(wait_for_job_to_resume=True)
            self.log.info("Job Resumed")

            if "linux" not in self.client.os_info.lower():
                self.log.info("Waiting for stubbing phase to run.")
                while job.phase.lower() != 'stubbing':
                    time.sleep(3)
                job._wait_for_status("RUNNING")
                self.log.info("Pausing job at stubbing phase.")
                job.pause(wait_for_job_to_pause=True)
                self.log.info("Job paused at stubbing phase for 30 seconds")
                time.sleep(30)
                job.resume(wait_for_job_to_resume=True)
                self.log.info("Job Resumed")

            job.wait_for_completion()

            self.OPHelper.verify_stub(path=self.origin_folder_path, test_data_list=self.OPHelper.test_file_list,
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall()

            self.log.info('Job restartability at Scan/Backup/Stub phase passed')

        except Exception as exp:
            self.log.error('Job restartability at Scan/Backup/Stub phase failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
