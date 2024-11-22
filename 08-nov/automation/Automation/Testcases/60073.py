# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of browse from office365 apps page, backupset restore,
selected sites browse, point in time restore browse and basic search validation.

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

Input Example:

    {
        "ExpectedSearchFilterResult": [
            [
              {
                "Name": "https://cvautomation.sharepoint.com/sites/SPAutomationWeb12",
                "Title": "SPAutomationWeb12",
                "Type": "Site"
              }
            ],
            [
              {
                "Name": "subsite_1",
                "Title": "subsite_1",
                "Type": "Site"
              }
            ]
          ],
        "Sites": {
            "https://cvautomation.sharepoint.com/sites/SPAutomationWeb12": "SPAutomationWeb12",
            "https://cvautomation.sharepoint.com/sites/SPAutomationWeb13": "SPAutomationWeb13",
            "https://cvautomation.sharepoint.com/sites/SPAutomationWeb13/subsite_1": "subsite_1"
          },
        "ExpectedDefaultBrowseTableView": [
            {
              "Name": "https://cvautomation.sharepoint.com/sites/SPAutomationWeb12",
              "Title": "SPAutomationWeb12",
              "Type": "Site"
            },
            {
              "Name": "https://cvautomation.sharepoint.com/sites/SPAutomationWeb13",
              "Title": "SPAutomationWeb13",
              "Type": "Site"
            },
            {
              "Name": "subsite_1",
              "Title": "subsite_1",
              "Type": "Site"
            }
          ],
        "BrowseTreeViewTerms": [
            "cvautomation",
            "SPAutomationWeb12",
            "SPAutomationWeb13",
            "subsite_1",
            "Contents"
          ]
    }


