# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports: Table level Filters"""
from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    EXPECTED_VALUES = {
        "number": {
            ">9": ["10"] * 3,
            "<2": ["1"] * 3,
            "<=2": ["1"] * 3 + ["2"] * 3,
            ">5 && <7": ["6"] * 3,
            ">5 && <7 || >8 && <10": ["6"] * 3 + ["9"] * 3,
            "=3": ["3"] * 3
        },
        "text": {
            "begins:Big": ["Big Flat Earth"],
            "ends:Big": ["Flat Earth Big"],
            "equals:Earth Big Flat": ["Earth Big Flat"],
            "notequals:Earth Big Flat": ["Big Flat Earth", "Flat Earth Big"],
            "contains:Flat": ["Big Flat Earth", "Earth Big Flat", "Flat Earth Big"],
            "notcontains:Flat": [],
            "word:Earth": ["Big Flat Earth", "Earth Big Flat", "Flat Earth Big"]

        },
        "datetime_t": {
            ">-120s": list(map(str, list(range(1, 9)))),
            ">-5m": list(map(str, list(range(1, 10)))),
            "<-24h": list(map(str, list(range(18, 31)))),
            ">-1000m && >-2h": list(map(str, list(range(1, 14)))),
            "<-3M": list(map(str, list(range(24, 31)))),
            "<-5y": list(map(str, list(range(29, 31))))
        }
    }

    def __init__(self):
        super(TestCase, self).__init__()
        self.navigator = None
        self.name = "Custom Reports: Table level Filters"
        self.browser = None
        self.admin_console = None
        self.manage_report = None
        self.webconsole = None
        self.utils = CustomReportUtils(self)
        self.table = None

    def init_tc(self, browser_type):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object(browser_type=browser_type)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.manage_report = ManageReport(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.utils.webconsole = self.webconsole
            self.navigator.navigate_to_reports()
            self.manage_report.delete_report(self.name)
            self.browser.driver.refresh()
            self.admin_console.wait_for_completion()
            self.manage_report.add_report()
            self.build_report_and_open(self.browser)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def build_report_and_open(self, browser_type):
        """Builds and opens report"""
        report = DefaultReport(self.utils, self.admin_console, browser_type)
        report.build_default_report(sql=SQLQueries.sql_server_q2(), overwrite=False)
        self.admin_console.wait_for_completion()
        self.manage_report.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable(report.table.title)
        report_viewer.associate_component(self.table)

    @test_step
    def numeric_filter(self):
        """Testing Numeric Filter"""
        column_name = "number"
        for value in TestCase.EXPECTED_VALUES[column_name]:
            self.table.set_filter(column_name, value)
            data = self.table.get_table_data()
            SQLQueries.validate_list_equality(TestCase.EXPECTED_VALUES[column_name][value], data[column_name])
        self.table.set_filter(column_name, "")

    @test_step
    def string_filter(self):
        """Testing String Filter"""
        column_name = "text"
        self.table.set_filter("number", "=1")
        for value in TestCase.EXPECTED_VALUES[column_name]:
            self.table.set_filter(column_name, value)
            data = self.table.get_table_data()
            SQLQueries.validate_list_equality(TestCase.EXPECTED_VALUES[column_name][value], data.get(column_name, []))
        self.table.set_filter(column_name, "")
        self.table.set_filter("number", "")

    @test_step
    def time_filter(self):
        """Testing Time Filter"""
        column_name = "datetime_t"
        for value in TestCase.EXPECTED_VALUES[column_name]:
            self.table.set_filter(column_name, value)
            data = self.table.get_table_data()
            SQLQueries.validate_list_equality(TestCase.EXPECTED_VALUES[column_name][value], data["id"])
        self.table.set_filter(column_name, "")

    @test_step
    def bookmark_filter(self):
        """Bookmark any filter string"""
        self.table.set_filter("id", ">10")
        self.table.set_filter("number", "!=4")
        self.table.set_filter("text", "=Big Flat Earth")
        self.table.set_filter("datetime_t", "<-3M")
        self.browser.driver.refresh()
        self.admin_console.wait_for_completion()
        data = self.table.get_table_data()
        del data['datetime_t']
        SQLQueries.validate_equality(
            data, {
                'id': ['25', '28'],
                'number': ['9', '10'],
                'text': ['Big Flat Earth', 'Big Flat Earth']
            }
        )

    def run(self):
        try:
            browsers = (
                Browser.Types.FIREFOX,
                Browser.Types.CHROME,
                # Browser.Types.IE  # TODO: Uncomment IE when IE issue is fixed
            )
            for browser in browsers:
                self.init_tc(browser)
                self.time_filter()
                self.numeric_filter()
                self.string_filter()
                self.bookmark_filter()
                AdminConsole.logout_silently(self.admin_console)
                Browser.close_silently(self.browser)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
