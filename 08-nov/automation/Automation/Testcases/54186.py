# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.health_tiles import SLA
from Web.AdminConsole.Reports.sla import Sla
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import RDashboard
from Web.AdminConsole.Reports.manage_reports import ManageReport

_CONFIG = get_config()


class SLAReportDataExpected:
    """SLA report data row column values"""
    client_name = ''
    subclient = ''

    def __init__(self, client_name, subclient):
        self.client_name = client_name
        self.subclient = subclient


class TestCase(CVTestCase):
    """test case class"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Validate SLA counts for Web, Metrics and Custom Report SLA"
        self.browser: Browser = None
        self.dashboard = None
        self.private_metrics = None
        self.utils: TestCaseUtils = None
        self.metrics_sla = None
        self.admin_console_sla = None
        self.dashboard_sla = None
        self.custom_report_utils = CustomReportUtils(self)
        self.report = None
        self.manage_report = None
        self.admin_console = None
        self.sla = None
        self.SLAReportMissedList = []

    def init_tc(self):
        """initialize test case"""
        try:
            self.utils = TestCaseUtils(self)

            self.init_adminconsole()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def init_adminconsole(self):
        """initialize adminconsole objects"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.sla = Sla(self.admin_console)
            self.navigator.navigate_to_dashboard()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def get_metrics_sla(self):
        """" validate metrics SLA report"""
        self.navigator.navigate_to_metrics()
        self.manage_report.access_commcell_health(self.commcell.commserv_name)
        sla_tile = SLA(self.admin_console)
        self.metrics_sla = sla_tile.get_sla_percent()
        self.log.info(f"Metrics SLA value [{self.metrics_sla}]")

    @test_step
    def get_adminconsole_sla(self):
        """ validate adminconsole SLA report"""
        rdashboard = RDashboard(self.admin_console)
        self.dashboard_sla = float(rdashboard.get_dashboard_sla())
        self.log.info("Adminconsole Dashboard SLA value is [{self.dashboard_sla}]")
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("SLA")
        self.admin_console_sla = float(self.sla.get_sla_percentage())
        self.log.info(f"Adminconsole SLA value is [{self.admin_console_sla}]")

    @test_step
    def validate_sla(self):
        """" validate all three SLA values"""
        self.log.info(f" Metrics SLA [{self.metrics_sla}],"
                      f" Admin console SLA [{self.admin_console_sla}],"
                      f" Admin Dashboard SLA [{self.dashboard_sla}]")
        if self.metrics_sla == self.admin_console_sla == self.dashboard_sla:
            self.log.info("Metrics SLA, Admin Dashboard SLA,  Admin console SLA are matching")
        else:
            raise Exception(
                f"Mismatched SLA, All three values are not same. "
                " Metrics SLA [{self.metrics_sla}], "
                "Admin console SLA [{self.admin_console_sla}], "
                "Admin Dashboard SLA [{self.dashboard_sla}]"
            )

    def run(self):
        try:
            self.init_tc()
            self.get_adminconsole_sla()
            self.get_metrics_sla()
            self.validate_sla()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
