# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify Virtualization dashboard page loading without any errors."""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import (RVirtualizationDashboard as RVD, RDashboard)

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Test case to verify Virtualization dashboard page is loading fine, and all the expected panes are
    present"""
    test_step = TestStep()

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Admin console Virtualization Dashboard page verification"
        self.browser = None
        self.utils = None
        self.dashboard = None
        self.report = None
        self.admin_console = None
        self.expected_panes = []

    def init_tc(self):
        """Initialize browser and redirect to page"""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"],
            )
            self.expected_panes = [pane.value for pane in RVD
                                   if "pane" in pane.name]
            self.dashboard = RDashboard(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def verify_dashboard_navigation(self):
        """Navigate to virtualization dashboard without any errors"""
        self.admin_console.navigator.navigate_to_virtualization()

    @test_step
    def verify_dashboard_page(self):
        """
        Verify virtualization dashboard page is not having any errors/notifications
        """
        if self.browser.driver.title != RVD.title.value:
            raise CVTestStepFailure(f"Expecting 'Overview' title of landing page but {self.browser.driver.title} is the title of the page.")
        notification = self.admin_console.get_notification()
        if notification:
            raise CVTestStepFailure(f"Dashboard page has Notification error {notification}")
        self.log.info("Dashboard page load is successful")

    @test_step
    def verify_pane_titles(self):
        """Verify all panes are present in dashboard page"""
        if set(self.dashboard.get_dash_pane_titles()) != set(self.expected_panes):
            raise CVTestStepFailure(f"Expected panes: {str(self.expected_panes)} are not present on dashboard."
                                    f"Existing panes: {str(self.dashboard.get_dash_pane_titles())}")                                  
        self.log.info("Dashboard pane's titles are verified successfully")

    @staticmethod
    def get_mapped_title(pane_name, entity_name=None):
        """Get expected titles of pane details page"""

        _mapped_items = [{"p_name": RVD.pane_hypervisors.value,
                          "entity": None,
                          "title": "Hypervisors"},
                         {"p_name": RVD.pane_vms.value,
                          "entity": RVD.entity_protected.value,
                          "title": "Virtual machines"},
                         {"p_name": RVD.pane_vms.value,
                          "entity": RVD.entity_not_protected.value,
                          "title": "Unprotected VMs"},
                         {"p_name": RVD.pane_vms.value,
                          "entity": RVD.entity_backed_up_with_error.value,
                          "title": "Virtual machines"},
                         {"p_name": RVD.pane_sla.value,
                          "entity": None,
                          "title": "VM Backup Health"},
                         {"p_name": RVD.pane_jobs_in_last_24_hours.value,
                          "entity": RVD.entity_running.value,
                          "title": "Active jobs"},
                         {"p_name": RVD.pane_jobs_in_last_24_hours.value,
                          "entity": RVD.entity_success.value,
                          "title": "Job history"},
                         {"p_name": RVD.pane_jobs_in_last_24_hours.value,
                          "entity": RVD.entity_failed.value,
                          "title": "Job history"},
                         {"p_name": RVD.pane_jobs_in_last_24_hours.value,
                          "entity": RVD.entity_events.value,
                          "title": "Events"},
                         {"p_name": RVD.pane_last_week_backup_job_summary.value,
                          "entity": None,
                          "title": "Job history"},
                         {"p_name": RVD.pane_largest_hypervisors.value,
                          "entity": None,
                          "title": "Hypervisors"}]
        for pane in _mapped_items:
            if pane["p_name"] == pane_name and pane["entity"] == entity_name:
                return pane["title"]
        raise CVTestStepFailure(f"{pane_name} pane is not mapped.")

    @test_step
    def verify_pane_details_page(self):
        """Access details page of pane and verify the page titles are correct"""
        panes_dict = {
            RVD.pane_hypervisors: None,
            RVD.pane_vms: [RVD.entity_protected,
                           RVD.entity_not_protected,
                           RVD.entity_backed_up_with_error],
            RVD.pane_sla: None,
            RVD.pane_jobs_in_last_24_hours:
                [RVD.entity_running,
                 RVD.entity_success,
                 RVD.entity_failed,
                 RVD.entity_events],
            RVD.pane_last_week_backup_job_summary: None,
            RVD.pane_largest_hypervisors: None
        }
        for pane, entities in panes_dict.items():
            if entities:
                for each_value in entities:
                    self.log.info(f"Accessing details page of Pane:{pane.value}, Entity:{each_value.value}")
                    self.dashboard.access_details_page(pane_name=pane.value,
                                                       entity_name=each_value.value)
                    self.validate_title(pane.value, entity=each_value.value)
            else:
                self.log.info(f"Accessing details page of Pane:{pane.value}")
                self.dashboard.access_details_page(pane_name=pane.value)
                self.validate_title(pane.value, entity=entities)

    def validate_title(self, pane, entity):
        """Access pane details page and verify page titles"""
        expected_title = self.get_mapped_title(pane, entity_name=entity)
        handles = self.browser.driver.window_handles
        size = len(handles)
        page_title = None
        if size > 1:
            parent_handle = self.browser.driver.current_window_handle
            for x in range(size):
                if handles[x] != parent_handle:
                    self.browser.driver.switch_to.window(handles[x])
                    page_title = self.dashboard.get_page_title()
                    self.browser.driver.close()
                    break
            self.browser.driver.switch_to.window(parent_handle)
            self.admin_console.wait_for_completion()
        else:
            page_title = self.dashboard.get_page_title()
            self.browser.driver.back()
            self.admin_console.wait_for_completion()

        if page_title == expected_title:
            self.log.info(f"Verified title for {pane} pane, {entity} entity")
        else:
            raise CVTestStepFailure(f"Title did not match for {pane} pane, {entity} entity. {expected_title}"
                                    f" title is expected. {page_title} title is found on page.")

    def run(self):
        try:
            self.init_tc()
            self.verify_dashboard_navigation()
            self.verify_dashboard_page()
            self.verify_pane_titles()
            self.verify_pane_details_page()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
