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

    tear_down()                     --  tear down method for testcase

    navigate_to_redshift_instance() --  Navigates to redshidt instance details page

    submit_backup()                 --  Submits RedShift backup and returns snapshot name

    submit_restore()                --  Submits RedShift restore

    wait_for_job_completion()       --  Waits for completion of job and gets the object
    once job completes

    create_redshift_cluster()       --  Creates redshift test cluster

    upgrade_client()                --  method to upgrade client

    cleanup()                       --  Cleans-up the redshift clusters/Instance created
    by testcase

    run()                           --  run function of this test case

Input Example:

    "testCases":
            {
                "58929":
                        {
                            "CloudAccountName":"CLOUD_ACCOUNT_NAME",
                            "PlanName":"PLAN_NAME",
                            "SecretKey":"SECRET_KEY",
                            "AccessKey":"ACCESS_KEY",
                            "EC2InstanceName":"INSTANCE_NAME",
                            "EC2Region":"REGION_NAME",
                            "access_node": "ACCESS_NODE_NAME",
                            "credential_name": "CREDENTIAL_NAME"
                        }
            }
"""
import time
from cvpysdk.deployment.install import Install
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonRedshiftCLIHelper


class TestCase(CVTestCase):
    """Admin Console: REDSHIFT agent: Basic acceptance test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "REDSHIFT agent acceptance test case from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.db_instance_details = None
        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "secret_key": None,
            "access_key": None,
            "EC2InstanceName": None,
            "EC2Region": None,
            "access_node": None,
            "credential_name": None
        }
        self.redshift_helper = None
        self.redshift_subclient = None
        self.hyperv_helper = None
        self.install = None
        self.ec2_turned_on = False

    def setup(self):
        """ Method to setup test variables """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.inputJSONnode['commcell']["commcellUsername"],
                password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_db_instances()
            self.database_instance = DBInstances(self.admin_console)
            self.database_type = self.database_instance.Types.REDSHIFT
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.redshift_subclient = SubClient(self.admin_console)
            self.redshift_helper = AmazonRedshiftCLIHelper(
                self.tcinputs['access_key'], self.tcinputs['secret_key'])
            self.log.info("Starting ec2 instance")
            if self.redshift_helper.ec2_state(self.tcinputs['EC2InstanceName'], self.tcinputs['EC2Region']).lower() != "running":
                self.redshift_helper.start_ec2_instance(self.tcinputs['EC2InstanceName'], self.tcinputs['EC2Region'])
                self.ec2_turned_on = True
            self.hyperv_helper = Hypervisors(self.admin_console)
            self.install = Install(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Sleeping for 2 mins before deleting clusters")
        time.sleep(120)
        if self.redshift_helper.is_cluster_present('ap-south-1', 'tc-58929', False):
            self.redshift_helper.delete_cluster('tc-58929', 'ap-south-1')
        if self.redshift_helper.is_cluster_present('ap-south-1', 'tc-58929-restore', False):
            self.redshift_helper.delete_cluster(
                'tc-58929-restore', 'ap-south-1')
        if self.ec2_turned_on:
            self.log.info("Stopping ec2 instance")
            self.redshift_helper.stop_ec2_instance(
                self.tcinputs['EC2InstanceName'], self.tcinputs['EC2Region'])

    @test_step
    def navigate_to_redshift_instance(self):
        """Navigates to redshift instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(
            self.database_instance.Types.CLOUD_DB,
            'Redshift',
            self.tcinputs['cloud_account'])

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
        snapshots = self.redshift_helper.get_all_manual_snapshots('ap-south-1')
        for snapshot in snapshots:
            if 'tc-58929' in snapshot:
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
            'ap-south-1': [snapshot_name]
        }
        restore_panel_obj = self.redshift_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'Sub_58929')
        jobid = restore_panel_obj.same_account_same_region('tc-58929-restore')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure("Redshift restore failed")

    @test_step
    def wait_for_job_completion(self, jobid=None, job_obj=None):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

            job_obj (obj): Job Object
        """
        if not job_obj:
            job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def create_redshift_cluster(self):
        """ Creates redshift test cluster """
        if not self.redshift_helper.is_cluster_present('ap-south-1', 'tc-58929', False):
            self.redshift_helper.create_redshift_cluster(
                region='ap-south-1',
                cluster_identifier='tc-58929',
                node_type='dc2.large',
                master_username='admin123',
                master_password='Password123',
                wait_time_for_creation=20)
        self.log.info("Deleting all manual snapshots in the region: ap-south-1")
        self.redshift_helper.delete_all_manual_snapshots('ap-south-1')

    @test_step
    def upgrade_client(self):
        """ method to upgrade client """
        update_job = self.install.push_servicepack_and_hotfix([self.tcinputs['access_node']])
        self.wait_for_job_completion(job_obj=update_job)

    @test_step
    def cleanup(self):
        """ Cleans-up the redshift clusters/Instance created by testcase """
        self.navigator.navigate_to_db_instances()
        if self.database_instance.is_instance_exists(
                self.database_instance.Types.CLOUD_DB, "Redshift", self.tcinputs['cloud_account']):
            self.database_instance.select_instance(
                self.database_instance.Types.CLOUD_DB,
                'Redshift',
                self.tcinputs['cloud_account'])
            self.db_instance_details.delete_instance()
        self.navigator.navigate_to_hypervisors()
        if self.hyperv_helper.is_hypervisor_exists(self.tcinputs['cloud_account']):
            self.hyperv_helper.action_retire(self.tcinputs['cloud_account'])

    def run(self):
        """Main method to run test case"""
        try:
            self.cleanup()
            self.create_redshift_cluster()
            self.upgrade_client()
            self.navigator.navigate_to_db_instances()
            content = {'Asia Pacific (Mumbai) (ap-south-1)': ['tc-58929']}
            self.database_instance.add_redshift_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'],
                auth_type="ACCESS_KEY", access_node=self.tcinputs['access_node'],
                credential_name=self.tcinputs['credential_name'],
                content=content)
            self.db_instance_details.click_on_entity('default')
            self.redshift_subclient.disable_backup()
            self.navigate_to_redshift_instance()
            add_subclient_obj = self.db_instance_details.click_add_subclient(
                self.database_type)
            add_subclient_obj.add_redshift_subclient('Sub_58929', self.tcinputs['plan'],
                                                     content=content)
            snapshot = self.submit_backup()
            self.navigate_to_redshift_instance()
            self.db_instance_details.click_on_entity('Sub_58929')
            self.submit_restore(snapshot)
            time.sleep(120)
            if not self.redshift_helper.is_cluster_present(
                    'ap-south-1', 'tc-58929-restore'):
                raise Exception("Restore did not create the cluster in the region")
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
