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

    run_restore_validate()      --  method to run restore and validate test data

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "56509":
                        {
                          "ClientName":"pgtestunix",
                          "InstanceName":"gk_snap1"
                        }
            }

"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper, machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for PostgreSQL SNAP """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "PostgreSQL SNAP ACC1 from command center"
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
            raise CVTestStepFailure(
                "Unable to get the database list."
            )
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
    def run_restore_validate(
            self, backupset_page, before_full_backup_db_list):
        """ method to run restore and validate test data

        Args:

            backupset_page              (obj)   --  backupset page object

            before_full_backup_db_list  (dict)  -- postgreSQL metadata collected before restore

                default: None

        """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.log.info(
            "#" * (10) + "  Running FSBasedBackupSet Restore  " + "#" * (10))
        backupset_page.access_restore()
        restore_panel = None
        restore_panel = backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES,
            all_files=True,
            skip_selection=True)
        job_id = restore_panel.in_place_restore(fsbased_restore=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")
        self.postgres_helper_object.refresh()
        self.postgres_database_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        after_restore_db_info = self.get_metadata()
        self.log.info("Validating the database information collected before \
            Incremental Backup and after volume level Restore")
        if not self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list, after_restore_db_info):
            raise CVTestStepFailure(
                "Database information validation failed.!!!"
            )
        else:
            self.log.info(
                "###Database information validation passed successfully..!!###")

    @test_step
    def check_prerequisite(self):
        """Checks if snapshot is enabled at subclient level"""
        machine_object = machine.Machine(
            self.commcell.clients.get(self.tcinputs['ClientName']))
        dbhelper_object = DbHelper(self.commcell)
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        backupset_page = PostgreSQLBackupset(self.admin_console)
        backupset_page.access_subclient(subclient_name='default')
        subclient_page = PostgreSQLSubclient(self.admin_console)

        self.log.info("Checking if snapshot and blocklevel are enabled for subclient")
        if not subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        if "unix" in machine_object.os_info.lower():
            if subclient_page.is_blocklevel_backup_enabled():
                self.log.info("Disabling block level option as it is enabled")
                snap_engine = subclient_page.get_snap_engine()
                subclient_page.disable_blocklevel_backup()
                self.admin_console.refresh_page()
                if not subclient_page.is_snapshot_enabled():
                    subclient_page.enable_snapshot(snap_engine)
        return dbhelper_object, backupset_page, subclient_page

    @test_step
    def populate_data_and_backup(self, subclient_page, dbhelper_object, backup_type="INCR"):
        """ populates test data and runs backup """
        db_prefix = "auto_full"
        if backup_type == "INCR":
            db_prefix = "auto_incr"
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            2,
            10,
            100,
            self.port,
            self.postgres_server_user_name,
            self.postgres_database_object,
            True,
            db_prefix)
        job_id = None
        log_job = None
        if backup_type == "INCR":
            self.log.info("Starting FSBASED incremental backup")
            job_id = subclient_page.backup()
            self.wait_for_job_completion(job_id)
            self.log.info("FSBASED INCREMENTAL backup is completed")
        else:
            self.log.info("Running FSBASED Full Backup.")
            job_id = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("FSBASED FULL backup is completed")
            log_job = dbhelper_object.get_snap_log_backup_job(job_id)
            self.log.info("Log backup job with ID:%s is now completed", log_job)

    def run(self):
        """ Main function for test case execution """
        try:
            dbhelper_object, backupset_page, subclient_page = self.check_prerequisite()
            self.populate_data_and_backup(subclient_page, dbhelper_object, backup_type="FULL")
            self.populate_data_and_backup(subclient_page, dbhelper_object)
            before_full_backup_db_list = self.get_metadata()
            self.postgres_helper_object.cleanup_database_directories(self.archive_log_dir)
            self.run_restore_validate(
                backupset_page, before_full_backup_db_list)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
