# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Basic acceptance test case for Credential Manager in AdminConsole

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.securityhelper import RoleHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.userhelper import UserHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.credential_manager_helper import CredentialManagerHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "54147":
                {
                "account_type": "Windows Account"
                }

        """

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Credential Manager in AdminConsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.credential_manager_helper = None
        self.user_helper = None
        self.user_group_helper = None
        self.role_helper = None
        self.role = "Credential_54147"
        self.permission_list = ['Use Credential']
        self.tcinputs = {
            "account_type": None
        }

    def setup(self):
        try:
            self.browser = BrowserFactory().create_browser_object(name="User Browser")
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.inputJSONnode['commcell']["commcellUsername"],
                password=self.inputJSONnode['commcell']["commcellPassword"])
            self.credential_manager_helper = CredentialManagerHelper(self.admin_console)
            self.user_helper = UserHelper(self.commcell)
            self.user_group_helper = UsergroupHelper(self.commcell)
            self.role_helper = RoleHelper(self.commcell)
        except Exception as exception:
            raise exception

    def run(self):

        try:
            password = self.user_helper.password_generator(3, 12)
            self.commcell.user_groups.add(usergroup_name='credential_group')
            self.user_helper.create_user(user_name='credential_user', email='credential@commvault.com',
                                         full_name='credential_user', password=password)

            self.role_helper.create_role(role_name=self.role,
                                         permission_list=self.permission_list)

            self.credential_manager_helper.account_type = self.tcinputs['account_type']
            self.credential_manager_helper.credential_name = "test54147"
            self.credential_manager_helper.new_credential_name = "newtest54147"
            self.credential_manager_helper.credential_username = "test54147"
            self.credential_manager_helper.credential_password = password

            self.log.info("*********Adding a credential*********")
            self.credential_manager_helper.add_credential()

            self.log.info("*********Editing a credential*********")
            self.credential_manager_helper.credential_username = "newtest54147"
            self.credential_manager_helper.credential_password = password
            self.credential_manager_helper.user_or_group = ["credential_user", "credential_group"]
            self.credential_manager_helper.role = self.role

            self.credential_manager_helper.edit_credential()

            self.log.info("*********Adding security association*********")
            self.credential_manager_helper.update_security()

            self.admin_console.logout()
            self.admin_console.wait_for_completion()

            self.credential_manager_helper.credential_name = self.credential_manager_helper.new_credential_name
            self.log.info("*********Attempting edit/delete from non-owner account*********")
            self.admin_console.login(username="credential_user", password=password)

            self.credential_manager_helper.credential_username = "test54147"

            self.credential_manager_helper.attempt_edit_delete_non_owner()
            self.admin_console.logout()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        try:
            self.admin_console.login(
                username=self.inputJSONnode['commcell']["commcellUsername"],
                password=self.inputJSONnode['commcell']["commcellPassword"])
            self.credential_manager_helper.credential_name = self.credential_manager_helper.new_credential_name
            self.credential_manager_helper.delete_credential()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.role_helper.delete_role(self.role)
            self.user_helper.cleanup_users("credential_user")
            self.user_group_helper.cleanup_user_groups('credential_group')
