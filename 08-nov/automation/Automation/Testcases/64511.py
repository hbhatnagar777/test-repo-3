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
import datetime
import time

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange_Acceptance:
    Basic Validation for Metallic Exchange existing and new tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.custom_dict = None
        self.service_catalogue = None
        self.name = "Metallic_O365_Exchange_Custom_Category"
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
        self.users = None
        self.app_name = None
        self.exmbclient_object = None
        self.utils = TestCaseUtils(self)

    def initialize_exchange_object(self):
        """Initializes Exchange Object"""
        self.tcinputs['ProxyServers'] = ["dummy_name"]
        self.exmbclient_object = ExchangeMailbox(self)
        self.exmbclient_object.environment_type = 4
        self.exmbclient_object.client_name = self.app_name
        self.exmbclient_object.exchange_online_user = self.tcinputs['GlobalAdmin']
        self.exmbclient_object.exchange_online_password = self.tcinputs['Password']

    def setup(self):
        """Setup function for the testcase"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs["TenantUser"],
                                 self.tcinputs["TenantPassword"])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)
        self.custom_dict = self.tcinputs["CustomCategoryAssociation"]

    def run(self):
        """Main function for test case execution"""
        try:
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'])
            self.navigator.navigate_to_plan()
            self.office365_obj.get_plans_list()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.add_custom_category(self.custom_dict)
            self.log.info("Waiting for users to get associated")
            time.sleep(20)
            licensed_users = self.office365_obj.fetch_licensed_users_for_client()
            count = self.office365_obj.get_total_associated_users_count()
            if 0 < count == len(licensed_users):
                self.log.info("Custom Category is matched")
            else:
                raise Exception("Custom Category count is mismatching")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
