from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom.builder import Datasets

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Components.panel import RDropDown

from Web.Common.page_object import handle_testcase_exception, CVTestStepFailure

from collections import Counter
import re


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.builder = None
        self.manage_reports = None
        self.report = None
        self.name = "Custom Report: Validate Table to Chart Functionality"
        self.utils = None
        self.webconsole: WebConsole = None
        self.admin_console = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.navigator = None
        self.dataset = None
        self.data_table = None
        self.table = None
        self.report_viewer = None
        self.api = None
        self.expected_data = None
        self.report_name = 'TC 59036-Chart to table'
        self.q1 = f"""
                select top 5 status,jobid from jmjobstats
                """
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.rdropdown = RDropDown(self.admin_console)
            self.report = Report(self.admin_console)
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.delete_report(self.name)
            self.manage_reports.add_report()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_dataset(self):
        """Create Database dataset"""
        self.builder = builder.ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("dbdataset")
        self.dataset.set_sql_query(self.q1)
        data = self.dataset.get_preview_data()
        self.expected_data = dict(Counter(list(data.values())[0]))
        self.dataset.save()

    @test_step
    def add_datasource_to_table(self):
        """Add the datasource to any table"""
        self.data_table = builder.DataTable("TestTable")
        self.rpt_builder.add_component(self.data_table, self.dataset)
        self.data_table.add_column_from_dataset()
        self.rpt_builder.save_and_deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def table_to_chart(self):
        """Converts Table to Chart"""
        self.table = viewer.DataTable("TestTable")
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.report_viewer.associate_component(self.table)
        self.table.charts()

    @test_step
    def verify_data(self):
        """Verify that the table data is correct"""
        self.rdropdown.select_drop_down_values(drop_down_id='dimension1Columns', values=['status'])
        chart = viewer.PieChart("TestTable")
        self.report_viewer.associate_component(chart)
        _, received_data = chart.get_chart_legend()
        pat = []
        for key in self.expected_data.keys():
            pat.append(str(key) + ' : ' + str(self.expected_data[key]) + ' (100 %)')

        if pat != received_data:
            raise CVTestStepFailure(f"Expected legend {pat} "
                                    f"Received legends {received_data}")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_dataset()
            self.add_datasource_to_table()
            self.table_to_chart()
            self.verify_data()
            self.delete_report()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
