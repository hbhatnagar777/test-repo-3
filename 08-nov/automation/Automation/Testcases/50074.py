# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.Common.page_object import TestStep

from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.cvbrowser import (
    BrowserFactory, Browser
)
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Reports.Custom.report_templates import DefaultReport
from Web.WebConsole.Reports.Custom import (
    viewer, dashboard
)


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports Custom Dashboard"
        self.dash_name = "DASHBOARD " + self.name
        self.util = None
        self.browser = None
        self.webconsole: WebConsole = None
        self.dashboard: dashboard.Dashboard = None
        self.table = viewer.DataTable("Automation Table")
        self.table_data = None

    def init_tc(self):
        try:
            self.util = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                           password=self.inputJSONnode['commcell']['commcellPassword'])
            self.browser = BrowserFactory().create_browser_object().open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.goto_reports()
            DefaultReport(self.util).build_default_report(
                overwrite=False,
                sql="""SELECT @@servername [Server], GETDATE() [Time]""",
                chart_cols={"X": "Server", "Y": "Time"}
            )
            Navigator(self.webconsole).goto_custom_dashboard()
            dash_mgr = dashboard.DashboardManager(self.webconsole)
            dash_mgr.delete_silently(self.dash_name)
        except Exception as err:
            raise CVTestCaseInitFailure(err) from err

    @test_step
    def create_dashboard(self):
        """Create a Custom Dashboard"""
        dash_msg = dashboard.DashboardManager(self.webconsole)
        self.dashboard = dash_msg.add_dashboard(
            self.dash_name,
            "Automation Dashboard Description"
        )
        dash_msg.open(self.dash_name)

    @test_step
    def add_url(self):
        """Add a URL to the dashboard"""
        self.dashboard.add_url(
            "URLComponent",
            self.webconsole.base_url + f"reportsplus/reportViewer.jsp?reportId={self.name}"
        )
        try:
            url = dashboard.URLAdaptor(
                "URLComponent",
                viewer.CustomReportViewer(self.webconsole)
            )
            self.dashboard.focus_component(url)
            titles = url.get_all_component_titles()
            if titles != ["Automation Table", "Automation Chart"]:
                raise CVTestStepFailure(
                    "URL component not showing the components"
                )
        finally:
            self.dashboard.un_focus_all_components()

    @test_step
    def add_chart(self):
        """Add a chart component from report to dashboard	"""
        self.dashboard.add_report(self.name, "Automation Chart")
        try:
            chart = viewer.VerticalBar("Automation Chart")
            self.dashboard.focus_component(chart)
            if not chart.get_chart_details():
                raise CVTestStepFailure(
                    "Unable to add chart to dashboard"
                )
        finally:
            self.dashboard.un_focus_all_components()

    @test_step
    def add_table(self):
        """Add a table component from report to dashboard	"""
        self.dashboard.add_report(self.name, "Automation Table")
        try:
            self.dashboard.focus_component(self.table)
            self.table_data = self.table.get_table_data()
            if not self.table_data:
                raise CVTestStepFailure(
                    "No data found in added component"
                )
        finally:
            self.dashboard.un_focus_all_components()

    @test_step
    def refresh_dashboard(self):
        """Refresh the dashboard"""
        try:
            self.dashboard.refresh()
            self.dashboard.focus_component(self.table)
            new_data = self.table.get_table_data()
            if self.table_data == new_data:
                raise CVTestStepFailure(
                    "Latest data is not seen after refresh"
                )
        finally:
            self.dashboard.un_focus_all_components()

    @test_step
    def delete_dashboard(self):
        """Delete a Custom Dashboard"""
        Navigator(self.webconsole).goto_custom_dashboard()
        self.webconsole.clear_all_notifications()
        dashboard.DashboardManager(self.webconsole).delete(self.dash_name)

    def run(self):
        try:
            self.init_tc()
            self.create_dashboard()
            self.add_table()
            self.add_chart()
            self.add_url()
            self.refresh_dashboard()
            self.delete_dashboard()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
