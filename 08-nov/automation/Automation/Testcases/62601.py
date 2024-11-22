"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    initial_setup()             --  method to crete an instance of AWS Dynamo DB
                                    in the metallic

    navigate_to_dynamo_db()     --  Redirects to Dynamo instance

    create_test_data()          --  method for creating test data

    wait_for_job_completion()   --  waits for completion of job

    submit_backup()             -- method to run backup

    submit_in_place_restore()   --  method to run restore in place

    delete_tenant()             --  method to deactivate and delete the tenant

    cleanup()                   --  method to clean up all testcase created changes/resources

    run()                       --  run function of this test case

    tear_down()                 --  tear down method for testcase



Input Example:

    "testCases":
            {
                "62601":
                        {
                            "Region"        :   "Region where Dynamo DB is hosted in AWS(us-east-2)",
                            "key-pair"      :   "key pair for backup gateway(AWS)",
                            "vpc"           :   "vpc for backup gateway(AWS)",
                            "subnet"        :   "subnet for backup gateway(AWS)",
                            'TestData'      :   "[10, 20, 100]",
                            "os_type"       :   OS type of the access node
                        }
            }
    "Examaple":
        {
            "62601":
            {
                "Region":"us-east-2",
                "key-pair":"aws-key",
                "vpc":"vpc-xxxx",
                "subnet":"subnet-xxxx",
                "TestData":"[10, 20, 100]",
                "os-type":"Linux"
            }
        }

