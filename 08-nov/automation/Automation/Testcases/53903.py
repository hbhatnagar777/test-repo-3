# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify Orchestration dashboard page loading without any errors."""

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import (OrchestrationDashboard, Dashboard)


from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Test case to verify Orchestration dashboard page is loading fine, and all the expected
    panes are present"""
    test_step = TestStep()

    def __init__(self):
        """Init method for test case class"""
        super(TestCase, self).__init__()
        self.name = "Admin console : Orchestration dashboard page verification"
        self.browser = None
        self.utils = None
        self.dashboard = None
        self.report = None
        self.admin_console = None
        self.expected_panes = []
        self.expected_headers = []

    def init_tc(self):
        """Initialize browser and redirect to page"""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.expected_headers = [header.value for header in OrchestrationDashboard
                                     if "header" in header.name]
            self.expected_panes = [pane.value for pane in OrchestrationDashboard
                                   if "pane" in pane.name]
            self.dashboard = Dashboard(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def verify_dashboard_navigation(self):
        """Navigate to orchestration dashboard without any errors"""
        self.dashboard.navigate_to_given_dashboard("Orchestration Dashboard")

    @test_step
    def verify_dashboard_page(self):
        """
        Verify Orchestration dashboard page is not having any errors/notifications
        """
        if self.browser.driver.title != "Orchestration Dashboard":
            raise CVTestStepFailure("Expecting [Orchestration Dashboard] title of page"
                                    ", but [%s] is the currently title of the page" %
                                    self.browser.driver.title)
        notification = self.dashboard.get_notification()
        if notification:
            raise CVTestStepFailure("Dashboard page has Notification error [%s]" % notification)
        self.log.info("Dashboard page load is successful")

    @test_step
    def verify_header_and_pane_titles(self):
        """Verify all panes are present in Orchestration dashboard page"""
        titles = self.dashboard.get_header_and_dash_pane_titles()
        headers = []
        for key, value in titles.items():
            headers.append(key)
            if sorted(value) == sorted(self.expected_panes):
                self.log.info("panes for %s header are verified successfully", key)
        if sorted(headers) == sorted(self.expected_headers):
            self.log.info("Dashboard headers and panes are verified successfully")
        else:
            raise CVTestStepFailure("Dashboard headers are not displayed correctly")

    @staticmethod
    def get_mapped_title(header_name, pane_name, entity_name=None):
        """Get expected titles of pane details page"""

        _mapped_items = [{"h_name": OrchestrationDashboard.header_databases.value,
                          "p_name": None,
                          "entity": None,
                          "title": "Instances"},
                         {"h_name": OrchestrationDashboard.header_databases.value,
                          "p_name": OrchestrationDashboard.pane_overview.value,
                          "entity": OrchestrationDashboard.entity_servers.value,
                          "title": "Instances"},
                         {"h_name": OrchestrationDashboard.header_databases.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_clones.value,
                          "title": "Instances"},
                         {"h_name": OrchestrationDashboard.header_databases.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_cloud_migration.value,
                          "title": "Cloud Migrations"},
                         {"h_name": OrchestrationDashboard.header_databases.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_failover_runs.value,
                          "title": "Job history"},
                         {"h_name": OrchestrationDashboard.header_file_servers.value,
                          "p_name": None,
                          "entity": None,
                          "title": "File servers"},
                         {"h_name": OrchestrationDashboard.header_file_servers.value,
                          "p_name": OrchestrationDashboard.pane_overview.value,
                          "entity": OrchestrationDashboard.entity_file_servers.value,
                          "title": "File servers"},
                         {"h_name": OrchestrationDashboard.header_file_servers.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_live_mounts.value,
                          "title": "Live Mount Jobs"},
                         {"h_name": OrchestrationDashboard.header_file_servers.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_failover_runs.value,
                          "title": "Job history"},
                         {"h_name": OrchestrationDashboard.header_vms.value,
                          "p_name": None,
                          "entity": None,
                          "title": "Hypervisors"},
                         {"h_name": OrchestrationDashboard.header_vms.value,
                          "p_name": OrchestrationDashboard.pane_overview.value,
                          "entity": OrchestrationDashboard.entity_vms.value,
                          "title": "Virtual machines"},
                         {"h_name": OrchestrationDashboard.header_vms.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_live_mounts.value,
                          "title": "Live Mount Jobs"},
                         {"h_name": OrchestrationDashboard.header_vms.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_cloud_migration.value,
                          "title": "Cloud Migrations"},
                         {"h_name": OrchestrationDashboard.header_vms.value,
                          "p_name": OrchestrationDashboard.pane_last_month_stats.value,
                          "entity": OrchestrationDashboard.entity_failover_runs.value,
                          "title": "Job history"}]
        for pane in _mapped_items:
            if pane['h_name'] == header_name and pane["p_name"] == pane_name and \
                    pane["entity"] == entity_name:
                return pane["title"]
        raise CVTestStepFailure("[%s]Pane is not mapped" % pane_name)

    @test_step
    def verify_pane_details_page(self):
        """Access details page of pane and verify the page titles are correct"""

        hierarchical_dict = {
            OrchestrationDashboard.header_databases:
                {OrchestrationDashboard.pane_overview: [OrchestrationDashboard.entity_servers],
                 OrchestrationDashboard.pane_last_month_stats:
                     [OrchestrationDashboard.entity_clones,
                      OrchestrationDashboard.entity_cloud_migration,
                      OrchestrationDashboard.entity_failover_runs]},
            OrchestrationDashboard.header_file_servers:
                {OrchestrationDashboard.pane_overview:
                     [OrchestrationDashboard.entity_file_servers],
                 OrchestrationDashboard.pane_last_month_stats:
                     [OrchestrationDashboard.entity_live_mounts,
                      OrchestrationDashboard.entity_failover_runs]},
            OrchestrationDashboard.header_vms:
                {OrchestrationDashboard.pane_overview: [OrchestrationDashboard.entity_vms],
                 OrchestrationDashboard.pane_last_month_stats:
                     [OrchestrationDashboard.entity_live_mounts,
                      OrchestrationDashboard.entity_cloud_migration,
                      OrchestrationDashboard.entity_failover_runs]}}
        for header, panes in hierarchical_dict.items():
            if panes:
                for pane, entities in panes.items():
                    if entities:
                        for each_value in entities:
                            self.log.info("Accessing details page of header:%s, Pane:%s, "
                                          "Entity:%s", header.value, pane.value,
                                          each_value.value)
                            self.dashboard.access_details_page(pane_name=pane.value,
                                                               entity_name=each_value.value,
                                                               header_name=header.value)
                            self.validate_title(header.value,
                                                pane.value,
                                                entity=each_value.value)
                    else:
                        self.log.info("Accessing details page of Header:%s, Pane:%s",
                                      header.value, pane.value)
                        self.dashboard.access_details_page(header_name=header.value,
                                                           pane_name=pane.value)
                        self.validate_title(header.value,
                                            pane.value,
                                            entity=entities)
            else:
                self.dashboard.access_details_page(header_name=header.value)
                self.validate_title(header.value, pane=None, entity=None)

    def validate_title(self, header, pane, entity):
        """Access pane details page and verify page titles"""
        expected_title = self.get_mapped_title(header, pane, entity_name=entity)
        page_title = self.dashboard.get_page_title()
        if page_title == expected_title:
            self.log.info("Verified title for [%s] header, [%s] pane, [%s] entity",
                          header, pane, entity)
            self.browser.driver.back()
            self.dashboard.wait_for_completion()
        else:
            raise CVTestStepFailure("Title did not match for [%s] pane, [%s] entity,"
                                    "[%s] title is Expected, [%s] title is found on page" %
                                    (pane, entity, expected_title, page_title))

    def run(self):
        try:
            self.init_tc()
            self.verify_dashboard_navigation()
            self.verify_dashboard_page()
            self.verify_header_and_pane_titles()
            self.verify_pane_details_page()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
