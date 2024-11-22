# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

Test cases to validate schedule.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                      --  Initialize TestCase class

    init_tc()                       --  To perform initial configuration for the test case

    get_webconsole_table_data()     --  To get data from the table present in web page

    get_mail_table_data()           --  To get the data from the table embedded in the mail

    cleanup_schedule()              --  Deletes the schedules which contain 'Automation_tc_54786_'
                                        in schedule name

    verify_schedule_exists()        --  To verify is schedule is created successfully

    run_schedule()                  --  To run the created schedule

    validate_schedule_mail()        --  To validate the schedule mail received with
                                        the web page report

    modify_schedule()               --  Modifies schedule and update details

    validate_recipient_column()       -- To validate the Recipient User and User Group column values

    delete_schedule()               --  To delete the created schedule

    run()                           --  Main function for test case execution

"""
import re
import time

from cvpysdk import schedules
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom._components.table import MailTable
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from Reports.Custom.report_templates import DefaultReport
from Reports.utils import TestCaseUtils
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import mail_box
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase

CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = self.report_name = "Custom report: Users to Notify feature in schedule"
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.navigator = None
        self.report = None
        self.schedule_name = OptionsSelector.get_custom_str('Automation_58660')
        self.format = "Email body"
        self.tcinputs = {
            "user_group": None,
            "user_name": None
        }
        self.recipient_id = CONSTANTS.email.email_id
        self.user_name = None
        self.schedule_window = None
        self.mail = None
        self.mails_download_directory = None
        self.schedules = None
        self.default_rpt = None
        self.column_string = None
        self.manage_schedules = None
        self.manage_reports = None
        self.table = None
        self.viewer = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.mail = mail_box.MailBox()
            self.mail.connect()
            self.schedules = schedules.Schedules(self.commcell)
            self.user_name = self.tcinputs["user_name"]
            if not self.user_name:
                raise CVTestCaseInitFailure("User name is not specified in config file")

            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            # login to Admin Console
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.utils.webconsole = self.webconsole
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.report = Report(self.admin_console)
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.manage_reports.delete_report(self.report_name)
            self.manage_reports.view_schedules()
            self.viewer = viewer.CustomReportViewer(self.admin_console)
            self.table = viewer.DataTable("Automation Table")
            self.default_rpt = DefaultReport(self.utils, self.admin_console, self.browser)
            self.cleanup_schedules()
            self.navigator.navigate_to_reports()
            self.manage_reports.add_report()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_webconsole_table_data(self):
        """Read the data present in table"""
        self.viewer.associate_component(self.table)
        data = self.table.get_table_data()
        self.log.info("Table data present in webpage:")
        self.log.info(data)
        return data

    def get_mail_table_data(self, table_id):
        """
        To get the mail table data
        table_id    (str)   -- Comp ID of the table
        """
        mail_table = MailTable(self.browser.driver, table_id)
        data = mail_table.get_table_data()
        self.log.info("Table data present in Mail:")
        self.log.info(data)
        return data

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_58660_' in schedule name """
        self.manage_schedules.cleanup_schedules("Automation_tc_58660_")

    @test_step
    def create_schedule(self):
        """To create a new schedule"""
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.report_name)
        self.schedule_window = self.report.schedule()
        self.log.info("Creating schedule for the [%s] report with [%s] file format",
                      self.report_name, self.format)
        self.schedule_window.create_schedule(
            schedule_name=self.schedule_name,
            email_recipient=self.recipient_id,
            file_format=self.format,
            user_or_group=self.user_name
        )
        self.log.info("Schedule created successfully for the report [%s]", self.report_name)

    @test_step
    def modify_schedule(self):
        """To edit the schedule"""
        self.navigator.navigate_to_reports()
        self.manage_reports.view_schedules()
        self.manage_schedules.open_schedule(self.schedule_name)
        self.manage_schedules.edit_schedule(page_level=True)
        self.schedule_window.create_schedule(
            schedule_name=self.schedule_name,
            email_recipient=self.recipient_id,
            file_format=self.format,
            user_or_group=self.tcinputs['user_group']
        )
        self.admin_console.close_popup()
        self.manage_schedules.edit_schedule(page_level=True)
        self.schedule_window.click_edit_report_settings()
        self.viewer.associate_component(self.table)
        rows = self.table.get_row_count()
        if rows > 1:
            columns = self.table.get_table_columns()
            self.column_string = self.table.get_table_data()[columns[0]][0]
            self.table.set_filter(column_name=columns[0], filter_string=f"{self.column_string}\n")
            self.report.update_report_settings()
            self.log.info("Filter has been applied on report [%s].", self.report_name)
        else:
            self.log.info("No content available in report [%s].", self.report_name)
            self.report.cancel_report_update()
            self.log.info("No filter applied to report [%s].", self.report_name)
        time.sleep(10)
        self.log.info("Schedule modified successfully for the report [%s].", self.report_name)

    @test_step
    def verify_filter_exists(self):
        """ To verify whether a filter exists"""
        self.manage_schedules.edit_schedule(page_level=True)
        self.schedule_window.click_edit_report_settings()
        self.admin_console.wait_for_completion()
        self.viewer.associate_component(self.table)
        columns = self.table.get_table_columns()
        table_data = self.table.get_table_data()[columns[0]]
        total_records = len(table_data)
        if total_records == 1 and table_data[0] == self.column_string:
            self.log.info("Filter has been retained in the scheduled report [%s].", self.report_name)
        else:
            self.log.info("No filter has been applied to report [%s].", self.report_name)
            raise CVTestStepFailure("Filter is not retained in scheduled report")

    @test_step
    def verify_schedule_exists(self):
        """To verify whether schedule is created"""
        self.log.info("Checking [%s] schedule is created", self.schedule_name)
        self.schedules.refresh()
        if not self.schedules.has_schedule(self.schedule_name):
            err_str = "[%s] schedule does not exists in db, created on [%s] report with [%s]" \
                      " file extension" % (self.schedule_name, self.report_name, self.format)
            raise CVTestStepFailure(err_str)
        self.log.info("[%s] schedule is created successfully", self.schedule_name)

    @test_step
    def run_schedule(self):
        """To run the schedule"""
        schedule = schedules.Schedule(self.commcell, schedule_name=self.schedule_name)
        self.log.info("Running [%s] schedule", self.schedule_name)
        job_id = schedule.run_now()
        time.sleep(5)

        job = self.commcell.job_controller.get(job_id)
        self.log.info("Wait for [%s] job to complete", str(job))
        if job.wait_for_completion():
            self.log.info("Schedule job completed with job id:[%s], for the report:[%s], "
                          "with file format:[%s]",
                          job_id,
                          self.report_name,
                          self.format)
        else:
            err_str = "Schedule job failed with job id [%s], for the report name [%s],file " \
                      "format [%s]" % (job_id, self.report_name, self.format)
            raise CVTestStepFailure(err_str)

    @test_step
    def validate_schedule_mail(self):
        """Validate schedule mails"""
        self.utils.reset_temp_dir()
        self.log.info("verifying [%s] schedule email for [%s] report with [%s] file extension",
                      self.schedule_name, self.report_name, self.format)
        self.utils.download_mail(self.mail, self.schedule_name)

        web_report_table_data = self.get_webconsole_table_data()

        # To navigate to the downloaded mail
        file_path = self.utils.poll_for_tmp_files(ends_with="html")[0]
        self.browser.open_new_tab()
        self.browser.switch_to_latest_tab()
        self.browser.driver.get(file_path)
        time.sleep(3)

        mail_report_table_data = self.get_mail_table_data(self.table.id)

        self.browser.close_current_tab()
        self.browser.switch_to_latest_tab()

        if web_report_table_data != mail_report_table_data:
            self.log.error("Mail table contents are not matching with report table content")
            self.log.error("Mail content:%s", mail_report_table_data)
            self.log.error("Web report content:%s", web_report_table_data)
            raise CVTestStepFailure("Mail table contents are not matching with report table")
        self.log.info("Mail contents are verified successfully")
        self.browser.switch_to_first_tab()

    @test_step
    def validate_recipient_column(self):
        """Validate that User and User group is displayed in Recipient Users and Groups column"""
        self.navigator.navigate_to_reports()
        self.manage_reports.view_schedules()
        recipient_users = self.manage_schedules.get_email_recipients(self.schedule_name, user_or_user_groups=True)
        for index, recipient in enumerate(recipient_users):
            match = re.search(r'\((.*?)\)', recipient)
            if match:
                recipient_users[index]=match.group(1)

        if sorted([self.user_name, self.tcinputs["user_group"]]) == sorted(recipient_users):
            self.log.info("User and User Group are displayed correctly in "
                          "Recipient Users and Groups column as [%s]", [self.user_name, self.tcinputs["user_group"]])
        else:
            self.log.info("Expected User in Recipient Users and Groups column - %s",
                          [self.user_name, self.tcinputs["user_group"]])
            self.log.info("Actual User in Recipient Users and Groups column - %s",
                          recipient_users)
            raise CVTestStepFailure("Expected User and User group are NOT displayed in "
                                    "Recipient Users and Groups column")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.report_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            # To create a new report
            self.default_rpt.build_default_report(
                sql="""
                         SELECT TOP 5 id, name, csHostName
                         FROM APP_Client
                    """,
                overwrite=False
            )
            self.create_schedule()
            self.verify_schedule_exists()
            self.run_schedule()
            self.validate_schedule_mail()
            self.modify_schedule()
            self.verify_filter_exists()
            self.validate_recipient_column()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            self.cleanup_schedules()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
