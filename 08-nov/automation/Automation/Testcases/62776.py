# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Transfer schedules and alerts when user is deleted

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

Input Example:
    "testCases":
            {
                "62776":
                 {
                     "company": "Tenant admin company name",
                     "password": "Password of the user"
                 }
            }
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import mail_box, config
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Reports import cte
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_alerts import ManageAlerts
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.cte import ConfigureAlert
from Web.AdminConsole.Reports.Custom import viewer
from Reports.utils import TestCaseUtils
from Reports import reportsutils

export_type = cte.ConfigureSchedules.Format

REPORTS_CONFIG = reportsutils.get_reports_config()
CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Transfer schedules and alerts when user is deleted"
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.reports = None
        self.mail = None
        self.manage_alerts = None
        self.manage_report = None
        self.manage_schedules = None
        self.company = None
        self.tenant_admin_password = None
        self.schedule_name = "Automation_tc_62776_Schedule_%s" % str(int(time.time()))
        self.alert_name = "Automation_tc_62776_Alert_%s" % str(int(time.time()))
        self.tenant_admin_to_be_deleted = "TC_62776_to_be_deleted_user"
        self.tenant_admin = "TC_62776_transfer_user"
        self.format = export_type.HTML
        self.recipient_id = CONSTANTS.email.email_id

    def setup(self):
        """Setup function of this test case"""
        commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.company = self.tcinputs['company']
        self.tenant_admin_password = self.tcinputs['password']
        self.create_tenant_admin(self.tenant_admin_to_be_deleted, "tenant1@commvault.com")
        self.create_tenant_admin(self.tenant_admin, "tenant2@commvault.com")
        self.mail = mail_box.MailBox()
        self.mail.connect()
        self.utils = TestCaseUtils(self, username=self.commcell.commcell_username, password=commcell_password)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=commcell_password)
        self.navigator = self.admin_console.navigator
        self.manage_report = ManageReport(self.admin_console)
        self.manage_alerts = ManageAlerts(self.admin_console)
        self.manage_schedules = ManageSchedules(self.admin_console)
        self.cleanup_alert()
        self.cleanup_schedule()
        self.admin_console.logout()
        self.admin_console.login(self.company + "\\" + self.tenant_admin_to_be_deleted,
                                 self.tenant_admin_password)
        self.navigator.navigate_to_reports()
        self.reports = REPORTS_CONFIG.REPORTS.CUSTOM
        self.manage_report.access_report(self.reports[0])

    @test_step
    def cleanup_alert(self):
        """ Deletes the alert if exists """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.manage_alerts.cleanup_alerts("Automation_tc_62776")

    @test_step
    def cleanup_schedule(self):
        """ Deletes the schedule if exists """
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        self.manage_schedules.cleanup_schedules("Automation_tc_62776")

    def create_tenant_admin(self, tenant_admin, email):
        """ Create a tenant admin """
        # if user exists no need to create user/role.
        if not self.commcell.users.has_user(self.company + "\\" + tenant_admin):
            self.log.info("Creating tenant admin [%s]", tenant_admin)
            self.commcell.users.add(
                user_name=self.company + "\\" + tenant_admin,
                email=email,
                full_name=tenant_admin,
                password=self.tenant_admin_password,
                local_usergroups=[self.company + "\\" + "Tenant Admin"]
            )
        else:
            self.log.info("User [%s] already exists", tenant_admin)
            return

    @test_step
    def create_schedule(self):
        """create schedule"""
        self.log.info("Creating [%s]  schedule with the [%s] export_type for the [%s] user ",
                      self.schedule_name, self.format, self.tenant_admin_to_be_deleted)
        report = Report(self.admin_console)
        schedule = report.schedule()
        schedule.create_schedule(
            schedule_name=self.schedule_name,
            email_recipient=self.recipient_id,
            file_format=self.format
        )
        alert = Alert(self.admin_console)
        alert.close_popup()

    @test_step
    def run_schedule(self):
        """ Run schedule """
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        self.manage_schedules.run_schedules([self.schedule_name])

    @test_step
    def validate_schedule_mails(self):
        """ Validate schedule mails """
        self.utils.reset_temp_dir()
        self.log.info("verifying [%s] schedule email", self.schedule_name)
        self.utils.download_mail(self.mail, self.schedule_name)
        self.utils.get_attachment_files(ends_with=self.format)
        self.log.info("Schedule [%s] mail validated", self.schedule_name)

    @test_step
    def create_alert(self):
        """ Create alert """
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Summary")
        report_viewer.associate_component(table)
        columns = table.get_table_columns()
        if not columns:
            raise CVTestStepFailure("Report might be empty. Please verify!")
        condition_string = table.get_table_data()[columns[0]][0]
        self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                      "[%s]", self.reports[0], columns[0], condition_string)
        table.configure_alert()
        alert_window = ConfigureAlert(self.admin_console)
        alert_window.create_alert(alert_name=self.alert_name, column_name=columns[0], criteria=alert_window.operator.EQUAL_TO,
                                  column_value=condition_string, recipient_mail=self.recipient_id)
        self.admin_console.logout()

    @test_step
    def run_alert(self):
        """ Run alert """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.manage_alerts.run_alerts([self.alert_name])

    @test_step
    def validate_alert_email(self):
        """ Validate alert email """
        self.log.info("verifying [%s] alert email", self.alert_name)
        self.utils.download_mail(self.mail, subject=self.alert_name)
        self.log.info("Alert [%s] mail validated", self.alert_name)

    @test_step
    def verify_schedule_and_alert_transfer(self):
        """ Check from Db if alert and schedule transfer was successful"""
        sql_string = f"""
        select userId from CustomAlarmProps where DisplayName = '{self.alert_name}'
        """
        alert_owner = self.utils.cre_api.execute_sql(sql_string)[0]

        sql_string = f"""
        select id from umUsers where name = '{self.tenant_admin}'
        """
        transfer_user_id = self.utils.cre_api.execute_sql(sql_string)[0]

        sql_string = f"""
        select runUserId from tm_task where taskId=(select taskId 
        from tm_subtask where subTaskName = '{self.schedule_name}')
        """
        schedule_owner = self.utils.cre_api.execute_sql(sql_string)[0]

        sql_string = f"""
                select groupId from umUserGroup where userid = 
                (select id from umUsers where name = '{self.tenant_admin}')
                """
        transfer_user_group_id = self.utils.cre_api.execute_sql(sql_string)[0]

        sql_string = f"""
                select id from umUsers where description = (SELECT CONCAT('Create As for user group', 
                {transfer_user_group_id[0]}))
                """
        schedule_user_id = self.utils.cre_api.execute_sql(sql_string)[0]

        if alert_owner != transfer_user_id:
            raise CVTestStepFailure("Transfer of alert was not successful")
        if schedule_owner != schedule_user_id:
            raise CVTestStepFailure("Transfer of schedule was not successful")

    def run(self):
        """Main function for test case execution"""

        try:
            self.create_schedule()
            self.create_alert()
            self.commcell.users.delete(self.company + "\\" + self.tenant_admin_to_be_deleted,
                                       self.company + "\\" + self.tenant_admin)
            self.admin_console.login(self.company + "\\" + self.tenant_admin, self.tenant_admin_password)
            self.verify_schedule_and_alert_transfer()
            self.run_schedule()
            self.run_alert()
            self.log.info("Wait for mails to be received for 5 minutes")
            time.sleep(300)
            self.validate_schedule_mails()
            self.validate_alert_email()
            self.cleanup_alert()
            self.cleanup_schedule()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
