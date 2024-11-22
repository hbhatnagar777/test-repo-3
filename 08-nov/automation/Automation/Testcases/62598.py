"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    initial_setup()             --  method to crete an instance of AWS Redshift
                                    in the metallic

    create_redshift_cluster     --  method to create the redshift cluster

    wait_for_job_completion()   --  waits for completion of job

    submit_backup()             -- method to run backup

    submit_restore()            --  method to run restore in place

    delete_tenant()             --  method to deactivate and delete the tenant

    cleanup()                   --  method to clean up all testcase created changes

    run()                       --  run function of this test case

    tear_down()                 --  tear down method for testcase



Input Example:

    "testCases":
            {
                "62598":
                        {
                            "Region": "Region where Redshift is hosted in AWS(us-east-2)",
                            "key-pair":"key pair for backup gateway(AWS)",
                            "vpc":"vpc for backup gateway(AWS)",
                            "subnet":"subnet for backup gateway(AWS)",
                            "cloud_account": "name of the cloud account to be created"
                            "os_type":  "Type of OS access node to be created"
                        }
            }
    "Examaple":
        {
            "62598":
            {
                "Region":"us-east-2",
                "key-pair":"aws-key",
                "vpc":"vpc-xxxx",
                "subnet":"subnet-xxxx",
                "os-type":"Linux"

            }
        }

