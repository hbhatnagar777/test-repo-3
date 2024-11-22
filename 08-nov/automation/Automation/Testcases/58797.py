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

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.health_tiles import SLA
from Web.AdminConsole.Reports.sla import Sla
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer

from Reports.utils import TestCaseUtils

_CONFIG = get_config()


class TestCase(CVTestCase):
    """ Testcase for SLA validation for migrated clients"""
    # pylint: disable=too-many-instance-attributes

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.navigator_ac = None
        self.manage_report = None
        self.subclient1 = None
        self.name = "SLA validation for migrated clients"
        self.browser: Browser = None
        self.admin_console: AdminConsole = None
        self.navigator = None
        self.dashboard = None
        self.tcinputs = {
            "ClientName1": None,
            "BackupsetName1": None,
            "SubclientName1" : None
        }
        self.utils: TestCaseUtils = None
        self.schedule_helper = None
        self.storage_policy = None
        self.client1 = None
        self.client_name = None
        self.backupset1 = None
        self.agent1 = None

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
            self.client1 = self.commcell.clients.get(self.tcinputs['ClientName1'])
            self.agent1 = self.client1.agents.get(self.tcinputs['AgentName'])
            self.backupset1 = self.agent1.backupsets.get(self.tcinputs['BackupsetName1'])
            self.subclient1 = self.backupset1.subclients.get(self.tcinputs['SubclientName1'])
            self.verify_migrated_client(client_name=self.client.client_name)
            self.verify_migrated_client(client_name=self.client1.client_name)
        except Exception as Ex:
            raise CVTestCaseInitFailure(Ex) from Ex

    def verify_migrated_client(self, client_name):
        """
        verify the give client is migrated or not
        """
        client_migrated= self.utils.get_migrated_clients(client_name)
        if client_name.lower() not in client_migrated.lower():
            raise CVTestCaseInitFailure(f"The give client{client_name} is not migrated")

    def init_command_center(self):
        """initialzie command center objects"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator_ac = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator_ac.navigate_to_reports()
            self.manage_report.access_report("SLA")
        except Exception as Ex:
            raise CVTestCaseInitFailure(Ex) from Ex

    @test_step
    def validate_metrics_sla(self):
        """ validate metrics SLA report"""
        self.navigator.navigate_to_metrics()
        self.manage_report.access_commcell_health(self.commcell.commserv_name)
        sla_tile = SLA(self.admin_console)
        sla_tile.access_view_details()
        self.validate_command_center_sla_subclients(title="Details for Clients Missed SLA")

    @test_step
    def validate_command_center_sla_subclients(self, table_name):
        """
        validate the subclients that are supposed to be in all met and missed SLA page

        Args:
            table_name:  missed SLA table
        """
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable(table_name)
        report_viewer.associate_component(table)
        if table_name == "All subclients and VMs that missed SLA":
            table.set_filter('Server', self.client.display_name)
            table.set_filter('Subclient', self.subclient.subclient_name)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if not rowcount:
                raise Exception(
                    "Mismatched SLA, expected entry client [%s] subclient [%s] not found in the missed SLA" % (
                        self.client.display_name,
                        self.subclient.subclient_name
                    )
                )
        if table_name == "Protected servers":
            table.set_filter('Server', self.client1.display_name)
            table.set_filter('Subclient', self.subclient1.subclient_name)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Server'])
            if not rowcount:
                raise Exception(
                    "Mismatched SLA, expected entry client [%s] subclient [%s] not found" % (
                        self.client1.client_name,
                        self.subclient.subclient_name
                    )
                )
        if table_name == "Details for Clients Missed SLA":
            table.set_filter('Client', self.client.display_name)
            table.set_filter('Subclient', self.subclient.subclient_name)
            sla_table_data = table.get_table_data()
            rowcount = len(sla_table_data['Client'])
            if not rowcount:
                raise Exception(
                    "Mismatched SLA, expected entry client [%s] subclient [%s] not found" % (
                        self.client1.client_name,
                        self.subclient.subclient_name
                    )
                )

    @test_step
    def run_backup(self):
        """ run backup """
        job_obj = self.subclient1.backup()
        ret = job_obj.wait_for_completion()
        if ret is not True:
            raise CVTestStepFailure(f"Expected job status is completed but the current job status {job_obj.status}")

    @test_step
    def validate_admin_sla_report(self):
        """ validate Admin console SLA report"""
        sla = Sla(self.admin_console)
        sla.access_all_missed_sla()
        self.validate_command_center_sla_subclients('All subclients and VMs that missed SLA')
        self.log.info("Validated the missed SLA from Command Center")
        self.navigator_ac.navigate_to_reports()
        self.manage_report_admin.access_report("SLA")
        sla.access_met_sla()
        self.validate_command_center_sla_subclients('Protected servers')
        self.log.info("Validated the missed SLA from Command Center")

    def run(self):
        try:
            self.init_tc()
            self.subclient.backup()
            self.run_backup()
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.utils.private_metrics_upload(enable_all_services=True)
            self.init_command_center()
            self.validate_admin_sla_report()
            self.validate_metrics_sla()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
