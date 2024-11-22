# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from datetime import datetime
from AutomationUtils import logger, config
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.Security.user_login_validator import LoginValidator
from Server.Security.userhelper import UserHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.Common.page_object import TestStep
from Server.Security.userconstants import WebConstants


class TestCase(CVTestCase):
    """Class for executing commcell user email login test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Commcell User's[local user, AD user, AD as Generic LDAP user, Redhat as Generic LDAP user, openldap
         user, oracle directory user] login with email from [adminconsole, Rest api, qlogin]"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.user_helper = None
        self.local_user_name = None
        self.local_user_upn = None
        self.ldap_entity = None
        self.result_string = "Successful"
        self.console_user_helper = None
        self.password = None
        self.tcinputs = {
            "Commcell": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()
        self.user_helper = UserHelper(self.commcell)
        self.local_user_name = 'local_user' + str(datetime.today().microsecond)
        self.local_user_upn = self.local_user_name + '@commvault.com'
        self.ldap_entity = config.get_config().Security.LDAPs.Active_Directory_1

    @test_step
    def login_and_add_user(self):
        """*********Command Center Login and add local user*********"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        try:
            login_obj = AdminConsole(browser, self.commcell.webconsole_hostname)
            login_obj.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                            password=self.inputJSONnode['commcell']["commcellPassword"])
            login_obj.check_error_message()
            self.log.info("Successfully logged in Command Center")
            login_obj.navigator.navigate_to_users()
            login_obj.wait_for_completion()
            self.console_user_helper = Users(login_obj)
            self.password = self.user_helper.password_generator(complexity_level=3, min_length=12)
            self.console_user_helper.add_local_user(email=self.ldap_entity.UsersToImport[0].email2,
                                                    username=self.local_user_name,
                                                    name=self.local_user_name,
                                                    password=self.password,
                                                    upn=self.local_user_upn)
            AdminConsole.logout(login_obj)
        except Exception as exp:
            Browser.close_silently(browser)
            raise Exception(exp)
        Browser.close_silently(browser)    

    def run(self):
        """Execution method for this test case"""
        try:
            tc = ServerTestCases(self)
            validator = LoginValidator(self)
            validator.validate(feature='user_login', login_with="email")
            self.log.info("creating local user and ad user with same email")
            self.commcell.domains.add(domain_name=self.ldap_entity.DomainName,
                                      netbios_name=self.ldap_entity.NETBIOSName,
                                      user_name=self.ldap_entity.UserName,
                                      password=self.ldap_entity.Password,
                                      company_id=0)
            self.user_helper.create_user(user_name=self.ldap_entity.UsersToImport[0].UserName2,
                                         email=self.ldap_entity.UsersToImport[0].email2,
                                         domain=self.ldap_entity.NETBIOSName,
                                         local_usergroups=['master'])
            self.login_and_add_user()
            self.log.info("Login with local user email")
            try:
                self.user_helper.web_login(self.ldap_entity.UsersToImport[0].email2, self.password,
                                           web=WebConstants(self._commcell.commserv_hostname))
                raise Exception("User is able to login")
            except Exception as exp:
                if "Invalid Username or Password" in str(exp):
                    self.log.info("Another user is having same email")
                else:
                    raise Exception(exp)
            self.log.info("Login with Ad user email")
            self.user_helper.web_login(self.ldap_entity.UsersToImport[0].email2,
                                       self.ldap_entity.UsersToImport[0].Password2,
                                       web=WebConstants(self._commcell.commserv_hostname))

        except Exception as excep:
            tc.fail(excep)

    def tear_down(self):
        """To clean up the test case environment created"""
        self.user_helper.cleanup_users(self.local_user_name)
        self.commcell.domains.delete(self.ldap_entity.NETBIOSName)    
