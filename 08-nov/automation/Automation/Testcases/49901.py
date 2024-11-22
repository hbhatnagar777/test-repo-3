# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from datetime import datetime, timezone

from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from cvpysdk.security.user import Users, User

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.users = None
        self.name = "Custom Report: (DataSet) - System tokens"
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.utils = None
        self.data = None
        self.navigator = None
        self.automation_username = "autouser_49901"
        self.automation_password = "P@ssw0rd1"
        self.expected_data_for_admin_user = None
        self.expected_data_for_automation_user = None
        self.table_data = None
        self.current_user = None
        self.current_password = None
        self.manage_reports = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.current_user = self.inputJSONnode["commcell"]["commcellUsername"]
            self.current_password = self.inputJSONnode["commcell"]["commcellPassword"]
            self.admin_console.login(self.current_user, self.current_password)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.delete_report(self.name)
            self.users = Users(self.commcell)
            self.manage_reports.add_report()
            name = self.webconsole.get_login_name().strip()
            self.create_user()
            self.expected_data_for_admin_user = {
                "UserID": [self.fetch_id(name), ],
                "UserName": [name, ],
                "Timezone": [str(datetime.now(timezone.utc).astimezone())[-6:], ]
            }
            self.expected_data_for_automation_user = self.expected_data_for_admin_user.copy()
            self.expected_data_for_automation_user["UserID"] = \
                [self.fetch_id(self.automation_username), ]
            self.expected_data_for_automation_user["UserName"] = [self.automation_username, ]

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def create_user(self):
        if self.users.has_user(self.automation_username) is False:
            self.log.info(f"[{self.automation_username}] does not exist, creating it")
            self.users.add(
                self.automation_username,
                self.automation_username,
                "reports@testing.com",
                None,
                self.automation_password
            )
            user = User(self.commcell, self.automation_username)
            user.add_usergroups(["Master"])

    def fetch_id(self, username):
        return str(self.utils.cre_api.execute_sql(
            f"""SELECT id
                FROM UMUsers
                where login ='{username}'
                """,
            desc=f"Get id of username [{username}]"
        )[0][0])

    @test_step
    def create_dataset_using_sys_params(self):
        """Create dataset using system parameters"""

        report_builder = builder.ReportBuilder(self.webconsole)
        report_builder.set_report_name(self.name)
        database_dataset = builder.Datasets.DatabaseDataset()
        report_builder.add_dataset(database_dataset)
        database_dataset.set_dataset_name("AutomationDataSet")
        database_dataset.set_sql_query(
            """
            SELECT
                @sys_userid [UserID],
                @sys_username [UserName],
                @sys_locale [Locale],
                @sys_timezone [Timezone]
            """
        )
        preview_data = database_dataset.get_preview_data()
        if "Locale" in preview_data:
            del preview_data["Locale"]
        if self.expected_data_for_admin_user != preview_data:
            self.log.error(
                f"Expected data [{self.expected_data_for_admin_user}]"
                f"\nReceived[{preview_data}]"
            )
            raise CVTestStepFailure("Unexpected data during preview")
        database_dataset.save()
        table = builder.DataTable("AutomationTable")
        report_builder.add_component(table, database_dataset)
        table.add_column_from_dataset()
        report_builder.save(deploy=True)

    def get_data_for_automation_admin(self):
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        AdminConsole.logout_silently(self.admin_console)
        self.admin_console.login(self.automation_username, self.automation_password)
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.name)
        table = viewer.DataTable("AutomationTable")
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        report_viewer.associate_component(table)
        self.table_data = table.get_table_data()

    @test_step
    def validate_user_id_and_username_on_table(self):
        """
        @sys_userid and @sys_username should show ID and username of the logged in user
        """
        if self.table_data["UserID"] != self.expected_data_for_automation_user["UserID"]:
            self.log.error("\nReceived %s\nExpected %s" % (
                self.table_data["UserID"][0], self.expected_data_for_automation_user["UserID"]
            ))
            raise CVTestStepFailure("Validation of userID failed")
        if self.table_data["UserName"] != self.expected_data_for_automation_user["UserName"]:
            self.log.error("\nReceived %s\nExpected %s" % (
                self.table_data["UserName"], self.expected_data_for_automation_user["UserName"]
            ))
            raise CVTestStepFailure("Validation of UserName failed")

    @test_step
    def validate_timezone(self):
        """@sys_timezone should show the timezone of the browser"""
        if self.table_data["Timezone"] != self.expected_data_for_automation_user["Timezone"]:
            self.log.error("\nReceived %s\nExpected %s" % (
                self.table_data["Timezone"], self.expected_data_for_automation_user["Timezone"]
            ))
            raise CVTestStepFailure("Validation of timezone failed")

    @test_step
    def validate_locale(self):
        """@sys_locale should show the currently active language"""
        if self.table_data["Locale"]:
            if not self.table_data["Locale"][0].startswith("en"):
                self.log.error("\nReceived %s\nExpected %s" % (
                    self.table_data["Locale"], self.expected_data_for_automation_user["Locale"]
                ))
                raise CVTestStepFailure("@sys_locale validation failed")

    @test_step
    def delete_report_and_user(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)
        self.users.delete(self.automation_username, new_user=self.current_user)

    def run(self):
        try:
            self.init_tc()
            self.create_dataset_using_sys_params()
            self.get_data_for_automation_admin()
            self.validate_user_id_and_username_on_table()
            self.validate_timezone()
            self.validate_locale()
            self.delete_report_and_user()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
