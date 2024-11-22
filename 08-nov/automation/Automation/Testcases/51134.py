# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports: Column Properties"""
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom.builder import Datasets

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    QUERY = """
            SELECT 'Split Test, Split Test, Split Test' [SplitTest],
            'Twinkle, twinkle, little star, How I wonder what you are!
            Up above the world so high, Like a diamond in the sky. ' [WrapText],
            1 [One],
            2 [Two],
            3 [Three],
            4 [Hidden],
            5 [Five],
            6 [Six]
            UNION ALL
            SELECT '1', '2', 1, 2, 3, 4, 5, 6
            UNION ALL
            SELECT '1', '2', 1, 2, 1, 4, 5, 6
            """
    JOIN_QUERY = """SELECT [Data Source],[SplitTest],[WrapText],[One],[Two],[Hidden],[Five],[Six],SUM(Three)
                AS [Three] FROM [:AutomationDataset] 
                GROUP BY [Data Source],[SplitTest],[WrapText],[One],[Two],[Hidden],[Five],[Six]
                """
    EXPECTED_DATA = {'OneRenamed': ['1', '1'],
                     'TestExpr': ['2', '2'],
                     'WrapText': ['2', 'Twinkle, twinkle, little star, How I wonder what you are!'
                                       ' Up above the world so high, Like a diamond in the sky.'],
                     'SplitTest': ['1', 'Split Test\nSplit Test\nSplit Test'],
                     'Five': ['5', '5'],
                     'Six': ['6', '6'],
                     'Three': ['4', '3']}

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Column Properties"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.join_dataset = None
        self.rpt_builder = None
        self.table = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                           password=self.inputJSONnode['commcell']['commcellPassword'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
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
            self.build_report()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def build_report(self):
        self.rpt_builder = builder.ReportBuilder(self.webconsole)
        self.rpt_builder.set_report_name(self.name)
        dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(dataset)
        dataset.set_dataset_name("AutomationDataset")
        dataset.set_sql_query(TestCase.QUERY)
        dataset.save()
        self.join_dataset = builder.Datasets.JoinDataset()
        self.rpt_builder.add_dataset(self.join_dataset)
        self.join_dataset.set_dataset_name("Joined DS")
        self.join_dataset.set_sql_query(TestCase.JOIN_QUERY)
        self.join_dataset.save()
        self.table = builder.DataTable("Automation Table")
        self.rpt_builder.add_component(self.table, self.join_dataset)
        self.table.add_column_from_dataset()

    @test_step
    def change_column_name(self):
        """Change Column name"""
        col_one = self.table.Column("One")
        self.table.add_column(col_one, drag_from_dataset=False)
        col_one.set_display_name("OneRenamed")

    @test_step
    def set_column_expression(self):
        """Write expression in column name"""
        col_two = self.table.Column("Two")
        self.table.add_column(col_two, drag_from_dataset=False)
        col_two.set_display_name("='Test' + 'Expr'")

    @test_step
    def enable_wrap_text(self):
        """Enables wrap text"""
        col_wrap_text = self.table.Column("WrapText")
        self.table.add_column(col_wrap_text, drag_from_dataset=False)
        col_wrap_text.wrap_text(toggle=True)

    @test_step
    def split(self):
        """Splits the text in the column and modifies the width"""
        col_split_test = self.table.Column("SplitTest")
        self.table.add_column(col_split_test, drag_from_dataset=False)
        col_split_test.split_column_by(",")
        col_split_test.set_column_width("120")

    @test_step
    def modify_width(self):
        """Modifies the width of the column"""
        col_five = self.table.Column("Five")
        self.table.add_column(col_five, drag_from_dataset=False)
        col_five.set_column_width("120")

    @test_step
    def hide_column(self):
        """Hides the Column"""
        col_hidden = self.table.Column("Hidden")
        self.table.add_column(col_hidden, drag_from_dataset=False)
        col_hidden.hide_column()

    @test_step
    def exclude_column_from_csv(self):
        """Excludes column from CSV exports"""
        col_six = self.table.Column("Six")
        self.table.add_column(col_six)
        col_six.exclude_column_from_csv()

    @test_step
    def column_level_aggregation(self):
        """Set Column level aggregation"""
        col_three = self.table.Column("Three")
        self.table.add_column(col_three)
        col_three.set_aggregation("sum")

    @test_step
    def validate_table(self):
        """Validate changes on builder and viewer"""
        self.rpt_builder.save()
        self.rpt_builder.deploy()
        actual_data = self.table.get_table_data()
        SQLQueries.validate_equality(TestCase.EXPECTED_DATA, actual_data)
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(table)
        actual_data = table.get_table_data()
        SQLQueries.validate_equality(TestCase.EXPECTED_DATA, actual_data)

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.change_column_name()
            self.set_column_expression()
            self.enable_wrap_text()
            self.split()
            self.modify_width()
            self.hide_column()
            self.exclude_column_from_csv()
            self.column_level_aggregation()
            self.validate_table()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
