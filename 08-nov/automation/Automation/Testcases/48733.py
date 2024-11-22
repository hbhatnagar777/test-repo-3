# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Web Reports: Email unsubscribe """
import time

from cvpysdk import schedules

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.Reports.Metrics.components import ScheduleMail
from Web.AdminConsole.Reports import cte
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.LoginPage import LoginPage
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from AutomationUtils import mail_box
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

CONSTANTS = config.get_config()
Format = cte.ConfigureSchedules.Format


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.manage_schedules = None
        self.manage_reports = None
        self.name = "Web Reports: Email unsubscribe"
        self.show_to_user = True
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.report = None
        self.report_name = "User and user group permissions"
        self.recipient_id = CONSTANTS.email.email_id
        self.mail = None
        self.mails_download_directory = None
        self.schedules = None
        self.mail_browser = None
        self.schedule_mail = None
        self.mail_webconsole = None
        self.schedule_list = []
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.mail = mail_box.MailBox()
            self.schedules = schedules.Schedules(self.commcell)
            if not self.recipient_id:
                raise CVTestCaseInitFailure("Recipient's id is not specified in config file")

            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()

            # login to Admin Console
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.report = Report(self.admin_console)
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.view_schedules()
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.cleanup_schedules()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_48733_' in schedule name """
        self.manage_schedules.cleanup_schedules("Automation_tc_48733_")

    def redirect_to_report_page(self, report_name):
        """Redirect to report's page"""
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(report_name)

    @test_step
    def create_schedules(self):
        """Create schedules"""
        multiple_user_recipient_ids = "%s, dummy@commvault.com" % self.recipient_id
        for each_email_id in [self.recipient_id, multiple_user_recipient_ids]:
            self.redirect_to_report_page(self.report_name)
            self.log.info("Creating schedule for the [%s] report with pdf file format with [%s] "
                          "recipient id", self.report_name, each_email_id)
            schedule_name = "Automation_tc_48733_%s" % str(int(time.time()))

            schedule_window = self.report.schedule()

            schedule_window.create_schedule(schedule_name=schedule_name,
                                            email_recipient=each_email_id, file_format=Format.PDF)

            self.schedule_list.append(schedule_name)
            self.log.info("[%s] Schedule is created for the [%s] report with pdf file format "
                          "and [%s] email id", schedule_name, self.report_name, each_email_id)
        self.log.info("Schedule created successfully for the report [%s]", self.report_name)

    @test_step
    def verify_schedule_exists(self):
        """Verify schedules are created"""
        self.schedules.refresh()
        for each_schedule in self.schedule_list:
            self.log.info("Checking [%s] schedule is created", each_schedule)
            if not self.schedules.has_schedule(each_schedule):
                err_str = "[%s] schedule does not exists in db, created on [%s] report " \
                          % (each_schedule, self.report_name)
                raise CVTestStepFailure(err_str)
            self.log.info("[%s] schedule is created successfully", each_schedule)

    @test_step
    def run_schedules(self):
        """Run schedule"""
        _job_ids = []
        for each_schedule in self.schedule_list:
            _schedule = schedules.Schedule(self.commcell, schedule_name=each_schedule)
            self.log.info("Running [%s] schedule", each_schedule)
            _job_ids.append(_schedule.run_now())
        for each_job_id in _job_ids:
            job = self.commcell.job_controller.get(each_job_id)
            self.log.info("Waiting for [%s] job to complete", str(job))
            if job.wait_for_completion(300):  # wait for max 5 minutes
                self.log.info("Schedule job completed with job id:[%s], for the report:[%s]",
                              each_job_id, self.report_name)
            else:
                err_str = "[%s] Schedule job failed with job id [%s], for the report name [%s]" \
                          % (self.schedule_list[_job_ids.index(each_job_id)], each_job_id,
                             self.report_name)
                raise CVTestStepFailure(err_str)
        self.log.info("All schedules are completed successfully")

    def access_email_file(self):
        """Access email downloaded file in browser"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.mail_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.mail_browser.open()
        self.mail_browser.goto_file(file_path=html_path)
        self.schedule_mail = ScheduleMail(self.mail_browser)

    @test_step
    def unsubscribe_email(self):
        """unsubscribe emails"""
        self.mail.connect()
        for each_schedule in self.schedule_list:
            self.utils.reset_temp_dir()
            self.log.info("Downloading [%s] schedule email for [%s] report", each_schedule,
                          self.report_name)
            self.utils.download_mail(self.mail, each_schedule)
            self.log.info("Downloaded Schedule [%s] mail for [%s] report ", each_schedule,
                          self.report_name)
            self.access_email_file()
            self.schedule_mail.un_subscribe_email()

            self.mail_webconsole = AdminConsole(self.mail_browser, "")
            login_page = LoginPage(self.mail_webconsole)  # to use the current login page
            login_page.login(self.inputJSONnode['commcell']["commcellUsername"],
                            self.inputJSONnode['commcell']["commcellPassword"], is_saml=False)

            if not self.schedule_mail.is_valid_notification(self.recipient_id):
                raise Exception("Unsubscribe email is not having valid notification")

            self.log.info("Unsubscribed [%s] schedule successfully", each_schedule)

            AdminConsole.logout_silently(self.mail_webconsole)
            Browser.close_silently(self.mail_browser)

    @test_step
    def verify_delete_schedules(self):
        """Delete schedules"""
        self.navigator.navigate_to_reports()
        self.manage_reports.view_schedules()
        if self.schedule_list[0] in self.manage_schedules.get_all_schedules("Name"):
            raise CVTestStepFailure("Unsubscibed schedule didnt get deleted automatically")
        existing_email_recipient_id = self.manage_schedules.get_email_recipients(self.schedule_list[1])
        if existing_email_recipient_id == "dummy@commvault.com":
            self.manage_schedules.delete_schedules([self.schedule_list[1]])
        else:
            raise CVTestStepFailure("For [%s] schedule, expected email recipient id is "
                                    "dummy@commvault.com, But existing email recipient id:[%s]" %
                                    (self.schedule_list[1], existing_email_recipient_id))

        self.log.info("All schedules deleted successfully")

    def run(self):
        try:
            self.init_tc()
            self.create_schedules()
            self.verify_schedule_exists()
            self.run_schedules()
            self.unsubscribe_email()
            self.verify_delete_schedules()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
