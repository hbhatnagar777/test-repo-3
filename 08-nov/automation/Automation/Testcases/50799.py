# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Growth and trend report export validation """
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.Metrics.growthtrend import GrowthNTrend
from Web.WebConsole.Reports.Metrics.report import ExportedReport
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    TILES = ['CommCells', 'Agents', 'Client Groups', 'Disk Libraries', 'Capacity License Usage',
             'Capacity License Usage by Agent', 'CommCell Dedupe Savings', 'Agent Dedupe Savings',
             'Storage Policy Dedupe Savings', 'Subclient Dedupe Savings', 'Clients Count']

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Growth and trend report export validation"
        self.show_to_user = True
        self.log = logger.get_log()
        self.tcinputs = {}
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.export = None
        self.report_name = 'Growth and Trends'
        self.entities = None
        self.report_url = None
        self.growth_n_trend = None
        self.exported_file_browser = None
        self.exported_file = None
        self.growthtrend = None
        self.commcell_password = None
        self.utils = TestCaseUtils(self)

    def _init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.utils.reset_temp_dir()
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
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_worldwide_report(self.report_name)
            self.report_url = self.browser.driver.current_url
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
            self.growthtrend = GrowthNTrend(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def save_as_html(self):
        """Export report to html"""
        self.utils.reset_temp_dir()
        self.export.to_html()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('html')
        self.log.info("html export completed successfully")

    def access_growth_and_trend_report(self):
        """Access growth and trend report"""
        self.browser.driver.get(self.report_url)
        self.webconsole.wait_till_load_complete()

    def access_exported_file(self):
        """Access exported html file"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.exported_file_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.exported_file_browser.open()
        self.exported_file_browser.goto_file(file_path=html_path)
        self.exported_file = ExportedReport(self.exported_file_browser)

    @test_step
    def validate_exported_file(self):
        """Compare exported file title with web page growth and trend report page title"""
        web_page_title = self.report.get_page_title()
        self.access_exported_file()
        exported_file_title = self.exported_file.get_page_title()
        if web_page_title != exported_file_title:
            raise CVTestStepFailure("webpage %s growth and trend report title is not matching "
                                    "with %sexported file growth and trend report title " %
                                    (web_page_title, exported_file_title))
        Browser.close_silently(self.exported_file_browser)
        self.log.info("Validated exported file for %s growth and trend report", web_page_title)

    @test_step
    def verify_tiles(self):
        """Verifies the presence of necessary tiles tiles"""
        violated_tiles = [tile for tile in TestCase.TILES if tile not in self.entities]
        if violated_tiles:
            raise CVTestStepFailure(f"{violated_tiles} are not seen in Growth and Trends report")

    def run(self):
        try:
            self._init_tc()
            self.entities = self.growthtrend.get_entities()  # Read all the entities
            self.log.info("Growth and trend reports:%s", str(self.entities))
            for each_entity in self.entities:
                self.log.info("Validating export for %s growth and trend report", each_entity)
                self.growthtrend.access_view_details(each_entity)
                self.save_as_html()
                self.validate_exported_file()
                self.access_growth_and_trend_report()  # for next export access the report again
                # todo : table level export validation
                self.verify_tiles()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
