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
    __init__()                  --  Initialize TestCase class

    setup()                     --  Setup method for test case

    tear_down()                 --  Tear down method for testcase

    wait_for_job_completion()   --  Waits for completion of job and gets the
    object once job completes

    get_metadata()              --  Method to collect database information

    navigate_to_backupset()     --  Navigates to DumpBasedBackupSet page of the instance

    enable_parallel_job()       --  Enables parallel jobs and sets the staging path

    disable_parallel_job()      --  Disables parallel jobs

    validate_data()             --  Validates the data in source and destination

    validate_log()              --  Validates the backup and restore job by comparing the log files

    run_backup_and_restore()    -- Method to run DumpBased backup and restore

    remove_dir()                --  Removes the folder created in staging path during automation

    run()                       --  Run function of this test case


Input Example:

    "testCases":
            {
                "64079":
                        {
                          "ClientName":"pg_test_unix",
                          "InstanceName":"pgtest_5516",
                          "NumberOfParallelJob": "2",
                          "StagingPath": "/tmp"
                        }
            }


"""

from AutomationUtils import database_helper
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Web.AdminConsole.Components.dialog import RModalDialog, RBackup
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.Common.page_object import TestStep, handle_testcase_exception
import re

class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for PostgreSQL Parallel jobs to dump the database """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Parallel jobs based backup and restore from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'StagingPath': None,
            'NumberOfParallelJob': None
        }
        self.database_instances = None
        self.db_instance_details = None
        self.panel = None
        self.dialog = None
        self.postgres_helper_object = None
        self.postgres_database_object = None
        self.port = None
        self.postgres_server_user_name = None
        self.postgres_db_password = None
        self.machine_object = None

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
        self.dialog = RModalDialog(self.admin_console)
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
                dict        --      metadata info of database

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
    def navigate_to_backupset(self):
        """ navigates to DumpBasedBackupSet page of the instance """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('DumpBasedBackupSet')

    @test_step
    def enable_parallel_job(self):
        """ Enable parallel jobs and sets the staging path """
        self.panel.edit_tile()
        self.dialog.enable_toggle(toggle_element_id='useParallelJobs')
        self.dialog.fill_text_in_field('numParallelJobs', self.tcinputs['NumberOfParallelJob'])
        self.dialog.click_button_on_dialog(aria_label='Browse')
        self.dialog.browse_path(self.tcinputs['StagingPath'])
        self.dialog.select_checkbox('enableGlobalObjectsBkp')
        self.dialog.click_submit()

    @test_step
    def disable_parallel_job(self):
        """ Disable parallel jobs """
        self.navigate_to_backupset()
        self.panel.edit_tile()
        self.dialog.disable_toggle(toggle_element_id='useParallelJobs')
        self.dialog.deselect_checkbox('enableGlobalObjectsBkp')
        self.dialog.click_submit()

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
        Backup and after Restore")
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
        Validates the backup and restore by comparing the log files : PostgresBackupCtrl.log, PostgresRestoreCtrl.log

        Args:

            is_backup_job   (bool)    --  if False does the restore validation

            jobid           (int)     -- Backup jobID

            restore_jobid   (int)     -- Restore jobID

         Raises:
                Exception:

                   If validation of the job failed

        """
        subclient_id = self.client.agents.get('Postgresql').instances.get(self.tcinputs['InstanceName']).backupsets.get(
            'Dumpbasedbackupset').subclients.get('default').subclient_id
        staging_dir = self.tcinputs['StagingPath']
        NumberOfParallelJob = self.tcinputs['NumberOfParallelJob']
        if is_backup_job:
            if "UNIX" in self.machine_object.os_info:
                search_term = f"pg_dump.*-Fd -b -j {NumberOfParallelJob}.*{staging_dir}/{subclient_id}"
            else:
                re_stagingdir = re.escape(staging_dir)
                search_term = rf"pg_dump.*-Fd -b -j {NumberOfParallelJob}.*{re_stagingdir}\\{subclient_id}"
            output = self.machine_object.get_logs_for_job_from_file(
                jobid, "PostgresBackupCtrl.log", search_term)
            if output is None:
                raise Exception(f"Validation of Backup job for job ID {jobid} by comparing the log files failed !!")
            else:
                self.log.info(f"## Backup validation for job ID {jobid} completed successfully ##")

        else:
            if "UNIX" in self.machine_object.os_info:
                search_term = f"pg_restore.*-Fd -v .*-j {NumberOfParallelJob}.*{staging_dir}/{restore_jobid}"
            else:
                re_stagingdir = re.escape(staging_dir)
                search_term = rf"pg_restore.*-Fd -v .*-j {NumberOfParallelJob}.*{re_stagingdir}\\{restore_jobid}"
            output = self.machine_object.get_logs_for_job_from_file(
                restore_jobid, "PostgresRestoreCtrl.log", search_term)
            if output is None:
                raise Exception(
                    f"Validation of Restore job for job ID {restore_jobid} by comparing the log files failed !!")
            else:
                self.log.info(f"## Restore validation for job ID {restore_jobid} completed successfully ##")

    @test_step
    def run_backup_and_restore(self):
        """Method to run DumpBased Backup/Restore Operations"""
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

        self.backupset_page.access_subclient(subclient_name='default')

        self.log.info("Get the database meta data before backup")
        before_full_backup_db_list = self.get_metadata()

        self.log.info("Running DumpBased Backup.")
        jobid = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(jobid)
        self.log.info("Dumpbased backup is completed")

        self.log.info("Deleting Automation Created databases before trying restore")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.port,
            self.postgres_server_user_name,
            self.postgres_database_object,
            "auto_full")

        self.navigate_to_backupset()
        self.log.info(
            "#" * (10) + "  Running DumpBasedBackupSet Restore  " + "#" * (10))
        self.backupset_page.access_restore()
        restore_panel = self.backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=database_list_to_restore)

        restore_jobid = restore_panel.in_place_restore(staging_path=self.tcinputs['StagingPath'],
                                                       global_objects=True)
        self.wait_for_job_completion(restore_jobid)
        self.log.info("Restore completed")
        self.postgres_helper_object.refresh()
        self.postgres_database_object.reconnect()

        self.log.info("Collecting database metadata after restore")
        after_restore_db_info = self.get_metadata()

        self.validate_data(before_full_backup_db_list, after_restore_db_info)
        self.validate_log(jobid=jobid)
        self.validate_log(is_backup_job=False, restore_jobid=restore_jobid)
        return restore_jobid

    @test_step
    def remove_dir(self, jobid):
        """ Removes the folder created in staging path during automation """
        if "UNIX" in self.machine_object.os_info:
            path = f'{self.tcinputs['StagingPath']}/{jobid}'
            output = self.machine_object.remove_directory(path)
        else:
            path = f'{self.tcinputs['StagingPath']}\\{jobid}'
            output = self.machine_object.remove_directory(path)

        if output is not None:
            self.log.info(f"## {path} directory removed successfully ##")

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_backupset()
            self.enable_parallel_job()
            job_id = self.run_backup_and_restore()
            self.disable_parallel_job()
            self.remove_dir(job_id)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
