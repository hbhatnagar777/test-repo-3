# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.sla import WebSla

from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer
from FileSystem.FSUtils.fshelper import FSHelper
from cvpysdk.metricsreport import PrivateMetrics
from cvpysdk.subclient import Subclient, Subclients
from cvpysdk.subclients.fssubclient import FileSystemSubclient
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
from time import sleep
from datetime import datetime

_CONFIG = get_config()


class SLAReportDataExpected:
    client_name = ''
    agent_name = ''
    instance = ''
    backupset = ''
    subclient = ''
    reason = ''
    lastjobid = ''
    lastjobend = ''
    lastjobstatus = ''

    def __init__(self, client_name, agent_name, instance, backupset, subclient,
                 reason='', lastjobid='', lastjobend='', lastjobstatus=''):
        self.client_name = client_name
        self.agent_name = agent_name
        self.instance = instance
        self.backupset = backupset
        self.subclient = subclient
        self.reason = reason
        self.lastjobid = lastjobid
        self.lastjobend = lastjobend
        self.lastjobstatus = lastjobstatus


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics and Admin SLA"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.admin_console: AdminConsole = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.SLAReportExpectedObjList = []
        self.SLAShouldNotInclude = []
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.subclients = ["44399_sc1", "44399_sc2", "44399_sc3", "44399_sc4", "44399_sc5", "44399_sc6", "44399_sc7", "44399_sc8", "44399_sc9"]
        self.private_metrics = None
        self.backupset = None
        self.utils: TestCaseUtils = None
        self.schedule_helper = None
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.client_name = None

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
            self.helper = None
            FSHelper.populate_tc_inputs(self)
            """Initializes Private metrics object required for this test case"""
            self.private_metrics = PrivateMetrics(self.commcell)
            self.private_metrics.enable_all_services()
            self.schedule_helper = ScheduleCreationHelper(self)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def init_webconsole(self):
        """initialzie webconsole objects"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
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

    def create_valid_path(self, subclient_name):
        """create a valid path to backup"""
        test_path = self.test_path
        slash_format = self.slash_format
        test_path = test_path + slash_format + "subclient_" + subclient_name
        self.client_machine.generate_test_data(
            test_path,
        )
        return test_path

    def create_sc(self, sc_type, subclient_name):
        """create new subclient, if type is valid, valid path will be given as content
        if type is mixed, valid and invalid paths are given as content
        if type is invalid, invalid path is given as content"""
        storage_policy = self.storage_policy
        subclient_content = []
        """if sc_type is mixed, one valid path and one invalid path will be added to the content"""
        if sc_type == 'valid' or sc_type == 'mixed':
            path = self.create_valid_path(subclient_name)
            subclient_content.append(path)
        if sc_type == 'mixed' or sc_type == 'invalid':
            path = "C:\\Test" + subclient_name
            subclient_content.append(path)

        self.helper.create_subclient(name=subclient_name,
                                     storage_policy=storage_policy,
                                     content=subclient_content,
                                     delete=True)

    def run_backup(self):
        """ run backup """
        try:
            self.helper.run_backup()
        except Exception:
            return

    @test_step
    def validate_sla_subclients(self, table_name, report_type):
        """ validate the subclients that are not supposed to be in missed SLA"""
        table = MetricsTable(self.webconsole, table_name)
        if report_type == 'web':
            client_index = 1
            subclient_index = 3
            reason_index = 4
        elif report_type == 'metrics':
            client_index = 0
            subclient_index = 4
            reason_index = 5
        rowcount = table.get_rows_count()
        sla_table_data = table.get_data()
        for sla_object in self.SLAShouldNotInclude:
            expected_entry_not_found = True
            for row_idx in range(0, int(rowcount)):
                rowobject = sla_table_data[row_idx]
                if (rowobject[client_index], rowobject[subclient_index], rowobject[reason_index]) == (
                        sla_object.client_name, sla_object.subclient, sla_object.reason):
                    expected_entry_not_found = False
            if not expected_entry_not_found:
                    raise Exception(
                        "Mismatched SLA, valid client [%s] subclient [%s] backupset [%s] is found in the missed SLA" % (
                            sla_object.client_name,
                            sla_object.subclient,
                            self.backupset
                        )
                    )
        for sla_object in self.SLAReportExpectedObjList:
            expected_entry_found = False
            for row_idx in range(0, int(rowcount)):
                rowobject = sla_table_data[row_idx]
                if rowobject[client_index] == sla_object.client_name and rowobject[subclient_index] == sla_object.subclient \
                        and rowobject[reason_index] == sla_object.reason:
                    expected_entry_found = True
            if not expected_entry_found:
                raise Exception(
                    "Mismatched SLA, expected entry client [%s] subclient [%s] backupset[%s] reason [%s] not found" % (
                        sla_object.client_name,
                        sla_object.subclient,
                        self.backupset,
                        sla_object.reason
                    )
                )

    @test_step
    def validate_metrics_sla(self):
        """" validate metrics SLA report"""
        self.utils.private_metrics_upload()
        self.navigator.goto_commcell_dashboard(self.commcell.commserv_name)
        self.dashboard.view_detailed_report("SLA")
        self.validate_sla_subclients('Details for Clients Missed SLA', 'metrics')

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
        for sla_object in self.SLAShouldNotInclude:
            table.set_filter('Server', sla_object.client_name)
            table.set_filter('Subclient', sla_object.subclient)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if rowcount:
                raise Exception(
                    "Mismatched SLA, valid client [%s] subclient [%s] backupset [%s] is found in the missed SLA" % (
                        sla_object.client_name,
                        sla_object.subclient,
                        self.backupset
                    )
                )
        for sla_object in self.SLAReportExpectedObjList:
            table.set_filter('Server', sla_object.client_name)
            table.set_filter('Subclient', sla_object.subclient)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if not rowcount:
                raise Exception(
                    "Mismatched SLA, expected entry client [%s] subclient [%s] backupset[%s] reason [%s] not found" % (
                        sla_object.client_name,
                        sla_object.subclient,
                        self.backupset,
                        sla_object.reason
                    )
                )

    @test_step
    def validate_admin_sla_report(self):
        """ validate Admin console SLA report"""
        sla = WebSla(self.webconsole)
        sla.access_missed_sla()
        sla.access_failed_clients()
        self.validate_adminconsole_missed_sla_subclients('Failed servers')


    def run(self):
        try:
            self.init_tc()
            self.create_backupset()
            self.create_sc('valid', self.subclients[0])
            self.run_backup()
            self.SLAShouldNotInclude.append(
                SLAReportDataExpected(self._client.client_name, "Windows File System",
                                      "DefaultInstanceName", self.backupset, self.subclients[0]))
            self.create_sc('mixed', self.subclients[1])
            self.run_backup()
            self.SLAShouldNotInclude.append(
                SLAReportDataExpected(self._client.client_name, "Windows File System",
                                      "DefaultInstanceName", self.backupset, self.subclients[1],
                                      "Backup job failed", "Completed with errors"))
            self.create_sc("invalid", self.subclients[2])
            self.run_backup()
            self.SLAReportExpectedObjList.append(
                SLAReportDataExpected(self._client.client_name, "Windows File System",
                                      "DefaultInstanceName", self.backupset, self.subclients[2],
                                      "Backup job failed", "Failed"))
            self.create_sc("valid", self.subclients[3])
            self.SLAShouldNotInclude.append(
                SLAReportDataExpected(self._client.client_name, "Windows File System", "DefaultInstanceName",
                                      self.backupset, self.subclients[3]))
            self.create_sc("valid", self.subclients[4])
            job = self.subclient.backup()
            job.kill()
            self.SLAReportExpectedObjList.append(
                SLAReportDataExpected(self._client.client_name, "Windows File System",
                                      "DefaultInstanceName", self.backupset, self.subclients[4],
                                      "Backup job failed", "Failed"))
            self.create_sc("valid", self.subclients[5])
            self.schedule_helper.create_schedule(
                'subclient_backup',
                schedule_pattern={'freq_type': 'Daily'},
                subclient=self.subclient,
                backup_type="Full",
                wait=False
            )
            self.create_sc("valid", self.subclients[6])
            subclient = FileSystemSubclient(self.backupset, self.subclients[6])
            subclient.disable_backup()
            self.create_sc("valid", self.subclients[7])
            subclient = FileSystemSubclient(self.backupset, self.subclients[7])
            subclient.exclude_from_sla()
            self.create_sc("valid", self.subclients[8])
            subclient = Subclient(self.backupset, self.subclients[8])
            job = subclient.backup()
            job.kill(True)
            scs = Subclients(self.backupset)
            scs.delete(self.subclients[8])
            self.SLAShouldNotInclude.append(
                SLAReportDataExpected(self._client.client_name, "Windows File System",
                                      "DefaultInstanceName", self.backupset, self.subclients[8]))
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.init_webconsole()
            self.validate_metrics_sla()
            WebConsole.logout_silently(self.webconsole)
            self.init_admin_console()
            self.validate_admin_sla_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
