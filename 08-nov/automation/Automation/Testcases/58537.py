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

    change_timestamps()     --  Changes last Access Time of the files.

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from datetime import datetime
import time


class TestCase(CVTestCase):
    """Class for Access time rule based archiving verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Access time rule verification"
        self.show_to_user = True
        self.base_folder_path = None
        self.OPHelper = None
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

        if "windows" in self.client.os_info.lower():
            update_properties = self.OPHelper.testcase.agent.properties
            self.log.info(update_properties)
            update_properties['AgentProperties']['isAccessTimeCollected'] = True
            update_properties['AgentProperties']['disableHonorArchiverRetention'] = True
            update_properties['AgentProperties']['honorArchiverRetention'] = True
            self.log.info(update_properties)

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", False), ("test3.txt", True),
                                        ("test4.txt", False)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
                            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.OPHelper.org_hashcode = self.OPHelper.prepare_turbo_testdata(
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

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": True,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 30,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True,
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def change_timestamps(self):
        """ Changes the Access time of files. """
        for i in range(4):
            self.OPHelper.client_machine.modify_item_datetime(path=self.OPHelper.client_machine.join_path(
                self.base_folder_path, self.OPHelper.test_file_list[i][0]),
                access_time=datetime(year=2019, month=1, day=1))
            time.sleep(15)

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Set the "fileAccessTimeOlderThan" rule to 30 days. 
        2. Set "useNativeSnapshotToPreserveFileAccessTime" and "isAccessTimeCollected".
        2. create test data and change their access time greater than 30 days. 
        3. Run archive, Files qualify for archiving.
        4. Create another set of test files and run archive. 
        5. These files should not qualify for archiving.
        """

        try:
            self.log.info("Changing access time of all files to older than 30 days")
            self.change_timestamps()

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                                      ("test4.txt", True)], is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info("All the files got qualified for archiving based on access time property")

            self.OPHelper.prepare_turbo_testdata(
                self.base_folder_path, [("test5.txt", True), ("test6.txt", False)],
                size1=20 * 1024,
                size2=20 * 1024, backup_type="INCREMENTAL")

            self.change_timestamps()

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                                      ("test4.txt", True), ("test5.txt", False), ("test6.txt", False)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info("Only first 4 files with access time older than 30 days get archived")

            self.log.info('The access time rule is honored correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The access time rule is not honored correctly  with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
