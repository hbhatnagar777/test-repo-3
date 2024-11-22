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

    setup_subclient()       --  Setup to create test data and setup sub-client properties.

    validate_automount_unmounted()       --  To Validate auto mount path is unmounted.

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from datetime import datetime
from FileSystem.FSUtils.fshelper import ScanType
import time


class TestCase(CVTestCase):
    """Class for NFS AutoMount: Kill during Scan/Backup phase verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For NFS AutoMount: Kill during Scan/Backup phase"
        self.show_to_user = True
        self.base_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path1 = None
        self.mount_path = None
        self.mount_folder_path = None
        self.origin_mount_path = None
        self.data_mount_path1 = None
        self.nfs_server = None
        self.nfs_share = None
        self.OPHelper = None
        self.before_mtime = None
        self.before_atime = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully")

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
                                        ("test7.txt", True), ("test8.txt", True), ("test9.txt", True),
                                        ("test10.txt", True), ("test11.txt", True), ("test12.txt", True),
                                        ("test13.txt", True), ("test14.txt", True), ("test15.txt", True),
                                        ("test16.txt", True), ("test17.txt", True), ("test18.txt", True)]

        self.mount_path = self.tcinputs.get("MountPath", "/mnt")
        self.base_folder_path = self.OPHelper.access_path + '{0}{1}'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.mount_folder_path = self.mount_path + '{0}{1}'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.data_folder_path1 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data1')
        self.origin_mount_path = self.OPHelper.client_machine.join_path(self.mount_folder_path, 'origin')
        self.data_mount_path1 = self.OPHelper.client_machine.join_path(self.mount_folder_path, 'data1')
        self.nfs_server = self.OPHelper.access_path[:self.OPHelper.access_path.find(':')]
        self.nfs_share = self.OPHelper.access_path[self.OPHelper.access_path.find(':') + 1:]

        try:
            self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, force_unmount=True)
        except Exception:
            self.log.info(Exception)
        self.OPHelper.client_machine.mount_nfs_share(nfs_client_mount_dir=self.mount_path,
                                                     server=self.nfs_server,
                                                     share=self.nfs_share)
        self.OPHelper.prepare_turbo_testdata(
            self.origin_mount_path,
            self.OPHelper.test_file_list,
            size1=1024 * 1024,
            size2=1024 * 1024)
        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=self.origin_mount_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, force_unmount=True)
        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=True)
        self.OPHelper.create_subclient(name=self.origin_folder_path, delete=True, content=[self.origin_folder_path],
                                       scan_type=ScanType.RECURSIVE)

        update_properties = self.OPHelper.testcase.subclient.properties
        update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
        update_properties['fsSubClientProp']['checkArchiveBit'] = True
        self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "fileModifiedTimeOlderThan": 0,
            "fileAccessTimeOlderThan": 0,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
        }
        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def validate_automount_unmounted(self, job_id):
        """ To Validate auto mount path is unmounted"""
        log = self.OPHelper.client_machine.get_logs_for_job_from_file(job_id=job_id, log_file_name="FileScan.log",
                                                                      search_term="FileShareAutoMount::mount")
        log = log.strip()
        auto_mount_path = log[log.find(self.OPHelper.client_machine.client_object.install_directory):log.find(",")]
        self.log.info(log)
        if self.OPHelper.client_machine.is_path_mounted(mount_path=auto_mount_path):
            raise Exception("AutoMount path is still mounted")
        else:
            self.log.info("AutoMount path was unmounted after the job.")

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Create test files with atime and mtime greater than 90 days.
        2. Create Archiveset and Subclient and run first archive job.
        3. Kill the archive job during scan phase.
        4. Verify that automount is unmounted.
        5. Run second archive job.
        6. Kill the job during Backup Phase.
        7. Verify that automount is unmounted.
        """

        try:

            self.log.info(_desc)

            if self.tcinputs.get("SkipScanKill", "false") == "false":
                job = self.OPHelper.run_archive(repeats=1, do_not_wait=True)[0]

                while job.phase.lower() != 'scan':
                    time.sleep(3)

                while job.status.lower() != 'running':
                    time.sleep(3)

                time.sleep(self.tcinputs.get("TimeToKillScan", 4))
                job.kill(wait_for_job_to_kill=True)

                self.log.info("First job killed at scan phase")
                self.validate_automount_unmounted(job.job_id)
            else:
                self.log.info("Skipping Kill at FileScan phase. As SkipScanKill is set to True in tc inputs")

            job = self.OPHelper.run_archive(repeats=1, do_not_wait=True)[0]

            while job.phase.lower() != 'backup':
                time.sleep(3)

            while job.status.lower() != 'running':
                time.sleep(3)

            files_transferred = job.num_of_files_transferred
            self.log.info("Number of files transferred out of 18 are %s", files_transferred)
            while files_transferred < 1:
                time.sleep(3)
                files_transferred = job.num_of_files_transferred
                self.log.info("Number of files transferred out of 18 are %s", files_transferred)

            time.sleep(self.tcinputs.get("TimeToKillBackup", 0))
            self.log.info("Killing the backup job")
            job.kill(wait_for_job_to_kill=True)

            time.sleep(60)
            self.validate_automount_unmounted(job.job_id)

            self.log.info('NFS AutoMount: Kill during Scan/Backup phase is running correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            try:
                self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, delete_folder=True,
                                                          force_unmount=True)
            except Exception:
                self.log.info(Exception)
            self.log.error('NFS AutoMount: Kill during Scan/Backup phase is not running correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
