# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.Custom import inputs as wc_inputs
from Web.AdminConsole.Reports.Custom import inputs as ac_inputs
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    expected_columns = ['idleTime', 'loggedInMode', 'userGUID', 'userId', 'userName', 'companyId',
                        'companyName', 'multiCommcellId']

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (DataSet) - HTTP GET"
        self.webconsole = None
        self.navigator = None
        self.builder: builder.ReportBuilder = None
        self.browser = None
        self.manage_reports = None
        self.admin_console = None
        self.input_textbox = None
        self.integer_input_variable = None
        self.utils = TestCaseUtils(self)
        self.inbuilt_user_ids = None
        self.dataset = None

    def init_tc(self):
        try:
            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)
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
            self.builder = builder.ReportBuilder(self.webconsole)
            self.integer_input_variable = wc_inputs.Integer("HTTPTestingString")
            self.builder.set_report_name(self.name)
            self.builder.add_input(self.integer_input_variable)
            self.integer_input_variable.set_default_value("1")
            self.input_textbox = wc_inputs.TextBoxController("HTTPTestingTextBox")
            self.integer_input_variable.add_html_controller(self.input_textbox)
            self.integer_input_variable.save()
            user_ids = self.utils.cre_api.execute_sql(
                """
                SELECT id
                FROM UmUsers
                """,
                as_json=True
            )
            self.inbuilt_user_ids = set(map(str, user_ids["id"]))
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_json_dataset(self):
        """Create Dataset with LocalCommcell DS and submit a GET command with JSON response type"""
        self.dataset = builder.Datasets.HTTPDataset()
        self.builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("Test HTTP Dataset")
        self.dataset.set_get("SearchSvc/CVWebService.svc/User", json_accept_type=True)
        data = self.dataset.get_preview_data()
        row_expression = self.dataset.get_row_expression()

        # validate columns
        columns = list(data.keys())
        columns.sort()
        TestCase.expected_columns.sort()
        if columns != TestCase.expected_columns:
            raise CVTestStepFailure("Unexpected columns; [%s]" % str(columns))

        # validate data
        if set(data.get("userId", (-9999,))) - self.inbuilt_user_ids:
            raise CVTestStepFailure("Unexpected preview data [%s]" % str(data))

        # validate row expression
        if row_expression != "users":
            raise CVTestStepFailure(
                "Unexpected JSONPath expression [%s], expected [users]" % row_expression)

    @test_step
    def create_xml_dataset(self):
        """Repeat request used in step 1 with XML accept type"""
        self.dataset.set_get("SearchSvc/CVWebService.svc/User", json_accept_type=False)
        self.dataset.set_row_expression("")
        data = self.dataset.get_preview_data()

        # validate columns
        columns = list(data.keys())
        columns.sort()
        if columns != TestCase.expected_columns:
            raise CVTestStepFailure("Unexpected columns [%s], expected [%s]" % (
                str(columns), str(TestCase.expected_columns)))

        # validate data
        if set(data.get("userId", (-9999,))) - self.inbuilt_user_ids:
            self.log.error("Preview data received [%s]" % str(data))
            raise CVTestStepFailure("Unexpected preview data")

        # validate row expression
        row_expression = self.dataset.get_row_expression()
        if row_expression != "/App_GetUserPropertiesResponse/users":
            raise CVTestStepFailure("Unexpected row expression [%s]" % row_expression)

    @test_step
    def preview_generated_xpath(self):
        """Preview with manually entered XPath row expression"""
        self.dataset.set_get("SearchSvc/CVWebService.svc/User", json_accept_type=False)
        self.dataset.set_row_expression("/App_GetUserPropertiesResponse/users/userEntity")
        data = self.dataset.get_preview_data()

        # validate row expression
        row_expression = self.dataset.get_row_expression()
        if row_expression != "/App_GetUserPropertiesResponse/users/userEntity":
            raise CVTestStepFailure("Unexpected row expression [%s], expected [%s]" % (
                row_expression, "/App_GetUserPropertiesResponse/users/userEntity "))

        # validate data
        if not all(str(uid) in self.inbuilt_user_ids for uid in data.get("userId", [])):
            raise CVTestStepFailure("Unexpected preview data [%s] received" % str(data))

    @test_step
    def add_input(self):
        """Add input to the REST dataset"""
        parameter_name = "user_val"
        self.dataset.set_get(
            "SearchSvc/CVWebService.svc/User/@%s" % parameter_name, json_accept_type=False)
        self.dataset.set_row_expression("/App_GetUserPropertiesResponse/users/userEntity")
        self.dataset.add_parameter(parameter_name, self.integer_input_variable)
        data = self.dataset.get_preview_data()
        if "1" not in data.get("userId", []):
            raise CVTestStepFailure("Unexpected preview data [%s] received" % str(data))
        self.dataset.save()

    @test_step
    def add_dataset_to_table(self):
        """Associate the dataset to table and verify data"""
        table = builder.DataTable("HTTP Dataset Table")
        self.builder.add_component(table, self.dataset)
        table.add_column_from_dataset("userId")
        data = table.get_table_data()
        if set(data.get("userId", (-9999,))) - self.inbuilt_user_ids:
            raise CVTestStepFailure("Unexpected data [%s] in table" % str(data))
        self.builder.save_and_deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def save_report(self):
        """Save the report and try setting various input values on viewer"""
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        textbox = ac_inputs.TextBoxController("HTTPTestingTextBox")
        report_viewer.associate_input(textbox)

        table = viewer.DataTable("HTTP Dataset Table")
        report_viewer.associate_component(table)

        # test valid user
        textbox.set_textbox_controller("1")
        textbox.apply()
        data = table.get_table_data()
        if "1" not in data.get("userId", []):
            raise CVTestStepFailure("Unexpected data [%s] in table" % str(data))

        # test invalid user
        textbox.set_textbox_controller("999999")
        textbox.apply()
        if not data.get("userId", []):
            raise CVTestStepFailure(
                "Input not applied, received data [%s]" % str(data)
            )
        sleep(3)

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_json_dataset()
            self.create_xml_dataset()
            self.preview_generated_xpath()
            self.add_input()
            self.add_dataset_to_table()
            self.save_report()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
