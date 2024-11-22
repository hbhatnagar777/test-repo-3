# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Public Company dashboard validation TestCase"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies
from Web.WebConsole.Reports.Company.dashboard import Dashboard
from Web.WebConsole.Reports.monitoringform import ManageCommcells
from Reports.utils import TestCaseUtils
from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()
_CONFIG = get_config()


class TestCase(CVTestCase):
    """Public cloud: Company dashboard validation"""
    # pylint: disable=too-many-instance-attributes

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Public Metrics Company Dashboard: Verify CommCell list"
        self.utils = None
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.companies = None
        self.monitoringform = None
        self.db_commcells = None
        self.company_name = None
        self.dashboard = None

    def init_tc(self):
        """ Initialize the test case arguments"""
        try:
            self.utils = TestCaseUtils(self, self.inputJSONnode['commcell']["commcellUsername"],
                                       self.inputJSONnode['commcell']["commcellPassword"])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"]
                                  , self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.dashboard = Dashboard(self.webconsole)
            self.monitoringform = ManageCommcells(self.webconsole)
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_companies()
            self.companies = RegisteredCompanies(self.webconsole)
            self.company_name = REPORTS_CONFIG.REPORTS.METRICS.COMPANY_NAME
            global_id = self.utils.get_account_global_id(self.company_name)
            self.db_commcells = self.utils.get_company_commcells(global_id,
                                                                 self.tcinputs['linked_server'])

        except Exception as expt:
            raise CVTestCaseInitFailure(expt) from expt

    @test_step
    def verify_commcell_count(self):
        """Match the CommCell count from dashboard and CommCell listing page"""
        self.companies.access_company(self.company_name)
        self.navigator.goto_commcells_in_group()
        commcell_count = len(self.monitoringform.get_column_values('CommCell Name'))
        commcell_count_panel = self.navigator.get_commcell_count()
        if commcell_count == commcell_count_panel and commcell_count == len(self.db_commcells):
            self.log.info("CommCell count of the company_name is verified ")
        else:
            raise CVTestStepFailure("Expected CommCell count is [%s] but received count[%s]"
                                    % (self.db_commcells, commcell_count_panel))

    @test_step
    def verify_commcell_list(self):
        """Verify commcells in company dashboard and commcells in LG Database are matching"""
        company_commcells = self.monitoringform.get_column_values('CommCell ID')
        dashboard_commcell = {item.lower() for item in company_commcells}
        db_commcell = {item.lower() for item in self.db_commcells}
        if dashboard_commcell == db_commcell:
            self.log.info("CommCells list from company_name is verified")
        else:
            raise CVTestStepFailure("Expected CommCells from the Company is [%s]"
                                    "but we got [%s]" % (dashboard_commcell, db_commcell))

    def run(self):
        try:
            self.init_tc()
            self.verify_commcell_count()
            self.verify_commcell_list()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
