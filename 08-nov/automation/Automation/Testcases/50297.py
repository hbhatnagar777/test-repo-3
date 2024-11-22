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
    """Class for executing Sybase Point In Time Restore Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Point In Time Restore Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB50297"

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
        user_table_list = ["T50297_FULL", "T50297_TL1", "T50297_TL2"]
        try:
            self.log.info("Started executing point in time restore testcase: %s", self.id)

            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_table_list[0])

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # subclient creation with user database
            self.subclient = self.sybase_cv_helper.create_sybase_subclient(self.database_name,
                                                                           storage_policy,
                                                                           [self.database_name])

            # Full backup of given user database
            self.log.info("Full Backup")
            full_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'full')
            full_job_end_time = self.sybase_cv_helper.get_end_time_of_job(full_job)
            self.log.info("Full Job End time : %s", full_job_end_time)
            time.sleep(120)

            # Add test table before next transaction Log backup to user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_table_list[1])

            # Launch transaction log backup TL1
            self.log.info("First Transaction Log Backup : TL1")
            tl_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental')
            tl1_job_end_time = self.sybase_cv_helper.get_end_time_of_job(tl_job)
            self.log.info("TL1 Job End time : %s", tl1_job_end_time)
            status, tl1_table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("table list after TL1 status : %s", status)
            time.sleep(120)

            # Add another test table before next transaction Log backup to user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_table_list[2])

            # Launch transaction log backup TL2
            self.log.info("Second Transaction Log Backup : TL2")
            tl2_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental')
            tl2_job_end_time = self.sybase_cv_helper.get_end_time_of_job(tl2_job)
            self.log.info("TL2 Job End time : %s", tl2_job_end_time)
            time.sleep(120)

            # Run restore to end time of transaction log backup
            self.log.info(
                "Restoring database %s to end time of TL1 job : %s",
                self.database_name,
                tl1_job_end_time)
            restore_status = self.sybase_cv_helper.single_database_restore(
                database_name=self.database_name,
                user_table_list=user_table_list[:2],
                expected_table_list=tl1_table_list,
                timevalue=tl1_job_end_time)

            # TC status setting based on data validation results
            if restore_status:
                self.log.info("Sybase Point in Time Restore Test case succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Sybase Point in Time Restore Test case failed")
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
        subclient = self.instance.subclients.get("default")
        self.sybase_cv_helper.sybase_delete_database_from_subclient(subclient, self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
