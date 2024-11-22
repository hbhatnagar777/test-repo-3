# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify appliance dashboard page loading without any errors."""
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import (ApplianceDashboard, Dashboard)

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Test case to verify appliance dashboard page is loading fine, and all the expected panes are
    present"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin console appliance Dashboard page verification"
        self.browser = None
        self.utils = None
        self.dashboard = None
        self.report = None
        self.expected_panes = []

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
            self.expected_panes = [pane.value for pane in ApplianceDashboard
                                   if "pane" in pane.name]
            self.dashboard = Dashboard(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def verify_default_landing_page(self):
        """Verify default landing page appliance dashboard after login"""
        if self.browser.driver.title != "Appliance Dashboard":
            raise CVTestStepFailure("Expecting [Appliance Dashboard]title of landing page, but "
                                    "[%s] is the currently title of the page" %
                                    self.browser.driver.title)

    @test_step
    def verify_dashboard_page(self):
        """
        Verify dashboard page is not having any errors/notifications
        """
        notification = self.dashboard.get_notification()
        if notification:
            raise CVTestStepFailure("Dashboard page has Notification error [%s]" % notification)
        self.log.info("Dashboard page load is successful")

    @test_step
    def verify_pane_titles(self):
        """Verify all panes are present in dashboard page"""
        titles = self.dashboard.get_dash_pane_titles()
        if sorted(titles) != sorted(self.expected_panes):
            raise CVTestStepFailure("Expected [%s] panes are not present in dashboard page. "
                                    "Existing panes are [%s]" % (str(self.expected_panes),
                                                                 str(titles)))
        self.log.info("Dashboard pane's titles are verified successfully")

    @staticmethod
    def get_mapped_title(pane_name, entity_name=None):
        """Get expected titles of pane details page"""
        _mapped_items = [{"p_name": ApplianceDashboard.pane_environment.value,
                          "entity": ApplianceDashboard.entity_appliances.value,
                          "title": "Appliances"},
                         {"p_name": ApplianceDashboard.pane_environment.value,
                          "entity": ApplianceDashboard.entity_servers.value, "title": "Servers"},
                         {"p_name": ApplianceDashboard.pane_environment.value,
                          "entity": ApplianceDashboard.entity_vms.value, "title": "VMs"},
                         {"p_name": ApplianceDashboard.pane_environment.value,
                          "entity": ApplianceDashboard.entity_critical_alerts.value,
                          "title": "Triggered alerts"},

                         {"p_name": ApplianceDashboard.pane_needs_attentions.value,
                          "entity": ApplianceDashboard.entity_servers.value,
                          "title": "Servers need attention"},
                         {"p_name": ApplianceDashboard.pane_needs_attentions.value,
                          "entity": ApplianceDashboard.entity_infrastructures.value,
                          "title": "Infrastructures need attention"},
                         {"p_name": ApplianceDashboard.pane_needs_attentions.value,
                          "entity": ApplianceDashboard.entity_jobs.value,
                          "title": "Jobs need attention"},

                         {"p_name": ApplianceDashboard.pane_system.value,
                          "entity": None, "title": "Infrastructure Load"},

                         {"p_name": ApplianceDashboard.pane_hardware.value,
                          "entity": None, "title": "Appliance Hardware Report"},

                         {"p_name": ApplianceDashboard.pane_disk_space.value, "entity": None,
                          "title": "Disk Library Utilization"},

                         {"p_name": ApplianceDashboard.pane_sla.value, "entity": None,
                          "title": "Recovery Readiness"},

                         {"p_name": ApplianceDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ApplianceDashboard.entity_running.value,
                          "title": "Active jobs"},
                         {"p_name": ApplianceDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ApplianceDashboard.entity_success.value,
                          "title": "Job history"},
                         {"p_name": ApplianceDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ApplianceDashboard.entity_failed.value,
                          "title": "Job history"},
                         {"p_name": ApplianceDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ApplianceDashboard.entity_critical_events.value,
                          "title": "Events"}]

        for pane in _mapped_items:
            if pane["p_name"] == pane_name and pane["entity"] == entity_name:
                return pane["title"]
        raise CVTestStepFailure("[%s]Pane is not mapped" % pane_name)

    @test_step
    def verify_pane_details_page(self):
        """Access details page of pane and verify the page titles are correct"""
        panes_dict = {
            ApplianceDashboard.pane_environment: [ApplianceDashboard.entity_servers,
                                                  ApplianceDashboard.entity_vms,
                                                  ApplianceDashboard.entity_critical_alerts],
            ApplianceDashboard.pane_needs_attentions: [ApplianceDashboard.entity_servers,
                                                       ApplianceDashboard.entity_infrastructures,
                                                       ApplianceDashboard.entity_jobs],
            ApplianceDashboard.pane_system: None,
            ApplianceDashboard.pane_hardware: None,
            ApplianceDashboard.pane_disk_space: None,
            ApplianceDashboard.pane_sla: None,
            ApplianceDashboard.pane_jobs_in_last_24_hours: [ApplianceDashboard.entity_running,
                                                            ApplianceDashboard.entity_success,
                                                            ApplianceDashboard.entity_failed,
                                                            ApplianceDashboard.entity_critical_events],
        }
        for pane, entities in panes_dict.items():
            if entities:
                for each_value in entities:
                    self.log.info("Accessing details page of Pane:%s, Entity:%s", pane.value,
                                  each_value.value)
                    self.dashboard.access_details_page(pane_name=pane.value,
                                                       entity_name=each_value.value)
                    self.validate_title(pane.value, entity=each_value.value)
            else:
                self.log.info("Accessing details page of Pane:%s", pane.value)
                self.dashboard.access_details_page(pane_name=pane.value)
                self.validate_title(pane.value, entity=entities)

    def validate_title(self, pane, entity):
        """Access pane details page and verify page titles"""
        expected_title = self.get_mapped_title(pane, entity_name=entity)
        page_title = self.dashboard.get_page_title()
        if page_title == expected_title:
            self.log.info("Verified title for [%s] pane, [%s] entity", pane, entity)
            self.browser.driver.back()
            self.dashboard.wait_for_completion()
        else:
            raise CVTestStepFailure("Title did not match for [%s] pane, [%s] entity, [%s] title is"
                                    " Expected, [%s] title is found on page" %
                                    (pane, entity, expected_title, page_title))

    def run(self):
        try:
            self.init_tc()
            self.verify_default_landing_page()
            self.verify_dashboard_page()
            self.verify_pane_titles()
            self.verify_pane_details_page()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
