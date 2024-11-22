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

from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Validation Test of Metallic_O365_React_Sharepoint_Content_Association:
    Basic Validation for Content Association in Metallic SharePoint Client
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_React_Sharepoint_Content_Association"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.company_name = None
        self.app_type = None
        self.sites = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.sp_api_object = None
        self.total_num_of_sites = None
        self.groups = None
        self.regular_sites = None
        self.teams_sites = None
        self.plans = None

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

        self.regular_sites = self.tcinputs.get("RegularSites", "")
        self.teams_sites = self.tcinputs.get("TeamsSites", "")
        self.plans = self.tcinputs.get("Office365Plans", "")
        self.groups = {
            'All sites': 'All Web Sites',
            'All team sites': 'All Teams Sites'
        }

        self.navigator.navigate_to_office365()
        self.office365_obj.create_office365_app(name=self.app_name,
                                                is_express_config=False,
                                                tenant_site_url=self.tcinputs['ClientTenantUrl'],
                                                app_id=self.tcinputs['ClientId'],
                                                dir_id=self.tcinputs['ClientTenantId'],
                                                app_secret=self.tcinputs['ClientSecret'],
                                                cert_path=self.tcinputs['CertificatePath'],
                                                cert_pass=self.tcinputs['CertificatePassword'])
        self.app_name = self.office365_obj.get_app_name()

    def initialize_sp_api_object(self):
        """Initializes SharePoint object to make api calls"""
        self.sp_api_object = SharePointOnline(self)
        self.sp_api_object.azure_app_id = self.tcinputs.get("ClientId", "")
        self.sp_api_object.azure_app_secret = self.tcinputs.get("ClientSecret", "")
        self.sp_api_object.azure_app_tenant_id = self.tcinputs.get("ClientTenantId", "")
        self.sp_api_object.tenant_url = self.tcinputs.get("ClientTenantUrl", "")
        self.sp_api_object.global_administrator = self.tcinputs.get("GlobalAdmin", "")
        self.sp_api_object.global_administrator_password = self.tcinputs.get("Password", "")
        self.total_num_of_sites = self.sp_api_object.get_group_based_sites_count()

    def verify_auto_association_all_sites_group(self):
        """Associated all groups and team sites and verifies the association"""
        try:
            associated_sites_count = self.office365_obj.add_user_group(
                group_name=list(self.groups)[0],
                plan=self.company_name+"-"+(list(self.plans)[0])
            )
            self.office365_obj.verify_added_user_groups([list(self.groups.values())[0]])
            if associated_sites_count < self.total_num_of_sites[list(self.groups.values())[0]]:
                raise Exception(f'All sites are not auto associated for {list(self.groups.values())[0]} group')
            self.log.info(f"{list(self.groups.values())[0]} association is verified")
            self.office365_obj.remove_user_group(list(self.groups.values())[0])
        except Exception:
            raise Exception(f'Exception while verifying {list(self.groups.values())[0]} auto association')

    def verify_auto_association_all_teams_sites_group(self):
        """Associated all groups and team sites and verifies the association"""
        try:
            associated_sites_count = self.office365_obj.add_user_group(
                group_name=list(self.groups)[1],
                plan=self.company_name+"-"+(list(self.plans)[0])
            )
            self.office365_obj.verify_added_user_groups([list(self.groups.values())[1]])
            if associated_sites_count < self.total_num_of_sites[list(self.groups.values())[1]]:
                raise Exception(f'All sites are not auto associated for {list(self.groups.values())[1]} group')
            self.log.info(f"{list(self.groups.values())[0]} association is verified")
            self.office365_obj.remove_user_group(list(self.groups.values())[1])
        except Exception:
            raise Exception(f'Exception while verifying {list(self.groups.values())[1]} auto association')

    def verify_multiple_site_auto_association_group(self):
        """Associate multiple groups with various O365 plans and verify sites, subsites and retention conflict"""
        try:
            self.office365_obj.add_user_group(
                group_name=list(self.groups)[0], plan=self.company_name+"-"+(list(self.plans)[0]))
            for i in self.regular_sites:
                self.regular_sites[i]["Office 365 plan"] = self.company_name+"-"+(list(self.plans)[0])
            self.office365_obj.add_user_group(
                group_name=list(self.groups)[1], plan=self.company_name+"-"+(list(self.plans)[1]))
            for i in self.teams_sites:
                self.teams_sites[i]["Office 365 plan"] = self.company_name+"-"+(list(self.plans)[1])
            self.office365_obj.verify_site_details(expected_sites_details=self.regular_sites)
            self.office365_obj.verify_site_details(expected_sites_details=self.teams_sites)
        except Exception:
            raise Exception(f'Exception while verifying multiple groups auto association')

    def verify_o365_plan_change_multiple_auto_association_group(self):
        """Change O365 plan of multiple groups, run discovery and verify sites, subsites and retention conflict"""
        try:
            self.office365_obj.change_office365_plan_group(
                group_name=list(self.groups.values())[0], plan_name=self.company_name+"-"+(list(self.plans)[2]))
            for i in self.regular_sites:
                self.regular_sites[i]["Office 365 plan"] = self.company_name+"-"+(list(self.plans)[2])
            for i in self.teams_sites:
                self.teams_sites[i]["Office 365 plan"] = self.company_name + "-" + (list(self.plans)[2])
            self.office365_obj.verify_site_details(expected_sites_details={**self.regular_sites, **self.teams_sites})
            self.office365_obj.change_office365_plan_group(
                group_name=list(self.groups.values())[1], plan_name=self.company_name+"-"+(list(self.plans)[3]))
            for i in self.teams_sites:
                self.teams_sites[i]["Office 365 plan"] = self.company_name+"-"+(list(self.plans)[3])
            self.office365_obj.verify_site_details(expected_sites_details={**self.regular_sites, **self.teams_sites})
        except Exception:
            raise Exception(f'Exception while verifying O365 plan change of multiple groups')

    def verify_remove_auto_association_group(self):
        try:
            self.office365_obj.remove_user_group(group_name=list(self.groups.values())[0])
            self.office365_obj.remove_user_group(group_name=list(self.groups.values())[1])
        except Exception:
            raise Exception(f'Exception while verifying removal of auto association groups')

    def create_plans_if_not_present(self):
        plan_list = self.office365_obj.get_plans_list()
        for plan in self.plans:
            if (self.company_name+"-"+plan) not in plan_list:
                self.navigator.navigate_to_plan()
                self.office365_obj.create_o365_plan(plan_name=plan, days=self.plans[plan])

    def run(self):
        """Main function for test case execution"""
        try:
            self.office365_obj.wait_for_discovery_to_complete()
            # Get Total site count for each group category before beginning tests
            self.initialize_sp_api_object()
            # Create the required plans
            self.create_plans_if_not_present()

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            # verify All Team Sites group association
            self.verify_auto_association_all_sites_group()
            # verify All Sites group association
            self.verify_auto_association_all_teams_sites_group()
            # verify multiple Site groups association and retention conflict
            self.verify_multiple_site_auto_association_group()
            # verify plan change
            self.verify_o365_plan_change_multiple_auto_association_group()
            # verify group association removal
            self.verify_remove_auto_association_group()

            self.log.info("Content Association Metallic testcase is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
