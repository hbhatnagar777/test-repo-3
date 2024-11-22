# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to Customize Default Dashboards on Command Center

TestCase:
    __init__()      --  Initializes the TestCase class

    run()           --  Contains the core testcase logic and it is the one executed

    Input Example:
    "testCases":
            {
                "58969":
                 {
                     "non_admin_user": "TC_58969_non_admin_user",
                     "password": "",
                     "tile_to_be_removed": "Environment"
                 }
            }
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import RDashboard
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Test case to Customize Default Dashboards on Command Center"""
    test_step = TestStep()

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Customize Default Dashboards on Command Center"
        self.browser = None
        self.utils = None
        self.dashboard = None
        self.clone_dashboard_name = None
        self.admin_console = None
        self.non_admin_user = None
        self.password = None
        self.navigator = None
        self.tile_to_be_removed = None
        self.commcell_password = None

    def init_tc(self):
        """Initialize browser and redirect to page"""
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.utils = TestCaseUtils(self)
            self.non_admin_user = self.tcinputs['non_admin_user']
            self.password = self.tcinputs['password']
            self.tile_to_be_removed = self.tcinputs['tile_to_be_removed']
            self.clone_dashboard_name = 'Overview Dashboard Copy ' + self.utils.testcase.id
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=self.commcell_password)
            self.create_user(self.non_admin_user, 'tc58969@cmvt.com')
            self.navigator = self.admin_console.navigator
            self.dashboard = RDashboard(self.admin_console)
            dashboards = self.dashboard.get_all_dashboards()
            # delete cloned dashboard if already exists
            if self.clone_dashboard_name in dashboards:
                self.dashboard.navigate_to_given_dashboard(self.clone_dashboard_name)
                self.dashboard.delete_dashboard()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def create_user(self, username, email):
        """ Create a user """
        # if user exists no need to create user/role.
        if not self.commcell.users.has_user(username):
            self.log.info("Creating user [%s]",  username)
            self.commcell.users.add(
                user_name=username,
                email=email,
                full_name=username,
                password=self.password
            )
        else:
            self.log.info("User [%s] already exists", username)
            return

    @test_step
    def edit_overview_dashboard(self):
        """Edit overview dashboard"""
        self.dashboard.navigate_to_given_dashboard("Overview")
        # revert dashboard if not in original state
        if 'Revert' in self.dashboard.get_dashboard_actions():
            self.dashboard.revert_dashboard()
        self.dashboard.edit_dashboard()
        self.dashboard.remove_tile(self.tile_to_be_removed)
        self.dashboard.save()
        titles = self.dashboard.get_dash_pane_titles()
        if self.tile_to_be_removed in titles:
            raise CVTestStepFailure("Tile not removed after editing the dashboard")

    @test_step
    def verify_revert(self):
        """Verify revert"""
        self.dashboard.revert_dashboard()
        titles = self.dashboard.get_dash_pane_titles()
        if self.tile_to_be_removed not in titles:
            raise CVTestStepFailure("Dashboard was not reverted to original state successfully")

    @test_step
    def verify_delete_for_default_dashboard(self):
        """Verify delete for default dashboard"""
        dashboard_actions = self.dashboard.get_dashboard_actions()
        if 'Delete' in dashboard_actions:
            raise CVTestStepFailure("Default dashboard should not have option to delete")

    @test_step
    def verify_clone(self):
        """Verify clone"""
        self.dashboard.navigate_to_given_dashboard("Overview")
        self.dashboard.clone_dashboard(self.clone_dashboard_name)
        dashboards = self.dashboard.get_all_dashboards()
        if self.clone_dashboard_name not in dashboards:
            raise CVTestStepFailure("Dashboard was not cloned successfully")

    @test_step
    def verify_security(self):
        """Verify security"""
        self.dashboard.dashboard_security(self.non_admin_user)
        self.admin_console.logout()
        self.admin_console.login(self.non_admin_user, self.password)
        dashboards = self.dashboard.get_all_dashboards()
        if self.clone_dashboard_name not in dashboards:
            raise CVTestStepFailure("Cloned dashboard was not shared successfully with the user")
        self.admin_console.logout()

    @test_step
    def verify_delete(self):
        """Verify delete"""
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.dashboard.navigate_to_given_dashboard(self.clone_dashboard_name)
        self.dashboard.delete_dashboard()
        dashboards = self.dashboard.get_all_dashboards()
        if self.clone_dashboard_name in dashboards:
            raise CVTestStepFailure("Dashboard was not deleted successfully")

    def run(self):
        try:
            self.init_tc()
            self.edit_overview_dashboard()
            self.verify_revert()
            self.verify_delete_for_default_dashboard()
            self.verify_clone()
            self.verify_security()
            self.verify_delete()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            # revert dashboard if not in original state
            self.dashboard.navigate_to_given_dashboard("Overview")
            if 'Revert' in self.dashboard.get_dashboard_actions():
                self.dashboard.revert_dashboard()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
