# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Web Console: Validate tenant user security on Report"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)

from Reports.Custom.utils import CustomReportUtils
from Reports.metricsutils import MetricsServer

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.home import ReportsHomePage


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Web Console: Validate tenant user don't have access to metrics reports"
        self.browser = None
        self.webconsole = None
        self.tcinputs = {
            "tenant_email": None,
            'password': None
        }

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.tcinputs['tenant_email'],
                self.tcinputs['password']
            )
            self.webconsole.goto_reports()
            self.utils = CustomReportUtils(self)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_report_name_from_DB(self):
        """
        Get the report name from the DB
        """
        metrics_utils = MetricsServer(
            self.commcell.webconsole_hostname,
            self.inputJSONnode['commcell']["commcellUsername"],
            self.inputJSONnode['commcell']["commcellPassword"]
        )
        metrics_reports_DB = metrics_utils.get_metrics_reports()
        return metrics_reports_DB

    def get_reports_from_report_page(self):
        """
        Get the report names from the report page
        """
        reports_home_page = ReportsHomePage(webconsole=self.webconsole)
        reports = reports_home_page.get_all_report_details()
        web_reports = []
        for report in range(len(reports)):
            new_report = reports[report].get('name')
            web_reports.append(new_report)
        return web_reports

    @test_step
    def validate_repot_data(self):
        """
        Validate the metrics report from the tenant user account
        """
        DB_reports = self.get_report_name_from_DB()
        web_reports = self.get_reports_from_report_page()
        for each_report in web_reports:
            if each_report in DB_reports and each_report != "SLA":
                self.log("Metrics reports are available")
                self.log(f"List of web reports {web_reports}")
                self.log(f"List of reports from DB {DB_reports}")
                raise CVTestStepFailure(f'Metrics report {each_report} is visible for tenant admin')

    def run(self):
        try:
            self._init_tc()
            self.validate_repot_data()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
