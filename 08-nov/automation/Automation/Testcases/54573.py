# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics : Dashboard support incident validation """
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Dashboard : Verify support incident"
        self.commcell_name = None
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.tcinputs = {"commcellname": None}
        self.utils = TestCaseUtils(self)
        self.report = None
        self.viewer = None
        self.table = None
        self.dashboard = None
        self.active_count = None
        self.closed_count = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"]
                                  )
            self.webconsole.goto_reports()
            self.dashboard = Dashboard(self.webconsole)
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_commcell_dashboard(self.tcinputs["commcellname"])
            self.active_count = int(self.dashboard.get_active_support_incident())
            self.closed_count = int(self.dashboard.get_closed_support_incident())
            self.dashboard.view_detailed_report('Support Incidents')
            self.viewer = viewer.CustomReportViewer(self.webconsole)
            self.table = viewer.DataTable("All Support Incidents")
            self.viewer.associate_component(self.table)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_active_incident(self):
        """verify the active incident count is matching with details """
        self.table.set_filter('Incident State', 'Active')
        active_incdent = self.table.get_column_data('Incident State')
        detail_count = len(active_incdent)
        if self.active_count != detail_count:
            raise CVTestStepFailure("Expected active count is [%s] but received count [%s]"
                                    %(self.active_count, detail_count))

    @test_step
    def verify_closed_incident(self):
        """verify the closed incident count is matching with details"""
        self.table.set_filter('Incident State', 'Resolved')
        resolved_incdent = self.table.get_column_data('Incident State')
        detail_count = len(resolved_incdent)
        if self.closed_count != detail_count:
            raise CVTestStepFailure("Expected resolved count is [%s] but received count [%s]"
                                    % (self.closed_count, detail_count))

    def run(self):
        try:
            self.init_tc()
            self.verify_active_incident()
            self.verify_closed_incident()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
