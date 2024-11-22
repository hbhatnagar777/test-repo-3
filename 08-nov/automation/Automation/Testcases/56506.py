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
                "56506":
                        {
                          "ClientName":"pgtestunix",
                          "InstanceName":"gk_snap1"
                        }
            }

"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for postgreSQL """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "PostgreSQL ACC1 from command center"
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
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
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
            self.postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.port,
                self.postgres_server_user_name,
                self.postgres_db_password,
                "auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

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
            Incremental Backup and after volume level Restore")
        if not self.postgres_helper_object.validate_db_info(
                db_info_source, db_info_destination):
            raise Exception(
                "Database information validation failed.!!!"
            )
        else:
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
            backupset_name="DumpBasedBackupSet", database_list=None):
        """ method to run restore and validate test data

        Args:

            backupset_page              (obj)   --  backupset page object

            before_full_backup_db_list  (dict)  -- postgreSQL metadata collected before restore

            backupset_name              (str)   --  backupset name

                default = "DumpBasedBackupSet"

                Accepted values = DumpBasedBackupSet/FSBasedBackupSet

            database_list               (list)  --  list of databases to restore in
            dumpbased restore

                default: None

        """
        self.navigate_to_backupset(backupset_name)
        self.log.info(
            "#" * (10) + "  Running "+backupset_name+" Restore  " + "#" * (10))
        backupset_page.access_restore()
        restore_panel = None
        is_fsbased_restore = False
        if 'Dump' in backupset_name:
            restore_panel = backupset_page.restore_folders(
                database_type=DBInstances.Types.POSTGRES, items_to_restore=database_list)
        else:
            restore_panel = backupset_page.restore_folders(
                database_type=DBInstances.Types.POSTGRES,
                all_files=True,
                skip_selection=True)
            is_fsbased_restore = True
        job_id = restore_panel.in_place_restore(fsbased_restore=is_fsbased_restore)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")
        self.postgres_helper_object.refresh()
        self.postgres_database_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        after_restore_db_info = self.get_metadata()
        self.validate_data(before_full_backup_db_list, after_restore_db_info)


    def run(self):
        """ Main function for test case execution """
        try:

            ################# DumpBased Backup/Restore Operations ########################
            self.log.info(
                "#" * (10) + "  DumpBased Backup/Restore Operations  " + "#" * (10))
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

            self.navigate_to_backupset('DumpBasedBackupSet')
            backupset_page = PostgreSQLBackupset(self.admin_console)
            backupset_page.access_subclient(subclient_name='default')
            subclient_page = PostgreSQLSubclient(self.admin_console)

            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.get_metadata()

            self.log.info("Running DumpBased Backup.")
            job_id = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("Dumpbased backup is completed")

            self.log.info("Deleting Automation Created databases before trying restore")
            self.postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.port,
                self.postgres_server_user_name,
                self.postgres_database_object,
                "auto_full")

            self.run_restore_validate(
                backupset_page, before_full_backup_db_list,
                backupset_name="DumpBasedBackupSet", database_list=database_list_to_restore)

            ################# FSBASED Backup/Restore Operations ########################
            self.log.info(
                "#" * (10) + "  Running FSBased Full Backup  " + "#" * (10))
            self.navigate_to_backupset('FSBasedBackupSet')
            backupset_page.access_subclient(subclient_name='default')

            self.log.info("Running FSBASED FULL Backup.")
            job_id = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("FSBASED FULL backup is completed")

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

            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.get_metadata()

            # Running FS Backup Log
            self.log.info(
                "#" * (10) + "  Running FSBased Incremental Backup  " + "#" * (10))
            job_id = subclient_page.backup()
            self.wait_for_job_completion(job_id)
            self.log.info("FSBASED INCREMENTAL backup is completed")

            self.log.info("Deleting data and wal directory before restore")
            self.postgres_helper_object.cleanup_database_directories(self.archive_log_dir)

            self.run_restore_validate(
                backupset_page, before_full_backup_db_list, backupset_name="FSBasedBackupSet")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
