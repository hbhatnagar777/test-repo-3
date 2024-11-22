# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
 "59827": {
          "cloud_account": "XXXX",
          "plan": "XXXX",
          "access_key": "XXXX",
          "secret_key": "XXXX",
          "rds_instance": "XXXX",
          "region": "US East (Virginia) (us-east-1)",
          "http_proxy_server": '172.16.0.0'
          "http_proxy_port": 808,
          "access_node_name": client_1
        }

Note: The following needs to be pre-configured before running this test case:

1. On the machine which will be used as http proxy server, ccproxy or an equivalent software
should be installed and http proxy port should be open

2. On the automation controller, config.json file under C:\Program Files\Commvault\
ContentStore\Automation\CoreUtils\Templates must be populated with the endpoints
to block in list format. These entries will be copied to access node during test case run

Add loopback address or any incorrect IP so that connections from access node don't work
        Example :
        "BlockCloudEndPoints": {
            "endpoints": ["127.0.0.1     dynamodb.ap-south-1.amazonaws.com",
            "127.0.0.1     dynamodb.ap-southeast-1.amazonaws.com"]
        }

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    tear_down()     --  Tear down method of this test case
"""
from time import sleep
from cvpysdk import job
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Application.CloudApps.amazon_helper import AmazonRDSCLIHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """HTTP proxy configuration and validation for Amazon RDS"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "HTTP proxy configuration and validation for Amazon RDS"
        self.browser = None
        self.admin_console = None
        self.dbhelper = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.rds_helper = None
        self.rds_subclient = None
        self.db_instance_details = None
        self.region = ""
        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "secret_key": None,
            "access_key": None,
            "rds_instance": None,
            "region": None,
            "http_proxy_server": None,
            "http_proxy_port": None,
            "access_node_name": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.database_instance = DBInstances(self.admin_console)
            self.database_type = self.database_instance.Types.RDS
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.rds_subclient = SubClient(self.admin_console)
            self.rds_helper = AmazonRDSCLIHelper(
                self.tcinputs['access_key'], self.tcinputs['secret_key'])
            input_region = self.tcinputs['region'].split()[-1]
            self.region = input_region[1:-1]
            self.dbhelper = DbHelper(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

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
        """Submits Amazon RDS backup and validates it"""
        bkp = self.rds_subclient.backup(backup_type=Backup.BackupType.FULL)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of RDS instance group failed")
        job_obj = job.Job(self.commcell, bkp)
        if job_obj.size_of_application <= 0:
            raise CVTestStepFailure("Backup validation failed, size of application is zero")

    @test_step
    def submit_restore(self, instance_name):
        """Submits restore of RDS instance
        Args:
            instance_name   (str)   --  The name of RDS instance to restore

        Returns:
            (str)   --  Name of the snapshot that was used by restore
        """
        self.rds_subclient.access_restore()
        mapping_dict = {
            self.region: instance_name
        }
        restore_panel_obj = self.rds_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'default', rds_agent=True)
        jobid = restore_panel_obj.restore(instance_name+'restored')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")
        self.admin_console.refresh_page()
        self.admin_console.select_hyperlink(self.region)
        snapshot = self.rds_subclient.get_items_in_browse_page('Snapshot name')
        return snapshot[0]

    @test_step
    def validate_rds_instance(self, instance_name):
        """Waits for 8 minutes after restore and validates if RDS instance
        was created successfully after restore and status is available.

        Args:
            instance_name   (str)   --  The name of RDS instance to validate
        """
        sleep(480)
        instances = self.rds_helper.discover_region_clusters(
            region=self.region)
        if instance_name not in instances[self.region]:
            raise CVTestStepFailure("Instance not found after restore or not in available state")

    @test_step
    def delete_rds_instance(self):
        """Delete the Instances and subclients created by test case"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'RDS',
                                               self.tcinputs['cloud_account'])

        self.db_instance_details.delete_instance()

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            instance_name = self.tcinputs['rds_instance']
            content = {self.tcinputs['region']: [instance_name]}
            if self.database_instance.is_instance_exists(self.database_type, 'RDS',
                                                         self.tcinputs['cloud_account']):
                self.delete_rds_instance()
            self.dbhelper.set_http_proxy_for_cs(self.tcinputs['http_proxy_server'],
                                                self.tcinputs['http_proxy_port'])
            self.dbhelper.block_cloud_endpoint_on_accessnode(self.tcinputs['access_node_name'])
            self.database_instance.add_rds_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'], content=content)
            self.db_instance_details.click_on_entity('default')
            self.submit_backup()
            self.admin_console.refresh_page()
            created_snapshot = self.submit_restore(instance_name)
            self.validate_rds_instance(instance_name+'restored')
            self.rds_helper.delete_snapshot(created_snapshot, self.region)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Delete the restored RDS instance"""
        self.dbhelper.cleanup_http_proxy_config(self.tcinputs['access_node_name'])
        self.rds_helper.delete_cluster(self.tcinputs['rds_instance']+'restored', self.region)
