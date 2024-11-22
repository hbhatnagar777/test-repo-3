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

from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange Tenant User:
    Basic Validation for Metallic Exchange existing and new tenant
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_exchange Tenant User Case"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.app_type = None
        self.user = None
        self.app_name = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['TenantUserName'],
                                 self.tcinputs['TenantPassword'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.navigator = self.admin_console.navigator
        self.user = self.tcinputs['User']
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    @staticmethod
    def verify_details(features_dict):
        for key in features_dict:
            if features_dict[key] is None:
                print("{} is present with the value {}. Please check.".format(key, features_dict[key]))
            else:
                print("{} is present with the value {}".format(key, features_dict[key]))

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.admin_console.wait_for_completion()
            features_dict = self.office365_obj.fetch_exchange_overview_details()
            self.verify_details(features_dict)
            self.office365_obj.browse_entity(entity_name=self.user)
            BrowsePageDetails = self.office365_obj.get_browse_page_details(folder_name=self.user.split("@")[0]+" ("+self.user+")")
            self.verify_details(BrowsePageDetails)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs["Name"])
            self.office365_obj.run_restore(email=self.user, unconditional_overwrite=False)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)