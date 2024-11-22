# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.sql_utils import (
    SQLQueries, ValueProcessors
)

from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
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
        self.name = "Custom Report: (DataSet) - Oracle Server DataSource"
        self.utils = TestCaseUtils(self)
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.dataset = None
        self.table = None

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
    def create_dataset(self):
        """Create and Preview dataSet with oracle Server DataSource"""
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("AutomationDataSet")
        self.dataset.set_all_oracle_datasource()
        self.dataset.set_database()
        self.dataset.set_sql_query(SQLQueries.oracle_q())
        received_data = self.dataset.get_preview_data()
        expected_data = SQLQueries.oracle_r()
        SQLQueries.validate_equality(
            received=received_data,
            expected=expected_data,
            value_processor=ValueProcessors.lower_and_unique,
            err_msg="Unexpected Table data when viewed from Dataset preview"
        )
        self.dataset.save()

    @test_step
    def add_datasource_to_table(self):
        """Add the datasource to any table"""
        data_table = builder.DataTable("AutomationTable")
        self.rpt_builder.add_component(data_table, self.dataset)
        data_table.add_column_from_dataset()
        received_data = data_table.get_table_data()
        expected_data = SQLQueries.oracle_r()
        SQLQueries.validate_equality(
            received=received_data,
            expected=expected_data,
            value_processor=ValueProcessors.lower_and_unique,
            err_msg="Unexpected Table data when viewed from Builder"
        )
        self.rpt_builder.save_and_deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        self.table = viewer.DataTable("AutomationTable")
        rpt_viewer = viewer.CustomReportViewer(self.admin_console)
        rpt_viewer.associate_component(self.table)

    @test_step
    def validate_report_viewer(self):
        """Table data should also be shown on viewer"""
        received_data = self.table.get_table_data()
        expected_data = SQLQueries.oracle_r()
        SQLQueries.validate_equality(
            received=received_data,
            expected=expected_data,
            value_processor=ValueProcessors.lower_and_unique,
            err_msg="Unexpected Table data when viewed from Viewer"
        )

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_dataset()
            self.add_datasource_to_table()
            self.validate_report_viewer()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
