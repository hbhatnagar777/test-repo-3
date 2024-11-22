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

    swap_files()     --  Swap files with same name in different folders

    move()          --  Move file using restores for network share clients

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
import time


class TestCase(CVTestCase):
    """Class for OnePass move stub scenarios check"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "OnePass move stub scenarios check"
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
        self.log.info("Test inputs populated successfully.")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", False),
                                        ("test4.txt", False)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.sub_folder_path1 = self.OPHelper.client_machine.join_path(self.base_folder_path, "SubFolder1")
        self.sub_folder_path2 = self.OPHelper.client_machine.join_path(self.base_folder_path, "SubFolder2")

        self.OPHelper.prepare_turbo_testdata(
            self.sub_folder_path1,
            self.OPHelper.test_file_list,
            size1=100 * 1024, size2=8 * 1024
        )

        self.OPHelper.prepare_turbo_testdata(
            self.sub_folder_path2,
            self.OPHelper.test_file_list,
            size1=100 * 1024, size2=8 * 1024
        )

        self.OPHelper.org_hashcode = None
        self.org_hashcode1 = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.OPHelper.client_machine.join_path(
                self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))
        self.org_hashcode2 = self.OPHelper.client_machine.get_checksum_list(
            data_path=self.OPHelper.client_machine.join_path(
                self.sub_folder_path2, self.OPHelper.test_file_list[0][0]))

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
            "enableArchivingWithRules": True,
            'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%']}
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def move(self, source, destination):
        """ Move file using restores for network share clients"""
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

    def swap_files(self):
        """ Swap files with same name in different folders. """
        if self.is_nas_turbo_type:
            self.OPHelper.client_machine.delete_file(
                self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))
            source = self.OPHelper.client_machine.join_path(self.sub_folder_path2, self.OPHelper.test_file_list[0][0])
            uncsource = source[2:]
            uncsource = "\\UNC-NT_" + uncsource
            self.OPHelper.restore_out_of_place(destination_path=self.sub_folder_path1,
                                               paths=[uncsource],
                                               fs_options={'restoreDataInsteadOfStub': False},
                                               impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                               impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                               client=self.tcinputs.get("ProxyClient"),
                                               restore_ACL=False,
                                               restore_data_and_acl=False,
                                               no_of_streams=10)
            self.OPHelper.client_machine.delete_file(
                self.OPHelper.client_machine.join_path(self.sub_folder_path2, self.OPHelper.test_file_list[0][0]))
            source = self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0])
            uncsource = source[2:]
            uncsource = "\\UNC-NT_" + uncsource
            self.OPHelper.restore_out_of_place(destination_path=self.sub_folder_path2,
                                               paths=[uncsource],
                                               fs_options={'restoreDataInsteadOfStub': False},
                                               impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                               impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                               client=self.tcinputs.get("ProxyClient"),
                                               restore_ACL=False,
                                               restore_data_and_acl=False,
                                               no_of_streams=10)

        elif "linux" in self.client.os_info.lower():
            self.OPHelper.client_machine.move_file(
                self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]),
                self.OPHelper.client_machine.join_path(self.base_folder_path, self.OPHelper.test_file_list[0][0]))
            self.OPHelper.client_machine.move_file(
                self.OPHelper.client_machine.join_path(self.sub_folder_path2, self.OPHelper.test_file_list[0][0]),
                self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))
            self.OPHelper.client_machine.move_file(
                self.OPHelper.client_machine.join_path(self.base_folder_path, self.OPHelper.test_file_list[0][0]),
                self.OPHelper.client_machine.join_path(self.sub_folder_path2, self.OPHelper.test_file_list[0][0]))
        else:
            self.OPHelper.move_file_gxhsm(
                self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]),
                self.OPHelper.client_machine.join_path(self.base_folder_path, self.OPHelper.test_file_list[0][0]))
            self.OPHelper.move_file_gxhsm(
                self.OPHelper.client_machine.join_path(self.sub_folder_path2, self.OPHelper.test_file_list[0][0]),
                self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))
            self.OPHelper.move_file_gxhsm(
                self.OPHelper.client_machine.join_path(self.base_folder_path, self.OPHelper.test_file_list[0][0]),
                self.OPHelper.client_machine.join_path(self.sub_folder_path2, self.OPHelper.test_file_list[0][0]))

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Create subfolder1 and subfolder2 with 4 test files each, create a subfolder3 inside subfolder1. 
        2. Run archive job and move stub of test1.txt from subfolder1 into subfolder3. 
        3. Check if the file test1.txt is being recalled while moving. 
        4. Check if recall of file test1.txt is working within the subfolder3.  
        5. Move back the stubbed file test1.txt to original folder subfolder1 and run archive.
        6. Move file test1.txt in subFolder1 to subFolder2 and vice-versa(loop). 
        7. Recall and verify moved file test1.txt from first folder subfolder1 to second folder subfolder2 has same 
            hashcode and vice-versa 
        """
        try:
            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)
            time.sleep(240)
            # Create a sub directory within one of the SubFolder1.
            self.log.info("Creating a sub directory: Sub Folder")
            if self.OPHelper.client_machine.create_directory(
                    directory_name=self.OPHelper.client_machine.join_path(self.sub_folder_path1, "SubFolder")):
                sub_folder_path = self.OPHelper.client_machine.join_path(self.sub_folder_path1, "SubFolder")
            else:
                raise Exception("Failed to create directory/SubFolder .")

            # Move the first file(stubbed) from SubFolder1 to sub directory.
            if self.is_nas_turbo_type:
                self.move(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]),
                    sub_folder_path)
            elif "linux" in self.client.os_info.lower():
                self.OPHelper.client_machine.move_file(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path1,
                                                           self.OPHelper.test_file_list[0][0]),
                    self.OPHelper.client_machine.join_path(sub_folder_path, self.OPHelper.test_file_list[0][0]))
            else:
                self.OPHelper.move_file_gxhsm(
                    self.OPHelper.client_machine.join_path(self.sub_folder_path1,
                                                           self.OPHelper.test_file_list[0][0]),
                    self.OPHelper.client_machine.join_path(sub_folder_path, self.OPHelper.test_file_list[0][0]))

            # Check if the file is being recalled while moving
            time.sleep(240)
            if self.OPHelper.client_machine.is_stub(
                    self.OPHelper.client_machine.join_path(sub_folder_path, self.OPHelper.test_file_list[0][0]),
                    is_nas_turbo_type=self.is_nas_turbo_type):
                self.log.info("The stub file is moved without being recalled.")
            else:
                raise Exception("The file is recalled and is not a stub.")

            # Check if recall is working within the sub directory.
            self.OPHelper.recall(org_hashcode=self.org_hashcode1,
                                 path=self.OPHelper.client_machine.join_path(sub_folder_path,
                                                                             self.OPHelper.test_file_list[0][0]))

            self.log.info("Move back the recalled file to original folder and run archive.")

            self.OPHelper.client_machine.move_file(
                    self.OPHelper.client_machine.join_path(sub_folder_path, self.OPHelper.test_file_list[0][0]),
                    self.OPHelper.client_machine.join_path(self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))

            self.log.info("Deleting Sub Folder %s", sub_folder_path)
            self.OPHelper.client_machine.remove_directory(sub_folder_path)

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            self.log.info("Move file1 in subFolder1 to subFolder2 and vice-versa")
            self.swap_files()

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            # Recall and verify swapped files have correct hashcode
            self.OPHelper.recall(org_hashcode=self.org_hashcode2,
                                 path=self.OPHelper.client_machine.join_path(
                                     self.sub_folder_path1, self.OPHelper.test_file_list[0][0]))
            self.log.info(
                "The first file in first folder has same hashcode as the first file in second folder before swapping.")
            self.OPHelper.recall(org_hashcode=self.org_hashcode1,
                                 path=self.OPHelper.client_machine.join_path(
                                     self.sub_folder_path2, self.OPHelper.test_file_list[0][0]))
            self.log.info(
                "The first file in second folder has same hashcode as the first file in first folder before swapping.")

            self.log.info('Move stub scenario check passed')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Move stub scenario check failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
