# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
TestCase to web report and metrics operation on cluster setup
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config

from Reports.utils import TestCaseUtils
from Reports import reportsutils

from Web.Common.page_object import TestStep

from cvpysdk.metricsreport import PrivateMetrics
from cvpysdk import schedules

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.manage_schedules import ScheduleSettings
from Web.WebConsole.Reports import cte

from AutomationUtils import mail_box

REPORTS_CONFIG = reportsutils.get_reports_config()
CONSTANTS = config.get_config()


class ScheduleDetails:
    """
    Set schedule details: report name, job id, email format
    """
    report_name = None
    format = None
    schedule_name = None
    job_id = None

    def __init__(self, report_name, file_format):
        self.schedule_name = "Automation_tc_54356_%s" % str(int(time.time()))
        self.report_name = report_name
        self.format = file_format
        self.job_id = None


class TestCase(CVTestCase):
    """TestCase to web report and metrics operation on cluster setup"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Cluster Reports Acceptance"
        self.show_to_user = True
        self.private_metrics = None
        self.utils = None
        self.navigator = None
        self.export = None
        self.worldwide_reports = None
        self.browser = None
        self.webconsole = None
        self.report = None
        self.recipient_id = CONSTANTS.email.email_id
        self.report_name = "Worldwide Dashboard"
        self.schedule_details = []
        self.mail = None

    def setup(self):
        """Intializes Private metrics object required for this testcase"""
        self.utils = TestCaseUtils(self, self.inputJSONnode["commcell"]["commcellUsername"],
                                   self.inputJSONnode["commcell"]["commcellPassword"])
        self.private_metrics = PrivateMetrics(self.commcell)
        self.private_metrics.enable_all_services()

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            client = self.commcell.clients.get(self.commcell.webconsole_hostname)
            if not client.is_cluster:
                raise CVTestCaseInitFailure("Webconsole client passed is not a cluster client")
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
            self.schedules = schedules.Schedules(self.commcell)
            if not self.recipient_id:
                raise CVTestCaseInitFailure("Recipient's email id is not specified in config file")
            self.schedule_settings = ScheduleSettings(self.webconsole)
            self.worldwide_reports = REPORTS_CONFIG.REPORTS.METRICS.WORLDWIDE
            self.worldwide_reports.extend(REPORTS_CONFIG.REPORTS.CUSTOM)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_47861_' in schedule name """
        self.navigator.goto_schedules_configuration()
        self.schedule_settings.cleanup_schedules("Automation_tc_54356_")

    @test_step
    def validate_private_uploadnow(self):
        """Validates Private Metrics uploadNow operation """
        self.log.info('Initiating Private Metrics upload now')
        self.private_metrics.upload_now()
        self.private_metrics.wait_for_uploadnow_completion()
        self.log.info('Private Metrics upload now completed Successfully')

    @test_step
    def verify_worldwide_reports_export(self):
        """
        Verify worldwide exports are working fine
        """
        for each_report in self.worldwide_reports:
            self.log.info("validating export for worldwide report %s", each_report)
            self.navigator.goto_worldwide_report(each_report)
            self.utils.reset_temp_dir()
            self.verify_export_to_html()
        self.log.info("Verified export for worldwide reports")

    def verify_export_to_html(self):
        """
        Verify export to html is working fine
        """
        self.export.to_html()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("html export completed successfully")

    @test_step
    def create_schedule(self):
        """Create schedules"""
        self.navigator.goto_worldwide_dashboard()
        file_format = cte.ConfigureSchedules.Format.HTML
        schedule_window = self.report.open_schedule()
        self.log.info("Creating schedule for the [%s] report with [%s] file format",
                      self.report_name, file_format)
        temp_schedule_details = ScheduleDetails(self.report_name, file_format)
        schedule_window.set_schedule_name(temp_schedule_details.schedule_name)
        schedule_window.set_recipient(self.recipient_id)
        schedule_window.select_format(file_format)
        schedule_window.save()
        time.sleep(5)
        self.schedule_details.append(temp_schedule_details)
        self.log.info("Schedule created for the [%s] report with [%s] file format",
                      self.report_name, file_format)
        self.log.info("Schedule created successfully for the report [%s]", self.report_name)

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
    def delete_schedules(self):
        """Delete schedules"""
        self.navigator.goto_schedules_configuration()
        schedule_names = []
        for each_schedule in self.schedule_details:
            schedule_names.append(each_schedule.schedule_name)
        self.schedule_settings.delete_schedules(schedule_names)
        self.log.info("All schedules deleted successfully")

    @test_step
    def validate_schedule_mails(self):
        """Validate schedule mails"""
        self.mail = mail_box.MailBox()
        self.mail.connect()
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

    def run(self):
        try:
            self.validate_private_uploadnow()
            self._init_tc()
            self.verify_worldwide_reports_export()
            self.cleanup_schedules()
            self.create_schedule()
            self.verify_schedule_exists()
            self.run_schedules()
            self.validate_schedule_mails()
            self.delete_schedules()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            if self.mail:
                self.mail.disconnect()
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
