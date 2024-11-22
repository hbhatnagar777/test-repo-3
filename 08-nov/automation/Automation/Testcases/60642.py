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
    navigate_to_backupset()     --  Navigates to details page of specified backupset
    backup_auxcopy_restore()    --  Run backup, invoke aux copy and restore functions
    wait_for_job_completion()   --  Waits for completion of job
    run_restore_validate()      --  method to run restore and validate metadata of test data
    table_level_restore()       --  Run table level restore from aux copy
    run()                       --  run function of this test case

Input Example:
    "testCases": {
				"60642": {
					"ClientName": "pgkuber3",
					"AgentName": "POSTGRESQL",
					"InstanceName": "pgkuber3_5434",
					"BackupsetName": "fsbasedbackupset",
					"SubclientName": "default"
				}
			}

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails

class TestCase(CVTestCase):
    """Class to execute restore from aux copy using command center for postgresql regular backup"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Restore from aux copy using command center for postgresql regular backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.postgres_helper_object = None
        self.postgres_db_object = None
        self.postgres_db_password = None
        self.dump_subc_obj = None
        self.db_instance_details = None
        self.database_instances = None

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
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
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
        backupset_obj = self.instance.backupsets.get('dumpbasedbackupset')
        self.dump_subc_obj = backupset_obj.subclients.get('default')

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
    def navigate_to_backupset(self, backupset_name="DumpBasedBackupSet"):
        """Opens details page for specified backupset
        Args:
            backupset_name (str) -- BackupSet name
                Accepted values  -- FSBasedBackupSet, DumpBasedBackupSet.
                                    Default is DumpBasedBackupSet"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity(backupset_name)

    @test_step
    def backup_auxcopy_restore(self, backupset_name="DumpBasedBackupSet"):
        """Run backup for default subclient of specified backupset
        It also calls aux copy and run_restore_validate functions
        Args:
            backupset_name (str) -- BackupSet to perform backup, restore operations
                Accepted values  -- FSBasedBackupSet, DumpBasedBackupSet.
                                    Default is DumpBasedBackupSet
        Returns:
            backup_jobid (int)   -- Job id of backup job
            restore_jobid (int)  -- Job id of restore job
        """
        self.log.info("Running backup for default subclient of %s", backupset_name)
        self.navigate_to_backupset(backupset_name)
        backupset_page = PostgreSQLBackupset(self.admin_console)
        backupset_page.access_subclient(subclient_name='default')
        subclient_page = PostgreSQLSubclient(self.admin_console)
        db_list = None
        if 'Dump' in backupset_name:
            db_list = self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                2,
                10,
                100,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_object,
                True,
                "auto_full")
        else:
            if subclient_page.is_snapshot_enabled():
                if "unix" in self.client.os_info.lower():
                    if subclient_page.is_blocklevel_backup_enabled():
                        self.log.info("Disabling block level option")
                        subclient_page.disable_blocklevel_backup()
                self.log.info("Disabling snap option")
                subclient_page.disable_snapshot()
                self.admin_console.refresh_page()
        backup_jobid = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(backup_jobid)
        if 'Dump' in backupset_name:
            self.postgres_helper_object.run_aux_copy(
                self.dump_subc_obj.storage_policy, fsbased=False)
        else:
            self.postgres_helper_object.run_aux_copy(self.subclient.storage_policy)
        restore_jobid = self.run_restore_validate(backupset_name, db_list)
        return backup_jobid, restore_jobid

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
    def run_restore_validate(self, backupset_name="DumpBasedBackupSet", database_list=None):
        """ method to run restore and validate metadata
        Args:
            backupset_name (str) -- backupset name. default = "DumpBasedBackupSet"
                                    Accepted values = DumpBasedBackupSet/FSBasedBackupSet
            database_list (list) -- list of databases to restore in dumpbased restore
                                    default: None
        Returns:
            job_id (int) -- Job id of restore operation
        """
        backup_metadata = self.postgres_helper_object.get_metadata()
        self.navigate_to_backupset(backupset_name)
        backupset_page = PostgreSQLBackupset(self.admin_console)
        backupset_page.access_restore()
        if 'Dump' in backupset_name:
            self.log.info("Running dumpbased restore")
            is_fsbased_restore = False
            self.postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.postgres_db_object,
                "auto_full")
        else:
            self.log.info("Running fsbased restore")
            self.postgres_helper_object.cleanup_database_directories()
            is_fsbased_restore = True
        time.sleep(30)
        restore_panel = backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES,
            items_to_restore=database_list,
            all_files=is_fsbased_restore,
            copy="automation_copy",
            skip_selection=is_fsbased_restore)
        job_id = restore_panel.in_place_restore(fsbased_restore=is_fsbased_restore)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore job %d completed", job_id)
        self.postgres_helper_object.refresh()
        self.postgres_db_object.reconnect()
        self.log.info("Collecting database metadata after restore")
        restore_metadata = self.postgres_helper_object.get_metadata()
        self.postgres_helper_object.validate_db_info(backup_metadata, restore_metadata)
        return job_id

    @test_step
    def table_level_restore(self, dump_cp):
        """ Verify table level restore from aux copy
        TODO: When command center start support for table level restore, update this
        Args:
            dump_cp (int)   -- copy precedence of aux copy named automation_copy
            for the SP associated with default subclient of dumpbased backupset
        Returns:
            job.jobid (int) -- job id of the restore job
        """
        backup_metadata = self.postgres_helper_object.get_metadata()
        self.log.info("Deleting a table from database")
        self.postgres_helper_object.drop_table(
            "testtab_1",
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto_full_testdb_0")
        self.log.info("Deleting function from database")
        self.postgres_helper_object.drop_function(
            "test_function_1", database="auto_full_testdb_0")
        self.log.info("### starting table level restore ###")
        job = self.postgres_helper_object.run_restore(
            [
                "/auto_full_testdb_0/public/testtab_1/",
                "/auto_full_testdb_0/public/test_view_1/",
                "/auto_full_testdb_0/public/test_function_1/"
            ],
            self.dump_subc_obj, table_level_restore=True,
            is_dump_based=True, copy_precedence=dump_cp)
        restore_metadata = self.postgres_helper_object.get_metadata()
        self.postgres_helper_object.validate_db_info(backup_metadata, restore_metadata)
        return job.job_id

    def run(self):
        """ Main function for test case execution """
        try:
            fs_cp = self.postgres_helper_object.prepare_aux_copy(
                self.subclient.storage_policy)
            if self.subclient.storage_policy == self.dump_subc_obj.storage_policy:
                dump_cp = fs_cp
            else:
                dump_cp = self.postgres_helper_object.prepare_aux_copy(
                    self.dump_subc_obj.storage_policy, fsbased=False)
            backup_jobid, restore_jobid = self.backup_auxcopy_restore()

            self.log.info("Verify copy used for dumpbased DB restore")
            dump_afile_id = self.postgres_helper_object.get_afileid(backup_jobid)
            self.postgres_helper_object.confirm_logging(
                restore_jobid, "PostGresRestore.log", dump_afile_id[0], f"= {dump_cp}")

            restore_jobid = self.table_level_restore(dump_cp)
            self.log.info("Verify copy used for dumpbased table restore")
            self.postgres_helper_object.confirm_logging(
                restore_jobid, "PostGresRestore.log", f"{dump_afile_id[0]}|{dump_afile_id[1]}", f"= {dump_cp}")

            backup_jobid, restore_jobid = self.backup_auxcopy_restore("FSBasedBackupSet")
            self.log.info("Verifying copy used for fsbased data restore")
            dump_afile_id = self.postgres_helper_object.get_afileid(backup_jobid)
            self.postgres_helper_object.confirm_logging(
                restore_jobid, "clRestore.log", dump_afile_id[0], f"= {fs_cp}")
            self.log.info("Verifying copy used for fsbased log restore")
            log_afile_id = self.postgres_helper_object.get_afileid(backup_jobid, "4")
            self.postgres_helper_object.confirm_logging(
                restore_jobid, "clRestore.log", f"{log_afile_id[0]}", f"= {fs_cp}")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
