# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Dynamics 365: Client Creation with Express Configuration and Modification of Configuration

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Dynamics365Pages.dynamics365 import Dynamics365Apps
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Dynamics 365: Client Creation with Express Configuration and Modification of Configuration

    Example for test case inputs:
        "60131":
        {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "ServerPlan": "<Server-Plan>>",
          "IndexServer": <Index-Server>>,
          "AccessNode": <access-node>>,
          "office_app_type": "Dynamics365",
          "GlobalAdmin": <global-admin-userid>>,
          "Password": <global-admin-password>>,
          "Dynamics365Plan": "",
          "NewServerPlan": <value-of-new-server-plan>>,
          "NewUNCPath": "<new-UNC-Path>>",
          "NewUserAccount": "<local-system-account>",
          "NewUserAccPwd": "<local-system-account-password>>,
          "NewIndexServer": "<new-index-server>>,
          "NewAccessNode": "<new-access-node>>",
          "D365_Plan": "<name-of-D365-Plan>>",
        }
    """

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365: Client Creation with Express Configuration and Modification of Configuration"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.dynamics = None
        self.client_name = None
        self.d365_helper = None
        self.tcinputs = {
            "Dynamics_Client_Name": None,
            "ServerPlan": None,
            "IndexServer": None
        }

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Logged in to Admin Console")

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_dynamics365()
            self.log.info("Navigated to D365 Page")

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Helper(admin_console=self.admin_console, tc_object=self, is_react=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.d365_helper.verify_client_configuration_value()
            self.log.info("Client Config Values successfully verifies")

            self.d365_helper.dynamics365_apps.modify_app_config_values(
                                                    new_server_plan=self.tcinputs['NewServerPlan'],
                                                    new_access_node=self.tcinputs['NewAccessNode'],
                                                    new_shared_path=self.tcinputs['NewUNCPath'],
                                                    new_user_account=self.tcinputs['NewUserAccount'],
                                                    new_password=self.tcinputs['NewUserAccPwd'],
                                                    new_index_server=self.tcinputs["NewIndexServer"])
            self.log.info("Modified the App Config Values")

            self.d365_helper.verify_client_configuration_value()
            self.log.info("Verified App Configuration Values after modification")

            self.d365_helper.verify_client_associated_with_plan()
            self.log.info("Verified client association with Plan")
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client()
                self.log.info("Client Deleted")
                self.log.info("Test Case Completed!!!")
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
