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
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue


class TestCase(CVTestCase):
    """
    Class for executing Test Case for Microsoft Office 365 Teams Acceptance

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Microsoft Office 365 Teams Acceptance"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.teams = None
        self.app_name = None
        self.global_admin = None
        self.password = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('Teams-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@teams{current_timestamp}.com')

    def setup(self):
        self.create_tenant()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name,
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.teams
        self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()
        self.hub_dashboard.click_continue()
        self.hub_dashboard.click_new_configuration()
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.service_catalogue.start_office365_trial()
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs.get('Name', "O365_Teams_App_TC_64252")
        self.global_admin = self.tcinputs['GlobalAdmin']
        self.password = self.tcinputs['Password']
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, True)

    @TestStep()
    def create_app(self):
        """Create the MS Teams Office 365 App."""
        self.office365_obj.create_office365_app(name=self.app_name, global_admin=self.global_admin,
                                                password=self.password)
        self.app_name = self.office365_obj.get_app_name()

    @TestStep()
    def return_to_app_page(self):
        """Navigate back to the MS Teams Office 365 App Page."""
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)

    @TestStep()
    def select_o365_plan(self):
        """Selects an Office 365 Plan to be used."""
        self.navigator.navigate_to_plan()
        plans = self.office365_obj.get_plans_list()
        self.office365_obj.verify_retention_of_o365_plans(self.tenant_name, plans)

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_app()
            self.select_o365_plan()
            self.return_to_app_page()
            self.office365_obj.add_teams(self.teams)
            self.office365_obj.run_backup()
            self.return_to_app_page()
            self.office365_obj.click_restore_page_action()
            self.office365_obj.delete_item_in_browse(self.teams)
            self.return_to_app_page()
            self.office365_obj.click_restore_page_action()
            self.office365_obj.search_item_in_browse(self.teams)
            self.log.info("Search is verified")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.hub_utils.deactivate_tenant(self.tenant_name)
        self.hub_utils.delete_tenant(self.tenant_name)