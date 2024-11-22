# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Admin Console Reports: Verification of Export functionality
    and content validation in Chinese Locale"""
import math
from decimal import Decimal, ROUND_HALF_UP
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter

from Web.AdminConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase

from Reports import reportsutils
from Reports.utils import TestCaseUtils

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = """Admin Console Reports: Verification of Export functionality
                         and content validation in Chinese Locale"""
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.report = None
        self.commcell_reports = None
        self.web_report_table_data = None
        self.table = None
        self.file_name = None
        self.html_browser = None
        self.csv_content = None
        self.admin_console = None
        self.navigator = None
        self.web_adapter = None
        self.automation_username = "tc57885"
        self.automation_password = "Tc!57885"
        self.full_username = None

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory: %s", download_directory)
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.create_user()
            self.admin_console.login(self.full_username, self.automation_password)
            self.report = Report(self.admin_console)
            self.admin_console.change_language('english', self.report)
            self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
            self.navigator = self.admin_console.navigator
            self.commcell_reports = REPORTS_CONFIG.REPORTS.CUSTOM
            self.report = Report(self.admin_console)
            manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            manage_report.access_report(self.commcell_reports[0])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def create_user(self):
        """Creates user and roles"""
        user_obj = self.commcell.users.get(self.inputJSONnode['commcell']["commcellUsername"])
        company_name = user_obj.user_company_name
        self.full_username = company_name+'\\'+self.automation_username
        if not self.commcell.users.has_user(self.full_username):
            self.commcell.users.add(
                self.automation_username,
                "reports@testing.com",
                self.automation_username,
                None,
                self.automation_password
            )
            dict_ = {"assoc1":
                     {
                         'clientName': [self.commcell.commserv_name],
                         'role': ["Report Management"]
                     }
                     }
            self.commcell.users.get(self.full_username).update_security_associations(
                dict_, "UPDATE"
            )

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

    def get_html_content(self):
        """
        Read rows from table in HTML
        """
        html_adminconsole = AdminConsole(self.html_browser, self.commcell.webconsole_hostname)
        html_viewer = viewer.CustomReportViewer(html_adminconsole)
        html_table = viewer.DataTable("作业详细信息")
        html_viewer.associate_component(html_table)
        html_data = html_table.get_exported_table_data()
        return html_data[0:20]  # reading first 20 rows only

    @staticmethod
    def convert_size(size_bytes):
        """
        Converts bytes to KB, MB, GB & TB
        Args:
            size_bytes (str): size in bytes
        Returns:
             converted size with format Ex: 1.6MB
        """
        size_bytes = int(size_bytes)
        if size_bytes == 0:
            return "0.00 KB"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        integer = int(math.floor(math.log(size_bytes, 1024)))
        power = math.pow(1024, integer)
        size = str(Decimal(size_bytes / power).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        if len(size.split(".")[1]) == 1:
            size = size+'0'
        return "%s %s" % (size, size_name[integer])

    def size_column_conversion(self, index=0):
        """
        Read csv content and convert format of specified columns
        Args:
            index (int) : index of column
        """
        for row in range(4, len(self.csv_content)):
            app_size = self.convert_size(self.csv_content[row][index])
            self.csv_content[row][index] = app_size

    def get_csv_content(self):
        """
        Read csv file content
        """
        self.csv_content = self.utils.get_csv_content(self.file_name)
        size_column = ['应用大小', '介质大小']  # Converting App size,Media Size column from bytes to KB,MB.
        for col in self.csv_content[3]:
            if col in size_column:
                index = self.csv_content[3].index(col)
                self.size_column_conversion(index)
        self.log.info("CSV file content:")
        self.log.info(self.csv_content[4:24])
        return self.csv_content[4:24]  # First 20 rows only

    @test_step
    def validate_csv_content(self):
        """
        Verify csv file contents are matching with report table content
        """
        self.log.info("Verifying csv content for the report [%s]", self.name)
        self.access_file("csv")
        csv_report_table_data = self.get_csv_content()
        if self.web_report_table_data != csv_report_table_data:
            self.log.error("CSV content:%s", str(csv_report_table_data))
            self.log.error("Web report content:%s", str(self.web_report_table_data))
            raise CVTestStepFailure("CSV contents are not matching with report table content")
        self.log.info("CSV contents are verified successfully")

    @test_step
    def validate_html_content(self):
        """
        Verify html file contents are matching with report table content
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

    @test_step
    def verify_export_to_csv(self):
        """
        Verify export to csv of table
        """
        self.table.export_to_csv()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("CSV export completed successfully")

    @test_step
    def verify_export_to_html(self):
        """
        Verify report export to html
        """
        self.report.save_as_html()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("HTML export completed successfully")

    @test_step
    def validate_export(self):
        """
        Verify export, in HTML and CSV, of report in Chinese Language
        """
        self.log.info("validating export for report %s", self.commcell_reports[0])
        self.verify_export_to_html()
        self.verify_export_to_csv()
        self.log.info("Report is exported in Admin Console")

    @test_step
    def initial_config(self):
        """
        Initial Configuration for export like changing locale and table configurations
        """
        self.log.info("Initial Configuration for test steps")
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        self.admin_console.change_language('chinese', self.report)
        self.admin_console.wait_for_completion()
        self.table = viewer.DataTable("作业详细信息")  # "Job Details" table
        viewer_obj.associate_component(self.table)
        visible_columns = self.table.get_table_columns()
        expected_columns = ['作业ID', 'Server', '代理', '子客户端', '类型', '备份类型', '应用大小', '介质大小', '作业状态']#, '失败原因']
        if visible_columns != expected_columns:
            hide_columns = list(set(visible_columns) - set(expected_columns))
            for col in hide_columns:
                self.table.toggle_column_visibility(col)
        self.log.info("Initial setup completed")

    def run(self):
        """Run method for the test"""
        try:
            self._init_tc()
            self.initial_config()
            self.validate_export()
            self.validate_html_content()
            self.validate_csv_content()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            self.admin_console.change_language('english', self.report)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.html_browser)
            Browser.close_silently(self.browser)
