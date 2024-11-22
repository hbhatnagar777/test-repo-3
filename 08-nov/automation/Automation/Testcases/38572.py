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
from AutomationUtils import idautils
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper


class TestCase(CVTestCase):
    """Class for executing Full Sybase Server Restore Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Full Server Restore Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB38572"

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Setup function")
        self.sybase_helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.sybase_helper.csdb = self.csdb
        self.log.info(
            "creation of sybase helper succeeded."
            "lets create sybase cv helper object")
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)

        # Setting Sybase Instance user password
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()
        self.common_utils_object = idautils.CommonUtils(self.commcell)

    def run(self):
        """Main function for test case execution"""
        user_tables = ["T38572_FULL", "T38572_TLOG1"]
        try:
            self.log.info("Started executing %s testcase", "38572")

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
            self.log.info("TL job : %s completed", tl_job.job_id)

            # Full sybase server restore
            restore_status = self.sybase_cv_helper.sybase_full_restore(self.database_name,
                                                                       user_tables)
            if restore_status:
                self.log.info("Full Sybase Server Restore Succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Full Sybase Server Restore Failed")
                self.log.info("Test Case Failed")
                self.status = constants.FAILED

        except Exception as exp:
            self.log.error("Full Sybase Server Restore failed with exception : %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("Cleanup inside tear down")
        self.sybase_cv_helper.sybase_cleanup_test_data(self.database_name)
        self.sybase_cv_helper.sybase_delete_database_from_subclient(self.subclient,
                                                                    self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
