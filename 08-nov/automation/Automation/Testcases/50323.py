# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Button Panel in Custom Reports"""
import ast

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.utils import CustomReportUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    ENABLE_OPTION_EXPRESSION = "=false"
    CUSTOM_CLASS = "btn btn-danger"
    BUTTON_EXPRESSION = "alert(JSON.stringify(selectedRows))"
    EXPECTED_ROWS = [{'id': 2,
                      'text_t': 'Text00000016',
                      'datetime_t': 'Oct 2, 1992, 07:36:40 AM',
                      'timestamp_t': 718011400
                      },
                     {'id': 5,
                      'text_t': 'Text00000040',
                      'datetime_t': 'Oct 2, 1992, 09:16:40 AM',
                      'timestamp_t': 718017400
                      }
                     ]

    EXPECTED_ROW = [{'id': 3,
                     'text_t': 'Text00000024',
                     'datetime_t': 'Oct 2, 1992, 08:10:00 AM',
                     'timestamp_t': 718013400
                     }
                    ]

    def __init__(self):
        super(TestCase, self).__init__()
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.name = "Custom Reports: Button Panel in Custom Reports"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.button = None
        self.report = None
        self.button_viewer = None
        self.report_viewer = None
        self.table_viewer = None

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
            self.report.build_default_report(keep_same_tab=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_button_and_set_properties(self):
        """Adds button to the table and sets properties of the button"""
        self.button = self.report.table.Button("Button 1")
        self.report.table.toggle_button_panel()
        self.report.table.add_button(self.button)
        self.report.table.toggle_row_selection()
        self.report.table.toggle_multiple_row_selection()
        # Set on click expression
        self.button.set_expression(TestCase.BUTTON_EXPRESSION)
        self.save_deploy_open_report()

    @test_step
    def verify_row_selection(self):
        """Verify row selection."""
        self.switch_to_builder()
        self.button.enable_option(self.button.EnableOption.CUSTOM, TestCase.ENABLE_OPTION_EXPRESSION)
        self.save_deploy_open_report()
        if self.button_viewer.is_button_enabled():
            raise CVTestStepFailure("Button is enabled when script is set to disable button.")

        self.switch_to_builder()
        self.button.enable_option(self.button.EnableOption.ALWAYS)
        self.save_deploy_open_report()
        if not self.button_viewer.is_button_enabled():
            raise CVTestStepFailure("Button is disabled when always enabled option is selected.")

        self.switch_to_builder()
        self.button.enable_option(self.button.EnableOption.SINGLE_SELECT)
        self.save_deploy_open_report()
        self.table_viewer.select_rows([1, 2])
        if self.button_viewer.is_button_enabled():
            raise CVTestStepFailure("Button is enabled on selecting more than one row for the singleSelect option.")

        self.table_viewer.select_rows([1])
        self.switch_to_builder()
        self.button.enable_option(self.button.EnableOption.MULTI_SELECT)
        self.save_deploy_open_report()
        self.table_viewer.select_rows([1, 2, 3])
        if not self.button.is_button_enabled():
            raise CVTestStepFailure("Button is not enabled on selecting more than one or more rows.")
        self.table_viewer.select_rows([1, 2, 3])

    @test_step
    def verify_checkbox_selected_rows(self):
        """Verify checkbox selected rows"""
        self.table_viewer.select_rows([2, 5])
        self.button_viewer.click_button()
        list_ = self.browser.get_text_from_alert()
        temp_list = list_.replace('false', 'False').replace('true', 'True')
        temp_dict = ast.literal_eval(temp_list)
        for dict_ in temp_dict:
            dict_.pop("sys_rowid", None)
            dict_.pop("DataSource", None)
            dict_.pop("expanded", None)
            dict_.pop("selected", None)
        if temp_dict != TestCase.EXPECTED_ROWS:
            raise CVTestStepFailure(f"Button click returned the rows {str(list_)}.\n "
                                    f"Expected rows: {TestCase.EXPECTED_ROWS}")
        self.switch_to_builder()

    @test_step
    def verify_radiobutton_selected_rows(self):
        """Verify radiobutton selected rows"""
        self.report.table.toggle_multiple_row_selection()
        self.save_deploy_open_report()
        self.table_viewer.select_rows([3])
        self.button_viewer.click_button()
        list_ = self.browser.get_text_from_alert()
        temp_list = list_.replace('false', 'False').replace('true', 'True')
        temp_dict = ast.literal_eval(temp_list)
        temp_dict.pop("sys_rowid", None)
        temp_dict.pop("DataSource", None)
        temp_dict.pop("$$hashKey", None)
        temp_dict.pop("expanded", None)
        temp_dict.pop("selected", None)
        list_ = [temp_dict]
        if list_ != TestCase.EXPECTED_ROW:
            raise CVTestStepFailure(f"Button click returned the row: {str(list_)}.\n"
                                    f"Expected row: {TestCase.EXPECTED_ROW}")
        self.browser.driver.refresh()

    def switch_to_builder(self):
        """Closes current tab and switches to builder"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])

    def save_deploy_open_report(self):
        """Saves deploys and opens report"""
        self.report.report_builder.save()
        self.report.report_builder.deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.name)
        self.table_viewer = viewer.DataTable("Automation Table")
        self.button_viewer = viewer.DataTable.Button("Button 1")
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.report_viewer.associate_component(self.table_viewer)
        self.table_viewer.associate_button(self.button_viewer)

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_button_and_set_properties()
            self.verify_row_selection()
            self.verify_checkbox_selected_rows()
            self.verify_radiobutton_selected_rows()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
