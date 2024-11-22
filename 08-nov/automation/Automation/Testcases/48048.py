# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" verify Email Now Feature"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports import cte
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
Format = cte.Email.Format


class EmailDetails:
    """
    Set email details: report name, job id, email format
    """
    report_name = None
    format = None
    job_id = None

    def __init__(self, report_name, file_format, job_id):
        self.report_name = report_name
        self.format = file_format
        self.job_id = job_id


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "verify Email Now Feature"
        self.admin_console = None
        self.browser = None
        self.navigator = None
        self.report = None
        self.manage_schedules = None
        self.manage_reports = None
        self.reports = REPORTS_CONFIG.REPORTS.DISTINCT_REPORTS
        self.recipient_id = CONSTANTS.email.email_id
        self.email_details = []
        self.mail = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.mail = mail_box.MailBox()
            self.mail.connect()
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
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.report = Report(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def email_job_validation(self):
        """
        Verify email jobs are completed
        """
        for each_email in self.email_details:
            self.log.info("Verifying job completed with job id:[%s], for the report:[%s], with "
                          "file format:[%s]", each_email.job_id, each_email.report_name,
                          each_email.format)
            job = self.commcell.job_controller.get(each_email.job_id)  # Creates job object
            if job.wait_for_completion(300):  # wait for max 5 minutes
                self.log.info("Email job completed with job id:[%s], for the report:[%s], with "
                              "file format:[%s]", each_email.job_id, each_email.report_name,
                              each_email.format)
                continue
            err_str = "Email job failed with job id [%s], for the report name [%s],file format" \
                      " [%s]" % (each_email.job_id, each_email.report_name, each_email.format)
            raise CVTestStepFailure(err_str)
        self.log.info("Email jobs completed successfully")

    @test_step
    def verify_email_attachment(self, file_type):
        """
        Verify email attachment file type

        Args:
            file_type       (String): email attachment file type

        """
        self.log.info("Verifying email attachment for file type [%s]", file_type)
        for each_email in self.email_details:
            self.utils.reset_temp_dir()
            self.log.info("Verifying attachment for the report [%s] with file type [%s]",
                          each_email.report_name, file_type)
            self.utils.download_mail(self.mail, each_email.report_name)
            self.utils.get_attachment_files(ends_with=file_type)
            self.log.info("Attachment is verified for report [%s] with file type [%s]",
                          each_email.report_name, file_type)
        self.log.info("Email attachment for file type [%s] is verified", file_type)

    def redirect_to_reports_page(self, report_name):
        """Redirect to reports page"""
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
    def email_now(self, email_format):
        """
        Email now with specific file format

        Args:
            email_format(String):email attachment file type

        """
        self.email_details = []
        for each_report in self.reports:
            if each_report == "Worldwide Dashboard" and email_format == Format.CSV:
                continue # CSV Email for worldwide dashboard is not supported.
            self.log.info(" ## Performing EmailNow for the report [%s], with file format [%s]",
                          each_report, email_format)
            self.redirect_to_reports_page(each_report)
            email_window = self.report.email()
            email_window.email_now(email_format, self.recipient_id)
            job_id = email_window.get_job_id()
            self.email_details.append(EmailDetails(each_report, email_format, job_id))
            self.log.info(" ## Email is done for the report [%s], with file format [%s]",
                          each_report, email_format)

    def run(self):
        try:
            self.init_tc()
            for each_file_type in [Format.PDF, Format.HTML, Format.CSV]:
                self.email_now(each_file_type)
                self.email_job_validation()
                self.verify_email_attachment(each_file_type)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.mail.disconnect()
