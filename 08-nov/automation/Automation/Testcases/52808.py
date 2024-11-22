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
    """Class for executing Basic acceptance Test Sybase Backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Basic acceptance Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB52808"

    def setup(self):
        """Setup function of this test case"""

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
        user_tables = ["T52808_FULL", "T52808_TLOG1"]
        try:
            self.log.info("Started executing %s testcase", self.id)
            #  Test data Population
            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_tables[0])
            # Full backup on default subclient
            self.log.info("Full Backup")
            full_job = self.sybase_cv_helper.backup_and_validation(
                self.subclient, backup_type='full')
            self.log.info("Full job : %s completed", full_job.job_id)

            # Add test table before next transaction log backup to custom user
            # database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_tables[1])

            # Transaction Log Backup
            self.log.info("Transaction Log Backup")
            tl_job = self.sybase_cv_helper.backup_and_validation(
                self.subclient, backup_type='incremental')
            self.log.info("TL job : %s completed", tl_job.job_id)

            # single database restore and validation
            restore_status = self.sybase_cv_helper.single_database_restore(self.database_name,
                                                                           user_tables)
            # TC status setting based on data validation results
            if restore_status:
                self.log.info("Sybase Basic acceptance Test Case passed")
                self.status = constants.PASSED
            else:
                self.log.info("Sybase Basic acceptance Test Case Failed")
                self.status = constants.FAILED
        except Exception as exp:
            self.log.error("Testcase failed with exception : %s", exp)
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
