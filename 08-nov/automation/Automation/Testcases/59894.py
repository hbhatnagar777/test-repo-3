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
    """Class for executing MySQL backup and restore with a corrupt view within a database"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MySQL backup and restore with corrupt view in database"
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
            self.mysql_helper.cleanup_test_data(database_prefix="automation_cv_full")

    def run(self):
        """Run function for test case execution"""

        try:
            # Checking the basic settings required for Automation
            if not self.subclient.is_default_subclient:
                raise Exception("Please provide default subclient name as input")

            # Populating Databases For Full Backup
            database_list = self.mysql_helper.generate_test_data(
                database_prefix="automation_cv_full")

            # Delete dependent tables for view to make the views corrupt
            self.mysql_helper.delete_table_for_dependent_views(database_list)

            # Running Full Backup
            job_obj = self.dbhelper_object.run_backup(self.subclient, 'FULL')
            job_events = job_obj.get_events()

            db_list, event_list = self.mysql_helper.get_job_event_description_with_severity_six(
                job_events)

            event_string = "references invalid table(s) or column(s) or function(s) or " \
                           "definer/invoker of view lack rights to use them"

            # Database list and Event Verification
            if database_list.sort() == db_list.sort():
                for events in event_list:
                    if event_string not in events:
                        raise Exception("Event Verification failed")
            else:
                raise Exception("Database list verification failed")

            self.log.info("Event verification is success")
            self.log.info("Database list verification is success")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
