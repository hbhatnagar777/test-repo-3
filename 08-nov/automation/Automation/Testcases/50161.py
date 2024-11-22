# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: ESP Monthly and Quarterly ppt export validation"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole

from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies

from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports.reportsutils import PPTManager


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    MIN_FILE_SIZE = 310000
    MIN_MONTHLY_FILE_SIZE = 2459000
    FILE_TYPE = "pptx"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics:QBR ppt export validation"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.log = logger.get_log()
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.export = None
        self.table = None
        self.viewer = None
        self.companies = None
        self._ppt = None
        self.slides = None
        self.monthly_slides = None
        self.expected_number_of_slides = None
        self.expected_number_of_slides_monthly = None
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
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.viewer = viewer.CustomReportViewer(self.webconsole)
            self.table = viewer.DataTable("")
            self.companies = RegisteredCompanies(self.webconsole)
            self.webconsole.goto_reports()
            self.access_company_page()
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
            self.slides = self.tcinputs["SLIDES"]
            self.monthly_slides = self.tcinputs["MONTHLY_SLIDES"]
            self.expected_number_of_slides = len(self.slides)
            self.expected_number_of_slides_monthly = len(self.monthly_slides)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def access_company_page(self):
        """
        Navigate to 1st commcell group, which has at least 1 commcell
        """
        self.navigator.goto_companies()
        self.viewer.associate_component(self.table)
        self.table.set_filter("No of  CommCells", ">0")
        company_name = self.table.get_column_data("Name")
        self.companies.access_company(company_name[0])

    @test_step
    def export_qbr_ppt(self):
        """
        Generate QBR ppt
        """
        self.log.info("Exporting QBR ppt")
        self.utils.reset_temp_dir()
        self.export.to_qbr_ppt()
        self.log.info("QBR export is completed")

    @test_step
    def export_monthly_qbr_ppt(self):
        """
        Generate Monthly QBR ppt
        """
        self.log.info("Exporting monthly QBR ppt")
        self.utils.reset_temp_dir()
        self.export.to_qbr_monthly_ppt()
        self.log.info("QBR monthly export is completed")

    @test_step
    def validate_exported_file(self, ppt_type):
        """
        Validate exported file
        """
        self.log.info("Validating exported ppt file")
        self.utils.wait_for_file_to_download(TestCase.FILE_TYPE, timeout_period=200)
        if ppt_type == 'monthly':
            self.utils.validate_tmp_files(
                TestCase.FILE_TYPE, min_size=TestCase.MIN_MONTHLY_FILE_SIZE)
        else:
            self.utils.validate_tmp_files(TestCase.FILE_TYPE, min_size=TestCase.MIN_FILE_SIZE)

    def read_ppt(self):
        """Read ppt"""
        _files = self.utils.poll_for_tmp_files(ends_with=TestCase.FILE_TYPE)
        self._ppt = PPTManager(_files[0])

    def verify_slide_count(self, ppt_type):
        """Verify slide count"""
        self.log.info("Verifying slide count")
        number_of_slides = self._ppt.get_number_of_slides()
        if ppt_type == "monthly":
            if self.expected_number_of_slides_monthly != number_of_slides:
                raise CVTestStepFailure("Expected [%s] slides, but [%s] slides are present in qbr "
                                        "pptx"
                                        % (self.expected_number_of_slides_monthly,
                                           number_of_slides))
        else:
            if self.expected_number_of_slides != number_of_slides:
                raise CVTestStepFailure("Expected [%s] slides, but [%s] slides are present in qbr"
                                        " pptx"
                                        % (self.expected_number_of_slides, number_of_slides))
        self.log.info("expected number of slides are present in qbr ppt")

    def verify_slide_titles(self, ppt_type):
        """Verify slide titles"""
        self.log.info("Verifying slide titles")
        if ppt_type == "monthly":
            slide_number = 0
            while slide_number <= self.expected_number_of_slides_monthly-1:
                ppt_slide_text = self._ppt.get_text_from_slide(slide_number)
                self.log.info("Checking text [%s] is present in [%s] slide",
                              self.monthly_slides[slide_number], slide_number)
                if self.monthly_slides[slide_number] in \
                        str([each_list for each_list in ppt_slide_text]):
                    slide_number += 1
                    continue
                raise CVTestStepFailure("Expected text [%s] is not present in [%s] slide " %
                                        (str(self.monthly_slides[slide_number]), slide_number))
            self.log.info("slide titles verified successfully")
        else:
            slide_number = 0
            while slide_number <= self.expected_number_of_slides-1:
                ppt_slide_text = self._ppt.get_text_from_slide(slide_number)
                self.log.info("Checking text [%s] is present in [%s] slide"
                              , self.slides[slide_number], slide_number)
                if self.slides[slide_number] in str([each_list for each_list in ppt_slide_text]):
                    slide_number += 1
                    continue
                raise CVTestStepFailure("Expected text [%s] is not present in [%s] slide " %
                                        (str(self.slides[slide_number]), slide_number))
            self.log.info("slide titles verified successfully")

    @test_step
    def verify_ppt_data(self, ppt_type):
        """
        Verify exported ppt data
        """
        self.read_ppt()
        self.verify_slide_count(ppt_type)
        self.verify_slide_titles(ppt_type)

    def run(self):
        try:
            self.init_tc()
            for each_ppt_export in ["monthly", "quarterly"]:
                if each_ppt_export == "monthly":
                    self.export_monthly_qbr_ppt()
                else:
                    self.export_qbr_ppt()
                self.validate_exported_file(each_ppt_export)
                self.verify_ppt_data(each_ppt_export)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
