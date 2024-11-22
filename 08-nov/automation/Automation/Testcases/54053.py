# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks for Reseller model

Steps in this test case:
    Create a test user

    Assign Tenant Operator role  to that user

    Login to AdminConsole using the test user.

    Delete the test user.

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.userhelper import UserHelper, UserProperties
from Server.serverhelper import ServerTestCases
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.adminconsole import AdminConsole
from Server.Security.userconstants import USERGROUP, WebConstants
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Tenant Operator Check test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Test Case for Reseller Model"
        self.commcell_obj = None
        self._server_tc = None
        self._user_helper = None
        self.log = None
        self._user_list = None
        self.show_to_user = False
        self._roles_helper = None
        self.tcinputs = {
            "Email": None,
            "ADUserName": None,
            "ADUserPassword": None,
            "DomainName": None,
            "CompanyName": None
        }
    def setup(self):
        """Setup function of this test case"""
        self.commcell_obj = self._commcell
        self._server_tc = ServerTestCases(self)
        self._user_helper = UserHelper(self.commcell_obj)
        user1 = UserProperties(name='Test_100', cs_host=self.commcell_obj.commserv_hostname,
                               email=self.tcinputs["Email"], password='######',
                               full_name='Test User')
        user2 = UserProperties(name=self.tcinputs["ADUserName"], cs_host=self.commcell_obj.commserv_hostname,
                               email=self.tcinputs["Email"], password=self.tcinputs["ADUserPassword"],
                               domain=self.tcinputs["DomainName"])
        self._user_list = [user1, user2]

    def run(self):
        """Main function for test case execution"""

        self._server_tc.log_step(
            """
            Test Case
            1) Creates local user and domain user and then adds him to local group
            2) Set operator role for a company given in the input for both the users
            3) Login into adminconsole using both the users
            4) User should be able to see the company
            """, 200
        )

        organization_object = self.commcell_obj.organizations.get(self.tcinputs["CompanyName"])
        factory = BrowserFactory()
        browser = factory.create_browser_object()
        browser.open()
        driver = browser.driver

        try:
            for user in self._user_list:
                if user.domain:
                    domain_user = "{0}\\{1}".format(user.domain, user.username)
                    user.username = domain_user
                # delete user if already exists
                self._user_helper.delete_user(user.username, new_user='admin')
                #create new user with same name
                self._server_tc.log_step("""step 1: Creates User and adds him to local group""")
                self._user_helper.create_user(user_name=user.username,
                                              full_name=user.full_name,
                                              email=user.email,
                                              password=user.password,
                                              local_usergroups=[USERGROUP.MASTER])
                self._server_tc.log_step("""step 2: Assigns user as a tenant operator of the given company""")
                organization_object.add_users_as_operator([user.username], "UPDATE")
                tenant_operators = organization_object.tenant_operator
                if user.username in tenant_operators:
                    self._server_tc.log_step("""Operator role assigned successfully""")
                else:
                    raise Exception("Operator role is not assigned.")
                self._server_tc.log_step("""step 3: Updates the role associated with the tenant operator""")
                role_name = "Alert Owner"
                organization_object.operator_role = role_name
                if organization_object.operator_role != role_name:
                    raise Exception("Role name was not assigned.")
                self._server_tc.log_step("""step 4: Login into Adminconsole""")
                self.log.info("Creating the login object")
                login_obj = LoginMain(driver, self.csdb)
                login_obj.login(user.username, user.password)
                self.log.info("Login completed successfully")
                self.log.info("Login completed successfully")
                select_company = (AdminConsole(browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
                                  .navigator)
                self._server_tc.log_step("""step 5: Switching to company view""")
                select_company.switch_company_as_operator(self.tcinputs["CompanyName"])
                select_company.logout()
                hidden_tenant_operator = f'{self.tcinputs["CompanyName"]}\\{user.username}_Operator'
                self._server_tc.log_step("""step 6: Checking if hidden user for the company exists""")
                if not self._user_helper.check_if_hidden_user_exists(hidden_tenant_operator):
                    raise Exception("Hidden user not found.")
                self._server_tc.log_step("""step 7: Deleting the tenant operator user""")
                self._user_helper.delete_user(user.username, new_user='admin')
                self._server_tc.log_step("""step 8: Checking if hidden user created for tenant operator is deleted""")
                if self._user_helper.check_if_hidden_user_exists(hidden_tenant_operator):
                    raise Exception("Hidden user exists")
                self._server_tc.log_step("""step 8: Checking if operator is removed from company""")
                if not user.username in tenant_operators:
                    self._server_tc.log_step("""Operator role assigned successfully""")

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self._server_tc.log_step("""Test Case FAILED""", 200)
            self.result_string = str(exp)
            self.status = constants.FAILED
