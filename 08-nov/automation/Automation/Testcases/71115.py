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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Office365Pages import constants
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Office 365 Reseller case for all agents
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Reseller_Case"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.mailboxes = None
        self.users = None
        self.sites = None
        self.company = None
        self.teams = None
        self.app_name = None
        self.clients = list()
        self.exmbclient_object = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)

    @TestStep
    def create_client_for_agent(self, app_type):
        """Create clients for agents"""
        if app_type == O365AppTypes.exchange:
            self.log.info("------------------------------------"
                          "Creating Exchange Online Application"
                          "------------------------------------")
            self.office365_obj.app_type = O365AppTypes.exchange
            self.office365_obj.constants = constants.ExchangeOnline
            self.app_name = f'ExchangeOnline{self.tcinputs["Name"]}'
            self.mailboxes = self.tcinputs["ExchangeOnlineUsers"].split(',')
        elif app_type == O365AppTypes.onedrive:
            self.log.info("-----------------------------"
                          "Creating OneDrive Application"
                          "-----------------------------")
            self.office365_obj.app_type = O365AppTypes.onedrive
            self.office365_obj.constants = constants.OneDrive
            self.app_name = f'OneDrive{self.tcinputs["Name"]}'
            self.users = self.tcinputs["OneDriveUsers"].split(',')
        elif app_type == O365AppTypes.sharepoint:
            self.log.info("-------------------------------"
                          "Creating SharePoint Application"
                          "-------------------------------")
            self.office365_obj.app_type = O365AppTypes.sharepoint
            self.office365_obj.constants = constants.SharePointOnline
            self.app_name = f'SharePoint{self.tcinputs["Name"]}'
            self.sites = dict(zip(self.tcinputs['Sites'].split(","), self.tcinputs['SitesTitle'].split(",")))
        elif app_type == O365AppTypes.teams:
            self.log.info("--------------------------"
                          "Creating Teams Application"
                          "--------------------------")
            self.office365_obj.app_type = O365AppTypes.teams
            self.office365_obj.constants = constants.Teams
            self.app_name = f'Teams{self.tcinputs["Name"]}'
            self.teams = self.tcinputs["Teams"].split(',')
        self.office365_obj.create_office365_app(name=self.app_name,
                                                global_admin=self.tcinputs['GlobalAdmin'],
                                                password=self.tcinputs['Password'])
        self.app_name = self.office365_obj.get_app_name()
        self.clients.append(self.app_name)

    @TestStep
    def run_backup_and_restore(self, users):
        """
        Add user to the client and run backup
        Args :
            users(list) : List of users to add
        """
        self.office365_obj.add_user(users)
        self.office365_obj.run_backup()
        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.run_restore()

    def open_browser(self):
        """Open browser"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name, self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.office365
        self.navigator = self.admin_console.navigator

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.tcinputs["Tenant Username"],
                                 password=self.tcinputs["Tenant Password"],
                                 )
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs['Name']
        self.company = self.tcinputs['Company']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    def run(self):
        """Main function for test case execution"""

        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.onedrive)
        self.run_backup_and_restore(self.users)
        self.log.info("Onedrive backup and restore completed")

        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.browse_entity(self.users)
        self.office365_obj.perform_operations_on_self_user_client(
            client_name=self.tcinputs["Name"],
            operation="Export",
            export_as="PST"
        )
        self.log.info("Onedrive export is verified")

        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.exchange)
        self.run_backup_and_restore(self.mailboxes)
        self.log.info("Exchange backup and restore completed")

        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.browse_entity(self.mailboxes)
        self.office365_obj.perform_operations_on_self_user_client(
             client_name=self.tcinputs["Name"],
             operation="Export",
             export_as="PST"
        )
        self.log.info("Exchange export is verified")

        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.sharepoint)
        self.run_backup_and_restore(self.sites)
        self.log.info("Sharepoint backup and restore completed")

        self.office365_obj.switch_company(self.company)
        self.navigator.navigate_to_office365()
        self.create_client_for_agent(O365AppTypes.teams)
        self.run_backup_and_restore(self.teams)
        self.log.info("Teams backup and restore completed")

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Testcase completed successfully!!!")
        try:
            if self.status == constants.PASSED:
                self.admin_console.logout()
                self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                         self.inputJSONnode['commcell']['commcellPassword'])
                self.office365_obj.disable_compliance_lock()
                self.admin_console.logout()
                self.admin_console.login(self.tcinputs["Tenant Username"],
                                         self.tcinputs["Tenant Password"])
                for client in self.clients:
                    self.navigator.navigate_to_office365()
                    self.office365_obj.delete_office365_app(client)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            