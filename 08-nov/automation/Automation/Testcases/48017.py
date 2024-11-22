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
        self.name = "Custom Report: Dependent Listbox Input"
        self.admin_console = None
        self.navigator = None
        self.manage_reports = None
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.builder: builder.ReportBuilder = None
        self.util = TestCaseUtils(self)

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
        except Exception as err:
            raise CVTestCaseInitFailure(err) from err

    @test_step
    def add_source_dataset(self):
        """
        Create the dataset which will be the source for all the dependant input
        """
        dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(dataset)
        dataset.set_dataset_name("Source")
        dataset.set_sql_query(
            """
            SELECT 1 [Number], 'A' [Character]
            UNION
            SELECT 2, 'B'
            UNION
            SELECT 4, 'D'
            UNION
            SELECT 3, 'C'
            UNION
            SELECT 6, 'F'
            UNION
            SELECT 5, 'E'
            """
        )
        dataset.save()
        return dataset

    def add_dependent_dataset(self, input_datatype: wc_inputs.Integer):
        """
        Create the dataset which will display the values received from the dependent input
        """
        dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(dataset)
        dataset.set_dataset_name("Dependant")
        dataset.set_sql_query(
            """
            SELECT source_dataset_selected_values
            FROM @source_dataset_selected_values
            """
        )
        dataset.add_parameter(
            "source_dataset_selected_values",
            input_datatype,
            required=True
        )
        dataset.save()
        return dataset

    @test_step
    def add_required_multi_non_dependent_input(self):
        """
        Create listbox that is required, allows multi-select

        This listbox is also the source for dependant input
        """
        datatype = wc_inputs.Integer("RequiredMultiInput")
        self.builder.add_input(datatype)
        datatype.set_required()
        datatype.enable_multi_selection()
        listbox = wc_inputs.ListBoxController("RequiredMultiInput")
        datatype.add_html_controller(listbox)
        listbox.set_dataset_options("Source", "Number", "Character")
        datatype.save()
        listbox.select_values(["A", "B", "C", "D"])
        return datatype, listbox

    @test_step
    def add_dependent_input(self):
        """Add dependent listbox input"""
        datatype = wc_inputs.Integer("DependentInput")
        listbox = wc_inputs.ListBoxController("DependentInput")
        self.builder.add_input(datatype)
        datatype.add_html_controller(listbox)
        datatype.enable_multi_selection()
        listbox.set_dataset_options(
            "Dependant",
            "source_dataset_selected_values",
            "source_dataset_selected_values",
            depends_on="RequiredMultiInput"
        )
        datatype.save()
        return datatype, listbox

    @test_step
    def dependent_dataset_preview(
            self,
            input_datatype: wc_inputs.Integer,
            listbox: wc_inputs.ListBoxController):
        """Add dataset and table to view the dependent input values"""
        dataset = builder.DatabaseDataset()
        self.builder.add_dataset(dataset)
        dataset.set_dataset_name("PreviewInputDataset")
        dataset.add_parameter("input", input_datatype)
        dataset.set_sql_query(
            """
            SELECT input
            FROM @input
            """
        )
        dataset.save()

        table = builder.DataTable("PreviewTable")
        self.builder.add_component(table, dataset)
        table.add_column_from_dataset()
        self.builder.save(deploy=True)

        listbox.select_values(["1", "3"])
        listbox.apply()
        received_data = table.get_table_data()
        expected_data = {"input": ["1", "3"]}
        if received_data != expected_data:
            self.log.error(
                f"\nExpected: {expected_data}\nReceived: {received_data}"
            )
            raise CVTestStepFailure(
                "Unexpected data in table for dependent input"
            )
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def validate_dependent_input_on_viewer(self):
        """Validate dependent input on viewer"""
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        titles = viewer_obj.get_all_component_titles()
        if "PreviewTable" in titles:
            raise CVTestStepFailure(
                "Components are visible without selecting the required Listbox"
            )

        listbox = ac_inputs.ListBoxController("RequiredMultiInput")
        viewer_obj.associate_input(listbox)
        listbox.select_values(["C", "B", "D"])
        listbox = ac_inputs.ListBoxController("DependentInput")
        viewer_obj.associate_input(listbox)
        listbox.select_values(["2", "4"])
        listbox.apply()

        table = viewer.DataTable("PreviewTable")
        viewer_obj.associate_component(table)
        received_data = table.get_table_data()
        expected_data = {"input": ["2", "4"]}
        if received_data != expected_data:
            raise CVTestStepFailure(
                "Unexpected data in the table after selecting dependent input"
            )

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_source_dataset()
            input_datatype, _ = self.add_required_multi_non_dependent_input()
            self.add_dependent_dataset(input_datatype)
            input_datatype, listbox = self.add_dependent_input()
            self.dependent_dataset_preview(input_datatype, listbox)
            self.validate_dependent_input_on_viewer()
            self.delete_report()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
