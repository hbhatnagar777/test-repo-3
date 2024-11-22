# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Report Alert """
import datetime
import time

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.manage_alerts import ManageAlerts
from Web.AdminConsole.Reports.cte import ConfigureAlert

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer

from AutomationUtils import mail_box
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.reportsutils import get_reports_config
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
REPORTS_CONFIG = get_reports_config()


class AlertDetails:
    """Set alert details"""
    column_name = None
    condition = None
    hours = None
    minutes = None
    ampm = None

    def __init__(self, column_name, condition, report_name, report_url):
        AlertDetails.column_name = column_name
        AlertDetails.condition = condition
        self.report_name = report_name
        self.report_url = report_url
        self.generate_alert_time()

    @classmethod
    def generate_alert_time(cls):
        """Generate alert time to set in alert"""
        now = datetime.datetime.now()
        now_plus_2mins = now + datetime.timedelta(minutes=2)
        AlertDetails.hours = str(int(datetime.datetime.strftime(now_plus_2mins, "%I")))
        AlertDetails.minutes = str(int(datetime.datetime.strftime(now_plus_2mins, "%M")))
        if len(AlertDetails.minutes) == 1:
            AlertDetails.minutes = "0" + AlertDetails.minutes
        AlertDetails.ampm = str(datetime.datetime.strftime(now_plus_2mins, "%p"))


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin Console Report Alerts"
        self.browser = None
        self.mail = None
        self.webconsole = None
        self.manage_report = None
        self.manage_alerts = None
        self.navigator = None
        self.admin_console = None
        self.utils = CustomReportUtils(self)
        self.alert_name = 'Command_Center_alert_TC53989'

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.mail = mail_box.MailBox()
            self.mail.connect()
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=commcell_password)
            if self.admin_console.driver.title == 'Hub - Metallic':
                self.log.info("Navigating to adminconsole from Metallic hub")
                hub_dashboard = Dashboard(self.admin_console, HubServices.endpoint)
                try:
                    hub_dashboard.choose_service_from_dashboard()
                    hub_dashboard.go_to_admin_console()
                except:  # in case service is already opened
                    hub_dashboard.go_to_admin_console()
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            self.manage_alerts = ManageAlerts(self.admin_console)
            self.cleanup_alerts()
            self.manage_report.access_report(REPORTS_CONFIG.REPORTS.CUSTOM[0])

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup_alerts(self):
        """ Deletes the alert if exists """
        self.manage_report.view_alerts()
        if self.alert_name in self.manage_alerts.get_all_alerts(column_name='Name'):
            self.manage_alerts.delete_alerts([self.alert_name])
        self.navigator.navigate_to_reports()

    @test_step
    def create_alert(self):
        """Create alert"""
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table = viewer.DataTable("Summary")
        report_viewer.associate_component(table)
        columns = table.get_table_columns()
        if not columns:
            raise CVTestStepFailure(f"Report [{self.alert_name}] might be empty. Please verify!")
        condition_string = table.get_table_data()[columns[0]][0]
        self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                      "[%s]", self.alert_name, columns[0], condition_string)
        table.configure_alert()
        alert = AlertDetails(columns[0], condition_string, report_name=self.alert_name,
                             report_url=self.browser.driver.current_url)
        alert_window = ConfigureAlert(self.admin_console)
        alert_window.create_alert(alert_name=alert.report_name, column_name=columns[0],
                                  criteria = alert_window.operator.EQUAL_TO, column_value=condition_string)

    @test_step
    def run_alert(self):
        """ Run alert """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        if self.alert_name in self.manage_alerts.get_all_alerts(column_name='Name'):
            self.manage_alerts.run_alerts([self.alert_name])
        else:
            raise CVTestStepFailure(f"The [{self.alert_name}] might not available. Please verify!")

    @test_step
    def validate_alert_email(self):
        """ Validate alert email """
        self.log.info("verifying [%s] alert email", self.alert_name)
        self.utils.download_mail(self.mail, subject=self.alert_name)
        self.log.info("Alert [%s] mail validated", self.alert_name)

    def run(self):
        try:
            self.init_tc()
            self.create_alert()
            self.run_alert()
            self.log.info("Wait for mails to be received for 5 minutes")
            time.sleep(400)
            self.validate_alert_email()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
