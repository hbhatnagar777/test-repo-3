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

    add_registry_key()  --  Add registry keys to enable this feature

    remove_registry_key()   --  Remove registry keys to disable this feature

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils import constants
from AutomationUtils.database_helper import MSSQL
import time


class TestCase(CVTestCase):
    """Class for File System backup of same content as archive."""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For File System backup of same content as archive."
        self.show_to_user = True
        self.base_folder_path = None
        self.is_nas_turbo_type = False
        self.OPHelper = None
        self.FSHelper = None
        self.UNC_base_folder_path = None
        self.subclient_id = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def add_registry_key(self):
        """
            Add registry keys to enable this feature
        """
        if self.is_nas_turbo_type:
            sqldb = MSSQL(self.tcinputs.get("SQLServer"), self.tcinputs.get("SQLUserName"),
                          self.tcinputs.get("SQLPassword"), 'CommServ')
            self.subclient_id = sqldb.execute(
                "select id from CommServ.dbo.APP_Application where subclientName like 'testSC' and clientId = (select id from CommServ.dbo.APP_Client where name like '{0}')".format(
                    self.tcinputs.get("ClientName"))
            ).rows[0][0]
            self.OPHelper.client_machine.create_registry("FileSystemAgent", 'bEnableStubCheck_'+str(self.subclient_id), 1,
                                                         reg_type='DWord')

    def remove_registry_key(self):
        """
            Remove registry keys to disable this feature
        """
        if self.is_nas_turbo_type:
            self.OPHelper.client_machine.remove_registry("FileSystemAgent", 'bEnableStubCheck_'+str(self.subclient_id))

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.FSHelper = FSHelper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path

        self.OPHelper.prepare_turbo_testdata(
            self.base_folder_path,
            self.OPHelper.test_file_list,
            size1=100 * 1024,
            size2=100 * 1024)

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
        self.OPHelper.testcase.subclient.archiver_retention_days = -1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Create archive set with test content.
        2. Run archive job and verify stub. 
        3. Create backupset and subclient with same content. 
        4. Run backup and verify that stubs are not being recalled. 
        5. Match all files are being backedup.
        """

        try:

            if "linux" in self.client.os_info.lower():
                self.OPHelper.run_archive(repeats=2)
            else:
                self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.base_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            self.FSHelper.create_backupset("test", delete=True)
            self.FSHelper.create_subclient("testSC", self.tcinputs.get('StoragePolicyName'),
                                           content=[self.base_folder_path],
                                           data_access_nodes=self.tcinputs.get("DataAccessNodes"),
                                           delete=True)
            if self.is_nas_turbo_type:
                self.add_registry_key()
                update_properties = self.FSHelper.testcase.subclient.properties
                update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
                update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
                self.FSHelper.testcase.subclient.update_properties(update_properties)

            self.log.info("Running normal backup job")
            backup_job = self.FSHelper.run_backup()

            time.sleep(120)
            self.OPHelper.verify_stub(is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info("Stubs are not recalled during normal backup.")

            self.FSHelper.run_find_verify(machine_path=self.base_folder_path, job=backup_job[0])
            self.log.info("All the files get backed up during normal backup job.")
            self.remove_registry_key()

            self.log.info('File System backup of same content as archive rule is honored correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('File System backup of same content as archive rule is not honored correctly with error: %s',
                           exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
