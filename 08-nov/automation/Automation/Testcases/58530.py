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
    """Class for Maximum file size migration rule verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For Maximum file size migration rule verification"
        self.show_to_user = True
        self.base_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path = None
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
        self.log.info("Test inputs populated successfully")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", False),
                                        ("test4.txt", False)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path
            self.UNC_origin_folder_path = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin')

        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.data_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data')

        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=40 * 1024)

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

        self.log.info("The maximum file size is set to 30KB")
        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 30,
            "fileAccessTimeOlderThan": 0,
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

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Generate 2 files of 20KB and 40KB each. 
        2. Set "maximumFileSize" property to 30KB. 
        3. Run Archive and verify stub.
        4. Change "maximumFileSize" property to 50KB.
        5. Run Archive and verify stub.
        6. Recall the stubs and verify checksum. 
        7. Restore out of place and verify.
        """

        try:

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True), ("test3.txt", False),
                                     ("test4.txt", False)], is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info("First 2 files got qualified for archiving based on file size rule")

            self.log.info("Changing maximum file size property to 50KB")
            _disk_cleanup_rules = {
                "maximumFileSize": 50
            }
            self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                                      ("test4.txt", True)], is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info("All 4 files get archived")

            self.OPHelper.recall(path=self.origin_folder_path)

            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path,
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
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': True},
                                                   no_of_streams=10)

            self.OPHelper.verify_restore_result(source_path=self.origin_folder_path,
                                                dest_path=self.data_folder_path)

            self.log.info('The maximum file size rule is honored correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The maximum file size rule is not honored correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
