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

    validate_multi_threading_from_logs()    --  Validates multi-threaded index query from clBackup.log

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from AutomationUtils.machine import Machine
import time


class TestCase(CVTestCase):
    """Class for Basic Acceptance Test for Multi-Threaded Index Query"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Multi-Threaded Index Query"
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
        self.fsa = "FileSystemAgent"
        self.winfsdm = "WinFSDataMigrator"

    def add_registry_key(self):
        """
            Add registry keys to enable this feature
        """
        if "linux" in self.client.os_info.lower():
            self.OPHelper.client_machine.create_registry(self.fsa, 'NumFSStubCollectSplitAt', self.reg_key_val)
            return

        if self.tcinputs.get("Coordinator"):
            coord_client = Machine(machine_name=self.tcinputs.get("Coordinator"), commcell_object=self.commcell)
            coord_client.create_registry(self.winfsdm, "NumFSTurboStubCollectSplitAt",
                                                         self.reg_key_val,
                                                         reg_type='DWord')
        else:
            self.OPHelper.client_machine.create_registry(self.winfsdm, "NumFSTurboStubCollectSplitAt",
                                                         self.reg_key_val,
                                                         reg_type='DWord')
        time.sleep(30)

    def remove_registry_key(self):
        """
            Remove registry keys to disable this feature
        """
        if "linux" in self.client.os_info.lower():
            self.OPHelper.client_machine.remove_registry(self.fsa, 'NumFSStubCollectSplitAt')
            return
        if self.tcinputs.get("Coordinator"):
            coord_client = Machine(machine_name=self.tcinputs.get("Coordinator"), commcell_object=self.commcell)
            coord_client.remove_registry(self.winfsdm, "NumFSTurboStubCollectSplitAt")
        else:
            self.OPHelper.client_machine.remove_registry(self.winfsdm, "NumFSTurboStubCollectSplitAt")
        time.sleep(30)

    def validate_multi_threading_from_logs(self, job_id):
        """
            Validates if index query is multi-threaded and performed in backup phase
        """
        if "linux" in self.client.os_info.lower():
            log_line = self.OPHelper.client_machine.get_logs_for_job_from_file(job_id=job_id,
                                                                               log_file_name="clBackupParent.log",
                                                                               search_term="Index query completed")
            if log_line is None:
                return False
            else:
                self.log.info(log_line)
                log_line = self.OPHelper.client_machine.get_logs_for_job_from_file(job_id=job_id,
                                                                                   log_file_name="clBackupParent.log",
                                                                                   search_term="GetIndexLookupThreads")
        else:
            if self.tcinputs.get("Coordinator"):
                coord_client = Machine(machine_name=self.tcinputs.get("Coordinator"), commcell_object=self.commcell)
                log_line = coord_client.get_logs_for_job_from_file(job_id=job_id, log_file_name="clBackup.log",
                                                                  search_term="CFsdmIndexLookupManager::PrepareLookupJobs")
                if log_line is None:
                    return False
                self.log.info(log_line)
                log_line = log_line.split('TotalLookupJobs')[1]
            else:
                log_line = self.OPHelper.client_machine.get_logs_for_job_from_file(job_id=job_id,
                                                                                   log_file_name="clBackup.log",
                                                                                   search_term="CFsdmIndexLookupManager::PrepareLookupJobs")
                if log_line is None:
                    return False
                self.log.info(log_line)
                log_line = log_line.split('TotalLookupJobs')[1]

        if log_line is None:
            return False

        no_of_stubcollect = int(log_line.split('[')[1].split(']')[0])

        n = int(self.no_of_files/self.reg_key_val)
        if no_of_stubcollect >= n:
            self.log.info("No of stubcollects used for index query: {}".format(no_of_stubcollect))
            return True
        else:
            self.log.info("No of stubcollects: {} is not/less than expected".format(no_of_stubcollect))
            return False

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
                size1=5 * 1024, size2=5 * 1024)
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
            "fileSizeGreaterThan": 4,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": True,
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
        2. Under 'WinFSDataMigrator', add 'bEnableMultiThreadedIndexQueryStub' and 'bIsMultiThreadedIdxQueryEnabled' 
            keys with value 1 and 'NumFSTurboStubCollectSplitAt' key with value 10
            In case of multinode backup, the index query will be performed on coordinator node.
            Input "Coordinator" variable in inputJSON for this.
        3. Run three archive jobs.
        4. Verify that all the qualified files got stubbed.
        5. Validate from clBackup.log that index query is done and stubcollects are created 
        6. Recall all the files from 'Origin' Folder and verify checksum.  
        """

        try:
            self.add_registry_key()

            jobs = self.OPHelper.run_archive(repeats=1)

            if int(jobs[0].details['jobDetail']['detailInfo']["stubbedFiles"]) != 0:
                self.log.info("The archive jobs are running in POC mode, the TC applies for non-POC mode\n")
                return

            _disk_cleanup_rules = {
                "enableRedundancyForDataBackedup": False
            }
            self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

            time.sleep(10)
            jobs = self.OPHelper.run_archive(repeats=1)
            self.OPHelper.verify_stub(path=self.origin_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)

            if self.validate_multi_threading_from_logs(jobs[0].job_id) is False:
                raise Exception("Multi-threading validation from logs failed\n")

            self.log.info("The index query is performed in backup phase\n")
            self.OPHelper.recall(path=self.origin_folder_path)

            self.remove_registry_key()

            self.log.info('Basic Acceptance tests for Multi-threaded index query passed')
            self.log.info('Test case executed successfully.')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Basic Acceptance test for Multi-threaded index query failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.remove_registry_key()
            self.status = constants.FAILED
