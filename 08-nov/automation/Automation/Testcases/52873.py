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
from AutomationUtils import idautils
from AutomationUtils import constants
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper

class TestCase(CVTestCase):
    """Class for executing Sybase File System Based Snap Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase File System Based Snap Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB52873"

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
        user_table_list = ["T52873_FULL", "T52873_TLOG1"]
        full_server_restore_status = False
        partial_restore_status = False

        try:
            self.log.info("Started executing %s testcase", self.id)

            # Test data Population
            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_table_list[0])

            # Enable FS based  intellisnap operation
            snap_engine_name = constants.SnapShotEngineNames.SM_SNAPSHOT_ENGINE_NETAPP_NAME.value
            status = self.sybase_cv_helper.enable_fs_based_snap(
                self.subclient,
                proxy_name=self.client.client_name,
                snap_engine=snap_engine_name)
            self.log.info("FS based snap enabled : %s", status)

            # Snap Backup with Backup Copy on default subclient
            self.log.info("Snap Backup with Backup Copy")
            snap_job_status = self.sybase_cv_helper.snap_backup(
                self.subclient,
                create_backup_copy_immediately=True)
            if snap_job_status:
                self.log.info("Snap and backup copy succeeded")

            # Add test table before next transaction log backup to custom user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, user_table_list[1])

            # Transaction Log Backup
            self.log.info("Transaction Log Backup")
            tl_job = self.sybase_cv_helper.backup_and_validation(
                self.subclient, backup_type='incremental')
            self.log.info("TL job : %s completed", tl_job.job_id)
            status, expected_table_list = self.sybase_helper.get_table_list(self.database_name)

            # Full Server restore from transaction Log backup
            if self.sybase_cv_helper.sybase_full_restore(
                    self.database_name,
                    user_table_list,
                    timevalue=None):
                self.log.info("Full Server Restore from Snap backup succeeded")
                full_server_restore_status = True

            # Partial database restore from backup copy
            if self.sybase_cv_helper.single_database_restore(
                    self.database_name,
                    user_table_list,
                    expected_table_list=expected_table_list,
                    copy_precedence=2):
                self.log.info("Partial restore from backup copy succeeded")
                partial_restore_status = True

            # TC status setting based on data validation results
            if full_server_restore_status and partial_restore_status:
                self.log.info("File System Snap based Sybase Acceptance testcase passed")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("File System Snap based Sybase Acceptance testcase failed")
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
        subclient = self.instance.subclients.get("default")
        self.sybase_cv_helper.sybase_delete_database_from_subclient(subclient, self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
