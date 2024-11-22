# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

Web automation to test custom alert as tenant admin

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
"""

import os

from AutomationUtils import constants, commonutils
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
from Web.AdminConsole.AdminConsolePages.Roles import Roles
from Web.Common.exceptions import CVWebAutomationException

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Web automation to test custom alert as tenant admin"
        self.browser = None
        self.admin_console = None
        self.exp = None
        self.subclients = None
        self.tcinputs = {
            "companyName": None,
            "tenantAdminUsername": None,
            "tenantAdminPassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.cs_user = self.inputJSONnode['commcell']['commcellUsername']
        self.cs_password = self.inputJSONnode['commcell']['commcellPassword']
        self.company_name = self.tcinputs['companyName']
        self.tenant_admin_username = self.tcinputs['tenantAdminUsername']
        self.tenant_admin_password = self.tcinputs['tenantAdminPassword']
        self.alert_name = None
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.cs_user, self.cs_password)
        self.navigator = self.admin_console.navigator
        self.alert_helper = RAlertMain(self.admin_console)
        self.alerts = Ralerts(self.admin_console)
        self.alert_definitions = RAlertDefinitions(self.admin_console)
        self.roles = Roles(self.admin_console)
        self.alert_rules = AlertRules(self.admin_console)
        self.alert_rule_details = AlertRuleDetails(self.admin_console)
        self.alert_path = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server','Alerts','CustomAlertXml','TFA_disabled.xml')

    def run(self):
        """Run function of this test case"""

        try:
            # Create a role to for tenant admin to execute alert rule
            self.commcell.roles.add("Execute Alert", ["Execute"])

            # import alert rule
            self.navigator.navigate_to_alert_rules()
            self.alert_rules.import_alert_rule(self.alert_path)

            # add role to the alert rule
            self.alert_rule_details.edit_security({f"{self.company_name}\Tenant Admin":["Execute Alert"]})

            # switch to company persona
            self.navigator.switch_company_as_operator(self.company_name)

            # create alert using the imported alert rule
            self.alert_name = "Test Custom Alert " + commonutils.get_random_string()
            self.alert_rule_details.click_add_alert_definition()
            self.alert_definitions.create_alert_definition({
                "general":{
                    "input":[{"id":"name", "text_to_fill":self.alert_name}]
                },
                "criteria":{
                    "checkbox":[{"label":"Include company groups which had TFA disabled"}],
                },
                "notification":{
                    "locale":"English",
                    "console":{
                        "to":[f"{self.company_name}\\Tenant Admin"],
                        "content":self.alert_name
                    },
                    "email":{
                        "to": [f"{self.company_name}\\Tenant Admin", "testautomation3@devmgt.commvault.com"],
                        "format":"HTML",
                        "content":self.alert_name
                        },
                    }
                })

            # login as tenant admin to see triggered alert
            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(self.tenant_admin_username, self.tenant_admin_password)

            # trigger the alert
            self.commcell.organizations.get(self.company_name).enable_tfa()
            self.commcell.organizations.get(self.company_name).disable_tfa()

            # validate the alert
            alert_notif_text = self.alert_helper.get_alert_notification_text(self.alert_name, wait=900)
            if alert_notif_text != self.alert_name:
                raise CVWebAutomationException("Alert notification text not as expected")


        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.roles.delete("Execute Alert")
        try:
            self.commcell.alerts.delete(self.alert_name)
        except:
            pass
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
