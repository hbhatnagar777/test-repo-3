# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function for the test case

    run()           --  run function of this test case

    teardown()      --  teardown function of this test case
"""
import time
import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import idautils
from AutomationUtils import constants
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper


class TestCase(CVTestCase):
    """Class for executing Sybase Concurrent Log Backup Feature Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Concurrent Log Backup Feature Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.tcinputs = {
            "user_database": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.sybase_helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.sybase_helper.csdb = self.csdb
        self.log.info(
            "creation of sybase helper succeeded."
            "lets create sybase cv helper object")
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)
        self.common_utils_object = idautils.CommonUtils(self.commcell)

        # Setting Sybase Instance user password
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()

    def run(self):
        """Main function for test case execution"""
        database_name = self.tcinputs['user_database']
        user_table_list = ["T53108_T1", "T53108_T2", "T53108_T3"]

        try:
            self.log.info("Started executing %s testcase", self.id)

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # subclient creation with user database
            status = self.sybase_helper.remove_user_db(database_name)
            self.subclient = self.sybase_cv_helper.create_sybase_subclient(database_name,
                                                                           storage_policy,
                                                                           [database_name])
            # Full backup [F1] of given user database
            self.log.info("Full Backup")
            first_full_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'full')
            self.log.info("First full job %s completed", first_full_job.job_id)
            # Add test table before next full backup to user database
            self.sybase_cv_helper.single_table_populate(
                database_name, user_table_list[0])

            # second Full backup [F2] of given user database
            self.log.info("Second Full Backup")
            second_full_job = self.subclient.backup(backup_level='full')

            # make change c2 . Add test table
            self.sybase_cv_helper.single_table_populate(
                database_name, user_table_list[1])

            # sleep for two minutes
            time.sleep(120)

            # Launch transaction log backup TL1
            self.log.info("First Transaction Log Backup : TL1")
            tl1_job = self.subclient.backup(backup_level='incremental')

            # Lets check if TL1 backup  is completed
            if not tl1_job.wait_for_completion():
                raise Exception("Failed to run TL1 backup job with error: {0}".format(
                    tl1_job.delay_reason))

            # Transaction log backup TL1 validation
            status = self.common_utils_object.backup_validation(tl1_job.job_id, "Transaction Log")
            if status:
                self.log.info("Transaction Log Backup Validation successful")

            # Fetch TL1 job's end time
            tl1_end_time = tl1_job.end_time

            # Fetch table lists and table content lists after TL1 job
            status, tl1_table_lists = self.sybase_helper.get_table_list(database_name)

            # Check if full backup F2 is completed
            if not second_full_job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: {0}".format(
                    second_full_job.delay_reason))

            # Full backup job 2 validation
            status = self.common_utils_object.backup_validation(second_full_job.job_id, "Full")
            if status is True:
                self.log.info("Backup Validation for second full is successful")

            # Make change c3 after F2 backup
            self.sybase_cv_helper.single_table_populate(
                database_name, user_table_list[2])

            # Transaction Log backup TL2 of given user database
            self.log.info("Transaction Log Backup TL2")
            tl2_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental')

            # Fetch end time of TL2 job
            tl2_end_time = tl2_job.end_time

            # Fetch table lists and table content after TL2
            status, tl2_table_lists = self.sybase_helper.get_table_list(database_name)

            # Invoke restores based on concurrent backup
            restore_status = self.sybase_cv_helper.concurrent_backup_based_restore(tl1_end_time,
                                                                                   tl2_end_time,
                                                                                   tl1_table_lists,
                                                                                   tl2_table_lists,
                                                                                   user_table_list,
                                                                                   database_name)

            # TC status setting based on data validation results
            if restore_status:
                self.log.info("Concurrent Backup Test case succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Concurrent Backup Test case failed")
                self.log.info("Test Case Failed")
                self.status = constants.FAILED
        except Exception as exp:
            self.log.error("Testcase failed with exception : %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED


    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("Cleanup inside tear down")
        table_list = ["T53108_T1", "T53108_T2", "T53108_T3"]
        self.sybase_cv_helper.cleanup_tables(self.tcinputs['user_database'], table_list)
        self.instance.subclients.delete(self.tcinputs['user_database'])
        self.sybase_helper.sybase_helper_cleanup()
