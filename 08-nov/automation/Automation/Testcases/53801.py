# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify overview dashboard page loading without any errors."""
from cvpysdk.security.user import Users
from cvpysdk.security.role import Roles, Role

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import (ROverviewDashboard, RDashboard)
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Test case to verify overview dashboard page is loading fine, and all the expected panes are
    present"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.admin_console = None
        self.name = "Admin console overview Dashboard page verification"
        self.browser = None
        self.utils = None
        self.dashboard = None
        self.report = None
        self.admin_user = None
        self.admin_user_password = None
        self.non_admin_user = "automated_non_admin_53801"
        self.non_admin_user_password = "hUfHC8hI3L8^"
        self.expected_panes = []
        self.utils = TestCaseUtils(self)
        self.expected_panes = [ROverviewDashboard.pane_environment.value,
                               ROverviewDashboard.pane_needs_attentions.value,
                               ROverviewDashboard.pane_sla.value,
                               ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                               ROverviewDashboard.pane_health.value,
                               ROverviewDashboard.pane_current_capacity_usage.value,
                               ROverviewDashboard.pane_disk_space.value,
                               ROverviewDashboard.pane_top_5_largest_servers.value,
                               ROverviewDashboard.pane_storage_usage.value]

    def read_inputs(self):
        """Read inputs"""
        self.admin_user = self.inputJSONnode['commcell']['commcellUsername']
        self.admin_user_password = self.inputJSONnode['commcell']['commcellPassword']

    def init_tc(self, user_name, password):
        """Initialize browser and redirect to page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=user_name, password=password)
            self.dashboard = RDashboard(self.admin_console)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def create_non_admin_user(self):
        """create new user """
        user = Users(self.commcell)
        role_name = "Report Management"
        roles = Roles(self.commcell)
        # If user exists no need to create user/role.
        if not user.has_user(self.non_admin_user):
            user.add(user_name=self.non_admin_user, password=self.non_admin_user_password,
                     email="AutomatedUser@cvtest.com")
        else:
            return
        if not roles.has_role(role_name):
            roles.add(rolename=role_name, permission_list=["Report Management", "View"])
        role = Role(self.commcell, role_name=role_name)
        role.associate_user(role_name, self.non_admin_user)
        self.log.info("Non admin user [%s] is created", self.non_admin_user)

    @test_step
    def verify_dashboard_page(self):
        """
        Verify dashboard page is not having any errors/notifications
        """
        notification = self.admin_console.get_notification()
        if notification:
            raise CVTestStepFailure("Dashboard page has Notification error [%s]" % notification)
        self.log.info("Dashboard page load is successful")

    @test_step
    def verify_pane_titles(self, user=None):
        """Verify all panes are present in dashboard page"""
        try:
            self.log.info("Verify expected panes are present with [%s] user", user)
            titles = self.dashboard.get_dash_pane_titles()
            if user is self.non_admin_user:
                self.expected_panes = [ROverviewDashboard.pane_environment.value,
                                       ROverviewDashboard.pane_needs_attentions.value,
                                       ROverviewDashboard.pane_sla.value,
                                       ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                                       ROverviewDashboard.pane_last_week_backup_job_summary.value,
                                       ROverviewDashboard.pane_top_5_largest_servers.value]
            if sorted(titles) != sorted(self.expected_panes):
                raise CVTestStepFailure("Expected [%s] panes are not present in dashboard page. "
                                        "Existing panes are [%s]" % (str(self.expected_panes),
                                                                     str(titles)))
            self.log.info("Dashboard pane's titles are verified successfully for [%s] user", user)
        finally:
            Browser.close_silently(self.browser)

    @staticmethod
    def get_mapped_title(pane_name, entity_name=None):
        """Get expected titles of pane details page"""
        _mapped_items = [{"p_name": ROverviewDashboard.pane_environment.value,
                          "entity": ROverviewDashboard.entity_file_servers.value, "title": "File servers"},
                         {"p_name": ROverviewDashboard.pane_environment.value,
                          "entity": ROverviewDashboard.entity_vms.value, "title": "Virtual machines"},
                         {"p_name": ROverviewDashboard.pane_environment.value,
                          "entity": ROverviewDashboard.entity_laptops.value, "title": "Laptops"},
                         {"p_name": ROverviewDashboard.pane_environment.value,
                          "entity": ROverviewDashboard.entity_users.value, "title": "Users"},
                         {"p_name": ROverviewDashboard.pane_needs_attentions.value,
                          "entity": ROverviewDashboard.entity_servers.value,
                          "title": "Needs attention - Servers"},
                         {"p_name": ROverviewDashboard.pane_needs_attentions.value,
                          "entity": ROverviewDashboard.entity_infrastructures.value,
                          "title": "Needs attention - Infrastructures"},
                         {"p_name": ROverviewDashboard.pane_needs_attentions.value,
                          "entity": ROverviewDashboard.entity_jobs.value,
                          "title": "Active jobs"},
                         {"p_name": ROverviewDashboard.pane_sla.value, "entity": None,
                          "title": "SLA"},
                         {"p_name": ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ROverviewDashboard.entity_running.value,
                          "title": "Active jobs"},
                         {"p_name": ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ROverviewDashboard.entity_success.value,
                          "title": "Job history"},
                         {"p_name": ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ROverviewDashboard.entity_cwe.value,
                          "title": "Job history"},
                         {"p_name": ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ROverviewDashboard.entity_failed.value,
                          "title": "Job history"},
                         {"p_name": ROverviewDashboard.pane_jobs_in_last_24_hours.value,
                          "entity": ROverviewDashboard.entity_events.value,
                          "title": "Events"},
                         {"p_name": ROverviewDashboard.pane_health.value, "entity": None,
                          "title": "Health Report"},
                         {"p_name": ROverviewDashboard.pane_current_capacity_usage, "entity": None,
                          "title": "License summary"},
                         {"p_name": ROverviewDashboard.pane_disk_space.value, "entity": None,
                          "title": "Storage Utilization"},
                         {"p_name": ROverviewDashboard.pane_storage_usage.value,
                          "entity": ROverviewDashboard.entity_disk_library.value,
                          "title": "Storage Utilization"},
                         {"p_name": ROverviewDashboard.pane_storage_usage.value,
                          "entity": ROverviewDashboard.entity_space_savings.value,
                          "title": "Storage Utilization"}
                         ]
        for pane in _mapped_items:
            if pane["p_name"] == pane_name and pane["entity"] == entity_name:
                return pane["title"]
        raise CVTestStepFailure("[%s]Pane is not mapped" % pane_name)

    @test_step
    def verify_pane_details_page(self):
        """Access details page of pane and verify the page titles are correct"""
        panes_dict = {
            ROverviewDashboard.pane_environment: [ROverviewDashboard.entity_file_servers,
                                                  ROverviewDashboard.entity_vms,
                                                  ROverviewDashboard.entity_laptops,
                                                  ROverviewDashboard.entity_users],
            ROverviewDashboard.pane_needs_attentions: [ROverviewDashboard.entity_servers,
                                                       ROverviewDashboard.entity_infrastructures,
                                                       ROverviewDashboard.entity_jobs],
            ROverviewDashboard.pane_sla: None,
            ROverviewDashboard.pane_jobs_in_last_24_hours: [ROverviewDashboard.entity_running,
                                                            ROverviewDashboard.entity_success,
                                                            ROverviewDashboard.entity_cwe,
                                                            ROverviewDashboard.entity_failed,
                                                            ROverviewDashboard.entity_events],
            ROverviewDashboard.pane_health: None,
            ROverviewDashboard.pane_current_capacity_usage: None,
            ROverviewDashboard.pane_disk_space: None,
            ROverviewDashboard.pane_storage_usage: [ROverviewDashboard.entity_disk_library,
                                                    ROverviewDashboard.entity_space_savings],

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
                self.admin_console.navigator.navigate_to_dashboard()

    def validate_title(self, pane, entity):
        """Access pane details page and verify page titles"""
        expected_title = self.get_mapped_title(pane, entity_name=entity)
        if pane == "Jobs in the last 24 hours" or (pane == "Needs Attention" and entity == "Jobs"):
            # Fetch page title from get_page_title()
            page_title = self.dashboard.get_page_title()
        elif pane == "Health":
            # Fetch page title from next page's title
            self.browser.driver.switch_to.window(
                self.browser.driver.window_handles[-1])
            self.admin_console.wait_for_completion()
            page_title = self.browser.driver.title
        else:
            # Fetch page_title from current page's title
            page_title = self.browser.driver.title

        if expected_title in page_title:
            self.log.info("Verified title for [%s] pane, [%s] entity", pane, entity)
            if pane == "Health":
                self.browser.driver.close()
                self.browser.driver.switch_to.window(
                    self.browser.driver.window_handles[-1])
                return
            self.browser.driver.back()
            self.admin_console.wait_for_completion()
        else:
            raise CVTestStepFailure("Title did not match for [%s] pane, [%s] entity, [%s] title is"
                                    " Expected, [%s] title is found on page" %
                                    (pane, entity, expected_title, page_title))

    @test_step
    def verify_pane_titles_for_non_admin(self):
        """Verify expected panes are present for non admin user"""
        self.create_non_admin_user()
        self.init_tc(user_name=self.non_admin_user, password=self.non_admin_user_password)
        self.verify_pane_titles(user=self.non_admin_user)

    def run(self):
        try:
            self.read_inputs()
            self.init_tc(user_name=self.admin_user, password=self.admin_user_password)
            self.verify_dashboard_page()
            self.verify_pane_details_page()
            self.verify_pane_titles(user=self.admin_user)
            self.verify_pane_titles_for_non_admin()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
