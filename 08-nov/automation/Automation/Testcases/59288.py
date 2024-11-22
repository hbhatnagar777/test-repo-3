# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Validate generation of POR"""

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import (inputs, viewer)

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.WebConsole.Reports.cte import ExportHandler
from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    FILE_TYPE = "docx"
    MIN_FILE_SIZE = 1600  # BYTES

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify POR doc exports"
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.viewer_obj = None
        self.export = None
        self.report = None
        self.navigator = None

    def _init_tc(self):
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
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
            self.viewer_obj = viewer.CustomReportViewer(self.webconsole)
            self.navigator.goto_worldwide_report(REPORTS_CONFIG.REPORTS.CUSTOM)
            self.obj_export = ExportHandler(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def select_feature_release(self):
        """
           Gets a list of SP available from SP Input and selects a SP from it
        """
        sp_input_controller = inputs.DropDownController("Feature Release")
        self.viewer_obj.associate_input(sp_input_controller)
        sp_input_controller.select_value('11.' + str(self.commcell.commserv_version))  # selecting current SP

    def generate_por(self):
        """
           Generates POR document by clicking on 'Generate POR'
        """
        html_component = viewer.HtmlComponent("")  # because title of html component is blank
        self.viewer_obj.associate_component(html_component)
        html_component.click_button("Generate POR")

    @test_step
    def verify_por_generation(self):
        """
        Verify POR document is generated

        """
        self.select_feature_release()
        self.generate_por()
        self.utils.wait_for_file_to_download(TestCase.FILE_TYPE, timeout_period=120)
        self.utils.validate_tmp_files(TestCase.FILE_TYPE,min_size=TestCase.MIN_FILE_SIZE)
        self.log.info("Verified generation of POR")

    def run(self):
        try:
            self._init_tc()
            self.verify_por_generation()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
