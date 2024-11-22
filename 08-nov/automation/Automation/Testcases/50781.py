# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase to Verify SQL given to Dimension Data for Monthly Chargeback
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    """TestCase to Verify SQL given to Dimension Data for Monthly Chargeback"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify SQL given to Dimension Data for Monthly Chargeback"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.custom_report_name = "DimensionData Chargeback Report"
        self.webconsole = None
        self.navigator = None
        self.report_viewer = None
        self.report_summary_table = None
        self.report_details_table = None

    def setup(self):
        """Initializes object required for this testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_worldwide_report(self.custom_report_name)
            self.report_viewer = viewer.CustomReportViewer(self.webconsole)
            self.report_summary_table = viewer.DataTable("Summary")
            self.report_details_table = viewer.DataTable("Details")
            self.report_viewer.associate_component(self.report_summary_table)
            self.report_viewer.associate_component(self.report_details_table)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    @test_step
    def verify_data_exists(self):
        """Verify data exists in report"""
        summary_table = self.report_summary_table.get_table_data()
        details_table = self.report_details_table.get_table_data()
        if not summary_table:
            raise CVTestStepFailure("Summary table in report is not having any data")
        if not details_table:
            raise CVTestStepFailure("Details table in report is not having any data")
        self.log.info("verified custom report is loading fine")

    def run(self):
        try:
            self.verify_data_exists()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
