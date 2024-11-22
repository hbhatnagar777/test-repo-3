# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of Alerts in Admin console.

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase
"""

import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.AlertHelper import AlertMain


class TestCase(CVTestCase):
    """ Basic Acceptance test for Alerts """

    def __init__(self):
        """ Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test Alerts in AdminConsole"
        self.browser = None
        self.admin_console = None
        self.alert_obj = None

        self.tcinputs = {
            'client_name': None,
            'plan_name': None
        }

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        security_role = {
            "assoc1":
                {
                    'clientName': [self.commcell.commserv_name],
                    'role': ["View"]
                }
        }
        self.commcell.users.add(user_name="51142-tester", email='TestAutomation3@commvault.com',
                                password="Testing@51142", entity_dictionary=security_role)

    def run(self):
        try:
            self.alert_obj = AlertMain(self.admin_console)
            self.alert_obj.alert_name = "Restore_Alert " + str(datetime.datetime.today())
            self.alert_obj.alert_criteria = "Restore Job Succeeded"
            self.alert_obj.recipients = {
                "To": {
                    "Group": [
                        "master"
                    ],
                    "Email": [],
                    "User": []
                },
                "Cc": {
                    "Group": [],
                    "Email": [
                        "TestAutomation3@commvault.com"
                    ],
                    "User": []
                },
                "Bcc": {
                    "Group": [],
                    "Email": ["TestAutomation3@commvault.com"],
                    "User": []
                }
            }
            self.alert_obj.client_name = self.tcinputs['client_name']
            self.alert_obj.subclient_name = "Test_01"
            self.alert_obj.plan_name = self.tcinputs['plan_name']
            self.alert_obj.alert_target = {
                "Email": True,
                "Event viewer": True,
                "Console": True,
                "SNMP": False
            }

            self.alert_obj.add_alert_definition()
            self.alert_obj.create_fs_subclient()
            self.alert_obj.perform_fs_subclient_backup()
            self.alert_obj.perform_fs_subclient_restore()
            self.alert_obj.validate_triggered_alert()

            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login("51142-tester", "Testing@51142")

            self.alert_obj.add_alert_definition()

            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            self.commcell.users.delete(user_name="51142-tester", new_user="admin")
            self.alert_obj.delete_test_subclient()
            self.alert_obj.delete_alert_definition()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
