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

    set_mariadb_helper_object()     --  Creates MariaDB helper Object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Creates a database group( more like a subclient )

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

     run()                           --  run function of this test case
"""

import time
from datetime import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Database.MariaDBUtils.mariadbhelper import MariaDBHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.Databases.databases import RDatabasesMetallic, RAzureMariaDBInstance
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Databases.Instances.add_subclient import AddMySQLSubClient
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Hub.constants import DatabaseTypes
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser

_CONFIG_DATA = get_config()


class TestCase(CVTestCase):
    """ Basic acceptance Test for Metallic - Azure MariaDB using Non AD Authentication
    Example:
        "63092": {
          "Region": "azure region",
          "StorageAccountName": "",
          "StoragePassword": "",
          "container": "storage container",
          "InstanceName": "database instance name",
          "DatabaseUser": "database user name",
          "Password": "database password",
          "testdata": [1,1,10]
        }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.databases = None
        self.azuredatabases = None
        self.name = "Metallic - ACC1 for Azure MariaDB using Non AD Authentication"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.company_name = None
        self.tenant_mgmt = None
        self.tenant_username = None
        self.tenant_password = None
        self.timestamp = str(int(time.time()))

        self.mariadb_helper_object = None
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
            "Password": None
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
        if self.mariadb_helper_object:
            self.log.info("Deleting Automation Created Data")
            self.log.info("Database list deleted --- %s", self.database_list)
            self.mariadb_helper_object.cleanup_test_data(database_prefix='metallic_auto_dump_63092')
            self.log.info("Deleted Automation Created Data")

    @test_step
    def create_instance(self):
        """ Method to run a deployment & create DB Instance """
        self.databases = RDatabasesMetallic(self.admin_console, DatabaseTypes.azure)
        self.azuredatabases = RAzureMariaDBInstance(self.admin_console)

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
                                                       database_password=self.tcinputs["Password"],
                                                       storage_account_name=self.tcinputs["StorageAccountName"],
                                                       storage_password=self.tcinputs["StoragePassword"],
                                                       resource_group=self.resource_group,
                                                       cloud_storage_name=cloud_storage_name,
                                                       storage_credential=storage_credential,
                                                       container=self.tcinputs["container"],
                                                       app_auth=True,
                                                       app_credential=app_credential,
                                                       ssl=False,
                                                       commcell=self.commcell
                                                       )
        self.log.info(f"BackupGateway deployed : {backup_gateway}")

    @test_step
    def set_mariadb_helper_object(self):
        """ Generating MariaDB helper object """
        self.commcell.refresh()
        self._client = self.commcell.clients.get(self.cloud_account)
        self._agent = self._client.agents.get('MySQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])

        self.log.info("Creating MariaDB Helper Object")
        self.mariadb_helper_object = MariaDBHelper(
            commcell=self.commcell,
            subclient='metallic_automation_sc',
            instance=self.instance,
            user=self.instance.mysql_username,
            port=self.instance.port,
            ssl_ca=_CONFIG_DATA.MySQL.MySqlSSLOptions.ssl_ca
        )
        self.log.info("Created MariaDB Helper Object")

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
        timestamp = str(int(time.time()))
        data = self.tcinputs['testdata']
        db_prefix = "metallic_auto_dump_63092"
        self.log.info("Generating Test Data")
        self.database_list = \
            self.mariadb_helper_object.generate_test_data(database_prefix=db_prefix + "_" + timestamp,
                                                          num_of_databases=2,
                                                          num_of_tables=2,
                                                          num_of_rows=10)
        self.log.info("Successfully generated Test Data.")

    @test_step
    def navigate_to_db_group(self):
        """
        Creates a database group( similar to a subclient )
        """
        self.navigator.navigate_to_db_instances()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.cloud_account)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.db_instance_details.click_add_subclient(database_type=DBInstances.Types.MYSQL)
        AddMySQLSubClient(self.admin_console).add_subclient(subclient_name='metallic_automation_sc',
                                                            number_backup_streams=2,
                                                            plan=self.plan,
                                                            database_list=self.database_list)
        self.log.info("Database group creation successful.")
        self.log.info("Conencted to 'metallic_automation_sc' database group.")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("#" * 10 + "  Backup/Restore Operations  " + "#" * 10)
        self.log.info("Running Full Backup.")
        db_group_page = MySQLSubclient(self.admin_console)
        job_id = db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.databases.wait_for_job_completion(job_id, self.commcell)
        self.log.info("Full backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.log.info("#" * 10 + "  Running Restore  " + "#" * 10)
        self.log.info("Database list to restore --- %s", self.database_list)
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.cloud_account)
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.MYSQL, items_to_restore=self.database_list)
        job_id = restore_panel.in_place_restore(data_restore=False,
                                                log_restore=False,
                                                staging_location=None,
                                                notify_job_completion=False,
                                                is_cloud_db=True)
        self.databases.wait_for_job_completion(job_id, self.commcell)
        self.log.info("Restore completed successfully.")

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info(f"{self.company_name} is created")
            self.create_instance()
            self.set_mariadb_helper_object()
            self.tear_down()
            self.generate_test_data()
            self.navigate_to_db_group()
            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.mariadb_helper_object.get_database_information()
            self.backup()
            self.tear_down()
            self.restore()
            self.log.info("Get the database meta data after restore")
            after_restore_db_list = self.mariadb_helper_object.get_database_information()
            self.mariadb_helper_object.validate_db_info(before_full_backup_db_list, after_restore_db_list)
            self.log.info("Testcase executed successfully.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.log.info("cleaning up the resources-deactivate & delete tenant")
            self.log.info(f"Azure resource group - {self.resource_group} and tenant are deleted")
            self.tear_down()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)