from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

Test cases to validate embedded email in schedule

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                      --  Initialize TestCase class

    init_tc()                       --  To perform initial configuration for the test case

    get_webconsole_table_data()     --  To get data from the table present in web page

    get_webconsole_chart_title()    --  To get the title of the chart in the web page

    get_mail_table_data()           --  To get the data from the table embedded in the mail

    get_mail_chart_title()          --  To get the title of the chart present in the mail

    cleanup_schedule()              --  Deletes the schedules which contain 'Automation_tc_54786_' in schedule name

    verify_schedule_exists()        --  To verify is schedule is created successfully

    run_schedule()                  --  To run the created schedule

    validate_schedule_mail()        --  To validate the schedule mail received with the web page report

    delete_schedule()               --  To delete the created schedule

    run()                           --  Main function for test case execution

"""
import os
import time

from cvpysdk import schedules

from Web.AdminConsole.Components.alert import Alert
from Web.API import cc
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom._components.table import MailTable
from Web.WebConsole.Reports.Custom._components.chart import MailChart
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_schedules import ManageSchedules
from Web.AdminConsole.Reports import cte
from Reports.Custom.report_templates import DefaultReport
from Reports.utils import TestCaseUtils
from Reports.Custom.utils import CustomReportUtils
from AutomationUtils.constants import AUTOMATION_DIRECTORY
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
        self.manage_schedules = None
        self.manage_reports = None
        self.name = self.report_name = "Custom report: validate embedded email in schedule"
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.navigator = None
        self.report = None
        self.alert = None
        self.default_rpt = None
        self.schedule_name = OptionsSelector.get_custom_str('Automation_54786')
        self.format = "Email body"
        self.recipient_id = CONSTANTS.email.email_id
        self.schedule_window = None
        self.schedule_details = []
        self.mail = None
        self.wc_adapter = None
        self.mails_download_directory = None
        self.schedules = None
        self.rpt_api = None
        self.table = None
        self.chart = None
        self.viewer = None
        self.utils = TestCaseUtils(self)
        self.cre_utils = CustomReportUtils(self)
        self.import_report_name = "Formatters"

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
            self.rpt_api = cc.Reports(machine=self.commcell.webconsole_hostname,
                                      username=self.inputJSONnode['commcell']["commcellUsername"],
                                      password=self.inputJSONnode['commcell']["commcellPassword"])
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
            self.wc_adapter = WebConsoleAdapter(self.admin_console, self.browser)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.report = Report(self.admin_console)
            self.alert = Alert(self.admin_console)
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_schedules = ManageSchedules(self.admin_console)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
            self.chart = viewer.VerticalBar('Automation Chart')
            self.default_rpt = DefaultReport(self.cre_utils, self.admin_console, self.browser)
            self.cleanup_schedules()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_webconsole_table_data(self, table_name):
        """Read the data present in table"""
        self.table = viewer.DataTable(table_name)
        self.viewer.associate_component(self.table)
        data = self.table.get_table_data()
        self.log.info("Table data present in webpage:")
        self.log.info(data)
        return data

    def get_webconsole_chart_title(self):
        """To get the chart title"""
        self.viewer.associate_component(self.chart)
        title = self.chart.title
        self.log.info("Chart title present in webpage: %s", title)
        return title

    def get_mail_table_data(self, table_id):
        """
        To get the mail table data

        table_id    (str)   -- Comp ID of the table

        """
        mail_table = MailTable(self.browser.driver, table_id)
        data = mail_table.get_table_data(row_limit=20)
        self.log.info("Table data present in Mail:")
        self.log.info(data)
        if not data:
            raise CVTestStepFailure(
                "Unable to fetch the table data from the mail."
            )
        return data

    def get_mail_chart_title(self, chart_id):
        """To get the chart title present in mail

        Args:
            chart_id    (str)   -- Comp ID of the chart

        """
        mail_chart = MailChart(self.browser.driver, chart_id)
        title = mail_chart.get_chart_title()
        self.log.info("Chart title present in mail: %s", title)
        return title

    def cleanup_schedules(self):
        """ Deletes the schedules which contain 'Automation_tc_54786_' in schedule name """
        self.manage_schedules.cleanup_schedules("Automation_tc_54786_")

    @test_step
    def create_schedule(self):
        """To create a new schedule"""
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.report_name)
        schedule_window = self.report.schedule()
        self.log.info("Creating schedule for the [%s] report with [%s] file format",
                      self.report_name, self.format)
        schedule_window.create_schedule(
            schedule_name=self.schedule_name,
            email_recipient=self.recipient_id,
            file_format=self.format
        )
        self.alert.close_popup()
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
    def validate_schedule_mail(self, table_name, chart_present=False):
        """Validate schedule mails"""
        self.utils.reset_temp_dir()
        self.log.info("verifying [%s] schedule email for [%s] report with [%s] file extension",
                      self.schedule_name, self.report_name, self.format)
        self.utils.download_mail(self.mail, self.schedule_name)
        web_report_table_data = self.get_webconsole_table_data(table_name)
        for column_name, data in web_report_table_data.items():
            data = [d.replace('BYTES', 'KB') for d in data]
            web_report_table_data[column_name] = data

        if chart_present:
            web_report_chart_title = self.get_webconsole_chart_title()
        # To navigate to the downloaded mail
        file_path = self.utils.poll_for_tmp_files(ends_with="html")[0]
        self.browser.open_new_tab()
        self.browser.switch_to_latest_tab()
        self.browser.driver.get(file_path)
        time.sleep(3)

        mail_report_table_data = self.get_mail_table_data(self.table.id)
        if chart_present:
            mail_chart_title = self.get_mail_chart_title(self.chart.id)
        self.browser.close_current_tab()
        self.browser.switch_to_first_tab()
        self.navigator.navigate_to_reports()

        if web_report_table_data != mail_report_table_data:
            self.log.error("Mail table contents are not matching with report table content")
            self.log.error("Mail content:%s", mail_report_table_data)
            self.log.error("Web report content:%s", web_report_table_data)
            raise CVTestStepFailure("Mail table contents are not matching with report table content")

        if chart_present:
            if web_report_chart_title != mail_chart_title:
                self.log.error("Mail chart title is not matching with report chart title")
                self.log.error("Mail chart title:%s", mail_chart_title)
                self.log.error("Web report content:%s", web_report_chart_title)
                raise CVTestStepFailure("Mail chart title is not matching with report chart title")
        self.log.info("Mail contents are verified successfully")

    @test_step
    def delete_schedule(self):
        """Delete schedules"""
        self.schedules.delete(self.schedule_name)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            report_types = ['create_report', 'import_report']
            for report in report_types:
                self.log.info(f"Starting schedule verification for report : {report}")
                if report == 'create_report':
                    try:
                        self.manage_reports.delete_report(self.report_name)
                    except:
                        self.log.info(f"Report {self.report_name} doesn't exist on Reports page")
                    self.navigator.navigate_to_reports()
                    self.manage_reports.add_report()
                    self.default_rpt.build_default_report(
                        sql="""
                                                SELECT TOP 10 id, name, csHostName
                                                FROM App_Client
                                                """,
                        overwrite=False,
                        chart_cols={'X': 'id', 'Y': 'name'}
                    )
                else:
                    self.rpt_api.import_custom_report_xml(os.path.join(AUTOMATION_DIRECTORY, "Reports",
                                                                       "Templates", f"{self.import_report_name}.xml"))
                    self.report_name = self.import_report_name

                self.create_schedule()
                self.verify_schedule_exists()
                self.run_schedule()
                if report == 'create_report':
                    self.validate_schedule_mail("Automation Table", chart_present=True)
                else:
                    self.validate_schedule_mail(self.import_report_name)
                self.delete_schedule()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
