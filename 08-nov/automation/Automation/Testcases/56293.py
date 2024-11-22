# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Validate HTML export of Custom report and  HTML file content validation"""
import os

from Web.API import cc
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import AUTOMATION_DIRECTORY


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "HTML export validation"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.utils = TestCaseUtils(self)
        self.html_browser = None
        self.table = None
        self.rpt_api = None
        self.web_adapter = None
        self.manage_report = None
        self.report = None
        self.file_name = None
        self.web_report_table_data = None
        self.import_report_name = "Formatters"

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.report = Report(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.rpt_api = cc.Reports(machine=self.commcell.webconsole_hostname,
                                      username=self.inputJSONnode['commcell']["commcellUsername"],
                                      password=self.inputJSONnode['commcell']["commcellPassword"])
            self.manage_report = ManageReport(self.admin_console)
            self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def access_report(self):
        """Access custom report"""
        self.rpt_api.import_custom_report_xml(
            os.path.join(AUTOMATION_DIRECTORY, "Reports", "Templates", f"{self.import_report_name}.xml"))
        self.admin_console.wait_for_completion()
        self.manage_report.access_report(self.import_report_name)
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable(self.import_report_name)
        viewer_obj.associate_component(self.table)

    def modify_html_content(self, html_data):
        """
        To modify the 0 Bytes to 0 kb in the exported html file
        """
        for i in range(len(self.web_report_table_data)):
            for j in range(len(self.web_report_table_data[i])):
                if self.web_report_table_data[i][j] == '0.00 BYTES' and html_data[i][j] == '0.00 KB':
                    html_data[i][j] = '0.00 BYTES'

        return html_data

    def get_html_content(self):
        """
        Read rows from table present in HTML
        """
        html_adminconsole = AdminConsole(self.html_browser, self.commcell.webconsole_hostname)
        html_viewer = viewer.CustomReportViewer(html_adminconsole)
        html_table = viewer.DataTable(self.import_report_name)
        html_viewer.associate_component(html_table)
        html_data = html_table.get_rows_from_exported_file_table_data()
        html_data = self.modify_html_content(html_data)
        return html_data[0:20]  # reading first 20 rows only

    @test_step
    def verify_export_to_html(self):
        """
        Verify export to html is working fine
        """
        self.report.save_as_html()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("HTML export completed successfully")

    def access_file(self, file):
        """
        Access downloaded html file
        Args:
            file (str): file extension
        """
        self.file_name = self.utils.poll_for_tmp_files(ends_with=file)[0]
        if file == "html":
            self.html_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.html_browser.open()
            self.html_browser.goto_file(file_path=self.file_name)

    @test_step
    def verify_html_content(self):
        """
        Verify html file server column values are matching with report column values
        """
        self.log.info("Verifying html content for the report [%s]", self.name)
        self.web_report_table_data = self.table.get_rows_from_table_data()
        self.access_file("html")
        html_report_table_data = self.get_html_content()
        if html_report_table_data != self.web_report_table_data:
            self.log.error("HTML contents are not matching with report table content")
            self.log.error("HTML content:%s", str(html_report_table_data))
            self.log.error("Web report content:%s", str(self.web_report_table_data))
            raise CVTestStepFailure("HTML contents are not matching with report table content")
        self.log.info("HTML contents are verified successfully")

    def run(self):
        """Run method for the test"""
        try:
            self._init_tc()
            self.access_report()
            self.verify_export_to_html()
            self.verify_html_content()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.html_browser)
            Browser.close_silently(self.browser)
