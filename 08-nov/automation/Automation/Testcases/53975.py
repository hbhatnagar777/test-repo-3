# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Custom Reports: Validate Export Preview"""

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.utils import CustomReportUtils
from Reports.Custom.sql_utils import (
    SQLQueries,
    ValueProcessors
)
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom.viewer import (
    CustomReportViewer,
    DataTable
)


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.navigator = None
        self.manage_report = None
        self.admin_console = None
        self.name = "Custom Reports - Validate Export Preview"
        self.browser = None
        self.webconsole = None
        self.utils = CustomReportUtils(self)
        self.commcell_password = None
        self.report = None

    def init_tc(self):
        """Initializes the Test case"""
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                         username=self.commcell.commcell_username,
                                         password=self.commcell_password)
            self.admin_console.login(username=self.commcell.commcell_username,
                                  password=self.commcell_password)
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
            self.manage_report = ManageReport(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.delete_report()
            self.manage_report.add_report()
            self.report = DefaultReport(self.utils, self.admin_console, self.browser)
            self.report.build_default_report(overwrite=False)
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[1])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def delete_report(self):
        """Delete the report"""
        self.navigator.navigate_to_reports()
        self.manage_report.delete_report(self.name)
        self.browser.driver.refresh()
        self.admin_console.wait_for_completion()

    @test_step
    def validate_export_preview(self):
        """Validates export preview"""
        self.utils.reset_temp_dir()
        self.report.report_builder.export_preview()
        self.utils.poll_for_tmp_files("html")
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        with BrowserFactory().create_browser_object(name="ClientBrowser") as browser:
            browser.goto_file(file_path=html_path)
            admin_console = WebConsole(browser, self.commcell.webconsole_hostname)
            viewer = CustomReportViewer(admin_console)
            table = DataTable("Automation Table")
            viewer.associate_component(table)
            SQLQueries.validate_equality(SQLQueries.sql_server_r1(value_processor=ValueProcessors.string),
                                         table.get_exported_table_data())

    def run(self):
        try:
            self.init_tc()
            self.validate_export_preview()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
