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

    init_tc()             --  method to crete an instance of AWS Dynamo DB
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
                "64227":
                        {
                            "Region"        :   "Region where Dynamo DB is hosted in AWS(us-east-2)",
                            "key-pair"      :   "key pair for backup gateway(AWS)",
                            "vpc"           :   "vpc for backup gateway(AWS)",
                            "subnet"        :   "subnet for backup gateway(AWS)",
                            "os_type"       :   OS type of the access node
                            "tables_count"(optional):   Number of dynamo tables to be created
                            "secondary_storage_name":   Type of storage using("MRR", "S3")
                            "secondary_storage_provider":   Name of storage provider("Azure", "OCI")
                        }
            }
    "Examaple":
        {
            "64227":
            {
                "Region":"us-east-2",
                "key-pair":"aws-key",
                "vpc":"vpc-xxxx",
                "subnet":"subnet-xxxx",
                "os-type":"Linux",
                "tables_count":3,
                "secondary_storage_name": "MRR",
                "secondary_storage_provider": "Azure"
            }
        }

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.config import get_config
from datetime import datetime
from cvpysdk.commcell import Commcell
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper
from Metallic.hubutils import HubManagement
from Application.CloudStorage.s3_helper import S3MetallicHelper, S3Helper
from Web.AdminConsole.Hub.Databases.databases import RAWSDynamoDB
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, DatabaseTypes
from Web.AdminConsole.Components.panel import Backup


