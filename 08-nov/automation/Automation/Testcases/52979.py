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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper


class TestCase(CVTestCase):
    """
    Class for executing
    description
    this test case will do basic onepass related function check
    will cover backupset/subclient creation and subclient level
    onepass properties setting
    stub creation, recall/recall verification, restore data/restore
    verification all these operations
    detail steps:
    1:under existing client, create new backupset/subclient 
      since for onepass we use v2 index, it is backupset level,
      in order to make each run start from clean on,
      we will always recreate backuspet

    2: create onepass subclient with migration rule set properly

    3: assign subclient content with two files, with one file should
      meet migration rule and one file should not meet migration rule

    4: run archive job,verify file that meet migration rule is stubbed
       and not meet will not stubbed

    5: verify recall stub successfully bring data back

    6: do in place restore data and verify restore data match original data
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "onepass basic scenario check"

    def run(self):
        """Main function for test case execution"""
        log = self.log
        log.info("start run test case")
        try:
            # Initialize test case inputs
            _desc = """
                    this test case will do basic onepass related function check
                    will cover backupset/subclient creation and subclient level
                    onepass properties setting
                    stub creation, recall/recall verification, restore
                    data/restore verification all these operations
                    detail steps:
                    1:under existing client, create new backupset/subclient 
                      since for onepass we use v2 index, it is backupset level,
                      in order to make each run start from clean on,
                      we will always recreate backuspet

                    2: create onepass subclient with migration rule set

                    3: assign subclient content with two files, with one file
                       meet migration rule and one file not meet migration rule

                    4: run archive job,verify file that meet migration rule is
                      stubbed and not meet will not stubbed

                    5: verify recall stub successfully bring data back

                    6: do in place restore data and verify restore data match
                       original data
                    """
            log.info("start running test case with id: %s ", str(self._id))
            log.info("below are detail test case description")
            log.info("*" * 80)
            log.info(_desc)
            log.info("*" * 80)
            helper = cvonepas_helper(self)
            helper.populate_tc_inputs(self)
            helper.populate_inputs(self)
            helper.create_backupset(delete=False)
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
            helper.testcase.subclient.backup_retention = True
            helper.testcase.subclient.disk_cleanup = True
            helper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
            helper.org_hashcode = helper.prepare_turbo_testdata(
                _subclient_cont,
                helper.test_file_list,
                size1=12*1024, size2=8*1024
                )
            _ret_job_list = helper.run_archive()
            # extra one more backup to backup stubs
            helper.run_archive()
            # wait os to sync the changes
            sleep(30)
            helper.verify_stub()
            helper.recall()
            helper.restore_in_place(
                paths=helper.subclient_props['subclient_content']
                )
            _status = helper.verify_restore_result(
                dest_path=_subclient_cont,
                verify_acl=True
                )
            if _status is True:
                log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
                self.status = constants.PASSED
            else:
                log.info("***TEST CASE FAILED***")
                self.status = constants.FAILED

        except Exception as excp:
            log.error("exception raised with error %s" % str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
