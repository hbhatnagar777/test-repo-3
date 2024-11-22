# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics:QBR ppt export validation"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Reports.reportsutils import PPTManager


SLIDES = {
    1: "Monthly Report",
    2: "Backup SLA",
    3: "Daily Backup Job Success Rates – 30-days",
    4: "Daily Backup Job Success Rates – 30-days",
    5: "License Consumption",
    6: "Client Data - Backup",
    7: "Client Data - Backup",
    8: "Storage Resources Summary",
    9: "Storage Resources Summary",
    10: "Health Report Summary",
    11: "Thank you!"
}


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    MIN_FILE_SIZE = 4200000  # BYTES
    FILE_TYPE = "pptx"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: RMS ppt validation"
        self.tcinputs = {}
        self.browser = None
        self.webconsole = None
        self.export = None
        self._ppt = None
        self.expected_number_of_slides = 11
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
            navigator = Navigator(self.webconsole)
            self.webconsole.goto_commcell_dashboard()
            navigator.goto_commcell_dashboard(self.commcell.commserv_name)
            report = MetricsReport(self.webconsole)
            self.export = report.export_handler()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def export_rms_ppt(self):
        """
        Generate QBR ppt
        """
        self.log.info("Exporting RMS ppt")
        self.export.to_rms_ppt()
        self.log.info("RMS export is completed")

    @test_step
    def validate_exported_file(self):
        """
        Validate exported file
        """
        self.log.info("Validating exported ppt file")
        self.utils.wait_for_file_to_download(TestCase.FILE_TYPE)
        self.utils.validate_tmp_files(TestCase.FILE_TYPE, min_size=TestCase.MIN_FILE_SIZE)

    def read_ppt(self):
        """Read ppt"""
        _files = self.utils.poll_for_tmp_files(ends_with=TestCase.FILE_TYPE)
        self._ppt = PPTManager(_files[0])

    def verify_slide_count(self):
        """Verify slide count"""
        self.log.info("Verifying slide count")
        number_of_slides = self._ppt.get_number_of_slides()
        if self.expected_number_of_slides != number_of_slides:
            raise CVTestStepFailure("Expected [%s] slides, but [%s] slides are present in qbr pptx"
                                    % (self.expected_number_of_slides, number_of_slides))
        self.log.info("expected number of slides are present in qbr ppt")

    def verify_slide_titles(self):
        """Verify slide titles"""
        self.log.info("Verifying slide titles")
        slide_number = 0
        while slide_number < self.expected_number_of_slides:
            ppt_slide_text = self._ppt.get_text_from_slide(slide_number)
            self.log.info("Checking text [%s] is present in [%s] slide", SLIDES[slide_number + 1],
                          slide_number)
            if any(SLIDES[slide_number+1] in each_list for each_list in ppt_slide_text):
                slide_number += 1
                continue
            raise CVTestStepFailure("Expected text [%s] is not present in [%s] slide "
                                    % (str(SLIDES[slide_number+1]), slide_number))
        self.log.info("slide titles verified successfully")

    @test_step
    def verify_ppt_data(self):
        """
        Verify exported ppt data
        """
        self.read_ppt()
        self.verify_slide_count()
        self.verify_slide_titles()

    def run(self):
        try:
            self.init_tc()
            self.export_rms_ppt()
            self.validate_exported_file()
            self.verify_ppt_data()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
