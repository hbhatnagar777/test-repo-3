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

    extent_recall_log_validation()      --  Validate whether file was recalled in extents or not

    recall_status_validation()          --  Validate whether recall was successful or not
"""
from time import sleep
import datetime
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
        self.name = "onepass extent based recalls"
        self.client_machine = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.helper = None
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
        else:
            self.client_machine = UnixMachine(self.client, self.commcell)
            self.client_machine.create_registry(self.fsa, 'bEnableArchiveFileExtentBackup', 1)
            self.client_machine.create_registry(self.fsa, 'bEnableExtentBasedRecall', 1)

    def remove_registry_key(self):
        """
            Remove registry keys to disable this feature
        """
        if "windows" in self.client.os_info.lower():
            self.client_machine = WindowsMachine(self.client, self.commcell)
            self.client_machine.remove_registry(self.fsa, 'bEnableFileExtentBackup')
            self.client_machine.remove_registry(self.winfsdm, 'bEnableFileExtentBackup')
        else:
            self.client_machine = UnixMachine(self.client, self.commcell)
            self.client_machine.remove_registry(self.fsa, 'bEnableArchiveFileExtentBackup')
            self.client_machine.remove_registry(self.fsa, 'bEnableExtentBasedRecall')

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

    def extent_recall_log_validation(self):
        """
                Validate whether file was recalled in extents or not
        """
        lastMinsDateTime = datetime.datetime.now() - datetime.timedelta(minutes=10)
        timestamp = str(lastMinsDateTime.strftime('%m/%d %H:%M:%S'))
        past_10_minutes = datetime.datetime.strptime(timestamp, '%m/%d %H:%M:%S')
        search_term = "CFileExtentRestoreObject::OnExtentItemRecalled"
        log_lines = self.helper.get_logs_for_job_from_file(log_file_name="ClMgrS.log", search_term=search_term)
        if log_lines is None:
            raise Exception("No logs found for the search term %s", search_term)
        self.log.info("*" * 50)
        self.log.info("Found search term in log file\n\n %s", log_lines)
        self.log.info("*" * 50)
        for log_line in log_lines.split("\r\n"):
            if log_lines.find("shouldbearchived.txt"):
                logs = list(log_line.split())
                if logs:
                    result_log_time = str(logs[2] + " " + logs[3])
                    log_timestamp = datetime.datetime.strptime(result_log_time, '%m/%d %H:%M:%S')
                    # If logged in past 10 minutes print the log line and exit
                    if past_10_minutes < log_timestamp:
                        self.log.info(log_line)
                        self.log.info("********** File shouldbearchived.txt was recalled in extents **********")
                        break
                    else:
                        continue
            else:
                raise Exception("File shouldbearchived.txt was not recalled in extents. Please check ClMgrS.log")

    def recall_status_validation(self):
        """
                Validate whether recall was successful or not
        """

        # Get current month and day in 0m/0d format
        dt = datetime.datetime.today() - datetime.timedelta()
        current_month = str(dt.month)
        past_day = str(dt.day)
        date_validation = int(dt.day)
        #If date is less than 10, add a prefix 0 to match RecalledItems.log format
        if date_validation < 10:
            current_month_and_day = str.format('0' + current_month + '/' + '0' + past_day)
        else:
            current_month_and_day = str.format('0' + current_month + '/' + past_day)

        # Parse the logs to get log lines only for last 10 minutes
        lastMinsDateTime = datetime.datetime.now() - datetime.timedelta(minutes=10)
        timestamp = str(lastMinsDateTime.strftime('%m/%d %H:%M:%S'))
        log_past_10_minutes = datetime.datetime.strptime(timestamp, '%m/%d %H:%M:%S')

        # String to be searched
        search_term = "shouldbearchived.txt"
        log_lines = self.helper.get_logs_for_job_from_file(log_file_name="RecalledItems.log", search_term=search_term)
        if log_lines is None:
            raise Exception("No logs found for the search term")
        self.log.info("*" * 50)
        self.log.info("Found search term in specified log file\n\n %s", log_lines)
        self.log.info("*" * 50)

        # For each log line found with search string, grep only current day's logs based on date and timestamp
        for log_line in log_lines.split("\r\n"):
            logs = list(log_line.split())
            if logs:
                log_time = str(logs[2] + " " + logs[3])
                result_status = str(logs[11])
                date_logged = str(logs[2])
                result_log_time = datetime.datetime.strptime(log_time, '%m/%d %H:%M:%S')
                # If logged today in last 10 minutes in RecalledItems.log
                if date_logged == current_month_and_day:
                    if log_past_10_minutes < result_log_time:
                        self.log.info("Found line with search term logged in past 10 minutes %s", logs)
                        if result_status != 'Result[Success],':
                            raise Exception("File was not recalled sucessfully. Please check RecalledItems.log")
                        else:
                            self.log.info("********** File was recalled successfully **********")

    def run(self):
        """Main function for test case execution"""
        log = self.log
        log.info("start run test case")
        try:
            # Initialize test case inputs
            _desc = """
                                This test case will cover Extent Based Recall functionality for archiving
                                
                                1: Create new backupset/subclient 
                                  since for onepass we use v2 index, it is backupset level,
                                  in order to make each run start from clean on,
                                  we will always recreate backuspet

                                2: Create onepass subclient with migration rule set
                                
                                3: Add registry keys depending on ostype to enable extent based recall feature
                                
                                4: Restart ClMgrS service for registry changes to take effect

                                5: Assign subclient content with two files, with one file
                                   meet migration rule and one file not meet migration rule

                                6: Run archive jobs and backup corresponding stubs

                                7: Verify recall stub successfully bring data back

                                8: Verify that the stub is recalled in extents
                                
                                9: Verify that complete file has been recalled and no extents have been dropped
                                
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
            sleep(30)
            
            self.extent_recall_log_validation()
            self.recall_status_validation()
            
            log.info("Removing registry keys")
            self.remove_registry_key()

        except Exception as excp:
            log.error("exception raised with error %s" % str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
