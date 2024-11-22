# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case

    restore_and_validation()    --  Method to run inplace restore and validate data after restore

    populate_database()         --  Inserts test tables in the each database in the
    subclient content

    cleanup_data()              --  cleans up test generated data

    tear_down()                 --  Tear down function for this testcase

    run()                       --  run function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of MySQL XtraBackup test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Acceptance test case for MySQL XtraBackup"
        self.mysql_helper = None
        self.dbhelper_object = None
        self.full_tables_dict = None
        self.inc_tables_dict1 = None

    def setup(self):
        """Setup function of this test case"""
        self.mysql_helper = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username)
        self.dbhelper_object = DbHelper(self.commcell)

    def restore_and_validation(self, data_restore=True, log_restore=True, database_info=None):
        """method to run inplace restore and validate data after restore

        Args:
            data_restore   (bool)  -- data restore flag

                default: True

            log_restore    (bool)  -- log restore flag

                default: True

            database_info  (dict)  -- database information to validate against
            the data after restore

                default: None

        Args:
            Exception:

                if database information dict is not provided

                if failed to run restore job

        """
        if database_info is None:
            raise Exception(
                "database information needed to validate the data after restore")
        if not ((not data_restore) and log_restore):
            self.cleanup_data()
        # Removing mysql and sys system db's from restore list
        paths = self.subclient.content.copy()

        if '\\mysql' in paths:
            paths.remove('\\mysql')

        if '\\sys' in paths:
            paths.remove('\\sys')

        job = self.instance.restore_in_place(
            paths,
            self.client.job_results_directory,
            self.client.client_name,
            self.instance.instance_name,
            data_restore=data_restore,
            log_restore=log_restore)
        self.log.info("Started restore with Job ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run data only restore job with error: {1}".format(
                    job.delay_reason
                )
            )

        self.log.info("Successfully finished data only restore job")

        # Getting Database Size and Table sizes after Restore
        data_after_restore = self.mysql_helper.get_database_information(
            self.subclient.content)

        self.log.info("###Starting data validation after restore###")
        # validating data after restore
        self.mysql_helper.validate_db_info(
            database_info,
            data_after_restore)

    def populate_database(self):
        """Inserts test tables in the each database in the subclient content

        Returns:

            database_dict   (dict)  -- Dictionary consisting of database names
            as key and its table list as value

        """
        # Timestamp For Tablenames
        timestamp_full = str(int(time.time()))
        database_dict = {}
        self.log.info("Populating Databases before Backup")
        for each_db in self.subclient.content:
            table_list = self.mysql_helper.create_table_with_text_db(
                each_db,
                table_name="full_38610_{0}".format(timestamp_full),
                no_of_tables=10,
                column_in_each_table=5,
                drop_table_before_create=False)
            database_dict[each_db] = table_list
        return database_dict

    def cleanup_data(self):
        """cleans up test generated data"""
        # Dropping the Automation created tables for Full Backup
        self.mysql_helper.clean_up_tables(self.full_tables_dict)
        # Dropping the Automation created tables for Incremental Backup 1
        self.mysql_helper.clean_up_tables(self.inc_tables_dict1)

    def tear_down(self):
        """Tear down function for this testcase"""
        self.log.info("Deleting Automation Created Tables")
        self.cleanup_data()


    def run(self):
        """Run function for test case execution"""

        try:
            # Checking the basic settings required for Automation
            self.log.info(
                "Check Basic Setting of mysql server before stating the test cases")
            self.mysql_helper.basic_setup_on_mysql_server()

            # Checking whether Binary Logging is enabled or not in MySQL Server
            # (Required to run Incremental Backup)
            self.mysql_helper.log_bin_on_mysql_server()

            ## check xtrabackup eligibility
            if not self.mysql_helper.is_xtrabackup_eligible():
                raise Exception("Failed to qualify xtrabackup eligibility")

            self.log.info("Read subclient content")
            self.log.info("Subclient Content: %s", self.subclient.content)

            if self.subclient.content == [] or self.subclient.content == ['/']:
                raise Exception(
                    "Subclient Content is empty please add subclient content from Commcell Console"
                )

            # Populating Databases For Full Backup
            self.full_tables_dict = self.populate_database()

            # Running Full Backup
            full_job = self.dbhelper_object.run_backup(self.subclient, 'FULL')

            self.log.info("Checking if xtrabackup is effective during FULL backup")
            if not self.mysql_helper.is_xtrabackup_effective(full_job.job_id):
                raise Exception("xtrabackup was not effective during FULL backup")
            self.log.info("xtrabackup was effective during FULL backup")
            # Populating Databases For INC 1 Backup
            self.inc_tables_dict1 = self.populate_database()

            # Running Incremental Backup
            self.dbhelper_object.run_backup(self.subclient, 'INCREMENTAL')

            # Getting Database Size and table sizes (Incremental 2)
            db_size_inc = self.mysql_helper.get_database_information(
                self.subclient.content)

            # Running In Place Data + Log Restore
            self.log.info("Running In Place Restore - Data + Log")
            self.restore_and_validation(database_info=db_size_inc)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
