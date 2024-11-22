from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.Common.page_object import CVTestStepFailure
from Web.WebConsole.Reports.Custom.inputs import DateRange
from Web.AdminConsole.Reports.Custom.inputs import DateRangeController
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Input Daterange Validation"
        self.webconsole: WebConsole = None
        self.admin_console = None
        self.manage_reports = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.navigator = None
        self.dataset = None
        self.data_table = None
        self.table = None
        self.viewer = None
        self.expected_data = None
        self.input = None
        self.util = TestCaseUtils(self)
        self.report_name = 'TC 59039-Daterange'
        self.q1 = f"""
                select @daterange_to as 'to', @daterange_from as 'from'
                """

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.delete_report(self.report_name)
            self.manage_reports.add_report()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.report_name)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def add_daterange_input(self):
        """Add Daterange Input"""
        self.input = DateRange("daterange")
        self.rpt_builder.add_input(self.input)
        self.input.set_display_name("daterange")
        self.input.enable_options(last_n=True, days=True, weeks=True, months=True, years=True)
        self.input.save()

    @test_step
    def create_dataset(self):
        """Create Database dataset"""
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("dbdataset")
        self.dataset.set_sql_query(self.q1)
        self.dataset.add_parameter("daterange", self.input)
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
        self.manage_reports.access_report(self.report_name)

    @test_step
    def validate_the_daterange_input(self):
        """Validates the Daternage type input controller
        1) Apply input via input conroller
        2) get table data
        3) estimate dates
        4) compare
        """
        self.table = viewer.DataTable("TestTable")
        self.viewer.associate_component(self.table)
        input_ctrl = DateRangeController("daterange")
        self.viewer.associate_input(input_ctrl)
        daterange_options = input_ctrl.get_available_options()

        for option in daterange_options:
            input_ctrl.set_relative_daterange(option)
            num = re.search(r'\d', option).group()

            if re.search(r'days', option):
                days = int(num)
                years, months, weeks, = 0, 0, 0
            elif re.search(r'weeks', option):
                years, months, days = 0, 0, 0
                weeks = int(num)
            elif re.search(r'months', option):
                months = int(num)
                years, weeks, days = 0, 0, 0
            elif re.search(r'Year', option):
                years = int(num)
                weeks, months, days = 0, 0, 0
            else:
                raise CVTestStepFailure("Only days, weeks, months and year are supported")

            today = datetime.today()
            expected_to = today.strftime("%b %#d, %Y")
            expected_from = (today - relativedelta(years=years, months=months, weeks=weeks, days=days)).strftime("%b %#d, %Y")

            table_data = self.table.get_table_data()
            received_to = re.search(r'\w+ \d+, \d+', table_data['to'][0]).group()
            received_from = re.search(r'\w+ \d+, \d+', table_data['from'][0]).group()

            if received_to != expected_to:
                raise CVTestStepFailure(f"Expected to date [{expected_to}] received to date [{received_to}]")
            if received_from != expected_from:
                raise CVTestStepFailure(f"Expected from date [{expected_from}] received from [{received_from}]")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.report_name)

    def run(self):
        try:
            self.init_tc()
            self.add_daterange_input()
            self.create_dataset()
            self.add_datasource_to_table()
            self.validate_the_daterange_input()
            self.delete_report()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
