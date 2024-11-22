# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    init_tc()                              --  Initial configuration for the test case
    validate_adminconsole_met_sla()        --  Verify Met SLA table has plan level SLA value
    validate_adminconsole_excluded_sla()   -- Verify plan level sla excluded subclients 
    run()                                  --  run function of this test case

Input Example:

    "testCases":
            {
                "59635":
                        {
                            "Client1": None,
                            "Subclient1": None,
                            "Plan1": None,
                            "Plan1SLADays": None,
                            "Excluded_Client2": None,
                            "Excluded_Subclient2": None,
                            "Excluded_Plan2": None
                        }
            }


"""
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.Reports.sla import Sla
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport

_CONFIG = get_config()


class TestCase(CVTestCase):
    """test case class"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Validate SLA counts for Web, Metrics and Custom Report SLA"
        self.browser: Browser = None
        self.navigator = None
        self.dashboard = None
        self.private_metrics = None
        self.utils: TestCaseUtils = None
        self.tcinputs = {
            "Client1": None,
            "Plan1": None,
            "Subclient1": None,
            "Plan1SLADays": None,
            "Excluded_Client2": None,
            "Excluded_Subclient2": None,
            "Excluded_Plan2": None

        }
        self.custom_report_utils = CustomReportUtils(self)
        self.report = None
        self.manage_report = None
        self.admin_console = None
        self.client1 = None
        self.plan1 = None
        self.sladays = None
        self.excluded_client = None
        self.excluded_subclient2 = None
        self.excluded_plan2 = None
        self.sla = None

    def init_tc(self):
        """initialize test case"""
        try:
            self.utils = TestCaseUtils(self)
            self.client1 = self.tcinputs["Client1"]
            self.plan1 = self.tcinputs["Plan1"]
            self.sladays = self.tcinputs["Plan1SLADays"]
            self.excluded_client = self.tcinputs["Excluded_Client2"]
            self.excluded_subclient2 = self.tcinputs["Excluded_Subclient2"]
            self.subclient1 = self.tcinputs["Subclient1"]
            self.excluded_plan2 = self.tcinputs["Excluded_Plan2"]
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
            self.navigator.navigate_to_reports()
            self.manage_report.access_report("SLA")
            self.report = Report(self.admin_console)
            self.webconsole = WebConsoleAdapter(self.admin_console, self.browser)
            self.sla = Sla(self.admin_console)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def validate_adminconsole_sla_clients(self, table_name, client_name, subclient_name, sla_days,
                                          plan, sla_days_level):
        """
        validate the clients in Admin console SLA

        Args:
            table_name:  missed or excluded SLA table
            Client_name: name of the client
            SLA_days: sla days
            Plan: Plan
            Sla_days_level: SLA days level
        """

        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable(table_name)
        report_viewer.associate_component(table)
        table.set_filter('Server', client_name)
        if subclient_name:
            table.set_filter('Subclient', subclient_name)
        sla_table_data = table.get_table_data()

        rowcount = len(sla_table_data['Server'])
        if not rowcount:
            raise CVTestStepFailure(
                "Mismatched SLA, Client [%s] and subclient %s is not found" %(client_name,
                                                                              subclient_name)
            )

        if sla_days:
            if sla_days != sla_table_data['SLA days'][0]:
                raise CVTestStepFailure(
                    "SLA days value [%s] is not matching for Client [%s] and subclient [%s] " %(
                        sla_days, client_name, subclient_name)
                )

        if plan:
            if plan != sla_table_data['Plan'][0]:
                raise CVTestStepFailure(
                    "Plan %s is not matching for Client [%s] and subclient %s " %(plan, client_name,
                                                                                  subclient_name)
                )

        if sla_days_level:
            if sla_days_level != sla_table_data['SLA days level'][0]:
                raise CVTestStepFailure(
                    "SLA days level [%s] is not matching for Client [%s] and subclient [%s] " %(
                        sla_days_level, client_name, subclient_name)
                )
        self.log.info("Client [{0}] is present in the table [{1}]".format(client_name, table_name))

    @test_step
    def validate_adminconsole_met_sla(self):
        """
         validate the subclients in met SLA
        """
        self.sla.access_met_sla()
        self.log.info(f"Verifying {self.client1} is in Met SLA")
        title = 'Protected servers'
        self.validate_adminconsole_sla_clients(title, self.client1, self.subclient1, self.sladays,
                                               None, 'Subclient Plan')
        self.admin_console.select_breadcrumb_link_using_text("SLA")

    @test_step
    def validate_adminconsole_excluded_sla(self):
        """
         validate the subclients in excluded SLA
        """
        self.sla.access_excluded_sla()
        self.log.info(f"Verifying {self.excluded_client} is in excluded list")
        title = 'Excluded Entities'
        self.validate_adminconsole_sla_clients(title, self.excluded_client,
                                               self.excluded_subclient2, None,
                                               self.excluded_plan2, None)


    def run(self):
        try:
            self.init_tc()
            self.init_adminconsole()
            self.validate_adminconsole_met_sla()
            self.validate_adminconsole_excluded_sla()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
