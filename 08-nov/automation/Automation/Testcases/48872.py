# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: Executive Summary Report PPT generation """
import time

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.cte import ConfigureSchedules
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.AdminConsole.Reports.manage_schedules import ManageSchedules

from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils import mail_box
from AutomationUtils import config
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase

from Reports.reportsutils import PPTManager
from Reports.utils import TestCaseUtils

from cvpysdk import schedules


CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()
    REPORT_NAME = 'Activity'
    MIN_FILE_SIZE = 340000  # BYTES
    SCHEDULE_NAME = 'Automation_tc_48872_' + str(int(time.time()))
    FILE_TYPE = "pptx"

    def __init__(self):
        super(TestCase, self).__init__()
        self._ppt = None
        self.name = "Executive Summary Report PPT generation"
        self.log = logger.get_log()
        self.browser = None
        self.report = None
        self.navigator = None
        self.export = None
        self.schedule_email_id = None
        self.schedules = None
        self.schedule_settings = None
        self.mail = None
        self.admin_console = None
        self.commcell_password = None
        self.expected_number_of_slides_executive = None
        self.executive_slides = None
        self.utils = TestCaseUtils(self)

    def _init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.mail = mail_box.MailBox()
            self.mail.connect()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.cleanup_schedules()
            self.schedule_email_id = CONSTANTS.email.email_id
            self.schedules = schedules.Schedules(self.commcell)
            self.executive_slides = self.tcinputs['EXECUTIVE_SLIDES']
            self.expected_number_of_slides_executive = len(self.executive_slides)
            self.commcell_group = [self.commcell.commserv_name]
            self.navigator.navigate_to_metrics()
            self.manage_report.access_report_tab()
            self.manage_report.access_report(TestCase.REPORT_NAME)
            self.report = Report(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_48872_' in schedule name  """
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        self.manage_schedules.cleanup_schedules("Automation_tc_48872_")

    @test_step
    def _export_executive_summary_report(self):
        """
        Generates executive summary report ppt
        """
        self.report.to_executive_summary(values=self.commcell_group)

    @test_step
    def _validate_schedule(self):
        """
        Validate ppt schedules at commcell level
        """
        self.navigator.navigate_to_metrics()
        self.manage_report.select_commcell_name(self.commcell.commserv_name)
        self.manage_report.access_report_tab()
        self.manage_report.access_report(TestCase.REPORT_NAME)
        self.log.info("Creating schedule [%s]", TestCase.SCHEDULE_NAME)
        schedule = self.report.schedule()
        schedule.create_schedule(TestCase.SCHEDULE_NAME, self.schedule_email_id,
                                 ConfigureSchedules.Format.EXECUTIVE_SUMMARY,
                                 )
        self.log.info("Created schedule successfully")

        self.schedules.refresh()
        if not self.schedules.has_schedule(TestCase.SCHEDULE_NAME):
            err_str = "[%s] schedule does not exists. Please verify schedule is created " \
                      "successfully"
            raise CVTestStepFailure(err_str)

        self.log.info("Running the schedule [%s]", TestCase.SCHEDULE_NAME)
        _schedule = schedules.Schedule(self.commcell,
                                       schedule_name=TestCase.SCHEDULE_NAME)
        _job_id = _schedule.run_now()
        _job = self.commcell.job_controller.get(_job_id)

        self.log.info("Wait for [%s] job to complete", str(_job))
        if _job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info(f"Schedule job completed with job id: {_job_id}")
        else:
            err_str = f"Schedule job failed with job id {_job_id}"
            raise CVTestStepFailure(err_str)

        self.log.info("verify scheduled report mail has proper attachment")
        self.utils.reset_temp_dir()
        self.utils.download_mail(self.mail, TestCase.SCHEDULE_NAME)
        self.utils.get_attachment_files(ends_with="pptx")
        self.log.info("Verified attachment for the Schedule [%s] ", TestCase.SCHEDULE_NAME)
        self.cleanup_schedules()

    @test_step
    def _validate_exported_file(self):
        """
        Validate exported file
        """
        self.utils.wait_for_file_to_download("pptx")
        self.utils.validate_tmp_files("pptx", min_size=TestCase.MIN_FILE_SIZE)
        self.log.info("Validated exported file")

    def read_ppt(self):
        """Read ppt"""
        _files = self.utils.poll_for_tmp_files(ends_with=TestCase.FILE_TYPE)
        self._ppt = PPTManager(_files[0])

    def  verify_slide_count(self):
        """Verify slide count"""
        self.log.info("Verifying slide count")
        number_of_slides = self._ppt.get_number_of_slides()
        if number_of_slides < self.expected_number_of_slides_executive :
            raise CVTestStepFailure(f"Expected {self.expected_number_of_slides_executive} slides, but"
                                    f"{number_of_slides} slides are present in qbr pptx")
        self.log.info("expected number of slides are present in qbr ppt")

    def verify_slide_titles(self):
        """Verify slide titles"""
        self.log.info("Verifying slide titles")
        slide_number = 0
        while slide_number <= self.expected_number_of_slides_executive-1:
            ppt_slide_text = self._ppt.get_text_from_slide(slide_number)
            if self.executive_slides[slide_number] not in str([each_list for each_list in ppt_slide_text]):
                raise CVTestStepFailure(
                        f"Expected text {str(self.executive_slides[slide_number])} is not present in{slide_number} "
                        f"slide")
            self.log.info(f"Expected text {self.executive_slides[slide_number]} is present in {slide_number} slide")
            slide_number += 1
            continue
        self.log.info("slide titles verified successfully")

    @test_step
    def verify_ppt_data(self):
        """
        Verify exported ppt data
        """
        self.read_ppt()
        self.verify_slide_count()
        self.verify_slide_titles()

    def run(self):
        """ run method"""
        try:
            self._init_tc()
            self._export_executive_summary_report()
            self._validate_exported_file()
            self.verify_ppt_data()
            self._validate_schedule()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
