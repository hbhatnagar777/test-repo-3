# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from datetime import datetime

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.activity import MetricsActivity
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Verify MSP company data in Private Metrisc server
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "MSP company data in Private Metrisc server"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.navigator: Navigator = None
        self.activity = None
        self.tcinputs = {
            "CompanyName": None,
            "clients": None
        }
        self.utils: TestCaseUtils = None
        self.report = None
        self.client = None

    def init_tc(self):
        """initialize Fs helper """
        try:
            self.utils = TestCaseUtils(self)

        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def init_webconsole(self):
        """
        initialize webconsole objects
        """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.navigator = Navigator(self.webconsole)
            self.activity = MetricsActivity(self.webconsole)
            self.report = MetricsReport(self.webconsole)
            self.webconsole.goto_reports()
            self.navigator.goto_commcell_reports('Activity',
                                                 commcell_name=self.commcell.commserv_name)
            self.report.select_company(self.tcinputs["CompanyName"])
            self.activity.access_last_12_months_chart()
            self.clients = self.tcinputs["clients"]

        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def get_current_day(self):
        """
        get the current day
        """
        day = datetime.today().strftime('%d')
        return day

    @test_step
    def access_daily_report(self):
        """
        Access daily report
        """
        self.init_webconsole()
        self.activity.access_daily_details(self.get_current_day())

    @test_step
    def verify_company_date(self):
        """
        validate the company client are only showing in the details report
        """
        table = MetricsTable(self.webconsole, table_name='Job Details')
        client_list = table.get_data_from_column('Client')
        client_list = list(set(client_list))
        if self.clients not in client_list:
            raise CVTestStepFailure(
                    "Client [%s] listed in report is not part of the company", self.clients)

    def run(self):
        try:
            self.init_tc()
            self.access_daily_report()
            self.verify_company_date()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
