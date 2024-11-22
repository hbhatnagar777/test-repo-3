# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Report: Column formatter"""
from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole

from Web.AdminConsole.Reports.Custom.viewer import CustomReportViewer
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Forms.forms import Forms

from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    SQL = """DECLARE @i BIGINT = 0
            DECLARE @j INT = -5
            DECLARE @seed_time BIGINT = 718007400
            DECLARE @tmp TABLE
            (
                id BIGINT IDENTITY,
                text_t AS 'Text' + RIGHT (
                    '00000000' + CAST(id * 7 + id AS VARCHAR(8)), 8
                ) PERSISTED,
                datetime_t BIGINT,
                number BIGINT,
                size BIGINT,
                duration BIGINT,
                bool INT
            )
            WHILE @i < 10
            BEGIN
                SET @seed_time = @seed_time + 200000
                INSERT INTO @tmp (datetime_t, number, size, bool, duration) VALUES
                (@seed_time, @seed_time, @seed_time, @j, @seed_time)
                SET @i = @i + 1
                SET @j += 1
            END
            SELECT  *
            FROM @tmp"""
    EXPECTED_DATA = {
        'id': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
        'text_t': ['Text00000008', 'Text00000016', 'Text00000024', 'Text00000032', 'Text00000040',
                   'Text00000048', 'Text00000056', 'Text00000064', 'Text00000072', 'Text00000080'],
        'datetime_t': ['10-04-1992', '10-07-1992', '10-09-1992', '10-11-1992', '10-14-1992',
                       '10-16-1992', '10-18-1992', '10-21-1992', '10-23-1992', '10-25-1992'],
        'number': ['718,207,400', '718,407,400', '718,607,400', '718,807,400', '719,007,400',
                   '719,207,400', '719,407,400', '719,607,400', '719,807,400', '720,007,400'],
        'size': ['701374.41 MB', '701569.73 MB', '701765.04 MB', '701960.35 MB', '702155.66 MB',
                 '702350.98 MB', '702546.29 MB', '702741.60 MB', '702936.91 MB', '703132.23 MB'],
        'duration': ['22Y 9M 2D 14h 03m 20s', '22Y 9M 4D 21h 36m 40s', '22Y 9M 1W 7D 05h 10m',
                     '22Y 9M 1W 9D 12h 43m 20s', '22Y 9M 1W 11D 20h 16m 40s',
                     '22Y 9M 2W 14D 03h 50m', '22Y 9M 2W 16D 11h 23m 20s',
                     '22Y 9M 2W 18D 18h 56m 40s', '22Y 9M 3W 21D 02h 30m',
                     '22Y 9M 3W 23D 10h 03m 20s'],
        'bool': ['✓', '✓', '✓', '✓', '✓', '✗', '✓', '✓', '✓', '✓']
    }

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Column formatter"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.report = None
        self.wf_name = 'Demo_CheckReadiness'

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
            self.report = DefaultReport(self.utils, browser=self.browser)
            self.report.build_default_report(sql=TestCase.SQL, open_report=False, keep_same_tab=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def link_formatter(self):
        """Sets URL link formatter"""
        column = self.report.table.Column("text_t")
        self.report.table.associate_column_in_builder(column)
        column.format_as_url_link(f"{self.webconsole.base_url}reports/index.jsp?page=Dashboard")
        column.open_hyperlink_on_cell("Text00000008", open_in_new_tab=True)
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])

    @test_step
    def wf_formatter(self):
        """Enter column level script"""
        colscrpt = self.report.table.Column("id")
        self.report.table.associate_column_in_builder(colscrpt)
        colscrpt.format_as_link_wf(self.wf_name)

    @test_step
    def date_formatter(self):
        """Sets Date Formatter"""
        column = self.report.table.Column("datetime_t")
        self.report.table.associate_column_in_builder(column)
        column.format_as_date("Asia/Kolkata", "ts", "MM-DD-YYYY")

    @test_step
    def number_formatter(self):
        """Sets number formatter"""
        column = self.report.table.Column("number")
        self.report.table.associate_column_in_builder(column)
        column.format_as_number("comma")
        self.webconsole.wait_till_load_complete()

    @test_step
    def size_formatter(self):
        """Sets size formatter"""
        column = self.report.table.Column("size")
        self.report.table.associate_column_in_builder(column)
        column.format_as_size("kb", "mb", 2)

    @test_step
    def boolean_formatter(self):
        """Sets Boolean Formatter"""
        column = self.report.table.Column("bool")
        self.report.table.associate_column_in_builder(column)
        column.format_as_boolean()

    @test_step
    def duration_formatter(self):
        """Sets duration Formatter"""
        column = self.report.table.Column("duration")
        self.report.table.associate_column_in_builder(column)
        column.format_as_duration("seconds")

    @test_step
    def verify_wf_formatter(self):
        """verifies if the form is submitted"""
        report_viewer = CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(table)
        column = table.Column('id')
        table.associate_column(column)
        column.open_hyperlink_on_cell('1')
        forms = Forms(self.admin_console)
        if forms.is_form_open(self.wf_name):
            forms.close_form()
        else:
            raise CVTestStepFailure("Workflow didn't open from column formatter")

    @test_step
    def verify(self):
        """Verifies table data"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(table)
        actual_data = table.get_table_data()
        SQLQueries.validate_equality(TestCase.EXPECTED_DATA, actual_data)

        column = table.Column("text_t")
        table.associate_column(column)
        column.open_hyperlink_on_cell("Text00000008", open_in_new_tab=True)
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.link_formatter()
            self.wf_formatter()
            self.date_formatter()
            self.number_formatter()
            self.size_formatter()
            self.boolean_formatter()
            self.duration_formatter()
            self.verify()
            self.verify_wf_formatter()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
