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
import time


class TestCase(CVTestCase):
    """Class for basic Acceptance Test for File Archiving System"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for File Archiving System"
        self.show_to_user = True
        self.base_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path1 = None
        self.data_folder_path2 = None
        self.stub_folder_path = None
        self.UNC_base_folder_path = None
        self.UNC_origin_folder_path = None
        self.is_nas_turbo_type = False
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

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
                            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path
            self.UNC_origin_folder_path = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin')

        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.data_folder_path1 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data1')
        self.data_folder_path2 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data2')
        self.stub_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'stub')

        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            self.OPHelper.test_file_list,
            size1=10 * 1024, size2=10 * 1024
        )

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.origin_folder_path])

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
        1. Backup test data.
        2. Out of place Restore Data and verification.
        3. Stub the test data, backup stubs and verify stubs.
        4. Out of place Restore data instead of stub and verification.
        5. Recall stub from original data.
        6. Out of place Restore stub and verification. 
        7. Recall out of place restored stub. 
        """

        try:
            self.OPHelper.run_archive(repeats=1)

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

            self.OPHelper.verify_restore_result(source_path=self.origin_folder_path,
                                                dest_path=self.data_folder_path1)

            self.OPHelper.run_archive(repeats=2)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.origin_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path2,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.UNC_origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': True},
                                                   impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                                   impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                                   client=self.tcinputs.get("ProxyClient"),
                                                   restore_ACL=False,
                                                   restore_data_and_acl=False,
                                                   no_of_streams=10)
            else:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path2,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': True},
                                                   no_of_streams=10)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.data_folder_path2, is_nas_turbo_type=self.is_nas_turbo_type,
                                      test_data_list=[("test1.txt", False), ("test2.txt", False), ("test3.txt", False),
                                                      ("test4.txt", False)])
            self.OPHelper.verify_restore_result(source_path=self.data_folder_path1,
                                                dest_path=self.data_folder_path2)

            self.OPHelper.recall(path=self.origin_folder_path)

            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.stub_folder_path,
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
                self.OPHelper.restore_out_of_place(destination_path=self.stub_folder_path,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': False},
                                                   no_of_streams=10)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.stub_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)
            self.OPHelper.verify_restore_result(source_path=self.data_folder_path1,
                                                dest_path=self.stub_folder_path)

            self.OPHelper.recall(path=self.stub_folder_path)
            self.log.info('Basic Acceptance tests for File Archiving System passed')
            self.log.info('Test case executed successfully.')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Basic Acceptance tests failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