"""

import ast
from cvpysdk.commcell import Commcell
from datetime import datetime
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Hub.Databases.databases import RAWSDynamoDB
from Web.AdminConsole.Hub.dashboard import Dashboard
from Application.CloudStorage.s3_helper import S3MetallicHelper, S3Helper
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from AutomationUtils.idautils import CommonUtils
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Components.dialog import RBackup


class TestCase(CVTestCase):
    """Class for executing """
    test_step = TestStep()

    def __init__(self):
        """Initialize the class"""
        super(TestCase, self).__init__()
        self.dynamodb_subclient = None
        self.dynamodb_helper = None
        self.backup_gateway = None
        self.byos_bucket_name = None
        self.byos_storage_name = None
        self.stack_name = None
        self.s3_helper = None
        self.s3_container_helper = None
        self.gateway_created = None
        self.dynamodb_metallic_configuration = None
        self.database_type = None
        self.test_data = None
        self.hub_dashboard = None
        self.name = "Test Case for Dynamo DB from Metallic Command Center on AWS cloud"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_62601'
        self.tenant_mgmt = None
        self.company_name = None
        self.company_email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.email = None
        self.tenant_created = None
        self.app_type = None
        self.service = None
        self.tables = {"full": "CV_TABLE_", "incr": "CV_TABLE_INCR_"}
        self.table_list = []
        self.vendor = None
        self.database_instances = None
        self.db_instance_details = None
        self.cloud_account = None
        self.config_files = get_config()
        self.service_catalogue = None

    def setup(self):
        """ Method to setup test variables"""
        self.log.info("Started Executing %s testcase", self.id)
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="Dynamo-DB-Automation-AWS-SK")
        self.company_name = datetime.now().strftime("Dynamo-DB-Automation-AWS-SK-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_Dynamo_db_AWS_SK_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = self.config_files.Metallic.tenant_password
        self.tenant_created = True
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.cloud_account = "DynamoDBsk"
        self.database_type = DBInstances.Types.DYNAMODB
        self.service = HubServices.database
        self.app_type = DatabaseTypes.AWS
        self.s3_container_helper = S3Helper(self)
        self.s3_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.vendor = "Amazon Web Services"
        self.dynamodb_helper = AmazonDynamoDBCLIHelper(
            secret_key=self.config_files.aws_access_creds.secret_key,
            access_key=self.config_files.aws_access_creds.access_key)
        self.dynamodb_helper.initialize_client(self.tcinputs.get("Region"))
        self.dynamodb_metallic_configuration = RAWSDynamoDB(
            self.admin_console,
            aws_helper=self.dynamodb_helper,
            s3_helper=self.s3_helper)
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        if self.tcinputs.get("TestData"):
            if isinstance(self.tcinputs["TestData"], str):
                self.test_data = ast.literal_eval(self.tcinputs["TestData"])
            else:
                self.test_data = self.tcinputs["TestData"]

    def initial_setup(self):
        """initial setup method"""
        self.hub_dashboard.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(self.service.value, id="Amazon Web Services")
        self.dynamodb_metallic_configuration.select_trial_subscription()
        params = [
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
        self.stack_name = "awsmetallicdynamodb" + datetime.now().strftime("sk%d%B%H%M")
        self.byos_storage_name = "awsmetallicdynamodbstorage" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.byos_bucket_name = "awsmetallicdynamodbbucket" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.backup_gateway = self.dynamodb_metallic_configuration.create_gateway(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params, gateway_os_type=self.tcinputs.get("os_type") or "Linux")
        job = self.dynamodb_metallic_configuration.upgrade_client_software(self.backup_gateway)
        self.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.dynamodb_metallic_configuration.click_add_cloud_db()
        self.dynamodb_metallic_configuration.configure(
            region=self.tcinputs.get("Region"),
            byos_storage_name=self.byos_storage_name,
            byos_bucket_name=self.byos_bucket_name,
            cloud_account_name=self.cloud_account,
            plan_name="AWSMetallicDynamoDBPlan",
            content=["TC_62601"],
            is_dynamo=True)
        self.gateway_created = True
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.dynamodb_subclient = SubClient(self.admin_console)

    @test_step
    def navigate_to_dynamodb_instance(self):
        """Navigates to dynamodb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(self.database_instances.Types.CLOUD_DB, 'DynamoDB',
                                                self.tcinputs['cloud_account'])

    @test_step
    def create_test_data(self, table_name, partition_key):
        """Creates dynamodb table and populates test data
        Args:
            table_name (str): Name of table
            partition_key (str): Name of the partition key column
        """
        self.dynamodb_helper.create_dynamodb_table(table_name, partition_key)
        self.dynamodb_helper.populate_dynamodb_table(table_name, partition_key, 10)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def submit_backup(self, level='Incremental'):
        """Submits DynamoDB backup and validates it
        Args:
            level    (str): Backup level, full or incremental

        """
        if level == "Full":
            bkp = self.dynamodb_subclient.backup(RBackup.BackupType.FULL)
        else:
            bkp = self.dynamodb_subclient.backup()
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(bkp, level)

    @test_step
    def submit_in_place_restore(self, table_name):
        """
        Submits in place restore
        table_name  (str)   :   name of the table to get restored
        """
        self.dynamodb_subclient.access_restore()
        mapping_dict = {
            self.tcinputs.get("Region"): [table_name]
        }
        restore_panel_obj = self.dynamodb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'default')
        jobid = restore_panel_obj.same_account_same_region(overwrite='True')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")

    def delete_tenant(self):
        """
        This deletes the tenant created
        """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)

    def cleanup(self):
        """Delete the Resources, Tables and Tenants created by test case"""
        self.dynamodb_helper.delete_dynamodb_table("TC_62601")
        self.s3_helper.delete_stack(stack_name=self.stack_name)
        s3_session = self.s3_container_helper.create_session_s3(
            access_key=self.config_files.aws_access_creds.access_key
            , secret_access_key=self.config_files.aws_access_creds.secret_key, region=self.tcinputs.get('Region'))
        self.s3_container_helper.delete_container_s3(s3_session, self.byos_bucket_name)

    def run(self):
        """Main method to run test case"""
        try:
            table_name = 'TC_62601'
            self.create_test_data(table_name, 'id')
            self.initial_setup()
            self.db_instance_details.click_on_entity('default')
            self.submit_backup(level='Full')
            self.dynamodb_helper.populate_dynamodb_table(table_name, 'id', 20)
            self.submit_backup()
            self.admin_console.refresh_page()
            self.submit_in_place_restore(table_name)
            self.dynamodb_helper.validate_dynamodb_table(table_name, 'id', 20)
            self.admin_console.refresh_page()
            self.delete_tenant()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """
        Function to run after automation execution
        """
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
