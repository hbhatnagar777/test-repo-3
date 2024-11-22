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
    """Class for executing Sybase Snap Redirect Based Cross Machine Restore Test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Snap Redirect Based Cross Machine Restore"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.database_name = "master53882"
        self.tcinputs = {
            "destination_client": None,
            "destination_instance": None,
            "base_path":None
        }

    def setup(self):
        """Setup function of this test case"""

        self.sybase_helper = SybaseHelper(
            self.commcell, self.instance, self.client)
        self.sybase_helper.csdb = self.csdb
        self.log.info(
            "creation of sybase helper succeeded."
            " and create sybase cv helper object")
        self.sybase_cv_helper = SybaseCVHelper(self.sybase_helper)

        # Setting Sybase Instance user password
        self.sybase_helper.sybase_sa_userpassword = self.sybase_helper.get_sybase_user_password()


    def run(self):
        """Main function for test case execution"""
        destination_client = self.tcinputs["destination_client"]
        destination_instance = self.tcinputs["destination_instance"]
        user_table_list = ["T53882_FULL"]
        redirect_path = self.tcinputs["base_path"]
        try:
            # Generate test data
            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_table_list[0])

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # subclient creation with user database
            self.subclient = self.sybase_cv_helper.create_sybase_subclient(self.database_name,
                                                                           storage_policy,
                                                                           [self.database_name])
            # Enable FS based intellisnap operation
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
            self.log.info("Snap and backup copy succeeded : %s ", snap_job_status)

            status, expected_table_list = self.sybase_helper.get_table_list(self.database_name)
            self.log.info("Status of table list fetch: %s", status)

            # snap based cross machine redirect restore
            self.log.info("Snap copy based redirect restore on cross machine")
            snap_restore_status = self.sybase_cv_helper.single_database_restore(
                self.database_name,
                user_table_list=user_table_list,
                expected_table_list=expected_table_list,
                destination_client=destination_client,
                destination_instance=destination_instance,
                sybase_create_device=True,
                rename_databases=True,
                copy_precedence=1,
                snap_redirect=True,
                redirect_path=redirect_path)
            self.log.info("Snap based redirect restore on cross"
                          " machine succeeded : %s ", snap_restore_status)

            # backup copy based redirect restore in-place
            self.log.info("Backup copy based redirect restore on source machine")
            backup_copy_restore = self.sybase_cv_helper.single_database_restore(
                self.database_name,
                user_table_list=user_table_list,
                expected_table_list=expected_table_list,
                sybase_create_device=True,
                rename_databases=True,
                copy_precedence=2,
                snap_redirect=True,
                redirect_path=redirect_path)
            self.log.info("Backup Copy based redirect restore on"
                          " source succeeded : %s", backup_copy_restore)
            self.log.info("Sybase Snap Redirect Based Cross Machine Restore succeeded")
            self.log.info("Test Case Passed")
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
