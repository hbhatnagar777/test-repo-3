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
import threading


class TestCase(CVTestCase):
    """Class for Kill job in middle of backup phase"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Kill job in middle of backup phase"
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
                                        ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
                                        ("test7.txt", True), ("test8.txt", True), ("test9.txt", True),
                                        ("test10.txt", True), ("test11.txt", True), ("test12.txt", True),
                                        ("test13.txt", True), ("test14.txt", True), ("test15.txt", True),
                                        ("test16.txt", True), ("test17.txt", True), ("test18.txt", True),
                                        ("test19.txt", True), ("test20.txt", True)]

        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
             ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
             ("test7.txt", True), ("test8.txt", True), ("test9.txt", True),
             ("test10.txt", True), ("test11.txt", True), ("test12.txt", True),
             ("test13.txt", True), ("test14.txt", True), ("test15.txt", True),
             ("test16.txt", True), ("test17.txt", True), ("test18.txt", True)],
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
        3. Wait for the backup phase to run and kill the job in the middle of backup phase.
        4. Add few more files to the test data.
        5. Run another incremental job.
        6. Verify that all the qualified files are stubbed. 
        7. Recall the stubs and verify the checksum integrity.
        """

        try:

            self.log.info(_desc)
            job = self.OPHelper.run_archive(do_not_wait=True)[0]

            self.log.info("Waiting for the backup phase to start")
            while job.phase.lower() != 'backup':
                time.sleep(7)
                job.refresh()

            self.log.info("Waiting for the backup phase to run")
            job._wait_for_status("RUNNING")

            files_transferred = job.num_of_files_transferred
            self.log.info("Number of files transferred out of 18 are %s", files_transferred)
            while files_transferred < 1:
                time.sleep(3)
                files_transferred = job.num_of_files_transferred
                self.log.info("Number of files transferred out of 18 are %s", files_transferred)

            time.sleep(self.tcinputs.get("TimeToKillBackup", 0))
            self.log.info("Killing the backup job")
            job.kill()
            self.log.info("Job Killed")
            job._wait_for_status("KILLED")

            self.log.info("Killed the job")

            self.OPHelper.org_hashcode = self.OPHelper.prepare_turbo_testdata(
                self.origin_folder_path,
                [("test19.txt", True), ("test20.txt", True)],
                size1=10 * 1024, size2=10 * 1024,
                backup_type='Incremental'
            )

            self.OPHelper.run_archive()

            self.OPHelper.verify_stub(path=self.origin_folder_path, test_data_list=self.OPHelper.test_file_list,
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall(org_hashcode=self.OPHelper.org_hashcode, path=self.origin_folder_path)

            self.log.info('Kill job in middle of backup phase passed')

        except Exception as exp:
            self.log.error('Kill job in middle of backup phase failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
