# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.AdminConsole.Reports.manage_alerts import TestCriteriaHealthTable, ManageAlerts
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.cte import ConfigureAlert
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep

from AutomationUtils import config

from Reports.utils import TestCaseUtils
from Reports import reportsutils
from Reports.storeutils import StoreUtils
from Web.WebConsole.Reports.Metrics.components import AlertMail

from Web.WebConsole.Reports.Metrics.health import HealthConstants
from Web.WebConsole.Reports import cte
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure

import datetime
import time
from AutomationUtils import mail_box
CONSTANTS = config.get_config()
REPORTS_CONFIG = reportsutils.get_reports_config()
Format = cte.ConfigureSchedules.Format


def rank_severity(severity):
    """Rank severity"""
    if severity == HealthConstants.STATUS_GOOD:
        rank = 1
    elif severity == HealthConstants.STATUS_WARNING:
        rank = 2
    else:
        rank = 3
    return rank


class TestCase(CVTestCase):
    """
       TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.manage_report = None
        self.name = "Alert on Health Tile"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.navigator = None
        self.health_tile = None
        self.alert_window = None
        self.alert_mail = None
        self.mail_browser = None
        self.util = StoreUtils(self)
        self.alert_name = "Automation_tc_60154_%s" % str(int(time.time()))
        self.mail = None
        self.recipient_id = CONSTANTS.email.email_id
        self.alert_settings = None
        self.tile_status = None
        self.tile_name = None

    def setup(self):
        """Setup function of this test case"""
        commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.mail = mail_box.MailBox()
        self.mail.connect()
        if not self.recipient_id:
            raise CVTestCaseInitFailure("Recipient's id is not specified in config file")
        download_directory = self.utils.get_temp_dir()
        # open browser
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(download_directory)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        # login to console
        self.admin_console.login(username=self.commcell.commcell_username,
                              password=commcell_password)
        self.navigator = self.admin_console.navigator
        self.manage_report = ManageReport(self.admin_console)
        self.navigator.navigate_to_metrics()
        # navigate to dashboard
        self.tile_name = self.tcinputs['tile_name']
        self.manage_report.access_commcell_health(self.commcell.commserv_name)
        self.alert_settings = ManageAlerts(self.admin_console)
        self.health_tile = GenericTile(self.admin_console, self.tile_name)
        self.tile_status = self.health_tile.get_health_status()
        self.health_tile.access_alert()
        self.alert_window = ConfigureAlert(self.admin_console)

    @test_step
    def validate_test_criteria(self, status):
        """ Test alert criteria page data validation"""
        self.alert_window.select_health_param(status)
        table_data = self.goto_test_criteria()
        if rank_severity(self.tile_status) < rank_severity(status):
            if table_data:
                raise CVTestStepFailure(f"Test Criteria table data is not empty for "
                                        f"Selected alert status: {status} where "
                                        f"Tile status: {self.tile_status} ")
        else:
            if not table_data:
                raise CVTestStepFailure(f"Test Criteria table data is empty for status, "
                                        f"Selected alert status: {status}.\n "
                                        f"Tile status: {self.tile_status} ")

    def create_alert(self, status):
        """Create alert for tile"""
        self.tile_status = self.health_tile.get_health_status()
        self.health_tile.access_alert()
        self.alert_window = ConfigureAlert(self.admin_console)
        self.alert_window.create_alert(alert_name=self.alert_name, criteria= status, is_health='Yes')

    def goto_test_criteria(self):
        """open test criteria window and fetch data"""
        self.alert_window.check_test_criteria()
        alert_criteria_table = TestCriteriaHealthTable(self.admin_console)
        table_data = alert_criteria_table.get_alert_table_data()
        self.close_alert_criteria_window()
        return table_data

    def run_alert(self):
        """ Run alert """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.alert_settings.run_alerts([self.alert_name])

    @test_step
    def verify_alerts(self, status):
        """Create alert, verify alert mail received"""
        self.create_alert(status)
        self.log.info("Wait for 3 minutes for alert mails to be received")
        self.run_alert()
        time.sleep(180)
        if rank_severity(self.tile_status) >= rank_severity(status):
            self.validate_alert_email()

        if rank_severity(self.tile_status) < rank_severity(status):
            try:
                self.utils.download_mail(self.mail, subject=self.alert_name)
                raise CVTestStepFailure(f"Alert Mail received for selected alert status: {status} where "
                                        f"tile status is: {self.tile_status} ")
            except Exception as e:
                if "email is not found" in str(e):
                    self.log.info(f"Alert Mail not found as criteria did not override."
                                  f"Selected alert status: {status}.\n Tile status: {self.tile_status}")

        self.delete_alert()
        self.navigator.navigate_to_metrics()
        self.manage_report.access_commcell_health(self.commcell.commserv_name)

    def close_alert_criteria_window(self):
        """
        close alert criteria window
        """
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])

    def access_email_file(self):
        """Access email downloaded file in browser"""
        html_path = self.utils.poll_for_tmp_files(ends_with='html')[0]
        self.mail_browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.mail_browser.open()
        self.mail_browser.goto_file(file_path=html_path)
        self.alert_mail = AlertMail(self.mail_browser)

    def validate_alert_email(self):
        """Validate alert email"""
        self.utils.reset_temp_dir()
        self.utils.download_mail(self.mail, subject=self.alert_name)
        self.access_email_file()
        alert_mail_name = self.alert_mail.get_alert_name()

        if alert_mail_name != self.alert_name:
            raise CVTestStepFailure("Alert tile name not matching with tile name on email, "
                                    "alert name in mail:%s,alert name in webconsole:%s" %
                                    (alert_mail_name, self.alert_name))

        alert_mail_data = self.alert_mail.get_bold_data()

        if alert_mail_data[3] != self.commcell.commserv_name:
            raise CVTestStepFailure("Commserve name on alert mail not matching with commserve name on webconsole,"
                                    "Commserve name in mail:%s,Commserve name in webconsole:%s" %
                                    (alert_mail_data[3], self.commcell.commserv_name))

        if alert_mail_data[6] != self.tile_name:
            raise CVTestStepFailure("Tile name on alert mail not matching with Tile name on webconsole, "
                                    "Tile name in mail:%s,Tile name in webconsole:%s" %
                                    (alert_mail_data[6], self.tile_name))

    def delete_alert(self):
        """
        Delete alert
        """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.alert_settings.delete_alerts([self.alert_name])

    @test_step
    def cleanup_alerts(self):
        """ Deletes the alerts which contain 'Automation_tc_60154' in alert name """
        self.navigator.navigate_to_reports()
        self.manage_report.view_alerts()
        self.alert_settings.cleanup_alerts("Automation_tc_60154")

    def run(self):
        try:
            self.validate_test_criteria(HealthConstants.STATUS_CRITICAL)
            self.validate_test_criteria(HealthConstants.STATUS_WARNING)
            self.validate_test_criteria(HealthConstants.STATUS_GOOD)
            self.alert_window.cancel()
            self.verify_alerts(HealthConstants.STATUS_CRITICAL)
            self.verify_alerts(HealthConstants.STATUS_WARNING)
            self.verify_alerts(HealthConstants.STATUS_GOOD)
            self.cleanup_alerts()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.mail.disconnect()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.mail_browser)
