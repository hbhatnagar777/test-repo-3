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
				"62470": {
					"ClientName": "client1",
					"AgentName": "POSTGRESQL",
					"InstanceName": "instance1",
					"BackupsetName": "fsbasedbackupset",
					"SubclientName": "default",
                    "PortForClone": 5442,
                    "DestinationClient": "client2",
                    "DestinationInstance": "instance2",
                    "tablespace_name": "tblspc1"
				}
			}
"""
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.Instances.instant_clone import InstantClone
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """Class to execute cross machine clone restore for block level from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Cross machine clone from command center for postgresql block level"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'PortForClone': None,
            'DestinationClient': None,
            'DestinationInstance': None,
            'tablespace_name': None
        }
        self.source_postgres_helper_object = None
        self.database_instances = None
        self.instant_clone = None
        self.destination_client = None
        self.destination_instance = None
        self.destination_postgres_helper_object = None
        self.db_instance_details = None
        self.backupset_page = None

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
        self.source_postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.instant_clone = InstantClone(self.admin_console)
        self.destination_client = self.commcell.clients.get(self.tcinputs['DestinationClient'])
        agent = self.destination_client.agents.get('postgresql')
        self.destination_instance = agent.instances.get(self.tcinputs['DestinationInstance'])
        self.destination_postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.destination_client, self.destination_instance)
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.backupset_page = PostgreSQLBackupset(self.admin_console)

    def tear_down(self):
        """ tear down method for test case """
        self.log.info("Deleting Automation Created databases")
        if self.source_postgres_helper_object:
            self.source_postgres_helper_object.cleanup_tc_db(
                self.client.client_hostname,
                self.instance.postgres_server_port_number,
                self.instance.postgres_server_user_name,
                self.source_postgres_helper_object.postgres_password,
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
        """Runs full and log backup for the block level subclient
        Raises:
            CVTestStepFailure exception:
                If snapshot is not enabled on subclient
        """
        self.navigate_to_subclient()
        subclient_page = PostgreSQLSubclient(self.admin_console)
        if not subclient_page.is_snapshot_enabled():
            raise CVTestStepFailure("snapshot is not enabled at subclient level")
        snap_engine = subclient_page.get_snap_engine()
        if not subclient_page.is_blocklevel_backup_enabled():
            subclient_page.enable_blocklevel_backup()
        self.log.info("Add metadata before full backup.")
        self.source_postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            2,
            10,
            100,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.source_postgres_helper_object.postgres_password,
            True,
            "auto_full",
            tablespace=self.tcinputs['tablespace_name'])
        self.log.info("Run FS based full snap backup.")
        snap_jobid = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(snap_jobid)
        dbhelper_object = DbHelper(self.commcell)
        log_jobid = dbhelper_object.get_snap_log_backup_job(snap_jobid)
        self.log.info("Log backup job with ID:%s is now completed", log_jobid)
        if snap_engine.lower() == "native":
            self.log.info("Snap engine is native, check backup copy status")
            dbhelper_object.get_backup_copy_job(str(snap_jobid))
        else:
            self.log.info("Snap engine is not native, run backup copy")
            dbhelper_object.run_backup_copy(self.subclient.storage_policy)
        self.log.info("Add metadata before log backup.")
        self.source_postgres_helper_object.generate_test_data(
            self.client.client_hostname,
            1,
            2,
            10,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.source_postgres_helper_object.postgres_password,
            True,
            "auto_log",
            tablespace=self.tcinputs['tablespace_name'])
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
        postgres_db_obj = self.destination_postgres_helper_object.get_postgres_db_obj(
            self.destination_client.client_hostname,
            self.tcinputs['PortForClone'],
            self.destination_instance.postgres_server_user_name,
            self.destination_postgres_helper_object.postgres_password,
            "postgres")
        database_list = postgres_db_obj.get_db_list()
        if database_list is None:
            raise CVTestStepFailure("Unable to get the database list.")
        for database in ["postgres", "template0", "template1"]:
            if database in database_list:
                database_list.remove(database)
        return self.destination_postgres_helper_object.generate_db_info(
            database_list,
            self.destination_client.client_hostname,
            self.tcinputs['PortForClone'],
            self.destination_instance.postgres_server_user_name,
            self.destination_postgres_helper_object.postgres_password)

    @test_step
    def run_clone_validate(self, backup_metadata, pit_time=None):
        """Method to run clone restore and validate test data
        Args:
            backup_metadata(dict) -- metadata collected before restore
            pit_time -- Point in time in format "%m/%d/%Y %H:%M:%S"
                (eg. 12/31/2020 23:59:59) Default: None
        """
        instant_clone_panel = self.database_instances.instant_clone(
            database_type=DBInstances.Types.POSTGRES,
            source_server=self.tcinputs['ClientName'],
            source_instance=self.tcinputs['InstanceName'])
        if pit_time is None:
            job_id = instant_clone_panel.instant_clone(
                destination_client=self.tcinputs['DestinationClient'],
                destination_instance=self.tcinputs['DestinationInstance'],
                **{'clone_retention': {"hours": 1},
                   'port': self.tcinputs['PortForClone']})
        else:
            job_id = instant_clone_panel.instant_clone(
                destination_client=self.tcinputs['DestinationClient'],
                destination_instance="< Custom >",
                **{'binary_dir': self.instance.postgres_bin_directory,
                   'library_dir': self.instance.postgres_lib_directory,
                   'recover_to': pit_time,
                   'custom': True,
                   'clone_retention': {"hours": 1},
                   'overwrite': True,
                   'port': self.tcinputs['PortForClone']})
        self.wait_for_job_completion(job_id)
        self.destination_postgres_helper_object.set_port_and_listen_address(
            job_id, PortForClone=self.tcinputs['PortForClone'])
        self.log.info("Clone restore job completed. Collect metadata and validate")
        restore_metadata = self.get_clone_metadata()
        self.source_postgres_helper_object.validate_db_info(backup_metadata, restore_metadata)
        self.source_postgres_helper_object.refresh()
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
            backup_metadata1 = self.source_postgres_helper_object.get_metadata()
            pit = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
            self.backup()
            backup_metadata2 = self.source_postgres_helper_object.get_metadata()
            self.log.info("Run clone restore to latest time and existing instance")
            self.navigator.navigate_to_db_instances()
            self.database_instances.access_instant_clones_tab()
            self.run_clone_validate(backup_metadata2)
            self.log.info("Overwrite existing clone with PIT and custom options")
            clone_jobid = self.run_clone_validate(backup_metadata1, pit)
            self.instant_clone.refresh()
            job_details = self.instant_clone.get_clone_details(clone_jobid)
            creation_time = datetime.strptime(
                job_details['Creation time'][0], '%b %d, %I:%M %p').utctimetuple()[3]
            expiry_time = datetime.strptime(
                job_details['Expiration date'][0], '%b %d, %I:%M %p').utctimetuple()[3]
            if expiry_time - creation_time != 1:
                raise CVTestStepFailure("Retention is not set correctly")
            self.log.info("Delete the clone")
            self.instant_clone.select_clone_delete(clone_jobid=clone_jobid)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
