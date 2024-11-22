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
import sys
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils import idautils
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper


class TestCase(CVTestCase):
    """Class for executing Sybase Cumulative Incremental Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Cumulative Incremental Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB50449"
        self.default_database_name = "Default50449"

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
        user_table_list = ["T50449_FULL", "T50449_TL1", "T50449_CUM", "T50297_TL2"]
        try:

            self.log.info("Started executing point in time restore testcase: %s", self.id)

            #Adding data to user db
            self.sybase_cv_helper.sybase_populate_data(self.database_name, user_table_list[0])

            #Adding data to default subclient db
            self.sybase_cv_helper.sybase_populate_data(self.default_database_name, user_table_list[0])

            # setting incremental dump support for user database
            cumulative_status = self.sybase_helper.set_cumulative(self.database_name)
            self.log.info("Cumulative Status for database %s is %s", self.database_name,
                          cumulative_status)

            # setting incremental dump support for default subclient user database
            cumulative_status = self.sybase_helper.set_cumulative(self.default_database_name)
            self.log.info("Cumulative Status for database %s is %s", self.default_database_name,
                          cumulative_status)

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # Create Subclient object of default subclient
            self.default_subclient = self.sybase_helper.instance.subclients.get(subclient_name="default")

            # subclient creation with user database
            self.subclient = self.sybase_cv_helper.create_sybase_subclient(self.database_name,
                                                                           storage_policy,
                                                                           [self.database_name])

            # Full backup of given user database
            self.log.info("Full Backup for new subclient")
            full_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'full', syntax_check=True,
                                                                   db=[self.database_name])
            full_job_end_time = self.sybase_cv_helper.get_end_time_of_job(full_job)
            self.log.info("Full Job End time : %s", full_job_end_time)
            time.sleep(120)

            # Full backup of given default subclient database
            self.log.info("Full Backup for default subclient")
            full_job_default = self.sybase_cv_helper.backup_and_validation(self.default_subclient,'full',
                                                                           syntax_check=True,
                                                                           db=[self.default_database_name])
            full_job_end_time_default = self.sybase_cv_helper.get_end_time_of_job(full_job_default)
            self.log.info("Full Job End time : %s", full_job_end_time_default)
            time.sleep(120)

            # Add test table before next transaction Log backup to user database
            self.sybase_cv_helper.single_table_populate(self.database_name, user_table_list[1])

            # Add another test table before next transaction Log backup to user database
            self.sybase_cv_helper.single_table_populate(self.database_name, user_table_list[2])

            # Add test table before next transaction log backup to default subclient database
            self.sybase_cv_helper.single_table_populate(self.default_database_name, user_table_list[1])

            # Add test table before next transaction log backup to default subclient database
            self.sybase_cv_helper.single_table_populate(self.default_database_name, user_table_list[2])


            # Launch cumulative backup
            self.log.info("Cumulative Backup")
            cum_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'differential', syntax_check=True,
                                                                  db=[self.database_name])
            cum_job_end_time = self.sybase_cv_helper.get_end_time_of_job(cum_job)
            self.log.info("Cumulative Job End time : %s", cum_job_end_time)
            status, cum_table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("Status of fetching cumulative table list : %s", status)
            time.sleep(120)

            # Launch cumulative backup on default subclient
            self.log.info("Cumulative Backup on default subclient")
            cum_job_2 = self.sybase_cv_helper.backup_and_validation(self.default_subclient, backup_type='differential',
                                                                    syntax_check=True,
                                                                    db=[self.default_database_name])
            cum_job_end_time_2 = self.sybase_cv_helper.get_end_time_of_job(cum_job_2)
            self.log.info("Cumulative Job End time : %s", cum_job_end_time_2)
            status_2, cum_table_list_2 = self.sybase_helper.get_table_list(self.default_database_name)
            self.log.info("Status of fetching cumulative table list : %s", status_2)
            time.sleep(120)

            # Make change 3 and run transaction log backup
            self.sybase_cv_helper.single_table_populate(self.database_name, user_table_list[3])

            # Make change 3 to default subclient user db
            self.sybase_cv_helper.single_table_populate(self.database_name, user_table_list[3])

            # Launch transaction log backup TL2 on new subclient
            self.log.info("Second Transaction Log Backup : TL2")
            tl2_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental', syntax_check=True,
                                                                  db=[self.database_name])
            tl2_job_end_time = self.sybase_cv_helper.get_end_time_of_job(tl2_job)
            self.log.info("TL2 Job End time : %s", tl2_job_end_time)
            time.sleep(120)

            # Launch Transaction log backup TL2 on default subclient
            self.log.info("Second Transaction Log Backup : TL2 on default subclient")
            tl2_job_default = self.sybase_cv_helper.backup_and_validation(self.default_subclient, 'incremental',
                                                                          syntax_check=True,
                                                                          db=[self.default_database_name])
            tl2_job_end_time_default = self.sybase_cv_helper.get_end_time_of_job(tl2_job_default)
            self.log.info("TL2 Job End time : %s", tl2_job_end_time_default)
            time.sleep(120)

            # Run restore to end time of cumulative backup
            self.log.info(
                "Restoring database %s to end time of cumulative job : %s",
                self.database_name,
                cum_job_end_time)

            restore_status = self.sybase_cv_helper.single_database_restore(
                database_name=self.database_name,
                user_table_list=user_table_list[:3],
                expected_table_list=cum_table_list,
                timevalue=cum_job_end_time)


            time.sleep(120)

            # Run Restore for default subclient user db to end time of cumulative backup
            self.log.info(
                "Restoring database %s to end time of cumulative job : %s",
                self.default_database_name,
                cum_job_end_time_2)

            restore_status_2 = self.sybase_cv_helper.single_database_restore(
                database_name=self.default_database_name,
                user_table_list=user_table_list[:3],
                expected_table_list=cum_table_list_2,
                timevalue=cum_job_end_time_2)

            # TC status setting based on data validation results
            if restore_status and restore_status_2:
                self.log.info("Sybase Cumulative Incremental Test case succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Sybase Cumulative Incremental Test case failed")
                self.log.info("Test Case Failed")
                self.status = constants.FAILED

        except Exception as exp:
            self.log.error("Testcase failed with exception : %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.sybase_cv_helper.sybase_cleanup_test_data(self.database_name)
        self.instance.subclients.delete(self.database_name)
        self.sybase_cv_helper.sybase_delete_database_from_subclient(self.default_subclient, self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
