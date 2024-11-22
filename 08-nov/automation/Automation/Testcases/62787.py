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

    add_registry_key()  --  Add registry keys to enable this feature

    remove_registry_key()   --  Remove registry keys to disable this feature

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import ScanType
import time


class TestCase(CVTestCase):
    """Class for file delete and re-add check with re-stubbing"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For file delete and re-add with re-stubbing check"
        self.show_to_user = True
        self.base_folder_path = None
        self.UNC_base_folder_path = None
        self.is_nas_turbo_type = False
        self.OPHelper = None
        self.before_mtime = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.fsa = "FileSystemAgent"

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
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
            size1=20 * 1024,
            size2=20 * 1024)

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.base_folder_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        if "linux" in self.client.os_info.lower():
            self.OPHelper.create_subclient(delete=True, content=[self.base_folder_path], scan_type=ScanType.RECURSIVE)
        else:
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

    def add_registry_key(self):
        """
            Add registry keys to enable this feature
        """
        if "linux" in self.client.os_info.lower():
            self.OPHelper.client_machine.create_registry(self.fsa, 'nEnabledRestubbing', 1)
            return

        if self.tcinputs.get("StubClient"):
            stub_client = Machine(machine_name=self.tcinputs.get("StubClient"), commcell_object=self.commcell)
            stub_client.create_registry("FileSystemAgent", "nEnabledRestubbing", 1, reg_type='DWord')
        else:
            self.OPHelper.client_machine.create_registry("FileSystemAgent", "nEnabledRestubbing", 1, reg_type='DWord')
        time.sleep(30)

    def remove_registry_key(self):
        """
            Remove registry keys to disable this feature
        """
        if "linux" in self.client.os_info.lower():
            self.OPHelper.client_machine.remove_registry(self.fsa, 'nEnabledRestubbing')
            return

        if self.tcinputs.get("StubClient"):
            stub_client = Machine(machine_name=self.tcinputs.get("StubClient"), commcell_object=self.commcell)
            stub_client.remove_registry("FileSystemAgent", "nEnabledRestubbing")
        else:
            self.OPHelper.client_machine.remove_registry("FileSystemAgent", "nEnabledRestubbing")
        time.sleep(30)

    def run(self):
        """Run function of this test case"""

        _desc = """. 
        1. create test data 
        2. Run 2 archive jobs, verify Files are stubbed
        3. Delete one of the test file , take another backup
        4. Delete one more file and take another backup
        5. Restore back the deleted files as data, run archive jobs
        6. Verify readded files are rebackedup and stubbed in next job
        """

        try:
            self.add_registry_key()

            jobs = self.OPHelper.run_archive(repeats=2)

            start_time = jobs[0].start_time
            end_time = jobs[0].end_time

            time.sleep(30)

            self.OPHelper.verify_stub(path=self.base_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.client_machine.delete_file(
                self.OPHelper.client_machine.join_path(self.base_folder_path, "test4.txt"))

            self.OPHelper.run_archive(repeats=1)

            self.OPHelper.client_machine.delete_file(
                self.OPHelper.client_machine.join_path(self.base_folder_path, "test3.txt"))

            self.OPHelper.run_archive(repeats=1)

            if self.is_nas_turbo_type:
                restore_files = [self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, "test4.txt"),
                                 self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, "test3.txt")]
                self.OPHelper.restore_in_place(paths=restore_files, from_time=start_time, to_time=end_time,
                                               impersonate_user=self.tcinputs.get("ImpersonateUser"),
                                               impersonate_password=self.tcinputs.get("ImpersonatePassword"),
                                               proxy_client=self.tcinputs.get("ProxyClient"))
            else:
                restore_files = [self.OPHelper.client_machine.join_path(self.base_folder_path, "test4.txt"),
                                 self.OPHelper.client_machine.join_path(self.base_folder_path, "test3.txt")]
                self.OPHelper.restore_in_place(paths=restore_files, from_time=start_time, to_time=end_time)

            time.sleep(100)
            jobs = self.OPHelper.run_archive(repeats=3)

            self.OPHelper.restub_checks(jobs, 2, flag=False)

            self.OPHelper.verify_stub(path=self.base_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            self.remove_registry_key()
            self.log.info('The deleted and re-added files are backed up again')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The restub feature didnt work as expected for deleted-readded files : %s', exp)
            self.result_string = str(exp)
            self.remove_registry_key()
            self.log.info('Test case failed')
            self.status = constants.FAILED
