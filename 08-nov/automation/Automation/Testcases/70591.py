# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

This test case verifies alert rule "Restore Job failed"

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
"""

import time

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
        self.name = "Web automation for Restore Job failed alert"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None
        self.subclients = None
        self.tcinputs = {
            "clientName": None,
            "instanceName": None,
            "storagePolicy": None,
            "restorePath": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.cs_user = self.inputJSONnode['commcell']['commcellUsername']
        self.cs_password = self.inputJSONnode['commcell']['commcellPassword']
        self.client_name = self.tcinputs['clientName']
        self.instance_name = self.tcinputs['instanceName']
        self.storage_policy = self.tcinputs['storagePolicy']
        self.restore_path = self.tcinputs['restorePath']
        self.client_obj = None
        self.instance_obj = None
        self.subclient_obj = None
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
        self.alerts = Ralerts(self.admin_console)
        self.alert_rule_details = AlertRuleDetails(self.admin_console)
        self.alert_definitions = RAlertDefinitions(self.admin_console)
        self.client_obj = self.commcell.clients.get(self.client_name)
        self.agent_obj = self.client_obj.agents.get('file system')
        self.instance_obj = self.agent_obj.instances.get(self.instance_name)
        self.subclients = self.instance_obj.subclients
        self.subclient_obj = self.subclients.get("default")

    def run(self):
        """Run function of this test case"""

        try:
            # 1) Navigating to alert definitions page
            self.navigator.navigate_to_alerts()
            self.alerts.select_alert_definitions()

            # 2) adding the alert definition
            self.alert_definitions.select_add_alert_definitions()
            self.alert_definitions.create_alert_definition({
                "general":{
                    "input":
                    [
                        {"id":"name", "text_to_fill":"Test Custom Alert"}
                    ],
                    "dropdown":
                    [
                        {"id":"alertType", "options_to_select":["Restore Job Failed"]}
                    ]
                },
                "entities":{
                    "checkbox":
                    [
                        {"label":"Server groups"},
                        {"label":"Servers"}
                    ]
                },
                "criteria":{
                    "checkbox":[
                        {"label": "Restore Job Failed"}
                    ]
                },
                "target":{
                    "combobox":
                    [
                        {"id":"toUsersAutoComplete", "options_to_select":["Administrator", "testautomation3"]}
                    ],
                },
                "template":{
                    "email":
                    {
                        "subject":"Test Custom Alert",
                        "content":"<ALERT CATEGORY - ALERT TYPE>| <DETECTED CRITERIA>| <JOB ID>| <CLIENT DISPLAY NAME>| <SUBCLIENT NAME>| <FAILURE REASON>"
                    },
                    "console":
                    {
                        "content":"<ALERT CATEGORY - ALERT TYPE>| <DETECTED CRITERIA>| <JOB ID>| <CLIENT DISPLAY NAME>| <SUBCLIENT NAME>| <FAILURE REASON>"
                    }
                }
            })

            # 3) Triggering the Alert by Running Restore
            self.log.info("Restoring")
            restore_job = self.subclient_obj.restore_out_of_place(client=self.client_name, destination_path="A:\\DoesNotExist", paths=[self.restore_path],overwrite=False, fs_options={'no_of_streams': 10})
            restore_job.wait_for_completion()
            time.sleep(60)

            # 4) Validate the alert triggering
            self.log.info("Validating the alert triggering")

            text_to_verify = ["Job Management - Data Recovery", "Job Failed", str(restore_job.job_id), self.client_name, "default", "Failed to restore even a single file"]
            self.alert_helper.validate_console_notification("Test Custom Alert", text_to_verify)
            
            self.utils.download_mail(self.mailbox, subject="Test Custom Alert")
            self.alert_helper.validate_alert_email("Test Custom Alert", 
                                                   self.utils.get_temp_dir(),
                                                    text_to_verify)

            # 5) delete the custom alert
            self.log.info("Deleting the custom alert")
            self.alert_helper.navigate_and_delete_custom_alert("Test Custom Alert")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""

        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
        self.mailbox.disconnect()


    @test_step
    def create_broken_subclient(self, subclients, new_subclient_name, broken_path):
        """ 
            Create a broken subclient 

            Args:
                subclients (obj): Subclients object
                new_subclient_name (str): Name of the new subclient
                broken_path (str): Path that does not exist

            Returns:
                Subclient: Subclient object
        """
        subclient_obj = subclients.add(new_subclient_name, self.storage_policy)
        subclient_obj.content = [broken_path]
        subclient_obj.refresh()
        return subclient_obj
