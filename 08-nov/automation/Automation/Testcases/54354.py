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
    validate_web_missed_sla()                             --  Validate missed VMs in web SLA
    validate_adminconsole_missed_sla()                    --  Validate missed VMs in amdinconsole SLA
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "54354":
                        {
                            "FailedClient" : "Client_Name",
                            "FailedSubclient" : "Subclient_Name",
                            "NoJobClient" : "Client_Name",
                            "NoJobSubclient" : "Subclient_Name",
                            "NoScheduleClient" : "Client_Name",
                            "NoScheduleSubclient" : "Subclient_Name",
                            "SnapClient" : "Client_Name",
                            "SnapSubclient" : "Subclient_Name"
                  }
                        }
            }


"""
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.sla import WebSla
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
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
        self.name = "Validation of missed SLA drill down in web and admin console SLA"
        self.browser: Browser = None
        self.webconsole_adapter: WebConsoleAdapter = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.SLAReportMissedList = []
        self.SLAReportMetList = []
        self.tcinputs = {
            "FailedClient": None,
            "FailedSubclient": None,
            "NoJobClient": None,
            "NoJobSubclient": None,
            "NoScheduleClient": None,
            "NoScheduleSubclient": None,
            "SnapClient": None,
            "SnapSubclient": None
        }
        self.utils: TestCaseUtils = None
        self.helper = None
        self.FailedClient = None
        self.FailedSubclient = None
        self.NoJobClient = None
        self.NoJobSubclient = None
        self.NoScheduleClient = None
        self.NoScheduleSubclient = None
        self.SnapClient = None
        self.SnapSubclient = None
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
            self.FailedClient = self.tcinputs["FailedClient"]
            self.FailedSubclient = self.tcinputs["FailedSubclient"]
            self.NoJobClient = self.tcinputs["NoJobClient"]
            self.NoJobSubclient = self.tcinputs["NoJobSubclient"]
            self.NoScheduleClient = self.tcinputs["NoScheduleClient"]
            self.NoScheduleSubclient = self.tcinputs["NoScheduleSubclient"]
            self.SnapClient = self.tcinputs["SnapClient"]
            self.SnapSubclient = self.tcinputs["SnapSubclient"]
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def init_adminconsole(self):
        """ validate adminconsole SLA report"""
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
        self.webconsole_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        self.sla = WebSla(self.webconsole_adapter)
        self.custom_report_utils.webconsole = self.webconsole_adapter

    @test_step
    def validate_adminconsole_missed_sla(self):
        """
         validate the subclients that are not supposed to be in missed SLA
        """
        self.sla.access_missed_sla()
        self.sla.access_failed_clients()
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for Failed clients")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.FailedClient, self.FailedSubclient))
        title = 'Failed servers'
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for No Job category clients")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.NoJobClient, self.NoJobSubclient))
        title = 'No Finished Job within SLA Period'
        self.sla.access_no_job_clients()
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for No Schedule Clients")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.NoScheduleClient, self.NoScheduleSubclient))
        title = 'No Schedule'
        self.sla.access_no_schedule_clients()
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for Snap with No Backup Copy clients")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.SnapClient, self.SnapSubclient))
        title = 'Snap Job with No Backup Copy'
        self.sla.access_snap_with_nobackupcopy_clients()
        self.validate_adminconsole_missed_sla_subclients(title)

    @test_step
    def validate_adminconsole_missed_sla_subclients(self, table_name):
        """
        validate the subclients that are not supposed to be in missed Admin console SLA

        Args:
            table_name:  missed SLA table
            report_type: web or metrics report
        """
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable(table_name)
        report_viewer.associate_component(table)
        sla_table_data = table.get_table_data()
        for sla_object in self.SLAReportMissedList:
            table.set_filter('Server', sla_object.client_name)
            table.set_filter('Subclient', sla_object.subclient)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if not rowcount:
                raise CVTestStepFailure(
                    "Mismatched SLA, expected entry VM [%s] subclient [%s] not found in table [%s]" % (
                        sla_object.client_name,
                        sla_object.subclient,
                        table_name
                    )
                )
            self.log.info("Client [{0}] Subclient [{1}] are present in the table [{2}]".format(
                        sla_object.client_name, sla_object.subclient, table_name))

    def run(self):
        try:
            self.init_tc()
            self.init_adminconsole()
            self.validate_adminconsole_missed_sla()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
