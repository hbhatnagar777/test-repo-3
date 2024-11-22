# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Method to setup test variables

    wait_for_job_completion()       --  Waits for completion of job and gets the object once job completes

    tear_down()                     --  tear down function to delete automation generated data

    kill_active_jobs()              --  Method to kill the active jobs running for the client

    navigate_to_instance_page()     --  Connects to instance delete and recreates if exists else creates a new one

    set_postgres_helper_object()    --  Creates Postgres helper Object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Creates a database group( more like a subclient )

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

    delete_database_group()         --  Deletes the database group (similar to subclient)

    cleanup()                       --  Deletes instance if it is created by automation

    run()                           --  run function of this test case

"""
import time
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from Web.AdminConsole.Databases.Instances.add_subclient import AddPostgreSQLSubClient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails, PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Components.panel import Backup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """ PostgreSQL GCP PAAS create and delete entity from command center
        Example
        "60039": {
              "ClientName": "gcp_pseudo_ash",
              "PlanName": "plan_ash",
              "InstanceName": "pg10-gk[us-central1]",
              "PostgreSQLUserName": "postgres",
              "PostgreSQLPassword": "12345",
              "testdata": [2,10,100]
        }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "GCP PAAS PostgreSQL create and delete entity from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.postgres_helper_object = None
        self.pgsql_db_object = None
        self.db_instance = None
        self.db_instance_details = None
        self.is_automation_instance = False
        self.perform_instance_check = True
        self.database_list = None
        self.db_prefix = None

    def setup(self):
        """ setup test variables """
        self.log.info("*" * 10 + " Initialize browser objects. " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
        Args:
            jobid   (str): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self.log.info("Successfully finished %s job", jobid)

    def tear_down(self):
        """ tear down function to delete automation generated data """
        self.log.info("Deleting Automation Created databases")
        self.log.info("Database list deleted --- %s", self.database_list)
        self.postgres_helper_object.cleanup_tc_db(
            self.postgres_helper_object.postgres_server_url,
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            "auto_full_dmp")
        self.log.info("Automation Created databases deleted.")

    @test_step
    def kill_active_jobs(self):
        """ Method to kill the active jobs running for the client """
        active_jobs = self.commcell.job_controller.active_jobs(self.tcinputs['ClientName'])
        if active_jobs:
            for job in active_jobs:
                Job(self.commcell, job).kill(True)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def navigate_to_instance_page(self):
        """ Connects to instance delete and recreates if exists else creates a new instance """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        if self.perform_instance_check:
            self.perform_instance_check = False
            if self.db_instance.is_instance_exists(DBInstances.Types.POSTGRES,
                                                   self.tcinputs["InstanceName"],
                                                   self.tcinputs["ClientName"]):
                self.admin_console.select_hyperlink(self.tcinputs["InstanceName"])
                self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
                self.kill_active_jobs()
                self.db_instance_details.delete_instance()

        self.log.info("Creating new instance")
        self.is_automation_instance = True
        self.db_instance.add_gcp_postgresql_instance(self.tcinputs['ClientName'],
                                                     self.tcinputs['PlanName'],
                                                     self.tcinputs['InstanceName'],
                                                     self.tcinputs['PostgreSQLUserName'],
                                                     self.tcinputs['PostgreSQLPassword'])
        self.log.info("Successfully created Instance.")
        self._agent = self._client.agents.get('PostgreSQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)

    @test_step
    def set_postgres_helper_object(self):
        """ Creates Postgres helper Object """
        self.log.info("Creating PostgreSQL Helper Object")
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self._client, self._instance)
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.postgres_helper_object.postgres_server_url,
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            "postgres")
        self.postgres_helper_object.pgsql_db_object = self.pgsql_db_object
        self.log.info("Created PostgreSQL Helper Object")

    @test_step
    def generate_test_data(self, db_prefix):
        """ Generates test data for backup and restore """
        data = self.tcinputs['testdata']
        self.log.info("Generating Test Data")
        self.postgres_helper_object.generate_test_data(
            self.postgres_helper_object.postgres_server_url,
            data[0],
            data[1],
            data[2],
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            True,
            db_prefix)
        self.log.info("Successfully generated Test Data.")

    @test_step
    def navigate_to_db_group(self):
        """ Creates a database group( more like a subclient ) """
        self.database_list = []
        db_list = self.pgsql_db_object.get_db_list()
        for database in db_list:
            if self.db_prefix in database:
                self.database_list.append(database)
        self.navigator.navigate_to_db_instances()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.db_instance_details.click_on_entity('Add database group')
        AddPostgreSQLSubClient(self.admin_console).add_subclient('automation_sc',
                                                                 2,
                                                                 True,
                                                                 self.tcinputs['PlanName'],
                                                                 self.database_list)
        self.db_instance_details.click_on_entity('automation_sc')

    @test_step
    def edit_db_group(self, streams):
        """ Edits database group
        Args:
             streams    (int)   --  Number of streams
        """
        self.database_list = []
        db_list = self.pgsql_db_object.get_db_list()
        for database in db_list:
            if self.db_prefix in database:
                self.database_list.append(database)
        db_group_page = PostgreSQLSubclient(self.admin_console)
        db_group_page.edit_content(self.database_list)
        db_group_page.edit_no_of_streams(streams)
        general_details = db_group_page.get_subclient_general_properties()
        self.log.info(general_details)
        if not int(general_details['Number of data streams'].split('\n')[0]) == streams:
            raise CVTestStepFailure(f"Number of streams is not edited to {streams}")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("#" * 10 + "  DumpBased Backup/Restore Operations  " + "#" * 10)
        self.log.info("Running DumpBased Backup.")
        db_group_page = PostgreSQLSubclient(self.admin_console)
        job_id = db_group_page.backup(backup_type=Backup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.log.info(
            "#" * 10 + "  Running Dumpbased Restore  " + "#" * 10)
        self.log.info("Database list to restore --- %s", self.database_list)
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=self.database_list)
        job_id = restore_panel.in_place_restore(fsbased_restore=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed successfully.")
        self.postgres_helper_object.refresh()
        self.pgsql_db_object.reconnect()

    @test_step
    def delete_database_group(self):
        """ Deletes the database group (similar to subclient) """
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(DBInstances.Types.POSTGRES,
                                         self.tcinputs["InstanceName"],
                                         self.tcinputs["ClientName"])
        self.db_instance_details.click_on_entity('automation_sc')
        db_group_page = PostgreSQLSubclient(self.admin_console)
        db_group_page.delete_subclient()

    @test_step
    def cleanup(self):
        """Deletes instance if it is created by automation"""
        if self.is_automation_instance:
            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(DBInstances.Types.POSTGRES,
                                             self.tcinputs["InstanceName"],
                                             self.tcinputs["ClientName"])
            db_instance_details = DBInstanceDetails(self.admin_console)
            self.kill_active_jobs()
            db_instance_details.delete_instance()

    def run(self):
        """ Main method to run testcase """
        try:
            self.navigate_to_instance_page()
            self.set_postgres_helper_object()
            timestamp = str(int(time.time()))
            self.db_prefix = "auto_full_dmp_" + timestamp
            self.generate_test_data(self.db_prefix)
            self.navigate_to_db_group()
            self.log.info("Regenerating test data to edit contents")
            self.generate_test_data(self.db_prefix + "_r")
            self.edit_db_group(streams=4)
            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.postgres_helper_object.get_metadata()
            self.backup()
            self.tear_down()
            self.restore()
            self.log.info("Get the database meta data after restore")
            after_restore_db_list = self.postgres_helper_object.get_metadata()
            result = self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list,
                after_restore_db_list)
            if result:
                self.log.info("GCP PostgreSQL Backup and Restore Successful!!")
            else:
                self.log.info("GCP PostgreSQL Backup and Restore Failed!!")
            if self.is_automation_instance:
                self.delete_database_group()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
