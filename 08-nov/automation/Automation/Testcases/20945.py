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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper


class TestCase(CVTestCase):
    """Class for executing DR Sybase Restore Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DR Sybase Restore Test Cas"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.database_name = "DB20945"

    def setup(self):
        """Setup function of this test case"""
        self.sybase_helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.sybase_helper.csdb = self.csdb
        self.log.info(
            "creation of sybase helper succeeded."
            "now creating sybase cv helper object")
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)

        # Setting Sybase Instance user password
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()

    def run(self):
        """Main function for test case execution"""
        user_tables = ["T20945_FULL", "T20945_TLOG1"]
        try:
            #  Test data Population
            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_tables[0])

            # Full backup on default subclient
            self.log.info("Full Backup")
            full_job = self.sybase_cv_helper.backup_and_validation(
                self.subclient, backup_type='full')
            self.log.info("Full job : %s completed", full_job.job_id)

            # Add test table before next transaction log backup
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_tables[1])

            # Transaction Log Backup
            self.log.info("Transaction Log Backup")
            tl_job = self.sybase_cv_helper.backup_and_validation(
                self.subclient, backup_type='incremental')
            self.log.info("Transaction Log job : %s completed", tl_job.job_id)
            tl1_job_end_time = self.sybase_cv_helper.get_end_time_of_job(tl_job)

            # Full sybase server restore
            restore_status = self.sybase_cv_helper.sybase_full_restore(
                user_database_name=self.database_name,
                user_table_list=user_tables,
                timevalue=tl1_job_end_time,
                dr_restore_flag=True)
            if restore_status:
                self.log.info("DR Sybase Server Restore Succeeded")
            else:
                self.log.info("DR Sybase Server Restore Failed")
                self.status = constants.FAILED

        except Exception as exp:
            self.log.error("DR Sybase Server Restore failed with exception : %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.sybase_cv_helper.sybase_cleanup_test_data(self.database_name)
        self.sybase_cv_helper.sybase_delete_database_from_subclient(self.subclient,
                                                                    self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
