# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Report: (DataSet) Oracle Stored Procedure"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports import reportsutils

from Reports.Custom.sql_utils import SQLQueries
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    STORED_PROCEDURE = "test_proc(@cursor);"
    CONSTANTS = reportsutils.get_reports_config()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (DataSet) Oracle Stored Procedure"
        self.utils = TestCaseUtils(self)
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.webconsole = None
        self.browser = None
        self.builder = None
        self.table = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_report(self):
        """Create dataSet with Oracle Server DataSource"""
        self.builder = builder.ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(dataset)
        dataset.set_dataset_name("Automation Dataset")
        dataset.set_oracle_datasources(TestCase.CONSTANTS.DATASOURCE.ORACLE)
        dataset.set_database()
        dataset.set_sql_query(TestCase.STORED_PROCEDURE)
        dataset.save()

        self.table = builder.DataTable("Automation Table")
        self.builder.add_component(self.table, dataset)
        self.table.add_column_from_dataset()
        self.builder.save(deploy=True)

    @test_step
    def validate_on_builder(self):
        """Validate table on builder"""
        received_data = self.table.get_table_data()
        SQLQueries.validate_equality(
            received=received_data,
            expected=SQLQueries.oracle_r(),
            err_msg="Unexpected Table data when viewed from Builder"
        )

    @test_step
    def validate_on_viewer(self):
        """Validate table on viewer"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(table)

        received_data = table.get_table_data()
        SQLQueries.validate_equality(
            received=received_data,
            expected=SQLQueries.oracle_r(),
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
            self.create_report()
            self.validate_on_builder()
            self.validate_on_viewer()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
