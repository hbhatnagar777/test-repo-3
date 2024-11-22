# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics Reports: Table level export validation"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Reports: Table level export validation"
        self.show_to_user = True
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.reports = None
        self.table_objs = None
        self.table_index = None
        self.file_name = None
        self.commcell_password = None
        self.utils = TestCaseUtils(self)

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.reports = REPORTS_CONFIG.REPORTS.METRICS.TABLE_EXPORT
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname,
                                         username=self.commcell.commcell_username,
                                         password=self.commcell_password)
            self.webconsole.login(username=self.commcell.commcell_username,
                                  password=self.commcell_password)
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.report = MetricsReport(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def trigger_table_level_export(self, report_name):
        """
        click on table level export and verify csv file downloaded
        """
        # find available tables in report. If no tables are found then skip the validation.
        self.webconsole.wait_till_load_complete()
        self.utils.reset_temp_dir()
        self.table_objs = self.report.get_tables()
        if not self.table_objs:
            raise CVTestStepFailure("No tables are found in report [%s] for csv export"
                                    % report_name)
        self.table_index = None
        for each_table_obj in self.table_objs:
            if each_table_obj.is_csv_export_exists:
                each_table_obj.csv_export()  # click on 1st csv export of table
                # collect table index on which export is clicked
                self.table_index = self.table_objs.index(each_table_obj)
                break
        if self.table_index is None:
            raise CVTestStepFailure("No table level csv exports are found in report [%s]"
                                    % report_name)
        self.file_name = self.utils.poll_for_tmp_files(ends_with="csv")[0]
        self.log.info("Table level export csv file is downloaded for the report [%s]", report_name)
        self.log.info("File name:[%s]", self.file_name)

    def get_webconsole_table_data(self):
        """
        Read 1st 10 rows from table present in report
        """
        self.table_objs[self.table_index].show_number_of_results(number_of_results=10)
        data = self.table_objs[self.table_index].get_data()
        self.log.info("Table data present in webpage:")
        self.log.info(data)
        return data

    def get_csv_content(self):
        """
        Read csv file content
        """
        csv_content = self.utils.get_csv_content(self.file_name)
        # csv_content[0]  # 1st row has it's header(column name), So taking list from 1 to 9.
        return csv_content[1:11]

    @test_step
    def verify_csv_content(self, report_name):
        """
        Verify csv file contents are matched with web report table content
        """
        self.log.info("Verifying csv content for the report [%s]", report_name)
        web_report_table_data = self.get_webconsole_table_data()
        csv_report_table_data = self.get_csv_content()
        if web_report_table_data != csv_report_table_data:
            self.log.error("CSV contents are not matching with report table content")
            self.log.error("CSV content:%s", str(csv_report_table_data))
            self.log.error("web report content:%s", str(web_report_table_data))
            raise CVTestStepFailure("CSV contents are not matching with report table content")
        self.log.info("csv contents are verified successfully")

    def run(self):
        try:
            self._init_tc()
            for each_report in self.reports:
                self.navigator.goto_worldwide_report(each_report)
                self.trigger_table_level_export(each_report)
                self.verify_csv_content(each_report)
            # todo: sending email status for all reports.
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