"""

from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.sharepoint import SharePoint
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Office365Pages import constants as o365_constants


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "SharePoint V2 Web Automation: Verification of browse from office365 apps page, " \
                    "backupset restore, selected sites browse and basic search validation"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.sharepoint = None
        self.driver = None
        self.sites = {}
        self.site_url_list = []
        self.ignore_folders = ['Composed Looks', 'Master Page Gallery']
        self.api_files = []
        self.api_all_lists = []

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
            self.driver = self.browser.driver
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.sites = self.tcinputs['Sites']
            self.site_url_list = list(self.sites.keys())
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = SharePoint.AppType.share_point_online
            self.sharepoint = SharePoint(self.tcinputs, self.admin_console, is_react=True)
            self._initialize_sp_api_object()
            self.sharepoint.create_office365_app()
            self.sharepoint.wait_for_discovery_to_complete()
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _initialize_sp_api_object(self):
        """Initializes SharePoint object to make api calls"""
        self.sp_api_object = SharePointOnline(self)
        self.sp_api_object.azure_app_id = self.tcinputs.get("ClientId", "")
        self.sp_api_object.azure_app_secret = self.tcinputs.get("ClientSecret", "")
        self.sp_api_object.azure_app_tenant_id = self.tcinputs.get("AzureDirectoryId", "")

    @staticmethod
    def get_list_diff(list1, list2):
        """Returns difference between two lists

            Args:

                list1   (list)      :   First list

                list2   (list)      :   Second list

            Returns:

                list[tuple]         :   Difference between the two lists
        """
        if len(list1) == 0 or not isinstance(list1[0], dict):
            return [i for i in list2 if i not in list1]

        diff_list = []
        for dict1, dict2 in zip(list1, list2):
            common_keys = set(dict1.keys()).intersection(set(dict2.keys()))

            if not common_keys:
                diff_list.append((dict1, dict2))
                continue

            for key in common_keys:
                if dict1[key] != dict2[key]:
                    diff_list.append((dict1, dict2))

        return diff_list

    def verify_default_browse(self, expected_browse_table_content, expected_default_browse_tree_view_content):
        """Verifies default browse view when restore is clicked
            Args:
                expected_browse_table_content (list)    --  list of dictionaries of expected items in browse table

                expected_default_browse_tree_view_content (list)    --  list of tree view terms
                    Example:
                        ['Sites', 'TestSite', 'Contents', 'Subsites', 'TestSite2']
        """
        browse_table_content = self.sharepoint.get_browse_table_content()
        if self.get_list_diff(browse_table_content, expected_browse_table_content):
            raise Exception(f'Default browse table content is not displayed as expected\n'
                            f'Actual: {browse_table_content}\n'
                            f'Expected: {expected_browse_table_content}\n')
        browse_tree_view_content = self.sharepoint.get_browse_tree_view_content()
        if self.get_list_diff(browse_tree_view_content, expected_default_browse_tree_view_content):
            raise Exception(f'Default browse tree view is not displayed as expected\n'
                            f'Actual: {browse_tree_view_content}\n'
                            f'Expected: {expected_default_browse_tree_view_content}\n')

    def verify_custom_browse(self, expected_browse_tree_view_content, site_name):
        """Verifies browse by performing some actions on browse page
            Args:
                expected_browse_tree_view_content (list)    --  list of tree view terms

                site_name (str)                             --  name of the site

        """
        for title in expected_browse_tree_view_content:
            self.sharepoint.click_item_in_browse_tree_view(title)
        self.sharepoint.click_item_in_browse_tree_view('Documents')

        # verifying browse for list of files in a library
        browse_table_content = self.sharepoint.get_browse_table_content(columns=['Name'])
        if not self.api_files:
            self.sp_api_object.site_url = self.site_url_list[-1]
            for file in self.sp_api_object.get_all_files('Shared Documents'):
                self.api_files.append({
                    'Name': file.get('Name')
                })
        if self.get_list_diff(browse_table_content, self.api_files):
            raise Exception(f'Browse table content is not displayed as expected\n'
                            f'Expected : {self.api_files}\n'
                            f'Actual : {browse_table_content}\n')
        # verifying tree view hierarchy for a site
        if not self.api_all_lists:
            self.api_all_lists = [item['Title'] for item in self.sp_api_object.get_all_lists_metadata()
                                  if item['Title'] not in self.ignore_folders]
            self.api_all_lists.append('images')
        expected_browse_tree_view_content.extend(self.api_all_lists)
        expected_browse_tree_view_content.append('Subsites')
        self.sharepoint.click_browse_bread_crumb_item(site_name)
        browse_tree_view_content = self.sharepoint.get_browse_tree_view_content(active_tree=True)
        if site_name not in expected_browse_tree_view_content:
            expected_browse_tree_view_content.append(site_name)
        if self.get_list_diff(browse_tree_view_content, expected_browse_tree_view_content) and \
                len(browse_tree_view_content) != len(expected_browse_tree_view_content):
            raise Exception(f'Browse tree view hierarchy is not displayed as expected\n'
                            f'Expected : {expected_browse_tree_view_content}\n'
                            f'Actual : {browse_tree_view_content}\n')

    def verify_global_search(self, expected_result, keyword=None):
        """Applies global search with given keyword and verifies it
            Args:
                expected_result (dict)  --  list of dictionaries of expected items in browse table after applying search

                keyword (str)           --  keyword to apply search filter
        """
        if not keyword:
            keyword = expected_result[0]['Title']
        global_search_result = self.sharepoint.apply_global_search_filter_and_get_result(keyword,
                                                                                         ['Title', 'Name', 'Type'])
        if self.get_list_diff(global_search_result, expected_result):
            raise Exception(f"Default browse table content is not displayed as expected "
                            f"when applied filter for keyword {keyword}\n"
                            f"Actual : {global_search_result}\n"
                            f"Expected : {expected_result}")

    def verify_site_browse(self):
        """Verifies browse for selected site
        """
        expected_tree_view_terms = [self.tcinputs['BrowseTreeViewTerms'][-2], 'Contents', 'Subsites']
        expected_default_browse_table_view = []
        for title in expected_tree_view_terms[1:]:
            expected_default_browse_table_view.append({
                'Title': title,
                'Name': title,
                'Type': title
            })
        self.verify_default_browse(expected_default_browse_table_view,
                                   expected_tree_view_terms)
        self.verify_custom_browse(['Contents'], self.tcinputs['BrowseTreeViewTerms'][-2])
        self.verify_global_search(expected_result=self.tcinputs['ExpectedSearchFilterResult'][1])

    def verify_full_browse(self):
        """Verifies browse for all sites
        """
        self.verify_default_browse(self.tcinputs['ExpectedDefaultBrowseTableView'][:-1],
                                   self.tcinputs['BrowseTreeViewTerms'][:-2])
        expected_browse_tree_view_content = [
            self.tcinputs['BrowseTreeViewTerms'][2], 'Subsites',
            self.tcinputs['BrowseTreeViewTerms'][-2], 'Contents']
        self.verify_custom_browse(expected_browse_tree_view_content, self.tcinputs['BrowseTreeViewTerms'][2])
        for search_filter_item in self.tcinputs['ExpectedSearchFilterResult']:
            self.verify_global_search(expected_result=search_filter_item)

    @test_step
    def associate_sites_and_run_backup(self):
        """Associates sites and runs backup"""
        try:
            self.sharepoint.add_user(users=self.sites)
            backupset_level_bkp = self.sharepoint.initiate_backup()
            self.sharepoint.verify_backup_job(job_id=backupset_level_bkp)
        except Exception:
            raise CVTestStepFailure('Exception while associating sites or running backup')

    @test_step
    def verify_client_level_browse(self):
        """Opens browse page from office 365 apps page and validates browse"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.click_client_level_restore(self.tcinputs['Name'])
            self.verify_full_browse()
        except Exception:
            raise CVTestStepFailure('Exception while verifying client level browse')

    @test_step
    def verify_backupset_level_browse(self):
        """Opens browse page from sites tab and validates browse"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_backupset_level_restore()
            self.verify_full_browse()
        except Exception:
            raise CVTestStepFailure('Exception while verifying backupset level browse')

    @test_step
    def verify_single_site_browse(self):
        """Selects a site, clicks restore documents of it and verifies browse"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_site_level_restore(sites=self.site_url_list[-1:])
            self.verify_site_browse()
        except Exception:
            raise CVTestStepFailure('Exception while verifying single site browse')

    @test_step
    def verify_multiple_site_browse(self):
        """Selects multiple sites, clicks restore documents of them and verifies browse"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self.admin_console.access_tab(o365_constants.SharePointOnline.ACCOUNT_TAB.value)
            self.sharepoint.click_site_level_restore(sites=self.site_url_list)
            expected_tree_view_terms = [self.tcinputs['BrowseTreeViewTerms'][0],
                                        self.tcinputs['BrowseTreeViewTerms'][1],
                                        self.tcinputs['BrowseTreeViewTerms'][3]]
            self.verify_default_browse(self.tcinputs['ExpectedDefaultBrowseTableView'],
                                       expected_tree_view_terms)
            expected_browse_tree_view_content = [
                self.tcinputs['BrowseTreeViewTerms'][-2], 'Contents']
            self.verify_custom_browse(expected_browse_tree_view_content, self.tcinputs['BrowseTreeViewTerms'][-2])
            self.verify_global_search(expected_result=self.tcinputs['ExpectedSearchFilterResult'][1])
        except Exception:
            raise CVTestStepFailure('Exception while verifying multiple sites browse')

    @test_step
    def verify_point_in_time_browse(self):
        """Clicks on a site title in app page, clicks restore and verifies point in time browse"""
        try:
            self.navigator.navigate_to_office365()
            self.sharepoint.access_office365_app(self.tcinputs['Name'])
            self.admin_console.access_tab(o365_constants.SharePointOnline.OVERVIEW_TAB.value)
            self.sharepoint.click_point_in_time_browse()
            self.verify_full_browse()
        except Exception:
            raise CVTestStepFailure('Exception while verifying point in time browse')

    def run(self):
        try:
            self.associate_sites_and_run_backup()
            self.verify_client_level_browse()
            self.verify_backupset_level_browse()
            self.verify_single_site_browse()
            self.verify_multiple_site_browse()
            self.verify_point_in_time_browse()
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
