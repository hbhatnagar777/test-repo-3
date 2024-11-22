# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Non metrics webconsole report export validation """
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.home import ReportsHomePage
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.health_tiles import GenericTile

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
        self.name = "Non metrics webconsole report export validation"
        self.browser = None
        self.webconsole = None
        self.report = None
        self.export = None
        self.commcell_name = None
        self.custom_report = None
        self.report_home_page = None
        self.tcinputs = {"reportname": None}
        self.navigator = None
        self.health_tile = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
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
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.report_home_page = ReportsHomePage(self.webconsole)
            self.navigator = Navigator(self.webconsole)
            self.health = GenericTile(self.webconsole, self.tcinputs["reportname"])
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
            self.custom_report = REPORTS_CONFIG.REPORTS.CUSTOM[0]
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def verify_export_to_pdf(self):
        """
        Verify report export to pdf
        """
        self.export.to_pdf()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download(ends_with='pdf', timeout_period=200)
        self.utils.validate_tmp_files("pdf")
        self.log.info("pdf export completed successfully")

    def verify_export_to_csv(self):
        """
        Verify report export to csv
        """
        self.export.to_csv()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("csv export completed successfully")

    def verify_export_to_html(self):
        """
        Verify report export to html
        """
        self.export.to_html()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("html export completed successfully")

    @test_step
    def verify_report_export(self):
        """
        Verify custom report exports
        """
        self.webconsole.goto_reports()
        self.report_home_page.goto_report(self.custom_report)
        self.log.info("validating export for report [%s]", self.custom_report)
        self.utils.reset_temp_dir()
        self.verify_export_to_pdf()
        self.verify_export_to_csv()
        self.verify_export_to_html()
        self.log.info("Verified export!")

    @test_step
    def verify_health_via_tppm(self):
        """
        Verify health report export
        """
        self.navigator.goto_health_report()
        self.health.access_view_details()
        self.verify_export_to_html()

    def verify_dashboard_is_not_visible(self):
        """Verify dashboard is not visible for non metrics server"""
        if self.webconsole.is_commcell_dashboard_visible():
            raise CVTestStepFailure("Dashboard is visible in non metrics setup [%s]" %
                                    self.commcell.commserv_name)
        self.log.info("Verified commcell dashboard is not visible!")

    def run(self):
        try:
            self.init_tc()
            self.verify_dashboard_is_not_visible()
            self.verify_report_export()
            self.verify_health_via_tppm()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
