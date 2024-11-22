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

    tear_down()                     --  tear down function to delete automation generated data

    create_instance()               --  Method to run a deployment & create DB Instance

    set_postgres_helper_object()    --  Creates Postgres helper Object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Creates a database group( more like a subclient )

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

    get_metadata()                  --  Get Metadata

    run()                           --  run function of this test case
"""

import time
from datetime import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils import database_helper
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.Instances.add_subclient import AddPostgreSQLSubClient
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Hub.Databases.databases import RDatabasesMetallic, RAzurePostgreSQLInstance
from Web.AdminConsole.Hub.constants import DatabaseTypes
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser

_CONFIG_DATA = get_config()


class TestCase(CVTestCase):
    """ Basic acceptance Test for Metallic - Azure PostgreSQL using App Based Authentication
    Example:
        "63088": {
          "Region": "azure region",
          "StorageAccountName": "",
          "StoragePassword": "",
          "container": "storage container",
          "InstanceName": "database instance name",
          "DatabaseUser": "database user name",
          "testdata": [1,1,10]
        }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.databases = None
        self.azuredatabases = None
        self.name = "Metallic - ACC1 for Azure PostgreSQL using App Based Authentication"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.company_name = None
        self.tenant_mgmt = None
        self.tenant_username = None
        self.tenant_password = None
        self.timestamp = str(int(time.time()))

        self.postgres_helper_object = None
        self.pgsql_db_object = None
        self.db_instance_details = None
        self.database_list = list()
        self.db_instance = None
        self.cloud_account = None
        self.azure_rg = None
        self.resource_group = None
        self.plan = None

        self.tcinputs = {
            "Region": None,
            "StorageAccountName": None,
            "container": None,
            "StoragePassword": None,
            "InstanceName": None,
            "DatabaseUser": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.company_name = datetime.now().strftime("AZUREDB-Automation-%d-%B-%H-%M")
        email = datetime.now().strftime(f"metallic_azuredb_%H-%M-%S@{self.company_name}.com")

        ring_hostname = self.tcinputs.get("ring_hostname", self.commcell.webconsole_hostname)
        self.tenant_username = RDatabasesMetallic.create_tenant(self, 'AZUREDB-NEW', ring_hostname)
        self.timestamp = (datetime.strptime(self.tenant_username,
                                            "AZUREDB-NEW-Automation-%Y-%d-%B-%H-%M\\automation_user")
                          .strftime("%Y-%d-%B-%H-%M"))
        self.tenant_password = _CONFIG_DATA.Metallic.tenant_password

        self.commcell = Commcell(webconsole_hostname=ring_hostname,
                                 commcell_username=_CONFIG_DATA.Metallic.workflow_user,
                                 commcell_password=_CONFIG_DATA.Metallic.workflow_password)

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_password, stay_logged_in=True)
        self.navigator = self.admin_console.navigator

    def tear_down(self):
        """ Tear down function to delete automation generated data """
        self.log.info("Deleting Automation Created databases")
        self.log.info("Database list deleted --- %s", self.database_list)
        if self.postgres_helper_object:
            self.postgres_helper_object.cleanup_tc_db(
                self.postgres_helper_object.postgres_server_url,
                self.postgres_helper_object.postgres_port,
                self.postgres_helper_object.postgres_db_user_name,
                self.postgres_helper_object.postgres_password,
                "metallic_auto_dump_63088")
        self.log.info("Automation Created databases deleted.")

    @test_step
    def create_instance(self):
        """ Method to run a deployment & create DB Instance """
        self.databases = RDatabasesMetallic(self.admin_console, DatabaseTypes.azure)
        self.azuredatabases = RAzurePostgreSQLInstance(self.admin_console)
        self.cloud_account = f"automation-azuredb-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.resource_group = f"automation-{self.timestamp}"
        self.plan = f"automation-azuredb-plan-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cloud_storage_name = f"automation-BYOS-storage-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        storage_credential = f"automation-azuredb-storage-credential-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        app_credential = f"automation-azuredb-app-credential-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backup_gateway = self.azuredatabases.configure(region=self.tcinputs["Region"],
                                                       cloud_account=self.cloud_account,
                                                       plan=self.plan,
                                                       instance_name=self.tcinputs["InstanceName"],
                                                       database_user=self.tcinputs["DatabaseUser"],
                                                       storage_account_name=self.tcinputs["StorageAccountName"],
                                                       storage_password=self.tcinputs["StoragePassword"],
                                                       resource_group=self.resource_group,
                                                       cloud_storage_name=cloud_storage_name,
                                                       storage_credential=storage_credential,
                                                       container=self.tcinputs["container"],
                                                       app_auth=True,
                                                       app_credential=app_credential,
                                                       ssl=True,
                                                       ad_auth=True,
                                                       commcell=self.commcell,
                                                       storage_auth_type="IAM AD application",
                                                       )
        self.log.info(f"BackupGateway deployed : {backup_gateway}")

    @test_step
    def set_postgres_helper_object(self, client):
        """
        Creates Postgres helper Object
        Args:
            client      (object)    :   client object
        """
        self.log.info("Creating PostgreSQL Helper Object")
        self.commcell.refresh()
        self._client = self.commcell.clients.get(client)
        self._agent = self._client.agents.get('PostgreSQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])

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
        data = self.tcinputs['testdata']
        db_prefix = "metallic_auto_dump_63088"
        self.log.info("Generating Test Data")
        self.postgres_helper_object.generate_test_data(
            hostname=self.postgres_helper_object.postgres_server_url,
            num_of_databases=2,
            num_of_tables=2,
            num_of_rows=2,
            port=self.postgres_helper_object.postgres_port,
            user_name=self.postgres_helper_object.postgres_db_user_name,
            password=self.postgres_helper_object.postgres_password,
            delete_if_already_exist=True,
            database_prefix=db_prefix + "_" + self.timestamp)
        self.log.info("Successfully generated Test Data.")

    @test_step
    def navigate_to_db_group(self, plan_name):
        """
        Connects to a database group( similar to a subclient )
        Args:
            plan_name       (str):      Name of the plan to associate to subclient
        """
        db_list = self.pgsql_db_object.get_db_list()
        db_prefix = "metallic_auto_dump_63088"
        for database in db_list:
            if db_prefix in database:
                self.database_list.append(database)

        self.navigator = self.admin_console.navigator
        self.log.info("Navigating to DB_instances")
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.cloud_account)

        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
        self.db_instance_details.click_add_subclient(database_type=DBInstances.Types.POSTGRES)
        AddPostgreSQLSubClient(self.admin_console).add_subclient('metallic_automation_sc',
                                                                 2,
                                                                 collect_object_list=False,
                                                                 database_list=self.database_list,
                                                                 plan=plan_name,
                                                                 )
        self.log.info("Database group creation successful.")
        self.log.info("Connected to 'metallic_automation_sc' database group.")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("Running DumpBased Backup.")
        db_group_page = PostgreSQLSubclient(self.admin_console)
        job_id = db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.databases.wait_for_job_completion(job_id, self.commcell)
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.navigator = self.admin_console.navigator
        self.log.info("Database list to restore:%s", self.database_list)
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.cloud_account)

        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=self.database_list)
        job_id = restore_panel.in_place_restore(fsbased_restore=False)
        self.databases.wait_for_job_completion(job_id, self.commcell)
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

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info(f"{self.company_name} is created")
            self.create_instance()
            self.db_instance = DBInstances(self.admin_console)
            self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)
            self.set_postgres_helper_object(client=self.cloud_account)
            self.tear_down()
            self.generate_test_data()
            self.navigate_to_db_group(plan_name=self.plan)
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
            self.log.info("Testcase executed successfully.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.log.info("cleaning up the resources-deactivate & delete tenant")
            self.log.info(f"Azure resource group - {self.resource_group} and tenant are deleted")
            self.tear_down()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
