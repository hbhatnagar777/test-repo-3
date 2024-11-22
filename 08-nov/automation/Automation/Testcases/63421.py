from selenium.webdriver.common.by import By
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

    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.

    Input Example

    "testCases": {
        "60045": {
            "Name": "AppName",
            "GlobalAdmin": "GA@company.onmicrosoft.com",
            "Password": "abc123",
            "Office365Plan": "O365",
            "Teams": "Team1, Team2"
            }
        }

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from datetime import datetime as dt


class TestCase(CVTestCase):
    """
    Class for executing Test Case for Microsoft Office 365 Teams Acceptance

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MS Teams: Create Client using custom config"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.app_type = None
        self.teams = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.is_created = False

    def setup(self):
        username = self.inputJSONnode['commcell'].get('commcellUsername')
        password = self.inputJSONnode['commcell'].get('commcellPassword')
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(username, password)
        self.app_type = O365AppTypes.teams
        if self.admin_console.check_if_entity_exists("id","customStartupMessage_button_#123"):
            self.admin_console.driver.find_element(By.ID, "customStartupMessage_button_#123").click()
        self.navigator = self.admin_console.navigator
        self.app_name = dt.now().strftime("TeamsClient_63421_%d%h%Y_%H%M")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type)

    def run(self):
        """Main function for test case execution"""
        try:
            app_details = {"app_id": self.tcinputs['AppId'], "dir_id": self.tcinputs['DirId'],
                           "app_secret": self.tcinputs['AppSec']}
            plan = self.tcinputs['ServerPlan']
            global_admin = self.tcinputs.get('GlobalAdmin')
            global_pass = self.tcinputs.get('Password')
            infra_details = {"index_server": self.tcinputs.get('IndexServer', None),
                             "access_nodes": self.tcinputs.get('AccessNodes', None),
                             "jr_details": self.tcinputs.get('JobResultsss', None)}
            app_name = self.office365_obj.create_team_cvpysdk_custom(self.app_name, plan, global_admin,
                                                                     global_pass, app_details, infra_details)
            if app_name != self.app_name:
                raise Exception(f"App name does not match. Created AppName:{app_name}, Expected:{self.app_name}")
            self.log.info(f"Created Team: {self.app_name}")
            self.is_created = True
            self.office365_obj.search_and_goto_app(self.app_name)
            self.log.info("Team shows up in the Apps list")
            if not self.office365_obj.validate_infra(self.app_name, plan, infra_details):
                raise Exception("Validation of infrastructure settings failed")
            self.log.info(f"Infrastructure settings verified for team: {self.app_name}")
            time.sleep(10)
            teams = [team.strip() for team in self.tcinputs.get("Teams").split(",")]
            self.office365_obj.add_teams_react(teams, self.tcinputs.get("O365Plan"))
            self.log.info(f"Added teams to client: {self.app_name}")
            if not self.office365_obj.verify_added_teams(teams):
                raise Exception("Error")
            self.log.info("Discovered and added user successfully")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.is_created:
            self.navigator.navigate_to_office365()
            self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
