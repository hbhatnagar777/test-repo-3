# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""App Creation and Sharing"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.App.util import AppUtils
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Apps.apps import (
    AppsPage, App, AppBuilder
)
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "App Creation"
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.utils: AppUtils = None
        self.apps_page: AppsPage = None
        self.automation_username = "tc52900"
        self.automation_password = "Tc@52900"

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = AppUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.webconsole.goto_apps()
            self.apps_page = AppsPage(self.webconsole)
            if self.utils.is_app_installed(self.name):
                app = App(self.name, self.apps_page)
                app.delete()
            self.utils.verify_if_alerts_exists(self.utils.config.Alerts)
            self.utils.verify_if_workflows_exists(self.utils.config.Workflows)
            self.utils.verify_if_reports_exists(self.utils.config.Reports)
            self.create_user()
        except Exception as ex:
            raise CVTestCaseInitFailure(ex) from ex

    def create_user(self):
        """Creates User"""
        if self.commcell.users.has_user(self.automation_username):
            self.log.info("Deleting existing user")
            self.commcell.users.delete(self.automation_username, "admin")

        self.commcell.users.add(
            self.automation_username,
            self.automation_username,
            "reports@testing.com",
            None,
            self.automation_password
        )

    @TestStep()
    def create_app(self):
        """Create App"""
        self.apps_page.goto_new_app()
        builder = AppBuilder(self.apps_page)
        builder.add_components(
            workflows=self.utils.config.Workflows,
            reports=self.utils.config.Reports,
            alerts=self.utils.config.Alerts
        )
        builder.set_name(self.name)
        builder.set_primary_component(self.utils.config.Reports[0])
        builder.save()
        self.apps_page.lookup_app(self.name)
        self.utils.verify_if_app_is_installed(self.name)

    @TestStep()
    def share_app(self):
        """Shares the app to newly created user"""
        app = App(self.name, self.apps_page)
        app.share(self.automation_username)

        with BrowserFactory().create_browser_object() as browser,\
                WebConsole(browser, self.commcell.webconsole_hostname,
                           self.automation_username, self.automation_password) as webconsole:
            webconsole.goto_apps()
            apps_page = AppsPage(webconsole)
            apps_page.lookup_app(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_app()
            self.share_app()
        except Exception as ex:
            self.utils.handle_testcase_exception(ex)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
