# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.utils import CustomReportUtils

from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
    CVWebAutomationException
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom.builder import ReportBuilder

from Web.WebConsole.Reports.cte import CustomSecurity
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """Admin Console: Security roles for report"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Admin Console: Security roles for report"
        self.utils = None
        self.browser = None
        self.browser_2 = None
        self.webconsole = None
        self.webconsole_2 = None
        self.login_obj = None
        self.default_report = None
        self.report = None
        self.navigator = None
        self.navigator2 = None
        self.admin_console_2 = None
        self.manage_report = None
        self.manage_report_2 = None
        self.custom_security = None
        self.automation_username = "tc50970"
        self.automation_password = None

    def init_tc(self):
        """Initializes the testcase"""
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                           password=self.inputJSONnode['commcell']['commcellPassword'])
            self.automation_password = self.tcinputs["auto_create_user_pwd"]
            self.clean_up()
            self.create_user()
            self.init_user_browser()
        except Exception as excep:
            raise CVTestCaseInitFailure from excep

    def clean_up(self):
        """Deletes the existing user and roles"""
        if self.commcell.roles.has_role("Report Management"):
            self.log.info("Deleting role 'Report Management'")
            self.commcell.roles.delete("Report Management")

        if self.commcell.roles.has_role("Add Report"):
            self.log.info("Deleting role 'Add Report'")
            self.commcell.roles.delete("Add Report")

        if self.commcell.roles.has_role("Query Datasource"):
            self.log.info("Deleting role 'Query Datasource'")
            self.commcell.roles.delete("Query Datasource")

        if self.commcell.users.has_user(self.automation_username):
            self.log.info("Deleting existing user")
            self.commcell.users.delete(self.automation_username, "admin")

    def init_user_browser(self):
        """Initial configuration for the test case."""
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.utils.webconsole = self.webconsole
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.automation_username, password=self.automation_password)
        self.navigator = self.admin_console.navigator

    def init_admin_browser(self):
        """Initial configuration for the test case."""
        self.browser_2 = BrowserFactory().create_browser_object(name="Admin Browser")
        self.browser_2.open()
        self.webconsole_2 = WebConsole(self.browser_2, self.commcell.webconsole_hostname)
        self.utils.webconsole = self.webconsole_2
        self.admin_console_2 = AdminConsole(self.browser_2, self.commcell.webconsole_hostname)
        self.admin_console_2.login()
        self.navigator2 = self.admin_console_2.navigator

    def create_user(self):
        """Creates user and roles"""
        self.commcell.roles.add("Report Management", ["Report Management"])
        self.commcell.roles.add("Add Report", ["Add Report"])
        self.commcell.roles.add("Query Datasource", ["Query Datasource"])

        self.commcell.users.add(
            self.automation_username,
            self.automation_username,
            "reports@testing.com",
            None,
            self.automation_password
        )
        dict_ = {"assoc1":
                 {
                     'clientName': [self.commcell.commserv_name],
                     'role': ["Report Management"]
                 }


                 }
        self.commcell.users.get(self.automation_username).update_security_associations(
            dict_, "UPDATE"
        )

    @test_step
    def verify_inability_to_add_report(self):
        """Verifies the user is unable to add report"""
        self.manage_report = ManageReport(self.admin_console)
        self.navigator.navigate_to_reports()
        try:
            self.manage_report.add_report()
            raise CVTestStepFailure(
                f"User {self.automation_username} is able to add report without 'Add Report' Role."
            )
        except CVWebAutomationException as excep:
            if "Add report is not available" not in str(excep):
                raise CVTestStepFailure(
                    f"Expected 'Add report is not available' in exception.\n Received {excep}"
                )

    @test_step
    def addition_edition_deletion_of_report_created_by_user(self):
        """Verifies whether the user is able add/edit/delete report created by him
         but unable to edit or delete report of others"""
        dict_ = {"assoc1":
                 {
                     'commCellName': [self.commcell.commserv_name],
                     'role': ["Add Report"]
                 },
                 "assoc2":
                 {
                     'commCellName': [self.commcell.commserv_name],
                     'role': ["Query Datasource"]
                 }
                 }
        self.commcell.users.get(self.automation_username).update_security_associations(
            dict_, "UPDATE"
        )
        self.navigator.logout()
        self.admin_console.login(self.automation_username, self.automation_password)
        self.navigator.navigate_to_reports()
        try:
            self.manage_report.add_report()
        except CVWebAutomationException:
            raise CVTestStepFailure(
                f"User {self.automation_username} is not able to add report "
                f"after 'Add Report' Role."
            )
        self.default_report = DefaultReport(self.utils)
        self.default_report.build_default_report(open_report=False)
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])

        self.navigator.refresh_page()
        self.manage_report.access_report(self.name)
        self.report = Report(self.admin_console)
        try:
            self.report.edit_report()
        except CVWebAutomationException as exception:
            raise CVTestStepFailure(exception)
        self.default_report.report_builder.set_report_description("Edited")
        self.default_report.report_builder.save()
        self.default_report.report_builder.deploy()
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
        try:
            self.report.delete_report()
        except CVWebAutomationException as exception:
            raise CVTestStepFailure(exception)

        # Verify immutability of already existing report for non admin user with 'Add Report' role
        self.manage_report.access_report("SLA")
        try:
            self.report.edit_report()
            raise CVTestStepFailure(
                f"User {self.automation_username} is able to edit report with only 'Add Report'.")
        except CVWebAutomationException:
            pass

        try:
            self.report.delete_report()
            raise CVTestStepFailure(
                f"User {self.automation_username} is able to delete report with"
                f" only 'Add Report'."
            )
        except CVWebAutomationException:
            pass

    @test_step
    def non_accessibility_of_report_added_by_admin_user(self):
        """Admin user adds a new report and the user shouldn't be able to see it"""
        self.init_admin_browser()
        self.manage_report_2 = ManageReport(self.admin_console_2)
        self.navigator2.navigate_to_reports()
        self.manage_report_2.add_report()

        self.default_report = DefaultReport(self.utils)
        self.default_report.build_default_report(open_report=False)
        self.browser_2.driver.close()
        self.browser_2.driver.switch_to.window(self.browser_2.driver.window_handles[-1])

        self.navigator.navigate_to_reports()
        self.navigator.refresh_page()
        if self.manage_report.is_report_exists(self.name):
            raise CVTestStepFailure(
                "The report created by admin is visible to non admin user before sharing")

    @test_step
    def validate_visibility_of_report_with_execute_permission(self):
        """Admin grants execute permission on one of the reports to the user"""

        self.navigator2.refresh_page()
        self.manage_report_2.report_permissions(self.name)
        self.custom_security = CustomSecurity(self.webconsole_2)
        self.custom_security.associate_security_permission([self.automation_username])
        self.custom_security.update()

        self.navigator.refresh_page()
        self.navigator.navigate_to_reports()
        self.manage_report.access_report(self.name)
        try:
            self.report.edit_report()
            raise CVTestStepFailure(
                f"User {self.automation_username} is able to edit report with "
                f"only 'Execute Permission'."
            )
        except CVWebAutomationException:
            pass

        try:
            self.report.delete_report()
            raise CVTestStepFailure(
                f"User {self.automation_username} is able to delete report with "
                f"only 'Execute Permission'."
            )
        except CVWebAutomationException:
            pass

    @test_step
    def validate_edition_of_report_with_edit_permission(self):
        """Admin grants edit permission on the same report to the same user"""
        self.manage_report_2.report_permissions(self.name)
        self.custom_security.modify_permissions(
            self.automation_username, [CustomSecurity.Permissions.EDIT_REPORT]
        )
        self.custom_security.update()

        AdminConsole.logout_silently(self.admin_console)
        self.admin_console.login(self.automation_username, self.automation_password)
        self.navigator.navigate_to_reports()
        self.manage_report.access_report(self.name)
        try:
            self.report.edit_report()
        except CVWebAutomationException:
            raise CVTestStepFailure(
                f"User {self.automation_username} is unable to edit report "
                f"with 'Execute,Edit' Permission."
            )
        builder = ReportBuilder(self.webconsole)
        builder.set_report_description("Edited 2")
        builder.save()
        builder.deploy()
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
        try:
            self.report.delete_report()
            raise CVTestStepFailure(
                f"User {self.automation_username} is able to delete report with "
                f"only 'Execute,Edit' Permission."
            )
        except CVWebAutomationException:
            pass

    @test_step
    def validate_deletion_of_report_with_delete_permission(self):
        """Admin grants delete permission on the same report to the same user"""
        self.manage_report_2.report_permissions(self.name)
        self.custom_security.modify_permissions(
            self.automation_username, [CustomSecurity.Permissions.DELETE_REPORT]
        )
        self.custom_security.update()

        self.navigator.refresh_page()
        try:
            self.report.edit_report()
        except CVWebAutomationException:
            raise CVTestStepFailure(
                f"User {self.automation_username} is unable to edit report "
                f"with 'Execute,Edit,Delete' Permissions."
            )
        builder = ReportBuilder(self.webconsole)
        builder.set_report_description("Edited 3")
        builder.save()
        builder.deploy()
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
        try:
            self.report.delete_report()
        except CVWebAutomationException:
            raise CVTestStepFailure(
                f"User {self.automation_username} is unable to delete report "
                f"with 'Execute,Edit,Delete' Permission."
            )

    def run(self):
        try:
            self.init_tc()
            self.verify_inability_to_add_report()
            self.addition_edition_deletion_of_report_created_by_user()
            self.non_accessibility_of_report_added_by_admin_user()
            self.validate_visibility_of_report_with_execute_permission()
            self.validate_edition_of_report_with_edit_permission()
            self.validate_deletion_of_report_with_delete_permission()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            WebConsole.logout_silently(self.webconsole_2)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.browser_2)
