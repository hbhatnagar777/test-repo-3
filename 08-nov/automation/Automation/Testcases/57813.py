# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"57813": {
          "cloud_account": "XXXX",
          "plan": "XXXX",
          "cloud_credential": "XXXX"
        }

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


class TestCase(CVTestCase):
    """Admin Console: DynamoDB- Validate all properties during instance creation"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DynamoDB: Validate all properties during instance creation"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instance = None
        self.dynamodb_instance = None
        self.db_instance_details = None
        self.dynamodb_subclient = None
        self.tcinputs = {
            "cloud_account": None,
            "plan": None,
            "cloud_credential": None
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
            self.db_instance_details = DBInstanceDetails(self.admin_console)
            self.dynamodb_subclient = SubClient(self.admin_console)
            if self.database_instance.is_instance_exists(self.database_instance.Types.CLOUD_DB,
                                                         'DynamoDB',self.tcinputs['cloud_account']):
                self.cleanup()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_dynamodb_instance(self):
        """Navigates to dynamodb instance details page"""
        self.navigator.navigate_to_db_instances()
        self.database_instance.select_instance(self.database_instance.Types.CLOUD_DB, 'DynamoDB',
                                               self.tcinputs['cloud_account'])

    @test_step
    def validate_instance_properties(self):
        """Validates if instance was created with properties set by user

        Raises:
            Exception if any of the attributes set by user were not set
            while creating instance
        """
        instance_details = self.db_instance_details.get_instance_details()
        if (instance_details['Cloud account'].lower() == self.tcinputs['cloud_account'].lower()
            and instance_details['Plan'].strip('\nEdit').lower() == self.tcinputs['plan'].lower() 
            and instance_details['Cloud credential'].strip('\nEdit...').lower() 
            == self.tcinputs['cloud_credential'].lower()):
            self.log.info("Instance properties validation passed")
        else:
            raise CVTestStepFailure("Instance properties validation failed")

    @test_step
    def validate_subclient_properties(self):
        """Validates if the user settings were applied on default subclient

        Raises:
            Exception if any of the attributes set by user were not set
            when default subclient was auto created
        """
        self.db_instance_details.click_on_entity('default')
        subclient_details = self.dynamodb_subclient.get_subclient_general_properties()
        if (subclient_details['Cloud account'].lower() == self.tcinputs
                ['cloud_account'].lower() and subclient_details['Plan'].strip('\nEdit').lower()
                == self.tcinputs['plan'].lower() and subclient_details
                ['Number of data streams'].strip('\nEdit...') == str(2) and
                subclient_details['Adjust read capacity'].lower() == 'on'):
            self.log.info("Subclient properties validated successfully")
        else:
            raise CVTestStepFailure("Subclient properties validation failed")

    @test_step
    def cleanup(self):
        """Cleanup the dynamodb tables
        Delete the Instances and subclients created by test case
        """
        self.navigate_to_dynamodb_instance()
        self.db_instance_details.delete_instance()

    def run(self):
        """Main method to run test case"""
        try:
            self.init_tc()
            self.database_instance.add_dynamodb_instance(
                self.tcinputs['cloud_account'], self.tcinputs['plan'],
                adjust_read_capacity=10,
                content=['Asia Pacific (Singapore) (ap-southeast-1)'])
            self.db_instance_details.click_on_entity('default')
            self.dynamodb_subclient.disable_backup()
            self.navigate_to_dynamodb_instance()
            self.validate_instance_properties()
            self.validate_subclient_properties()
            self.cleanup()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
