# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Login/Logout for local user, SAML user, admin user, tenant admin user, ad user

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    commandcenter_login()        --  Login verification for admin console

    run()                       --  Contains the core testcase logic, and it is the one executed

    tear_down()                 --  Clean up entities

"""

from datetime import datetime
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Server.Security.userhelper import UserHelper
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "70733":
                {
                "ad_username": "infernoad\\username",
                "ad_useremail": "inferno@inferno.loc",
                "ad_userpassword": "#####",
                "ad_userfullname": "fullname"
                }

        """

        super(TestCase, self).__init__()

        self.name = "Login with special characters in Username and Password"
        self.result_string = "Successful"
        self.user_helper = None
        self.user1 = None
        self.user2 = None
        self.user3 = None
        self.fullname1 = None
        self.fullname2 = None
        self.ad_entity = None
        self.tcinputs = {
            "ad_username": None,
            "ad_useremail": None,
            "ad_userpassword": None,
            "ad_userfullname": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""

        self.user_helper = UserHelper(self.commcell)
        self.ad_entity = config.get_config().Security.LDAPs.Active_Directory_1

    @test_step
    def commandcenter_login(self, username, password, fullname):
        """*********Command Center Login for special characters*********"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        try:
            login_obj = AdminConsole(browser, self.commcell.webconsole_hostname)
            login_obj.login(username, password)
            login_obj.check_error_message()
            self.log.info("Successfully logged in Command Center")
            login_obj.navigator.navigate_to_dashboard()
            login_obj.wait_for_completion()
            fullname_shown = login_obj.logged_in_user()
            if fullname_shown != fullname:
                raise Exception(
                    f'Full name is not matching. Expected Full Name: {fullname}'
                    '\nFull Name shown: {fullname_shown}')
            AdminConsole.logout(login_obj)
        except Exception as exp:
            raise Exception(exp)
        finally:
            Browser.close_silently(browser)

    def run(self):
        try:
            self.log.info("*********Creating only special chars user*********")
            self.user1, self.fullname1 = self.user_helper.special_char_user_generator()
            self.user_helper.create_user(user_name=self.user1,
                                         email='user1' + str(datetime.today().microsecond) + '@commvault.com',
                                         full_name=self.fullname1, password=self.user1)

            self.log.info("*********Creating user with mixture of special chars and alphabets*********")
            self.user2, self.fullname2 = self.user_helper.special_char_user_generator(special_char_only=False)
            self.user_helper.create_user(user_name=self.user2,
                                         email='user2' + str(datetime.today().microsecond) + '@commvault.com',
                                         full_name=self.fullname2, password=self.user2)
            self.user3 = 'Usér_Nâmè@2024!'
            self.user_helper.create_user(user_name=self.user3,
                                         email='user3' + str(datetime.today().microsecond) + '@commvault.com',
                                         full_name=self.user3, password=self.user3)

            self.log.info("*********Creating Active Directory and Ad User*********")
            self.commcell.domains.add(domain_name=self.ad_entity.DomainName,
                                      netbios_name=self.ad_entity.NETBIOSName,
                                      user_name=self.ad_entity.UserName,
                                      password=self.ad_entity.Password,
                                      company_id=0)
            self.user_helper.create_user(user_name=self.tcinputs["ad_username"], email=self.tcinputs["ad_useremail"],
                                         domain=self.ad_entity.NETBIOSName,
                                         local_usergroups=['master'])

            self.commandcenter_login(self.user1, self.user1, self.fullname1)
            self.commandcenter_login(self.user2, self.user2, self.fullname2)
            self.commandcenter_login(self.user3, self.user3, self.user3)
            self.commandcenter_login(self.tcinputs['ad_username'], self.tcinputs['ad_userpassword'],
                                     self.tcinputs['ad_userfullname'])

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        self.user_helper.cleanup_users(self.user1)
        self.user_helper.cleanup_users(self.user2)
        self.user_helper.cleanup_users(self.user3)
        self.commcell.refresh()
        self.commcell.domains.delete(self.ad_entity.NETBIOSName)
