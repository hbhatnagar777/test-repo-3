# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: Royalty report pdf export"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports import reportsutils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    REPORT_NAME = "Royalty Report"
    MIN_FILE_SIZE = 79820
    FILE_TYPE = "pdf"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Royalty report pdf export"
        self.tcinputs = {}
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.export = None
        self.commcell_name = None
        self.metrics_table = None
        self.commcell_password = None
        self.utils = TestCaseUtils(self)

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname,
                                         username=self.commcell.commcell_username,
                                         password=self.commcell_password)
            self.webconsole.login(username=self.commcell.commcell_username,
                                  password=self.commcell_password)
            self.webconsole.goto_commcell_dashboard()
            self.navigator = Navigator(self.webconsole)
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
            self.commcell_name = reportsutils.get_commcell_name(self.commcell)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _verify_exported_file(self):
        """
        Validate exported file
        """
        self.utils.wait_for_file_to_download(TestCase.FILE_TYPE)
        self.utils.validate_tmp_files(TestCase.FILE_TYPE, min_size=TestCase.MIN_FILE_SIZE)
        self.log.info("Validated exported file")

    @test_step
    def _royalty_report_export(self):
        """
        verify commcell reports exports are working fine
        """
        self.utils.reset_temp_dir()
        self.log.info("Triggering Royalty report pdf export")
        self.navigator.goto_commcell_reports(TestCase.REPORT_NAME,
                                             self.commcell_name)
        self.export.to_pdf()
        self.log.info("Royalty report export completed successfully")

    @test_step
    def verify_report_content(self):
        """
        Verify the report content
        """
        table = self.report.get_tables()
        if not table:
            raise CVTestStepFailure("Royalty report is empty, please check the logs")
        self.log.info("Royalty report table data is available")
        MetricsReport(self.webconsole).verify_page_load()
        table_data = table[0].get_data()
        if not table_data:
            raise CVTestStepFailure("No data available on Royalty report")

    def run(self):
        try:
            self._init_tc()
            self._royalty_report_export()
            self.verify_report_content()
            self._verify_exported_file()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
