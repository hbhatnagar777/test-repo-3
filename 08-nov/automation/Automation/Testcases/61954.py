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
    __init__()                 --  initialize TestCase class
    setup()                    --  setup method for test case
    tear_down()                --  tear down method for testcase
    backup()                   --  runs full and log backup
    cleanup_old_clones()       --  method to cleanup old clones for the instance
    get_clone_metadata()       --  method to get metadata from clone instance
    run_clone_validate()       --  method to run clone and validate data
    wait_for_job_completion()  --  Waits for completion of job
    navigate_to_subclient()    --  method to open details page for
                                   default database group of fsbased backupset
    run()                      --  run function of this test case

Input Example:
    "testCases": {
				"61954": {
					"ClientName": "client1",
					"AgentName": "POSTGRESQL",
					"InstanceName": "instance1",
					"BackupsetName": "fsbasedbackupset",
					"SubclientName": "default",
                    "PortForClone": 5442
				}
			}
"""
from time import sleep
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.Instances.instant_clone import InstantClone
from Web.AdminConsole.Databases.Instances.instant_clone_details import InstantCloneDetails
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup, RModalDialog
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class to execute clone restore for PostgreSQL snap from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Clone restore for PostgreSQL snap from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'PortForClone': None
        }
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.database_instances = None
        self.instant_clone = None
        self.instant_clone_details = None
        self.table = None
        self.db_instance_details = None
        self.dialog = None
        self.page_container = None

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
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.instant_clone = InstantClone(self.admin_console)
        self.instant_clone_details = InstantCloneDetails(self.admin_console)
        self.table = Table(self.admin_console)
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.backupset_page = PostgreSQLBackupset(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.page_container = PageContainer(self.admin_console)

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
    def navigate_to_subclient(self):
        """Opens details page for default database group of fsbased backupset"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(DBInstances.Types.POSTGRES,
                                                self.tcinputs['InstanceName'],
                                                self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.backupset_page.access_subclient('default')

    @test_step
    def backup(self):
        """Runs full and log backup for the snap subclient
        Raises:
            CVTestStepFailure exception:
                If snapshot is not enabled on subclient
        """
        self.navigate_to_subclient()
        subclient_page = PostgreSQLSubclient(self.admin_console)
        if not subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        snap_engine = subclient_page.get_snap_engine()
        if subclient_page.is_blocklevel_backup_enabled():
            subclient_page.disable_blocklevel_backup()
            subclient_page.disable_snapshot()
            self.admin_console.refresh_page()
            subclient_page.enable_snapshot(snap_engine)
        self.log.info("Add metadata before full backup.")
        postgres_db_object = self.postgres_helper_object._get_postgres_database_connection(
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
            postgres_db_object,
            True,
            "auto_full")
        self.log.info("Run FS based full snap backup.")
        snap_jobid = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(snap_jobid)
        dbhelper_object = DbHelper(self.commcell)
        log_jobid = dbhelper_object.get_snap_log_backup_job(snap_jobid)
        self.log.info("Log backup job with ID:%s is now completed", log_jobid)
        if snap_engine == "native":
            self.log.info("Native snap engine set, waiting for backup copy job")
            dbhelper_object.get_backup_copy_job(str(snap_jobid))
        self.log.info("Add metadata before log backup.")
        self.postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            1,
            2,
            10,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            postgres_db_object,
            True,
            "auto_log")
        self.log.info("Run log backup.")
        log_jobid = subclient_page.backup()
        self.wait_for_job_completion(log_jobid)

    @test_step
    def get_clone_metadata(self):
        """Method to get metadata from clone instance
        Raises:
            CVTestStepFailure exception:
                If unable to get database list from clone
        """
        postgres_db_obj = self.postgres_helper_object._get_postgres_database_connection(
            self.client.client_hostname,
            self.tcinputs['PortForClone'],
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")
        database_list = postgres_db_obj.get_db_list()
        if database_list is None:
            raise CVTestStepFailure("Unable to get the database list.")
        for database in ["postgres", "template0", "template1"]:
            if database in database_list:
                database_list.remove(database)
        return self.postgres_helper_object.generate_db_info(
            database_list,
            self.client.client_hostname,
            self.tcinputs['PortForClone'],
            self.instance.postgres_server_user_name,
            self.postgres_db_password)

    @test_step
    def run_clone_validate(self, backup_metadata, pit_time=None):
        """Method to run clone restore and validate test data
        Args:
            backup_metadata(dict) -- metadata collected before restore
            pit_time -- Point in time in format "%m/%d/%Y %H:%M:%S"
                (eg. 12/31/2020 23:59:59) Default: None
        """
        instant_clone_panel = self.backupset_page.access_clone(
            database_type=DBInstances.Types.POSTGRES)
        if pit_time is None:
            job_id = instant_clone_panel.instant_clone(
                destination_client=self.tcinputs['ClientName'],
                destination_instance=self.tcinputs['InstanceName'],
                **{'clone_retention': {"hours": 1},
                   'port': self.tcinputs['PortForClone']})
        else:
            job_id = instant_clone_panel.instant_clone(
                destination_client=self.tcinputs['ClientName'],
                destination_instance="< Custom >",
                **{'binary_dir': self.instance.postgres_bin_directory,
                   'library_dir': self.instance.postgres_lib_directory,
                   'recover_to': pit_time,
                   'custom': True,
                   'clone_retention': {"hours": 1},
                   'overwrite': True,
                   'port': self.tcinputs['PortForClone']})
        self.wait_for_job_completion(job_id)
        self.postgres_helper_object.set_port_and_listen_address(
            job_id, PortForClone=self.tcinputs['PortForClone'])
        self.log.info("Clone restore job completed. Collect metadata and validate")
        restore_metadata = self.get_clone_metadata()
        self.postgres_helper_object.validate_db_info(backup_metadata, restore_metadata)
        self.postgres_helper_object.refresh()
        return job_id

    @test_step
    def cleanup_old_clones(self):
        """Cleans up old clones present for the instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.access_instant_clones_tab()
        self.instant_clone.delete_clone_if_exists(self.tcinputs['InstanceName'])

    def run(self):
        """ Main function for test case execution """
        try:
            self.cleanup_old_clones()
            backup_metadata1 = self.postgres_helper_object.get_metadata()
            pit = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
            self.backup()
            backup_metadata2 = self.postgres_helper_object.get_metadata()
            self.log.info("Run clone restore to latest time and existing instance")
            self.admin_console.select_breadcrumb_link_using_text('FSBasedBackupSet')
            self.run_clone_validate(backup_metadata2)
            self.log.info("Overwrite existing clone with PIT and custom options")
            clone_jobid = self.run_clone_validate(backup_metadata1, pit)
            self.navigator.navigate_to_db_instances()
            self.database_instances.access_instant_clones_tab()
            self.admin_console.select_hyperlink(clone_jobid)
            creation_time = int(datetime.timestamp(
                datetime.strptime(self.instant_clone_details.get_creation_time,
                                  '%b %d, %Y %I:%M:%S %p')))
            expiry_time = int(datetime.timestamp(
                datetime.strptime(self.instant_clone_details.get_expiry_time,
                                  '%b %d, %Y %I:%M:%S %p')))
            if expiry_time - creation_time < 3600:
                raise CVTestStepFailure("Retention is not set correctly")
            self.log.info("Extend the clone expiry time by 1 day")
            new_expiry_set = self.instant_clone_details.extend_retention({"days": 1})
            self.instant_clone_details.verify_retention(new_expiry_set)
            self.log.info("Delete the clone")
            self.page_container.access_page_action('Delete')
            self.dialog.type_text_and_delete('DELETE')
            self.admin_console.wait_for_completion()
            sleep(120)
            self.admin_console.refresh_page()
            if self.table.is_entity_present_in_column('Clone job id', str(clone_jobid)):
                raise CVTestStepFailure("Clone job {:d} is not deleted".format(clone_jobid))

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
