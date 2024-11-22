# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Report: Validate HTTP POST datasets"""
from base64 import b64encode

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.inputs import String
from Web.WebConsole.Reports.Custom.inputs import TextBoxController as WC_TxtBox
from Web.AdminConsole.Reports.Custom.inputs import TextBoxController as AC_TxtBox
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    HTTP_CONTENT = """<DM2ContentIndexing_CheckCredentialReq mode="Webconsole" username="%s" password="%s" />"""
    API = "SearchSvc/CVWebService.svc/Login"
    POST_QUERY_FILTER = "SELECT * FROM $this$ UNION ALL SELECT * FROM $this$"
    CONSTANTS = config.get_config()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Validate HTTP POST datasets"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.report_builder = None
        self.dataset = None

    def init_tc(self):
        """ Initial configuration for the test case. """
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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_http_dataset_with_post_query(self):
        """Creates a HTTP dataset via REST"""
        self.report_builder = builder.ReportBuilder(self.webconsole)
        self.report_builder.set_report_name(self.name)
        self.dataset = builder.HTTPDataset()
        self.report_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("Automation Dataset")
        self.dataset.set_post(
            TestCase.API,
            TestCase.HTTP_CONTENT %
            (TestCase.CONSTANTS.ADMIN_USERNAME, b64encode(TestCase.CONSTANTS.ADMIN_PASSWORD.encode()).decode()),
            json_content_type=False,
            json_accept_type=False
        )
        preview_data = self.dataset.get_preview_data()
        row_expression = self.dataset.get_row_expression()
        if not row_expression:
            raise CVTestStepFailure("Row Expression is empty")
        if not preview_data:
            raise CVTestStepFailure("preview_data is empty")
        self.dataset.save()

    @test_step
    def set_username_and_password_via_input(self):
        """Sets username and password from input"""
        username = String("Username")
        textbox_1 = WC_TxtBox("Username")
        self.report_builder.add_input(username)
        username.add_html_controller(textbox_1)
        username.set_required()
        username.save()

        password = String("Password")
        textbox_2 = WC_TxtBox("Password")
        self.report_builder.add_input(password)
        username.add_html_controller(textbox_2)
        username.set_required()
        password.save()

        table = builder.DataTable("Automation Table")
        self.report_builder.add_component(table, self.dataset)
        table.add_column_from_dataset()
        self.report_builder.edit_dataset(self.dataset)
        self.dataset.set_post(
            TestCase.API,
            TestCase.HTTP_CONTENT %
            ("@username", "@password"),
            json_content_type=False,
            json_accept_type=False
        )
        self.dataset.set_post_query_filter(TestCase.POST_QUERY_FILTER)
        self.dataset.add_parameter("username", username)
        self.dataset.add_parameter("password", password)
        self.dataset.save()
        self.report_builder.save(deploy=True)
        self.report_builder.refresh()
        textbox_1.set_textbox_controller(TestCase.CONSTANTS.ADMIN_USERNAME)
        textbox_2.set_textbox_controller(b64encode(TestCase.CONSTANTS.ADMIN_PASSWORD.encode()).decode())
        textbox_2.set_textbox_controller(
            b64encode(TestCase.CONSTANTS.ADMIN_PASSWORD.encode()).decode() + '\t')
        # textbox_1.apply()
        data = table.get_table_data()
        if not data:
            raise CVTestStepFailure("No data present")
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def validate(self):
        """Validating contents on viewer"""
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        textbox_1 = AC_TxtBox("Username")
        textbox_2 = AC_TxtBox("Password")
        report_viewer.associate_input(textbox_1)
        report_viewer.associate_input(textbox_2)
        textbox_1.set_textbox_controller(TestCase.CONSTANTS.ADMIN_USERNAME)
        textbox_2.set_textbox_controller(b64encode(TestCase.CONSTANTS.ADMIN_PASSWORD.encode()).decode())
        textbox_2.set_textbox_controller(
            b64encode(TestCase.CONSTANTS.ADMIN_PASSWORD.encode()).decode() + '\t')
        # textbox_1.apply()
        table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(table)
        data = table.get_table_data()
        if not data:
            raise CVTestStepFailure("No data present")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_http_dataset_with_post_query()
            self.set_username_and_password_via_input()
            self.validate()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
