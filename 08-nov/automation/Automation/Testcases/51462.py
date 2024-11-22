# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports: Validate Join Datasets"""

from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.Custom import inputs as wc_inputs

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.Custom import inputs as ac_inputs


def validate(data, result):
    """Validates the data against the given result"""
    if data != result:
        raise CVTestStepFailure("Unexpected data [%s], expected [%s]" % (
            str(data), str(result)))


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Validate Join Datasets"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.table = None
        self.join_dataset = None
        self.report_builder = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
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
    def create_join_dataset(self):
        """Creates join dataset from two database datasets"""
        self.report_builder = builder.ReportBuilder(self.webconsole)
        self.report_builder.set_report_name(self.name)

        database_dataset = builder.Datasets.DatabaseDataset()
        self.report_builder.add_dataset(database_dataset)
        database_dataset.set_dataset_name("DataSet A")
        database_dataset.set_sql_query("SELECT '1' [One], '2' [Two], '3' [Three] "
                                       "UNION ALL "
                                       "SELECT '11' [One], '12' [Two], '13' [Three]")
        database_dataset.save()

        database_dataset = builder.Datasets.DatabaseDataset()
        self.report_builder.add_dataset(database_dataset)
        database_dataset.set_dataset_name("DataSet B")
        database_dataset.set_sql_query("SELECT 'a' [One], 'b' [Two],  'c' [Three] "
                                       "UNION ALL "
                                       "SELECT 'x' [One], 'y' [Two],  'z' [Three]")
        database_dataset.save()

        value = self.add_input()
        self.join_dataset = builder.Datasets.JoinDataset()
        self.report_builder.add_dataset(self.join_dataset)
        self.join_dataset.set_dataset_name("Joined DS")
        self.join_dataset.add_parameter('char', value)
        self.join_dataset.set_sql_query("SELECT * FROM :[DataSet A] UNION ALL "
                                        "SELECT * FROM :[DataSet B] where One in (select char from @char)")

    def add_input(self):
        """Add Report Input"""
        datatype = wc_inputs.String("char")
        self.report_builder.add_input(datatype)
        datatype.enable_multi_selection()
        listbox = wc_inputs.ListBoxController("char")
        datatype.add_html_controller(listbox)
        listbox.set_labels_and_values(["a", "x"], ["a", "x"])
        datatype.save()
        listbox.select_value('a')
        return datatype

    @test_step
    def preview_data(self):
        """Preview the data"""
        result = {'One': ['1', '11', 'a'], 'Two': ['2', '12', 'b'], 'Three': ['3', '13', 'c']}
        data = self.join_dataset.get_preview_data()
        validate(data, result)

    @test_step
    def add_post_query_filter(self):
        """Add post query filter"""
        result = {'One': ['1', 'a'], 'Two': ['2', 'b'], 'Three': ['3', 'c']}
        self.join_dataset.set_post_query_filter("SELECT *FROM $this$ WHERE One != '11'")
        data = self.join_dataset.get_preview_data()
        validate(data, result)
        self.join_dataset.save()
        self.table = builder.DataTable("Automation Table 51462")
        self.report_builder.add_component(self.table, self.join_dataset)
        self.table.add_column_from_dataset()
        self.report_builder.save(deploy=True)

    @test_step
    def apply_filter(self):
        """Apply filter on table"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable("Automation Table 51462")
        report_viewer.associate_component(self.table)
        listbox = ac_inputs.ListBoxController("char")
        report_viewer.associate_input(listbox)
        listbox.select_values(["a"])
        listbox.apply()
        data = self.table.get_table_data()
        result = {'One': ['1', 'a'], 'Two': ['2', 'b'], 'Three': ['3', 'c']}
        validate(data, result)

        self.table.set_filter("One", "a")

        data = self.table.get_table_data()
        result = {'One': ['a'], 'Two': ['b'], 'Three': ['c']}
        validate(data, result)

    @test_step
    def export_as_csv(self):
        """Export to CSV"""
        row_1 = ['One', 'Two', 'Three']
        row_2 = ['a', 'b', 'c']
        self.utils.reset_temp_dir()
        self.table.export_to_csv()
        self.utils.poll_for_tmp_files("csv")
        content = self.utils.get_csv_content(self.utils.get_temp_files()[0])
        if content[3] != row_1 or content[4] != row_2:
            raise CVTestStepFailure("Received data [%s\n%s] \n expected [%s\n%s]" % (
                str(content[3]), str(content[4]), str(row_1), str(row_2)))

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_join_dataset()
            self.preview_data()
            self.add_post_query_filter()
            self.apply_filter()
            self.export_as_csv()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
