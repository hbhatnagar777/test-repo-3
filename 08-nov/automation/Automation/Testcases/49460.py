# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase to Metrics reports: User Security testing on CTE features
"""
import datetime
import time

from cvpysdk.security.user import Users
from cvpysdk.security.role import Roles
from cvpysdk import schedules

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import mail_box
from AutomationUtils import config

from Reports import reportsutils
from Reports.utils import TestCaseUtils
from Reports import utils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from Web.AdminConsole.Reports.manage_alerts import ManageAlerts
from Web.AdminConsole.Reports.cte import Email
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.manage_schedules import ScheduleSettings
from Web.WebConsole.Reports.manage_alerts import AlertSettings
from Web.WebConsole.Reports.Metrics.components import AlertMail
from Web.WebConsole.Reports.navigator import Navigator

_CONSTANTS = config.get_config()
_FORMAT = Email.Format
REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """TestCase to Metrics reports: User Security testing on CTE features"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.admin_console = None
        self.name = "Metrics reports: User Security testing on CTE features"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.non_admin_user = None
        self.non_admin_password = None
        self.manage_report = None
        self.metrics_report_name = REPORTS_CONFIG.REPORTS.METRICS.TABLE_EXPORT[0]
        self.file_types = []
        self.report = None
        self.reports = None
        self.export = None
        self.manage_schedules = None
        self.manage_schedule = None
        self.manage_alerts = None
        self.mail = None
        self.webconsole = None
        self.manage_reports = None
        self.schedule_settings = None
        self.schedule_name = None
        self.schedules = []
        self.alerts = []
        self.mail_browser = None
        self.alert_mail = None
        self.alert_condition_string = None
        self.navigator = None
        self.alert_settings = None
        self.alert_name = None
        self.full_username = None

    def setup(self):
        """Initializes object required for this testcase"""
        self.non_admin_user = "automated_non_admin_user_49460"
        self.non_admin_password = "Tc49460##"
        self.utils = utils.TestCaseUtils(self)
        self.file_types = [_FORMAT.PDF, _FORMAT.HTML, _FORMAT.CSV]
        self.create_non_admin_user()

    def init_tc(self):
        """Initialize browser and redirect to required report page"""
        try:
            self.mail = mail_box.MailBox()
            self.mail.connect()
            self.manage_schedules = schedules.Schedules(self.commcell)
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory: %s", download_directory)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.full_username, password=self.non_admin_password)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.reports = Report(self.admin_console)
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.view_schedules()
            self.manage_schedule = ManageSchedules(self.admin_console)
            self.manage_alerts = ManageAlerts(self.admin_console)
            self.cleanup()
            self.navigator.navigate_to_reports()
            self.manage_reports.access_report(self.metrics_report_name)
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def create_non_admin_user(self):
        """create non admin user """
        user = Users(self.commcell)
        user_obj = user.get(self.inputJSONnode['commcell']["commcellUsername"])
        company_name = user_obj.user_company_name
        if not company_name == 'commcell':
            self.full_username = company_name + '\\' + self.non_admin_user
        else:
            self.full_username = self.non_admin_user
        role_name = "Report_Management_49460"
        roles = Roles(self.commcell)
        # If user exists no need to create user/role.
        if not user.has_user(self.full_username):
            self.log.info("Creating user [%s]", self.non_admin_user)
            user.add(user_name=self.non_admin_user, password=self.non_admin_password,
                     email="AutomatedUser@cvtest.com")
        else:
            self.log.info("Non admin user [%s] already exists", self.full_username)
            return
        # Create role
        if not roles.has_role(role_name):
            roles.add(rolename=role_name, permission_list=["Report Management"])
        entity_dictionary = {
            'assoc1': {
                'clientName': [self.commcell.commserv_name],
                'role': [role_name]
            }
        }
        non_admin_user = self.commcell.users.get(self.full_username)
        non_admin_user.update_security_associations(entity_dictionary=entity_dictionary,
                                                    request_type='UPDATE')
        self.log.info("Non admin user [%s] is created", self.full_username)

    def verify_email_attachment(self, file_type):
        """
        Verify email attachment file type
        Args:
            file_type       (String): email attachment file type
        """
        self.utils.reset_temp_dir()
        self.log.info("Verifying attachment for the report [%s] with file type [%s]",
                      self.metrics_report_name, file_type)
        self.utils.download_mail(self.mail, self.metrics_report_name)
        self.utils.get_attachment_files(ends_with=file_type)
        self.log.info("Attachment is verified for report [%s] with file type [%s]",
                      self.metrics_report_name, file_type)

    @test_step
    def verify_email_now(self):
        """Email metrics report, and verify email is received and it has valid attachment"""
        for each_file_type in self.file_types:
            self.log.info("Emailing [%s] report with [%s] as attachment type",
                          self.metrics_report_name, each_file_type)
            self.navigator.navigate_to_reports()
            self.manage_reports.access_report(self.metrics_report_name)
            email = self.reports.email()
            email.email_now(each_file_type, _CONSTANTS.email.email_id)
            self.log.info("Email is requested for [%s] report with [%s] user with [%s] as"
                          " file type", self.metrics_report_name, self.full_username,
                          each_file_type)

            job_id = email.get_job_id()
            job = self.commcell.job_controller.get(job_id)  # Creates job object

            if not job.wait_for_completion(300):  # wait for max 5 minutes
                err_str = "Email job failed with job id [%s], for the report name [%s]," \
                          "file format [%s]" % (job_id, self.metrics_report_name, each_file_type)
                raise CVTestStepFailure(err_str)

            self.log.info("Email job completed with job id:[%s], for the report:[%s], "
                          "with file format:[%s]", job_id, self.metrics_report_name,
                          each_file_type)
            self.verify_email_attachment(each_file_type)

    def validate_schedule_mails(self):
        """Validate schedule mails"""
        for each_schedule in self.schedules:
            self.utils.reset_temp_dir()
            file_type = self.file_types[self.schedules.index(each_schedule)]
            self.log.info("verifying [%s] schedule email", each_schedule)
            self.utils.download_mail(self.mail, each_schedule)
            self.utils.get_attachment_files(ends_with=file_type)
            self.log.info("Schedule [%s] mail validated for [%s] file attachment",
                          each_schedule, file_type)
        self.log.info("All schedule email's attachments are verified")

    @test_step
    def verify_schedules(self):
        """Create schedule and validate the schedule mails"""
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.metrics_report_name)
        self.create_schedules()
        self.verify_schedule_exists()
        self.run_schedules()
        self.log.info("Wait for 2 minutes for mail to be received")
        time.sleep(120)
        self.validate_schedule_mails()
        self.delete_schedules()

    def delete_schedules(self):
        """Delete the schedules"""
        self.navigator.navigate_to_reports()
        self.manage_reports.view_schedules()
        for each_schedule in self.schedules:
            self.manage_schedules.cleanup_schedules(each_schedule)

    def cleanup(self):
        self.manage_schedule.cleanup_schedules("Automation_tc_49460_")
        self.navigator.navigate_to_reports()
        self.manage_reports.view_alerts()
        self.manage_alerts.cleanup_alerts("Automation_tc_49460_")

    def create_schedules(self):
        """Create schedules"""
        for each_file_format in self.file_types:
            schedule_name = "Automation_tc_49460_%s_%s" % \
                            (each_file_format, str(int(time.time())))
            self.log.info("Creating [%s]  schedule", schedule_name)
            schedule_window = self.reports.schedule()
            schedule_window.create_schedule(schedule_name=schedule_name,
                                            email_recipient=_CONSTANTS.email.email_id,
                                            file_format=each_file_format)
            self.log.info("[%s] schedule created successfully", schedule_name)
            self.schedules.append(schedule_name)

    def run_schedules(self):
        """Run schedule"""
        job_ids = []
        for each_schedule in self.schedules:
            _schedule = schedules.Schedule(self.commcell,
                                           schedule_name=each_schedule)
            self.log.info("Running [%s] schedule", each_schedule)
            job_ids.append(_schedule.run_now())
            time.sleep(5)
        for each_schedule in self.schedules:
            job_id = job_ids[self.schedules.index(each_schedule)]
            job = self.commcell.job_controller.get(job_id)
            self.log.info("Wait for [%s] job to complete", str(job))
            if job.wait_for_completion(300):  # wait for max 5 minutes
                self.log.info("Schedule job completed with job id:[%s] for [%s] schedule",
                              job_id, each_schedule)
            else:
                err_str = "[%s] Schedule job failed with job id [%s]" % \
                          (each_schedule, job_id)
                raise CVTestStepFailure(err_str)
        self.log.info("All schedules are completed successfully")

    def verify_schedule_exists(self):
        """Verify schedules are present in commcell"""
        self.manage_schedules.refresh()
        for each_schedule in self.schedules:
            self.log.info("Checking [%s] schedule is created", each_schedule)
            if not self.manage_schedules.has_schedule(each_schedule):
                err_str = "[%s] schedule does not exists in commcell" % each_schedule
                raise CVTestStepFailure(err_str)
            else:
                self.log.info("verified [%s] schedule is present in commcell",
                              each_schedule)

    @test_step
    def verify_exports(self):
        """Verify exports"""
        for each_file_type in self.file_types:
            self.log.info("Checking export for [%s] file type", each_file_type)
            self.utils.reset_temp_dir()
            if each_file_type == _FORMAT.PDF:
                self.export.to_pdf()
            elif each_file_type == _FORMAT.HTML:
                self.export.to_html()
            elif each_file_type == _FORMAT.CSV:
                self.export.to_csv()
            self.utils.wait_for_file_to_download(each_file_type.lower())
            self.utils.validate_tmp_files(each_file_type.lower())
            self.log.info("[%s] export completed successfully", each_file_type)

    def access_email_file(self):
        """Access email downloaded file in browser"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.mail_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.mail_browser.open()
        self.mail_browser.goto_file(file_path=html_path)
        self.alert_mail = AlertMail(self.mail_browser)

    def get_report_content(self, filter_value):
        """Read report data"""
        table = self.report.get_tables()[0]
        column_name = table.get_visible_column_names()[0]
        table.set_filter(column_name, filter_value)
        return table.get_data()

    def validate_alert_email(self):
        """Validate alert email"""
        self.utils.reset_temp_dir()
        self.utils.download_mail(self.mail, subject=self.alert_name)
        self.access_email_file()
        web_report_table_data = self.get_report_content(self.alert_condition_string)
        mail_report_name = self.alert_mail.get_report_name()
        if mail_report_name != self.metrics_report_name:
            raise CVTestStepFailure("Report names are not matching with mail content, "
                                    "report name in mail:%s,report name in webconsole:%s" %
                                    (mail_report_name, self.metrics_report_name))

        mail_table_data = self.alert_mail.get_table_data()
        if mail_table_data != web_report_table_data:
            raise CVTestStepFailure("Table data in report is not matching with mail "
                                    "content, table data in mail:%s,report data in "
                                    "webconsole:%s" % (str(mail_table_data),
                                                       str(web_report_table_data)))
        self.log.info("Email content is matched successfully with report content for "
                      "the report [%s]", self.metrics_report_name)

    def create_alert(self):
        """Create alert"""
        table = self.report.get_tables()[0]
        column_name = table.get_visible_column_names()[0]
        self.alert_name = "Automation_tc_49460_%s" % str(int(time.time()))
        self.alert_condition_string = table.get_data_from_column(column_name)[0]

        now = datetime.datetime.now()
        now_plus_2mins = now + datetime.timedelta(minutes=3)
        hours = str(int(datetime.datetime.strftime(now_plus_2mins, "%I")))
        minutes = str(int(datetime.datetime.strftime(now_plus_2mins, "%M")))
        ampm = str(datetime.datetime.strftime(now_plus_2mins, "%p"))
        if len(minutes) == 1:
            minutes = "0" + minutes

        self.log.info("Creating [%s] alert for [%s] report for [%s] column with condition "
                      "string:[%s] with time is set as %s:%s:%s", self.alert_name,
                      self.metrics_report_name, column_name, self.alert_condition_string, hours,
                      minutes, ampm)
        alert_window = table.open_alert()
        alert_window.set_time(hours, minutes, ampm)
        alert_window.create_alert(alert_name=self.alert_name, column_name=column_name,
                                  column_value=self.alert_condition_string)
        self.log.info("Alert [%s] created successfully on [%s] report ", self.alert_name,
                      self.metrics_report_name)

    def delete_alerts(self):
        """
        Delete alert
        """
        self.navigator.navigate_to_reports()
        self.manage_reports.view_alerts()
        self.manage_alerts.delete_alerts([self.alert_name])

    @test_step
    def verify_alerts(self):
        """Create alert, verify alert mail received"""
        self.create_alert()
        self.log.info("Wait for 3 minutes for alert mails to be received")
        time.sleep(180)
        self.validate_alert_email()
        self.delete_alerts()

    def run(self):
        try:
            self.init_tc()
            self.verify_email_now()
            self.verify_exports()
            self.verify_alerts()
            self.verify_schedules()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
            Browser.close_silently(self.mail_browser)
            self.mail.disconnect()
