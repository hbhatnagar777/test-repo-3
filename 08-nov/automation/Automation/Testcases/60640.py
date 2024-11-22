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
    wait_for_job_completion()   --  Waits for completion of job
    run_restore_validate()      --  method to run restore and validate test data
    run()                       --  run function of this test case

Input Example:
    "testCases": {
				"60640": {
					"ClientName": "pgkuber3",
					"AgentName": "POSTGRESQL",
					"InstanceName": "pgkuber3_5434",
					"BackupsetName": "fsbasedbackupset",
					"SubclientName": "default",
                    "ProxyClient": "mpgstandby"
				}
			}
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails

class TestCase(CVTestCase):
    """Class to execute proxy and revert restore for PostgreSQL block level from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Backup and restore using proxy and revert restore for block level " \
                    "postgres subclient using command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'ProxyClient': None}
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
        self.navigator.navigate_to_db_instances()
        DBInstances(self.admin_console).select_instance(DBInstances.Types.POSTGRES,
                                                        self.tcinputs['InstanceName'],
                                                        self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.database_instances = DBInstances(self.admin_console)
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
            "auto_60640")

    def tear_down(self):
        """ tear down method for test case """
        self.log.info("Removing proxy for subclient")
        self.subclient.unset_proxy_for_snap()
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
    def run_restore_validate(self, backup_metadata, restore_type="revert"):
        """ method to run restore, validate test data and verify restore options
        Args:
            backup_metadata (dict)  -- metadata collected before restore
            restore_type    (str)   -- type of restore performed
                Accepted values = 'revert','snap_copy',backup_copy'. Default = 'revert'
        Raises:
            CVTestStepFailure exception: if restore options check in commvault logs fail
        """
        self.postgres_helper_object.cleanup_database_directories()
        self.admin_console.select_breadcrumb_link_using_text('FSBasedBackupSet')
        backupset_page = PostgreSQLBackupset(self.admin_console)
        backupset_page.access_restore()
        copy = None
        proxy_client = None
        revert = False
        if restore_type == 'backup_copy':
            copy = 'Primary'
            search_term = "Opening archive"
            sp_copies = self.commcell.storage_policies.get(self.subclient.storage_policy).copies
            copy_precedence_primary = sp_copies["primary"]["copyPrecedence"]
            text = "copyPrecdence = " + str(copy_precedence_primary)
        elif restore_type == 'snap_copy':
            proxy_client = search_term = text = self.tcinputs['ProxyClient']
        else:
            revert = True
            search_term = "revertVolumeSnaps"
            text = "Request for revertVolumeSnaps Succeeded"
        restore_panel = backupset_page.restore_folders(
            database_type=DBInstances.Types.POSTGRES, all_files=True, copy=copy,
            skip_selection=True)
        job_id = restore_panel.in_place_restore(
            fsbased_restore=True, revert=revert, proxy_client=proxy_client)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed fine")
        self.postgres_helper_object.refresh()
        self.postgres_db_object.reconnect()
        self.log.info("Collecting database metadata after restore and validating it")
        restore_metadata = self.postgres_helper_object.get_metadata()
        self.postgres_helper_object.validate_db_info(backup_metadata, restore_metadata)
        self.log.info("Verify restore options from clRestore.log")
        machine_obj = machine.Machine(self.client)
        output = machine_obj.get_logs_for_job_from_file(job_id, "clRestore.log", search_term)
        if text not in output:
            raise CVTestStepFailure("Verifying restore option from clRestore.log failed."
                                    "Output is {}".format(output))

    def run(self):
        """ Main function for test case execution """
        try:
            subclient_page = PostgreSQLSubclient(self.admin_console)
            if not subclient_page.is_snapshot_enabled():
                raise CVTestStepFailure("snapshot is not enabled at subclient level")
            snap_engine = subclient_page.get_snap_engine()
            if snap_engine == "native":
                raise CVTestStepFailure("Engine type is native, TC requires hardware engine setup")       
            subclient_page.disable_blocklevel_backup()
            if not subclient_page.is_blocklevel_backup_enabled():
                subclient_page.disable_snapshot()
                self.admin_console.refresh_page()
                subclient_page.enable_snapshot(snap_engine, proxy_node=self.tcinputs['ProxyClient'])
                subclient_page.enable_blocklevel_backup()
            self.log.info("Run FS based full snap backup.")
            backup_jobid = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            self.wait_for_job_completion(backup_jobid)
            dbhelper_object = DbHelper(self.commcell)
            log_jobid = dbhelper_object.get_snap_log_backup_job(backup_jobid)
            self.log.info("Log backup job with ID:%s is now completed", log_jobid)
            backup_metadata = self.postgres_helper_object.get_metadata()
            self.log.info("Run revert restore 1 before backup copy")
            self.run_restore_validate(backup_metadata)
            self.log.info("Run restore from snap copy using proxy")
            self.run_restore_validate(backup_metadata, restore_type="snap_copy")
            self.log.info("Run backup copy for the full job")
            dbhelper_object.run_backup_copy(self.subclient.storage_policy)
            backup_copy_job_obj = dbhelper_object.get_backup_copy_job(backup_jobid)
            if not dbhelper_object.check_if_backup_copy_run_on_proxy(
                    backup_copy_job_obj.job_id,
                    self.commcell.clients.get(self.tcinputs['ProxyClient'])):
                raise CVTestStepFailure("Proxy client was not used for backup copy")
            self.log.info("Run revert restore 2 after backup copy")
            self.run_restore_validate(backup_metadata)
            self.log.info("Run restore from backup copy")
            self.run_restore_validate(backup_metadata, restore_type="backup_copy")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
