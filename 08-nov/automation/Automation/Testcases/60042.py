# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for  SharePoint v2 - Verification of Auto-discovery and Refresh Cache Operation

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import time
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
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
        self.name = "SharePoint V2: Verification of Auto-discovery and Refresh Cache Operation"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.sp_api_object = None
        self.total_num_of_root_sites = None
        self.total_num_of_subsites = None
        self.o365_plan = None
        self.teams_site_dict = None
        self.normal_site_dict = None
        self.testdata = None
        self.share_point_data_flag = False
        self.restore_obj = None
        self.subsites_metadata = {}

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
            self.o365_plan = self.tcinputs['Office365Plan']
            self.teams_site_dict = self.tcinputs['TeamsSite']
            self.normal_site_dict = self.tcinputs['NormalSite']
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)
            self._initialize_sp_api_object()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _initialize_sp_api_object(self):
        """Initializes SharePoint object to make api calls"""
        self.sp_api_object = SharePointOnline(self)
        self.sp_api_object.site_url_list = [self.normal_site_dict['URL'], self.teams_site_dict['URL']]
        self.sp_api_object.site_url = self.teams_site_dict['URL']
        self.sp_api_object.azure_app_id = self.tcinputs.get("ClientId", "")
        self.sp_api_object.azure_app_secret = self.tcinputs.get("ClientSecret", "")
        self.sp_api_object.azure_app_tenant_id = self.tcinputs.get("AzureDirectoryId", "")
        self.sp_api_object.tenant_url = self.tcinputs.get("SiteAdminUrl", "")
        self.sp_api_object.global_administrator = self.tcinputs.get("GlobalAdministrator", "")
        self.sp_api_object.global_administrator_password = self.tcinputs.get("GlobalAdministrator Password", "")
        self.total_num_of_root_sites, self.total_num_of_subsites, _ = self.sp_api_object.get_sites_count(
            get_only_root_sites=False)
        self.testdata = TestData(self.sp_api_object)
        self.restore_obj = Restore(self.sp_api_object)

    def clean_up_sites(self):
        """Cleans up the test sites used in test case"""
        try:
            for site in self.sp_api_object.site_url_list:
                self.sp_api_object.site_url = site
                self.log.info(f"Cleaning up all subsites for {site} if exists")
                subsite_end_url_list = ["subsite_1", "subsite_2", "subsite_3", "subsite_1_rename"]
                self.sp_api_object.delete_subsites(subsite_end_url_list)
        except Exception as exception:
            self.log.exception(f"Exception while deleting sites: %s", str(exception))
            raise exception

    @test_step
    def create_test_subsites(self):
        """Creates test subsites
        """
        try:
            self.clean_up_sites()
            for site in self.sp_api_object.site_url_list:
                self.sp_api_object.site_url = site
                _, self.subsites_metadata[site] = self.testdata.create_test_subsites()
        except Exception:
            raise CVTestStepFailure('Exception while creating test subsites')

    @test_step
    def verify_discovery(self):
        """Waits till the completion of discovery and verifies discovery stats"""
        try:
            self.sharepoint.wait_for_discovery_to_complete(time_out=600, poll_interval=120)
            self.sharepoint.open_discovery_stats_dialog()
            discovery_stats = self.sharepoint.get_discovery_dialog_stats()
            self.admin_console.refresh_page()
            if discovery_stats['Status'] != 'Completed' or discovery_stats['Progress'] != '100%' or \
                    abs(int(discovery_stats['Total number of sites']) - self.total_num_of_root_sites) > 10 or \
                    abs(int(discovery_stats['Total number of subsites']) - self.total_num_of_subsites) > 10:
                raise CVTestStepFailure(f'Discovery stats are not validated\n'
                                        f'Stats displayed : {discovery_stats}\n'
                                        f'Total sites count from graph api :{self.total_num_of_root_sites}')
            else:
                self.total_num_of_root_sites = int(discovery_stats['Total number of sites'])
                self.total_num_of_subsites = int(discovery_stats['Total number of subsites'])
            total_discovered_sites = self.sharepoint.get_sites_count_under_add_webs()
            if total_discovered_sites != self.total_num_of_root_sites + self.total_num_of_subsites:
                raise CVTestStepFailure(f'All sites are not listed under add webs after discovery')
        except Exception:
            raise CVTestStepFailure('Exception while verifying discovery')

    @test_step
    def make_site_level_changes(self):
        """Makes site level changes - Add/Edit/Delete"""
        try:
            for site in self.sp_api_object.site_url_list:
                self.sp_api_object.site_url = site
                self.log.info("Creating a sub site after discovery")
                title = "Test Subsite - 3"
                url_end = "subsite_3"
                self.subsites_metadata[site].update(self.sp_api_object.create_subsites([{
                    "Title": title,
                    "Url End": url_end
                }]))
                if site == self.normal_site_dict['URL']:
                    # Editing site url/title for modern sites is not supported using REST API
                    # so not validating edit option for modern teams/group site
                    self.log.info("Edit site level properties of a subsite")
                    subsite_url = "/" + "/".join(self.sp_api_object.site_url.split("/")[3:]) + "/subsite_1"
                    self.subsites_metadata[site][subsite_url]['Old Url End'] = self.subsites_metadata.get(site) \
                        .get(subsite_url).get('Url End')
                    self.subsites_metadata[site][subsite_url]['Url End'] = self.subsites_metadata.get(site).get(
                        subsite_url).get('Url End') + "_rename"
                    self.subsites_metadata[site][subsite_url]['Title'] = self.subsites_metadata.get(site).get(
                        subsite_url).get('Title') + " - Rename"
                    prop_dict = {
                        'ServerRelativeUrl': self.subsites_metadata[site][subsite_url].get('Url End'),
                        'Title': self.subsites_metadata[site][subsite_url].get('Title')
                    }
                    self.sp_api_object.update_subsite_level_properties(prop_dict,
                                                                       self.subsites_metadata[site][subsite_url].
                                                                       get('Old Url End'))
                    self.log.info(f"New properties of subsite are\n URL: {self.sp_api_object.site_url}/"
                                  f"{self.subsites_metadata[site][subsite_url].get('Url End')}\n Title: "
                                  f"{self.subsites_metadata[site][subsite_url].get('Title')}")
                self.log.info("Deleting the subsite")
                self.sp_api_object.delete_subsite("subsite_2")

        except Exception:
            raise CVTestStepFailure('Exception while making site level changes')

    @test_step
    def refresh_cache_and_verify_site_properties(self):
        """Runs discovery after making site level changes and verifies sites properties after discovery"""
        try:
            self.sharepoint.refresh_cache(time_out=600, poll_interval=120)
            self.sharepoint.open_discovery_stats_dialog()
            discovery_stats = self.sharepoint.get_discovery_dialog_stats()
            self.admin_console.refresh_page()
            # Plan reconciliation happens after completion of discovery, waiting for plan reconciliation to complete
            time.sleep(120)
            if discovery_stats['Status'] != 'Completed' or discovery_stats['Progress'] != '100%' or \
                    (int(discovery_stats['Total number of sites']) - self.total_num_of_root_sites > 10):
                raise CVTestStepFailure(f'Discovery stats are not validated\n'
                                        f'Stats displayed : {discovery_stats}\n'
                                        f'Expected Sites Count : {self.total_num_of_root_sites}')

            teams_sites_details = {self.teams_site_dict['URL']: {}}
            teams_sites_details[self.teams_site_dict['URL']]['Name'] = self.teams_site_dict['Title']
            teams_sites_details[self.teams_site_dict['URL']]['Office 365 plan'] = self.o365_plan
            teams_sites_details[self.teams_site_dict['URL']]['Last backup'] = 'Not processed'
            self.sharepoint.verify_site_details(teams_sites_details)

            normal_sites_details = {self.normal_site_dict['URL']: {}}
            normal_sites_details[self.normal_site_dict['URL']]['Name'] = self.normal_site_dict['Title']
            normal_sites_details[self.normal_site_dict['URL']]['Office 365 plan'] = self.o365_plan
            normal_sites_details[self.normal_site_dict['URL']]['Last backup'] = 'Not processed'
            self.sharepoint.verify_site_details(normal_sites_details)
        except Exception:
            raise CVTestStepFailure('Exception while verifying discovery')

    def run(self):
        try:
            self.create_test_subsites()
            self.sharepoint.create_office365_app()
            self.verify_discovery()
            self.sharepoint.add_user_group(group_name='All team sites')
            self.make_site_level_changes()
            self.refresh_cache_and_verify_site_properties()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.clean_up_sites()
                self.navigator.navigate_to_office365()
                self.sharepoint.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
