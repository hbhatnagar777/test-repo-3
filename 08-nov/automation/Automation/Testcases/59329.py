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

    verify_timestamps()     --  Verify that Last Modified time of files is not changed.

    setup_subclient()       --  Setup to create test data and setup sub-client properties.

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from datetime import datetime
from FileSystem.FSUtils.fshelper import ScanType
import time


class TestCase(CVTestCase):
    """Class for last Access time and last Modification time rule verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For last Access time and last Modification time rule verification"
        self.show_to_user = True
        self.base_folder_path = None
        self.UNC_base_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path1 = None
        self.data_folder_path2 = None
        self.origin_folder_path2 = None
        self.UNC_origin_folder_path = None
        self.UNC_origin_folder_path2 = None
        self.is_nas_turbo_type = False
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

        if "windows" in self.client.os_info.lower():
            update_properties = self.OPHelper.testcase.agent.properties
            self.log.info(update_properties)
            update_properties['AgentProperties']['isAccessTimeCollected'] = True
            update_properties['AgentProperties']['disableHonorArchiverRetention'] = True
            update_properties['AgentProperties']['honorArchiverRetention'] = True
            self.log.info(update_properties)

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path
            self.UNC_origin_folder_path = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin')
            self.UNC_origin_folder_path2 = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin2')

        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.origin_folder_path2 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin2')
        self.data_folder_path1 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data1')
        self.data_folder_path2 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data2')

    def setup_subclient(self, path):
        """Setup to create test data and setup sub-client properties."""

        self.OPHelper.prepare_turbo_testdata(
            path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=20 * 1024)
        self.log.info("Test data populated successfully.")

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=path)
        self.OPHelper.create_subclient(name=path, delete=True, content=[path], scan_type=ScanType.RECURSIVE)

        if (path is self.origin_folder_path2) and ("linux" not in self.client.os_info.lower()):
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": True if path is self.origin_folder_path2 else False,
            "fileModifiedTimeOlderThan": 30 if path is self.origin_folder_path else 0,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 30 if path is self.origin_folder_path2 else 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True,
            'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%']}
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

    def verify_modified_time(self, path=None):
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

    def run(self):
        """Run function of this test case"""

        _desc = """
        Mtime based archiving 
        1. Run a single Archive job.
        2. After the backup [not stubbing] mtime of the file should not change. 
        3. Run a second Archive job. After the stubbing verify mtime and atime of the file should not change.
        4. Recall the file, check the Mtime  and checksum of the file,  it should not be changed
        5. Restore the file and verify the mtime and  checksum.
        Access time rule, which will set the preserve access time. 
        6. Run a single Archive job.
        7. After the backup [not stubbing] mtime and atime of the file should not change. 
        8. Run a second Archive job. After the stubbing verify mtime and atime of the file should not change.
        9. Recall the file, check the mtime  and checksum of the file, it should not be changed. [As atime will change anyway as file is accessed]
        10. Restore the file and verify the mtime and checksum.
        """

        try:
            self.log.info(_desc)
            self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
            self.log.info("Modified time rule verification")
            self.setup_subclient(path=self.origin_folder_path)

            self.log.info("Changing timestamps of all files to older than 30 days")
            self.change_timestamps(path=self.origin_folder_path)

            self.OPHelper.run_archive(repeats=1)
            self.verify_modified_time(path=self.origin_folder_path)

            self.OPHelper.run_archive(repeats=1)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.origin_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)
            self.verify_modified_time(path=self.origin_folder_path)

            self.OPHelper.recall(path=self.origin_folder_path)
            self.verify_modified_time(path=self.origin_folder_path)

            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path1,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.UNC_origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': False},
                                                   impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                   impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                   client=self.tcinputs.get("ProxyClient"),
                                                   restore_ACL=False,
                                                   restore_data_and_acl=False,
                                                   no_of_streams=10)
            else:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path1,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': False},
                                                   no_of_streams=10)
            self.verify_modified_time(self.data_folder_path1)
            self.OPHelper.verify_restore_result(source_path=self.origin_folder_path,
                                                dest_path=self.data_folder_path1)

            self.log.info("Access time rule verification")
            self.setup_subclient(path=self.origin_folder_path2)

            self.log.info("Changing timestamps of all files to older than 30 days")
            self.change_timestamps(path=self.origin_folder_path2)

            self.OPHelper.run_archive(repeats=1)
            self.verify_modified_time(path=self.origin_folder_path2)
            self.verify_access_time(path=self.origin_folder_path2)

            self.OPHelper.run_archive(repeats=1)

            time.sleep(300)
            self.verify_modified_time(path=self.origin_folder_path2)
            self.verify_access_time(path=self.origin_folder_path2)
            self.OPHelper.verify_stub(path=self.origin_folder_path2, is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall(path=self.origin_folder_path2)
            self.verify_modified_time(path=self.origin_folder_path2)

            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path2,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.UNC_origin_folder_path2, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': False},
                                                   impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                   impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                   client=self.tcinputs.get("ProxyClient"),
                                                   restore_ACL=False,
                                                   restore_data_and_acl=False,
                                                   no_of_streams=10)
            else:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path2,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.origin_folder_path2, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': False},
                                                   no_of_streams=10)

            self.verify_modified_time(self.data_folder_path2)
            self.OPHelper.verify_restore_result(source_path=self.origin_folder_path2,
                                                dest_path=self.data_folder_path2)

            self.log.info('Access time and Modified time is preserved and subsequent rules are honored correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The modified time rule is not honored correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
