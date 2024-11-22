# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

Test cases to validate download and install service pack.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                      --  Initialize TestCase class

    init_tc()                       --  To perform initial configuration for the test case

    get_webconsole_table_data()     --  To get 1st 10 rows from table present in web page

    get_mail_table_data()           --  To get the data from the table embedded in the mail

    cleanup_schedule()              --  Deletes the schedules which contain 'Automation_tc_54787_' in schedule name

    verify_schedule_exists()        --  To verify is schedule is created successfully

    run_schedule()                  --  To run the created schedule

    validate_schedule_mail()        --  To validate the schedule mail received with the web page report

    delete_schedule()               --  To delete the created schedule

    run()                           --  Main function for test case execution

"""

import time
from cvpysdk import schedules
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from Web.WebConsole.Reports.Custom._components.table import MailTable
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import mail_box
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics report: validate embedded email in schedule"
        self.report_name = 'Strike Count'
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.admin_console = None
        self.report = None
        self.manage_reports = None
        self.manage_schedules = None
        self.schedule_name = OptionsSelector.get_custom_str('Automation_54787')
        self.format = "INLINE"
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
            self.rtable = Rtable(self.admin_console)
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.view_schedules()
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.cleanup_schedules()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_webconsole_table_data(self):
        """
        Read 1st 10 rows from table present in report

        Returns:
            (dict)  -- Table ID as key and table title as value

            (dict)  -- Table ID as key and table data as value

        """
        table_data = {}
        table_titles = {}
        for table in self.report.get_tables():
            table.show_number_of_results(10)
            data = table.get_data()
            title = table.get_table_title()
            table_data[table.id] = data
            table_titles[table.id] = title
            self.log.info("Table data present in webpage for table [%s]: ", title)
            self.log.info(data)

        return table_titles, table_data

    def get_mail_table_data(self, table_id):
        """
        To get the mail table data

        table_id    (str)   -- Comp ID of the table

        """
        mail_table = MailTable(self.browser.driver, table_id)
        data = mail_table.get_data_table_rows()
        self.log.info("Table data present in Mail:")
        self.log.info(data)

        return data

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_54787_' in schedule name """
        self.manage_schedules.cleanup_schedules("Automation_tc_54787_")

    @test_step
    def create_schedule(self):
        """To create a new schedule"""
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.report_name)
        schedule_window = self.report.schedule()
        self.log.info("Creating schedule for the [%s] report with [%s] file format",
                      self.report_name, self.format)
        schedule_window.set_schedule_name(self.schedule_name)
        schedule_window.set_recipient(self.recipient_id)
        schedule_window.select_format(self.format)
        schedule_window.save()
        time.sleep(5)
        self.log.info("Schedule created successfully for the report [%s]", self.report_name)

    @test_step
    def verify_schedule_exists(self):
        """To verify whether schedule is created"""
        self.log.info("Checking [%s] schedule is created", self.schedule_name)
        self.schedules.refresh()
        if not self.schedules.has_schedule(self.schedule_name):
            err_str = "[%s] schedule does not exists in db, created on [%s] report with [%s]" \
                      " file extension" % (self.schedule_name, self.report_name, self.format)
            raise CVTestStepFailure(err_str)
        else:
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
            self.log.info("Schedule job completed with job id:[%s], for the report:[%s], with file format:[%s]",
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

        table_titles, table_data = self.get_webconsole_table_data()

        # To navigate to the downloaded mail
        file_path = self.utils.poll_for_tmp_files(ends_with="html")[0]
        self.browser.open_new_tab()
        self.browser.switch_to_latest_tab()
        self.browser.driver.get(file_path)
        time.sleep(3)

        for table_id in table_data:
            table_title = table_titles[table_id]
            self.log.info('Validating table content for table [%s]', table_title)
            mail_report_table_data = self.get_mail_table_data(table_id)[0:10]
            web_report_table_data = table_data[table_id]

            if web_report_table_data != mail_report_table_data:
                self.log.error(
                    "Mail table contents are not matching with report table content for table: [%s]",
                    table_title
                )
                self.log.error("Mail table content: %s", mail_report_table_data)
                self.log.error("Web report table content: %s", web_report_table_data)
                raise CVTestStepFailure(
                    f'Mail table contents are not matching with report table content for table [{table_title}]')
            self.log.info('Table validation successful')
        self.log.info("Validation successful for all the tables")

        self.browser.close_current_tab()
        self.browser.switch_to_latest_tab()

    @test_step
    def delete_schedule(self):
        """To delete schedules"""
        self.manage_schedules.cleanup_schedules(self.schedule_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.create_schedule()
            self.verify_schedule_exists()
            self.run_schedule()
            self.validate_schedule_mail()
            self.delete_schedule()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
