# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Report: Validate Other HTTP Datasets"""

from Reports.Custom.utils import CustomReportUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole

from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Validate Other HTTP Datasets"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.http_dataset = None
        self.utils = CustomReportUtils(self)
        self.api = "https://gitlab.testlab.commvault.com/api/v4/projects"
        self.report_builder = None

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
            raise CVTestStepFailure(exception)from exception

    @test_step
    def open_http_dataset_panel(self):
        """Creates join dataset from two database datasets"""
        self.report_builder = builder.ReportBuilder(self.webconsole)
        self.report_builder.set_report_name(self.name)
        self.http_dataset = builder.Datasets.HTTPDataset()
        self.report_builder.add_dataset(self.http_dataset)
        self.http_dataset.set_dataset_name("Automation Dataset 50526")
        self.http_dataset.enable_other_http(remove_existing=True)
        self.http_dataset.set_get(self.api)

    @test_step
    def preview_content(self):
        """Clicks preview to validate row expression"""
        expected_row_expression = "$.[*]"
        self.http_dataset.get_preview_data()
        row_expression = self.http_dataset.get_row_expression()

        if row_expression != expected_row_expression:
            raise CVTestStepFailure("Unexpected row expression [%s], expected [%s]" % (
                str(row_expression), str(expected_row_expression)))

        self.http_dataset.save()

    @test_step
    def save_and_deploy(self):
        """Builds the report,validates and deploys it"""
        table = builder.DataTable("Automation Table 50526")
        self.report_builder.add_component(table, self.http_dataset)
        table.add_column_from_dataset()
        data = table.get_table_data()
        self.validate(data)
        self.report_builder.save(deploy=True)

    @test_step
    def view_report(self):
        """Open report and validate the content"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Automation Table 50526")
        report_viewer.associate_component(table)
        data = table.get_table_data()
        self.validate(data)

    def validate(self, data):
        """Validates whether the column name is not empty and contains at least one row"""
        for key, value in data.items():
            if key == "":
                raise CVTestStepFailure("API response for %s has Empty Key." % self.api)
            if len(value) <= 0:
                raise CVTestStepFailure("API response for %s has Empty value" % self.api)

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.open_http_dataset_panel()
            self.preview_content()
            self.save_and_deploy()
            self.view_report()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
