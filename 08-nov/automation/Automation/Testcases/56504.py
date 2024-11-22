# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
 "56510": {
          "ClientName": "XXXX",
          "InstanceName": "XXXX",
          "AccessNode": "XXXX",
          "StoragePolicy": "XXXX",
          "AccessKey": "XXXX",
          "SecretKey": "XXXX"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case

    tear_down()            --   Tear down function of thie test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps.amazon_helper import AmazonCloudDatabaseHelper
from Application.CloudApps.amazon_helper import AmazonDynamoDBCLIHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import CloudDBInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Command center: Backup dynamodb subclient with table rules for AWS tags"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Backup DynamoDB subclient with table rule for AWS tags"
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'AccessNode': None,
            'StoragePolicy': None,
            'AccessKey': None,
            'SecretKey': None
        }
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.helper = None
        self.dynamodb_helper = None
        self.subclient_name = None
        self.content = None
        self.client_name = None
        self.instance_name = None
        self.storage_policy = None
        self.access_node = None
        self.access_key = None
        self.secret_key = None
        self.table_names = None
        self.db_instance_details = None
        self.database_instance = None
        self.dynamodb_subclient = None

    def init_tc(self):
        """Sets up the test case related helper function and members"""

        try:
            self.helper = AmazonCloudDatabaseHelper(self)
            self.helper.populate_tc_inputs(self)
            self.dynamodb_helper = AmazonDynamoDBCLIHelper(self.access_key, self.secret_key)
            self.dynamodb_helper.initialize_client('us-east-2')
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.database_instance = DBInstances(self.admin_console)
            self.db_instance_details = CloudDBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_dynamodb(self, subclient_name='None'):
        """Navigates to dynamodb instance details page
        Args:
            subclient_name  (str):  Name of subclient to navigate
                            Default is 'None', Navigate only to instance
        """
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'DynamoDB',
                                               self.client_name)
        if subclient_name != 'None':
            self.db_instance_details.click_on_entity(subclient_name)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def create_subclient_and_backup(self):
        """Create subclient with given table rule and run backup for it"""

        name = 'subclient_56504'
        backup_set = self.instance.backupsets.get('defaultBackupset')
        sub_client = backup_set.subclients.add(
            name, self.storage_policy, "Created from automation")
        self.log.info("Subclient :[%s] created", name)
        sub_client.storage_policy = self.storage_policy
        sub_client.content = [{
            "path": "",
            "negation": False,
            "displayName": "yes",
            "name": "TC56504",
            "allOrAnyChildren": True,
            "type": "47",
            "value": "yes"
        }]

        # Run backup and validate if only tables with matching criteria got backed up

        self.navigate_to_dynamodb(name)
        bkp = self.dynamodb_subclient.backup()
        job_status = self.wait_for_job_completion(bkp)
        if not job_status:
            raise CVTestStepFailure("Backup of dynamodb table group failed")
        self.admin_console.refresh_page()
        self.dynamodb_subclient.access_restore()
        self.admin_console.select_hyperlink('us-east-2')

    @test_step
    def validate_table_rule(self):
        """Validates if tables satisfying the rule were backed up
        """
        items = self.dynamodb_subclient.get_items_in_browse_page('Table')
        if len(items) == len(self.table_names):
            for table in self.table_names:
                if table not in items:
                    raise CVTestStepFailure("Found tables other than expected ones")
        else:
            raise CVTestStepFailure("Validation of backed up tables failed")

    @test_step
    def delete_tables(self):
        """Deletes all the tables created by test case"""
        for each_table in self.table_names:
            self.dynamodb_helper.delete_dynamodb_table(each_table)

    def run(self):
        """Main function for test case execution"""

        try:
            self.init_tc()

            #   Step 1 - Create dynamodb tables, tag them and populate data
            self.log.info("Creating dynamodb tables")
            self.table_names = ['Table_56504_1', 'Table_56504_2']
            for table in self.table_names:
                self.dynamodb_helper.create_dynamodb_table(table, 'id')
                self.log.info("Populating the table with records")
                self.dynamodb_helper.populate_dynamodb_table(table, 'id', 10)
            self.dynamodb_helper.tag_resource(self.table_names,
                                              tag_name='TC56504', value='yes')

            #   Step 2 - Create DynamoDB instance if it doesn't exist
            if self.agent.instances.has_instance(self.instance_name):
                self.instance = self.agent.instances.get(self.instance_name)
                self.log.info("Instance %s already exists. Using existing instance.",
                              self.instance.instance_name)
                autocreated_instance = False
            else:
                self.log.info(
                    "Instance %s does not exist. Creating it.",
                    self.instance_name)
                autocreated_instance = True
                dynamodb_options = {
                    "instance_name": self.instance_name,
                    "storage_plan": self.storage_policy,
                    "storage_policy": self.storage_policy,
                    "access_node": self.access_node,
                    "access_key": self.access_key,
                    "secret_key": self.secret_key,
                    "cloudapps_type": 'amazon_dynamodb'
                }
                self.instance = self.agent.instances.add_cloud_storage_instance(dynamodb_options)
                self.log.info("Instance %s created", self.instance.instance_name)
                self.navigate_to_dynamodb('default')
                self.dynamodb_subclient.disable_backup()

            #   Step 3 - Create a subclient for verifying table rule
            self.log.info("Creating subclient to verify table rule with AWS tag")
            self.create_subclient_and_backup()

            #   Step 4 - Validate if only the tables satisfying the criteria were backed up
            self.validate_table_rule()

            #   Step 5 - Delete the dynamodb instance created by test case
            if autocreated_instance:
                self.navigate_to_dynamodb()
                self.db_instance_details.delete_instance()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        self.log.info("Tear Down Function")
        self.log.info("Cleanup the tables created during test case run")
        # Drop the tables created during TC run
        try:
            self.delete_tables()
        except Exception as exp:
            self.log.error("Clean up failed")
            self.log.error(exp)
