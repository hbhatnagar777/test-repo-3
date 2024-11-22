# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Report Alert """
import datetime
import time

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.cte import ConfigureAlert
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.manage_alerts import AlertSettings
from Web.WebConsole.Reports.Metrics.components import AlertMail
from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils import mail_box
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.Custom.report_templates import DefaultReport


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

    def __init__(self, column_name, condition, report_name, report_url):
        self.alert_name = "Automation_tc_49899_%s" % str(int(time.time()))
        self.column_name = column_name
        self.condition = condition
        self.report_name = report_name
        self.report_url = report_url
        self.generate_alert_time()

    def generate_alert_time(self):
        """Generate alert time to set in alert"""
        now = datetime.datetime.now()
        now_plus_2mins = now + datetime.timedelta(minutes=2)
        self.hours = str(int(datetime.datetime.strftime(now_plus_2mins, "%I")))
        self.minutes = str(int(datetime.datetime.strftime(now_plus_2mins, "%M")))
        if len(self.minutes) == 1:
            self.minutes = "0" + self.minutes
        self.ampm = str(datetime.datetime.strftime(now_plus_2mins, "%p"))


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report Alert"
        self.show_to_user = True
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.alert_window = None
        self.alerts = []
        self.alert_settings = None
        self.table = None
        self.viewer = None
        self.mail = None
        self.mail_browser = None
        self.alert_mail = None
        self.utils = CustomReportUtils(self)

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
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(username=self.commcell.commcell_username,
                                  password=commcell_password)
            self.webconsole.goto_reports()

            self.navigator = Navigator(self.webconsole)
            self.viewer = viewer.CustomReportViewer(self.webconsole)
            self.table = viewer.DataTable("Automation Table")

            self.utils.webconsole = self.webconsole
            self.alert_settings = AlertSettings(self.webconsole)
            self.alert_window = ConfigureAlert(self.webconsole)
            self.cleanup_alerts()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def access_report(self):
        """Access custom report"""
        DefaultReport(self.utils).build_default_report(overwrite=False)
        self.table = viewer.DataTable("Automation Table")
        self.viewer.associate_component(self.table)

    def cleanup_alerts(self):
        """ Deletes the alert which contain 'Automation_tc_49899_' in alert name """
        self.navigator.goto_alerts_configuration()
        self.alert_settings.cleanup_alerts("Automation_tc_49899_")

    @test_step
    def create_alert(self):
        """Create alert"""
        data = self.table.get_table_data()
        column_name = list(data)[0]
        if not data[column_name]:
            raise CVTestStepFailure("Report [%s] might be empty. Please verify!", self.name)
        condition_string = data[column_name][0]
        self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                      "[%s]", self.name, column_name, condition_string)
        alert = AlertDetails(column_name, condition_string, report_name=self.name,
                             report_url=self.browser.driver.current_url)
        self.table.configure_alert()
        self.alert_window.set_time(alert.hours, alert.minutes, alert.ampm)
        self.alert_window.create_alert(alert_name=alert.alert_name, column_name=column_name,
                                       column_value=condition_string)
        self.log.info("Alert [%s] created successfully on [%s] report ", alert.alert_name,
                      self.name)
        self.alerts.append(alert)

    def access_email_file(self):
        """Access email downloaded file in browser"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.mail_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.mail_browser.open()
        self.mail_browser.goto_file(file_path=html_path)
        self.alert_mail = AlertMail(self.mail_browser)

    def get_report_content(self, filter_string):
        """Read report table limited to 50 lines"""
        column_name = self.table.get_table_columns()[0]
        self.table.set_filter(column_name=column_name, filter_string=filter_string)
        data = self.table.get_rows_from_table_data()
        self.log.info("Table data present in webpage:")
        self.log.info(data)
        return data

    @test_step
    def validate_alert_email(self):
        """Validate alert email"""
        for each_alert in self.alerts:
            self.utils.reset_temp_dir()
            self.utils.download_mail(self.mail, subject=each_alert.alert_name)
            self.access_report()
            self.access_email_file()
            web_report_table_data = self.get_report_content(each_alert.condition)
            mail_report_name = self.alert_mail.get_report_name()
            if mail_report_name != each_alert.report_name:
                raise CVTestStepFailure("Report names are not matching with mail content, "
                                        "report name in mail:%s,report name in webconsole:%s",
                                        mail_report_name, each_alert.report_name)
            mail_report_link = self.alert_mail.get_report_link()
            if mail_report_link != each_alert.report_url:
                raise CVTestStepFailure("Report links are not matching with mail content, report "
                                        "link in mail:%s, report link in webconsole:%s",
                                        mail_report_link, each_alert.report_url)
            mail_table_data = self.alert_mail.get_table_data()
            if mail_table_data != [list(web_report_table_data[0])]:
                err_str = "Table data in report is not matching with mail content, table data " \
                          "in mail:%s,report data in webconsole:%s", str(mail_table_data), \
                          str(web_report_table_data)
                raise CVTestStepFailure(err_str)
            self.log.info("Email content is matched successfully with report content for the "
                          "report [%s]", each_alert.report_name)

    @test_step
    def delete_alert(self):
        """
        Delete alerts
        """
        self.navigator.goto_alerts_configuration()
        alert_names = []
        for each_alert in self.alerts:
            alert_names.append(each_alert.alert_name)
        self.alert_settings.delete_alerts(alert_names)

    def run(self):
        try:
            self.init_tc()
            self.access_report()
            self.create_alert()
            self.log.info("Wait for mails to be received for 3 minutes")
            time.sleep(180)
            self.validate_alert_email()
            self.delete_alert()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.mail_browser)
