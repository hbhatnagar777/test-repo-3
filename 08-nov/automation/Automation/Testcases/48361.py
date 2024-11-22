# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure, CVException
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.builder import Datasets

from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (DataSet) - Offline DataSet Collection"
        self.manage_reports = None
        self.admin_console = None
        self.navigator = None
        self.utils = TestCaseUtils(self)
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.rpt_viewer = None
        self.dataset = None
        self.dataset_name = 'AutomationOfflineDataset48631'
        self.metrics_server = None

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.delete_report(self.name)
            self.manage_reports.add_report()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_offline_report(self):
        """Create and Deploy the dataset offline"""
        self.rpt_builder = builder.ReportBuilder(self.webconsole)
        self.rpt_builder.set_report_name(self.name)
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name(self.dataset_name)
        self.dataset.set_sql_query("SELECT 2 + 2 [Number]")
        self.dataset.enable_offline_collection()
        self.dataset.save()
        table = builder.DataTable("AutomationTable")
        self.rpt_builder.add_component(table, self.dataset)
        table.add_column_from_dataset()
        self.rpt_builder.save_and_deploy()

    @test_step
    def view_table_from_viewer(self):
        """Open and view report data from viewer"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        self.rpt_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("AutomationTable")
        self.rpt_viewer.associate_component(table)
        expected_data = {
            "Commcell Version": [str(self.commcell.version)],
            "Commcell Name": [self.commcell.commserv_name],
            "Number": ['4']
        }
        table.set_filter('Commcell Name', self.commcell.commserv_name)
        data = table.get_table_data()
        del data['Last collection time']
        if data != expected_data:
            self.log.info(
                f"Expected Data [{expected_data}]\n"
                f"Received data [{data}]"
            )
            raise CVTestStepFailure(
                "Unexpected data while viewing report"
            )

    @test_step
    def check_query_removed(self, file_name):
        """Validate offline collection queries are removed after report deletion"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)
        query_file = self.metrics_server.get_offline_collect_file_names(self.dataset_name)
        if query_file:
            raise CVTestStepFailure(
                f'Collection Query [{query_file[0][0]}] found in DB after deleting report'
            )
        if self.metrics_server.is_offline_query_exist(file_name):
            raise CVTestStepFailure(
                f'Collection Query [{file_name}] still exist after deleting report'
            )
        self.log.info('Offline entries and queries are removed')

    @test_step
    def check_query_creation(self):
        """Checks if query is created in DB and in script folder
        Returns:
            collection query name
        """
        try:
            content, url = self.metrics_server.get_collect_file_content(self.dataset_name)
            self.log.info('Offline collection query exists in metrics server')
            return url.split('/')[-1]
        except CVException as exp:
            raise CVTestStepFailure(exp)

    def run(self):
        try:
            self.init_tc()
            self.create_offline_report()
            private_metrics, self.metrics_server = self.utils.private_metrics_upload()
            query_file_name = self.check_query_creation()
            self.view_table_from_viewer()
            self.check_query_removed(query_file_name)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
