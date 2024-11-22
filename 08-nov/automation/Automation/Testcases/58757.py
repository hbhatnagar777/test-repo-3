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

    validate_multi_threading_from_logs()    --  Validates multi-threaded stubbing from GxHSMStub.log

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from AutomationUtils.machine import Machine
import time


class TestCase(CVTestCase):
    """Class for Basic Acceptance Test for Multi-Threaded Stubbing"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Multi-Threaded Stubbing"
        self.show_to_user = True
        self.base_folder_path = None
        self.UNC_base_folder_path = None
        self.UNC_origin_folder_path = None
        self.origin_folder_path = None
        self.data_folder_path = None
        self.is_nas_turbo_type = False
        self.OPHelper = None
        self.no_of_files = 100
        self.reg_key_val = 10
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def add_registry_key(self):
        """
            Add registry keys to enable this feature
        """
        if self.tcinputs.get("StubClient"):
            stub_client = Machine(machine_name=self.tcinputs.get("StubClient"), commcell_object=self.commcell)
            stub_client.create_registry("WinFSDataMigrator", "START_GXHSMSTUB_MULTITHREADED", 'Y',
                                                         reg_type='String')
            stub_client.create_registry("WinFSDataMigrator", "GXHSMSTUB_EARLYSTUBCOLLECTS_SPLITAT",
                                                         self.reg_key_val,
                                                         reg_type='DWord')
        else:
            self.OPHelper.client_machine.create_registry("WinFSDataMigrator", "START_GXHSMSTUB_MULTITHREADED", 'Y',
                                                         reg_type='String')
            self.OPHelper.client_machine.create_registry("WinFSDataMigrator", "GXHSMSTUB_EARLYSTUBCOLLECTS_SPLITAT",
                                                         self.reg_key_val,
                                                         reg_type='DWord')
        time.sleep(30)

    def remove_registry_key(self):
        """
            Remove registry keys to disable this feature
        """
        if self.tcinputs.get("StubClient"):
            stub_client = Machine(machine_name=self.tcinputs.get("StubClient"), commcell_object=self.commcell)
            stub_client.remove_registry("WinFSDataMigrator", "START_GXHSMSTUB_MULTITHREADED")
            stub_client.remove_registry("WinFSDataMigrator", "GXHSMSTUB_EARLYSTUBCOLLECTS_SPLITAT")
        else:
            self.OPHelper.client_machine.remove_registry("WinFSDataMigrator", "START_GXHSMSTUB_MULTITHREADED")
            self.OPHelper.client_machine.remove_registry("WinFSDataMigrator", "GXHSMSTUB_EARLYSTUBCOLLECTS_SPLITAT")
        time.sleep(30)

    def validate_multi_threading_from_logs(self, job_id):
        """
            Validates if stubbing was multi-threaded or not.
        """

        if self.tcinputs.get("StubClient"):
            stub_client = Machine(machine_name=self.tcinputs.get("StubClient"), commcell_object=self.commcell)
            log_line = stub_client.get_logs_for_job_from_file(job_id=job_id, log_file_name="GXHSMStub.log",
                                                              search_term="CGXHSMStub::SplitEarlyStubCollects")
        else:
            log_line = self.OPHelper.client_machine.get_logs_for_job_from_file(job_id=job_id,
                                                                               log_file_name="GXHSMStub.log",
                                                                               search_term="CGXHSMStub::SplitEarlyStubCollects")
        if log_line is None:
            return False

        no_of_threads = int(log_line[log_line.find('[')+1])

        self.log.info(log_line)
        self.log.info("No of threads: {}".format(no_of_threads))

        if no_of_threads == 1:
            self.log.info("Only one thread is used for stubbing")
            return False
        if no_of_threads > 1:
            self.log.info("Multi-threading validation from logs succeeded")
            return True
        return False

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.no_of_files = int(self.tcinputs.get("NoOfFiles", 100))
        self.reg_key_val = int(self.tcinputs.get("RegKeyVal", 10))
        self.log.info("Test inputs populated successfully.")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test{}.txt".format(i), True) for i in range(self.no_of_files)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
                            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path
            self.UNC_origin_folder_path = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin')

        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')
        self.data_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'data')

        if self.OPHelper.client_machine.check_directory_exists(self.origin_folder_path):
            self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)

        if len(self.OPHelper.org_hashcode) is not self.no_of_files:
            self.OPHelper.prepare_turbo_testdata(
                self.origin_folder_path,
                self.OPHelper.test_file_list,
                size1=2 * 1024, size2=2 * 1024)
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
            "fileSizeGreaterThan": 1,
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
        1. Create a folder named 'Origin', create 100 test files of size 2kb inside it, if already not present.
        2. Under 'WinFSDataMigrator', add 'START_GXHSMSTUB_MULTITHREADED' key with value 'Y' and 
           'GXHSMSTUB_EARLYSTUBCOLLECTS_SPLITAT' key with value 10
        3. Run three archive jobs.
        4. Verify that all the qualified files got stubbed.
        5. Validate from GxHSMStub.log that number threads > 1.
        6. Recall all the files from 'Origin' Folder and verify checksum.
        7. Confirm Stubs are backed up by running restore job with 'restoreDataInsteadOfStub' as False.
        8. Verify that the restored files are stubbed.
        9. Recall the restored files and verify checksum.  
        """

        try:
            self.add_registry_key()

            jobs = self.OPHelper.run_archive(repeats=3)

            time.sleep(120)
            self.OPHelper.verify_stub(path=self.origin_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            if self.validate_multi_threading_from_logs(
                    jobs[0].job_id) is False and self.validate_multi_threading_from_logs(
                    jobs[1].job_id) is False:
                raise Exception("Multi-threading validation from logs failed")

            self.OPHelper.recall(path=self.origin_folder_path)

            self.log.info("Confirm Stubs are backed up by running restore job with 'restoreDataInsteadOfStub' as False")
            if self.is_nas_turbo_type:
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path,
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
                self.OPHelper.restore_out_of_place(destination_path=self.data_folder_path,
                                                   paths=[self.OPHelper.client_machine.join_path(
                                                       self.origin_folder_path, file[0])
                                                       for file in self.OPHelper.test_file_list],
                                                   fs_options={'restoreDataInsteadOfStub': False},
                                                   no_of_streams=10)

            time.sleep(120)
            self.OPHelper.verify_stub(path=self.data_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            self.OPHelper.recall(path=self.data_folder_path)

            self.remove_registry_key()

            self.log.info('Basic Acceptance tests for Multi-threaded stubbing passed')
            self.log.info('Test case executed successfully.')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Basic Acceptance test for Multi-threaded stubbing failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
