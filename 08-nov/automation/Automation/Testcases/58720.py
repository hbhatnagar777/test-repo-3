# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Admin Console : Verification of Export in HTML and CSV with company selection"""

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
        self.name = """Admin Console: Export in HTML and CSV format with company selection"""
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.report = None
        self.commcell_reports = None
        self.table = None
        self.file_name = None
        self.html_browser = None
        self.admin_console = None
        self.navigator = None
        self.column_name = "Server"
        self.columns = None
        self.report_column_values = None
        self.company_clients = None
        self.tcinputs = {
            "companyName": None
        }

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
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])

            self.commcell_reports = REPORTS_CONFIG.REPORTS.CUSTOM
            self.report = Report(self.admin_console)
            self.navigator = self.admin_console.navigator

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def initial_config(self):
        """
        Initial Configuration for test steps like selecting a company, navigating to report etc.
        """
        self.log.info("Initial Configuration for test steps")

        # Selects a company
        self.navigator.switch_company_as_operator(self.tcinputs['companyName'])

        # Navigate to reports
        self.navigator.navigate_to_reports()
        manage_report = ManageReport(self.admin_console)
        manage_report.access_report(self.commcell_reports[0])

        # select Company column in table
        web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable("Job Details")
        viewer_obj.associate_component(self.table)
        visible_columns = self.table.get_table_columns()
        company_column = 'Company'
        if company_column not in visible_columns:
            self.table.toggle_column_visibility(company_column)

        # Get data of Server Column
        self.report_column_values = self.table.get_column_data(self.column_name)

        # Verify Company column contains only company name as in input
        if list(set(self.table.get_column_data(company_column))) != [self.tcinputs['companyName']]:
            self.log.info("Company column values displayed [%s]",
                          self.table.get_column_data(company_column))
            raise CVTestStepFailure("Company column contains values other than company [%s]",
                                    self.tcinputs['companyName'])
        self.log.info("Initial setup completed")

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
        Read HTML table and returns specified column data
        """
        html_adminconsole = AdminConsole(self.html_browser, self.commcell.webconsole_hostname)
        html_viewer = viewer.CustomReportViewer(html_adminconsole)
        html_table = viewer.DataTable("Job Details")
        html_viewer.associate_component(html_table)
        html_column_data = html_table.get_exported_table_data()
        return html_column_data[self.column_name][0:20]  # reading first 20 rows only

    def get_csv_column_content(self, data_column):
        """
        Read csv file content and returns value of column specified
        """
        csv_content = self.utils.get_csv_content(self.file_name)
        column_content = list(map(list, zip(*(csv_content[4:20]))))
        for columns in csv_content[3]:
            if columns == data_column:
                index = csv_content[3].index(data_column)
                return column_content[index]

    @test_step
    def validate_html_content(self):
        """
        Verify html file server column values are matching with report column values
        """
        self.log.info("Verifying html content for the report [%s]", self.name)
        self.access_file("html")
        html_column_values = self.get_html_content()
        if set(html_column_values) != set(self.report_column_values):
            self.log.error("HTML column has values :%s", str(html_column_values))
            self.log.error("Web report column has values :%s", set(self.report_column_values))
            raise CVTestStepFailure("HTML column values are not matching with report column values")

        self.log.info("HTML contents are verified successfully")

    @test_step
    def validate_csv_content(self):
        """
        Verify csv file server column values are matching with report column values
        """
        self.log.info("Verifying csv content for the report [%s]", self.name)
        self.access_file("csv")
        csv_column_values = self.get_csv_column_content(self.column_name)
        if set(csv_column_values) != set(self.report_column_values):
            self.log.error("CSV column has values :%s", str(csv_column_values))
            self.log.error("Web report column has values :%s", set(self.report_column_values))
            raise CVTestStepFailure("CSV column values are not matching with report column values")
        self.log.info("CSV contents are verified successfully")

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
    def verify_export_to_csv(self):
        """
        Verify export to csv of table "Job Details"
        """
        self.table.export_to_csv()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("CSV export completed successfully")

    def run(self):
        """Run method for the test"""
        try:
            self._init_tc()
            self.initial_config()
            self.verify_export_to_html()
            self.verify_export_to_csv()
            self.validate_html_content()
            self.validate_csv_content()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.html_browser)
            Browser.close_silently(self.browser)

