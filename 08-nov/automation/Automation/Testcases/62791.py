# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  Initialize TestCase class

    run()                               --  run function of this test case

    add_registry_key()                  --  Add registry keys to enable this feature

    remove_registry_key()               --  Remove registry keys to disable this feature

    restart_clmgrs_service()            --  Restart ClMgrS service for registry key changes to take effect

    recall_status_validation()          --  Validate whether recall was successful or not
"""
from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.unix_machine import UnixMachine
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.onepasshelper import cvonepas_helper


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Re-stubbing: archived extent based recalls"
        self.client_machine = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.helper = None
        self.is_nas_turbo_type = False
        self.fsa = "FileSystemAgent"
        self.winfsdm = "WinFSDataMigrator"

    def add_registry_key(self):
        """
            Add registry keys to enable this feature
        """
        if "windows" in self.client.os_info.lower():
            self.client_machine = WindowsMachine(self.client, self.commcell)
            self.client_machine.create_registry(self.fsa, 'bEnableFileExtentBackup', 1, reg_type='DWord')
            self.client_machine.create_registry(self.winfsdm, 'bEnableFileExtentBackup', 1, reg_type='DWord')
            self.client_machine.create_registry(self.fsa, "nEnabledRestubbing", 1, reg_type='DWord')
        else:
            self.client_machine = UnixMachine(self.client, self.commcell)
            self.client_machine.create_registry(self.fsa, 'bEnableArchiveFileExtentBackup', 1)
            self.client_machine.create_registry(self.fsa, 'bEnableExtentBasedRecall', 1)
            self.client_machine.create_registry(self.fsa, 'nEnabledRestubbing', 1)

    def remove_registry_key(self):
        """
            Remove registry keys to disable this feature
        """
        if "windows" in self.client.os_info.lower():
            self.client_machine = WindowsMachine(self.client, self.commcell)
            self.client_machine.remove_registry(self.fsa, 'bEnableFileExtentBackup')
            self.client_machine.remove_registry(self.winfsdm, 'bEnableFileExtentBackup')
            self.client_machine.remove_registry(self.fsa, 'nEnabledRestubbing')
        else:
            self.client_machine = UnixMachine(self.client, self.commcell)
            self.client_machine.remove_registry(self.fsa, 'bEnableArchiveFileExtentBackup')
            self.client_machine.remove_registry(self.fsa, 'bEnableExtentBasedRecall')
            self.client_machine.remove_registry(self.fsa, 'nEnabledRestubbing')

    def restart_clmgrs_service(self):
        """
            Restart ClMgrS service after adding registry key for the changes to take effect
        """
        if "windows" in self.client.os_info.lower():
            client_instance = self.client.instance
            service_name = 'GxClMgrS({})'.format(client_instance)
            self.client.restart_service(service_name)
            return True
        else:
            self.client.restart_service()

    def run(self):
        """Main function for test case execution"""
        log = self.log
        log.info("start run test case")
        try:
            # Initialize test case inputs
            _desc = """
                                This test case will cover Extent Based Recall functionality for archiving

                                1: Create new archiveset/subclient
                                  since for onepass we use v2 index, it is backupset level,
                                  in order to make each run start from clean on,
                                  we will always recreate archiveset

                                2: Create Archiveset subclient with migration rule set

                                3: Add registry keys depending on ostype to enable extent based recall feature and 
                                  enable restubbing feature

                                4: Restart ClMgrS service for registry changes to take effect

                                5: Assign subclient content with two files, with one file
                                   meet migration rule and one file not meet migration rule

                                6: Run archive jobs and backup corresponding stubs

                                7: Verify recall stub successfully bring data back

                                8: Run new archive job

                                9: Check if data is not re-backed up and is stubbed in the job

                                10: Remove registry keys
            """
            log.info("Start running test case with id: %s ", str(self._id))
            log.info("below are detail test case description")
            log.info("*" * 50)
            log.info(_desc)
            log.info("*" * 50)
            helper = cvonepas_helper(self)
            helper.populate_tc_inputs(self)
            helper.populate_inputs(self)
            log.info(self.client.os_info)
            helper.create_archiveset(delete=True)
            if "unix" in self.client.os_info.lower():
                helper.create_subclient(scan_type=ScanType.RECURSIVE)
            else:
                helper.create_subclient()

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
            _subclient_cont = helper.subclient_props['subclient_content'][0]

            # Archiver set rules
            helper.testcase.subclient.archiver_retention = True
            helper.testcase.subclient.archiver_retention_days = -1
            helper.testcase.subclient.backup_retention = False
            helper.testcase.subclient.disk_cleanup = True
            helper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
            helper.testcase.subclient.backup_only_archiving_candidate = True

            # Prepare test data for testcase
            helper.org_hashcode = helper.prepare_turbo_testdata(
                _subclient_cont,
                helper.test_file_list,
                size1=1150976 * 1024, size2=8 * 1024
            )

            log.info("Adding registry keys to enable this feature")
            self.add_registry_key()
            log.info("Restarting services for registry changes to take effect")
            self.restart_clmgrs_service()
            sleep(30)

            # Archive jobs to archive files and backup corresponding stubs
            helper.run_archive(repeats=3)

            # Recall the complete file. File should be recalled in extents.
            helper.recall()

            # Wait for changes to be synced
            sleep(300)

            jobs = helper.run_archive(repeats=2)

            helper.restub_checks(jobs, 1)

            helper.verify_stub(_subclient_cont, helper.test_file_list, is_nas_turbo_type=self.is_nas_turbo_type)
            log.info("Removing registry keys")
            self.remove_registry_key()
            self.restart_clmgrs_service()

        except Exception as excp:
            log.error("exception raised with error %s" % str(excp))
            self.result_string = str(excp)
            self.remove_registry_key()
            self.restart_clmgrs_service()
            self.status = constants.FAILED
