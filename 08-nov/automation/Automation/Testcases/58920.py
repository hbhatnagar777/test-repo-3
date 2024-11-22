# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    cleanup_database()          --  method to cleanup databases

    wait_for_job_completion()   --  Waits for completion of job and gets the
    object once job completes

    get_metadata()              --  method to collect database information

    validate_data()             --  validates the data in source and destination

    navigate_to_backupset()     --  navigates to specified backupset page of the instance

    run_restore_validate()      --  method to run restore and validate test data

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "58920":
                        {
                          "ClientName":"CLIENT_NAME",
                          "InstanceName":"INSTANCE_NAME"
                        }
            }

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """ Class for executing PIT restore TestCase for postgreSQL """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "PostgreSQL PIT restore from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None}
        self.postgres_helper_object = None
        self.postgres_database_object = None
        self.port = None
        self.postgres_server_user_name = None
        self.archive_log_dir = None
        self.postgres_db_password = None
        self.database_instances = None
        self.db_instance_details = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("***** Initialize browser objects *****")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.database_instances = DBInstances(self.admin_console)
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.port = self.db_instance_details.port
        self.postgres_server_user_name = self.db_instance_details.user
        self.archive_log_dir = self.db_instance_details.archive_log_directory
        connection_info = {
            'client_name': self.tcinputs['ClientName'],
            'instance_name': self.tcinputs['InstanceName'],
            'port': self.port,
            'hostname': self.client.client_hostname,
            'user_name':self.postgres_server_user_name,
            'password': None}
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, connection_info=connection_info)
        self.postgres_db_password = self.postgres_helper_object._postgres_db_password
        self.postgres_database_object = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.port,
            self.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created databases")
        if self.postgres_helper_object:
            self.cleanup_database("auto")

    @test_step
    def cleanup_database(self, db_prefix):
        """method to cleanup databases

        Args:
            db_prefix   (str)   -- Prefix of the databases to be cleaned

        """
        self.log.info("Deleting Databases with prefix:%s", db_prefix)
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.port,
            self.postgres_server_user_name,
            self.postgres_db_password,
            db_prefix)
        self.log.info("Databases deleted")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

        Returns:

            end_time    (str) -- Job end time

        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)
        end_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['lastUpdateTime']))
        return end_time

    @test_step
    def get_metadata(self):
        """ method to collect database information

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        database_list = self.postgres_database_object.get_db_list()
        if database_list is None:
            raise Exception(
                "Unable to get the database list."
            )
        self.log.info(
            "Collect information of the subclient content")
        for database in ["postgres", "template0", "template1"]:
            if database in database_list:
                database_list.remove(database)
        return self.postgres_helper_object.generate_db_info(
            database_list,
            self.client.client_hostname,
            self.port,
            self.postgres_server_user_name,
            self.postgres_db_password)

    @test_step
    def validate_data(self, db_info_source, db_info_destination):
        """validates the data in source and destination

            Args:
                db_info_source        (dict)  --  database information of source

                db_info_destination   (dict)  --  database information of destination

            Raises:
                Exception:

                    if database information validation failed

        """

        self.log.info("Validating the database information collected before \
            Incremental Backup and after Restore")
        if not self.postgres_helper_object.validate_db_info(
                db_info_source, db_info_destination):
            raise Exception(
                "Database information validation failed.!!!"
            )
        self.log.info(
            "###Database information validation passed successfully..!!###")

    @test_step
    def navigate_to_backupset(self, backupset_name="DumpBasedBackupSet"):
        """ navigates to specified backupset page of the instance

        Args:
            backupset_name  (str)   --  backupset name

                default = "DumpBasedBackupSet"

                Accepted values = DumpBasedBackupSet/FSBasedBackupSet

        """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity(backupset_name)

    @test_step
    def run_restore_validate(
            self, backupset_page, before_full_backup_db_list,
            to_time, backupset_name="DumpBasedBackupSet", database_list=None):
        """ method to run restore and validate test data

        Args:

            backupset_page              (obj)   --  backupset page object

            before_full_backup_db_list  (dict)  -- postgreSQL metadata collected before restore

            to_time                     (str)   -- Browse backups untill this time

            backupset_name              (str)   --  backupset name

                default = "DumpBasedBackupSet"

                Accepted values = DumpBasedBackupSet/FSBasedBackupSet

            database_list               (list)  --  list of databases to restore in
            dumpbased restore

                default: None

        """
        to_time = time.strftime('%d-%B-%Y-%H-%M',
                                time.localtime(time.mktime(time.strptime(to_time,
                                                                         '%d-%B-%Y-%I-%M-%p'))+60))
        self.navigate_to_backupset(backupset_name)
        self.log.info(
            "#####  Running %s Restore  #####", backupset_name)
        backupset_page.access_restore()
        restore_panel = None
        is_fsbased_restore = False
        if 'Dump' in backupset_name:
            restore_panel = backupset_page.restore_folders(
                database_type=DBInstances.Types.POSTGRES,
                items_to_restore=database_list, to_time=to_time)
        else:
            restore_panel = backupset_page.restore_folders(
                database_type=DBInstances.Types.POSTGRES,
                all_files=True, to_time=to_time, skip_selection=True)
            is_fsbased_restore = True
        job_id = restore_panel.in_place_restore(fsbased_restore=is_fsbased_restore)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")
        self.postgres_helper_object.refresh()
        self.postgres_database_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        after_restore_db_info = self.get_metadata()
        self.validate_data(before_full_backup_db_list, after_restore_db_info)

    @test_step
    def run_backup(
            self, subclient_page,
            backupset_name="DumpBasedBackupSet", backup_type=RBackup.BackupType.INCR):
        """ method to run backups and wait for its completion

        Args:

            subclient_page              (obj)               -- subclient page object

            backupset_name              (str)               -- backupset name

                default = "DumpBasedBackupSet"

                Accepted values = DumpBasedBackupSet/FSBasedBackupSet

            backup_type                 (Backup.BackupType) -- backup type

        Returns:

            end_time    (str) -- Job end time

        """
        self.log.info("Running %s Backup", backupset_name)
        job_id = subclient_page.backup(backup_type=backup_type)
        end_time = self.wait_for_job_completion(job_id)
        self.log.info("%s backup is completed", backupset_name)
        return end_time



    def run(self):
        """ Main function for test case execution """
        try:

            ################# Backup/Restore Operations ########################
            self.log.info(
                "##### Backup/PIT Restore Operations #####")
            self.log.info("Generating Test Data")
            database_list_to_restore = self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                2,
                10,
                100,
                self.port,
                self.postgres_server_user_name,
                self.postgres_database_object,
                True,
                "auto_full")
            self.log.info("Test Data Generated successfully")

            self.db_instance_details.click_on_entity('DumpBasedBackupSet')
            backupset_page = PostgreSQLBackupset(self.admin_console)
            backupset_page.access_subclient('default')
            subclient_page = PostgreSQLSubclient(self.admin_console)
            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.get_metadata()
            end_time = self.run_backup(
                subclient_page, backup_type=RBackup.BackupType.FULL)
            self.cleanup_database("auto_full_testdb_0")
            self.log.info("sleeping for 70 seconds before 2nd backup")
            time.sleep(70)
            self.run_backup(subclient_page, backup_type=RBackup.BackupType.FULL)
            self.log.info("Deleting test created databases before restore")
            self.cleanup_database("auto_full")
            self.run_restore_validate(
                backupset_page, before_full_backup_db_list, end_time,
                backupset_name="DumpBasedBackupSet", database_list=database_list_to_restore)

            ################# FSBASED Backup/Restore Operations ########################
            self.log.info(
                "##### Running FSBased Full Backup #####")
            self.navigate_to_backupset('FSBasedBackupSet')
            backupset_page.access_subclient('default')

            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.get_metadata()
            end_time = self.run_backup(
                subclient_page, "FSBasedBackupSet", backup_type=RBackup.BackupType.FULL)
            self.log.info("Adding test data before running incremental backup")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                2,
                10,
                100,
                self.port,
                self.postgres_server_user_name,
                self.postgres_database_object,
                True,
                "auto_incr")
            self.log.info("Test Data Generated successfully")
            self.log.info("Get the database meta data before incremental backup")
            before_inc_backup_db_list = self.get_metadata()
            self.log.info("sleeping for 70 seconds before incremental backup")
            time.sleep(70)
            inc_end_time = self.run_backup(subclient_page, "FSBasedBackupSet")
            self.log.info("genrating few more DBs before 2nd full, after 70 seconds")
            time.sleep(70)
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                2,
                10,
                100,
                self.port,
                self.postgres_server_user_name,
                self.postgres_database_object,
                True,
                "auto_full_2")
            self.log.info("sleeping for 70 seconds before 2nd Full backup")
            time.sleep(70)
            self.run_backup(
                subclient_page, "FSBasedBackupSet", backup_type=RBackup.BackupType.FULL)
            self.log.info("Deleting data and wal directory before restore")
            self.postgres_helper_object.cleanup_database_directories(self.archive_log_dir)
            self.log.info("Restore from 1st full")
            self.run_restore_validate(
                backupset_page, before_full_backup_db_list,
                end_time, backupset_name="FSBasedBackupSet")
            self.log.info("Deleting data and wal directory before restore")
            self.postgres_helper_object.cleanup_database_directories(self.archive_log_dir)
            self.log.info("Restore from incremental after 1st full")
            self.run_restore_validate(
                backupset_page, before_inc_backup_db_list,
                inc_end_time, backupset_name="FSBasedBackupSet")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
