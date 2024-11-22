# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Report: Verify working of inputs with multiselection """
from abc import ABC, abstractmethod

from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.inputs import (
    String as WCString,
    ListBoxController as WCListBoxController,
    CheckBoxController as WCCheckBoxController
)

from Web.AdminConsole.Reports.Custom.inputs import (
    ListBoxController as ACListBoxController,
    CheckBoxController as ACCheckBoxController
)


from Web.WebConsole.webconsole import WebConsole

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.sql_utils import SQLQueries


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Verify working of inputs with multi selection"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.report_builder = None
        self.report_viewer = None
        self.inputs = list()
        self.table = None
        self.dataset_name_1 = "InputDataSet 1"
        self.dataset_name_2 = "InputDataSet 2"

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
            database_dataset = builder.Datasets.DatabaseDataset()
            self.report_builder.add_dataset(database_dataset)
            database_dataset.set_dataset_name(self.dataset_name_1)
            database_dataset.set_sql_query(SQLQueries.mysql_q())
            database_dataset.save()

            self.report_builder.add_dataset(database_dataset)
            database_dataset.set_dataset_name(self.dataset_name_2)
            database_dataset.set_sql_query("SELECT 10 AS 'ID', 'P' AS 'Char' "
                                           "UNION ALL "
                                           "SELECT 20, 'Q' "
                                           "UNION ALL "
                                           "SELECT 30, 'R'")
            database_dataset.save()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def add_inputs(self):
        """ Adds inputs to the builder."""

        # string_checkbox_manual
        self.inputs.append(InputStringCheckboxManual("CheckBoxUserInput", "CheckBox User Input",
                                                     ["a", "b", "c"], ["1", "2", "3"]))
        # string_listbox_manual
        self.inputs.append(InputStringListboxManual("ListBoxUserInput", "ListBox User Input",
                                                    ["x", "y", "z"], ["4", "5", "6"]))
        # string_checkbox_dataset
        self.inputs.append(InputStringCheckboxDataset("CheckBoxDatasetIP", "CheckBox Dataset IP",
                                                      "ID", "Char", self.dataset_name_1))
        # string_listbox_dataset
        self.inputs.append(InputStringListboxDataset("ListBoxDatasetIP", "ListBox Dataset IP",
                                                     "ID", "Char", self.dataset_name_2))

        for input_ in self.inputs:
            self.report_builder.add_input(input_.data_type)
            input_.configure_input()

    @test_step
    def associate_inputs(self):
        """Add HTML input and parameter to Dataset and preview"""
        dataset = builder.Datasets.DatabaseDataset()
        self.report_builder.add_dataset(dataset)
        dataset.set_dataset_name("Test Dataset")
        dataset.set_sql_query("SELECT * FROM @CheckBoxUserInput UNION "
                              "SELECT * FROM @ListBoxUserInput UNION "
                              "SELECT * FROM @CheckBoxDatasetIP UNION "
                              "SELECT * FROM @ListBoxDatasetIP")

        for input_ in self.inputs:
            dataset.add_parameter(input_.data_type.name, input_.data_type)

        dataset.save()

        self.table = builder.DataTable("Automation Table 1")
        self.report_builder.add_component(self.table, dataset)
        self.table.add_column_from_dataset()

    @test_step
    def validate_data(self):
        """Validate data on both on builder and viewer"""
        self.report_builder.save(deploy=True)
        # self.inputs[0].controller.expand_input_controller()
        self.populate_input_and_validate()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable("Automation Table 1")
        self.report_viewer.associate_component(self.table)
        for input_ in self.inputs:
            self.report_viewer.associate_input(input_.controller_ac)

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
            self.inputs[0].controller_ac.select_values(self.inputs[0].labels)
            self.inputs[1].controller_ac.select_values(self.inputs[1].labels[0:2])
            self.inputs[2].controller_ac.select_values(["1", "2", "3"])
            self.inputs[3].controller_ac.select_values(["10", "20"])
            self.inputs[0].controller_ac.apply()

        data = self.table.get_table_data()
        expected_result = {'CheckBoxUserInput': ['1', '2', '3', '4', '5',
                                                 'A', 'B', 'C', 'P', 'Q']}
        if data != expected_result:
            raise CVTestStepFailure(
                "Unexpected data [%s], expected [%s]" % (
                    str(data), str(expected_result)))

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


class Input(ABC):
    """Abstract Base class for Input objects"""
    def __init__(self, var_name, display_name, labels, values):
        self.data_type = WCString(var_name)
        self.controller_wc = self._controller(display_name)
        self.controller_ac = self._controller1(display_name)
        self.labels = labels
        self.values = values

    @abstractmethod
    def _set_labels_and_values(self, labels, values):
        raise NotImplementedError

    @abstractmethod
    def _controller(self, display_name):
        raise NotImplementedError

    @abstractmethod
    def _controller1(self, display_name):
        raise NotImplementedError

    def configure_input(self):
        """Configures input object"""
        self.data_type.enable_multi_selection()
        self.data_type.add_html_controller(self.controller_wc)
        self._set_labels_and_values(self.labels, self.values)
        self.data_type.save()


class InputStringCheckboxManual(Input):
    """Class containing String Data type with Checkbox controller fed with manual inputs"""
    def _set_labels_and_values(self, labels, values):
        self.controller_wc.set_labels_and_values(labels, values)

    def _controller(self, display_name):
        return WCCheckBoxController(display_name)

    def _controller1(self, display_name):
        return ACCheckBoxController(display_name)


class InputStringCheckboxDataset(Input):
    """Class containing String Data type with Checkbox controller fed with dataset inputs"""
    def __init__(self, var_name, display_name, labels, values, dataset_name):
        super().__init__(var_name, display_name, labels, values)
        self.dataset_name = dataset_name

    def _set_labels_and_values(self, labels, values):
        self.controller_wc.set_dataset_options(self.dataset_name, values, labels)

    def _controller(self, display_name):
        return WCCheckBoxController(display_name)

    def _controller1(self, display_name):
        return ACCheckBoxController(display_name)


class InputStringListboxManual(Input):
    """Class containing String Data type with Listbox controller fed with Manual inputs"""
    def _set_labels_and_values(self, labels, values):
        self.controller_wc.set_labels_and_values(labels, values)

    def _controller(self, display_name):
        return WCListBoxController(display_name)

    def _controller1(self, display_name):
        return ACListBoxController(display_name)


class InputStringListboxDataset(Input):
    """Class containing String Data type with Listbox controller fed with dataset inputs"""
    def __init__(self, var_name, display_name, labels, values, dataset_name):
        super().__init__(var_name, display_name, labels, values)
        self.dataset_name = dataset_name

    def _set_labels_and_values(self, labels, values):
        self.controller_wc.set_dataset_options(self.dataset_name, values, labels)

    def _controller(self, display_name):
        return WCListBoxController(display_name)

    def _controller1(self, display_name):
        return ACListBoxController(display_name)