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
    __init__()                                         --  initialize TestCase class
    init_tc()                                          --  Initialize pre-requisites
    update_commandline_sla_condition                   --  enable exclude commandline subclient option
    validate_metrics_sla()                             --  Validate missed VMs in metrics SLA
    validate_adminconsole_missed_sla()                 --  Validate missed VMs in amdinconsole SLA
    run()                                              --  run function of this test case
Input Example:

    "testCases":
            {
                "54101":
                        {
                            "DBClientName" : "DBClientName"
                        }
            }


"""
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.sla import WebSla
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.Reports.Custom import viewer
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.metricsreport import PrivateMetrics

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
        self.name = "SLA report validation for Exclude Commandline subclients option"
        self.browser: Browser = None
        self.webconsole_adapter: WebConsoleAdapter = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.SLAReportDBClientList = []
        self.tcinputs = {
            "DBClientName": None
        }
        self.utils: TestCaseUtils = None
        self.helper = None
        self.DBClientName = None
        self.manage_report = None
        self.admin_console = None
        self.report = None
        self.custom_report_utils = CustomReportUtils(self)
        self.sla = None
        self.private_metrics = None

    def init_tc(self):
        """initialize test case"""
        try:
            self.utils = TestCaseUtils(self,
                                       username=self.inputJSONnode["commcell"]["commcellUsername"],
                                       password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.helper = None
            self.DBClientName = self.tcinputs["DBClientName"]
            self.private_metrics = PrivateMetrics(self.commcell)
            self.private_metrics.enable_all_services()
            self.SLAReportDBClientList.append(
                SLAReportDataExpected(self.DBClientName, "")
            )
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
        self.report = Report(self.admin_console)
        self.webconsole_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        self.webconsole_navigator = Navigator(self.webconsole_adapter)
        self.dashboard = Dashboard(self.webconsole_adapter)
        self.sla = WebSla(self.webconsole_adapter)
        self.custom_report_utils.webconsole = self.webconsole_adapter

    @test_step
    def validate_metrics_db_clients(self):
        """
        validate the given client is not in the unprotected client list
        """
        table = MetricsTable(self.webconsole_adapter, "Details for Clients Missed SLA")
        rowcount = table.get_rows_count()
        if rowcount == 0:
            if self.SLAReportDBClientList:
                raise CVTestStepFailure(
                    "Mismatched SLA, table is empty but expected list is non empty")
        sla_table_data = table.get_data_from_column("Client")
        subclient_table_date = table.get_data_from_column("Subclient")
        for sla_object in self.SLAReportDBClientList:
            entry_found = False
            if sla_object.client_name in sla_table_data and \
                    any("command line" in s for s in subclient_table_date):
                entry_found = True
            if entry_found:
                raise CVTestStepFailure(
                    "Mismatched SLA, excluded DB Client [%s] not found in Missed SLA table]" % (
                        sla_object.client_name
                    )
                )

    @test_step
    def validate_metrics_sla(self):
        """" validate metrics SLA report"""
        self.utils.private_metrics_upload()
        self.navigator.navigate_to_webconsole_monitoring()
        self.webconsole_navigator.goto_reports()
        self.webconsole_navigator.goto_commcell_dashboard(self.commcell.commserv_name)
        self.dashboard.view_detailed_report("SLA")
        self.validate_metrics_db_clients()

    @test_step
    def validate_adminconsole_missed_sla(self, client_exists):
        """
         validate the subclients that are not supposed to be in missed SLA
        """
        self.sla.access_missed_sla()
        self.sla.access_no_job_clients()
        self.validate_adminconsole_db_clients(client_exists)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.admin_console.select_breadcrumb_link_using_text("SLA")

    @test_step
    def validate_db_clients(self, client_exists):
        """
        validate the given client in unprotected client list
        """
        table = MetricsTable(self.webconsole_adapter, "Clients with no jobs")
        rowcount = table.get_rows_count()
        if rowcount == 0:
            return
        sla_table_data = table.get_data_from_column("Client")
        subclient_table_date = table.get_data_from_column("Subclient")
        for sla_object in self.SLAReportDBClientList:
            entry_found = False
            if sla_object.client_name in sla_table_data and \
                    any("command line" in s for s in subclient_table_date):
                entry_found = True
            if  entry_found and not client_exists:
                raise CVTestStepFailure(
                    "Mismatched SLA,  DB client [%s] with command line subclient found in "
                    "Unprotected Clients table" % (
                        sla_object.client_name,
                    )
                )

    @test_step
    def validate_adminconsole_db_clients(self, client_exists):
        """
        validate the given client not in the admin console unprotected client list
        """
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("No Finished Job within SLA Period")
        report_viewer.associate_component(table)
        sla_table_data = table.get_table_data()
        server_list = sla_table_data['Server']
        subclient_list = sla_table_data['Subclient']
        rowcount = len(server_list)
        if rowcount == 0:
            return
        for sla_object in self.SLAReportDBClientList:
            entry_found = False
            if sla_object.client_name in server_list and any("command line" in s for s in subclient_list):
                entry_found = True
            if  entry_found and not client_exists:
                raise CVTestStepFailure(
                    "Mismatched SLA, DB client [%s] found in Unprotected servers table" % (
                        sla_object.client_name
                    )
                )


    def update_commandline_sla_condition(self, val):
        """
            update command line sla condition
        Args:
            val: 0 or 1
        Returns:

        """

        """ Get last one shot query id , delete the one shot include file,
        generate new one shot id"""
        query = "IF NOT EXISTS (SELECT 1 FROM APP_ComponentProp WITH (NOLOCK) " \
                "               WHERE componentType = 1 AND componentId = 2 " \
                "               AND propertyTypeId = 3308 AND modified = 0) " \
                "INSERT INTO APP_ComponentProp VALUES (1, 2, 3308, 8, " + str(int(val)) + \
                ", 0, '', 0, 0) " \
                "ELSE  UPDATE APP_ComponentProp SET longVal = " + str(int(val)) + " " \
                "WHERE componentType = 1 AND componentId = 2 AND propertyTypeId = 3308"  \
                " AND modified = 0"

        self.utils.cs_db.execute(query)


    def run(self):
        try:
            self.init_tc()
            self.init_adminconsole()
            self.log.info("Settting Command line exclusion condition to False")
            self.update_commandline_sla_condition(False)
            self.log.info("Verifying that command line subclient exists in the missed sla section")
            self.navigator.navigate_to_reports()
            self.manage_report.access_report("SLA")
            self.validate_adminconsole_missed_sla(True)
            self.log.info("Settting Command line exclusion condition to True")
            self.utils.reset_cre()
            self.update_commandline_sla_condition(True)
            self.log.info("Verifying that command line subclient doesn't exist in the missed sla section")
            self.validate_adminconsole_missed_sla(False)
            self.validate_metrics_sla()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
