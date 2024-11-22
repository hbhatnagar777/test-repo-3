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

    initial_setup()             --  method to create an instance of AWS RDS
                                    in the metallic

    check_instance_status()      --  Method to check is instance present, and it's state

    start_rds_instance()           --  method to create the RDS instance

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
                "64159":
                        {
                            "Region": "Region where RDS is hosted in AWS(us-east-2)",
                            "key-pair":"key pair for backup gateway(AWS)",
                            "vpc":"vpc for backup gateway(AWS)",
                            "subnet":"subnet for backup gateway(AWS)",
                            "os_type":  "Type of OS access node to be created",
                            "instance_identifier":   "Name of the RDS instance_identifier"
                        }
            }
    "Example":
        {
            "64159":
            {
                "Region":"us-east-2",
                "key-pair":"aws-key",
                "vpc":"vpc-xxxx",
                "subnet":"subnet-xxxx",
                "os-type":"Linux",
                "Instance_identifier":"xxxxxx"

            }
        }

"""

import ast
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
from Web.AdminConsole.Hub.Databases.databases import RAWSRDS
from Web.AdminConsole.Hub.dashboard import Dashboard
from Application.CloudStorage.s3_helper import S3MetallicHelper, S3Helper
from Application.CloudApps.amazon_helper import AmazonRDSCLIHelper
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.panel import Backup


class TestCase(CVTestCase):
    """Class for executing """
    test_step = TestStep()

    def __init__(self):
        """Initialize the class"""
        super(TestCase, self).__init__()
        self.name = "Test Case for RDS Instance from Metallic Command Center on AWS cloud"
        self.tablespace_name = 'CV_64159'
        self.rds_subclient = None
        self.rds_helper = None
        self.byos_bucket_name = None
        self.stack_name = None
        self.s3_helper = None
        self.s3_container_helper = None
        self.rds_metallic_configuration = None
        self.hub_dashboard = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tenant_mgmt = None
        self.company_name = None
        self.tenant_username = None
        self.tenant_pswrd = None
        self.db_instance_details = None
        self.created_snapshot = None
        self.config_files = None
        self.tcinputs = {
            "Region": None,
            "key-pair": None,
            "vpc": None,
            "subnet": None,
            "os_type": None,
            "Instance_identifier": None
        }

    def setup(self):
        """ Method to setup test variables"""
        self.config_files = get_config()
        self.log.info(f"Started Executing {self.id} testcase")
        ring_hostname = self.tcinputs.get("RingHostname", self.commcell.webconsole_hostname)
        self.tenant_mgmt = HubManagement(self, ring_hostname)
        self.tenant_mgmt.delete_companies_with_prefix(prefix="rds-ins-Automation-AWS-SK")
        self.company_name = datetime.now().strftime("rds-ins-Automation-AWS-SK-%d-%B-%H-%M")
        email = datetime.now().strftime(f"metallic_rds_ins_AWS_SK_%H-%M-%S@{self.company_name}.com")
        self.tenant_username = self.tenant_mgmt.create_tenant(self.company_name, email)
        self.tenant_pswrd = self.config_files.Metallic.tenant_password
        self.commcell = Commcell(ring_hostname, self.tenant_username, self.tenant_pswrd)

        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, ring_hostname)
        self.admin_console.login(self.tenant_username, self.tenant_pswrd, stay_logged_in=True)
        self.s3_container_helper = S3Helper(self)
        self.s3_helper = S3MetallicHelper(self.tcinputs["Region"])
        self.hub_dashboard = Dashboard(self.admin_console, HubServices.database, DatabaseTypes.AWS)
        self.rds_helper = AmazonRDSCLIHelper(
            secret_key=self.config_files.aws_access_creds.secret_key,
            access_key=self.config_files.aws_access_creds.access_key)
        self.rds_metallic_configuration = RAWSRDS(
            self.admin_console,
            s3_helper=self.s3_helper,
            aws_helper=self.rds_helper)
    @test_step
    def initial_setup(self):
        """initial setup method"""
        self.start_rds_instance()
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.click_new_configuration()
        self.rds_metallic_configuration.select_trial_subscription()
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
        self.stack_name = "awsmetallicrds" + datetime.now().strftime("sk%d%B%H%M")
        byos_storage_name = "awsmetallicrdsstorage" + datetime.now().strftime("sk%d%B%H%M").lower()
        self.byos_bucket_name = "awsmetallicrdsbucket" + datetime.now().strftime("sk%d%B%H%M").lower()
        cloud_account = "RDSInsSK"
        backup_gateway_name = self.rds_metallic_configuration.create_gateway(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params, gateway_os_type=self.tcinputs.get("os_type") or "Linux")
        job = self.rds_metallic_configuration.upgrade_client_software(backup_gateway_name)
        self.wait_for_job_completion(job)
        self.log.info("Client software Upgrade successful.")
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.rds_metallic_configuration.click_add_cloud_db()
        self.rds_metallic_configuration.configure(
            region=self.tcinputs.get("Region"), stack_name=self.stack_name,
            stack_params=params,
            byos_storage_name=byos_storage_name,
            byos_bucket_name=self.byos_bucket_name,
            cloud_account_name=cloud_account,
            plan_name="AWSMetallicRDSPlan",
            content=[self.tcinputs.get("instance_identifier")])
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.rds_subclient = SubClient(self.admin_console)

    @test_step
    def check_instance_state(self):
        """
        Check's the instance state is it ready to start

        Returns:
            bool -- State of the RDS instance
        """
        instance_present = self.rds_helper.is_instance_present(
            self.tcinputs.get("Region"), self.tcinputs.get("instance_identifier"), availability=False)
        instance_available_state = self.rds_helper.is_instance_present(
            self.tcinputs.get("Region"), self.tcinputs.get("instance_identifier"))
        return instance_present and not instance_available_state

    @test_step
    def start_rds_instance(self):
        """ Creates RDS test instance """
        if self.check_instance_state():
            self.rds_helper.start_rds_instance(
                region=self.tcinputs.get("Region"),
                instance_identifier=self.tcinputs.get("instance_identifier")
            )

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

        Returns:
            bool    -   boolean specifying whether the job had finished or not
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def submit_backup(self):
        """
        Submits Amazon RDS backup and validates it

        Raises:
            Exception:  If the backup fails

        """
        bkp = self.rds_subclient.backup(backup_type=Backup.BackupType.FULL)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of RDS instance group failed")
        job_obj = self.commcell.job_controller.get(bkp)
        if job_obj.size_of_application <= 0:
            raise CVTestStepFailure("Backup validation failed, size of application is zero")

    @test_step
    def submit_restore(self, instance_name):
        """Submits restore of RDS instance
        Args:
            instance_name   (str)   --  The name of RDS instance to restore

        Returns:
            (str)   --  Name of the snapshot that was used by restore

        Raises:
            Exception: If restore job fails
        """
        self.rds_subclient.access_restore()
        mapping_dict = {
            self.tcinputs.get("Region"): instance_name
        }
        restore_panel_obj = self.rds_subclient.restore_files_from_multiple_pages(
            DBInstances.Types.RDS, mapping_dict, 'default', rds_agent=True)
        jobid = restore_panel_obj.restore(instance_name + 'restored')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")
        self.admin_console.refresh_page()
        self.admin_console.select_hyperlink(self.tcinputs.get("Region"))
        snapshot = self.rds_subclient.get_items_in_browse_page('Snapshot name')
        return snapshot[0]

    @test_step
    def delete_tenant(self):
        """
        This deletes the tenant created
        """
        self.tenant_mgmt.deactivate_tenant(self.company_name)
        self.tenant_mgmt.delete_tenant(self.company_name)
    @test_step
    def cleanup(self):
        """Delete the Resources, Tables and Tenants created by test case"""
        self.rds_helper.delete_snapshot(self.created_snapshot, self.tcinputs.get("Region"))
        self.rds_helper.delete_cluster(self.tcinputs.get("instance_identifier") + 'restored',
                                              self.tcinputs.get("Region"))
        self.s3_helper.delete_stack(stack_name=self.stack_name)
        s3_session = self.s3_container_helper.create_session_s3(
            access_key=self.config_files.aws_access_creds.access_key
            , secret_access_key=self.config_files.aws_access_creds.secret_key, region=self.tcinputs.get('Region'))
        self.s3_container_helper.delete_container_s3(s3_session, self.byos_bucket_name)
        self.rds_helper.stop_rds_instance(self.tcinputs.get("Region"), self.tcinputs.get("instance_identifier"))

    def run(self):
        """
        Main method to run test case
        Raises:
            Exception: If restore validation fails
        """

        try:
            self.initial_setup()
            self.db_instance_details.click_on_entity('default')
            self.submit_backup()
            self.admin_console.refresh_page()
            self.created_snapshot = self.submit_restore(self.tcinputs.get("instance_identifier"))
            self.log.info("Waiting to get restored instance available")
            time.sleep(480)
            if not self.rds_helper.is_instance_present(
                    self.tcinputs.get("Region"), self.tcinputs.get("instance_identifier") + 'restored'):
                raise Exception("Restore did not create the instance in the region")
            self.log.info("instance restored successfully")
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
