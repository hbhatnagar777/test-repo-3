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

    archived_files_got_deleted()    --  Verifies that Archived files are deleted or not.

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from datetime import datetime
import time


class TestCase(CVTestCase):
    """Class for File archiving based on Delete the file option set."""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For File archiving based on Delete the file option set."
        self.show_to_user = True
        self.base_folder_path = None
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

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", False), ("test3.txt", True),
                                        ("test4.txt", False)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.log.info("The modified time of each file is less than 1 day.")
        self.OPHelper.prepare_turbo_testdata(
            self.base_folder_path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=20 * 1024)

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.base_folder_path)
        self.log.info("Test data populated successfully.")

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

        self.log.info("The Delete the file option set is set to true. "
                      "The files which are archived are deleted.")
        self.log.info("The file modified time property is set to 30 days.")
        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 30,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 2,
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
        self.OPHelper.testcase.subclient.archiver_retention_days = -1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def change_timestamps(self):
        """ Changes the last Access time and Modified time of files in unix and windows.
                    Also changes the creation time in windows.
                """

        for i in range(4):
            self.OPHelper.client_machine.modify_item_datetime(path=self.OPHelper.client_machine.join_path(
                self.base_folder_path, self.OPHelper.test_file_list[i][0]),
                creation_time=datetime(year=2019, month=1, day=1),
                access_time=datetime(year=2019, month=1, day=1),
                modified_time=datetime(year=2019, month=1, day=1))

    def archived_files_got_deleted(self):
        """ Verifies that Archived files are deleted or not. """

        if ((self.OPHelper.client_machine.check_file_exists(self.OPHelper.client_machine.join_path(
                self.base_folder_path, self.OPHelper.test_file_list[0][0])) is False) and
                (self.OPHelper.client_machine.check_file_exists(self.OPHelper.client_machine.join_path(
                    self.base_folder_path, self.OPHelper.test_file_list[1][0])) is False) and
                (self.OPHelper.client_machine.check_file_exists(self.OPHelper.client_machine.join_path(
                    self.base_folder_path, self.OPHelper.test_file_list[2][0])) is False) and
                (self.OPHelper.client_machine.check_file_exists(self.OPHelper.client_machine.join_path(
                    self.base_folder_path, self.OPHelper.test_file_list[3][0])) is False)):
            return True
        else:
            return False

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Set the "fileModifiedTimeOlderThan" rule to 30 days. 
        2. Set the "afterArchivingRule" to (Delete) 
        3. Change timestamps of the few files to older date.
        4. Run archive jobs and validate the archived files are deleted. 
        5. Browse with show_deleted set to true
        6. Validate deleted files are backedup.
        """

        try:
            self.log.info("Changing modified time of all files prior to 30 days")
            self.change_timestamps()

            self.OPHelper.prepare_turbo_testdata(
                self.base_folder_path, [("test5.txt", True), ("test6.txt", False)],
                size1=20 * 1024, size2=20 * 1024, backup_type="INCREMENTAL")
            self.log.info("Creating 2 more files with last modified date less than 30 days.")

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            if self.archived_files_got_deleted():
                self.log.info("Delete the file option property is satisfied.")
            else:
                raise Exception("Delete the file option property is not satisfied.")

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            backedup_list, __ = self.subclient.find(file_name='*.txt', show_deleted=True)
            self.log.info("Deleted backedup items in dir: " + str(len(backedup_list)))
            if len(backedup_list) is 4:
                self.log.info("The deleted files are backedup successfully.")
            else:
                raise Exception("The files are not backedup correctly.")

            self.log.info('The delete after archiving rule is honored correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The delete after archiving rule is not honored correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
