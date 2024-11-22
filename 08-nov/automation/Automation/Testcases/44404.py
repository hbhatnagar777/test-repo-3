# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep

from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.WebConsole.Store.storeapp import StoreApp

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin console Reports: Display packages available for update"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.manage_report = None
        self.navigator = None
        self.admin_console = None
        self.reports = set()

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def get_reports_from_dash(self):
        """Get all the reports available for update from Reports Dashboard"""
        self.reports = set(self.manage_report.get_reports_available_for_update())
        self.manage_report.goto_store_for_update()

    @test_step
    def get_reports_from_store(self):
        """Get all the reports available for update from Store Homepage"""
        wc = WebConsoleAdapter(self.admin_console, self.browser)
        store = StoreApp(wc)
        dash_reports = set(map(lambda s: s.lower(), self.reports))
        home_reports = set(map(
            lambda s: s.lower(), store.get_all_packages()
        ))
        if sorted(home_reports) != sorted(dash_reports):
            self.log.error(f"Dash: {dash_reports}")
            self.log.error(f"Home: {home_reports}")
            raise CVTestStepFailure(
                "Reports list on dashboard does not match store homepage"
            )
        statuses = store.get_all_package_statuses()
        if len(set(statuses)) != 1 or statuses[0] != "Update":
            raise CVTestStepFailure("Unexpected report status received")

    def run(self):
        try:
            self.init_tc()
            self.get_reports_from_dash()
            self.get_reports_from_store()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
