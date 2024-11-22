# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
 "58158": {
          "cloud_account": "XXXX",
          "restricted_account": "XXXX",
          "plan": "XXXX",
          "access_key": "XXXX",
          "secret_key": "XXXX",
        }

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import CloudDBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.table import Rtable


class TestCase(CVTestCase):
    """Admin Console: Validate dynamodb operations with cloud account
    having AWS region restriction"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate dynamodb agent with cloud account having AWS region restriction"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.rtable = None
        self.database_instance = None
        self.database_type = None
        self.dynamodb_helper = None
        self.dynamodb_instance = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
        self.tcinputs = {
            "cloud_account": None,
            "restricted_account": None,
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
            self.db_instance_details = CloudDBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)
            self.dynamodb_helper = AmazonDynamoDBCLIHelper(
                secret_key=self.tcinputs['secret_key'], access_key=self.tcinputs['access_key'])
            self.dynamodb_helper.initialize_client('us-east-2')
            self.rtable = Rtable(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_dynamodb_instance(self, restricted_account=False):
        """Navigates to dynamodb instance details page
        Args:
            restricted_account  (Boolean): Flag differentiate between cloud account created with
                                            region restriction and without any restriction

                                            Default value is False
        """
        self.navigator.navigate_to_db_instances()
        self.rtable.reload_data()
        if restricted_account:
            self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB,
                                                   'DynamoDB', self.tcinputs['restricted_account'])
        else:
            self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB,
                                                   'DynamoDB', self.tcinputs['cloud_account'])

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
    def add_subclient(self, restricted_account=False):
        """validates that regions not set at instance level are not shown in cloud browse
        and adds subclient with the regions set at instance level

        Args:
            restricted_account  (Boolean): Flag differentiate between cloud account created with
                                            region restriction and without any restriction

                                            Default value is False
        """
        if restricted_account:
            self.navigate_to_dynamodb_instance(restricted_account=True)
        else:
            self.navigate_to_dynamodb_instance()
        add_subclient_obj = self.db_instance_details.click_add_subclient(self.database_type)
        try:
            add_subclient_obj.add_dynamodb_subclient('Sub_58158', self.tcinputs['plan'],
                                                     ['Asia Pacific (Singapore) (ap-southeast-1)'])
        except NoSuchElementException:
            pass
        self.admin_console.refresh_page()
        add_subclient_obj = self.db_instance_details.click_add_subclient(self.database_type)
        add_subclient_obj.add_dynamodb_subclient('Sub_58158', self.tcinputs['plan'],
                                                 ['US East (Ohio) (us-east-2)'])

    @test_step
    def submit_backup(self, level='Incremental'):
        """Submits DynamoDB backup and validates it
        Args:
            level    (str): Backup level, full or incremental

        """
        if level != 'Incremental':
            level = RBackup.BackupType.FULL
        else:
            level = RBackup.BackupType.INCR
        bkp = self.dynamodb_subclient.backup(backup_type=level)
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")

    @test_step
    def validate_regions_in_browse(self):
        """Verifies that only the regions set at instance level are backed up
        by validating browse data"""
        self.dynamodb_subclient.access_restore()
        items = self.dynamodb_subclient.get_items_in_browse_page('Region')
        if len(items) != 1 and 'us-east-2' not in items:
            raise CVTestStepFailure("Found cloud regions other than configured ones")

    @test_step
    def submit_in_place_restore(self, table_name):
        """Submits in place restore
        Args:
            table_name  (str):  Table to restore
        """
        self.dynamodb_subclient.access_restore()
        mapping_dict = {
            'us-east-2': [table_name]
        }
        restore_panel_obj = self.dynamodb_subclient.restore_files_from_multiple_pages(
            self.database_type, mapping_dict, 'Sub_58158')
        jobid = restore_panel_obj.same_account_same_region()
        job_status = self.wait_for_job_completion(jobid)
        if not job_status:
            raise CVTestStepFailure(f"In place restore job: {jobid} failed")

    @test_step
    def all_steps_to_validate_region_restriction(self, table_name, restricted_account=False):
        """Method to perform all steps in validating region restriction
        Steps:
        1. Check if default subclient backs up only the regions set at instance
        2. Add new table group and verify if cloud browse shows only the regions
        set at instance and backup completes successfully
        3. Restore from this table group
        4. Validate the restored data

        Args:
            table_name  (str):  The table to be restored

            restricted_account  (Boolean): Flag differentiate between cloud account created with
                                            region restriction and without any restriction

                                            Default value is False
        """
        self.db_instance_details.click_on_entity('default')
        self.submit_backup(level='Full')
        self.admin_console.refresh_page()
        self.validate_regions_in_browse()
        if restricted_account:
            self.add_subclient(restricted_account=True)
        else:
            self.add_subclient()
        self.submit_backup(level='Full')
        self.admin_console.refresh_page()
        self.submit_in_place_restore(table_name)
        self.dynamodb_helper.validate_dynamodb_table(table_name, 'id', 10)

    @test_step
    def cleanup(self):
        """Delete the Instances and subclients created by test case
        """
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.delete_instance()
        self.rtable.reload_data()
        self.navigate_to_dynamodb_instance(restricted_account=True)
        self.db_instance_details.delete_instance()
        self.rtable.reload_data()

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            table_name = 'TC_58158'
            self.create_test_data(table_name, 'id')

            """Create dynamodb instance with hypervisor/cloud account having no region restriction 
            and set restriction at dynamodb instance level.
            Run all steps to validate if region setting was successful"""
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB',self.tcinputs['cloud_account']):
                self.cleanup()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'], 0)
            self.db_instance_details.modify_region_for_cloud_account(['us-east-2'])
            self.db_instance_details.access_overview_tab()
            self.all_steps_to_validate_region_restriction(table_name)

            """Create dynamodb instance with hypervisor/cloud account already having a region
            restriction set and validate if dynamodb is inheriting regions from cloud account
            Run all steps to validate if region setting was successful"""

            self.navigator.navigate_to_db_instances()
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB',
                                                         self.tcinputs['restricted_account']):
                self.cleanup()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['restricted_account'], self.tcinputs['plan'], 0)
            self.all_steps_to_validate_region_restriction(table_name, restricted_account=True)
            self.cleanup()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Cleanup the tables created on dynamodb"""
        self.dynamodb_helper.delete_dynamodb_table('TC_58158')
