# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Report : Table level export"""
import os
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from Reports import reportsutils
from Reports.Custom.utils import CustomReportUtils
from Web.API.webconsole import Reports
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (Export) - Table level export"
        self.log = logger.get_log()
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.file_name = None
        self.table = None
        self.rpt_api = None
        self.report = None
        self.web_adapter = None
        self.manage_report = None
        self.commcell_password = None
        self.import_report_name = "TableLevelExport"
        self.report_table_name = "Automation Table"
        self.utils = CustomReportUtils(self)

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
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.report = Report(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.rpt_api = Reports(
                self.commcell.webconsole_hostname
            )
            self.manage_report = ManageReport(self.admin_console)
            self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def access_report(self):
        """Access custom report"""
        self.rpt_api.import_custom_report_xml(
            os.path.join(AUTOMATION_DIRECTORY, "Reports", "Templates", f"{self.import_report_name}.xml"))
        self.manage_report.access_report(self.import_report_name)
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable(self.report_table_name)
        viewer_obj.associate_component(self.table)

    def access_file(self, file):
        """
        Access downloaded file
        Args:
            file (str): file extension
        """
        self.file_name = self.utils.poll_for_tmp_files(ends_with=file)[0]

    @test_step
    def trigger_table_level_export(self):
        """
        click on table level export and verify csv file is downloaded
        """
        self.table.export_to_csv()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("CSV export completed successfully")

    def get_webconsole_table_data(self):
        """
        Read 1st 10 rows from table present in report
        """
        data = self.table.get_rows_from_table_data()
        self.log.info("Table data present in webpage:")
        self.log.info(data)
        return data

    def get_csv_content(self):
        """
        Read csv file content
        """
        self.access_file("csv")
        csv_content = self.utils.get_csv_content(self.file_name)
        #  csv_content[0]  #  report name ['Automation_report_49989-table export']
        #  csv_content[1]  #  line ['Report generated on Apr 09 2018 16:10 PM']
        #  csv_content[2]  #  table name ['Automation_report_49989-table export']
        #  csv_content[3]  #  column name (heading)
        #  so rows from 4 to 10 taking for validation
        self.log.info("CSV file content:")
        self.log.info(csv_content[4:10])
        return csv_content[4:10]

    @test_step
    def verify_csv_content(self):
        """
        Verify csv file contents are matched with web report table content
        """
        self.log.info("Verifying csv content for the report [%s]", self.name)
        web_report_table_data = self.get_webconsole_table_data()
        csv_report_table_data = self.get_csv_content()
        if web_report_table_data != csv_report_table_data:
            self.log.error("CSV contents are not matching with report table content")
            self.log.error("CSV content:%s", str(csv_report_table_data))
            self.log.error("web report content:%s", str(web_report_table_data))
            raise CVTestStepFailure("CSV contents are not matching with report table content")
        self.log.info("csv contents are verified successfully")

    def run(self):
        """Run method for the test"""
        try:
            self._init_tc()
            self.access_report()
            self.trigger_table_level_export()
            self.verify_csv_content()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
