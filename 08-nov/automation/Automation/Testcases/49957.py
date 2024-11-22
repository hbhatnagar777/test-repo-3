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
    CVTestCaseInitFailure, CVTestStepFailure
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
        self.name = "Custom Report: (DataSet) - PostQuery on Offline DataSet"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.dataset = None
        self.rpt_viewer = None

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
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.name)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_offline_dataset(self):
        """Create offline dataset with post query filter"""
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("AutomationOfflineDataset")
        self.dataset.set_sql_query("""
            SELECT 2 + 2 [Number]
            UNION ALL
            SELECT 2 + 2 + 3
            """
                                   )
        self.dataset.enable_offline_collection()
        self.dataset.set_post_query_filter("""
            SELECT *
            FROM $this$
            WHERE Number = 4
            """
                                           )
        self.dataset.save()

    @test_step
    def deploy_report(self):
        """Add a table using offline dataset"""
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
            "Number": ["4"]
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
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_offline_dataset()
            self.deploy_report()
            self.utils.private_metrics_upload()
            self.view_table_from_viewer()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
