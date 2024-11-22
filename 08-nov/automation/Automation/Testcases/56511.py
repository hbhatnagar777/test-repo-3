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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper


class TestCase(CVTestCase):
    """Admin Console: Backup with Adjust read capacity enabled at table group"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DynamoDB: Backup with Adjust read capacity enabled at table group"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.database_type = None
        self.dynamodb_helper = None
        self.dynamodb_instance = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
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
        self.dynamodb_helper.create_dynamodb_table(table_name, partition_key, )
        self.dynamodb_helper.populate_dynamodb_table(table_name, partition_key, 50)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def validate_capacity_change(self, table_name, temp_capacity):
        """Submits DynamoDB backup and validates if table's read capacity was increased to
        temporary value and then reverted after job completed
        Args:
            table_name    (str): The name of table to detect change in capacity

            temp_capacity (int): The temporary read capacity set at table group

        Raises:
            Exception:
                if backup of dynamodb table group failed
                if tables's read capacity was not reverted after job completed
        """
        bkp = self.dynamodb_subclient.backup()
        value = self.dynamodb_helper.detect_change_in_capacity(table_name, temp_capacity)
        if value:
            self.log.info("Table's read capacity was changed successfully")
            job_status = self.wait_for_job_completion(bkp)
            if not job_status:
                raise CVTestStepFailure("Backup of dynamodb table group failed")
        if self.dynamodb_helper.get_read_capacity(table_name) != 1:
            raise CVTestStepFailure("Read capacity of table is not reverted after backup")

    @test_step
    def cleanup(self):
        """Delete the Instances and subclients created by test case"""
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.delete_instance()
        self.log.info("Instance deleted successfully")

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            table_name = 'TC_56511'
            self.create_test_data(table_name, 'id')
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB',self.tcinputs['cloud_account']):
                self.cleanup()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'],
                adjust_read_capacity=5, content=['US East (Ohio) (us-east-2)'])
            self.db_instance_details.click_on_entity('default')
            self.validate_capacity_change(table_name, 5)
            self.admin_console.refresh_page()
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Cleanup the tables created on DynamoDB"""
        self.dynamodb_helper.delete_dynamodb_table('TC_56511')
