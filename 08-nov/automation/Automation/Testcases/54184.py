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
    validate_metrics_sla()                                --  Validate missed VMs in metrics SLA
    validate_adminconsole_missed_sla()                    --  Validate missed VMs in amdinconsole SLA
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "54184":
                        {
                            "FailedVMClient" : "VM_Name",
                            "FailedVMSubclient" : "VSASubclient_Name",
                            "NoJobVMClient" : "VM_Name",
                            "NoJobVMSubclient" : "VSASubclient_Name",
                            "NoScheduleVMClient" : "VM_Name",
                            "NoScheduleVMSubclient" : "SuccessfulVM",
                            "SnapVMClient" : "VM_Name",
                            "SnapVMSubclient" : "VSASubclient_Name",
                            "DisabledVMClient" : "VM_Name",
                            "ExcludedVMClient" : "VM_Name",
                            "DisabledVMSubclient" : "VSASubclient_Name",
                            "ExcludedVMSubclient" : "VSASubclient_Name"
                        }
            }


"""
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.sla import Sla
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.commcells import Commcell
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.health_tiles import SLA

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
        self.name = "SLA Validation for VM Clients"
        self.browser: Browser = None
        self.navigator = None
        self.metrics_commcell: Commcell = None
        self.SLAReportMissedList = []
        self.SLAReportExcludedList = []
        self.sla_tile = None
        self.tcinputs = {
            "FailedVMClient": None,
            "FailedVMSubclient": None,
            "NoJobVMClient": None,
            "NoJobVMSubclient": None,
            "NoScheduleVMClient": None,
            "NoScheduleVMSubclient": None,
            "SnapVMClient": None,
            "SnapVMSubclient": None,
            "DisabledVMClient": None,
            "ExcludedVMClient": None,
            "DisabledVMSubclient": None,
            "ExcludedVMSubclient": None
        }
        self.utils: TestCaseUtils = None
        self.helper = None
        self.FailedVMClient = None
        self.FailedVMSubclient = None
        self.NoJobVMClient = None
        self.NoJobVMSubclient = None
        self.NoScheduleVMClient = None
        self.NoScheduleVMSubclient = None
        self.ExcludedVMClient = None
        self.SnapVMClient = None
        self.SnapVMSubclient = None
        self.DisabledVMClient = None
        self.ExcludedVMClient = None
        self.DisabledVMSubclient = None
        self.ExcludedVMSubclient = None
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
            self.FailedVMClient = self.tcinputs["FailedVMClient"]
            self.FailedVMSubclient = self.tcinputs["FailedVMSubclient"]
            self.NoJobVMClient = self.tcinputs["NoJobVMClient"]
            self.NoJobVMSubclient = self.tcinputs["NoJobVMSubclient"]
            self.NoScheduleVMClient = self.tcinputs["NoScheduleVMClient"]
            self.NoScheduleVMSubclient = self.tcinputs["NoScheduleVMSubclient"]
            self.SnapVMClient = self.tcinputs["SnapVMClient"]
            self.SnapVMSubclient = self.tcinputs["SnapVMSubclient"]
            self.DisabledVMClient = self.tcinputs["DisabledVMClient"]
            self.ExcludedVMClient = self.tcinputs["ExcludedVMClient"]
            self.DisabledVMSubclient = self.tcinputs["DisabledVMSubclient"]
            self.ExcludedVMSubclient = self.tcinputs["ExcludedVMSubclient"]
            self.private_metrics = PrivateMetrics(self.commcell)
            self.private_metrics.enable_all_services()
            self.metrics_commcell = Commcell()

            self.SLAReportExcludedList.append(
                SLAReportDataExpected(self.DisabledVMClient, "")
            )
            self.SLAReportExcludedList.append(
                SLAReportDataExpected(self.ExcludedVMClient, "")
            )
            self.SLAReportExcludedList.append(
                SLAReportDataExpected(self.DisabledVMSubclient, "")
            )
            self.SLAReportExcludedList.append(
                SLAReportDataExpected(self.ExcludedVMSubclient, "")
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
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("SLA")
        self.report = Report(self.admin_console)
        self.sla = Sla(self.admin_console)

    @test_step
    def validate_metrics_sla(self):
        """" validate metrics SLA report"""
        self.utils.private_metrics_upload()
        self.navigator.navigate_to_metrics()
        self.manage_report.access_commcell_health(self.commcell.commserv_name)
        self.sla_tile = SLA(self.admin_console)
        self.sla_tile.access_view_details()
        self.SLAReportMissedList.clear()
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.FailedVMClient, self.FailedVMSubclient))
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.NoJobVMClient, self.NoJobVMSubclient))
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.NoScheduleVMClient, self.NoScheduleVMSubclient))
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.SnapVMClient, self.SnapVMSubclient))
        title = "Details for Clients Missed SLA"
        self.validate_adminconsole_missed_sla_subclients(title, True)

    @test_step
    def validate_adminconsole_missed_sla(self):
        """
         validate the subclients that are not supposed to be in missed SLA
        """
        self.sla.access_missed_sla()
        self.sla.access_failed_clients()
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for Failed VMs")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.FailedVMClient, self.FailedVMSubclient))
        title = 'Failed servers'
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for No Job category VMs")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.NoJobVMClient, self.NoJobVMSubclient))
        title = 'No Finished Job within SLA Period'
        self.sla.access_no_job_clients()
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for No Schedule VMs")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.NoScheduleVMClient, self.NoScheduleVMSubclient))
        title = 'No Schedule'
        self.sla.access_no_schedule_clients()
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.SLAReportMissedList.clear()
        self.log.info("Verifying for Snap With No Backup Copy VMs")
        self.SLAReportMissedList.append(
            SLAReportDataExpected(self.SnapVMClient, self.SnapVMSubclient))
        title = 'Snap Job with No Backup Copy'
        self.sla.access_snap_with_nobackupcopy_clients()
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text("Missed SLA")
        self.validate_adminconsole_excluded_clients()

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

    @test_step
    def validate_adminconsole_excluded_clients(self):
        """
        validate the given client is not in the admin console unprotected client list
        """
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Unprotected servers")
        report_viewer.associate_component(table)
        sla_table_data = table.get_table_data()
        server_list = sla_table_data['Server']
        rowcount = len(server_list)
        if rowcount == 0:
            return
        for sla_object in self.SLAReportExcludedList:
            excluded_entry_found = False
            if sla_object.client_name in server_list:
                excluded_entry_found = True
            if excluded_entry_found:
                raise CVTestStepFailure(
                    "Mismatched SLA, excluded client [%s] found in Unprotected servers table" % (
                        sla_object.client_name
                    )
                )

    def run(self):
        try:
            self.init_tc()
            self.init_adminconsole()
            self.validate_adminconsole_missed_sla()
            self.validate_metrics_sla()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
