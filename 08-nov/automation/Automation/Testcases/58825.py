# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Custom Report Alert edit and on-Demand Trigger"""
import time

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.cte import ConfigureAlert
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.manage_alerts import AlertSettings
from Web.WebConsole.Reports.Metrics.components import AlertMail
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole

from AutomationUtils import mail_box
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.Custom.report_templates import DefaultReport


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report Alert on-Demand Trigger"
        self.alert_name = "TC_58825_%s" % str(int(time.time()))
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.alert_window = None
        self.alert_settings = None
        self.table = None
        self.viewer = None
        self.mail = None
        self.mail_browser = None
        self.alert_mail = None
        self.condition_string = None
        self.report_url = None
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
        """ Deletes the alert which contain 'Automation_tc_58825_' in alert name """
        self.navigator.goto_alerts_configuration()
        self.alert_settings.cleanup_alerts("TC_58825_")

    @test_step
    def create_alert(self):
        """Create alert"""
        data = self.table.get_table_data()
        column_name = list(data)[0]
        if not data[column_name]:
            raise CVTestStepFailure("Report [%s] might be empty. Please verify!", self.name)
        self.condition_string = data[column_name][0]
        self.report_url = self.browser.driver.current_url
        self.log.info("Creating alert for [%s] report for [%s] column with condition string:"
                      "[%s]", self.alert_name, column_name, self.condition_string)
        self.table.configure_alert()
        self.alert_window.create_alert(alert_name=self.alert_name, column_name=column_name,
                                       column_value=self.condition_string)
        self.log.info("Alert [%s] created successfully on [%s] report ", self.alert_name,
                      self.name)

    @test_step
    def edit_alert(self):
        """Edit existing alert: update alert name"""
        self.navigator.goto_alerts_configuration()
        self.log.info("Editing [%s] alert" % self.alert_name)
        self.alert_window = self.alert_settings.edit_alert(self.alert_name)
        self.alert_name = self.alert_name + "_edited"
        self.alert_window.set_name(self.alert_name)
        time.sleep(1)
        self.alert_window.save()
        time.sleep(5)  # wait for alert page to refresh after edit
        self.log.info("Alert updated successfully as [%s]" % self.alert_name)

    @test_step
    def run_alert(self):
        """Trigger Alert on demand"""
        self.log.info("Running [%s] alert" % self.alert_name)
        self.alert_settings.trigger_alert([self.alert_name])
        self.log.info("Alert triggered successfully")

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
        self.utils.reset_temp_dir()
        self.utils.download_mail(self.mail, subject=self.alert_name)
        self.access_report()
        self.access_email_file()
        web_report_table_data = self.get_report_content(self.condition_string)
        mail_report_name = self.alert_mail.get_report_name()
        if mail_report_name != self.name:
            raise CVTestStepFailure("Report names are not matching with mail content, "
                                    "report name in mail:%s,report name in webconsole:%s",
                                    mail_report_name, self.name)
        mail_report_link = self.alert_mail.get_report_link()
        if mail_report_link != self.report_url:
            raise CVTestStepFailure("Report links are not matching with mail content, report "
                                    "link in mail:%s, report link in webconsole:%s",
                                    mail_report_link, self.report_url)
        mail_table_data = self.alert_mail.get_table_data()
        if mail_table_data != [list(web_report_table_data[0])]:
            err_str = "Table data in report is not matching with mail content, table data " \
                      "in mail:%s,report data in webconsole:%s", str(mail_table_data), \
                      str(web_report_table_data)
            raise CVTestStepFailure(err_str)
        self.log.info("Email content is matched successfully with report content for the "
                      "report [%s]", self.name)

    @test_step
    def delete_alert(self):
        """
        Delete alerts
        """
        self.navigator.goto_alerts_configuration()
        self.alert_settings.delete_alerts([self.alert_name])

    def run(self):
        try:
            self.init_tc()
            self.access_report()
            self.create_alert()
            self.edit_alert()
            self.run_alert()
            self.log.info("Wait for mails to be received for 5 minutes")
            time.sleep(300)
            self.validate_alert_email()
            self.delete_alert()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.mail_browser)
