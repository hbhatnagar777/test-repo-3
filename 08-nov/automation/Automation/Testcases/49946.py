# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase to Custom reports: User Security testing on CTE features with Adminconsole


Input Example:

    "testCases":
            {
                "49946":
                 {
                     "non_admin_password": "********"
                 }
            }

"""

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
from Web.WebConsole.webconsole import WebConsole

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.cte import Email
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules


_CONSTANTS = config.get_config()
_FORMAT = Email.Format
REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """TestCase to validate Custom reports: User Security testing on CTE features with
    Adminconsole"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom reports: User Security testing on CTE features with Adminconsole"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.non_admin_user = None
        self.manage_report = None
        self.navigator = None
        self.custom_report_name = None
        self.file_types = []
        self.report = None
        self.manage_schedules_web = None
        self.manage_schedules_api = None
        self.admin_console = None
        self.mail = None
        self.webconsole = None
        self.schedules = []

    def setup(self):
        """Initializes object required for this testcase"""
        self.non_admin_user = "automated_non_admin_user_49946"
        self.utils = utils.TestCaseUtils(self, self.inputJSONnode['commcell']["commcellUsername"],
                                         self.inputJSONnode['commcell']["commcellPassword"])
        self.custom_report_name = REPORTS_CONFIG.REPORTS.CUSTOM[0]
        self.file_types = [_FORMAT.PDF, _FORMAT.HTML, _FORMAT.CSV]
        self.create_non_admin_user()

    def init_tc(self):
        """Initialize browser and redirect to required report page"""
        try:
            self.mail = mail_box.MailBox()
            self.mail.connect()
            self.manage_schedules_api = schedules.Schedules(self.commcell)
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory: %s", download_directory)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.non_admin_user, password=self._tcinputs["non_admin_password"]
            )
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.manage_schedules_web = ManageSchedules(self.admin_console)
            self.navigator.navigate_to_reports()
            self.manage_report.access_report(self.custom_report_name)
            self.report = Report(self.admin_console)
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def create_non_admin_user(self):
        """create non admin user """
        user = Users(self.commcell)
        role_name = "Report_Management_49946"
        roles = Roles(self.commcell)
        # If user exists no need to create user/role.
        if not user.has_user(self.non_admin_user):
            self.log.info("Creating user [%s]", self.non_admin_user)
            user.add(user_name=self.non_admin_user, password=self._tcinputs["non_admin_password"],
                     email="AutomatedUser49946@cvtest.com")
        else:
            self.log.info("non admin user [%s] already exists", self.non_admin_user)
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
        non_admin_user = self.commcell.users.get(self.non_admin_user)
        non_admin_user.update_security_associations(entity_dictionary=entity_dictionary,
                                                    request_type='UPDATE')
        self.log.info("Non admin user [%s] is created", self.non_admin_user)

    def verify_email_attachment(self, file_type):
        """
        Verify email attachment file type
        Args:
            file_type       (String): email attachment file type
        """
        self.log.info("Verifying email attachment for file type [%s]", file_type)
        self.utils.reset_temp_dir()
        self.log.info("Verifying attachment for the report [%s] with file type [%s]",
                      self.custom_report_name, file_type)
        self.utils.download_mail(self.mail, self.custom_report_name)
        self.utils.get_attachment_files(ends_with=file_type)
        self.log.info("Attachment is verified for report [%s] with file type [%s]",
                      self.custom_report_name, file_type)
        self.log.info("Email attachment for file type [%s] is verified", file_type)

    @test_step
    def verify_email_now(self):
        """Email the admin console report, and verify email is received and it has valid attachment
        """
        for each_file_type in self.file_types:
            self.log.info("Emailing [%s] report with [%s] as attachment type",
                          self.custom_report_name, each_file_type)
            email = self.report.email()
            email.email_now(each_file_type, _CONSTANTS.email.email_id)
            self.log.info("Email is requested for [%s] report with [%s] user with [%s] as file "
                          "type", self.custom_report_name, self.non_admin_user, each_file_type)
            self.log.info("Waiting for 2 minutes for email to be received")
            time.sleep(120)
            self.verify_email_attachment(each_file_type)

    @test_step
    def verify_schedules(self):
        """Create schedule and validate the schedule mails"""
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
        self.manage_report.view_schedules()
        self.manage_schedules_web.delete_schedules(["Automation_tc_49946"])
        self.log.info("Schedules are deleted")

    def create_schedules(self):
        """Create schedules"""
        for each_file_format in self.file_types:
            schedule_name = "Automation_tc_49946_%s_%s" % (each_file_format, str(int(time.time())))
            self.log.info("Creating [%s]  schedule", schedule_name)
            schedule = self.report.schedule()
            schedule.create_schedule(schedule_name=schedule_name,
                                     email_recipient=_CONSTANTS.email.email_id,
                                     file_format=each_file_format)
            self.log.info("[%s] schedule created successfully", schedule_name)
            self.schedules.append(schedule_name)

    def verify_schedule_exists(self):
        """Verify schedules are present in commcell"""
        self.manage_schedules_api.refresh()
        for each_schedule in self.schedules:
            self.log.info("Checking [%s] schedule is created", each_schedule)
            if not self.manage_schedules_api.has_schedule(each_schedule):
                err_str = "[%s] schedule does not exists in commcell" % each_schedule
                raise CVTestStepFailure(err_str)
            else:
                self.log.info("verified [%s] schedule is present in commcell",
                              each_schedule)

    def run_schedules(self):
        """Run schedule"""
        job_ids = []
        for each_schedule in self.schedules:
            _schedule = schedules.Schedule(self.commcell,
                                           schedule_name=each_schedule)
            self.log.info("Running [%s] schedule", each_schedule)
            job_ids.append(_schedule.run_now())
        for each_schedule in self.schedules:
            job_id = job_ids[self.schedules.index(each_schedule)]
            job = self.commcell.job_controller.get(job_id)
            self.log.info("Wait for [%s] job to complete", str(job))
            if job.wait_for_completion(300):  # wait for max 5 minutes
                self.log.info("Schedule job completed with job id:[%s] for [%s] schedule",
                              job_id, each_schedule)
            else:
                err_str = "[%s] Schedule job failed with job id [%s]" % (each_schedule,
                                                                         job_id)
                raise CVTestStepFailure(err_str)
        self.log.info("All schedules are completed successfully")

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
    def verify_exports(self):
        """Verify exports"""
        for each_file_type in self.file_types:
            self.log.info("Checking export for [%s] file type", each_file_type)
            self.utils.reset_temp_dir()
            if each_file_type == _FORMAT.PDF:
                self.report.save_as_pdf()
            elif each_file_type == _FORMAT.HTML:
                self.report.save_as_html()
            elif each_file_type == _FORMAT.CSV:
                self.report.save_as_csv()
            self.utils.wait_for_file_to_download(each_file_type.lower())
            self.utils.validate_tmp_files(each_file_type.lower())
            self.log.info("[%s] export completed successfully", each_file_type)
            time.sleep(5)

    def run(self):
        try:
            self.init_tc()
            self.verify_email_now()
            self.verify_exports()
            self.verify_schedules()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.mail.disconnect()
