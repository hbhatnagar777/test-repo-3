# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Report: Validate Dataset fields. """


from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.WebConsole.Reports.Custom.builder import ReportBuilder, DataTable
from Web.AdminConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Validate Dataset fields"
        self.admin_console = None
        self.navigator = None
        self.manage_reports = None
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.data = None
        self.report_builder = None
        self.database_dataset = None

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
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
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_custom_report(self):
        """Creates a custom report having Database dataset. """

        # Set Report Name.
        self.report_builder = ReportBuilder(self.webconsole)
        self.report_builder.set_report_name(self.name)

        # Add Dataset.
        self.database_dataset = Datasets.DatabaseDataset()
        self.report_builder.set_report_description("Custom Reports")
        self.report_builder.add_dataset(self.database_dataset)

        self.database_dataset.set_dataset_name("AutomationDataSet")
        self.database_dataset.set_sql_query("SELECT 1, 2")
        self.database_dataset.get_preview_data()

    @test_step
    def click_show_all_fields(self):
        """Clicks show all fields. """
        self.database_dataset.enable_all_fields()

    @test_step
    def click_show_specific_fields(self):
        """Clicks show specific fields. """
        self.database_dataset.enable_show_specific_fields()

    @test_step
    def rename_field(self):
        """Renames the columns under the fields tab. """
        self.database_dataset.rename_field("No Column Name1", "One")
        self.database_dataset.rename_field("No Column Name2", "Two")
        report_data = self.database_dataset.get_preview_data()
        actual_data = {'One': ['1'], 'Two': ['2']}

        if actual_data != report_data:
            self.log.info(
                f"\nExpected Data [{report_data}]\nReceived Data [{actual_data}]"
            )
            raise CVTestStepFailure("Unable to change column name")

        # Save Dataset
        self.database_dataset.save()

        # Create Table and populate with the Dataset.
        table = DataTable("AutomationTable")
        self.report_builder.add_component(table, self.database_dataset)
        table.add_column_from_dataset()
        report_data = table.get_table_data()

        # Save and Deploy Report
        self.report_builder.save(deploy=True)

        # Opens report.
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

        # validate report
        report_viewer = CustomReportViewer(self.admin_console)
        table = viewer.DataTable("AutomationTable")
        report_viewer.associate_component(table)
        if report_data != table.get_table_data():
            raise CVTestStepFailure("Changing Column name failed.\
                                     Report Builder data -- {0}\
                                     Report Viewer data  -- {1}"
                                    .format(actual_data, report_data))

        self.browser.driver.switch_to.window(self.browser.driver.window_handles[1])
        self.report_builder.edit_dataset(self.database_dataset)

    @test_step
    def click_add(self):
        """ Checks add functionality. """
        value1 = self.database_dataset.get_fields_names()
        self.database_dataset.add_field("AutomationField")
        value2 = self.database_dataset.get_fields_names()

        if len(value1) != len(value2) - 1 and '' not in value2:
            raise CVTestStepFailure("Add Button under Fields Tab doesn't work as expected.")

    @test_step
    def click_delete(self):
        """ Checks delete functionality. """
        row_name = "One"
        value1 = self.database_dataset.get_fields_names()
        self.database_dataset.delete_field(row_name)
        value2 = self.database_dataset.get_fields_names()

        if len(value1) != len(value2) + 1 and row_name not in value2:
            raise CVTestStepFailure("Delete Button under Fields Tab doesn't work as expected.")

    @test_step
    def click_up_and_down(self):
        """ Checks up and down functionality. """

        def click(direction):
            """ Clicks either up or down.

            Args:
                direction:  The direction which you want to click which is either 'up' or 'down'.

            """
            row_name = "Two"
            if direction == "up":
                exception = "Row Didn't move up as expected."
                move = self.database_dataset.move_field_up
                offset = -1
            elif direction == "down":
                move = self.database_dataset.move_field_down
                exception = "Row Didn't move down as expected."
                offset = 1
            else:
                raise ValueError("up or down are the only values expected")

            value1 = self.database_dataset.get_fields_names()
            if row_name in value1:
                index = value1.index(row_name)
                move(row_name)
            else:
                raise CVTestStepFailure("The column '{0}' is not in the table. ")

            value2 = self.database_dataset.get_fields_names()
            if value2[index + offset] != row_name:
                raise CVTestStepFailure(exception)

        click("up")         # Click up
        click("down")       # Click down

        self.database_dataset.save()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_custom_report()
            self.click_show_all_fields()
            self.click_show_specific_fields()
            self.rename_field()
            self.click_add()
            self.click_delete()
            self.click_up_and_down()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
