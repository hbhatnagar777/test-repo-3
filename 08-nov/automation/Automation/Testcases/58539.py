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

    move()          --  To move files using restore out of place in network share based clients.


"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for move stub across SubClient and rename check"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "move stub across SubClient and rename check"
        self.show_to_user = True
        self.base_folder_path = None
        self.OPHelper = None
        self.sub_folder_path1 = None
        self.sub_folder_path2 = None
        self.org_hashcode1 = None
        self.org_hashcode2 = None
        self.org_hashcode3 = None
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

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True), ("test5.txt", True), ("test6.txt", True),
                                        ("test7.txt", True), ("test8.txt", True)]

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.sub_folder_path1 = self.OPHelper.client_machine.join_path(self.base_folder_path, "SubFolder1")
        self.sub_folder_path2 = self.OPHelper.client_machine.join_path(self.base_folder_path, "SubFolder2")

        self.OPHelper.prepare_turbo_testdata(
            self.sub_folder_path1,
            self.OPHelper.test_file_list[:4],
            size1=20 * 1024, size2=100 * 1024
        )
        self.OPHelper.prepare_turbo_testdata(
            self.sub_folder_path2,
            self.OPHelper.test_file_list[4:],
            size1=20 * 1024, size2=100 * 1024
        )
        self.org_hashcode1 = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.OPHelper.client_machine.join_path(
                self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))
        self.org_hashcode2 = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.OPHelper.client_machine.join_path(
                self.sub_folder_path1, self.OPHelper.test_file_list[1][0]))
        self.org_hashcode3 = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.OPHelper.client_machine.join_path(
                self.sub_folder_path1, self.OPHelper.test_file_list[2][0]))

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)

        self.OPHelper.create_subclient(name='sc1', delete=True, content=[self.sub_folder_path1])
        self.OPHelper.create_subclient(name='sc2', delete=True, content=[self.sub_folder_path2])

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
            'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%']}
        }
        self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc1')
        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True
        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc2')
        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True
        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

    def move(self, source, destination):
        """To move files using restore out of place in network share based clients."""

        uncsource = source[2:]
        uncsource = "\\UNC-NT_" + uncsource
        self.OPHelper.restore_out_of_place(destination_path=destination,
                                           paths=[uncsource],
                                           fs_options={'restoreDataInsteadOfStub': False},
                                           impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                           impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                           client=self.tcinputs.get("ProxyClient"),
                                           restore_ACL=False,
                                           restore_data_and_acl=False,
                                           no_of_streams=10)
        self.OPHelper.client_machine.delete_file(source)

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Create 2 subclients with 4 files and run archive jobs.
        2. Move 3 stubs of sc1 content to sc2 content.
        3. Rename one of moved stubs.
        4. Create new folder under sc2 content and move one of the sc1 stubs under new folder.
        5. Run couple of new archive jobs on sc1 and sc2 with some added content under sc1 and sc2.
        6. Recall all 3 moved stubs and verify.
        """

        try:

            if "linux" in self.client.os_info.lower():
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc1')
                self.OPHelper.run_archive(repeats=2)
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc2')
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc1')
                self.OPHelper.run_archive(repeats=3)
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc2')
                self.OPHelper.run_archive(repeats=3)

            if self.is_nas_turbo_type:
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc1')
                for i in range(1, 3):
                    self.move(
                        self.OPHelper.client_machine.join_path(self.sub_folder_path1,
                                                               self.OPHelper.test_file_list[i][0]),
                        self.sub_folder_path2)
            elif "windows" in self.client.os_info.lower():
                for i in range(3):
                    self.OPHelper.move_file_gxhsm(
                        self.OPHelper.client_machine.join_path(self.sub_folder_path1,
                                                               self.OPHelper.test_file_list[i][0]),
                        self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                               self.OPHelper.test_file_list[i][0]))
            else:
                for i in range(3):
                    self.OPHelper.client_machine.move_file(
                        self.OPHelper.client_machine.join_path(self.sub_folder_path1,
                                                               self.OPHelper.test_file_list[i][0]),
                        self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                               self.OPHelper.test_file_list[i][0]))

            # Create a sub directory within one of the SubFolder2.
            self.log.info("Creating a sub directory in Sub Folder2")
            if self.OPHelper.client_machine.create_directory(
                    directory_name=self.OPHelper.client_machine.join_path(self.sub_folder_path2, "SubFolder")):
                sub_folder_path = self.OPHelper.client_machine.join_path(self.sub_folder_path2, "SubFolder")
            else:
                raise Exception("Failed to create directory/SubFolder .")

            # Move the first file(stubbed) from SubFolder2 to sub directory.
            if self.is_nas_turbo_type:
                self.move(self.OPHelper.client_machine.join_path(self.sub_folder_path1,
                                                                 self.OPHelper.test_file_list[0][0]), sub_folder_path)
            elif "windows" in self.client.os_info.lower():
                self.OPHelper.move_file_gxhsm(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                           self.OPHelper.test_file_list[0][0]),
                    self.OPHelper.client_machine.join_path(sub_folder_path, self.OPHelper.test_file_list[0][0]))
            else:
                self.OPHelper.client_machine.move_file(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                           self.OPHelper.test_file_list[0][0]),
                    self.OPHelper.client_machine.join_path(sub_folder_path, self.OPHelper.test_file_list[0][0]))

            # Rename the second file.
            if self.is_nas_turbo_type:
                self.OPHelper.client_machine.rename_file_or_folder(
                    old_name=self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                                    self.OPHelper.test_file_list[1][0]),
                    new_name=self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                                    "renamed.txt"))
            elif "windows" in self.client.os_info.lower():
                self.OPHelper.move_file_gxhsm(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                           self.OPHelper.test_file_list[1][0]),
                    self.OPHelper.client_machine.join_path(self.sub_folder_path2, "renamed.txt"))
            else:
                self.OPHelper.client_machine.move_file(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path2,
                                                           self.OPHelper.test_file_list[1][0]),
                    self.OPHelper.client_machine.join_path(self.sub_folder_path2, "renamed.txt"))

            self.OPHelper.prepare_turbo_testdata(
                content_path=self.sub_folder_path1,
                test_file_list=[('test9.txt', True)],
                size1=20 * 1024, size2=20 * 1024,
                backup_type='Incremental'
            )
            self.OPHelper.prepare_turbo_testdata(
                content_path=self.sub_folder_path2,
                test_file_list=[('test10.txt', True)],
                size1=20 * 1024, size2=20 * 1024,
                backup_type='Incremental'
            )

            if "linux" not in self.client.os_info.lower():
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc1')
                self.OPHelper.run_archive(repeats=3)
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc2')
                self.OPHelper.run_archive(repeats=3)
            else:
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc1')
                self.OPHelper.run_archive(repeats=2)
                self.OPHelper.testcase.subclient = self.backupset.subclients.get('sc2')
                self.OPHelper.run_archive(repeats=2)

            # Run Archive and check if recall is working within the sub directory.
            self.OPHelper.recall(org_hashcode=self.org_hashcode1,
                                 path=self.OPHelper.client_machine.join_path(
                                     sub_folder_path, self.OPHelper.test_file_list[0][0]))

            self.OPHelper.recall(org_hashcode=self.org_hashcode2,
                                 path=self.OPHelper.client_machine.join_path(self.sub_folder_path2, "renamed.txt"))

            self.OPHelper.recall(org_hashcode=self.org_hashcode3,
                                 path=self.OPHelper.client_machine.join_path(
                                    self.sub_folder_path2, self.OPHelper.test_file_list[2][0]))

            self.log.info('Move and Rename stub across SC test passed.')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Move and Rename stub across SC with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
