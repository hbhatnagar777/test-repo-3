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
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
)
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import (
    builder, inputs as wc_inputs
)
from Web.AdminConsole.Reports.Custom import viewer, inputs as ac_inputs


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Required, Optional and Defaults in Listbox"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.builder: builder.ReportBuilder = None
        self.util = TestCaseUtils(self)
        self.listbox_wc: wc_inputs.ListBoxController = None
        self.listbox_ac: ac_inputs.ListBoxController = None
        self.string = None

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
            self.builder = builder.ReportBuilder(self.webconsole)
            self.builder.set_report_name(self.name)
            self.string = wc_inputs.String("Listbox")
            self.builder.add_input(self.string)
            self.listbox_wc = wc_inputs.ListBoxController("Listbox")
            self.listbox_ac = ac_inputs.ListBoxController("Listbox")
            self.string.add_html_controller(self.listbox_wc)
        except Exception as err:
            raise CVTestCaseInitFailure(err) from err

    def create_report(self):
        try:
            dataset = builder.Datasets.DatabaseDataset()
            self.builder.add_dataset(dataset)
            dataset.set_dataset_name("AutomationDataset")
            dataset.set_sql_query(
                """
                SELECT @val [Val]
                """
            )
            dataset.add_parameter("@val", self.string)
            dataset.save()

            table = builder.DataTable("AutomationTable")
            self.builder.add_component(table, dataset)
            table.add_column_from_dataset()
            self.builder.save(deploy=True)
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
            self.browser.driver.refresh()
            self.manage_reports.access_report(self.name)
        except Exception as err:
            raise CVTestStepFailure(err) from err

    @test_step
    def select_manual_values(self):
        """Create a Listbox with values populated manually and marked optional"""
        self.listbox_wc.set_labels_and_values(
            ["A", "C", "B", "D"],
            ["1", "3", "2", "4"]
        )

    @test_step
    def set_default_value(self):
        """Create a listbox having default value"""
        self.string.set_default_value("1")
        self.string.save()

    @test_step
    def validate_viewer_data(self):
        """Validate the data on the optional and default values on viewer"""
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("AutomationTable")
        viewer_obj.associate_component(table)
        viewer_obj.associate_input(self.listbox_ac)
        received_data = table.get_table_data()
        expected_data = {"Val": ["1"]}
        if received_data != expected_data:
            self.log.error(
                f"Expected: {expected_data}\nReceived: {received_data}"
            )
            raise CVTestStepFailure(
                "Default value not set, unexpected data"
            )

        self.listbox_ac.select_value("C")
        self.listbox_ac.apply()
        expected_data = {"Val": ["3"]}
        received_data = table.get_table_data()
        if received_data != expected_data:
            self.log.error(
                f"Expected: {expected_data}\nReceived: {received_data}"
            )
            raise CVTestStepFailure(
                "Selected value not set, unexpected data"
            )

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.select_manual_values()
            self.set_default_value()
            self.create_report()
            self.validate_viewer_data()
            self.delete_report()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
