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

    check_prerequisite()        --  Checks if snapshot is enabled at subclient level

    populate_data_and_backup()  --  populates test data and runs backup

    check_and_run_backup_copy() --  Method to check if backup copy job needs to be
    triggered manually

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "61950":
                        {
                          "ClientName":"pgtestunix",
                          "InstanceName":"gk_snap1",
                          "DestinationClientName": "destination",
                          "DestinationInstanceName": "instance2"
                        }
            }

"""

import time
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
    """ Class for executing PostgreSQL SNAP ACC1 from command center out of place restore """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "PostgreSQL SNAP ACC1 from command center out of place restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None}
        self.postgres_helper_object = None
        self.postgres_database_object = None
        self.instance = None
        self.postgres_db_password = None
        self.database_instances = None
        self.db_instance_details = None
        self.destination_postgres_helper_object = None
        self.destination_postgres_db_object = None
        self.destination_postgres_db_password = None
        self.destination_client = None
        self.destination_instance = None
        self.snap_engine = None
        self.subclient = None
        self.storage_policy = None
        self.primary_copy = None

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
        self.instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['InstanceName'])
        self.subclient = self.instance.backupsets.get('fsbasedbackupset').subclients.get('default')
        self.storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
        self.primary_copy = self.storage_policy.get_primary_copy().copy_name
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object._postgres_db_password
        self.postgres_database_object = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")
        self.destination_client = self.commcell.clients.get(self.tcinputs['DestinationClientName'])
        self.destination_instance = self.destination_client.agents.get(
            'postgresql').instances.get(self.tcinputs['DestinationInstanceName'])
        self.destination_postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.destination_client, self.destination_instance)
        self.destination_postgres_db_password = self.destination_postgres_helper_object.postgres_password
        self.destination_postgres_db_object = database_helper.PostgreSQL(
            self.destination_client.client_hostname,
            self.destination_instance.postgres_server_port_number,
            self.destination_instance.postgres_server_user_name,
            self.destination_postgres_db_password,
            "postgres")

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created databases")
        if self.postgres_helper_object:
            self.postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                "auto")
        if self.destination_postgres_helper_object:
            self.destination_postgres_helper_object.cleanup_tc_db(
                self.destination_client.client_hostname,
                self.destination_instance.postgres_server_port_number,
                self.destination_instance.postgres_server_user_name,
                self.destination_postgres_db_password,
                "auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
            Args:
                jobid   (int): Jobid

            Raises:
                CVTestStepFailure:
                    if job fails to run
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def get_metadata(self, database_list=None, destination_server=False):
        """ method to collect database information

            Args:
                database_list   (list)  --  List of databases to get the metadata
                    default: None

                destination_server  (bool)  --  Boolean value to check if metadata of
                destination postgres server needs to be fetched
                    default: None

            Returns:
                dict        --      meta data info of database

            Raises:
                CVTestStepFailure:
                    if unable to get the database list

        """
        if destination_server:
            helper_object = self.destination_postgres_helper_object
            database_object = self.destination_postgres_db_object
            client_name = self.destination_client.client_hostname
            port = self.destination_instance.postgres_server_port_number
            username = self.destination_instance.postgres_server_user_name
            password = self.destination_postgres_db_password
        else:
            helper_object = self.postgres_helper_object
            database_object = self.postgres_database_object
            client_name = self.client.client_hostname
            port = self.instance.postgres_server_port_number
            username = self.instance.postgres_server_user_name
            password = self.postgres_db_password

        if not database_list:
            database_list = database_object.get_db_list()
            if database_list is None:
                raise CVTestStepFailure(
                    "Unable to get the database list."
                )
        self.log.info(
            "Collect information of the server contents")
        for database in ["postgres", "template0", "template1"]:
            if database in database_list:
                database_list.remove(database)
        return helper_object.generate_db_info(
            database_list, client_name,
            port, username, password)

    @test_step
    def run_restore_validate(
            self, backupset_page, before_full_backup_db_list, copy_name=None, dbhelper_object=None):
        """ method to run restore and validate test data

        Args:

            backupset_page              (obj)   --  backupset page object

            before_full_backup_db_list  (dict)  --  postgreSQL metadata collected before restore

            copy_name                   (str)   --  Copy name

                default: None

            dbhelper_object             (str)   --  dbhelper object

                default: None

        """
        self.destination_postgres_helper_object.cleanup_database_directories(
            self.destination_instance.postgres_archive_log_directory)
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.log.info("####  Running FSBasedBackupSet Restore from %s copy ####", copy_name)
        backupset_page.access_restore()
        restore_panel = backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES, all_files=True, copy=copy_name, skip_selection=True)
        job_id = restore_panel.out_of_place_restore(
            self.tcinputs['DestinationClientName'], self.tcinputs['DestinationInstanceName'],
            fsbased_restore=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")
        self.destination_postgres_helper_object.refresh()
        self.destination_postgres_db_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        after_restore_db_info = self.get_metadata(destination_server=True)
        self.log.info("Validating the database information collected before \
            Incremental Backup and after volume level Restore")
        if not self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list, after_restore_db_info):
            raise CVTestStepFailure(
                "Database information validation failed.!!!"
            )
        self.log.info(
            "###Database information validation passed successfully..!!###")
        if not copy_name:
            self.log.info("Checking if snap restore run from snap copy or not")
            if not dbhelper_object.check_if_restore_from_snap_copy(
                    self.commcell.job_controller.get(job_id), self.destination_client):
                raise CVTestStepFailure(
                    "Data is not restored from snap copy."
                )

    @test_step
    def check_prerequisite(self):
        """Checks if snapshot is enabled at subclient level"""
        machine_object = machine.Machine(
            self.commcell.clients.get(self.tcinputs['ClientName']))
        dbhelper_object = DbHelper(self.commcell)
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        backupset_page = PostgreSQLBackupset(self.admin_console)
        backupset_page.access_subclient('default')
        subclient_page = PostgreSQLSubclient(self.admin_console)
        self.log.info("Checking if snapshot feature enabled for subclient")
        if not subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        self.snap_engine = subclient_page.get_snap_engine()
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
        """ populates test data and runs backup

        Args:

            subclient_page              (obj)   --  subclient page object

            dbhelper_object             (obj)   --  dbhelper object

                default: None

            backup_type                 (str)  --  Type of backup to run

                default: "INCR"

                Accepted Values: "FULL"/"INCR"

        Returns:
            Backup job ID

        """
        time_stamp = int(time.time())
        db_prefix = f"auto_{time_stamp}"
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            2,
            10,
            100,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_database_object,
            True,
            db_prefix)
        backup_level = RBackup.BackupType.INCR
        if backup_type == "FULL":
            backup_level = RBackup.BackupType.FULL
        self.log.info("Starting FSBASED backup")
        job_id = subclient_page.backup(backup_type=backup_level)
        self.wait_for_job_completion(job_id)
        self.log.info("FSBASED FULL backup is completed")
        if backup_type == "FULL":
            log_job = dbhelper_object.get_snap_log_backup_job(job_id)
            self.log.info("Log backup job with ID:%s is now completed", log_job)
        return job_id

    @test_step
    def check_and_run_backup_copy(self, full_backup=None):
        """Method to check if backup copy job needs to be triggered manually
            Args:
                full_backup (obj)   --  Full backup job object
        """
        dbhelper_object = DbHelper(self.commcell)
        if "native" not in self.snap_engine:
            self.log.info("Snap engine is not native.")
            self.log.info(
                "Running backup copy job for storage policy/Plan: %s",
                self.subclient.storage_policy)
            dbhelper_object.run_backup_copy(self.subclient.storage_policy)
        else:
            self.log.info(
                (
                    "Native Snap engine is being run. backup "
                    "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            job = dbhelper_object.get_backup_copy_job(full_backup.job_id)
            self.log.info("Job ID of backup copy Job is: %s", job.job_id)

    def run(self):
        """ Main function for test case execution """
        try:
            dbhelper_object, backupset_page, subclient_page = self.check_prerequisite()
            full_job = self.populate_data_and_backup(subclient_page, dbhelper_object, backup_type="FULL")
            self.populate_data_and_backup(subclient_page, dbhelper_object)
            before_full_backup_db_list = self.get_metadata()
            if "native" not in self.snap_engine:
                self.run_restore_validate(
                    backupset_page, before_full_backup_db_list, dbhelper_object=dbhelper_object)
            self.check_and_run_backup_copy(full_job)
            self.run_restore_validate(
                backupset_page, before_full_backup_db_list, self.primary_copy)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
