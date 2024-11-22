# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Basic login test case for secure ldap via proxy in AdminConsole

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.domain_helper import DomainHelper
from Web.AdminConsole.AdminConsolePages.Users import Users
from Server.Security.user_login_validator import LoginValidator
from Reports.utils import TestCaseUtils
from Server.Security.userhelper import UserHelper
from Server.Security.userconstants import WebConstants
from Web.Common.exceptions import CVWebAutomationException
from cvpysdk.domains import Domains


class TestCase(CVTestCase):
    
    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "62969":
                {
            "netbios_name": "###",
            "domain_name": "###",
            "domain_username": "###",
            "domain_password": "###",
            "client_name": "###",
            "user_group": "###",
            "login_username": "###",
            "login_password": "###",
            'domain_add_username': "###"

                }

        """

        super(TestCase, self).__init__()
        self.name = "AD via secure LDAP + Proxy"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.validator = None
        self.browser = None
        self.admin_console = None
        self.domain_helper = None
        self.domain = None
        self.user_helper = None
        self.user = None
        self.navigator = None
        self.tcinputs = {
            "netbios_name": None,
            "domain_name": None,
            "domain_username": None,
            "domain_password": None,
            "client_name": None,
            "user_group": None,
            "login_username": None,
            "login_password": None,
            'domain_add_username': None
        }

    def setup(self):
        try:
            self.browser = BrowserFactory().create_browser_object(name="User Browser")
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.inputJSONnode['commcell']["commcellUsername"],
                password=self.inputJSONnode['commcell']["commcellPassword"])
            self.domain_helper = DomainHelper(self.admin_console)
            self.domain = Domains(self.commcell)
            self.user = Users(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.validator = LoginValidator(self)
            self.user_helper = UserHelper(self.commcell)
        except Exception as exception:
            raise exception

    def run(self):
        """Secure LDAP via Proxy"""
        try:
            self.domain_helper.domain_name = self.tcinputs['domain_name']
            self.domain_helper.netbios_name = self.tcinputs['netbios_name']
            self.domain_helper.domain_username = self.tcinputs['domain_username']
            self.domain_helper.domain_password = self.tcinputs['domain_password']
            self.domain_helper.secure_ldap = True
            self.domain_helper.proxy_client = True
            self.domain_helper.proxy_client_value = self.tcinputs['client_name']
            self.domain_helper.user_group = self.tcinputs['user_group']
            self.domain_helper.local_group = ['master']
            self.log.info("*********Adding a Active Directory and UserGroup Browse*********")
            self.domain_helper.add_domain()

            self.log.info("*********Adding domain user*********")
            self.navigator.navigate_to_users()
            self.user.add_external_user(self.tcinputs['netbios_name'], self.tcinputs['domain_add_username'])

            self.log.info("*********Adding a non-exist domain user*********")
            self.navigator.navigate_to_users()
            try:
                self.user.add_external_user(self.tcinputs['netbios_name'], "nonexistuserindomain")
                raise Exception("user is added")
            except CVWebAutomationException as exp:
                if 'There is no user with name "nonexistuserindomain"' in exp.args[0]:
                    self.log.info("*********There is no user with name nonexistuserindomain in domian*********")
                else:
                    self.utils.handle_testcase_exception(exp)
            self.admin_console.logout()
            self.commcell.users.refresh()

            self.log.info("*********Login from adminconsole and webconsole*********")
            self.user_helper.web_login(user_name=self.tcinputs['login_username'],
                                       password=self.tcinputs['login_password'],
                                       web=WebConstants(self.commcell.commserv_hostname))

            self.log.info("*********Login from GUI*********")
            self.user_helper.gui_login(cs_host=self.commcell.commserv_hostname,
                                       user_name=self.tcinputs['login_username'],
                                       password=self.tcinputs['login_password'])

            self.log.info("*********QLogin*********")
            self.user_helper.qlogin(username=self.tcinputs['login_username'],
                                    password=self.tcinputs['login_password'])

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        Browser.close_silently(self.browser)
        self.domain.refresh()
        self.domain.delete(self.tcinputs['netbios_name'])
