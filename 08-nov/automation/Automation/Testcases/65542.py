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

    start_rds()                     --  starts the rds instance

    stop_rds()                      --  stops the rds instance

    create_and_update_bgw()         --  Method to run a deployment & create bgw and DB Instance & then update bgw

    create_instance()               --  Method to run a deployment & create bgw and DB Instance & then update bgw

    clean_and_stop_rds               -- cleans the test generated data & stops RDS instance

    tear_down()                     --  tear down function to delete automation generated data

    set_mysql_helper_object()       --  Creates MySQL helper Object

    generate_test_data()            --  Generates test data for backup and restore

    get_metadata()                   --  Gets Metadata for generated database list

    add_db_group()                  --  Creates and Connects to a database group consisting
                                        of generated Test data( similar to a sub client )

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

    delete_tenant()                 --  Deletes the Tenant

    run()                           --  run function of this test case

    add example inputs

"""
import time
from datetime import datetime
from cvpysdk.commcell import Commcell
from Application.CloudStorage.s3_helper import S3MetallicHelper
from Application.CloudApps.amazon_helper import AmazonRDSCLIHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from AutomationUtils.config import get_config
from Database.MySQLUtils import mysqlhelper
from Metallic.hubutils import HubManagement
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.Instances.add_subclient import AddMySQLSubClient
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Hub.Databases.databases import AWSRDSExport, RDatabasesMetallic
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure

_CONFIG_DATA = get_config()

class TestCase(CVTestCase):
    """ Basic acceptance Test for AWS Aurora MySQL metallic
    Example :
    "65542":{
            "Region": "ap-south-1",
            "InstanceName": "Instance[region]",
            "DatabaseUser": "mysql",
            "Password": "Password",
            "testdata": [2,2,10],
            "key-pair":"key",
            "vpc":"vpc",
            "subnet":"subnet",
            "OS_type":  "Linux",
            "BucketName" : "bucket"
    }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Metallic - ACC1 for AWS RDS(Export) Aurora MySQL using IAM Role"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.company_name = None
        self.tenant_mgmt = None
        self.tenant_username = None
        self.tenant_password = None
        self.timestamp = str(int(time.time()))
        self.mysql_helper_object = None
        self.mysql_db_object = None
        self.db_instance_details = None
        self.db_instance = None
        self.cloud_account = None
        self.plan = None
        self.wizard = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.s3_metallic_helper = None
        self.amazon_rds_helper = None
        self.awsdatabases = None
        self.stack_name = None
        self.bgw_name = None
        self.byos_storage_name = None
        self.generated_database_list = []
        self.db_prefix = "metallic_auto_dump"
        self.region = None
        self._instance_identifier = None
        self.RDM = None


    def setup(self):
        """Setup function of this test case"""

        self.company_name = datetime.now().strftime("AWSDB-Automation-SJ-%d-%B-%H-%M")
        email = datetime.now().strftime(f"metallic_awsdb_%H-%M-%S@{self.company_name}.com")
        ring_hostname = self.tcinputs.get("ring_hostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, email)
        self.tenant_password = _CONFIG_DATA.Metallic.tenant_password
        self.commcell = Commcell(webconsole_hostname=ring_hostname,
                                 commcell_username=_CONFIG_DATA.Metallic.workflow_user,
                                 commcell_password=_CONFIG_DATA.Metallic.workflow_password)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_password, stay_logged_in=True)
        self.navigator = self.admin_console.navigator

        self.wizard = Wizard(self.admin_console)
        self.hub_dashboard = Dashboard(self.admin_console, service=HubServices.database.value, 
                                       app_type=DatabaseTypes.AWS.value)
        self.service_catalogue = ServiceCatalogue(self.admin_console, service=HubServices.database.value,
                                                  app_type=DatabaseTypes.AWS.value)
        self.s3_metallic_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.amazon_rds_helper = AmazonRDSCLIHelper(
            access_key=_CONFIG_DATA.aws_access_creds.access_key,
            secret_key=_CONFIG_DATA.aws_access_creds.secret_key
        )
        
        self.RDM = RDatabasesMetallic(self.admin_console, app_type=DatabaseTypes.AWS.value)
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.awsdatabases = AWSRDSExport(self.admin_console, s3_helper=self.s3_metallic_helper,
                                         aws_helper=self.amazon_rds_helper, 
                                         database_type=DBInstances.Types.AURORA_MYSQL.value)
        
    @test_step
    def start_rds(self):
        """Method to start RDS cluster if it's present and in stopped state"""
        self.region = self.tcinputs['Region']
        self._instance_identifier = self.tcinputs["InstanceName"][:self.tcinputs["InstanceName"].index('[')]
        if self.amazon_rds_helper.is_cluster_present(self.region, self._instance_identifier, availability=False):
            if not self.amazon_rds_helper.is_cluster_present(self.region, self._instance_identifier):
                self.amazon_rds_helper.start_rds_cluster(self.region, self._instance_identifier)
                self.log.info("Instance started")
            else:
                self.log.info("Instance is in available state already")
       
    @test_step
    def stop_rds(self):
        """Method to stop RDS instance if it in available state"""
        if self.amazon_rds_helper.is_cluster_present(self.region, self._instance_identifier):
            self.amazon_rds_helper.stop_rds_cluster(self.region, self._instance_identifier)
        else:
            self.log.info("Instance is in stopped state already")


    @test_step
    def create_and_update_bgw(self):
        """ Method to run a deployment & create bgw and DB Instance & then update bgw"""
        self.hub_dashboard.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(service=HubServices.database.value,
                                                                     id=HypervisorDisplayName.AMAZON_AWS.value)
        self.awsdatabases.select_trial_subscription()

        params_for_bgw = [
            {
                "ParameterKey": "KeyName",
                "ParameterValue": self.tcinputs.get("key-pair")
            },
            {
                "ParameterKey": "VpcId",
                "ParameterValue": self.tcinputs.get("vpc")
            },
            {
                "ParameterKey": "SubnetId",
                "ParameterValue": self.tcinputs.get("subnet")
            }
        ]

        self.stack_name = "awsmetallicRDSmysql" + datetime.now().strftime("SJ%d%B%H%M")
        self.bgw_name = self.awsdatabases.create_gateway(region=self.tcinputs.get("Region"),
                                                         stack_name=self.stack_name,
                                                         stack_params=params_for_bgw,
                                                         gateway_os_type=self.tcinputs["OS_type"],
                                                         is_rds_export=True)
        job_id = self.awsdatabases.upgrade_client_software(self.bgw_name)
        self.RDM.wait_for_job_completion(job_id, self.commcell)
        self.log.info(f"{self.bgw_name} Created and updated successfully.")

    @test_step
    def create_instance(self):
        """ Method to create an instance"""
        self.cloud_account = f"automation-AWS-Aurora-MySQL-{self.timestamp}"
        self.plan = f"AWS_Aurora_MySQL_plan" + datetime.now().strftime("SJ%d%B%H%M").lower()
        self.navigator.navigate_to_db_instances()
        self.awsdatabases.click_add_cloud_db()
        self.byos_storage_name = "awsmetallicdocumentdbstorage" + datetime.now().strftime("SJ%d%B%H%M").lower()
        self.awsdatabases.configure(region=self.tcinputs.get("Region"),
                                    byos_storage_name=self.byos_storage_name,
                                    byos_bucket_name=self.tcinputs["BucketName"],
                                    cloud_account_name=self.cloud_account,
                                    plan_name=self.plan,
                                    instance_name="aurora/"+ self.tcinputs["InstanceName"],
                                    database_user=self.tcinputs["DatabaseUser"],
                                    database_password=self.tcinputs["Password"],
                                    maintenance_db=None,
                                    is_rds_export=True)

    @test_step
    def clean_and_stop_rds(self, stop_rds):
        """ tear down function to delete automation generated data 
        Args:
            stop_rds   (bool): True if RDS instance is to be stopped.
        """
        self.log.info("Deleting Automation Created databases")
        self.log.info("Database list deleted --- %s", self.generated_database_list)
        if self.amazon_rds_helper.is_cluster_present(self.region, self._instance_identifier):
            self.mysql_helper_object.cleanup_test_data(self.db_prefix)
            self.log.info("Automation Created databases deleted.")
        else:
            self.log.info("Instance not available for teardown")
        if stop_rds:
            self.stop_rds()

    def tear_down(self):
        """ tear down function to delete automation generated data """
        self.s3_metallic_helper.delete_stack(stack_name=self.stack_name)
        self.clean_and_stop_rds(stop_rds=True)

    @test_step
    def set_mysql_helper_object(self):
        """Creates MySQL helper Object"""
        self.log.info("Creating MySQL Helper Object")
        self.commcell.refresh()
        _client = self.commcell.clients.get(self.cloud_account)
        _agent = _client.agents.get('MySQL')
        _instance = _agent.instances.get("aurora/" + self.tcinputs['InstanceName'])
        _subclient = _instance.subclients.get('default')

        self.mysql_helper_object = mysqlhelper.MYSQLHelper(
            commcell=self.commcell,
            subclient=_subclient,
            instance=_instance,
            hostname = self.tcinputs['Hostname'],
            user = self.tcinputs['DatabaseUser'],
            port = _instance.port
            )
        self.log.info("Created MySQL Helper Object")

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
        self.clean_and_stop_rds(stop_rds=False)
        data = self.tcinputs['testdata']

        self.log.info("Generating Test Data")
        self.generated_database_list = self.mysql_helper_object.generate_test_data(
            database_prefix=self.db_prefix,
            num_of_databases=int(data[0]),
            num_of_tables=int(data[1]),
            num_of_rows=int(data[2])
            )
        self.log.info("Successfully generated Test Data.")

    @test_step
    def get_metadata(self):
        """ Returns complete metadata info of Database """
        return self.mysql_helper_object.get_database_information(database_list=self.generated_database_list)

    @test_step
    def add_db_group(self, plan_name):
        """ Creates and Connects to a database group consisting of generated Test data( similar to a sub client )
            Args:
            plan_name       (str):      Name of the plan to associate to subclient
        """
        self.log.info("Navigating to DB_instances")
        self.navigator.navigate_to_db_instances()
        self.wizard.table.reload_data()
        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.cloud_account)

        self.db_instance_details.click_add_subclient(DBInstances.Types.MYSQL)
        AddMySQLSubClient(self.admin_console).add_subclient('automation_sc',
                                                            2,
                                                            self.generated_database_list,
                                                            plan_name,)

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("#" * 10 + "  DumpBased Backup/Restore Operations  " + "#" * 10)
        self.log.info("Running DumpBased Backup.")
        db_group_page = MySQLSubclient(self.admin_console)
        job_id = db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.RDM.wait_for_job_completion(jobid=job_id, commcell=self.commcell)
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.log.info("#" * 10 + "  Running Dumpbased Restore  " + "#" * 10)
        self.log.info("Database list to restore ---- %s", self.generated_database_list)
        self.navigator.navigate_to_db_instances()

        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.cloud_account)
        self.db_instance_details.access_restore()

        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.MYSQL, items_to_restore=self.generated_database_list)

        job_id = restore_panel.in_place_restore(is_cloud_db=True)
        self.RDM.wait_for_job_completion(job_id, self.commcell)
        self.log.info("Restore completed successfully.")

    @test_step
    def delete_tenant(self):
        """ This deletes the tenant created """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)

    def run(self):
        """ Main method to run testcase """
        try:
            self.start_rds()
            self.create_and_update_bgw()
            self.create_instance()
            self.set_mysql_helper_object()
            self.generate_test_data()
            self.add_db_group(plan_name=self.plan)

            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.get_metadata()
            self.backup()
            self.clean_and_stop_rds(stop_rds=False)
            self.restore()

            self.log.info("Get the database meta data after restore")
            after_restore_db_list = self.get_metadata()
            result = self.mysql_helper_object.validate_db_info(
                before_full_backup_db_list,
                after_restore_db_list)

            if result == None:
                self.log.info("Amazon RDS Aurora MySQL Backup and Restore Successful!")
            

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.clean_and_stop_rds(stop_rds=True)
            self.delete_tenant()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
