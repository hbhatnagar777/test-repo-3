# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"58157": {
          "cloud_account": "XXXXX",
          "plan": "plan1",
          "access_key": "XXXX",
          "secret_key": "XXXX"

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    tear_down()     --  Tear down method of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.browse import Browse
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper


class TestCase(CVTestCase):
    """Admin Console: Validate multiple entry points for DynamoDB"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DynamoDB: Validate multiple entry points for backup and restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.dynamodb_helper = None
        self.dynamodb_instance = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
        self.table_object = None

        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "secret_key": None,
            "access_key": None
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
            self.database_type = self.database_instance.Types.DYNAMODB
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)
            self.table_object = Rtable(self.admin_console)
            self.dynamodb_helper = AmazonDynamoDBCLIHelper(
                self.tcinputs['secret_key'], self.tcinputs['access_key'])
            self.dynamodb_helper.initialize_client('us-east-2')

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_dynamodb_instance(self):
        """Navigates to dynamodb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'DynamoDB',
                                               self.tcinputs['cloud_account'])

    @test_step
    def create_test_data(self, table_name, partition_key):
        """Creates dynamodb table and poulates test data
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
    def submit_backup(self):
        """Submits backup from Instances tab-> Instance -> Actions"""

        self.table_object.access_action_item(self.tcinputs['cloud_account'],
                                             self.admin_console.props['label.globalActions.backup'])
        bkp = Backup(self.admin_console).submit_backup(backup_type=Backup.BackupType.FULL)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")

    @test_step
    def submit_restore(self, table_name):
        """Submits restore from Instances tab-> Instance->Actions
        Args:
            table_name  (str)-   Table to be restored

        """
        self.table_object.access_action_item(
            self.tcinputs['cloud_account'],
            self.admin_console.props['label.globalActions.restore'])
        mapping_dict = {
            'us-east-2': table_name
        }
        restore_panel_obj = self.dynamodb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'DynamoDB')
        jobid = restore_panel_obj.same_account_same_region()
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")
        """Submits restore from Databases tab-> Table Name"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.access_databases_tab()
        self.table_object.access_action_item(
            self.tcinputs['cloud_account'],
            self.admin_console.props['label.globalActions.restore'])
        browse = Browse(self.admin_console)
        browse.submit_for_restore()
        self.admin_console.refresh_page()

    @test_step
    def cleanup(self):
        """Delete the Instances and subclients created by test case"""
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.delete_instance()

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            table_name = 'TC_58157'
            self.create_test_data(table_name, 'id')
            self.init_tc()
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB',self.tcinputs['cloud_account']):
                self.cleanup()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['cloud_account'],
                self.tcinputs['plan'],
                adjust_read_capacity=10,
                content={'US East (Ohio) (us-east-2)':[table_name]})
            self.navigator.navigate_to_db_instances()
            self.submit_backup()
            self.admin_console.refresh_page()
            self.submit_restore(table_name)
            self.dynamodb_helper.validate_dynamodb_table(table_name, 'id', 10)
            self.admin_console.refresh_page()
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Cleanup the dynamodb tables"""
        self.dynamodb_helper.delete_dynamodb_table('TC_58157')
