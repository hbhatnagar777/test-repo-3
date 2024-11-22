# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: ESP Monthly and Quarterly ppt schedule validation"""

import time
from cvpysdk import schedules
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole

from Web.WebConsole.Reports import cte
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.manage_schedules import ScheduleSettings

from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies

from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import mail_box
from AutomationUtils import config

from Reports.utils import TestCaseUtils

CONSTANTS = config.get_config()
Format = cte.ConfigureSchedules.Format


class ScheduleDetails:
    """
    Set schedule details: report name, job id, email format
    """
    format = None
    schedule_name = None
    job_id = None

    def __init__(self,  file_format):
        self.schedule_name = "Automation_tc_59254_%s" % str(int(time.time()))
        self.format = file_format
        self.job_id = None


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics:ESP QBR schedule validation"
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.table = None
        self.viewer = None
        self.companies = None
        self.tcinputs = {
            "CommCellGroupName": None
        }
        self.recipient_id = CONSTANTS.email.email_id
        self.schedule_window = None
        self.schedule_details = []
        self.mail = None
        self.mails_download_directory = None
        self.schedules = None
        self.schedule_settings = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.mail = mail_box.MailBox()
            self.mail.connect()
            self.schedules = schedules.Schedules(self.commcell)
            if not self.recipient_id:
                raise CVTestCaseInitFailure("Recipient's id is not specified in config file")

            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.viewer = viewer.CustomReportViewer(self.webconsole)
            self.table = viewer.DataTable("")
            self.companies = RegisteredCompanies(self.webconsole)
            self.webconsole.goto_reports()
            self.schedule_settings = ScheduleSettings(self.webconsole)
            self.cleanup_schedules()
            self.access_company_page()
            self.report = MetricsReport(self.webconsole)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def access_company_page(self):
        """
        Navigate to the CommCell group
        """
        self.navigator.goto_companies()
        self.viewer.associate_component(self.table)
        self.companies.access_company(self.tcinputs["CommCellGroupName"])
        time.sleep(3)

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_59254_' in schedule name """
        self.navigator.goto_schedules_configuration()
        self.schedule_settings.cleanup_schedules("Automation_tc_59254_")

    @test_step
    def create_schedules(self, support_account_manager=None, technical_account_manager=None):
        """Create schedules"""
        for each_file_format in [Format.QBR_MONTHLY, Format.QBR_QUARTERLY]:
            schedule_window = self.report.open_schedule()

            self.log.info("Creating schedule for the QBR report with [%s] file format", each_file_format)
            temp_schedule_details = ScheduleDetails(each_file_format)
            schedule_window.set_schedule_name(temp_schedule_details.schedule_name)
            schedule_window.set_recipient(self.recipient_id)
            schedule_window.select_format(each_file_format)
            if each_file_format is Format.QBR_MONTHLY:
                schedule_window.set_support_manager_schedule(support_account_manager)
            elif each_file_format is Format.QBR_QUARTERLY:
                schedule_window.set_support_manager_schedule(support_account_manager)
                schedule_window.set_technical_manager_schedule(technical_account_manager)
            schedule_window.save()
            time.sleep(5)
            self.schedule_details.append(temp_schedule_details)
            self.log.info("Schedule created for the QBR report with [%s] file format"
                          , each_file_format)

    @test_step
    def verify_schedule_exists(self):
        """Verify schedules are created"""
        for each_schedule in self.schedule_details:
            self.log.info("Checking [%s] schedule is created", each_schedule.schedule_name)
            self.schedules.refresh()
            if not self.schedules.has_schedule(each_schedule.schedule_name):
                err_str = "[%s] schedule does not exists in db, created on QBR report with [%s]" \
                          " file extension" % (each_schedule.schedule_name, each_schedule.format)
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
            time.sleep(5)
        for each_schedule in self.schedule_details:
            job = self.commcell.job_controller.get(each_schedule.job_id)
            self.log.info("Wait for [%s] job to complete", str(job))
            if job.wait_for_completion(300):  # wait for max 5 minutes
                self.log.info("Schedule job completed with job id:[%s], for the QBR report, with "
                              "file format:[%s]", each_schedule.job_id, each_schedule.format)
            else:
                err_str = "Schedule job failed with job id [%s], for the QBR report name file " \
                          "format [%s]" % (each_schedule.job_id, each_schedule.format)
                raise CVTestStepFailure(err_str)
        self.log.info("All schedules are completed successfully")

    @test_step
    def validate_schedule_mails(self):
        """Validate schedule mails"""
        for each_schedule in self.schedule_details:
            self.utils.reset_temp_dir()
            self.log.info("verifying [%s] schedule email for the QBR report with [%s] file extension",
                          each_schedule.schedule_name, each_schedule.format)
            self.utils.download_mail(self.mail, each_schedule.schedule_name)
            self.utils.get_attachment_files(ends_with=".pptx")
            self.log.info("Schedule [%s] mail validated for the QBR report with [%s] file extension",
                          each_schedule.schedule_name, each_schedule.format)
            self.log.info("All schedule email's attachments are verified")

    @test_step
    def delete_schedules(self):
        """Delete schedules"""
        self.navigator.goto_schedules_configuration()
        schedule_names = []
        for each_schedule in self.schedule_details:
            schedule_names.append(each_schedule.schedule_name)
        self.schedule_settings.delete_schedules(schedule_names)
        self.log.info("All schedules deleted successfully")

    def run(self):
        try:
            self.init_tc()
            self.create_schedules(support_account_manager='account manager',
                                  technical_account_manager='technical manager')
            self.verify_schedule_exists()
            self.run_schedules()
            self.validate_schedule_mails()
            self.delete_schedules()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)