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
    tear_down()                 --  tear down method for test case
    run_backup()                --  Run backup and backup copy
    wait_for_job_completion()   --  Waits for completion of job
    run_restore_validate()      --  method to run restore and validate metadata of test data
    run()                       --  run function of this test case

Input Example:
    "testCases": {
				"60646": {
					"ClientName": "client_name",
					"AgentName": "POSTGRESQL",
					"InstanceName": "instance_name",
					"BackupsetName": "fsbasedbackupset",
					"SubclientName": "default"
				}
			}

"""
from AutomationUtils.cvtestcase import CVTestCase
from Database import dbhelper
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

class TestCase(CVTestCase):
    """Class to execute restore from aux copy using command center for postgresql snap backup"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Restore from aux copy using command center for postgresql snap backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.postgres_helper_object = None
        self.postgres_db_object = None
        self.postgres_db_password = None
        self.database_instances = None
        self.db_instance_details = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.database_instances = DBInstances(self.admin_console)
        self.navigator.navigate_to_db_instances()
        DBInstances(self.admin_console).select_instance(DBInstances.Types.POSTGRES,
                                                        self.instance.instance_name,
                                                        self.client.client_name)
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.postgres_db_object = self.postgres_helper_object._get_postgres_database_connection(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            2,
            10,
            100,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_object,
            True,
            "auto_60646")

    def tear_down(self):
        """ tear down method for test case """
        self.log.info("Deleting Automation Created databases")
        if self.postgres_helper_object:
            self.postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_password,
                "auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job
        Args:
            jobid (int): Job id of the operation
        Raises:
            CVTestStepFailure exception:
                If job finishes with status other than completed
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_backupset(self):
        """ navigates to FSBasedBackupSet backupset page of the instance """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('FSBasedBackupSet')

    @test_step
    def run_restore_validate(self):
        """ Method to run restore from aux copy and validate metadata
        Returns:
            job_id (int) -- Job id of restore operation
        """
        backup_metadata = self.postgres_helper_object.get_metadata()
        self.admin_console.select_breadcrumb_link_using_text('FSBasedBackupSet')
        backupset_page = PostgreSQLBackupset(self.admin_console)
        backupset_page.access_restore()
        self.log.info("Running fsbased restore")
        self.postgres_helper_object.cleanup_database_directories()
        restore_panel = backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES, all_files=True,
            copy="automation_copy", skip_selection=True)
        job_id = restore_panel.in_place_restore(fsbased_restore=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore job %d completed", job_id)
        self.postgres_helper_object.refresh()
        self.postgres_db_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        restore_metadata = self.postgres_helper_object.get_metadata()
        self.postgres_helper_object.validate_db_info(backup_metadata, restore_metadata)
        return job_id

    @test_step
    def run_backup(self):
        """ Run snap backup and backup copy jobs
        Returns:
            snap_jobid         (int) - Job id of the snap backup
            log_job_obj.job_id (int) - job id of the log backup
        Raises:
            CVTestStepFailure exception:
                If copy precedence value in clRestore.log differs from expected
        """
        subclient_page = PostgreSQLSubclient(self.admin_console)
        if not subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        snap_engine = subclient_page.get_snap_engine()
        if "unix" in self.client.os_info.lower():
            if subclient_page.is_blocklevel_backup_enabled():
                self.log.info("Disabling block level option as it is enabled")
                subclient_page.disable_blocklevel_backup()
                subclient_page.disable_snapshot()
                self.admin_console.refresh_page()
                subclient_page.enable_snapshot(snap_engine)
        snap_jobid = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(snap_jobid)
        dbhelper_object = dbhelper.DbHelper(self.commcell)
        log_job_obj = dbhelper_object.get_snap_log_backup_job(snap_jobid)
        self.log.info("Log backup job with ID:%s is now completed", log_job_obj.job_id)
        if snap_engine.lower() == "native":
            self.log.info("Snap engine is native, check backup copy status")
            dbhelper_object.get_backup_copy_job(str(snap_jobid))
        else:
            self.log.info("Snap engine is not native, run backup copy")
            dbhelper_object.run_backup_copy(self.subclient.storage_policy)            
        return snap_jobid, log_job_obj.job_id

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_backupset()
            backupset_page = PostgreSQLBackupset(self.admin_console)
            backupset_page.access_subclient(subclient_name='default')
            auxcopy_cp = self.postgres_helper_object.prepare_aux_copy(
                self.subclient.storage_policy)
            snap_jobid, log_jobid = self.run_backup()
            self.postgres_helper_object.run_aux_copy(self.subclient.storage_policy)
            restore_jobid = self.run_restore_validate()
            self.log.info("Verifying copy used for data restore")
            data_afile_id = self.postgres_helper_object.get_afileid(
                job_id=snap_jobid, flags=4)
            self.postgres_helper_object.confirm_logging(
                restore_jobid, "clRestore.log", data_afile_id[0], f"= {auxcopy_cp}")
            self.log.info("Verifying copy used for log restore")
            log_afile_id = self.postgres_helper_object.get_afileid(log_jobid, "4")
            self.postgres_helper_object.confirm_logging(
                restore_jobid, "clRestore.log", log_afile_id[0], f"= {auxcopy_cp}")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
