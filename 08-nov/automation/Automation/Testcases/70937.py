# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import time
from AutomationUtils import mail_box, config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports import cte
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.Custom.inputs import ListBoxController
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Components.alert import Alert

export_type = cte.RConfigureSchedules.Format
CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.diff_commcell_name = None
        self.report_column_values = None
        self.column_name = 'Server'
        self.file_name = None
        self.report_name = "Backup job summary"
        self.utils = CustomReportUtils(self)
        self.mail = None
        self.browser = None
        self.report = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.file_path = None
        self.manage_report = None
        self.manage_schedules = None
        self.format = export_type.CSV
        self.username = None
        self.password = None
        self.schedule_name = "Automation_tc_70937_Schedule_%s" % str(int(time.time()))
        self.recipient_id = CONSTANTS.email.email_id

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.username = self.inputJSONnode['commcell']['commcellUsername']
            self.password = self.inputJSONnode['commcell']['commcellPassword']
            self.mail = mail_box.MailBox()
            self.mail.connect()
            download_directory = self.utils.get_temp_dir()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.username, self.password)
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.cleanup_schedule()
            self.navigator.navigate_to_reports()
            self.manage_report.access_report(self.report_name)
            self.diff_commcell_name = self.tcinputs['commcell']

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_schedule(self):
        """Create schedule"""
        self.log.info("Creating [%s]  schedule with the [%s] export_type",
                      self.schedule_name, self.format)
        report = Report(self.admin_console)
        schedule = report.schedule()
        schedule.create_schedule(self.schedule_name, self.recipient_id, self.format)

        Alert(self.admin_console).close_popup()
        self.admin_console.wait_for_completion()

    @test_step
    def run_schedule(self):
        """ Run schedule """
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        job_id = self.manage_schedules.run_schedules([self.schedule_name])
        job = self.commcell.job_controller.get(job_id)
        self.log.info("Wait for [%s] job to complete", str(job))
        if job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Job id:[%s] Completed", job_id)
        else:
            err_str = "Job id:[%s] Failed" % job_id
            raise CVTestStepFailure(err_str)

    @test_step
    def validate_schedule_mails(self):
        """ Validate schedule mails """
        self.utils.reset_temp_dir()
        self.log.info("verifying [%s] schedule email", self.schedule_name)
        self.utils.download_mail(self.mail, subject=self.schedule_name)
        self.utils.get_attachment_files(ends_with=self.format)
        self.log.info("Schedule [%s] mail validated", self.schedule_name)

    @test_step
    def select_commcell(self):
        """
        Select different / remote commcell
        """
        self.table = viewer.DataTable("Job Details")
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        report_viewer.associate_component(self.table)
        list_box_controller = ListBoxController('CommCell')
        report_viewer.associate_input(list_box_controller)
        list_box_controller.select_value(self.commcell.commserv_name)
        list_box_controller.select_value(self.diff_commcell_name)
        list_box_controller.apply()
        self.report_column_values = self.table.get_column_data(self.column_name)

    def get_csv_column_content(self, column_name):
        """
        Read csv file content and returns value of column specified
        """
        try:
            csv_content = self.utils.get_csv_content(self.file_name)
            job_details_start = None
            database_sql_start = None

            for i, row in enumerate(csv_content):
                if row and row[0] == "Job ID":
                    job_details_start = i
                elif row and row[0] == "Databases in SQL Server and Sybase Backup Jobs":
                    database_sql_start = i
                    break

            if job_details_start is None:
                raise Exception("Job Details table not found in the CSV content.")

            if database_sql_start is None:
                raise Exception("Databases in SQL Server and Sybase Backup Jobs table not found in the CSV content.")

            # Extract the header and data rows of the 'Job Details' table
            job_details_header = csv_content[job_details_start]
            job_details_data = csv_content[job_details_start + 1:database_sql_start]

            # Find the index of the specified column
            if column_name not in job_details_header:
                raise Exception(f"Column '{column_name}' not found in the 'Job Details' table.")

            index = job_details_header.index(column_name)

            # Extract and return the content of the specified column
            column_content = []
            for row in job_details_data[0:20]:
                if row and len(row) > index:
                    column_content.append(row[index])

            return column_content
        except Exception as e:
            raise e

    def access_file(self):
        """
        Access downloaded csv file
        """
        self.file_name = self.utils.get_attachment_files(ends_with='csv')[0]

    @test_step
    def validate_csv_content(self):
        """
        Verify csv file contents are matching with report table content
        """
        self.log.info("Verifying csv content for the report [%s]", self.report_name)
        self.access_file()
        csv_column_values = self.get_csv_column_content(self.column_name)
        if set(csv_column_values) != set(self.report_column_values):
            self.log.error("CSV column has values :%s", str(csv_column_values))
            self.log.error("Web report column has values :%s", set(self.report_column_values))
            raise CVTestStepFailure("CSV column values are not matching with report column values for commcell: %s",
                                    self.diff_commcell_name)
        self.log.info("CSV contents are verified successfully for commcell: %s", self.diff_commcell_name)

    @test_step
    def cleanup_schedule(self):
        """ Deletes the schedule if exists """
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        self.manage_schedules.cleanup_schedules("Automation_tc_70937")

    def run(self):
        try:
            self.init_tc()
            self.select_commcell()
            self.create_schedule()
            self.run_schedule()
            self.validate_schedule_mails()
            self.validate_csv_content()
            self.cleanup_schedule()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
