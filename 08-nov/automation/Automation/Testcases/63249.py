# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                                       --   Initialize TestCase class
    self.init_commandcenter()                                        --   Initialize pre-requisites
    self.get_exclude_sla_count()                                     --   Exclude SLA count
    self.exclude_server_from_sla()                                   --   Exclude server from SLA
    self.validate_sla_exclusion()                                    --   Verify server exclusion
    self.validate_exclude_sla_count()                                --   Verify dashboard and report exclusion count
    self.run_backup()                                                --   Run a backup
    self.validate_met_sla()                                          --   Verify Met SLA count

Input Example:

    "testCases":
            {
                "63249":
                        {
                            "ClientName"    : "Name of the Client",
                            "AgentName"     : "Name of the agent",
                            "BackupsetName" : "Name of the backupset",
                            "SubclientName" : "Name of the subclient"
                        }
            }
"""

from time import sleep
from datetime import datetime, timedelta, date

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.sla import WebSla
from Web.WebConsole.Reports.navigator import Navigator

from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.dashboard import RDashboard
from Web.AdminConsole.Reports.manage_reports import ManageReport

_CONFIG = get_config()


class TestCase(CVTestCase):
    """test case class"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.web_adapter = None
        self.exclude_category = None
        self.job_obj = None
        self.helper = None
        self.table = None
        self.viewer = None
        self.admin_console_rpt_msp_count = None
        self.admin_console_rpt_custom_count = None
        self.dashboard_msp_action_pending = None
        self.dashboard_custom_action_pending = None
        self.name = "Varify SLA exclude categories Service provider and Customer action pending in command center " \
                    "and metrics report"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.navigator: Navigator = None
        self.dashboard = None
        self.utils: TestCaseUtils = None
        self.metrics_msp_count = None
        self.metrics_custom_count = None
        self.admin_console_sla = None
        self.dashboard_sla = None
        self.custom_report_utils = CustomReportUtils(self)
        self.manage_report = None
        self.admin_console = None
        self.sla = None

    def init_commandcenter(self):
        """ validate adminconsole SLA report"""
        self.utils = TestCaseUtils(self)
        self.custom_report_utils.webconsole = self.webconsole
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode["commcell"]["commcellUsername"],
            self.inputJSONnode["commcell"]["commcellPassword"]
        )
        self.navigator = self.admin_console.navigator
        self.manage_report = ManageReport(self.admin_console)
        self.navigator.navigate_to_dashboard()

    @test_step
    def get_exclude_sla_count(self):
        """ get the excluded action count """
        rdashboard = RDashboard(self.admin_console)
        self.dashboard_custom_action_pending = int(rdashboard.get_customer_action_pending_count())
        self.dashboard_msp_action_pending = int(rdashboard.get_msp_action_pending_count())
        self.log.info(f"Command Center dashboard custom action pending value is {self.dashboard_custom_action_pending}"
                      f" MSP action pending value is {self.dashboard_msp_action_pending}")
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("SLA")
        self.web_adapter = WebConsoleAdapter(self.admin_console, self.browser)
        self.sla = WebSla(self.web_adapter)
        self.admin_console_rpt_custom_count = self.sla.get_custom_action_pending()
        self.admin_console_rpt_msp_count = self.sla.get_msp_action_pending()
        self.log.info(f"Command Center SLA report custom action pending value is {self.admin_console_rpt_custom_count}"
                      f" MSP action pending value is {self.admin_console_rpt_msp_count}")

    @test_step
    def exclude_server_from_sla(self):
        """ exclude a server/subclient from SLA report"""

        self.exclude_category = self.sla.Exclude_sla_categories.INVESTIGATION_APPLICATION
        exclude_reason = "TC63249 exclude server from SLA"
        self.sla.exclude_sla(self.client.client_name, self.exclude_category.value, exclude_reason)

    @test_step
    def validate_sla_exclusion(self):
        """ verify the server/subclient is excluded from sla report"""
        current_date_string = date.today()
        new_date = current_date_string + timedelta(days=15)
        formatted_date = new_date.strftime("%b %d, %Y")
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("SLA")
        self.sla.access_excluded_sla()
        self.viewer = viewer.CustomReportViewer(self.admin_console)
        table_obj = viewer.DataTable("Excluded Entities")
        self.viewer.associate_component(table_obj)
        table_obj.set_filter(column_name='Server', filter_string=self.client.client_name.upper())
        server_name = table_obj.get_column_data('Server')
        category = table_obj.get_column_data('Category')
        exclude_until = table_obj.get_column_data('Excluded Until')
        if self.client.client_name not in server_name and self.exclude_category.value not in category \
                and formatted_date not in exclude_until:
            raise CVTestStepFailure(f"Expected client is {self.client.client_name} but received {server_name} and "
                                    f"Expected category is {self.exclude_category.value} but received{category}")

    @test_step
    def run_backup(self):
        """ run backup """
        job_obj = self.subclient.backup()
        ret = job_obj.wait_for_completion()
        if ret is not True:
            raise CVTestStepFailure(f"Expected job status is completed but the current job status : {ret}")

    @test_step
    def validate_met_sla(self):
        """ verify the server is included in protected server page"""
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("SLA")
        self.sla.access_met_sla()
        self.viewer = viewer.CustomReportViewer(self.admin_console)
        table_obj = viewer.DataTable("Protected servers")
        self.viewer.associate_component(table_obj)
        table_obj.set_filter(column_name='Server', filter_string=self.client.client_name.upper())
        server_name = table_obj.get_column_data('Server')
        if self.client.client_name.upper() not in server_name:
            raise CVTestStepFailure(f"Expected server is {self.client.client_name} but received {server_name}")

    @test_step
    def validate_exclude_sla_count(self):
        """" validate all three SLA values"""
        self.log.info(f"Command center pending customer action is [{self.admin_console_rpt_custom_count}], "
                      f" Command center pending MSP action is [{self.admin_console_rpt_msp_count}]")
        if self.admin_console_rpt_custom_count == self.dashboard_custom_action_pending:
            if self.admin_console_rpt_msp_count == self.dashboard_msp_action_pending:
                self.log.info("Command Center dashboard tile and report exclude sla count is matching")

        else:
            raise Exception(
                f"Expected customer action pending from command center is {self.dashboard_custom_action_pending} "
                f"but received from report {self.admin_console_rpt_custom_count}. Expected MSP action pending from "
                f"command center is {self.dashboard_msp_action_pending} but received {self.admin_console_rpt_msp_count}"
            )

    def run(self):
        """ run method"""
        try:
            self.init_commandcenter()
            self.get_exclude_sla_count()
            self.exclude_server_from_sla()
            self.validate_sla_exclusion()
            self.validate_exclude_sla_count()
            self.run_backup()
            now = datetime.now()
            minutes = 63 - now.minute
            self.log.info(f"SLA calculation is supposed to be done in {minutes} minutes , waiting")
            sleep(minutes * 60)
            self.validate_met_sla()
        except Exception as Exp:
            self.utils.handle_testcase_exception(Exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            WebConsole.logout_silently(self.webconsole)
