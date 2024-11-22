# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

This test case verifies the Clients not backed up for X minutes alert

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
"""

import time
import os

from AutomationUtils import constants
from AutomationUtils.config import get_config

from Reports.utils import TestCaseUtils
from AutomationUtils.mail_box import MailBox

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.AlertRules import AlertRules
from Web.AdminConsole.AdminConsolePages.AlertRuleDetails import AlertRuleDetails
from Web.AdminConsole.AdminConsolePages.AlertDetails import AlertDetails
from Web.AdminConsole.AdminConsolePages.AlertDefinitions import RAlertDefinitions
from Web.AdminConsole.AdminConsolePages.Alerts import Ralerts
from Web.AdminConsole.Helper.AlertHelper import RAlertMain

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Web automation for Clients not backed up for X minutes alert"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None

    def setup(self):
        """Setup function of this test case"""
        
        self.cs_user = self.inputJSONnode['commcell']['commcellUsername']
        self.cs_password = self.inputJSONnode['commcell']['commcellPassword']
        self.config = get_config()
        self.mailbox = MailBox()
        self.utils = TestCaseUtils(self)
        self.mailbox.connect()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.cs_user, self.cs_password)
        self.alert_rules = AlertRules(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.alert_helper = RAlertMain(self.admin_console)
        self.alerts = Ralerts(self.admin_console)
        self.alert_rule_details = AlertRuleDetails(self.admin_console)
        self.alert_definitions = RAlertDefinitions(self.admin_console)
        alert_path = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server','Alerts','CustomAlertXml','Clients not backed up for X minutes.xml')
        self.navigator.navigate_to_developer_tools()
        self.navigator.navigate_to_alert_rules()
        self.alert_rules.import_alert_rule(alert_path)
        self.admin_console.driver.back()
        

    def run(self):
        """Run function of this test case"""

        try:            
            
            # # 1) Create alert using the "Clients not backed up for X minutes"
            self.alert_rules.access_alert_rule('Clients not backed up for X minutes')

            # # 2) Create custom alert
            self.alert_rule_details.click_add_alert_definition()
            self.log.info("Creating custom alert")
            self.alert_definitions.create_alert_definition({
                "general":{
                    "input":[{"id":"name", "text_to_fill":"Test Custom Alert"}],
                    "dropdown":[{"id":"alertType", "options_to_select":["Clients not backed up for X minutes"]}]
                },
                "criteria":{
                    "input":[{"id":"BackupThresholdinMins", "text_to_fill":"1"}]
                },
                "target":{
                    "combobox":[{"id":"toUsersAutoComplete", "options_to_select":["Administrator", "testautomation3"]}],
                },
                "template":{
                    "email":{"subject":"Test Custom Alert", "content":"Test Custom Alert"},
                    "console":{"content":"Test Custom Alert"}
                }
            })

            # 3) Trigger the alert (assuming cs has at least one client)
            time.sleep(180)
            
            # 4) Validate the alert triggering
            alert_notif_text = self.alert_helper.get_alert_notification_text("Test Custom Alert")
            if alert_notif_text != "Test Custom Alert":
                raise Exception("Alert template not modified as expected")
            self.validate_alert_email("Test Custom Alert")

            # 5) delete the custom alert
            self.alert_helper.navigate_and_delete_custom_alert("Test Custom Alert")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
        self.mailbox.disconnect()
    
    @test_step
    def validate_alert_email(self, alert_name):
        """ Validate alert email """
        
        self.log.info("verifying [%s] alert email", alert_name)
        self.utils.download_mail(self.mailbox, subject=alert_name)
        self.log.info("Alert [%s] mail validated", alert_name)
