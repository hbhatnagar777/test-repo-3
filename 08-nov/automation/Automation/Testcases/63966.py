# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Basic login test case for Restricted Console

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    adminconsole_login()        --  Login verification for admin console

    q_login()                   --  Login verification for qlogin

    api_login()                 --  Login verification for api login

    run()                       --  Contains the core testcase logic, and it is the one executed

    tear_down()                 --  Clean up entities

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.UserGroups import UserGroups as UserGroupsHelp
from Web.AdminConsole.AdminConsolePages.UserGroupDetails import UserGroupDetails
from Web.AdminConsole.AdminConsolePages.UserDetails import AccessToken
from Server.Security.user_login_validator import LoginValidator
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.organizationhelper import OrganizationHelper
from Server.RestAPI.restapihelper import RESTAPIHelper
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "63966":
                {
                "external_user_group": "domain\\user_group",
                "external_user": "domain\\username",
                "external_user_password": "###"
                }

        """

        super(TestCase, self).__init__()

        self.name = "Basic Restricted Console"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.result_string = "Successful"
        self.validator = None
        self.browser = None
        self.admin_console = None
        self.restapi = None
        self.access_token = None
        self.commcell_helper = None
        self.organization_helper = None
        self.user_helper = None
        self.securitygroup = None
        self.navigator = None
        self.company = None
        self.company_details = None
        self.usergroupshelp = None
        self.usergroupdetails = None
        self.dialog = None
        self.tcinputs = {
            "external_user_group": None,
            "external_user": None,
            "external_user_password": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']["commcellUsername"],
            password=self.inputJSONnode['commcell']["commcellPassword"])
        self.commcell_helper = Commcell(self.admin_console)
        self.usergroupshelp = UserGroupsHelp(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.validator = LoginValidator(self)
        self.company = Companies(self.admin_console)
        self.company_details = CompanyDetails(self.admin_console)
        self.user_helper = UserHelper(self.commcell)
        self.securitygroup = UsergroupHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.usergroupdetails = UserGroupDetails(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.restapi = RESTAPIHelper()

    @test_step
    def adminconsole_login(self, username, password, isrestricted=True, isadmin=False):
        """*********Command Center Login*********"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        try:
            restricted_adminconsole = AdminConsole(browser, self.commcell.webconsole_hostname)
            restricted = False
            restricted_adminconsole.login(username, password)
            restricted_adminconsole.check_error_message()
            restricted = True
            self.log.info("Successfully logged in Command Center")
        except CVWebAutomationException as exp:
            if 'Access to this application is not permitted' in exp.args[0]:
                self.log.info("Restricted console is applied")
            else:
                handle_testcase_exception(self, exp)
        finally:
            if not isrestricted:
                AdminConsole.logout_silently(restricted_adminconsole)
            Browser.close_silently(browser)
            if restricted and isrestricted:
                raise Exception("user is able to login when restricted")
            if isadmin and not restricted:
                raise Exception("admin is unable to login when restricted")

    @test_step
    def q_login(self, username, password, isrestricted=True, isadmin=False):
        """*********Qlogin*********"""
        try:
            restricted = False
            self.user_helper.qlogin(username=username,
                                    password=password)
            restricted = True
        except Exception as exp:
            if 'You are restricted from logging on to this console' in exp.args[0]:
                self.log.info("Restricted console is applied")
            else:
                handle_testcase_exception(self, exp)
        if restricted and isrestricted:
            raise Exception("user is able to login when restricted")
        if isadmin and not restricted:
            raise Exception("admin is unable to login when restricted")

    @test_step
    def api_login(self, username, password, isrestricted=True, isadmin=False):
        """*********APILogin*********"""
        inputs = {"webserver": self.commcell.webconsole_hostname,
                  "username": username,
                  "password": password,
                  "isRestricted": isrestricted,
                  "isadmin": isadmin
                  }
        try:
            collection_json = 'RestrictedConsole.collection.json'
            # Start newman execution
            self.restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, inputs)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.restapi.clean_up()

    def run(self):

        self.log.info(
            """
            Test Case
            1) Apply restricted console on commcell level and try login for commcell user and company user
            2) Apply restricted console on company level and try login for company user
            3) Apply restricted console on user group level and try login for commcell user
            4) Apply restricted console on Master group and verify admin is exception for restricted console and verify for non admin
            user who is part of master group that restricted console is still applied.
            5) Apply restricted console on local group and associate external group to this local group and try login for
            external user
            6) Apply restricted console on API at user group level and try to create Access token for that user  
            7) Create Access token for the user and try Applying restricted console on API at user group level 
            8) Apply restricted console on API,CC at commcell level and remove CC at company level and try login for company user
            9) Apply restricted console on API,CC at commcell level and remove CC at company level and remove API at company group level and try login for company user
            10) Apply restricted console on API,CC at company level and remove CC at company group level and try login for company user
            11) Apply restricted console on API,CC at commcell level and remove CC at commcell group level and try login for commcell user
            12) Apply restricted console on CC at user group level and API at another user group level and try login for commcell user belonging to both user groups
            13) Apply restricted console on CC at user group level and API at another group level by overriding
            inherited restricted console and try login for commcell user belonging to both user groups
            14) Apply restricted console on CC at user group level and API at another user group level by overriding
            inherited restricted console on both levels and try login for commcell user
            15) Apply restricted console on CC,API at AD user group, override inherited restricted console in
             master group and add the AD user to it and try login for AD user
            """
        )

        try:
            self.log.info("*********Creating local group and local user*********")
            self.commcell.user_groups.add(usergroup_name='restricted_console_group')
            self.commcell.user_groups.add(usergroup_name='restricted_console_group2')
            self.commcell.user_groups.add(usergroup_name=self.tcinputs['external_user_group'])
            password = self.user_helper.password_generator()
            self.user_helper.create_user(user_name='restricted_console_user', email='restricted@local.com',
                                         full_name='restricted_console_user', password=password,
                                         local_usergroups=['restricted_console_group', 'restricted_console_group2'],
                                         security_dict={
                                             'assoc1':
                                                 {
                                                     'commCellName': [self.commcell.commserv_name],
                                                     'role': ['Master']
                                                 }
                                         })

            self.user_helper.create_user(user_name='restricted_console_user2', email='restricted2@local.com',
                                         full_name='restricted_console_user2', password=password,
                                         local_usergroups=['master'])

            self.log.info("*********Creating Company and Company user*********")
            self.organization_helper.create(name="restrictedcompany",
                                            email="automation63966@company.com",
                                            contact_name="automation63966",
                                            company_alias="restrictedcompany")

            self.organization_helper = OrganizationHelper(self.commcell, company='restrictedcompany')
            self.organization_helper.add_new_company_user_and_make_tenant_admin("restricted_company_user", password)

            self.log.info(
                "1) Apply restricted console on commcell level and try login for commcell user and company user")

            self.navigator.navigate_to_commcell()
            self.commcell_helper.add_restricted_console(["Command Center", "API"])

            self.adminconsole_login('restricted_console_user', password)
            self.adminconsole_login('restrictedcompany\\restricted_company_user', password)

            self.q_login('restricted_console_user', password)
            self.q_login('restrictedcompany\\restricted_company_user', password)

            self.api_login('restricted_console_user', password)
            self.api_login('restrictedcompany\\\\restricted_company_user', password)

            self.log.info("Remove restricted console on commcell level")
            self.commcell_helper.reset_restricted_console()

            self.log.info(
                "2) Apply restricted console on company level and try login for company user")
            self.admin_console.refresh_page()
            self.navigator.navigate_to_company()
            self.company.access_company("restrictedcompany")
            self.commcell_helper.add_restricted_console(["Command Center", "API"])

            self.adminconsole_login('restrictedcompany\\restricted_company_user', password)

            self.q_login('restrictedcompany\\restricted_company_user', password)

            self.api_login('restrictedcompany\\\\restricted_company_user', password)

            self.log.info("Remove restricted console on company level")
            self.commcell_helper.remove_restricted_console(["Command Center", "API"])

            self.log.info("3) Apply restricted console on user group level and try login for commcell user")
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group")
            self.commcell_helper.add_restricted_console(["Command Center", "API"])

            self.adminconsole_login('restricted_console_user', password)

            self.q_login('restricted_console_user', password)

            self.api_login('restricted_console_user', password)

            self.log.info("Remove restricted console on Group level")
            self.commcell_helper.remove_restricted_console(["Command Center", "API"])

            self.log.info(
                "4) Apply restricted console on Master group and verify admin is exception for restricted console and verify for non admin user who is part of master group that restricted console is still applied.")
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("master")
            self.commcell_helper.add_restricted_console(["Command Center", "API"])

            self.adminconsole_login('admin', self.inputJSONnode['commcell']["commcellPassword"], False, True)
            self.adminconsole_login('restricted_console_user2', password)

            self.q_login('admin', self.inputJSONnode['commcell']["commcellPassword"], False, True)
            self.q_login('restricted_console_user2', password)

            self.api_login('admin', self.inputJSONnode['commcell']["commcellPassword"], False, True)
            self.api_login('restricted_console_user2', password)

            self.log.info(
                "5) Apply restricted console on local group and associate external group to this local group and try login for external user")
            self.usergroupdetails.edit_user_group(associated_external_groups=[self.tcinputs['external_user_group']])

            self.adminconsole_login(self.tcinputs['external_user'], self.tcinputs['external_user_password'])

            self.q_login(self.tcinputs['external_user'], self.tcinputs['external_user_password'])

            external_user = self.tcinputs['external_user'].replace("\\", "\\\\")
            self.api_login(external_user, self.tcinputs['external_user_password'])

            self.commcell_helper.remove_restricted_console(["Command Center", "API"])
            self.usergroupdetails.remove_associated_external_groups(associated_external_groups=[self.tcinputs['external_user_group']])

            self.log.info(
                "6) Apply restricted console on API at user group level and try to create Access token for that user")
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group")
            self.commcell_helper.add_restricted_console(["API"])
            browser = BrowserFactory().create_browser_object()
            browser.open()
            try:
                token_adminconsole = AdminConsole(browser, self.commcell.webconsole_hostname)
                token_adminconsole.login('restricted_console_user', password)
                self.access_token = AccessToken(token_adminconsole, 'restricted_console_user')
                created = False
                self.access_token.create_token()
                created = True
            except CVWebAutomationException as exp:
                if 'Add token button does not exists' in exp.args[0]:
                    self.log.info("Restricted console is applied")
                else:
                    handle_testcase_exception(self, exp)
            finally:
                AdminConsole.logout_silently(token_adminconsole)
                Browser.close_silently(browser)
            if created:
                raise Exception("User is able to create AccessToken")
            self.commcell_helper.remove_restricted_console(["API"])

            self.log.info(
                "7) Create Access token for the user and try Applying restricted console on API at user group level")
            browser = BrowserFactory().create_browser_object()
            browser.open()
            try:
                createaccesstoken = AdminConsole(browser, self.commcell.webconsole_hostname)
                createaccesstoken.login('restricted_console_user', password)
                self.access_token = AccessToken(createaccesstoken, 'restricted_console_user')
                token, token_name, timedict = self.access_token.create_token()
            except CVWebAutomationException as exp:
                handle_testcase_exception(self, exp)
            finally:
                AdminConsole.logout_silently(createaccesstoken)
                Browser.close_silently(browser)

            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group")
            try:
                restricted = False
                self.commcell_helper.add_restricted_console(["API"], wait=False)
                restricted = True
            except Exception as exp:
                if ("Error: Cannot set API as restricted due to existing access tokens. Revoke these tokens or "
                        "contact your administrator. User: restricted_console_user") in exp.args[0]:
                    self.log.info("Access token exists")
                    self.dialog.click_cancel()
                else:
                    handle_testcase_exception(self, exp)
            if restricted:
                raise Exception("User is able to restrict on API when Access Token exist")

            browser = BrowserFactory().create_browser_object()
            browser.open()
            try:
                token_obj = AdminConsole(browser, self.commcell.webconsole_hostname)
                token_obj.login('restricted_console_user', password)
                self.access_token = AccessToken(token_obj, 'restricted_console_user')
                self.access_token.revoke_token(token_name)
                AdminConsole.logout(token_obj)
            except CVWebAutomationException as exp:
                handle_testcase_exception(self, exp)
            finally:
                Browser.close_silently(browser)

            self.log.info(
                "8) Apply restricted console on API,CC at commcell level and remove CC at company level and try login for company user")
            self.navigator.navigate_to_commcell()
            self.commcell_helper.add_restricted_console(["Command Center", "API"])
            self.navigator.navigate_to_company()
            self.company.access_company("restrictedcompany")
            self.commcell_helper.remove_restricted_console(["Command Center"], do_not_inherit=True)

            self.adminconsole_login('restrictedcompany\\restricted_company_user', password, False)

            self.q_login('restrictedcompany\\restricted_company_user', password)

            self.api_login('restrictedcompany\\\\restricted_company_user', password)

            self.log.info("9) Apply restricted console on API,CC at commcell level and remove CC at company level and "
                          "remove API at company group level and try login for company user")
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restrictedcompany\\Tenant Admin")
            self.commcell_helper.remove_restricted_console(["API"], do_not_inherit=True)

            self.adminconsole_login('restrictedcompany\\restricted_company_user', password, False)

            self.q_login('restrictedcompany\\restricted_company_user', password, False)

            self.api_login('restrictedcompany\\\\restricted_company_user', password, False)

            self.log.info("Reset restricted console at company group level")
            self.commcell_helper.reset_restricted_console()

            self.log.info("Reset restricted console at company level")
            self.navigator.navigate_to_company()
            self.company.access_company("restrictedcompany")
            self.commcell_helper.reset_restricted_console()

            self.log.info("Reset restricted console at commcell level")
            self.navigator.navigate_to_commcell()
            self.commcell_helper.reset_restricted_console()

            self.log.info(
                "10) Apply restricted console on API,CC at company level and remove CC at company group level and try login for company user")
            self.navigator.navigate_to_company()
            self.company.access_company("restrictedcompany")
            self.commcell_helper.add_restricted_console(["Command Center", "API"])

            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restrictedcompany\\Tenant Admin")
            self.commcell_helper.remove_restricted_console(["Command Center"], do_not_inherit=True)

            self.adminconsole_login('restrictedcompany\\restricted_company_user', password, False)

            self.q_login('restrictedcompany\\restricted_company_user', password)

            self.api_login('restrictedcompany\\\\restricted_company_user', password)

            self.log.info(
                "11) Apply restricted console on API,CC at commcell level and remove CC at commcell group level and try login for commcell user")
            self.navigator.navigate_to_commcell()
            self.commcell_helper.add_restricted_console(["Command Center", "API"])
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group")
            self.commcell_helper.remove_restricted_console(["Command Center"], do_not_inherit=True)

            self.adminconsole_login('restricted_console_user', password, False)

            self.q_login('restricted_console_user', password)

            self.api_login('restricted_console_user', password)

            self.commcell_helper.reset_restricted_console()

            self.log.info("Reset restricted console at commcell level")
            self.navigator.navigate_to_commcell()
            self.commcell_helper.reset_restricted_console()

            self.log.info("12) Apply restricted console on CC at user group level and API at another user group level"
                          " and try login for commcell user belonging to both user groups")
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group")
            self.commcell_helper.add_restricted_console(["Command Center"])

            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group2")
            self.commcell_helper.add_restricted_console(["API"])

            self.adminconsole_login('restricted_console_user', password)

            self.q_login('restricted_console_user', password)

            self.api_login('restricted_console_user', password)

            self.commcell_helper.remove_restricted_console(["API"])

            self.log.info("13) Apply restricted console on CC at user group level and API at another group level by"
                          " overriding inherited restricted console and try login for commcell user belonging to both user groups")
            self.commcell_helper.add_restricted_console(["API"], do_not_inherit=True)

            self.adminconsole_login('restricted_console_user', password, False)

            self.q_login('restricted_console_user', password)

            self.api_login('restricted_console_user', password)

            self.commcell_helper.reset_restricted_console()
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group")
            self.commcell_helper.remove_restricted_console(["Command Center"])

            self.log.info("14) Apply restricted console on CC at user group level and API at another user group level"
                          " by overriding inherited restricted console on both levels and try login for commcell user")
            self.commcell_helper.add_restricted_console(["Command Center"], do_not_inherit=True)
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("restricted_console_group2")
            self.commcell_helper.add_restricted_console(["API"], do_not_inherit=True)

            self.adminconsole_login('restricted_console_user', password)

            self.q_login('restricted_console_user', password)

            self.api_login('restricted_console_user', password)

            self.log.info("15) Apply restricted console on CC,API at AD user group, override inherited restricted"
                          " console at master group and add the AD user to it and try login for AD user")
            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group(self.tcinputs['external_user_group'])
            self.commcell_helper.add_restricted_console(["Command Center", "API"])

            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("master")
            self.commcell_helper.remove_restricted_console([], do_not_inherit=True)
            self.usergroupdetails.add_users_to_group([self.tcinputs['external_user']])

            self.adminconsole_login(self.tcinputs['external_user'], self.tcinputs['external_user_password'], False)

            self.q_login(self.tcinputs['external_user'], self.tcinputs['external_user_password'], False)

            external_user = self.tcinputs['external_user'].replace("\\", "\\\\")
            self.api_login(external_user, self.tcinputs['external_user_password'], False)

            self.navigator.navigate_to_user_groups()
            self.usergroupshelp.open_user_group("master")
            self.commcell_helper.reset_restricted_console()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.user_helper.cleanup_users('restricted_console_user')
        self.user_helper.cleanup_users(self.tcinputs['external_user'])
        self.securitygroup.cleanup_user_groups('restricted_console_group')
        self.securitygroup.cleanup_user_groups(self.tcinputs['external_user_group'])
        self.organization_helper.cleanup_orgs('restrictedcompany')
