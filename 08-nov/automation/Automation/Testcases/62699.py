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

    connect_to_instance()           --  Connects to instance if exists else creates a new instance

    set_postgres_helper_object()    --  Creates Postgres helper Object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Connects to database group( more like a subclient )

    backup()                        --  perform backup operation

    get_metadata()                  --  Get Metadata

    restore()                       --  perform restore operation

    cleanup()                       --  Deletes instance if it is created by automation

    run()                           --  run function of this test case

"""
import time
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.Instances.add_subclient import AddPostgreSQLSubClient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails, PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from AutomationUtils.config import get_config

_CONFIG_DATA = get_config()


class TestCase(CVTestCase):
    """ ACCT1 for Azure PAAS PostgreSQL- Flexible Server from command center- AD App
    Example if instance already exists:
    "62699": {
        "PsuedoClientName": "pseudo_ash",
        "InstanceName": "pg10[us-central1]",
        "testdata": [2,10,100]
    }

    Example if instance does not exist:
    "62699": {
          "PsuedoClientName": "pseudo_ash",
          "PlanName": "plan_ash",
          "InstanceName": "pg10[us-central1]",
          "DatabaseUser": "postgres",
          "AccessNode":"access_node",
          "testdata": [2,10,100]
    }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1 for Azure PAAS PostgreSQL- Flexible Server from command center- AD App"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.connection_info = None
        self.postgres_helper_object = None
        self.timestamp = str(int(time.time()))
        self.pgsql_db_object = None
        self.db_instance = None
        self.db_instance_details = None
        self.is_automation_instance = False
        self.perform_instance_check = True
        self.database_list = None

        self.tcinputs = {
            "PsuedoClientName": None,
            "PlanName": None,
            "InstanceName": None,
            "DatabaseUser": None,
            "AccessNode": None
        }

    def setup(self):
        """ Method to setup test variables """
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
        active_jobs = self.commcell.job_controller.active_jobs(self.tcinputs['PsuedoClientName'])
        if active_jobs:
            for job in active_jobs:
                Job(self.commcell, job).kill(True)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def connect_to_instance(self):
        """ Connects to instance if exists else creates a new instance """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        app_credential = f"automation-azuredb-app-credential-{self.timestamp}"
        if self.perform_instance_check:
            self.perform_instance_check = False
            if self.db_instance.is_instance_exists(DBInstances.Types.POSTGRES,
                                                   self.tcinputs["InstanceName"],
                                                   self.tcinputs["PsuedoClientName"]):
                self.log.info("Instance found!")
                self.admin_console.select_hyperlink(self.tcinputs["InstanceName"])
            else:
                self.log.info("Instance not found. Creating new instance")
                self.is_automation_instance = True
                self.db_instance.add_azure_postgresql_instance(cloud_account=self.tcinputs['PsuedoClientName'],
                                                               plan=self.tcinputs['PlanName'],
                                                               instance_name=self.tcinputs['InstanceName'],
                                                               database_user=self.tcinputs['DatabaseUser'],
                                                               access_node=self.tcinputs['AccessNode'],
                                                               app_credential=app_credential,
                                                               ad_auth=True
                                                               )
                self.log.info("Successfully created Instance.")

        self.commcell.refresh()
        self._client = self.commcell.clients.get(self.tcinputs['PsuedoClientName'])
        self._agent = self._client.agents.get('PostgreSQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)

    @test_step
    def set_postgres_helper_object(self):
        """ Creates Postgres helper Object """
        self.log.info("Creating PostgreSQL Helper Object")
        self.commcell.refresh()
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            commcell=self.commcell,
            client=self._client,
            instance=self._instance,
            ssl_ca=_CONFIG_DATA.MySQL.MySqlSSLOptions.ssl_ca)
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.postgres_helper_object.postgres_server_url,
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            "postgres",
            ssl_ca=_CONFIG_DATA.MySQL.MySqlSSLOptions.ssl_ca)
        self.postgres_helper_object.pgsql_db_object = self.pgsql_db_object
        self.log.info("Created PostgreSQL Helper Object")

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
        timestamp = str(int(time.time()))
        data = self.tcinputs['testdata']
        db_prefix = "auto_full_dmp"
        self.log.info("Generating Test Data")
        self.database_list=self.postgres_helper_object.generate_test_data(
            self.postgres_helper_object.postgres_server_url,
            data[0],
            data[1],
            data[2],
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            True,
            db_prefix + "_" + timestamp)
        self.log.info("Successfully generated Test Data.")

    @test_step
    def navigate_to_db_group(self):
        """
        Connects to a database group( similar to a subclient )
        """
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.db_instance_details.click_add_subclient(database_type=DBInstances.Types.POSTGRES)
        AddPostgreSQLSubClient(self.admin_console).add_subclient('automation_sc',
                                                                 2,
                                                                 collect_object_list=False,
                                                                 database_list=self.database_list,
                                                                 plan=self.tcinputs['PlanName'],
                                                                 )
        self.log.info("Database group creation successful.")
        self.log.info("Connected to 'automation_sc' database group.")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("Running DumpBased Backup.")
        db_group_page = PostgreSQLSubclient(self.admin_console)
        job_id = db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.log.info("Database list to restore:%s", self.database_list)
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.tcinputs['PsuedoClientName'])
        self.db_instance_details.access_restore()
        self.admin_console.wait_for_completion()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=self.database_list)
        job_id = restore_panel.in_place_restore(fsbased_restore=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed successfully.")
        self.postgres_helper_object.refresh()
        self.pgsql_db_object.reconnect()

    @test_step
    def get_metadata(self):
        """ Get Metadata """
        return self.postgres_helper_object.generate_db_info(
            db_list=self.database_list,
            hostname=self.postgres_helper_object.postgres_server_url,
            port=self.postgres_helper_object.postgres_port,
            user_name=self.postgres_helper_object.postgres_db_user_name,
            password=self.postgres_helper_object.postgres_password
        )

    @test_step
    def cleanup(self):
        """Deletes instance if it is created by automation"""
        if self.is_automation_instance:
            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(DBInstances.Types.POSTGRES,
                                             self.tcinputs["InstanceName"],
                                             self.tcinputs["PsuedoClientName"])
            db_instance_details = DBInstanceDetails(self.admin_console)
            self.kill_active_jobs()
            db_instance_details.delete_instance()

    def run(self):
        """ Main method to run testcase """
        try:
            self.connect_to_instance()
            self.set_postgres_helper_object()
            self.generate_test_data()
            self.navigate_to_db_group()
            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.get_metadata()
            self.backup()
            self.tear_down()
            self.restore()
            self.log.info("Get the database meta data after restore")
            after_restore_db_list = self.get_metadata()
            result = self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list,
                after_restore_db_list)
            if result:
                self.log.info("Azure PostgreSQL Backup and Restore Successful!")
            else:
                self.log.info("Azure PostgreSQL Backup and Restore Failed!")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
