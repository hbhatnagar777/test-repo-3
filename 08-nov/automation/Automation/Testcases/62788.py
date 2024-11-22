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

    add_registry_key()  --  Add registry keys to enable this feature

    remove_registry_key()   --  Remove registry keys to disable this features
"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from datetime import datetime
from FileSystem.FSUtils.fshelper import ScanType
import time,os


class TestCase(CVTestCase):
    """Class for last Access time and last Modification time rule and read-only file check verification"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Re-stubbing: For last Access time and last Mod time rule and read-only file check verification"
        self.show_to_user = True
        self.base_folder_path = None
        self.UNC_base_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path1 = None
        self.data_folder_path2 = None
        self.origin_folder_path2 = None
        self.origin_folder_path3 = None
        self.UNC_origin_folder_path = None
        self.UNC_origin_folder_path2 = None
        self.UNC_origin_folder_path3 = None
        self.is_nas_turbo_type = False
        self.OPHelper = None
        self.before_mtime = None
        self.before_atime = None
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
            self.UNC_origin_folder_path3 = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin3')

        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.origin_folder_path2 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin2')
        self.origin_folder_path3 = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin3')

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

    def setup_subclient(self, path):
        """Setup to create test data and setup sub-client properties."""

        if 'origin3' in path:
            if self.is_nas_turbo_type:
                self.OPHelper.client_machine.remove_directory(path)
                self.OPHelper.client_machine.generate_test_data(file_path=path, dirs=0,
                                                                attribute_files='R',
                                                                create_only=True,
                                                                file_size=12,
                                                                files=2,
                                                                username=self.tcinputs.get("ImpersonateUser"),
                                                                password=self.tcinputs.get("ImpersonatePassword"))
            else:
                self.OPHelper.client_machine.remove_directory(path)
                self.OPHelper.client_machine.generate_test_data(file_path=path, dirs=0,
                                                                attribute_files='R',
                                                                file_size=12,
                                                                files=2,
                                                                create_only=True)
        else:
            self.OPHelper.prepare_turbo_testdata(
                path,
                self.OPHelper.test_file_list,
                size1=20 * 1024,
                size2=20 * 1024)

        self.log.info("Test data populated successfully.")

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=path)
        self.OPHelper.create_subclient(name=path, delete=True, content=[path], scan_type=ScanType.RECURSIVE)

        if ('origin2' in path) and ("linux" not in self.client.os_info.lower()):
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
            "useNativeSnapshotToPreserveFileAccessTime": True if 'origin2' in path else False,
            "fileModifiedTimeOlderThan": 0 if 'origin2' in path or 'origin3' in path else 30,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 30 if 'origin2' in path else 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True,
            "archiveReadOnlyFiles": True if 'origin3' in path else False
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
        1. Setup the subclient with mod time based rule
        2. Create testdata following above rule, run archive jobs to stub the data
        3. Recall the file, check the Mtime  and checksum of the file,  it should not be changed
        4. Run a single Archive job, it should restub the file
        5. Setup the subclient with access time based rule
        6. Create testdata following above rule, run archive jobs to stub the data
        7. Recall the file, check the Mtime  and checksum of the file,  it should not be changed
        8. Run a single Archive job, it should not restub the file as access time of the file is changed.
        9. Create readonly files and set readonly property on subclient and stub the data
        10. Recall and run new archive job, it should restub the readonly file.
        """

        try:
            self.log.info(_desc)
            self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
            self.log.info("Modified time rule verification")

            self.setup_subclient(path=self.origin_folder_path)

            self.log.info("Set File type rule on the subclient")
            _disk_cleanup_rules = {
                'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%']}
            }

            self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

            self.log.info("Changing timestamps of all files to older than 30 days")
            self.change_timestamps(path=self.origin_folder_path)

            if self.is_nas_turbo_type:
                time.sleep(300)

            self.OPHelper.run_archive(repeats=2)

            time.sleep(30)
            self.OPHelper.recall(path=self.origin_folder_path)

            job = self.OPHelper.run_archive(repeats=1)

            self.OPHelper.restub_checks(job, len(self.OPHelper.test_file_list))
            self.OPHelper.verify_stub(path=self.origin_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)
            self.verify_modified_time(path=self.origin_folder_path)

            self.log.info("Access time rule verification")
            self.setup_subclient(path=self.origin_folder_path2)

            self.log.info("Changing timestamps of all files to older than 30 days")
            self.change_timestamps(path=self.origin_folder_path2)

            self.OPHelper.run_archive(repeats=2)

            time.sleep(30)

            self.OPHelper.recall(path=self.origin_folder_path2)

            job = self.OPHelper.run_archive(repeats=1)

            self.OPHelper.restub_checks(job, 0)

            self.log.info('Access time and Modified time is preserved and subsequent rules are honored correctly')

            self.log.info("Read only file rule verification")
            self.setup_subclient(path=self.origin_folder_path3)

            self.OPHelper.run_archive(repeats=2)

            time.sleep(30)

            self.OPHelper.recall(path=self.origin_folder_path3)

            job = self.OPHelper.run_archive(repeats=1)

            self.OPHelper.restub_checks(job, 2)

            stub_path = os.path.join(self.origin_folder_path3, "attribute_files")
            self.OPHelper.verify_stub(path=stub_path, test_data_list=[('read_only_file1', True),
                                                                      ('read_only_file2', True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The modified time rule is not honored correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
