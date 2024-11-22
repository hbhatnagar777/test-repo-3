# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: EMEA QBR doc export validation"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator

from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies

from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    MIN_FILE_SIZE = 1600000  # BYTES
    FILE_TYPE = "docx"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: EMEA QBR doc export validation"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.metrics_report = None
        self.export = None
        self.report = None
        self.table = None
        self.viewer = None
        self.companies = None

    def setup(self):
        """Initializes object required for this testcase"""
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
            self.access_commcell_group_page()
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def access_commcell_group_page(self):
        """
        Navigate to 1st commcell group, which has at least 1 commcell
        """
        self.navigator.goto_companies()
        self.viewer.associate_component(self.table)
        self.table.set_filter("No of  CommCells", ">0")
        company_name = self.table.get_column_data("Name")
        self.companies.access_company(company_name[0])

    @test_step
    def verify_qbr_doc_export(self):
        """
        Export QBR doc
        """
        self.log.info("Exporting EMEA QBR doc")
        self.export.to_emea_qbr_doc()
        self.log.info("Export is completed")

    @test_step
    def validate_exported_file(self):
        """
        Validate exported doc file
        """
        self.log.info("Validating exported ppt file")
        self.utils.wait_for_file_to_download(TestCase.FILE_TYPE)
        self.utils.validate_tmp_files(TestCase.FILE_TYPE, min_size=TestCase.MIN_FILE_SIZE)

    def run(self):
        try:
            self.verify_qbr_doc_export()
            self.validate_exported_file()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
