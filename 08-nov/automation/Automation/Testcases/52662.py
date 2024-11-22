# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of Editing Plan Details in Admin console for
laptop plan.

functions over,
1. Creation of laptop plan based on different criteria's passed as
    arguments to the test case and base files.
2. Edits values and checks if the updated values are retained correctly.
3. Deletes the plan created, edited and verified in above steps.

Pre-requisites :
1. Index Server should be configured, if using Edge Drive Feature for Laptop Plam.
2. Primary and secondary storage pools should be configured.
"""

import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain


class TestCase(CVTestCase):
    """ Basic Acceptance Test for Editing Plan Details for laptop plan in AdminConsole """

    def __init__(self):
        """ Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for  Editing Laptop Plan Details in AdminConsole"
        self.browser = None
        self.admin_console = None
        self.plan_obj = None

        self.tcinputs = {
            "primary_storage": None,
            "secondary_storage": None,
        }

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

    def run(self):

        try:
            self.plan_obj = PlanMain(self.admin_console)
            self.plan_obj.plan_name = {"laptop_plan": "Automation_Laptop_plan_" + str(datetime.datetime.today().day)}
            self.plan_obj.allowed_features = {
                "Edge Drive": "OFF",
                "audit_drive_operations": "False",
                "notification_for_shares": "False",
                "edge_drive_quota": "150",
                "DLP": "OFF",
                "Archiving": "ON"
            }
            self.plan_obj.storage = {
                "pri_storage": self.tcinputs['primary_storage'],
                "pri_ret_period": "30",
                "ret_unit": "day(s)",
                "sec_storage": "",
                "sec_ret_period": ""
            }

            self.plan_obj.edit_plan_dict = {
                "throttle_send": "1000",
                "throttle_receive": "1000",
                "file_system_quota": "100",
                "rpo_hours": "31",
                "additional_storage": {
                    'storage_name': 'Secondary',
                    'storage_pool': self.tcinputs['secondary_storage'],
                },
                "allowed_features": {
                    "Edge Drive": "OFF",
                    "audit_drive_operations": "False",
                    "notification_for_shares": "False",
                    "edge_drive_quota": "150",
                    "DLP": "OFF",
                    "Archiving": "ON"
                },
                "backup_data": "",
                "region": "",
                "edit_storage": {},
                "override_restrictions": {
                    "Storage_pool": "Override optional",
                    "RPO": "Override not allowed",
                    "Folders_to_backup": "Override optional",
                    "Retention": "Override not allowed"
                }
            }
            self.plan_obj.backup_data = None
            self.plan_obj.user_usergroup_association = []
            self.plan_obj.user_usergroup_de_association = {
                "DeleteAll": "True",
                "DeleteAllUsers": "False",
                "DeleteAllUserGroups": "False",
                "Delete_Specific_user_usergroup": "False"
            }

            self.plan_obj.add_plan()
            self.plan_obj.edit_laptop_plan()
            self.plan_obj.validate_plan_details()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            self.plan_obj.remove_associations()
            self.plan_obj.delete_plans()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
