# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: Validation of as built guide word export"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.cte import ExportHandler

from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    MIN_FILE_SIZE = 67521  # BYTES
    FILE_TYPE = "docx"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Validation of as built guide word export"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.log = logger.get_log()
        self.tcinputs = {}
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.export = None
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
            self.navigator = Navigator(self.webconsole)
            self.webconsole.goto_reports()
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _as_built_guide_export(self):
        """
        Generate as built guide export and verify the exported doc file
        """
        data_source_type = [ExportHandler.ExportConstants.AS_BUILT_GUIDE_DATSOURCE_DATABASE,
                            ExportHandler.ExportConstants.AS_BUILT_GUIDE_DATSOURCE_XML]
        for each_data_source_type in data_source_type:
            self.utils.reset_temp_dir()
            self.log.info("verifying as built guide export for data source type [%s]",
                          each_data_source_type)
            self.export.export_as_built_guide(data_source_type=each_data_source_type)
            self.log.info("As built guide export for data source type [%s] is completed",
                          each_data_source_type)
            self._verify_exported_file()

    def _verify_exported_file(self):
        """
        Validate exported file
        """
        self.utils.wait_for_file_to_download(TestCase.FILE_TYPE)
        self.utils.validate_tmp_files(TestCase.FILE_TYPE, min_size=TestCase.MIN_FILE_SIZE)
        self.log.info("Validated exported file")

    def run(self):
        try:
            self._init_tc()
            self._as_built_guide_export()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
