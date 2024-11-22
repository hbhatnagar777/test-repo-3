# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Validate exports for worldwide and commcell level reports"""
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Reports import reportsutils
from Web.Common.exceptions import CVWebAutomationException


REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.machine = None
        self.name = "Reports export validation"
        self.log = logger.get_log()
        self.browser = None
        self.admin_console = None
        self.manage_report = None
        self.report = None
        self.navigator = None
        self.worldwide_reports = None
        self.commcell_reports = None
        self.commcell_name = None
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
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.commcell.commcell_username,
                                              password=self.commcell_password)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=self.commcell_password)
            self.worldwide_reports = REPORTS_CONFIG.REPORTS.METRICS.WORLDWIDE
            self.commcell_name = reportsutils.get_commcell_name(self.commcell)
            self.machine = Machine(self.commcell.webconsole_hostname, self.commcell)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def init_props(self):
        """
        Initialize properties
        """
        self.report = Report(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.manage_report = ManageReport(self.admin_console)
        self.navigator.navigate_to_metrics()

    def verify_export_to_pdf(self):
        """
        Verify export to pdf is working fine
        """
        self.report.save_as_pdf()
        self.utils.wait_for_file_to_download('pdf')
        self.utils.validate_tmp_files("pdf")
        self.log.info("pdf export completed successfully")

    def verify_export_to_csv(self):
        """
        Verify export to csv is working fine
        """
        self.report.save_as_csv()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("csv export completed successfully")

    def verify_export_to_html(self):
        """
        Verify export to html is working fine
        """
        self.report.save_as_html()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("html export completed successfully")

    def _export_report(self):
        """
        Verify export to pdf, csv, html html is working fine
        """
        self.verify_export_to_pdf()
        self.verify_export_to_csv()
        self.verify_export_to_html()

    @test_step
    def verify_json_deleted(self):
        """Verify that JSON file is deleted after export completes"""
        path = self.machine.get_registry_value('Base', 'dGALAXYHOME') + "\\Reports\\exported"
        if self.machine.check_file_exists(path + "\\*.json"):
            raise CVTestStepFailure(f"JSON created as part of export is not being deleted from %s", path)

    @test_step
    def verify_worldwide_reports_export(self):
        """
        Verify worldwide exports are working fine
        """
        for each_report in self.worldwide_reports:
            self.log.info("validating export for worldwide report %s", each_report)
            self.manage_report.access_report_tab()
            self.manage_report.access_report(each_report)
            self.utils.reset_temp_dir()
            self._export_report()
            self.navigator.navigate_to_metrics()
        self.log.info("Verified export for worldwide reports")

    @test_step
    def verify_commcell_reports_exports(self):
        """
        verify commcell reports exports are working fine
        """
        for each_report in self.commcell_reports:
            self.log.info("validating export for commcell report %s", each_report)
            try:
                self.manage_report.goto_commcell_reports(each_report, self.commcell_name)
            except CVWebAutomationException as ex:
                if each_report == 'Job Summary' or each_report == 'SLA' or each_report == '作业摘要':
                    continue
                else:
                    raise CVWebAutomationException(ex)
            self.utils.reset_temp_dir()
            self._export_report()
            self.navigator.navigate_to_metrics()
        self.log.info("Verified export for commcell level reports")

    def run(self):
        try:
            self._init_tc()
            locales = ['english', 'chinese']
            self.init_props()
            self.verify_worldwide_reports_export()
            for local in locales:
                self.admin_console.change_language(local, self.navigator)
                self.init_props()
                if local == 'english':
                    self.commcell_reports = REPORTS_CONFIG.REPORTS.METRICS.COMMCELL_REPORTS
                elif local == 'chinese':
                    self.log.info("Verify export for commcell level reports using chines local ")
                    self.commcell_reports = REPORTS_CONFIG.REPORTS.METRICS.CHINES_LOCAL_COMMCELL_REPORTS
                self.verify_commcell_reports_exports()
            # need to implement json_delete TestStep for html exports
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.admin_console.change_language('english', self.report)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
