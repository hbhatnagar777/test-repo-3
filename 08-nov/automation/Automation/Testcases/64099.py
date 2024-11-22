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

    wait_for_job_completion()   --  waits for completion of job and gets the
    object once job completes

    get_metadata()              --  method to collect database information

    navigate_to_backupset()     --  navigates to FSBasedBackupSet page of the instance

    check_prerequisite()        --  checks if snapshot is enabled at subclient level

    set_data_streams()          --  method to set number of data streams

    validate_data()             --  validates the data in source and destination

    validate_log()              --  validates the backup and restore in the log files

    run_backup_and_restore()    --  method to run backup and restore

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "64099":
                        {
                          "ClientName":"pgtest_snap",
                          "InstanceName":"pg_snap"
                        }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper, machine
from AutomationUtils.machine import Machine
from Web.AdminConsole.Components.panel import RPanelInfo
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
import random


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for PostgreSQL Multi Stream Snap Backup and Restore"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.machine_object = None
        self.name = "Multi Stream snap backup and restore"
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
        self.backupset_page = None
        self.subclient_page = None
        self.panel = None

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
        self.panel = RPanelInfo(self.admin_console)
        self.machine_object = Machine(self.client, self.commcell)
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
            'user_name': self.postgres_server_user_name,
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
        self.backupset_page = PostgreSQLBackupset(self.admin_console)
        self.subclient_page = PostgreSQLSubclient(self.admin_console)
        self.noOfDataStreamsforBackup = random.randint(2, 6)
        self.noOfDataStreamsforRestore = random.randint(2, 6)

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
    def navigate_to_backupset(self):
        """ navigates to FSBasedBackupSet page of the instance """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('FSBasedBackupSet')

    @test_step
    def check_prerequisite(self):
        """Checks if snapshot is enabled at subclient level"""
        machine_object = machine.Machine(
            self.commcell.clients.get(self.tcinputs['ClientName']))
        dbhelper_object = DbHelper(self.commcell)
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.backupset_page.access_subclient(subclient_name='default')
        self.log.info("Checking if snapshot and blocklevel are enabled for subclient")
        if not self.subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        if "unix" in machine_object.os_info.lower():
            if self.subclient_page.is_blocklevel_backup_enabled():
                self.log.info("Disabling block level option as it is enabled")
                snap_engine = self.subclient_page.get_snap_engine()
                self.subclient_page.disable_blocklevel_backup()
                self.admin_console.refresh_page()
                if not self.subclient_page.is_snapshot_enabled():
                    self.subclient_page.enable_snapshot(snap_engine)
        return dbhelper_object, self.backupset_page, self.subclient_page

    @test_step
    def set_data_streams(self, noOfDataStreams):
        """ Method to set number of data streams

        Arg:
            noOfStream (str)  -- number of data streams for backup

        """
        self.backupset_page.access_subclient(subclient_name='default')
        self.panel.edit_tile()
        self.panel.fill_input(label="Number of data streams", text=noOfDataStreams)
        self.panel.click_button("Submit")

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
        self.log.info("Validating the database information collected before and after Restore")
        if not self.postgres_helper_object.validate_db_info(
                db_info_source, db_info_destination):
            raise Exception(
                "Database information validation failed.!!!"
            )
        else:
            self.log.info(
                "###Database information validation passed successfully..!!###")

    @test_step
    def validate_log(self, is_backup_job=True, jobid=None, restore_jobid=None):
        """
        Validates the backup and restore in the log files : clBackupParent.log, clBackup.log,PostgresRestoreCrdr.log

        Args:

            is_backup_job   (bool)    --  if False does the restore validation

            jobid           (str)     -- Backup copy jobID

            restore_jobid   (int)     -- Restore jobID

         Raises:
                Exception:

                   If validation of the job failed

        """
        if is_backup_job:
            search_term = rf".*getDataBackupStreams = {self.noOfDataStreamsforBackup}"
            if "UNIX" in self.machine_object.os_info:
                output = self.machine_object.get_logs_for_job_from_file(jobid, "clBackupParent.log", search_term)
            else:
                output = self.machine_object.get_logs_for_job_from_file(jobid, "clBackup.log", search_term)
            if output is None:
                raise Exception(f"Validation of Backup job for job ID {jobid} by comparing the log files failed !!")
            else:
                self.log.info(f"## Backup validation for job ID {jobid} completed successfully ##")

        else:
            if "UNIX" in self.machine_object.os_info:
                search_term = f"Number of workers.*[2-6].*number of workers.*{self.noOfDataStreamsforRestore}"
            else:
                search_term = rf"Number of workers.*[2-6].*number of workers.*{self.noOfDataStreamsforRestore}"
            output = self.machine_object.get_logs_for_job_from_file(restore_jobid, "PostgresRestoreCrdr.log", search_term)
            if output is None:
                raise Exception(f"Validation of Restore job for job ID {restore_jobid}"
                                f" by comparing the log files failed !!")
            else:
                self.log.info(f"## Restore validation for job ID {restore_jobid} completed successfully ##")

    @test_step
    def run_backup_and_restore(self, subclient_page, dbhelper_object):
        """ Method to run backup and restore """
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            2,
            10,
            100,
            self.port,
            self.postgres_server_user_name,
            self.postgres_database_object,
            True,
            "auto_full")
        job_id = None
        log_job = None
        self.log.info("Running FSBASED Full Backup.")
        job_id = subclient_page.backup(backup_type=RBackup.BackupType.FULL, immediate_backup_copy=True)

        self.wait_for_job_completion(job_id)
        self.log.info("FSBASED FULL backup is completed")
        log_job = dbhelper_object.get_snap_log_backup_job(job_id)
        self.log.info("Log backup job with ID:%s is now completed", log_job)
        backupcopy_job_obj = dbhelper_object.get_backup_copy_job(job_id)
        backupcopy_jobid = backupcopy_job_obj.job_id
        self.log.info("backup copy job with ID:%s is now completed", backupcopy_jobid)

        before_full_backup_db_list = self.get_metadata()

        self.log.info("Deleting data and wal directory before restore")
        self.postgres_helper_object.cleanup_database_directories(self.archive_log_dir)

        self.log.info(
            "#" * (10) + "  Running FSBasedBackupSet Restore  " + "#" * (10))
        self.navigate_to_backupset()
        self.backupset_page.access_restore()
        restore_panel = self.backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES,
            all_files=True,
            skip_selection=True)
        restore_jobid = restore_panel.in_place_restore(fsbased_restore=True,
                                                       numberofstreams=self.noOfDataStreamsforRestore)
        self.wait_for_job_completion(restore_jobid)
        self.log.info("Restore completed")
        self.postgres_helper_object.refresh()
        self.postgres_database_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        after_restore_db_info = self.get_metadata()

        self.validate_data(before_full_backup_db_list, after_restore_db_info)
        self.validate_log(jobid=backupcopy_jobid)
        self.validate_log(is_backup_job=False, restore_jobid=restore_jobid)

    def run(self):
        """ Main function for test case execution """
        try:
            dbhelper_object, backupset_page, subclient_page = self.check_prerequisite()
            self.navigate_to_backupset()
            self.set_data_streams(noOfDataStreams=self.noOfDataStreamsforBackup)
            self.run_backup_and_restore(subclient_page, dbhelper_object)
            self.navigate_to_backupset()
            self.set_data_streams(noOfDataStreams=1)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)