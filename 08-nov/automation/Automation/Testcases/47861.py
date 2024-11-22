# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics and custom report Schedule - Acceptance """
import time
from cvpysdk import schedules
from Web.AdminConsole.Components.alert import Alert
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.Reports import cte
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from AutomationUtils import mail_box
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports import reportsutils

CONSTANTS = config.get_config()
REPORTS_CONFIG = reportsutils.get_reports_config()
Format = cte.ConfigureSchedules.Format


class ScheduleDetails:
    """
    Set schedule details: report name, job id, email format
    """
    report_name = None
    format = None
    schedule_name = None
    job_id = None

    def __init__(self, report_name, file_format):
        self.schedule_name = "Automation_tc_47861_%s" % str(int(time.time()))
        self.report_name = report_name
        self.format = file_format
        self.job_id = None


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.alert = None
        self.name = "Metrics and custom report Schedule - Acceptance"
        self.show_to_user = True
        self.browser = None
        self.navigator = None
        self.report = None
        self.reports = REPORTS_CONFIG.REPORTS.DISTINCT_REPORTS
        self.recipient_id = CONSTANTS.email.email_id
        self.schedule_window = None
        self.schedule_details = []
        self.mail = None
        self.manage_schedules = None
        self.manage_reports = None
        self.admin_console = None
        self.mails_download_directory = None
        self.schedules = None
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
            self.alert = Alert(self.admin_console)
            self.manage_reports.view_schedules()
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.cleanup_schedules()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_47861_' in schedule name """
        self.manage_schedules.cleanup_schedules("Automation_tc_47861_")

    def redirect_to_report_page(self, report_name):
        """Redirect to report's page"""
        if report_name == 'Worldwide Dashboard':
            self.navigator.navigate_to_metrics()
            self.manage_reports.access_dashboard()
        elif report_name == 'Metrics Strike Count':
            self.navigator.navigate_to_metrics()
            self.manage_reports.access_report_tab()
            self.manage_reports.access_report(report_name)
        else:
            self.navigator.navigate_to_reports()
            self.manage_reports.access_report(report_name)

    @test_step
    def create_schedules(self):
        """Create schedules"""
        for each_report in self.reports:
            self.redirect_to_report_page(each_report)
            for each_file_format in [Format.PDF, Format.HTML, Format.CSV]:
                if each_report == "Worldwide Dashboard" and each_file_format == Format.CSV:
                    continue  # csv schedule for worldwide dashboard is not supported.
                schedule_window = self.report.schedule()
                self.log.info("Creating schedule for the [%s] report with [%s] file format",
                              each_report, each_file_format)

                temp_schedule_details = ScheduleDetails(each_report, each_file_format)

                schedule_window.create_schedule(
                    schedule_name=temp_schedule_details.schedule_name,
                    email_recipient=self.recipient_id,
                    file_format=each_file_format
                )
                try:
                    self.alert.close_popup()
                except Exception as exp:
                    self.log.error("Exception: %s", exp)
                    pass

                self.schedule_details.append(temp_schedule_details)
                self.log.info("Schedule created for the [%s] report with [%s] file format",
                              each_report, each_file_format)
            self.log.info("Schedule created successfully for the report [%s]", each_report)

    @test_step
    def verify_schedule_exists(self):
        """Verify schedules are created"""
        for each_schedule in self.schedule_details:
            self.log.info("Checking [%s] schedule is created", each_schedule.schedule_name)
            self.schedules.refresh()
            if not self.schedules.has_schedule(each_schedule.schedule_name):
                err_str = "[%s] schedule does not exists in db, created on [%s] report with [%s]" \
                          " file extension" % (each_schedule.schedule_name,
                                               each_schedule.report_name, each_schedule.format)
                raise CVTestStepFailure(err_str)
            else:
                self.log.info("[%s] schedule is created successfully",
                              each_schedule.schedule_name)

    @test_step
    def run_schedules(self):
        """Run schedule"""
        for each_schedule in self.schedule_details:
            _schedule = schedules.Schedule(self.commcell,
                                           schedule_name=each_schedule.schedule_name)
            self.log.info("Running [%s] schedule", each_schedule.schedule_name)
            each_schedule.job_id = _schedule.run_now()
        for each_schedule in self.schedule_details:
            job = self.commcell.job_controller.get(each_schedule.job_id)
            self.log.info("Wait for [%s] job to complete", str(job))
            if job.wait_for_completion(300):  # wait for max 5 minutes
                self.log.info("Schedule job completed with job id:[%s], for the report:[%s], with "
                              "file format:[%s]", each_schedule.job_id, each_schedule.report_name,
                              each_schedule.format)
            else:
                err_str = "Schedule job failed with job id [%s], for the report name [%s],file " \
                          "format [%s]" % (each_schedule.job_id, each_schedule.report_name,
                                           each_schedule.format)
                raise CVTestStepFailure(err_str)
        self.log.info("All schedules are completed successfully")

    @test_step
    def validate_schedule_mails(self):
        """Validate schedule mails"""
        for each_schedule in self.schedule_details:
            self.utils.reset_temp_dir()
            self.log.info("verifying [%s] schedule email for [%s] report with [%s] file extension",
                          each_schedule.schedule_name, each_schedule.report_name,
                          each_schedule.format)
            self.utils.download_mail(self.mail, each_schedule.schedule_name)
            self.utils.get_attachment_files(ends_with=each_schedule.format)
            self.log.info("Schedule [%s] mail validated for [%s] report with [%s] file extension",
                          each_schedule.schedule_name, each_schedule.report_name,
                          each_schedule.format)
            self.log.info("All schedule email's attachments are verified")

    @test_step
    def delete_schedules(self):
        """Delete schedules"""
        self.navigator.navigate_to_reports()
        self.manage_reports.view_schedules()
        for each_schedule in self.schedule_details:
            self.manage_schedules.cleanup_schedules(each_schedule.schedule_name)
        self.log.info("All schedules deleted successfully")

    def run(self):
        try:
            self.init_tc()
            self.create_schedules()
            self.verify_schedule_exists()
            self.run_schedules()
            self.mail.connect()
            self.validate_schedule_mails()
            self.delete_schedules()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
