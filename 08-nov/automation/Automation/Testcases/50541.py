# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Report: Daterange Component"""
import calendar
import datetime

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.report_templates import DefaultReport
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

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    CUSTOM_RANGES = {
        "Last 2 Month": ["1", "5"],
        "Last 2 Year": ["1", "2", "5", "6", "7"],
        "Last 1 hour": ["1"]}

    QUERY = """  DECLARE @currentTime DATETIME = DATEADD(MINUTE, -2, GETDATE())
                 DECLARE @result TABLE(id INT IDENTITY(1,1), dt DATETIME)

                 INSERT INTO @result VALUES(@currentTime)
                 INSERT INTO @result VALUES(DATEADD(YEAR, -1, @currentTime))
                 INSERT INTO @result VALUES(DATEADD(YEAR, -2, @currentTime))
                 INSERT INTO @result VALUES(DATEADD(YEAR, -3, @currentTime))
                 INSERT INTO @result VALUES(DATEADD(MONTH, -1, @currentTime))
                 INSERT INTO @result VALUES(DATEADD(MONTH, -2, @currentTime))
                 INSERT INTO @result VALUES(DATEADD(MONTH, -3, @currentTime))
                 SELECT *
                 FROM @result"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Daterange Component"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.table = None
        self.date_range = None

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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_custom_range_to_date_range_component(self):
        """Adds custom range to the properties panel and validates in builder"""
        report = DefaultReport(self.utils, browser=self.browser)
        report.build_default_report(sql=TestCase.QUERY, keep_same_tab=True)

        date_range_name = "Automation DateRange"
        self.date_range = builder.DateRange(date_range_name)
        report.report_builder.add_component(self.date_range, report.dataset)

        self.date_range.add_custom_range("Last 2 Year", ">-2y")
        self.date_range.add_custom_range("Last 2 Month", ">-2M")
        self.date_range.add_column_from_dataset("dt")
        self.table = report.table

        self.log.info("*****************Validate in Builder*****************")
        self.filter_range()
        self.relative_range()
        report.report_builder.save()
        report.report_builder.deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        self.log.info("*****************Validate in Viewer*****************")
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.date_range = viewer.DateRange(date_range_name)
        self.table = viewer.DataTable(report.table.title)
        report_viewer.associate_component(self.date_range)
        report_viewer.associate_component(self.table)

    @test_step
    def filter_range(self):
        """Filter the daterange component using the added custom range"""
        for range_, expected_result in TestCase.CUSTOM_RANGES.items():
            self.date_range.set_predefined_range(range_)
            id_ = self.table.get_table_data().get('id')
            SQLQueries.validate_list_equality(expected_result, id_)

    @test_step
    def relative_range(self):
        """Filter using relative range"""
        end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%m/%d/%Y").split("/")
        start_date = (datetime.datetime.now() + datetime.timedelta(days=-3)).strftime("%m/%d/%Y").split("/")
        month = dict((k, v) for k, v in enumerate(calendar.month_abbr))
        start_date[0] = month[int(start_date[0])]
        end_date[0] = month[int(end_date[0])]
        start_date = " ".join(start_date)
        end_date = " ".join(end_date)
        self.date_range.set_custom_range(start_date, end_date)
        id_ = self.table.get_table_data().get('id')
        SQLQueries.validate_list_equality(TestCase.CUSTOM_RANGES["Last 1 hour"], id_)

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_custom_range_to_date_range_component()
            self.filter_range()
            # self.relative_range() """Will implement later. Needs to have proper way to set the time"
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
