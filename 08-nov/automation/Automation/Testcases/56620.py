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

    navigate_to_docdb_instance() --  Navigates to DOCDB instance details page

    submit_backup()                 --  Submits docdb backup and returns snapshot name

    submit_restore()                --  Submits docdb restore

    wait_for_job_completion()       --  Waits for completion of job and gets the object
    once job completes

    create_docdb_cluster()       --  Creates docdb test cluster

    upgrade_client()                --  method to upgrade client

    cleanup()                       --  Cleans-up the docdb clusters/Instance created
    by testcase

    run()                           --  run function of this test case

Input Example:

    "testCases":
            {
                "56620":
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
from Application.CloudApps.amazon_helper import AmazonDocumentDBCLIHelper


class TestCase(CVTestCase):
    """Admin Console: DocumentDB agent: Basic acceptance test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DocumentDB agent acceptance test case from command center"
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
        self.docdb_helper = None
        self.docdb_subclient = None
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
            self.database_type = self.database_instance.Types.DOCUMENTDB
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.docdb_subclient = SubClient(self.admin_console)
            self.docdb_helper = AmazonDocumentDBCLIHelper(
                self.tcinputs['access_key'], self.tcinputs['secret_key'])
            self.log.info("Starting ec2 instance")
            if self.docdb_helper.ec2_state(self.tcinputs['EC2InstanceName'], self.tcinputs['EC2Region']).lower() != "running":
                self.docdb_helper.start_ec2_instance(self.tcinputs['EC2InstanceName'], self.tcinputs['EC2Region'])
                self.ec2_turned_on = True
            self.hyperv_helper = Hypervisors(self.admin_console)
            self.install = Install(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Sleeping for 2 mins before deleting clusters")
        time.sleep(120)
        if self.docdb_helper.is_cluster_present('ap-south-1', 'tc-56620', False):
            self.docdb_helper.delete_cluster('tc-56620', 'ap-south-1')
        if self.docdb_helper.is_cluster_present('ap-south-1', 'tc-56620-restore', False):
            self.docdb_helper.delete_cluster(
                'tc-56620-restore', 'ap-south-1')
        if self.ec2_turned_on:
            self.log.info("Stopping ec2 instance")
            self.docdb_helper.stop_ec2_instance(
                self.tcinputs['EC2InstanceName'], self.tcinputs['EC2Region'])

    @test_step
    def navigate_to_docdb_instance(self):
        """Navigates to docdb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(
            self.database_instance.Types.CLOUD_DB,
            'DocumentDB',
            self.tcinputs['cloud_account'])

    @test_step
    def submit_backup(self):
        """ Submits docdb backup and returns snapshot name

            Return:
                Returns snapshot name created for tc-56620 cluster

        """
        backup = self.docdb_subclient.backup(RBackup.BackupType.FULL)
        job_status = self.wait_for_job_completion(backup)
        if not job_status:
            raise CVTestStepFailure("docdb backup failed")
        snapshots = self.docdb_helper.get_all_manual_snapshots('ap-south-1')
        for snapshot in snapshots:
            if 'tc-56620' in snapshot:
                return snapshot
        raise Exception("Unable to find snapshot created by the backup")

    @test_step
    def submit_restore(self, snapshot_name):
        """ Submits docdb restore

            Args:
                snapshot_name(str): Name of the snapshot to be restored

        """
        self.docdb_subclient.access_restore()
        mapping_dict = {
            'ap-south-1': [snapshot_name]
        }
        restore_panel_obj = self.docdb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'Sub_56620')
        jobid = restore_panel_obj.same_account_same_region('tc-56620-restore')
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure("docdb restore failed")

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
    def create_docdb_cluster(self):
        """ Creates docdb test cluster """
        if not self.docdb_helper.is_cluster_present('ap-south-1', 'tc-56620', False):
            self.docdb_helper.create_docdb_cluster(
                region='ap-south-1',
                cluster_identifier='tc-56620',
                master_username='admin123',
                master_userpassword='Password123',
                wait_time_for_creation=20)
        self.log.info("Deleting all manual snapshots in the region: ap-south-1")
        self.docdb_helper.delete_all_manual_snapshots('ap-south-1')

    @test_step
    def upgrade_client(self):
        """ method to upgrade client """
        update_job = self.install.push_servicepack_and_hotfix([self.tcinputs['access_node']])
        self.wait_for_job_completion(job_obj=update_job)

    @test_step
    def cleanup(self):
        """ Cleans-up the docdb clusters/Instance created by testcase """
        self.navigator.navigate_to_db_instances()
        if self.database_instance.is_instance_exists(
                self.database_instance.Types.CLOUD_DB, "docdb", self.tcinputs['cloud_account']):
            self.database_instance.select_instance(
                self.database_instance.Types.CLOUD_DB,
                'docdb',
                self.tcinputs['cloud_account'])
            self.db_instance_details.delete_instance()
        self.navigator.navigate_to_hypervisors()
        if self.hyperv_helper.is_hypervisor_exists(self.tcinputs['cloud_account']):
            self.hyperv_helper.action_retire(self.tcinputs['cloud_account'])

    def run(self):
        """Main method to run test case"""
        try:
            self.cleanup()
            self.create_docdb_cluster()
            self.upgrade_client()
            self.navigator.navigate_to_db_instances()
            content = {'Asia Pacific (Mumbai) (ap-south-1)': ['tc-56620']}
            self.database_instance.add_documentdb_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'],
                auth_type="ACCESS_KEY", access_node=self.tcinputs['access_node'],
                credential_name=self.tcinputs['credential_name'],
                content=content)
            self.db_instance_details.click_on_entity('default')
            self.docdb_subclient.disable_backup()
            self.navigate_to_docdb_instance()
            add_subclient_obj = self.db_instance_details.click_add_subclient(
                self.database_type)
            add_subclient_obj.add_docdb_subclient('Sub_56620', self.tcinputs['plan'],
                                                     content=content)
            snapshot = self.submit_backup()
            self.navigate_to_docdb_instance()
            self.db_instance_details.click_on_entity('Sub_56620')
            self.submit_restore(snapshot)
            time.sleep(120)
            if not self.docdb_helper.is_cluster_present(
                    'ap-south-1', 'tc-56620-restore'):
                raise Exception("Restore did not create the cluster in the region")
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
