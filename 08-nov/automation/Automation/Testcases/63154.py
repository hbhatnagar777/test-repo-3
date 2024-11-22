# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Schedule validation on report views with input filters

TestCase:
    __init__()      --  Initializes the TestCase class

    run()           --  Contains the core testcase logic and it is the one executed

    Input Example:
    "testCases":
            {
                "63154":
                 {
                     "username": "AutomationTc@reportautomation.com,
                     "password": ""
                 }
            }
"""
import os
import time
from AutomationUtils import mail_box, config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Reports import cte
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.Custom.inputs import ListBoxController
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Components.alert import Alert

export_type = cte.ConfigureSchedules.Format
CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Schedule validation on report views with input filters"
        self.report_name = "Backup job summary"
        self.utils = CustomReportUtils(self)
        self.mail = None
        self.browser = None
        self.report = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.file_path = None
        self.html_browser = None
        self.manage_report = None
        self.manage_schedules = None
        self.report_table_data = None
        self.format = export_type.HTML
        self.username = None
        self.password = None
        self.schedule_name = "Automation_tc_63154_Schedule_%s" % str(int(time.time()))
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
            self.report = Report(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def save_view(self):
        """Save a view"""
        self.table = viewer.DataTable("Job Details")
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        report_viewer.associate_component(self.table)

        visible_app_type = self.table.get_column_data('Workload')[0]
        visible_job_status = self.table.get_column_data('Job status')[0]

        list_box_controller = ListBoxController('App types / Workloads')

        report_viewer.associate_input(list_box_controller)
        list_box_controller.unselect_all()
        list_box_controller.select_value(visible_app_type)
        list_box_controller.apply()
        self.table.set_filter("Job status", visible_job_status)
        self.report.save_as_view(self.utils.testcase.id, set_as_default=False)
        if self.utils.testcase.id not in self.report.get_all_views():
            raise CVTestStepFailure("The created view is not listed")

    @test_step
    def create_schedule(self):
        """Create schedule"""
        self.log.info("Creating [%s]  schedule with the [%s] export_type",
                      self.schedule_name, self.format)
        report = Report(self.admin_console)
        schedule = report.schedule()
        schedule.create_schedule(self.schedule_name, self.recipient_id, self.format)

        Alert(self.admin_console).close_popup()

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

    def access_file(self):
        """
        Access downloaded html file
        """
        temp_dir = self.utils.get_temp_dir()
        for path in os.listdir(temp_dir):
            if os.path.isdir(os.path.join(temp_dir, path)):
                for file in os.listdir(os.path.join(temp_dir, path)):
                    if file.endswith('html'):
                        self.file_path = os.path.join(os.path.join(temp_dir, path), file)
        self.html_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.html_browser.open()
        self.html_browser.goto_file(file_path=self.file_path)

    def get_html_content(self):
        """
        Read rows from table in HTML
        """
        html_webconsole = AdminConsole(self.html_browser, self.commcell.webconsole_hostname)
        html_viewer = viewer.CustomReportViewer(html_webconsole)
        html_table = viewer.DataTable("Job Details")
        html_viewer.associate_component(html_table)
        html_data = html_table.get_rows_from_table_data()
        return html_data[0:20]  # reading first 20 rows only

    @test_step
    def validate_html_content(self):
        """
        Verify html file contents are matching with report table content
        """
        self.log.info("Verifying html content for the report [%s]", self.report_name)
        self.access_file()
        html_file_table_data = self.get_html_content()
        if html_file_table_data != self.report_table_data[0:20]:
            self.log.error("HTML contents are not matching with report table content")
            self.log.error("HTML content:%s", str(html_file_table_data))
            self.log.error("Web report content:%s", str(self.report_table_data))
            raise CVTestStepFailure("HTML contents are not matching with report table content")

        self.log.info("HTML contents are verified successfully")

    @test_step
    def delete_view(self):
        """ Deletes the view """
        self.navigator.navigate_to_reports()
        self.manage_report.access_report(self.report_name)
        self.report.delete_view(self.id)
        if self.id in self.report.get_all_views():
            raise CVTestStepFailure("View exists even after deleting it")

    @test_step
    def cleanup_schedule(self):
        """ Deletes the schedule if exists """
        self.navigator.navigate_to_reports()
        self.manage_report.view_schedules()
        self.manage_schedules.cleanup_schedules("Automation_tc_63154")

    def run(self):
        try:
            self.init_tc()
            if self.id in self.report.get_all_views():
                self.delete_view()
            self.save_view()
            self.create_schedule()
            self.report_table_data = self.table.get_rows_from_table_data()
            self.run_schedule()
            self.validate_schedule_mails()
            self.validate_html_content()
            self.cleanup_schedule()
            self.delete_view()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
