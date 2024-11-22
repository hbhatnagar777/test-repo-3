# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports: Post query filter work on pivot"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import CVTestCaseInitFailure

from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.builder import (
    Datasets,
    ReportBuilder,
    PivotTable
)
from Web.AdminConsole.Reports.Custom.viewer import CustomReportViewer
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.adminconsole import AdminConsole

class TestCase(CVTestCase):

    test_step = TestStep()
    SQL = """
        select 1 as [Row], 2 [Column]
        union
        select 2 as [Row], 3 [Column]
        union
        select 2 as [Row], 2 [Column]
        union
        select 30 as [Row], 40 [Column]
        """
    EXPECTED_DATA = {'Row': ['1', '2'], '2': ['1', '1'], '3': ['', '1']}
    POST_QUERY_FILTER = "select * from $this$ where [Row] != 30"

    def __init__(self):
        super(TestCase, self).__init__()
        self.navigator = None
        self.admin_console = None
        self.name = "Custom Reports: Post query filter work on pivot"
        self.utils = CustomReportUtils(self)
        self.webconsole = None
        self.browser = None
        self.builder = None
        self.pivot_table = None
        self.manage_report = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.manage_report = ManageReport(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.utils.webconsole = self.webconsole
            self.navigator.navigate_to_reports()
            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)
            self.manage_report.add_report()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_report(self):
        """Creates report with post query filter"""
        self.builder = ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        dataset = Datasets.DatabaseDataset()
        self.builder.add_dataset(dataset)
        dataset.set_dataset_name("Automation Dataset")
        dataset.set_sql_query(TestCase.SQL)
        dataset.set_post_query_filter(TestCase.POST_QUERY_FILTER)
        dataset.save()

        self.pivot_table = PivotTable("Automation Table 49956")
        self.builder.add_component(self.pivot_table, dataset)
        self.pivot_table.set_pivot_row("Row")
        self.pivot_table.set_pivot_column("Column")

    @test_step
    def validate_report(self):
        """Validates Pivot Table content"""
        actual_data = self.pivot_table.get_table_data()
        SQLQueries.validate_equality(TestCase.EXPECTED_DATA, actual_data)

        self.builder.save(deploy=True)
        self.builder.open_report()
        report_viewer = CustomReportViewer(self.admin_console)
        self.pivot_table = viewer.PivotTable("Automation Table 49956")
        report_viewer.associate_component(self.pivot_table)
        actual_data = self.pivot_table.get_table_data()
        SQLQueries.validate_equality(TestCase.EXPECTED_DATA, actual_data)

    def run(self):
        try:
            self.init_tc()
            self.create_report()
            self.validate_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
