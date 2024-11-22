# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics Report Alert"""
import datetime
import time

from urllib.parse import urlparse

from Application.Exchange.ExchangeMailbox.constants import mailbox_type
from Web.AdminConsole.Reports.cte import ConfigureAlert
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.manage_alerts import ManageAlerts
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
        self.alert_name = "Automation_tc_47857_%s" % str(int(time.time()))
        self.column_name = column_name
        self.condition = condition
        self.report_url = report_url
        self.report_name = report_name
        self.generate_alert_time()

    def generate_alert_time(self):
        """
        Generate alert time to set in alert
        """
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
        self.admin_console = None
        self.alert = None
        self.table = None
        self.manage_report = None
        self.name = "Metrics Report Alert"
        self.show_to_user = True
        self.browser = None
        self.navigator = None
        self.report = None
        self.report_name = None
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
            self.manage_report = ManageReport(self.admin_console)
            self.alert_settings = ManageAlerts(self.admin_console)
            self.navigator.navigate_to_metrics()
            self.manage_report.access_report_tab()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_alert(self):
        """Create alert"""
        self.manage_report.access_report('Client Details')
        _viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable('Overview')
        _viewer.associate_component(self.table)
        columns = self.table.get_table_columns()
        condition_string = self.table.get_column_data(columns[0])
        self.log.info("Creating alert for Client Details report for [%s] column with condition string:"
                      "[%s]", columns[0], condition_string[0])
        self.alert = AlertDetails(column_name=columns[0], condition=condition_string[0],
                                  report_url=self._driver.current_url, report_name='Client Details')
        self.table.configure_alert()
        alert_window = ConfigureAlert(self.admin_console)
        alert_window.create_alert(alert_name=self.alert.alert_name, column_name=columns[0],
                                  criteria=alert_window.operator.EQUAL_TO, column_value=condition_string[0])
        self.log.info("Alert [%s] created successfully on Client details report ", self.alert.alert_name)
        self.alerts.append(self.alert.alert_name)

    def access_email_file(self):
        """Access email downloaded file in browser"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.mail_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.mail_browser.open()
        self.mail_browser.goto_file(file_path=html_path)
        self.alert_mail = AlertMail(self.mail_browser)

    def run_alert(self):
        """ Run alert """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.alert_settings.run_alerts([self.alert.alert_name])

    @test_step
    def validate_alert_email(self):
        """Validate alert email"""
        self.run_alert()
        self.log.info("Wait for mails to be received for 3 minutes")
        time.sleep(180)
        for each_alert in self.alerts:
            self.utils.reset_temp_dir()
            self.utils.download_mail(self.mail, subject=each_alert)
            self.access_email_file()
            web_report_table_data = self.alert.condition
            mail_report_name = self.alert_mail.get_report_name()
            if mail_report_name != self.alert.report_name:
                raise CVTestStepFailure("Report names are not matching with mail content, "
                                        "report name in mail:%s,report name in adminconsole:%s" %
                                        (mail_report_name, self.alert.report_name.report_name))
            mail_report_link = self.alert_mail.get_report_link()
            if urlparse(mail_report_link).path != urlparse(self.alert.report_url).path:
                raise CVTestStepFailure("Report links are not matching with mail content, report "
                                        "link in mail:%s, report link in adminconsole:%s" %
                                        (mail_report_link, self.alert.report_url))
            # read all the data from first column
            col_data = self.alert_mail.get_column_date()[0]
            col_lst = list(set(col_data))
            if len(col_lst) > 1:
                raise CVTestStepFailure(f"Expected column data  {col_data} is not matching with mail content")
            mail_table_data = self.alert_mail.get_table_data()[0]
            if mail_table_data[0] != web_report_table_data:
                raise CVTestStepFailure("Table data in report is not matching with mail content, "
                                        "table data in mail:%s,report data in adminconsole:%s"
                                        % (mail_table_data[0], web_report_table_data))
            self.log.info("Email content is matched successfully with report content for the "
                          "report [%s]", self.alert.report_name)

    @test_step
    def delete_alerts(self):
        """
        Delete alerts
        """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        if self.alert.alert_name not in self.alert_settings.get_all_alerts(column_name='Name'):
            raise CVTestStepFailure(f"Alert {self.alert.alert_name} is missing after creation")
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.alert_settings.delete_alerts([self.alert.alert_name])

    def run(self):
        try:
            self.init_tc()
            self.create_alert()
            self.validate_alert_email()
            self.delete_alerts()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.mail_browser)
