# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase to Metrics : Client Configuration Audit report
"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure, CVTimeOutException
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.config_audit import ConfigurationAuditReport
from Web.WebConsole.Reports.Metrics.report import MetricsReport

TYPE = ConfigurationAuditReport.EntityType


class TestCase(CVTestCase):
    """TestCase to Verify Metrics : Client Configuration Audit report"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics : Client Configuration Audit report"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.report_name = "Configuration Audit (Old)"
        self.entity_type = None
        self.config_report = None
        self.metrics_report = None

    def setup(self):
        """Initializes object required for this testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_worldwide_report(self.report_name)
            self.entity_type = [TYPE.STORAGE_POLICY, TYPE.MEDIA_AGENT, TYPE.LIBRARY,
                                TYPE.COMMCELL_PARAMETERS, TYPE.CLIENT]
            self.config_report = ConfigurationAuditReport(self.webconsole)
            self.utils.get_browser_logs("SEVERE")
            self.metrics_report = MetricsReport(self.webconsole)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def verify_report(self, entity_type):
        """Verify report page is not having any errors for each entity"""
        self.log.info("Verifying report for [%s] entity type", entity_type)
        self.config_report.configure_report(entity_type, True)
        self.verify_page_load()
        self.log.info("Verified report for [%s] entity type", entity_type)

    def verify_page_load(self):
        """Verify page is loaded fine"""
        self.check_page_load_time()
        self.metrics_report.verify_page_load()
        # self.check_console_error()

    def check_console_error(self):
        """Collect console errors on report"""
        console_errors = self.utils.get_browser_logs("SEVERE")
        if console_errors:
            raise CVTestStepFailure("[%s]console errors are found in report link %s" %
                                    (console_errors, self.browser.driver.current_url))

    def check_page_load_time(self, time_out=100):
        """Collect page load time for the report"""
        try:
            self.webconsole.wait_till_load_complete(timeout=time_out)
        except CVTimeOutException:
            raise CVTestStepFailure("Page did not load in report link %s" %
                                    self.browser.driver.current_url)

    def run(self):
        try:
            for each_entity in self.entity_type:
                self.verify_report(each_entity)
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
