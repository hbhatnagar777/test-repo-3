# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

This test case verifies the functional cases on alert rule details page

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
"""

import os

from AutomationUtils import logger, constants, commonutils
from AutomationUtils.config import get_config

from Reports.utils import TestCaseUtils
from AutomationUtils.mail_box import MailBox

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVWebAutomationException
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
        self.name = "Functional testing on alert rule listing page"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None
        self.logger = logger.get_log()

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
        self.alert_details = AlertDetails(self.admin_console)
        self.alert_helper = RAlertMain(self.admin_console)
        self.navigator.navigate_to_developer_tools()
        self.navigator.navigate_to_alert_rules()
        alert_path = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server','Alerts','CustomAlertXml','Alert to notify if activity at Commcell level is disabled.xml')
        self.alerts = Ralerts(self.admin_console)
        self.alert_rules.import_alert_rule(alert_path)
        self.admin_console.driver.back()
        self.alert_rule_details = AlertRuleDetails(self.admin_console)
        self.alert_definitions = RAlertDefinitions(self.admin_console)
        

    def run(self):
        """Run function of this test case"""

        try:            
            alert_name = "Test Custom Alert " + commonutils.get_random_string()
            # 1) Create alert using the "Alert to notify if activity at
            # Commcell level is disabled"
            self.alert_rules.access_alert_rule('Alert to notify if activity at Commcell level is disabled')

            # 2) Export the alert rule
            self.alert_rule_details.export_alert_rule()

            # 3) Create custom alert using that rule
            self.alert_rule_details.click_add_alert_definition()
            self.alert_definitions.create_alert_definition({
                "general":{
                    "input":[{"id":"name", "text_to_fill":alert_name}],
                    "dropdown":[{"id":"alertType", "options_to_select":["Alert to notify if activity at Commcell level is disabled"]}],
                    "toggle":[{"id":"sendIndividualNotifications"}]
                },
                # "target":{
                #     "combobox":[{"id":"toUsersAutoComplete", "options_to_select":["Administrator", "testautomation3"]}],
                # },
                # "template":{
                #     "email":{"subject":alert_name, "content":alert_name},
                #     "console":{"content":alert_name}
                # }
                "notification":{
                    "locale":"English",
                    "console":{
                        "to":["Administrator", "testautomation3@devmgt.commvault.com"],
                        "subject":alert_name,
                        "content":alert_name
                    },
                    "email":{
                        "to":["Administrator", "testautomation3@devmgt.commvault.com"],
                        "locale":"English",
                        "subject":alert_name,
                        "content":alert_name,
                    }
                }
            })

            # 4.a) Trigger the alert
            self.commcell.activity_control.set("AUX COPY", "Disable")
            
            # 4.b) Validate the alert triggering
            alert_notif_text = self.alert_helper.get_alert_notification_text(alert_name, wait=900)
            if alert_notif_text != alert_name:
                raise CVWebAutomationException("Alert notification text not changed as expected")
            self.validate_alert_email(alert_name)

            # 4.c) Delete the alert notification
            self.alerts.delete_alert_notification(alert_name)

            # 5) Enable the activity back
            self.commcell.activity_control.set("AUX COPY", "Enable")

            # 6) Change alert name and verify
            self.navigator.navigate_to_alerts()
            self.alerts.select_alert_definitions()
            self.alert_definitions.select_alert(alert_name)

            self.alert_details.edit_alert_name("Test Custom Alert Modified")
            self.navigator.navigate_to_alerts()
            self.alerts.select_alert_definitions()
            self.alert_definitions.select_alert("Test Custom Alert Modified")

            # 7) delete the custom alert
            self.alert_details.delete_alert()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.commcell.activity_control.set("AUX COPY", "Enable")
            self.commcell.alerts.delete(self.alert_name)
            self.commcell.alerts.delete("Test Custom Alert Modified")
        except:
            pass
        self.browser.close()
        self.mailbox.disconnect()
    
    
    @test_step
    def validate_alert_email(self, alert_name):
        """ Validate alert email """
        
        self.log.info("verifying [%s] alert email", alert_name)
        self.utils.download_mail(self.mailbox, subject=alert_name)
        self.log.info("Alert [%s] mail validated", alert_name)
