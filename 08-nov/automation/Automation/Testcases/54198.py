# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

AdminConsole - Credential Manager - Verify if owner accounts can view/edit/delete credentials
and non-owner accounts cannot view/edit/delete credentials

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.userhelper import UserHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.credential_manager_helper import CredentialManagerHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

                "54198":
                {
                "account_type": "Windows Account"
                }

        """

        super(TestCase, self).__init__()
        self.name = "Verify if credentials are visible to owner " \
                    "accounts and not visible to non-owner accounts"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.credential_manager_helper = None
        self.user_helper = None
        self.tcinputs = {
            "account_type": None
        }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.credential_manager_helper = CredentialManagerHelper(self.admin_console)
        self.user_helper = UserHelper(self.commcell)

    def run(self):

        try:
            password = self.user_helper.password_generator(3, 12)
            self.user_helper.create_user(user_name='credential_54198', email='credential54198@commvault.com',
                                         full_name='credential_54198', password=password)

            self.credential_manager_helper.account_type = self.tcinputs['account_type']
            self.credential_manager_helper.credential_name = "test54198"
            self.credential_manager_helper.new_credential_name = "newtest54198"
            self.credential_manager_helper.credential_username = "test54198"
            self.credential_manager_helper.credential_password = password

            self.log.info("*********Adding a credential*********")
            self.credential_manager_helper.add_credential()

            self.log.info("*********Verifying visibility of credential in "
                          "owner and non owner accounts*********")
            self.admin_console.logout()

            self.log.info("Logging in through non owner account and "
                          "verifying if credential is not visible.")

            self.admin_console.login(username="credential_54198", password=password)

            if self.credential_manager_helper.verify_cred_visibility():
                raise Exception("Credential is visible to non-owner account")

            self.admin_console.logout()

            self.log.info("Logging in through owner account and verifying if credential is visible.")
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.credential_manager_helper.credential_username = "newtest54198"
            self.credential_manager_helper.credential_password = password

            self.log.info("Verifying if owner account is able to edit the credential")
            self.credential_manager_helper.edit_credential()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean up the test case environment created """
        try:

            self.credential_manager_helper.delete_credential()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.user_helper.cleanup_users("credential_54198")
