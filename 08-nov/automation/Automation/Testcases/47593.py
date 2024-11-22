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

    tear_down()     -- tear down function of this test case
"""
import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils import idautils
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper


class TestCase(CVTestCase):
    """Class for executing Sybase Application Free Restore Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Application Free Restore Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.database_name = "DB47593"

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
        full_table_name = "{0}_FULL".format("T47593")
        tl_table_name = "{0}_TL1".format("T47593")
        try:
            self.log.info("Started executing app free restore testcase: %s", self.id)

            self.sybase_cv_helper.sybase_populate_data(
                self.database_name, full_table_name)

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # subclient creation with user database
            self.subclient = self.sybase_cv_helper.create_sybase_subclient(self.database_name,
                                                                           storage_policy,
                                                                           [self.database_name])
            # Full backup of given user database
            self.log.info("Full Backup")
            full_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'full')
            full_job_id = full_job.job_id

            # Add test table before next transaction Log backup to user database
            self.sybase_cv_helper.single_table_populate(
                self.database_name, tl_table_name)

            # Launch transaction log backup TL1
            self.log.info("First Transaction Log Backup : TL1")
            tl_job = self.sybase_cv_helper.backup_and_validation(self.subclient, 'incremental')
            tl_job_id = tl_job.job_id

            backup_job_ids = [int(full_job_id), int(tl_job_id)]
            user_tables = [full_table_name, tl_table_name]
            user_name = self.instance.localadmin_user
            password = self.sybase_helper.get_local_user_password()
            destination_path = self.sybase_helper.remote_path

            # Starting Application free restore
            restore_status = self.sybase_cv_helper.restore_to_disk_and_validation(
                destination_path,
                backup_job_ids,
                user_name,
                password,
                self.database_name,
                user_tables)
            # TC status setting based on data validation results
            if restore_status:
                self.log.info("Sybase Application Free Restore Test case succeeded")
                self.log.info("Test Case Passed")
                self.status = constants.PASSED
            else:
                self.log.info("Sybase Application Free Restore Test case failed")
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
        self.sybase_cv_helper.sybase_cleanup_test_data(self.database_name)
        self.instance.subclients.delete(self.database_name)
        self.sybase_helper.sybase_helper_cleanup()
