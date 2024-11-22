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

    tear_down()     -- tear down function of this test case
"""
import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils import idautils
from Database.SybaseUtils.sybasehelper import SybaseHelper
from Database.SybaseUtils.sybasehelper import SybaseCVHelper


class TestCase(CVTestCase):
    """Class for executing Sybase Ondemand Subclient Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sybase Ondemand Subclient Test Case"
        self.sybase_helper = None
        self.sybase_cv_helper = None
        self.common_utils_object = None
        self.subclient_name = "SUB49281"
        self.database_list = ["DB49281_1", "DB49281_2"]

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
        user_table_list = {"DB49281_1": [], "DB49281_2": []}
        ondemand_dict = {"ondemand_subclient": True}

        try:
            self.log.info("Started executing app free restore testcase: %s", self.id)

            for i in self.database_list:
                table_name = "{0}_{1}".format(i, "first")
                self.sybase_cv_helper.sybase_populate_data(i, table_name)
                user_table_list[i].append(table_name)
                self.log.info("setting cumulative settings")
                cumulative_status = self.sybase_helper.set_cumulative(i)
                self.log.info("Cumulative Status for database %s is %s", i, cumulative_status)

            # get storage policy of default subclient
            storage_policy = self.sybase_cv_helper.get_storage_policy()

            # creating directive file on client
            file_path = self.sybase_cv_helper.directive_file(self.database_list)

            # ondemand subclient creation
            if self.instance.subclients.has_subclient(self.subclient_name):
                self.log.info(
                    "subclient with this name : %s already exists.deleting",
                    self.subclient_name)
                self.instance.subclients.delete(self.subclient_name)

            self.subclient = self.instance.subclients.add(subclient_name=self.subclient_name,
                                                          storage_policy=storage_policy,
                                                          advanced_options=ondemand_dict)

            # ondemand full backup using directive file
            self.log.info("Ondemand First Full backup")
            full_job = self.sybase_cv_helper.backup_and_validation(subclient=self.subclient,
                                                                   backup_type='full',
                                                                   directive_file=file_path)
            full_job_id = full_job.job_id
            self.log.info("Ondemand Full backup : %s", full_job_id)

            # Add test tables before user databases
            for i in self.database_list:
                cum_table_name = "{0}_CUM".format(i)
                self.sybase_cv_helper.single_table_populate(i, cum_table_name)
                user_table_list[i].append(cum_table_name)

            # ondemand cumulative backup using directive file
            self.log.info("Ondemand Cumulative backup")
            cumulative_job = self.sybase_cv_helper.backup_and_validation(
                subclient=self.subclient, backup_type='differential', directive_file=file_path)
            cumulative_job_id = cumulative_job.job_id
            self.log.info("Cumulative Job ID : %s", cumulative_job_id)

            self.log.info("User Table List of all test databases : %s", user_table_list)
            # Starting restores of test databases created in test run
            for i in self.database_list:
                restore_status = self.sybase_cv_helper.single_database_restore(
                    i, user_table_list[i])
                if restore_status is False:
                    raise Exception("Restore validation failed for database:%s", i)
                self.log.info("Restore status for database %s is :%s", i, restore_status)

            # TC status setting based on data validation results
            self.log.info("Sybase Ondemand Subclient Test case succeeded")
            self.log.info("Test Case Passed")
            self.status = constants.PASSED
        except Exception as exp:
            self.log.error(
                "Sybase Ondemand Subclient Testcase failed: %s", exp)
            self.log.exception("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.instance.subclients.delete(self.subclient_name)
        subclient = self.instance.subclients.get("default")
        for i in self.database_list:
            self.sybase_cv_helper.sybase_cleanup_test_data(i)
            self.sybase_cv_helper.sybase_delete_database_from_subclient(subclient, i)
        self.sybase_helper.sybase_helper_cleanup()
