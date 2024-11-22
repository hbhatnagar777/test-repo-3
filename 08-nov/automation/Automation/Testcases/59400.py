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
    """Class for File size change between jobs"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "File size change between jobs"
        self.base_folder_path = None
        self.origin_folder_path = None
        self.is_nas_turbo_type = False
        self.before_mtime = None
        self.OPHelper = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully.")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True)]

        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            self.OPHelper.test_file_list,
            size1=10 * 1024, size2=10 * 1024
        )

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
            "fileSizeGreaterThan": 8,
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
        1. Prepare Test data, Archiveset and Subclient.
        2. Run an archive job.
        3. Wait for the scan phase to complete and pause the job.
        4. Dump some new data to the existing files and resume the job.
        5. All the files should be stubbed correctly. 
        6. Recall the stubs and verify the checksum integrity.
        7. Add few more files and run another archive job.
        8. Wait for the backup phase to complete and pause the job.
        9. Dump some new data to the existing files and resume the job.
        10. Verify that modified files does not get stubbed and unchanged files should get stubbed.
        11. Run another archive job and verify all the files are stubbed.
        12. Recall the stubs and verify the checksum integrity.
        """

        try:

            self.log.info(_desc)
            job = self.OPHelper.run_archive(do_not_wait=True)[0]

            while job.phase.lower() != 'backup':
                time.sleep(5)

            job.pause(wait_for_job_to_pause=True)

            self.log.info("Job paused at backup phase")
            self.OPHelper.client_machine.append_to_file(
                self.OPHelper.client_machine.join_path(self.origin_folder_path, self.OPHelper.test_file_list[0][0]),
                "New content is added such that checksum of the file must change.")
            self.log.info("New content added to 1st text file.")

            self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)

            job.resume(wait_for_job_to_resume=True)
            self.log.info("Job Resumed")

            job.wait_for_completion()

            self.OPHelper.verify_stub(path=self.origin_folder_path, test_data_list=self.OPHelper.test_file_list,
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall()

            self.OPHelper.org_hashcode = self.OPHelper.prepare_turbo_testdata(
                self.origin_folder_path,
                [("test5.txt", True), ("test6.txt", True), ("test7.txt", True), ("test8.txt", True)],
                size1=10 * 1024, size2=10 * 1024,
                backup_type='Incremental'
            )

            job = self.OPHelper.run_archive(do_not_wait=True)[0]

            while job.phase.lower() != 'archive index':
                time.sleep(3)

            job.pause(wait_for_job_to_pause=True)

            self.log.info("Job Paused after backup phase completed ")
            self.OPHelper.client_machine.append_to_file(
                self.OPHelper.client_machine.join_path(self.origin_folder_path, "test5.txt"),
                "New content is added such that checksum of the file must change.")
            self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)
            self.log.info("New content added to 5th text file.")

            job.resume(wait_for_job_to_resume=True)

            job.wait_for_completion()

            self.OPHelper.verify_stub(path=self.origin_folder_path,
                                      test_data_list=[("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                                      ("test4.txt", True), ("test5.txt", False), ("test6.txt", True),
                                                      ("test7.txt", True), ("test8.txt", True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.run_archive()

            self.OPHelper.verify_stub(path=self.origin_folder_path,
                                      test_data_list=[("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                                      ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
                                                      ("test7.txt", True), ("test8.txt", True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall(org_hashcode=self.OPHelper.org_hashcode, path=self.origin_folder_path)

            self.log.info('File size between jobs change passed')

        except Exception as exp:
            self.log.error('File size change between jobs failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