class TestCase(CVTestCase):
    """Admin Console: DynamoDB agent: Secondary storage acceptance test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DynamoDB agent secondary storage acceptance test case from command center"
        self.tables = None
        self.byos_bucket_name = None
        self.backup_gateway = None
        self.cloud_account = None
        self.dynamodb_metallic_configuration = None
        self.stack_name = None
        self.hub_dashboard = None
        self.s3_helper = None
        self.s3_container_helper = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.dynamodb_helper = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
        self.config_files = None
        self.plan = None
        self.tenant_mgmt = None
        self.company_name = None
        self.tcinputs = {
            "Region": None,
            "key-pair": None,
            "vpc": None,
            "subnet": None,
            "secondary_storage_name": None,
            "secondary_storage_provider": None
        }

    def setup(self):
        """Method to setup the Test variables"""
        self.config_files = get_config()
        self.log.info(f"Started Executing {self.id} testcase")
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="Dynamo-DB-SS-Automation-AWS-SK")
        self.company_name = datetime.now().strftime("Dynamo-DB-SS-Automation-AWS-SK-%d-%B-%H-%M")
        email = datetime.now().strftime(f"metallic_Dynamo_db_AWS_SK_%H-%M-%S@{self.company_name}.com")
        tenant_username = self.tenant_mgmt.create_tenant(self.company_name, email)
        # tenant_username = "Dynamo-DB-SS-Automation-AWS-SK-27-July-14-58\metallic_Dynamo_db_AWS_SK_14-58-30"
        tenant_pswrd = self.config_files.Metallic.tenant_password
        self.commcell = Commcell(ring_hostname, tenant_username, tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(tenant_username, tenant_pswrd, stay_logged_in=True)
        self.s3_container_helper = S3Helper(self)
        self.plan = "AWSMetallicDynamoDBPlan"
        self.cloud_account = "DynamoDBsk"
        self.s3_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.hub_dashboard = Dashboard(self.admin_console, HubServices.database, DatabaseTypes.AWS)
        self.dynamodb_helper = AmazonDynamoDBCLIHelper(
            access_key=self.config_files.aws_access_creds.access_key,
            secret_key=self.config_files.aws_access_creds.secret_key)
        self.dynamodb_helper.initialize_client(self.tcinputs.get("Region"))
        self.dynamodb_metallic_configuration = RAWSDynamoDB(
            self.admin_console, aws_helper=self.dynamodb_helper,
            s3_helper=self.s3_helper)

    @test_step
    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.hub_dashboard.click_get_started()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()
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
            byos_storage_name = "awsmetallicdynamodbstorage" + datetime.now().strftime("sk%d%B%H%M").lower()
            self.byos_bucket_name = "awsmetallicdynamodbbucket" + datetime.now().strftime("sk%d%B%H%M").lower()
            self.backup_gateway = self.dynamodb_metallic_configuration.create_gateway(
                region=self.tcinputs.get("Region"), stack_name=self.stack_name,
                stack_params=params, gateway_os_type=self.tcinputs.get("os_type", "Linux"))
            job = self.dynamodb_metallic_configuration.upgrade_client_software(self.backup_gateway)
            self.wait_for_job_completion(job)
            self.log.info("Client software Upgrade successful.")
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.dynamodb_metallic_configuration.click_add_cloud_db()
            self.dynamodb_metallic_configuration.configure(
                region=self.tcinputs.get("Region", ""),
                byos_storage_name=byos_storage_name,
                byos_bucket_name=self.byos_bucket_name,
                cloud_account_name=self.cloud_account,
                plan_name=self.plan,
                secondary_storage_name=self.tcinputs.get("secondary_storage_name", ""),
                secondary_storage_provider=self.tcinputs.get("secondary_storage_provider", "")
            )
            self.database_instance = DBInstances(self.admin_console)
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_dynamodb_instance(self):
        """Navigates to dynamodb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'DynamoDB',
                                               self.cloud_account)

    @test_step
    def create_test_data(self, table_name, partition_key):
        """Creates dynamodb table and populates test data
        Args:
            table_name (str): Name of table to be created
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
        bkp_type = Backup.BackupType.INCR
        if "full" in level.lower():
            bkp_type = Backup.BackupType.FULL
        bkp = self.dynamodb_subclient.backup(bkp_type)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(bkp, level)

    @test_step
    def submit_in_place_restore(self):
        """Submits in place restore"""
        self.dynamodb_subclient.access_restore()
        mapping_dict = {
            self.tcinputs.get("Region"): self.tables
        }
        restore_panel_obj = self.dynamodb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'Sub_64227', copy="secondary")
        jobid = restore_panel_obj.same_account_same_region()
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")

    @test_step
    def cleanup(self):
        """Delete the Resources created in the automation"""
        for table in self.tables:
            self.dynamodb_helper.delete_dynamodb_table(table)
        self.s3_helper.delete_stack(stack_name=self.stack_name)
        s3_session = self.s3_container_helper.create_session_s3(
            access_key=self.config_files.aws_access_creds.access_key
            , secret_access_key=self.config_files.aws_access_creds.secret_key, region=self.tcinputs.get('Region'))
        self.s3_container_helper.delete_container_s3(s3_session, self.byos_bucket_name)

    @test_step
    def delete_tenant(self):
        """
        This deletes the tenant created
        """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)

    def run(self):
        """Main method to run test case"""
        try:
            self.tables = []
            self.log.info(
                f"Creating {self.tcinputs.get('tables_count', 3)} dynamo db tables in {self.tcinputs.get('Region', '')} region")
            for i in range(self.tcinputs.get("tables_count", 3)):
                table_name = f'TC_64227_{i}'
                self.create_test_data(table_name, 'id')
                self.tables.append(table_name)
            self.init_tc()
            self.db_instance_details.click_on_entity('default')
            self.dynamodb_subclient.disable_backup()
            self.navigate_to_dynamodb_instance()
            self.database_type = self.database_instance.Types.DYNAMODB
            add_subclient_obj = self.db_instance_details.click_add_subclient(self.database_type)
            subclient_content = {self.tcinputs.get("Region"): self.tables}
            add_subclient_obj.add_dynamodb_subclient('Sub_64227', self.plan, subclient_content)
            self.submit_backup(level='Full')
            for table_name in self.tables:
                self.dynamodb_helper.populate_dynamodb_table(table_name, 'id', 20)
            self.submit_backup()
            self.admin_console.refresh_page()
            sp = self.commcell.storage_policies.get(self.plan)
            self.log.info("Waiting for backup to finish")
            time.sleep(120)
            sp.run_aux_copy("secondary", self.backup_gateway)
            self.submit_in_place_restore()
            for table_name in self.tables:
                self.dynamodb_helper.validate_dynamodb_table(table_name, 'id', 20)
            self.admin_console.refresh_page()
            self.delete_tenant()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Cleanup the tables created on DynamoDB"""
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
