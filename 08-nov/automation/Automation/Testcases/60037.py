# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for  SharePoint v2 Verification of Auto Association Groups Manage Options
and O365 Plan Conflict Validation - Content Tab

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import time
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.sharepoint import SharePoint
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "SharePoint V2: Verification of Auto Association Groups Manage Options " \
                    "and O365 Plan Conflict Validation- Content Tab"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.sp_api_object = None
        self.total_num_of_sites = None
        self.o365_plan = None
        self.group_site_dict = None
        self.normal_site_dict = None
        self.groups = [('All team sites', 'All Teams Sites'),
                       ('All sites', 'All Web Sites')]

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
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.group_site_dict = self.tcinputs['GroupSite']
            self.normal_site_dict = self.tcinputs['NormalSite']
            self.o365_plan = self.tcinputs['Office365Plan']
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)
            self._initialize_sp_api_object()
            self.sharepoint.create_office365_app()
            self.sharepoint.wait_for_discovery_to_complete()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def _initialize_sp_api_object(self):
        """Initializes SharePoint object to make api calls"""
        self.sp_api_object = SharePointOnline(self)
        self.sp_api_object.azure_app_id = self.tcinputs.get("ClientId", "")
        self.sp_api_object.azure_app_secret = self.tcinputs.get("ClientSecret", "")
        self.sp_api_object.azure_app_tenant_id = self.tcinputs.get("AzureDirectoryId", "")
        self.sp_api_object.tenant_url = self.tcinputs.get("SiteAdminUrl", "")
        self.sp_api_object.global_administrator = self.tcinputs.get("GlobalAdministrator", "")
        self.sp_api_object.global_administrator_password = self.tcinputs.get("GlobalAdministrator Password", "")
        self.total_num_of_sites = self.sp_api_object.get_group_based_sites_count()

    @staticmethod
    def update_o365_plan_in_properties(properties, o365_plan):
        """Updates o365 plan in the properties that are used for validation
            Args:
                properties (dict)   :  dictionary of site properties
                o365_plan (str)     :  o365 plan to be updated
        """
        try:
            for site in properties:
                properties[site]['Office 365 plan'] = o365_plan
            return properties
        except Exception:
            raise Exception('Exception while updating o365 plan in properties')

    @test_step
    def verify_all_groups_and_team_sites_auto_association(self):
        """Associated all groups and team sites and verifies the association"""
        try:
            self.sharepoint.groups = [self.groups[0][0]]
            self.sharepoint.add_user_group(group_name=self.groups[0][0])
            self.sharepoint.verify_added_auto_association_groups([self.groups[0][1]])
            self.sharepoint.verify_plan_association(users=[self.groups[0][1]], is_group=True)
            associated_sites_count = self.sharepoint.get_total_associated_sites_count()
            self.log.debug(f'{associated_sites_count = }, {self.total_num_of_sites = }')
            if (associated_sites_count < self.total_num_of_sites[self.groups[0][1]]
                    or associated_sites_count - self.total_num_of_sites[self.groups[0][1]] > 10
                    or associated_sites_count == 0):
                raise Exception(f'All sites are not auto associated for {self.groups[0][1]} group')
            self.update_o365_plan_in_properties(self.group_site_dict.get('ValidateSiteDetails'),
                                                self.o365_plan)
            self.sharepoint.verify_site_details(self.group_site_dict.get('ValidateSiteDetails'))
        except Exception:
            raise CVTestStepFailure(f'Exception while verifying {self.groups[0][1]} auto association')

    @test_step
    def verify_all_web_sites_auto_association(self):
        """Associated all web sites and verifies the association"""
        try:
            self.o365_plan = self.tcinputs['Office365Plan2']
            self.sharepoint.groups = [self.groups[1][0]]
            self.sharepoint.add_user_group(group_name=self.groups[1][0], plan=self.o365_plan)
            self.sharepoint.verify_added_auto_association_groups([self.groups[1][1]])
            self.sharepoint.verify_plan_association(users=[self.groups[1][1]], plan=self.o365_plan, is_group=True)
            associated_sites_count = self.sharepoint.get_total_associated_sites_count()
            if (abs(associated_sites_count - self.total_num_of_sites[self.groups[1][1]]) > 10
                    or associated_sites_count == 0):
                raise Exception(f'All sites are not auto associated for {self.groups[1][1]} group')
            self.total_num_of_sites[self.groups[1][1]] = associated_sites_count
            updated_properties = self.update_o365_plan_in_properties(self.group_site_dict.get('ValidateSiteDetails')
                                                                     , self.o365_plan)
            self.sharepoint.verify_site_details({**self.normal_site_dict.get('ValidateSiteDetails'),
                                                 **updated_properties})
        except Exception:
            raise CVTestStepFailure(f'Exception while verifying {self.groups[1][1]} auto association')

    def verify_change_o365_plan(self, group_name, new_o365_plan):
        """Changes o365 plan for auto association group and verifies it
              Args:
                    group_name (str)        :  name of the auto association group
                    new_o365_plan (str)     :  o365 plan to be updated
        """
        try:
            self.sharepoint.groups = [group_name]
            self.sharepoint.change_office365_plan(group_name, new_o365_plan, is_group=True)
            self.sharepoint.verify_plan_association(plan=new_o365_plan, is_group=True)
        except Exception:
            raise CVTestStepFailure('Exception while verifying change o365 plan for auto associated group')

    @test_step
    def verify_change_o365_plan_for_auto_association_group(self):
        """Changes o365 plan for auto association group, verifies it and
        verifies o365 plan conflicts for common sites  - checks for 3 different scenarios"""
        try:
            self.o365_plan = self.tcinputs['Office365Plan3']
            self.verify_change_o365_plan(self.groups[1][1], self.o365_plan)
            all_group_sites_updated_props = self.update_o365_plan_in_properties(
                self.group_site_dict.get('ValidateSiteDetails'), self.tcinputs['Office365Plan'])
            all_web_sites_updated_props = self.update_o365_plan_in_properties(
                self.normal_site_dict.get('ValidateSiteDetails'), self.tcinputs['Office365Plan3'])
            self.sharepoint.verify_site_details({**all_group_sites_updated_props,
                                                 **all_web_sites_updated_props})

            self.o365_plan = self.tcinputs['Office365Plan4']
            self.verify_change_o365_plan(self.groups[0][1], self.o365_plan)
            updated_properties = self.update_o365_plan_in_properties(self.group_site_dict.get('ValidateSiteDetails'),
                                                                     self.o365_plan)
            self.sharepoint.verify_site_details({**self.normal_site_dict.get('ValidateSiteDetails'),
                                                 **updated_properties})

            self.o365_plan = self.tcinputs['Office365Plan2']
            self.verify_change_o365_plan(self.groups[1][1], self.o365_plan)
            updated_properties = self.update_o365_plan_in_properties(self.normal_site_dict.get('ValidateSiteDetails'),
                                                                     self.tcinputs['Office365Plan2'])
            self.sharepoint.verify_site_details({**self.group_site_dict.get('ValidateSiteDetails'),
                                                 **updated_properties})
        except Exception:
            raise CVTestStepFailure('Exception while verifying change o365 plan for auto associated group')

    def change_o365_plan_retention_and_verify_association(self, o365_plan, new_retention_period, updated_o365_plan):
        """Changes retention period for o365 plan and verifies o365 plan associated for all groups and teams sites"""
        self.sharepoint.change_o365_plan_retention(plan=o365_plan,
                                                   retention=new_retention_period)
        self.navigator.navigate_to_office365()
        self.sharepoint.access_office365_app(self.tcinputs['Name'])
        self.sharepoint.refresh_cache(wait_for_discovery_to_complete=True)
        time.sleep(120)
        updated_properties = self.update_o365_plan_in_properties(self.group_site_dict.get('ValidateSiteDetails'),
                                                                 updated_o365_plan)
        self.sharepoint.verify_site_details(updated_properties)

    @test_step
    def verify_o365_plan_association_for_retention_conflict_case(self):
        """Verifies o365 plan association for common sites when they have retention conflict
        after changing retention period for o365 plan"""
        try:
            new_o365_plan = self.tcinputs['Office365Plan5']
            self.sharepoint.change_office365_plan(self.groups[0][1], new_o365_plan, is_group=True)
            self.change_o365_plan_retention_and_verify_association(
                o365_plan=new_o365_plan, new_retention_period='75 Day(s)',
                updated_o365_plan=self.tcinputs['Office365Plan2'])

            self.change_o365_plan_retention_and_verify_association(
                o365_plan=self.tcinputs['Office365Plan2'], new_retention_period='70 Day(s)',
                updated_o365_plan=new_o365_plan)

            new_o365_plan = self.tcinputs['Office365Plan5']
            self.change_o365_plan_retention_and_verify_association(
                o365_plan=new_o365_plan, new_retention_period='65 Day(s)',
                updated_o365_plan=self.tcinputs['Office365Plan2'])

            self.change_o365_plan_retention_and_verify_association(
                o365_plan=new_o365_plan, new_retention_period='Indefinitely',
                updated_o365_plan=new_o365_plan)

            self.sharepoint.change_o365_plan_retention(plan=self.tcinputs['Office365Plan2'], retention='100 Day(s)')
        except Exception:
            raise CVTestStepFailure('Exception while verifying change retention period for o365 plan')

    @test_step
    def verify_remove_auto_association(self):
        """Removes auto association group from backup content and verifies it - checks for 3 different scenarios"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self.sharepoint.remove_from_content(self.groups[1][1], is_group=True)
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.REMOVED.value, self.groups[1][1], is_group=True)
            associated_sites_count = self.sharepoint.get_total_associated_sites_count()
            if (abs(associated_sites_count - self.total_num_of_sites[self.groups[0][1]]) > 10
                    or associated_sites_count == 0):
                raise Exception(f'All sites are not removed from backup content for {self.groups[1][1]} group')

            self.sharepoint.add_user_group(group_name=self.groups[1][0], plan=self.o365_plan)
            self.sharepoint.remove_from_content(self.groups[0][1], is_group=True)
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.REMOVED.value, self.groups[0][1], is_group=True)
            associated_sites_count = self.sharepoint.get_total_associated_sites_count()
            if (associated_sites_count < self.total_num_of_sites[self.groups[1][1]]
                    or associated_sites_count - self.total_num_of_sites[self.groups[1][1]] > 10
                    or associated_sites_count == 0):
                raise Exception(
                    f'All sites are removed from backup content for {self.groups[0][1]} group as not expected')

            self.sharepoint.remove_from_content(self.groups[1][1], is_group=True)
            self.sharepoint.verify_user_status(
                o365_constants.StatusTypes.REMOVED.value, self.groups[1][1], is_group=True)
            associated_sites_count = self.sharepoint.get_total_associated_sites_count()
            if associated_sites_count != 0:
                raise Exception(f'All sites are not removed from backup content for {self.groups[0][1]} group')
        except Exception:
            raise CVTestStepFailure('Exception while verifying remove auto associated group')

    def run(self):
        try:
            self.verify_all_groups_and_team_sites_auto_association()
            self.verify_all_web_sites_auto_association()
            self.verify_change_o365_plan_for_auto_association_group()
            self.verify_o365_plan_association_for_retention_conflict_case()
            self.verify_remove_auto_association()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_office365()
                self.sharepoint.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
