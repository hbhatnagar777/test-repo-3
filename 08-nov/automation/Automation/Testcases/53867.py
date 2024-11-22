# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Admin Console Reports: Verification of Export functionality"""

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Reports import reportsutils
from AutomationUtils import config

REPORTS_CONFIG = reportsutils.get_reports_config()
CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin Console Reports: Verification of Export functionality"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.report = None
        self.manage_report = None
        self.commcell_reports = None

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
            self.navigator = self.admin_console.navigator
            self.commcell_reports = REPORTS_CONFIG.REPORTS.CUSTOM
            self.report = Report(self.admin_console)
            self.manage_report = ManageReport(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_export_to_pdf(self):
        """
        Verify export to pdf
        """
        self.report.save_as_pdf()
        '''
        notification = self.report.get_notification()
        if not notification == 'The report is being generated. Please wait.':
            raise CVWebAutomationException("Confirmation Message Failure:\n Expected: The "
                                           "report is being generated. Please wait. Received: "
                                           + notification)
        '''
        self.utils.wait_for_file_to_download('pdf')
        self.utils.validate_tmp_files("pdf")
        self.log.info("pdf export completed successfully")

    @test_step
    def verify_export_to_csv(self):
        """
        Verify export to csv
        """
        self.report.save_as_csv()
        '''
        notification = self.report.get_notification()
        if not notification == 'The report is being generated. Please wait.':
            raise CVWebAutomationException("Confirmation Message Failure:\n Expected: The "
                                           "report is being generated. Please wait. Received: "
                                           + notification)
        '''
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("csv export completed successfully")

    @test_step
    def verify_export_to_html(self):
        """
        Verify export to html
        """
        self.report.save_as_html()
        '''
        notification = self.report.get_notification()
        if not notification == 'The report is being generated. Please wait.':
            raise CVWebAutomationException("Confirmation Message Failure:\n Expected: The "
                                           "report is being generated. Please wait. Received: "
                                           + notification)
        '''
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("html export completed successfully")

    @test_step
    def validate_export(self):
        """
        Verify export for web reports
        """
        for report in self.commcell_reports:
            self.log.info("validating export for report %s", report)
            self.navigator.navigate_to_reports()
            self.manage_report.access_report(report)
            self.utils.reset_temp_dir()
            self.verify_export_to_pdf()
            self.verify_export_to_csv()
            self.verify_export_to_html()
        self.log.info("Verified export for reports in Admin Console")

    def run(self):
        """Run method for the test"""
        try:
            # verify export for tenant admin
            self._init_tc()
            self.validate_export()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close()
