# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Reports: Inputs with multi selection disabled"""

from Reports.Custom.sql_utils import SQLQueries, ValueProcessors
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.inputs import (
    String as WCString,
    ListBoxController as WCListBoxController,
    Time as WCTime,
    TimePickerController as WCTimePickerController
)

from Web.AdminConsole.Reports.Custom.inputs import (
    ListBoxController as ACListBoxController,
    TimePickerController as ACTimePickerController
)

from Web.WebConsole.webconsole import WebConsole

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Inputs with multi selection disabled"
        self.browser = None
        self.webconsole = None
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.utils = None
        self.report_builder = None
        self.report_viewer = None
        self.table = None
        self.time_picker_wc = None
        self.time_picker_ac = None
        self.list_box_wc = None
        self.list_box_ac = None
        self.wc_time = None
        self.wc_string = None
        self.utils = TestCaseUtils(self)

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
            self.report_builder = builder.ReportBuilder(self.webconsole)
            self.report_builder.set_report_name(self.name)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def add_inputs(self):
        """ Adds inputs to the builder."""

        self.wc_time = WCTime("Time_t")
        self.report_builder.add_input(self.wc_time)
        self.time_picker_wc = WCTimePickerController("Time_t")
        self.wc_time.add_html_controller(self.time_picker_wc)
        self.wc_time.save()

        self.wc_string = WCString("ListBox_t")
        self.report_builder.add_input(self.wc_string)
        self.list_box_wc = WCListBoxController("ListBox_t")
        self.wc_string.add_html_controller(self.list_box_wc)
        self.list_box_wc.set_labels_and_values(["A", "B", "C"], ["1", "2", "3"])
        self.wc_string.save()

    @test_step
    def associate_inputs(self):
        """Add HTML input and parameter to Dataset and preview"""
        dataset = builder.Datasets.DatabaseDataset()
        self.report_builder.add_dataset(dataset)
        dataset.set_dataset_name("Test Dataset")
        dataset.set_sql_query(
            "SELECT @time_t [Time], @listbox [ListBox]"
        )

        dataset.add_parameter("time_t", self.wc_time)
        dataset.add_parameter("listbox", self.wc_string)

        dataset.save()

        self.table = builder.DataTable("Automation Table 1")
        self.report_builder.add_component(self.table, dataset)
        self.table.add_column_from_dataset()

    @test_step
    def validate_data(self):
        """Validate data on viewer"""
        self.report_builder.save(deploy=True)
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable("Automation Table 1")
        self.report_viewer.associate_component(self.table)
        self.time_picker_ac = ACTimePickerController("Time_t")
        self.list_box_ac = ACListBoxController("ListBox_t")
        self.report_viewer.associate_input(self.time_picker_ac)
        self.report_viewer.associate_input(self.list_box_ac)

        self.populate_input_and_validate()

    @test_step
    def bookmark_report_url(self):
        """Bookmark the report URL with input and validate data"""
        self.browser.driver.refresh()
        self.table = viewer.DataTable("Automation Table 1")
        self.report_viewer.associate_component(self.table)
        self.populate_input_and_validate(populate=False)

    def populate_input_and_validate(self, populate=True):
        """Populates input and validates if set to true"""
        if populate:
            self.time_picker_ac.set_time_controller("12", "30", "AM")
            self.list_box_ac.select_value("A")
            self.list_box_ac.apply()

        data = self.table.get_table_data()
        expected_result = {
            "Time": ["12:30:00 am"],
            "ListBox": ["1"],
        }
        SQLQueries.validate_equality(data, expected_result, ValueProcessors.lower_string)

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_inputs()
            self.associate_inputs()
            self.validate_data()
            self.bookmark_report_url()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
