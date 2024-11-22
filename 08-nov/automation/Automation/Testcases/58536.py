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
    """Class for Read-only Option verification in Windows"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "For Read-only option verification in Windows"
        self.show_to_user = True
        self.base_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path = None
        self.OPHelper = None
        self.is_nas_turbo_type = False
        self.UNC_origin_folder_path = None
        self.UNC_base_folder_path = None
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

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")
        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'attribute_files')
        self.data_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data')

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path
            self.UNC_origin_folder_path = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path,
                                                                                 'attribute_files')

        self.log.info("Start generating Read-only test data")
        if self.is_nas_turbo_type:
            self.OPHelper.client_machine.generate_test_data(file_path=self.base_folder_path, dirs=0,
                                                            attribute_files='R',
                                                            create_only=True,
                                                            file_size=12,
                                                            files=2,
                                                            username=self.tcinputs.get("ImpersonateUser"),
                                                            password=self.tcinputs.get("ImpersonatePassword"))
        else:
            self.OPHelper.client_machine.generate_test_data(file_path=self.base_folder_path, dirs=0,
                                                            attribute_files='R',
                                                            files=2,
                                                            create_only=True)

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=self.origin_folder_path)

        self.log.info("Test data generation completed.")

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

        self.log.info("Read-only option to false.")
        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": True,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "archiveReadOnlyFiles": False,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
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
        1. Generate Read-only test data.
        2. Set Read-only option in SC Properties for Windows to False [Read-only files will not be Archived].
        3. Run Archive jobs [1: Backup Data, 2: Stubbing, 3: Backup Stub].
        4. Verify none of the files get Archived.
        5. Set Read-only option in SC Properties for Windows to True [Read-only files will be Archived].
        6. Recall the files and validate.
        7. Run Archive jobs and perform restore out of place with validation.
        """

        try:

            self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.origin_folder_path, test_data_list=[('read_only_file1', False),
                                                                                    ('read_only_file2', False)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)
            self.log.info("Changing diskCleanup property to include Read-only files.")
            _disk_cleanup_rules = {
                "archiveReadOnlyFiles": True
            }

            self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

            self.OPHelper.run_archive(repeats=3)

            time.sleep(240)
            self.OPHelper.verify_stub(path=self.origin_folder_path, test_data_list=[('read_only_file1', True),
                                                                                    ('read_only_file2', True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall(path=self.origin_folder_path)

            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.UNC_origin_folder_path, file[0])
                                                       for file in [('read_only_file1', True),
                                                                    ('read_only_file2', True)]],
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
                                                       for file in [('read_only_file1', True),
                                                                    ('read_only_file2', True)]],
                                                   fs_options={'restoreDataInsteadOfStub': True},
                                                   no_of_streams=10)
            self.OPHelper.verify_restore_result(source_path=self.origin_folder_path,
                                                dest_path=self.data_folder_path)

            self.log.info('The read-only option is honored correctly')
            self.log.info('Test case executed successfully')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('The read-only option is not honored correctly with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
