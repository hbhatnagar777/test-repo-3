# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics Report Alert"""
import datetime
import time

from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.cte import ConfigureAlert
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_alerts import ManageAlerts
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Metrics.components import AlertMail

from AutomationUtils import mail_box

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils


class AlertDetails:
    """
    Set alert details
    """
    alert_name = None
    column_name = None
    condition = None
    hours = None
    minutes = None
    ampm = None
    report_url = None
    report_name = None

    def __init__(self, column_name, condition, report_url, report_name):
        """
        Set alert details

        Args:
            column_name               (String)  --  name of the column
            condition:                (String)  --  the condition string which is set on table
            report_url:               (String)  --  URL of the report
            report_name:              (String)  --  Name of the report
        """
        self.alert_name = "Automation_tc_49502_%s" % str(int(time.time()))
        self.column_name = column_name
        self.condition = condition
        self.report_url = report_url
        self.report_name = report_name
        self.generate_alert_time()

    def generate_alert_time(self, excess_minutes=5):
        """
        Generate alert time to set in alert
        """
        now = datetime.datetime.now()
        now_plus_5mins = now + datetime.timedelta(minutes=excess_minutes)
        self.hours = str(int(datetime.datetime.strftime(now_plus_5mins, "%I")))
        self.minutes = str(int(datetime.datetime.strftime(now_plus_5mins, "%M")))
        if len(self.minutes) == 1:
            self.minutes = "0" + self.minutes
        self.ampm = str(datetime.datetime.strftime(now_plus_5mins, "%p"))


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.condition_string = None
        self.column_name = None
        self.table = None
        self.manage_report = None
        self.admin_console = None
        self.name = "Metrics alert Edit support through AdminConsole"
        self.show_to_user = True
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.report = None
        self.reports = None
        self.alert_window = None
        self.alerts = []
        self.metrics_table = None
        self.alert_settings = None
        self.mail = None
        self.alert_mail = None
        self.mail_browser = None
        self._driver = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.mail = mail_box.MailBox()
            self.mail.connect()

            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()

            # login to web console and redirect to ww reports.
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=commcell_password)
            self._driver = self.browser.driver
            self.navigator = self.admin_console.navigator
            self.reports = [self.tcinputs['report_names']]
            self.manage_report = ManageReport(self.admin_console)
            self.alert_settings = ManageAlerts(self.admin_console)
            self.alert_window = ConfigureAlert(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_alert(self):
        """Create alert"""
        for each_report in self.reports:
            self.navigator.navigate_to_reports()
            self.manage_report.access_report(each_report)
            viewer_obj = viewer.CustomReportViewer(self.admin_console)
            self.table = viewer.DataTable("Summary")
            viewer_obj.associate_component(self.table)
            self.column_name = self.table.get_table_columns()[0]
            self.condition_string = self.table.get_column_data(self.column_name)[0]
            self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                          "[%s]", each_report, self.column_name, self.condition_string)
            alert = AlertDetails(column_name=self.column_name, condition=self.condition_string,
                                 report_url=self._driver.current_url, report_name=each_report)
            self.table.configure_alert()
            self.alert_window.create_alert(alert_name=alert.alert_name, column_name=self.column_name,
                                           criteria=self.alert_window.operator.EQUAL_TO,
                                           column_value=self.condition_string)
            self.log.info("Alert [%s] created successfully on [%s] report ", alert.alert_name,
                          each_report)
            self.alerts.append(alert)

    def access_report(self, url):
        """Access report"""
        self._driver.get(url)
        self.admin_console.wait_for_completion()

    def access_email_file(self):
        """Access email downloaded file in browser"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.mail_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.mail_browser.open()
        self.mail_browser.goto_file(file_path=html_path)
        self.alert_mail = AlertMail(self.mail_browser)

    def get_report_content(self, filter_value):
        """Read report data"""
        column_name = self.table.get_table_columns()[0]
        self.table.set_filter(column_name=column_name, filter_string=filter_value)
        return self.table.get_table_data()

    def run_alert(self):
        """ Run alert """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.alert_settings.run_alerts([self.alerts[0].alert_name])

    @test_step
    def validate_alert_email(self):
        """Validate alert email"""
        self.run_alert()
        self.log.info("Wait for mails to be received for 3 minutes")
        time.sleep(180)
        for each_alert in self.alerts:
            self.utils.reset_temp_dir()
            self.utils.download_mail(self.mail, subject=each_alert.alert_name)
            self.access_report(each_alert.report_url)
            self.access_email_file()
            web_report_table_data = self.get_report_content(each_alert.condition)
            mail_report_name = self.alert_mail.get_report_name()
            if mail_report_name != each_alert.report_name:
                raise CVTestStepFailure("Report names are not matching with mail content, "
                                        "report name in mail:%s,report name in webconsole:%s",
                                        mail_report_name, each_alert.report_name)
            mail_report_link = self.alert_mail.get_report_link()
            # check the report id is matching
            if mail_report_link.split('=')[1].split('&')[0] != each_alert.report_url.split('=')[1].split('&')[0]:
                raise CVTestStepFailure("Report links are not matching with mail content, report "
                                        f"link in mail:{mail_report_link.split('&')[0]}, "
                                        f"report link in webconsole:{each_alert.report_url.split('&')[0]}"
                                        )
            mail_table_data = self.alert_mail.get_table_data()
            if mail_table_data[0][0] not in web_report_table_data.get('Job status')[0]:
                raise CVTestStepFailure("Table data in report is not matching with mail content, "
                                        "table data in mail:%s,report data in webconsole:%s",
                                        str(mail_table_data[0][0]), str(web_report_table_data.get('Job status')[0]))
            self.log.info("Email content is matched successfully with report content for the "
                          "report [%s]", each_alert.report_name)

    @test_step
    def edit_alert(self):
        """Edit existing alert: update alert name and alert time"""
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        for each_alert in self.alerts:
            self.log.info("Editing [%s] alert" % each_alert.alert_name)
            self.alert_settings.edit_alert(each_alert.alert_name)
            each_alert.alert_name = each_alert.alert_name + "_edit_alert"
            self.alert_window.create_alert(alert_name=each_alert.alert_name, column_name=self.column_name,
                                           criteria=self.alert_window.operator.EQUAL_TO,
                                           column_value=self.condition_string, is_edit_alert=True)
            self.log.info("Alert updated successfully as [%s]" % each_alert.alert_name)

    @test_step
    def delete_alerts(self):
        """
        Delete alerts
        """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        alert_names = []
        for each_alert in self.alerts:
            alert_names.append(each_alert.alert_name)
        self.alert_settings.delete_alerts(alert_names)

    def run(self):
        try:
            self.init_tc()
            self.create_alert()
            self.edit_alert()
            self.log.info("Verify the alert generated mails")
            self.validate_alert_email()
            self.delete_alerts()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.mail_browser)
