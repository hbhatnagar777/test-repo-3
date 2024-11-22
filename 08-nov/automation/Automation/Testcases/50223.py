# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Verify alert Test criteria for reports """
from Web.AdminConsole.Components.table import Rtable, Rfilter
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.cte import ConfigureAlert
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.AdminConsole.Reports.Custom import viewer

from Reports.Custom.utils import CustomReportUtils
from Reports import reportsutils

from AutomationUtils.cvtestcase import CVTestCase

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.admin_console = None
        self.name = "Verify alert Test criteria for reports"
        self.show_to_user = True
        self.browser = None
        self.AdminConsole = None
        self.navigator = None
        self.report = None
        self.alert_window = None
        self._driver = None
        self.utils = CustomReportUtils(self)
        self.custom_report = REPORTS_CONFIG.REPORTS.CUSTOM[0]
        self.table = None
        self.table_data = None
        self.column1 = None
        self.column2 = None
        self.column1_string = None
        self.column2_string = None
        self.dummy_condition_string = None

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()

            # login to web console and redirect to ww reports.
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.commcell.commcell_username,
                                  password=commcell_password)
            self.navigator = self.admin_console.navigator
            self._driver = self.browser.driver
            self.report = ManageReport(self.admin_console)
            self.rtable = Rtable(self.admin_console)
            self.alert_window = ConfigureAlert(self.admin_console)
            self.dummy_condition_string = "999TB"
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_criteria_table_content(self, report):
        """Get criteria table content"""
        self.alert_window.check_test_criteria()
        return self.rtable.get_table_data()

    @test_step
    def test_step_1(self, report):
        """
        Verify 1st column string test criteria is working with 'All' as condition
        """
        self.log.info("Verifying test criteria for [%s] report", report)
        self.table.set_filter(self.column1, self.column1_string)
        if report == self.custom_report:
            self.table_data = self.table.get_table_data()
            self.table.configure_alert()
        else:
            self.table_data = self.table.get_table_data()
            self.table.configure_alert()
        self.alert_window.set_value(self.column1_string)
        criteria_table = self.get_criteria_table_content(report)
        self.close_alert_criteria_window()
        self.alert_window.cancel()
        if self.table_data['Job status'] != criteria_table['Job status'] \
                and self.table_data['Total Jobs'] <= criteria_table['Total jobs'] :
            raise CVTestStepFailure(f"Tables values are not equal expected column {self.table_data['Job status']} and"
                                    f" total jobs {self.table_data['Total Jobs']} but received column "
                                    f"{criteria_table['Job status']} total jobs {criteria_table['Total jobs']}")
        self.log.info("Verified 1st column string test criteria is working with 'All' "
                      "as condition")

    @test_step
    def test_step_2(self, report):
        """
        With any condition, set 1st column string, for 2nd column set dummy value, it should list all the table data as
        same as with one condition string
        """
        self.log.info("Verifying test criteria for [%s] report", report)
        # this should be numeric, as columns may be take numeric value some times
        self.table.configure_alert()
        self.alert_window.set_value(self.column1_string)
        self.alert_window.add_condition(column_name=self.column2,
                                        column_value=self.dummy_condition_string,
                                        column_condition=self.alert_window.operator.NOT_EQUAL_TO, alert_criteria_idx=1)
        self.alert_window.select_alert_condition("any")
        criteria_table = self.get_criteria_table_content(report)
        self.close_alert_criteria_window()
        self.alert_window.cancel()
        if report == self.custom_report:
            self.table_data = self.table.get_table_data()
        if self.table_data['Job status'][0] not in criteria_table['Job status'][0]:
            raise CVTestStepFailure("Tables are not equal with 'any' condition: for [%s] column "
                                    "with [%s] condition string and [%s] column with [%s]condition"
                                    " string" % (self.column1, self.column1_string, self.column2,
                                                 self.dummy_condition_string))
        self.log.info("Verified for 'Any' condition with 1st column valid string and 2nd column "
                      "as dummy string! ")

    @test_step
    def test_step_3(self, report):
        """
        For all condition, for 1st column with valid string, and for 2nd column with dummy value, table should be empty
        """
        exception_string = str(("Test criteria for 'All' condition with [%s] 1st column "
                                "[%s] string and [%s] 2nd column [%s] dummy string failed!"
                                % (self.column1, self.column1_string, self.column2,
                                   self.dummy_condition_string)))
        self.log.info("Verifying test criteria for [%s] report", report)
        self.table.configure_alert()
        self.alert_window.set_value(self.column1_string)
        self.alert_window.add_condition(column_name=self.column2,
                                        column_value=self.dummy_condition_string,
                                        column_condition=self.alert_window.operator.EQUAL_TO, alert_criteria_idx=1)
        self.alert_window.select_alert_condition('all')
        criteria_table = self.get_criteria_table_content(report)
        self.close_alert_criteria_window()
        self.alert_window.cancel()
        if report == self.custom_report:
            for key, value in criteria_table.items():
                if value:
                    raise CVTestStepFailure(exception_string)
        else:
            if criteria_table != [['No matching records found']] or criteria_table == {}:
                raise CVTestStepFailure(exception_string)
        self.log.info("Verified test criteria for 'All' condition with 1st column valid string and"
                      "2nd column dummy string!")

    def test_step_4(self, report):
        """
        Verify test criteria for all condition, with valid string for 2 columns
        """
        dummy_value = '0TB'
        self.log.info("Verifying test criteria for [%s] report", report)
        self.table.set_filter(self.column1, self.column1_string)
        if report == self.custom_report:
            table_data = self.table.get_table_data()
            self.table.configure_alert()
            self.alert_window.set_value(self.column1_string)
            self.alert_window.add_condition(column_name=self.column2,
                                            column_value=dummy_value,
                                            column_condition=self.alert_window.operator.MORE_THAN,
                                            alert_criteria_idx=1,
                                            )
            criteria_table = self.get_criteria_table_content(report)
            self.close_alert_criteria_window()
            self.alert_window.cancel()
            if table_data['Job status'][0] != criteria_table['Job status'][0]:
                raise CVTestStepFailure("Test criteria with 'All' condition for [%s] 1st column with "
                                        "[%s] string, and for [%s] 2nd column with 0 string is "
                                        "failed!" % (self.column1, self.column1_string, self.column2
                                                     ))
        self.log.info("Test criteria with 'All' condition for 2 columns with valid strings is "
                      "verified!")

    def close_alert_criteria_window(self):
        """
        close alert criteria window
        """
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])

    def read_condition_string(self, report):
        """Read condition string to set to check alert criteria"""
        if report == self.custom_report:
            self.navigator.navigate_to_reports()
            self.report.access_report(report)
            _viewer = viewer.CustomReportViewer(self.admin_console)
            self.table = viewer.DataTable("Summary")
            _viewer.associate_component(self.table)
            columns = self.table.get_table_columns()
            self.column1 = columns[0]
            self.column2 = columns[1]
            row1 = self.table.get_rows_from_table_data()[0]
            self.column1_string = row1[0]
            self.column2_string = row1[1]

    def run(self):
        try:
            self.init_tc()
            for each_report in [self.custom_report]:
                self.read_condition_string(each_report)
                self.test_step_1(each_report)
                self.test_step_2(each_report)
                self.test_step_3(each_report)
                self.test_step_4(each_report)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
