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
    """Class for executing Sybase Rename Database and Restore to New Device Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Rename Database and Restore to New Device Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB50463"

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
        user_table_list = ["T50463_FULL", "T50463_TL1"]
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
            self.log.info("Full job %s completed", full_job.job_id)
            time.sleep(120)

            # Add test table before next transaction Log backup to user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_table_list[1])

            # Launch transaction log backup TL1
            self.log.info("First Transaction Log Backup : TL1")
            tl_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental')
            self.log.info("Transaction Log job %s completed", tl_job.job_id)
            time.sleep(120)
            status, expected_table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("status of expected table list fetch : %s", status)

            # Run restore to new device with new name
            restore_status = self.sybase_cv_helper.single_database_restore(
                self.database_name,
                user_table_list=user_table_list,
                expected_table_list=expected_table_list,
                sybase_create_device=True,
                rename_databases=True)


            # TC status setting based on data validation results
            if restore_status:
                self.log.info("Sybase Rename Database and "
                              "Restore to New Device Test case succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Sybase Rename Database and Restore to New Device Test case failed")
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
