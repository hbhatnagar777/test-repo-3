# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
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
    """Class for executing Basic acceptance Test Sybase Backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Dump Based Snap With Auxiliary Server"
        self.show_to_user = True
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.tcinputs = {
            "instance_properties": None
        }
        self.database_name = "DB52911"

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
        user_table_list = ["T52911_FULL", "T52911_TLOG1"]
        try:
            self.log.info("Started executing %s testcase", self.id)

            proxy_name = self.client.client_name
            instance_properties = self.tcinputs["instance_properties"]
            snap_engine_name = constants.SnapShotEngineNames.SM_SNAPSHOT_ENGINE_NETAPP_NAME.value

            # Test data Population
            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, user_table_list[0])

            # Enable Dump  based  intellisnap operation
            dump_based_option = constants.SYBASE_DUMP_BASED_WITH_AUXILIARY_SERVER
            status = self.sybase_cv_helper.enable_dump_based_snap(self.subclient,
                                                                  proxy_name=proxy_name,
                                                                  snap_engine=snap_engine_name,
                                                                  dump_based_backup_copy_option=
                                                                  dump_based_option,
                                                                  custom_instance_properties=
                                                                  instance_properties)
            self.log.info("Dump based backup option enabled : %s", status)

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
            self.log.info("Transaction Log  Backup")
            tl_job = self.sybase_cv_helper.backup_and_validation(
                self.subclient, backup_type='incremental')
            self.log.info("TL job : %s completed", tl_job.job_id)
            status, expected_table_list = self.sybase_helper.get_table_list(self.database_name)

            # Partial database restore from default precedence
            if self.sybase_cv_helper.single_database_restore(
                    self.database_name,
                    user_table_list,
                    expected_table_list=expected_table_list,
                    copy_precedence=0):
                self.log.info("Dump backup based partial"
                              " restore with default copy precedence succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Dump based partial restore testcase failed")
                self.log.info("Test Case Failed")
                self.status = constants.FAILED

        except BaseException as exp:
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
