"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    initial_setup()             --  method to crete an instance of AWS DocumentDB
                                    in the metallic

    create_document_db_cluster() --  Method to create the check and create the DocumentDB

    create_document_db_instance() --  Method to create the DocumentDB instance under a given cluster

    wait_for_job_completion()   --  waits for completion of job

    submit_backup()             -- method to run backup

    submit_restore()            --  method to run restore

    delete_tenant()             --  method to deactivate and delete the tenant

    cleanup()                   --  method to clean up all testcase created changes

    run()                       --  run function of this test case

    tear_down()                 --  tear down method for testcase



Input Example:

    "testCases":
            {
                "62600":
                        {
                            "Region": "Region where DocumentDB is hosted in AWS(us-east-2)",
                            "key-pair":"key pair for backup gateway(AWS)",
                            "vpc":"vpc for backup gateway(AWS)",
                            "subnet":"subnet for backup gateway(AWS)",
                            "os_type":  "Type of OS the access node should be"
                        }
            }
    "Examaple":
    {
        "62600":
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
import random
import string
import time
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
from Web.AdminConsole.Hub.Databases.databases import RAWSDocumentDB
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Application.CloudStorage.s3_helper import S3MetallicHelper, S3Helper
from Application.CloudApps.amazon_helper import AmazonDocumentDBCLIHelper
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup


class TestCase(CVTestCase):
    """Class for executing """
    test_step = TestStep()

    def __init__(self):
        """Initialize the class"""
        super(TestCase, self).__init__()
        self.documentdb_subclient = None
        self.documentdb_helper = None
        self.backup_gateway = None
        self.byos_bucket_name = None
        self.byos_storage_name = None
        self.stack_name = None
        self.s3_helper = None
        self.s3_container_helper = None
        self.gateway_created = None
        self.documentdb_metallic_configuration = None
        self.database_type = None
        self.hub_dashboard = None
        self.name = "Test Case for DocumentDB from Metallic Command Center on AWS cloud"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_62600'
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
        self.db_instance_details = None
        self.cloud_account = None
        self.config_files = get_config()
        self.service_catalogue= None

    def setup(self):
        """ Method to setup test variables"""
        self.log.info(f"Started Executing {self.id} testcase")
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="Document-DB-Automation-AWS-SK")
        self.company_name = datetime.now().strftime("Document-DB-Automation-AWS-SK-%d-%B-%H-%M")
        self.email = datetime.now().strftime(f"metallic_Document_db_AWS_SK_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, self.email)
        self.tenant_pswrd = self.config_files.Metallic.tenant_password
        self.tenant_created = True
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.database_type = DBInstances.Types.DOCUMENTDB
        self.cloud_account = "DocumentDBsk"
        self.service = HubServices.database
        self.app_type = DatabaseTypes.AWS
        self.s3_container_helper = S3Helper(self)
        self.s3_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.vendor = "Amazon Web Services"
        self.documentdb_helper = AmazonDocumentDBCLIHelper(
            secret_key=self.config_files.aws_access_creds.secret_key,
            access_key=self.config_files.aws_access_creds.access_key)
        self.documentdb_metallic_configuration = RAWSDocumentDB(
            self.admin_console,
            s3_helper=self.s3_helper,
            aws_helper=self.documentdb_helper)
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)

    def initial_setup(self):
        """initial setup method"""
        self.create_document_db_cluster()
        self.documentdb_helper.delete_cluster("tc-62600-restore", self.tcinputs.get("Region"))
        self.hub_dashboard.click_get_started()
        self.service_catalogue.choose_service_from_service_catalogue(self.service.value, id="Amazon Web Services")
        self.documentdb_metallic_configuration.select_trial_subscription()
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
        self.stack_name = "awsmetallicdocumentdb" + datetime.now().strftime("sk%d%B%H%M")
        self.byos_storage_name = "awsmetallicdocumentdbstorage" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.byos_bucket_name = "awsmetallicdocumentdbbucket" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.backup_gateway = self.documentdb_metallic_configuration.create_gateway(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params, gateway_os_type=self.tcinputs.get("os_type") or "Linux")
        job = self.documentdb_metallic_configuration.upgrade_client_software(self.backup_gateway)
        self.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.documentdb_metallic_configuration.click_add_cloud_db()

        self.documentdb_metallic_configuration.configure(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params, gateway_os_type="Linux",
            byos_storage_name=self.byos_storage_name,
            byos_bucket_name=self.byos_bucket_name,
            cloud_account_name=self.cloud_account,
            plan_name="AWSMetallicDocumentDBPlan",
            content=["tc-62600"])
        self.admin_console.refresh_page()
        self.gateway_created = True
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.documentdb_subclient = SubClient(self.admin_console)

    @test_step
    def create_document_db_cluster(self):
        """Creates DocumentDB cluster"""
        if not self.documentdb_helper.is_cluster_present(
                region=self.tcinputs.get("Region"),
                cluster_identifier="tc-62600",
                availability=True, turn_on=True):
            st = string.ascii_letters + string.digits
            ra_string = ''.join(random.choice(st) for _ in range(15))
            ra_string = f"Aa1{ra_string}"
            self.documentdb_helper.create_docdb_cluster(
                region=self.tcinputs.get("Region"),
                cluster_identifier="tc-62600",
                master_username="admin123",
                master_userpassword=ra_string)
            self.create_document_db_instance()
        self.log.info(f"Deleting all DocumentDB manual snapshots of tc-62600 cluster")
        self.documentdb_helper.delete_docdb_snapshots_of_cluster(
            self.tcinputs.get("Region"), "tc-62600")

    def create_document_db_instance(self):
        """Creates the instance of Doc DB under tc-62600 cluster"""
        self.documentdb_helper.create_docdb_instance(
            region=self.tcinputs.get("Region"),
            instance_identifier="tc-62600-instance",
            instance_class="db.t4g.medium",
            cluster_identifier="tc-62600")

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
        """ Submits DocumentDB backup and returns snapshot name

            Return:
                DocumentDB snapshot name created for tc-62600 cluster

        """
        backup = self.documentdb_subclient.backup(RBackup.BackupType.FULL)
        job_status = self.wait_for_job_completion(backup)
        if not job_status:
            raise CVTestStepFailure("DocumentDB backup failed")
        snapshot = self.documentdb_helper.get_manual_snapshot_of_cluster(self.tcinputs.get("Region"), "tc-62600")
        if snapshot != None:
            return snapshot
        raise Exception("Unable to find snapshot created by the backup")

    @test_step
    def submit_restore(self, snapshot_name):
        """ Submits RedShift restore

            Args:
                snapshot_name(str): Name of the snapshot to be restored

        """
        self.documentdb_subclient.access_restore()
        mapping_dict = {
            self.tcinputs.get("Region"): [snapshot_name]
        }
        restore_panel_obj = self.documentdb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'default')
        jobid = restore_panel_obj.same_account_same_region('tc-62600-restore')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure("DocumentDB restore failed")

    def delete_tenant(self):
        """
        This deletes the tenant created
        """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)

    def cleanup(self):
        """Delete the Resources, Tables and Tenants created by test case"""
        self.documentdb_helper.delete_docdb_snapshots_of_cluster(self.tcinputs.get("Region"), "tc-62600")
        self.s3_helper.delete_stack(stack_name=self.stack_name)
        s3_session = self.s3_container_helper.create_session_s3(
            access_key=self.config_files.aws_access_creds.access_key
            , secret_access_key=self.config_files.aws_access_creds.secret_key, region=self.tcinputs.get('Region'))
        self.s3_container_helper.delete_container_s3(s3_session, self.byos_bucket_name)
        self.documentdb_helper.delete_cluster("tc-62600", self.tcinputs.get("Region"))
        self.documentdb_helper.delete_cluster("tc-62600-restore", self.tcinputs.get("Region"))

    def run(self):
        """Main method to run test case"""
        try:
            self.initial_setup()
            self.db_instance_details.click_on_entity('default')
            snapshot_name = self.submit_backup()
            self.admin_console.refresh_page()
            self.submit_restore(snapshot_name)
            time.sleep(120)
            if not self.documentdb_helper.is_cluster_present(
                    self.tcinputs.get("Region"), 'tc-62600-restore'):
                raise Exception("Restore did not create the cluster in the region")
            self.log.info("Cluster restored successfully")
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
