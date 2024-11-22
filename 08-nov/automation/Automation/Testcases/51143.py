# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

'''
Test case to check the basic acceptance of Plans in Admin console.

functions over,
1. Creation of Alerts based on different criteria's passed as
   arguments to the test case and base files.
2. Validates if the alerts are created successfully, edits the values provided
    and are retained correctly in both cases.
3. Enables and disables alerts and verifies the triggering is working fine.
4. Deletes the alerts created & verified in above steps.

'''

import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.AlertHelper import AlertMain
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils

class TestCase(CVTestCase):
    ''' Basic Acceptance test for Alerts '''
    def __init__(self):
        '''
       Initializing the Test case file
        '''
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test Alerts in AdminConsole"
        self.admin_console = None
        self.browser = None
        self.alert_obj = None
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            'client_name': None,
            'plan_name': None,
            'backup_set': None
        }

    def run(self):

        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.alert_obj = AlertMain(self.admin_console, self.commcell, self.csdb)

            self.alert_obj.alert_name = "Backup_Alert " + str(datetime.datetime.today())
            self.alert_obj.alert_criteria = "Backup Job Succeeded"
            self.alert_obj.client_name = self.tcinputs['client_name']
            self.alert_obj.plan_name = self.tcinputs['plan_name']
            self.alert_obj.backup_set = self.tcinputs['backup_set']

            self.alert_obj.subclient_name = "test_subclient " + str(datetime.datetime.today())
            self.alert_obj.alert_target = {
                                                "Email": True,
                                                "Event viewer": False,
                                                "Console": True,
                                                "SNMP": False
                                          }
            self.alert_obj.recipients = {"To": {
                                            "Group": [],
                                            "Email": ["TestAutomation3@commvault.com"],
                                            "User": ["admin"]
                                            },
                                            "Bcc": {
                                                "Group": [],
                                                "Email": ["TestAutomation3@commvault.com"],
                                                "User": []
                                            },
                                            "Cc": {
                                                "Group": [],
                                                "Email": ["TestAutomation3@commvault.com"],
                                                "User": []
                                            }
                                        }
            self.alert_obj.ind_notification = 'ON'
            self.alert_obj.alert_entities = {
                                                'server_group_list': ['Server groups'],
                                                'server_list': ['Servers']
                                            }
            self.alert_obj.alert_target = {
                                                "Email": True,
                                                "Event viewer": True,
                                                "Console": True,
                                                "SNMP": False
                                          }
            self.alert_obj.update_recipients = {
                                                    "To": {
                                                        "Add": {
                                                            "Group": [],
                                                            "Email": ["abc@commvault.com"],
                                                            "User": []
                                                        },
                                                        "Remove": {
                                                            "Group": [],
                                                            "Email": [],
                                                            "User": []
                                                        }
                                                    },
                                                    "Bcc": {
                                                        "Add": {
                                                            "Group": [],
                                                            "Email": [],
                                                            "User": []
                                                        },
                                                        "Remove": {
                                                            "Group": [],
                                                            "Email": [],
                                                            "User": []
                                                        }
                                                    },
                                                    "Cc": {
                                                        "Add": {
                                                            "Group": [],
                                                            "Email": ["abc@commvault.com"],
                                                            "User": []
                                                        },
                                                        "Remove": {
                                                            "Group": [],
                                                            "Email": [],
                                                            "User": []
                                                        }
                                                    }
                                                }

            self.alert_obj.add_alert_definition()
            self.alert_obj.validate_alert_definition()
            self.alert_obj.edit_alert_definition()
            self.alert_obj.validate_alert_definition()
            self.alert_obj.create_fs_subclient()
            self.alert_obj.disable_and_validate()
            self.alert_obj.enable_and_validate()
            self.alert_obj.delete_curr_triggered_alert()
            self.alert_obj.clear_triggered_alerts()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.alert_obj.delete_test_subclient()
            self.alert_obj.delete_alert_definition()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
