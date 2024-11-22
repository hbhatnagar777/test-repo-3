# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.Custom import inputs as wc_inputs
from Web.AdminConsole.Reports.Custom import inputs as ac_inputs
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (Input) - String TextBox"
        self.manage_reports = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.builder: builder.ReportBuilder = None
        self.textbox: wc_inputs.TextBoxController = None
        self.input_variable = None

        # TC constant inputs
        self.expected_data = {
            "No Column Name1": [
                """||--~!@#$%^&*()_+{}:"\:{}""",
            ]
        }
        self.input_display_name = "Test Input Display Name"
        self.utils = TestCaseUtils(self)
        self.dataset = None

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.delete_report(self.name)
            self.manage_reports.add_report()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def validate_data(self, received, expected, msg):
        if expected != received:
            self.log.error(f"Expected : {expected}")
            self.log.error(f"Received : {received}")
            raise CVTestStepFailure(msg)

    @test_step
    def create_html_input(self):
        """Create report input UI component"""
        self.builder = builder.ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        self.input_variable = wc_inputs.String("TestInputVariableName")
        self.builder.add_input(self.input_variable)
        self.textbox = wc_inputs.TextBoxController(self.input_display_name)
        self.input_variable.add_html_controller(self.textbox)
        self.input_variable.save()

    @test_step
    def add_parameter(self):
        """Add HTML input and parameter to Dataset and preview"""
        self.dataset = builder.DatabaseDataset()
        self.builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("Test Dataset")
        self.dataset.set_sql_query("SELECT @sql_variable")
        self.dataset.add_parameter("sql_variable", self.input_variable)
        preview_data = self.dataset.get_preview_data()
        self.validate_data(
            preview_data,
            {'No Column Name1': ['', ]},
            "Unexpected data received during dataset preview"
        )
        self.dataset.save()

    @test_step
    def associate_input_to_dataset(self):
        """Associate dataset with input to Table and validate data"""
        table = builder.DataTable("Test Table")
        self.builder.add_component(table, self.dataset)
        table.add_column_from_dataset("No Column Name1")
        self.textbox.set_textbox_controller("Text Input Data" + '\t')
        self.textbox.apply()
        self.builder.save_and_deploy()
        table_data = table.get_table_data()
        self.validate_data(
            table_data,
            {"No Column Name1": ["Text Input Data", ]},
            "Unexpected data received after filtering using inputs"
        )
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def set_textbox_value(self):
        """Set textbox input, and verify data on report viewer"""
        html_textbox = ac_inputs.TextBoxController(self.input_display_name)
        table = viewer.DataTable("Test Table")
        viewer_ = viewer.CustomReportViewer(self.admin_console)
        viewer_.associate_input(html_textbox)
        viewer_.associate_component(table, "Test Table")
        html_textbox.set_textbox_controller(self.expected_data["No Column Name1"][0] + '\t')
        html_textbox.apply()
        data = table.get_table_data()
        self.validate_data(
            data,
            {'No Column Name1': ['||--~!@#$%^&*()_+{}:"\\:{}']},
            "Unexpected data received on report viewer"
        )

    @test_step
    def bookmarked_report_url(self):
        """Bookmark the report URL with input and validate data"""
        self.browser.driver.refresh()
        table = viewer.DataTable("Test Table")
        viewer_ = viewer.CustomReportViewer(self.admin_console)
        viewer_.associate_component(table, "Test Table")
        data = table.get_table_data()
        self.validate_data(
            data,
            self.expected_data,
            "Unexpected data received after bookmarking inputs"
        )

    @test_step
    def submit_input_value(self):
        """Submit input with HTML characters

        All the HTML characters will have
        """
        table = viewer.DataTable("Test Table")
        textbox = ac_inputs.TextBoxController(self.input_display_name)
        viewer_ = viewer.CustomReportViewer(self.admin_console)
        viewer_.associate_component(table, "Test Table")
        viewer_.associate_input(textbox)
        textbox.set_textbox_controller("<h1>Inside</h1>Outside" + '\t')
        textbox.apply()
        data = table.get_table_data()
        self.validate_data(
            data,
            {"No Column Name1": ["Outside", ]},
            "Unexpected data received while testing HTML sensitive characters"
        )

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_html_input()
            self.add_parameter()
            self.associate_input_to_dataset()
            self.set_textbox_value()
            self.bookmarked_report_url()
            self.submit_input_value()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
