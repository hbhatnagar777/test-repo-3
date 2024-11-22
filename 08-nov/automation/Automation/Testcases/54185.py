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
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    validate_web__sla()                                   --  Validate laptop clients in web SLA
    validate_adminconsole_sla()                    --  Validate laptop clients in amdinconsole SLA
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "54185":
                        {
                            "FailedLaptopClient" : "Laptop Client_Name",
                            "SuccessLaptopClient" : "Laptop Client_Name",
                            "ExcludedLaptopClient" : "Laptop Client_Name"
                            }
                        }
            }


"""
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.sla import Sla
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class ColumnNames:
    """
    Column names present in sla page
    """
    CLIENT = "Client"
    Subclient = "Subclient"

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
        self.name = "SLA Validation for laptop clients"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.SLAReportClientList = []
        self.SLAExcludedList = []
        self.tcinputs = {
            "FailedLaptopClient": None,
            "SuccessLaptopClient": None,
            "ExcludedLaptopClient": None
        }
        self.utils: TestCaseUtils = None
        self.helper = None
        self.FailedLaptopClient = None
        self.SuccessLaptopClient = None
        self.ExcludedLaptopClient = None
        self.manage_report = None
        self.admin_console = None
        self.report = None
        self.custom_report_utils = CustomReportUtils(self)
        self.sla = None

    def init_tc(self):
        """initialize test case"""
        try:
            self.utils = TestCaseUtils(self,
                                       username=self.inputJSONnode["commcell"]["commcellUsername"],
                                       password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.helper = None
            self.FailedLaptopClient = self.tcinputs["FailedLaptopClient"]
            self.SuccessLaptopClient = self.tcinputs["SuccessLaptopClient"]
            self.ExcludedLaptopClient = self.tcinputs["ExcludedLaptopClient"]
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e


    @test_step
    def init_adminconsole(self):
        """ validate adminconsole SLA report"""
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode["commcell"]["commcellUsername"],
            self.inputJSONnode["commcell"]["commcellPassword"]
        )
        self.navigator = self.admin_console.navigator
        self.sla = Sla(self.admin_console)
        self.manage_report = ManageReport(self.admin_console)
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("SLA")
        self.report = Report(self.admin_console)

    @test_step
    def validate_adminconsole_sla(self):
        """
         validate the clienta that are in admin console SLA
        """
        self.sla.access_missed_sla()
        self.SLAReportClientList.clear()
        self.log.info("Verifying for Failed laptop clients")
        self.SLAReportClientList.append(
            SLAReportDataExpected(self.FailedLaptopClient, ""))
        title = 'Unprotected servers'
        self.validate_adminconsole_sla_clients(title)
        self.admin_console.select_breadcrumb_link_using_text("SLA")
        self.log.info("Verifying successful laptop clients")
        self.SLAReportClientList.clear()
        self.SLAReportClientList.append(
            SLAReportDataExpected(self.SuccessLaptopClient, ""))
        self.sla.access_met_sla()
        title = 'Protected servers'
        self.validate_adminconsole_sla_clients(title)

    @test_step
    def validate_adminconsole_sla_clients(self, table_name):
        """
        validate the clients in Admin console SLA

        Args:
            table_name:  missed SLA table
            report_type: web or metrics report
        """

        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable(table_name)
        report_viewer.associate_component(table)
        sla_table_data = table.get_table_data()

        for sla_object in self.SLAReportClientList:
            table.set_filter('Server', sla_object.client_name)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if not rowcount:
                raise CVTestStepFailure(
                    "Mismatched SLA, expected entry client [%s]  not found in table [%s]" % (
                        sla_object.client_name,
                        table_name
                    )
                )
            self.log.info("Client [{0}] is present in the table [{1}]".format(
                            sla_object.client_name, table_name))

        for sla_object in self.SLAExcludedList:
            table.set_filter('Server', sla_object.client_name)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if  rowcount:
                raise CVTestStepFailure(
                    "Mismatched SLA, Excluded entry client [%s] found in table [%s]" % (
                        sla_object.client_name,
                        table_name
                    )
                )

    def run(self):
        try:
            self.init_tc()
            self.SLAExcludedList.append(
                SLAReportDataExpected(self.ExcludedLaptopClient, ""))
            self.init_adminconsole()
            self.validate_adminconsole_sla()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
