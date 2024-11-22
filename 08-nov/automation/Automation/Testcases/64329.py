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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import sys

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing content search verification
    after content indexing for exchange"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Verification of content search after Exchange Content Indexing"
        self.show_to_user = True
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            "IndexServer": None,
            "User": None,
            "O365Plan": None,
            "Name": None,
            "SearchView": None,
            "SearchKeyword": None,
            "ExpectedCount": None
        }

    def setup(self):
        """Setup function of this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console
                                           )

        self.tcinputs['GlobalAdmin'] = self.inputJSONnode['commcell']['AzureUsername']
        self.tcinputs['Password'] = self.inputJSONnode['commcell']['AzurePassword']

    @test_step
    def client_setup(self):
        """Creates Exchange client, Adds mailbox, runs backup and CI"""
        try:
            self.admin_console.close_popup()
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app()
            self.office365_obj.add_user(users=[self.tcinputs['User']], plan=self.tcinputs['O365Plan'])
            self.office365_obj.run_backup()
            self.office365_obj.run_ci_job(client_name=self.tcinputs['Name'])
        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)

    @test_step
    def _initialize_compliancesearch(self):
        """Initialize Objects for Compliance search"""
        self.app = ComplianceSearch(self.admin_console)
        gov_app = GovernanceApps(self.admin_console)

        navigator = self.admin_console.navigator
        navigator.navigate_to_governance_apps()

        gov_app.select_compliance_search()

    @test_step
    def set_preferences(self):
        """
            Set the Index Server, Search View in Preferences tab
            Set Datatype as OneDrive
        """
        self.app.set_indexserver_and_searchview_preference(
            self.tcinputs['IndexServer'], self.tcinputs['SearchView'])

        self.app.click_search_button()

    @test_step
    def validate_compliancesearch_results(self):
        """
            Validate Content Search from Compliance search page
        """
        try:
            custom_filter = CustomFilter(self.admin_console)
            custom_filter.apply_custom_filters_with_search(
                {"Client name": [self.tcinputs['Name']]})
        except Exception as ex:
            self.log.info(ex)
            self.log.info(f"Failed to filter with client name, check if the client is created")

        results = self.app.get_total_rows_count(self.tcinputs['SearchKeyword'])
        self.log.info(f"Compliance Search UI returned {results} results")
        self.log.info(f"Expected count is {self.tcinputs['ExpectedCount']}")

        if int(results) != int(self.tcinputs['ExpectedCount']):
            raise CVTestStepFailure(f'Compliance search count mismatch')
        else:
            self.log.info("Content search from Compliance search matches source data")

    def run(self):
        """Run function of this test case"""
        try:
            self.client_setup()
            self._initialize_compliancesearch()
            self.set_preferences()
            self.validate_compliancesearch_results()
            self.navigator.navigate_to_office365()
            self.office365_obj.delete_office365_app(self.tcinputs['Name'])

        except Exception as ex:
            handle_testcase_exception(self, ex)

        finally:
            self.log.info(f'Test case status: {self.status}')
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
