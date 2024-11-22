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

    change_timestamps()     --  Changes the Access time and Last Modified time of files.

    verify_access_time()     --  Verify that Last Access time of files is not changed.

    verify_modified_time()     --  Verify that Last Modified time of files is not changed.

    validate_automount_unmounted()       --  To Validate auto mount path is unmounted.

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from datetime import datetime
from FileSystem.FSUtils.fshelper import ScanType
import time


class TestCase(CVTestCase):
    """Class for NFS AutoMount Basic Acceptance verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For NFS AutoMount Basic Acceptance verification"
        self.show_to_user = True
        self.base_folder_path = None
        self.UNC_origin_folder_path = None
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
                                        ("test4.txt", True)]

        self.mount_path = self.tcinputs.get("MountPath", "/mnt")
        self.base_folder_path = self.OPHelper.access_path + '{0}{1}'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id))
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.data_folder_path1 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data1')
        self.origin_mount_path = self.OPHelper.client_machine.join_path(self.mount_path, 'origin')
        self.data_mount_path1 = self.OPHelper.client_machine.join_path(self.mount_path, 'data1')
        self.UNC_origin_folder_path = '/' + self.origin_folder_path
        self.UNC_origin_folder_path = self.UNC_origin_folder_path.replace(':', '')
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
            self.OPHelper.client_machine.join_path(self.mount_path, str(self.OPHelper.testcase.id), 'origin'),
            self.OPHelper.test_file_list,
            size1=1024 * 1024,
            size2=1024 * 1024)
        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.OPHelper.client_machine.join_path(self.mount_path, str(self.OPHelper.testcase.id), 'origin'))
        self.log.info("Test data populated successfully.")
        self.log.info("Changing timestamps of all files to older than 90 days")
        self.change_timestamps(
            path=self.OPHelper.client_machine.join_path(self.mount_path, str(self.OPHelper.testcase.id), 'origin'))

        self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, force_unmount=True)

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=True)
        self.OPHelper.create_subclient(name=self.base_folder_path, delete=True, content=[self.base_folder_path],
                                       scan_type=ScanType.RECURSIVE)

        update_properties = self.OPHelper.testcase.subclient.properties
        update_properties['fsSubClientProp']['checkArchiveBit'] = True
        self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "fileModifiedTimeOlderThan": 91,
            "fileAccessTimeOlderThan": 89,
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

    def change_timestamps(self, path):
        """Changes the last timestamps of files in unix and windows."""

        for i in range(4):
            self.OPHelper.client_machine.modify_item_datetime(path=self.OPHelper.client_machine.join_path(
                path, self.OPHelper.test_file_list[i][0]),
                creation_time=datetime(year=2019, month=1, day=1),
                access_time=datetime(year=2019, month=3, day=3),
                modified_time=datetime(year=2019, month=2, day=2))

        self.before_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()

        self.log.info(self.client.os_info)
        self.log.info(self.before_mtime)

        self.before_atime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastAccessTimeUtc'").strip()

        self.log.info(self.before_atime)

    def verify_modified_time(self, path):
        """ Verify that Last Modified time of files is not changed. """

        changed_mtime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastWriteTimeUtc'").strip()

        self.log.info("After mtime: %s", str(changed_mtime))
        self.log.info("Before mtime: %s", str(self.before_mtime))
        if str(self.before_mtime) != str(changed_mtime):
            raise Exception("The mtime of the files have been changed.")
        else:
            self.log.info("The mtime of the files have not been changed.")

    def verify_access_time(self, path):
        """ Verify that Last Access time of files is not changed. """

        changed_atime = self.OPHelper.client_machine.get_test_data_info(
            data_path=self.OPHelper.client_machine.join_path(path, self.OPHelper.test_file_list[0][0]),
            custom_meta_list="'LastAccessTimeUtc'").strip()

        self.log.info("After: atime: %s", str(changed_atime))
        self.log.info("Before atime: %s", str(self.before_atime))
        if str(self.before_atime) != str(changed_atime):
            raise Exception("The atime of the files have been changed.")
        else:
            self.log.info("The atime of the files have not been changed.")

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
        2. Create Archiveset and Subclient and run archive job.
        3. Validate that automount created during the archive job was unmounted.
        4. Verify atime, mtime is not changed.
        5. Verify the files are stubbed correctly.
        6. Run couple of more archive jobs to backup stubs.
        7. Restore out of place as stubs.
        8. Verify files are restored as stubs.
        9. Recall the files and compare checksums.
        10. Verify that modified time of files are not changed.
        """

        try:

            self.log.info(_desc)

            job = self.OPHelper.run_archive(repeats=1)[0]
            self.validate_automount_unmounted(job.job_id)

            self.OPHelper.client_machine.mount_nfs_share(nfs_client_mount_dir=self.mount_path,
                                                         server=self.nfs_server,
                                                         share=self.OPHelper.client_machine.join_path(self.nfs_share,
                                                                                                      str(self.OPHelper.testcase.id)))
            time.sleep(120)
            if self.tcinputs.get("SkipVerifyAtime", "false") == "false":
                self.verify_access_time(path=self.origin_mount_path)
            self.verify_modified_time(path=self.origin_mount_path)
            time.sleep(120)
            self.OPHelper.verify_stub(path=self.origin_mount_path)

            self.OPHelper.recall(path=self.origin_mount_path)
            self.verify_modified_time(path=self.origin_mount_path)

            # Verifying stubs changes the access time
            self.change_timestamps(self.origin_mount_path)

            self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, force_unmount=True)

            self.log.info("Re-stub and backup stubs")
            self.OPHelper.run_archive(repeats=2)

            self.OPHelper.client_machine.mount_nfs_share(nfs_client_mount_dir=self.mount_path,
                                                         server=self.nfs_server,
                                                         share=self.OPHelper.client_machine.join_path(self.nfs_share,
                                                                                                      str(
                                                                                                          self.OPHelper.testcase.id)))
            self.OPHelper.restore_out_of_place(client=self.tcinputs.get("ProxyClient"),
                                               destination_path=self.data_mount_path1,
                                               paths=[self.OPHelper.client_machine.join_path(
                                                   self.UNC_origin_folder_path, file[0])
                                                   for file in self.OPHelper.test_file_list],
                                               fs_options={'restoreDataInsteadOfStub': False},
                                               proxy_client=self.tcinputs.get("ProxyClient"),
                                               restore_ACL=False,
                                               restore_data_and_acl=False,
                                               no_of_streams=10)

            time.sleep(120)
            self.OPHelper.verify_stub(path=self.data_mount_path1)

            self.OPHelper.recall(path=self.data_mount_path1)
            self.verify_modified_time(path=self.data_mount_path1)

            self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, force_unmount=True)

            self.log.info('NFS AutoMount Basic Acceptance is running correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            try:
                self.OPHelper.client_machine.unmount_path(mount_path=self.mount_path, force_unmount=True)
            except Exception:
                self.log.info(Exception)
            self.log.error('NFS AutoMount Basic Acceptance is not running correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
