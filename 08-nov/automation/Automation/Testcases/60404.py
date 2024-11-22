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
                "60404":
                        {
                            "Client": None,
                            "Subclient": None
                        }
            }


"""
from datetime import datetime, date, timedelta, time
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.Reports.sla import WebSla
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.WebConsole.Reports.Custom.inputs import DateRangeController


_CONFIG = get_config()


class TestCase(CVTestCase):
    """test case class"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Command center SLA report - time range input option validation"
        self.browser: Browser = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.private_metrics = None
        self.webconsole: WebConsole = None
        self.utils: TestCaseUtils = None
        self.tcinputs = {
            "Client": None,
            "Subclient": None
        }
        self.custom_report_utils = CustomReportUtils(self)
        self.report = None
        self.manage_report = None
        self.admin_console = None
        self.client = None
        self.subclient = None
        self.sla = None
        self.viewer = None

    def init_tc(self):
        """initialize test case"""
        try:
            self.utils = TestCaseUtils(self)
            self.client = self.tcinputs["Client"]
            self.subclient = self.tcinputs["Subclient"]
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
            self.sla = WebSla(self.webconsole)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e


    @test_step
    def validate_adminconsole_sla_clients(self, table_name, client_name, subclient_name):
        """
        validate the clients in Admin console SLA

        Args:
            table_name:  missed or excluded SLA table
            Client_name: name of the client
            subclient_name: name of the subclient
        """

        table = viewer.DataTable(table_name)
        self.viewer.associate_component(table)
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

        self.log.info(f"Client " + client_name + " is present in the table " + table_name)

    @test_step
    def verify_adminconsole_met_sla_table_entries(self):
        """
        validate the clients are with in SLA in Admin console met SLA table
        """
        self.sla.access_met_sla()
        dt = date.today() - timedelta(2)
        endTime = time(8, 00, 00)
        time_stamp = datetime.combine(dt, endTime)
        self.log.info(f"Verifying rows in Met SLA table have backup time less than "
                      + time_stamp.strftime("%b %d, %Y, %I:%M:%S %p"))
        table = viewer.DataTable("Protected servers")
        self.viewer.associate_component(table)
        sla_table_data = table.get_table_data()
        backup_time_list = sla_table_data['Last backup time']
        for backup_time in backup_time_list:
            backup_time_value = datetime.strptime(backup_time, '%b %d, %Y, %I:%M:%S %p')
            if backup_time_value < time_stamp:
                raise CVTestStepFailure(
                    "Mismatched SLA, [{0}] is less than expected time [{1}]" % (backup_time_value,
                                                                                time_stamp)
                )

    @test_step
    def validate_adminconsole_met_sla(self):
        """
         validate the subclients in met SLA
        """
        self.sla.access_met_sla()
        self.log.info(f"Verifying {self.client} is in Met SLA")
        title = 'Protected servers'
        self.validate_adminconsole_sla_clients(title, self.client, self.subclient)
        self.admin_console.select_breadcrumb_link_using_text("SLA")

    @test_step
    def validate_adminconsole_missed_sla(self):
        """
         validate the subclients in missed SLA
        """
        self.sla.access_missed_sla()
        self.sla.access_no_job_clients()
        self.log.info(f"Verifying {self.client} is in No Job list")
        title = 'No Finished Job within SLA Period'
        self.validate_adminconsole_sla_clients(title, self.client,
                                               self.subclient)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.admin_console.select_breadcrumb_link_using_text("SLA")

    @test_step
    def change_time_range(self):
        """
         Change time range to last 2 days
        """
        input_ctrl = DateRangeController("Time frame : Default")
        self.viewer.associate_input(input_ctrl)
        input_ctrl.set_relative_daterange("Last 2 Days")

    def run(self):
        try:
            self.init_tc()
            self.init_adminconsole()
            self.validate_adminconsole_met_sla()
            self.change_time_range()
            self.validate_adminconsole_missed_sla()
            self.verify_adminconsole_met_sla_table_entries()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
