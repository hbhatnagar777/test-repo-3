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
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case

    tear_down()                 --  Tear down function for this testcase

    run()                       --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing MySQL support for restoring comments as part of dump restore
    test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MySQL support for restoring comments as part of dump restore"
        self.mysql_helper = None
        self.dbhelper_object = None

    def setup(self):
        """Setup function of this test case"""
        self.mysql_helper = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username)
        self.dbhelper_object = DbHelper(self.commcell)

    def tear_down(self):
        """Tear down function for this testcase"""
        if self.mysql_helper:
            self.log.info("Deleting Automation Created Tables")
            self.mysql_helper.cleanup_test_data(database_prefix='automation_cv')

    def run(self):
        """Run function for test case execution"""

        try:
            # Checking the basic settings required for Automation
            self.log.info(
                "Check Basic Setting of mysql server before stating the test cases")
            self.mysql_helper.basic_setup_on_mysql_server(log_bin_check=True)

            if not self.subclient.is_default_subclient:
                raise Exception("Please provide default subclient name as input")

            # Populating Databases For Full Backup
            db_full_bkp_list = self.mysql_helper.generate_test_data(
                database_prefix="automation_cv_full", comment_string="comment_comment")

            # Running Full Backup
            self.dbhelper_object.run_backup(self.subclient, 'FULL')

            # Populating Databases For INC 1 Backup
            db_inc1_bkp_list = self.mysql_helper.generate_test_data(
                database_prefix="automation_cv_inc1", comment_string="comment_comment")

            # Running Incremental data + log Backup
            self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

            # Getting Database Size and table sizes (Full + Inc 1)
            db_size_full_bkp = self.mysql_helper.get_database_information()

            self.mysql_helper.get_default_subclient_contents()

            # Getting Database Size and table sizes (Incremental 2)
            self.mysql_helper.populate_database(db_inc1_bkp_list, comment_string="comment_comment")

            # Running Incremental Backup
            self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

            # Getting Database Size and table sizes (2nd incr)
            db_size_inc2_bkp = self.mysql_helper.get_database_information()

            self.mysql_helper.cleanup_test_data(database_prefix='automation_cv')

            # Running In Place Data Only Restore
            self.log.info("Running In Place Restore - Data Only")
            self.mysql_helper.run_data_restore_and_validation(database_info=db_size_full_bkp)

            # Running In Place Log Only Restore
            self.log.info("Running In Place Restore - Log Only")
            self.mysql_helper.run_data_restore_and_validation(
                data_restore=False, log_restore=True, database_info=db_size_inc2_bkp)

            self.mysql_helper.cleanup_test_data(database_prefix='automation_cv')

            # Running In Place Data + Log Restore
            self.log.info("Running In Place Restore - Data + Log")
            self.mysql_helper.run_data_restore_and_validation(
                log_restore=True, database_info=db_size_inc2_bkp)

            comment_status = self.mysql_helper.check_comments_in_table(database_list=(
                    db_full_bkp_list + db_inc1_bkp_list), comment_string="comment_comment")
            if comment_status:
                self.log.info("Comment count is success")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
