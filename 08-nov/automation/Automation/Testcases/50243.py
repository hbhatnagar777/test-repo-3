# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from time import sleep
from datetime import datetime
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import idautils
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.sla import WebSla
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from FileSystem.FSUtils.fshelper import FSHelper
from cvpysdk.metricsreport import PrivateMetrics
from cvpysdk.policies.storage_policies import StoragePolicy
from cvpysdk.subclients.fssubclient import FileSystemSubclient

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
        self.name = "SLA validation for snap jobs"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.admin_console: AdminConsole = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.SLAReportMissedList = []
        self.SLAReportMetList = []
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "NASClient": None,
            "NASSubclient": None,
            "NASBackupCopySubclient": None
        }
        self.private_metrics = None
        self.backupset = None
        self.utils: TestCaseUtils = None
        self.schedule_helper = None
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.nas_backup_copy_subclient = None
        self.nas_client = None
        self.nas_subclient = None
        self.client_machine = None
        self.client_name = None
        self.vsa_client = None
        self.vsa_subclient = None

    def init_tc(self):
        """initialize test case"""
        try:
            self.utils = TestCaseUtils(self,
                                       username=self.inputJSONnode["commcell"]["commcellUsername"],
                                       password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.helper = None
            FSHelper.populate_tc_inputs(self)
            self.nas_client = self.tcinputs["NASClient"]
            self.nas_subclient = self.tcinputs["NASSubclient"]
            self.nas_backup_copy_subclient = self.tcinputs["NASBackupCopySubclient"]
            self.vsa_client = self.tcinputs['VSAClient']
            self.vsa_subclient = self.tcinputs['VSASubclient']
            """Initializes Private metrics object required for this test case"""
            self.private_metrics = PrivateMetrics(self.commcell)
            self.private_metrics.enable_all_services()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def init_webconsole(self):
        """initialzie webconsole objects"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                  self.inputJSONnode["commcell"]["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.dashboard = Dashboard(self.webconsole)
            self.webconsole.goto_reports()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def init_admin_console(self):
        """initialzie webconsole objects"""
        try:
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
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def create_backupset(self):
        """"create backupset"""
        self.backupset = "backupset_" + self.id
        self.helper.create_backupset(self.backupset, True)
        subclient = FileSystemSubclient(self.backupset, 'default')
        subclient.exclude_from_sla()

    def create_valid_data(self):
        """create a valid path to backup"""
        self.client_machine.generate_test_data(
            self.test_path,
        )

    def create_sc(self, subclient_name):
        """
        create new subclient with block level backup

        Args:
            subclient_name: subclient name

        Returns: returns newly created subclient object

        """
        storage_policy = self.storage_policy
        subclient_content = []
        self.create_valid_data()
        subclient_content.append(self.test_path)
        self.helper.create_subclient(name=subclient_name,
                                     storage_policy=storage_policy,
                                     content=subclient_content,
                                     delete=True)
        # Update Subclient with blocklevel value if not set
        self.log.info("Enabling BlockLevel Option")
        self.helper.update_subclient(content=subclient_content, block_level_backup=1)

    def run_backup(self):
        """ run backup """
        try:
            self.helper.run_backup()
        except Exception:
            return

    @test_step
    def validate_met_sla_subclients(self, table_name):
        """
        validate the subclients that met sla
        Args:
            table_name: SLA protected clients table

        """

        table = MetricsTable(self.webconsole, table_name)
        rowcount = table.get_rows_count()
        if not rowcount:
            if self.SLAReportMetList:
                raise Exception(
                    "Mismatched SLA, table is empty but expected list is non empty")
        sla_table_data = table.get_data()
        for sla_object in self.SLAReportMetList:
            expected_entry_found = False
            for row_idx in range(0, int(rowcount)):
                rowobject = sla_table_data[row_idx]
                if rowobject[1] == sla_object.client_name and rowobject[4] == sla_object.subclient:
                    expected_entry_found = True
                    break
            if not expected_entry_found:
                raise Exception("Mismatched SLA, valid subclient [%s] is not found in the table "
                                "[%s]" % (sla_object.subclient, table_name))

    @test_step
    def validate_missed_sla_subclients(self, table_name, report_type):
        """
        validate the subclients that are not supposed to be in missed SLA

        Args:
            table_name:  missed SLA table
            report_type: web or metrics report
        """
        if report_type == 'web':
            client_index = 1
            subclient_index =3
        elif report_type == 'metrics':
            client_index = 0
            subclient_index = 4

        table = MetricsTable(self.webconsole, table_name)
        rowcount = table.get_rows_count()
        if not rowcount:
            if self.SLAReportMissedList:
                raise Exception(
                    "Mismatched SLA, table is empty but expected list is non empty")
        sla_table_data = table.get_data()
        for sla_object in self.SLAReportMissedList:
            expected_entry_found = False
            for row_idx in range(0, int(rowcount)):
                rowobject = sla_table_data[row_idx]
                if rowobject[client_index] == sla_object.client_name and \
                                rowobject[subclient_index] == sla_object.subclient:
                    expected_entry_found = True
                    break
            if not expected_entry_found:
                raise Exception(
                    "Mismatched SLA, expected entry subclient [%s] not found in table [%s]" % (
                        sla_object.subclient,
                        table_name
                    )
                )


    @test_step
    def validate_adminconsole_met_sla_subclients(self, table_name):
        """
        validate the subclients that are  supposed to be in met Admin console SLA

        Args:
            table_name:  met SLA table
        """

        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable(table_name)
        report_viewer.associate_component(table)
        for sla_object in self.SLAReportMetList:
            table.set_filter('Server', sla_object.client_name)
            table.set_filter('Subclient', sla_object.subclient)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if not rowcount:
                raise Exception("Mismatched SLA, valid subclient [%s] is not found in the table "
                                "[%s]" % (sla_object.subclient, table_name))


    @test_step
    def validate_adminconsole_missed_sla_subclients(self, table_name):
        """
        validate the subclients that are not supposed to be in missed Admin console SLA

        Args:
            table_name:  missed SLA table
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
                raise Exception(
                    "Mismatched SLA, expected entry subclient [%s] not found in table [%s]" % (
                        sla_object.subclient,
                        table_name
                    )
                )


    @test_step
    def validate_metrics_sla(self):
        """" validate metrics SLA report"""
        self.utils.private_metrics_upload()
        self.navigator.goto_commcell_dashboard(self.commcell.commserv_name)
        self.dashboard.view_detailed_report("SLA")
        self.validate_missed_sla_subclients('Details for Clients Missed SLA', 'metrics')


    @test_step
    def validate_adminconsole_met_sla(self):
        """ validate Adminconsole SLA report"""
        sla = WebSla(self.webconsole)
        sla.access_met_sla()
        title = 'Protected servers'
        self.validate_adminconsole_met_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text('SLA')

    @test_step
    def validate_adminconsole_missed_snap_sla(self):
        """ validate Adminconsole SLA report for Snap job with no backup copy category"""
        sla = WebSla(self.webconsole)
        sla.access_missed_sla()
        sla.access_snap_with_nobackupcopy_clients()
        title = 'Snap Job with No Backup Copy'
        self.validate_adminconsole_missed_sla_subclients(title)
        self.admin_console.select_breadcrumb_link_using_text('Missed SLA')
        self.admin_console.select_breadcrumb_link_using_text('SLA')


    def update_snapshot_sla_condition(self, config_val, val):
        """
        update snapshot sla condition
        Args:
            val:

        Returns:
        """
        query = "IF NOT EXISTS (SELECT 1 FROM APP_ComponentProp WITH (NOLOCK) " \
                "               WHERE componentType = 1 AND componentId = 2 " \
                "               AND propertyTypeId = " + str(config_val) + " AND modified = 0) " \
                "INSERT INTO APP_ComponentProp VALUES (1, 2, " + str(config_val) + ", 8, " + str(int(val)) + \
                ", 0, '', 0, 0) " \
                "ELSE  UPDATE APP_ComponentProp SET longVal = " + str(int(val)) + " " \
                "WHERE componentType = 1 AND componentId = 2 AND propertyTypeId = " + str(config_val) + \
                " AND modified = 0"

        self.utils.cs_db.execute(query)

    def run(self):
        try:
            self.init_tc()
            self.update_snapshot_sla_condition(3303, False)
            self.update_snapshot_sla_condition(3312, False)
            self.create_backupset()
            self.create_sc("sc1")
            self.run_backup()
            self.SLAReportMetList.clear()
            self.SLAReportMetList.append(
                SLAReportDataExpected(self._client.client_name, "sc1"))
            idautil = idautils.CommonUtils(self)
            subclient_obj = idautil.get_subclient(self.nas_client, "NDMP",
                                                  subclient_name=self.nas_subclient)
            self.log.info("Running backup job for nas subclient {0}".format(self.nas_subclient))
            subclient_obj.backup()
            self.SLAReportMissedList.append(
                SLAReportDataExpected(self.nas_client, self.nas_subclient))
            subclient_backupobj = idautil.get_subclient(self.nas_client, "NDMP",
                                                        subclient_name=self.nas_backup_copy_subclient)
            '''vm client should be in missed sla, as only snap backup is run and bakcup copy is disabled.'''
            self.SLAReportMissedList.append(
                SLAReportDataExpected(self.vsa_client, self.vsa_subclient))
            self.log.info("Running backup job for nas subclient {0}".format(
                self.nas_backup_copy_subclient))

            subclient_backupobj.backup()

            storage_policy = StoragePolicy(self.commcell, subclient_backupobj.storage_policy)
            self.log.info("Running backup copy job for storage policy {0}".format(
                subclient_backupobj.storage_policy))
            storage_policy.run_backup_copy()
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.init_webconsole()
            self.validate_metrics_sla()
            WebConsole.logout_silently(self.webconsole)
            self.init_admin_console()
            self.validate_adminconsole_met_sla()
            self.log.info("validation of  SLA - protected clients table is successful.")
            self.validate_adminconsole_missed_snap_sla()
            self.log.info("validation of  SLA - Snap jobs with no bakcup copy table is "
                          "successful.")
            self.utils.reset_cre()
            self.log.info("Set the parameter,Include Snap Jobs for Met SLA,"
                          " if backup copy and snap vault copy are not enabled "
                          " as true")
            '''since we set this option, vm client should be shown in met sla'''
            self.update_snapshot_sla_condition(3312, True)
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.SLAReportMetList.clear()
            self.SLAReportMetList.append(
                SLAReportDataExpected(self.vsa_client, self.vsa_subclient))
            self.validate_adminconsole_met_sla()
            self.utils.reset_cre()
            self.update_snapshot_sla_condition(3312, False)
            self.log.info("Set the parameter,Include Snap Jobs with no Backup Copy as Met SLA"
                          " as true")
            self.update_snapshot_sla_condition(3303, True)

            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.SLAReportMetList.clear()
            self.SLAReportMetList.append(
                SLAReportDataExpected(self.nas_client, self.nas_subclient))
            self.validate_adminconsole_met_sla()

            self.log.info("validation of SLA - protected clients table is successful.")
            self.utils.reset_cre()
            self.update_snapshot_sla_condition(3303, False)



        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
