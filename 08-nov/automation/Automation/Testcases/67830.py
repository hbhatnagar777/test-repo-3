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
import time

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_React_Sharepoint_Custom_Categories:
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_React_Sharepoint_Custom_Categories"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.company_name = None
        self.app_type = None
        self.app_name = None
        self.plans = None
        self.custom_categories = None
        self.sites = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['ExistingComcellUserName'],
                                 self.tcinputs['ExistingComcellPassword'])
        self.company_name = self.tcinputs['ExistingComcellUserName'].split('\\')[0]
        self.app_type = O365AppTypes.sharepoint
        self.navigator = self.admin_console.navigator
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

        self.plans = self.tcinputs["Office365Plans"]
        self.custom_categories = self.tcinputs['CustomCategories']
        self.sites = self.tcinputs['Sites']

        self.navigator.navigate_to_office365()
        self.office365_obj.create_office365_app(name=self.app_name,
                                                global_admin=self.tcinputs['GlobalAdmin'],
                                                password=self.tcinputs['Password'])
        self.app_name = self.office365_obj.get_app_name()

    def verify_custom_category(self, custom_category_rules, office_plan):
        self.office365_obj.add_custom_category(custom_dict=custom_category_rules, plan=office_plan)
        self.office365_obj.verify_added_user_groups([custom_category_rules['name']])
        self.office365_obj.wait_for_discovery_to_complete()
        # half an hour sleep timer for Custom Category
        time.sleep(30*60)
        if int(self.office365_obj.get_total_associated_users_count()) == int(custom_category_rules["expectedSiteCount"]):
            self.log.info(f'Custom category verified for {custom_category_rules["name"]}')
        else:
            raise Exception(f'Custom category failed for {custom_category_rules["name"]}')

    def create_plans_if_not_present(self):
        plan_list = self.office365_obj.get_plans_list()
        for plan in self.plans:
            if (self.company_name+"-"+plan) not in plan_list:
                self.navigator.navigate_to_plan()
                self.office365_obj.create_o365_plan(plan_name=plan, days=self.plans[plan])

    def run(self):
        """Main function for test case execution"""
        try:
            # Create the required plans
            self.create_plans_if_not_present()

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.wait_for_discovery_to_complete()

            # Add Custom Categories and verify site association count are as expected
            for i in range(len(self.custom_categories)):
                if self.company_name:
                    o365plan = self.company_name+"-" + list(self.plans.keys())[i]
                else:
                    o365plan = list(self.plans.keys())[i]
                self.verify_custom_category(self.custom_categories[i], o365plan)
            # Add tenant name to plan names in expected site details
            for i in self.sites:
                self.sites[i]["Office 365 plan"] = self.company_name+"-"+self.sites[i]["Office 365 plan"]
            # Verify all the associated sites have the expected O365 plan
            self.office365_obj.verify_site_details(expected_sites_details=self.sites)

            self.log.info("Custom Categories Metallic testcase is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