"""

import ast
import time
import string
import random
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
from Web.AdminConsole.Hub.Databases.databases import RAWSRedshift
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Application.CloudStorage.s3_helper import S3MetallicHelper, S3Helper
from Application.CloudApps.amazon_helper import AmazonRedshiftCLIHelper
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """Class for executing """
    test_step = TestStep()

    def __init__(self):
        """Initialize the class"""
        super(TestCase, self).__init__()
        self.redshift_subclient = None
        self.redshift_helper = None
        self.backup_gateway = None
        self.byos_bucket_name = None
        self.byos_storage_name = None
        self.stack_name = None
        self.s3_helper = None
        self.s3_container_helper = None
        self.gateway_created = None
        self.redshift_metallic_configuration = None
        self.database_type = None
        self.hub_dashboard = None
        self.name = "Test Case for RedShift from Metallic Command Center on AWS cloud"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_62598'
        self.tenant_mgmt = None
        self.company_name = None
        self.company_email = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.email = None
        self.tenant_created = None
        self.app_type = None
        self.service = None
        self.vendor = None
        self.database_instances = None
        self.page_container = None
        self.db_instance_details = None
        self.config_files = get_config()
        self.service_catalogue = None

    def setup(self):
        """ Method to setup test variables"""
        self.log.info(f"Started Executing {self.id} testcase")
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="redshift-Automation-AWS-SK")
        self.company_name = datetime.now().strftime("redshift-Automation-AWS-SK-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_redshift_AWS_SK_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = self.config_files.Metallic.tenant_password
        self.tenant_created = True
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.database_type = DBInstances.Types.REDSHIFT
        self.service = HubServices.database
        self.app_type = DatabaseTypes.AWS
        self.s3_container_helper = S3Helper(self)
        self.s3_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.page_container = PageContainer(self.admin_console)
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.vendor = "Amazon Web Services"
        self.redshift_helper = AmazonRedshiftCLIHelper(
            secret_key=self.config_files.aws_access_creds.secret_key,
            access_key=self.config_files.aws_access_creds.access_key)
        self.redshift_metallic_configuration = RAWSRedshift(
            self.admin_console,
            s3_helper=self.s3_helper,
            aws_helper=self.redshift_helper)

    def initial_setup(self):
        """initial setup method"""
        if self.redshift_helper.is_cluster_present(self.tcinputs.get("Region"), 'tc-62598', False):
            self.redshift_helper.delete_cluster("tc-62598", self.tcinputs.get("Region"))
        if self.redshift_helper.is_cluster_present(self.tcinputs.get("Region"), 'tc-62598-restore', False):
            self.redshift_helper.delete_cluster("tc-62598-restore", self.tcinputs.get("Region"))
        self.create_redshift_cluster()
        self.hub_dashboard.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(self.service.value, id="Amazon Web Services")
        self.redshift_metallic_configuration.select_trial_subscription()

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
        self.stack_name = "awsmetallicredshift" + datetime.now().strftime("sk%d%B%H%M")
        self.byos_storage_name = "awsmetallicredshiftstorage" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.byos_bucket_name = "awsmetallicredshiftbucket" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.backup_gateway = self.redshift_metallic_configuration.create_gateway(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params, gateway_os_type=self.tcinputs.get("os_type") or "Linux")
        job = self.redshift_metallic_configuration.upgrade_client_software(self.backup_gateway)
        self.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.redshift_metallic_configuration.click_add_cloud_db()

        self.redshift_metallic_configuration.configure(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params,
            byos_storage_name=self.byos_storage_name,
            byos_bucket_name=self.byos_bucket_name,
            cloud_account_name=self.tcinputs.get("cloud_account"),
            plan_name="AWSMetallicredshiftPlan",
            content=["tc-62598"])
        self.gateway_created = True
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.redshift_subclient = SubClient(self.admin_console)

    @test_step
    def create_redshift_cluster(self):
        """ Creates redshift test cluster """
        if not self.redshift_helper.is_cluster_present(
                self.tcinputs.get("Region"),
                'tc-62598', False):
            st = string.ascii_letters + string.digits
            ra_string = ''.join(random.choice(st) for _ in range(15))
            ra_string = f"Aa1{ra_string}"
            self.redshift_helper.create_redshift_cluster(
                region=self.tcinputs.get("Region"),
                cluster_identifier='tc-62598',
                node_type='dc2.large',
                master_username='admin123',
                master_password=ra_string,
                wait_time_for_creation=20)
        self.log.info(f"Deleting all manual snapshots in the region: {self.tcinputs.get('Region')}")
        self.redshift_helper.delete_all_manual_snapshots(self.tcinputs.get("Region"))

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def submit_backup(self):
        """ Submits RedShift backup and returns snapshot name

            Return:
                Returns snapshot name created for tc-58929 cluster

        """
        backup = self.redshift_subclient.backup(RBackup.BackupType.FULL)
        job_status = self.wait_for_job_completion(backup)
        if not job_status:
            raise CVTestStepFailure("Redshift backup failed")
        snapshots = self.redshift_helper.get_all_manual_snapshots(self.tcinputs.get("Region"))
        for snapshot in snapshots:
            if 'tc-62598' in snapshot:
                return snapshot
        raise Exception("Unable to find snapshot created by the backup")

    @test_step
    def submit_restore(self, snapshot_name):
        """ Submits RedShift restore

            Args:
                snapshot_name(str): Name of the snapshot to be restored

        """
        self.redshift_subclient.access_restore()
        mapping_dict = {
            self.tcinputs.get("Region"): [snapshot_name]
        }
        restore_panel_obj = self.redshift_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'default')
        jobid = restore_panel_obj.same_account_same_region('tc-62598-restore')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure("Redshift restore failed")

    def delete_tenant(self):
        """
        This deletes the tenant created
        """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)

    def cleanup(self):
        """Delete the Resources, Tables and Tenants created by test case"""
        if self.redshift_helper.is_cluster_present(self.tcinputs.get("Region"), 'tc-62598', False):
            self.redshift_helper.delete_cluster("tc-62598", self.tcinputs.get("Region"))
        self.redshift_helper.delete_all_manual_snapshots(self.tcinputs.get("Region"))
        self.s3_helper.delete_stack(stack_name=self.stack_name)
        s3_session = self.s3_container_helper.create_session_s3(
            access_key=self.config_files.aws_access_creds.access_key
            , secret_access_key=self.config_files.aws_access_creds.secret_key, region=self.tcinputs.get('Region'))
        self.s3_container_helper.delete_container_s3(s3_session, self.byos_bucket_name)
        if self.redshift_helper.is_cluster_present(self.tcinputs.get("Region"), 'tc-62598-restore', False):
            self.redshift_helper.delete_cluster("tc-62598-restore", self.tcinputs.get("Region"))

    def run(self):
        """Main method to run test case"""
        try:
            self.log.info("started main run func")
            self.initial_setup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.db_instance_details.click_on_entity('Redshift [us-east-2]')
            self.page_container.select_entities_tab()
            self.db_instance_details.click_on_entity('default')
            snapshot_name = self.submit_backup()
            self.admin_console.refresh_page()
            self.submit_restore(snapshot_name)
            self.log.info("waiting to get restored cluster to available state")
            time.sleep(120)
            if not self.redshift_helper.is_cluster_present(
                    self.tcinputs.get("Region"), 'tc-62598-restore'):
                raise Exception("Restore did not create the cluster in the region")
            self.log.info("Cluster restored successfully")
            self.delete_tenant()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """
        Function to run after automation execution
        """
        self.log.info("started teardown")
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
