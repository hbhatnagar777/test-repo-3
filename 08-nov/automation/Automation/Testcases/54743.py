# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Validate exports for custom Backup Job summary report CSV export"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)

from Reports import reportsutils
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.Reports.Custom import viewer

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Backup Job summary report all columns Table Level export validation"
        self.browser = None
        self.admin_console = None
        self.file_name = None
        self.navigator = None
        self.table = None
        self.viewer = None
        self.wc = None
        self.commcell_password = None
        self.utils = TestCaseUtils(self)
        self.REPORT_NAME = "Backup job summary"
        self.TABLE_VIEW = "Job Details"

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.commcell.commcell_username,
                                              password=self.commcell_password)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=self.commcell_password)
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            self.manage_report.access_report(self.REPORT_NAME)
            self.wc = WebConsoleAdapter(self.admin_console, self.browser)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
            self.table = viewer.DataTable(self.TABLE_VIEW)
            self.viewer.associate_component(self.table)
            self.table.enable_all_columns()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def trigger_table_level_export(self):
        """
        click on table level export and verify csv file is downloaded
        """
        self.utils.reset_temp_dir()
        self.table.export_to_csv()
        self.file_name = self.utils.poll_for_tmp_files(ends_with="csv")[0]
        self.log.info("Table level export csv file is downloaded for the report [%s]",
                      self.name)
        self.log.info("File name:[%s]", self.file_name)

    def get_commandcenter_table_data(self):
        """
        Read all the column names from table present in report
        """
        data = self.table.get_all_columns()
        self.log.info("Table data present in webpage:")
        self.log.info(data)
        return data

    def get_csv_content(self):
        """
        Read csv file content
        """
        csv_content = self.utils.get_csv_content(self.file_name)
        #  csv_content[0]  #  report name ['Backup_Job_Summary_report_49989-table export']
        #  csv_content[1]  #  line ['Report generated on Apr 09 2018 16:10 PM']
        #  csv_content[2]  #  table name ['Backup_Job_Summary_report_49989-table export']
        #  csv_content[3]  #  column name (heading)
        self.log.info("CSV file content:")
        self.log.info(csv_content[3])
        return csv_content[3]

    @test_step
    def verify_csv_content(self):
        """
        Verify csv file contents are matched with web report table content
        """
        self.log.info("Verifying csv content for the report [%s]", self.name)
        web_report_table_data = self.get_commandcenter_table_data()
        csv_report_table_data = self.get_csv_content()
        if sorted(web_report_table_data) != sorted(csv_report_table_data):
            self.log.error("CSV contents are not matching with report table content")
            self.log.error("CSV content:%s", str(csv_report_table_data))
            self.log.error("web report content:%s", str(web_report_table_data))
            raise CVTestStepFailure("CSV contents are not matching with report table content")
        self.log.info("csv contents are verified successfully")

    def run(self):
        try:
            self._init_tc()
            self.trigger_table_level_export()
            self.verify_csv_content()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
