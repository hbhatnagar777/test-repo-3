"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    SP initiated SAML login with Azure as IDP
                    Existing user SAML login
                    New user SAML login when only username Attribute mappings are set

Input Example:

    "testCases": {
            "59907":{
                    "ClientName": "stormbreaker",
                    "SMTP" : "gmail.com",
                    "IDP admin username" : "backupadmin@cv.com",
                    "IDP admin password" : "123456",
                    "appname" : "AutomationApp",
                    "metadata path" : "C:\\AutomationApp.xml",
                    "SAML user name" : "user1@cv.com",
                    "SAML user pwd" : "pwd1",
                    "saml user2": user2@cv.com,
                    "user2 pwd": pwd2,
                    }
                }
"""
from datetime import datetime

import self as self

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing SAML login with Azure as IDP when only username mappings set"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Existing and new user SAML login with username mapping"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.sp_entity_id = None
        self.webconsole_url = None
        self.Azure_url = None
        self.navigator_obj = None
        self.saml_obj = None
        self.tcinputs = {
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "metadata path": None,
            "SMTP": None,
            "saml user1": None,
            "user1 pwd": None,
            "saml user2": None,
            "user2 pwd": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
            self.navigator_obj = self.admin_console.navigator
            self.Azure_url = "https://portal.azure.com/"
            self.user = Users(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_app(self):
        """ Adds SAML app """
        self.saml_obj.app_name = "test" + str(datetime.today().microsecond)
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['metadata path'],
                                      self.tcinputs['SMTP'],
                                      self.webconsole_url,
                                      False,
                                      None)
        self.sso_url = self.saml_obj.get_sso_url()
        self.sp_entity_id = self.saml_obj.get_sp_entity_id()
        self.appkey = self.sso_url.split('=')[1]
        self.slo_url = self.webconsole_url + "/server/SAMLSingleLogout?samlAppKey=" + self.appkey

    @test_step
    def sp_init_saml_login(self, username, pwd):
        """ Performs IDP init SAML login"""
        status = self.saml_obj.initiate_saml_login_with_azure(self.webconsole_url,
                                                              self.commcell.webconsole_hostname,
                                                              username,
                                                              pwd,
                                                              self.Azure_url,
                                                              self.tcinputs['appname'],
                                                              False,
                                                              tab_off_approach=True)
        return status

    @test_step
    def add_mappings(self):
        """ Adding username attribute mappings in SAML app"""
        mappings = {"user name" : "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"}
        self.saml_obj.edit_saml_rule_or_mappings(self.saml_obj.app_name, mappings=mappings)
        validate_key_dict = {"Attribute mapping": mappings}
        self.saml_obj.validate_saml_app(validate_key_dict)

    @test_step
    def verify_user_properties(self):
        """ Verifies the """
        self.navigator_obj.navigate_to_users()

        # get_user_details

    def run(self):
        try:
            self.init_tc()
            self.create_saml_app()
            self.add_mappings()

            self.navigator_obj.navigate_to_users()
            self.user.add_local_user(self.tcinputs['saml user2'],
                                     username=self.tcinputs['saml user2'].split('@')[0],
                                     groups=None,
                                     system_password=True)
            self.admin_console.wait_for_completion()
            self.navigator_obj.navigate_to_identity_servers()
            self.admin_console.logout()

            self.saml_obj.login_to_azure_and_edit_basic_saml_configuration(self.Azure_url,
                                                                           self.tcinputs['IDP admin username'],
                                                                           self.tcinputs['IDP admin password'],
                                                                           self.tcinputs['appname'],
                                                                           self.sp_entity_id,
                                                                           self.sso_url,
                                                                           self.slo_url)
            self.saml_obj.logout_from_azure()
            try:
                self.sp_init_saml_login(self.tcinputs['saml user2'], self.tcinputs['user2 pwd'])
            except Exception as exp:
                raise Exception("Existing user login failed")

            self.saml_obj.sp_init_logout(self.commcell.webconsole_hostname, self.Azure_url)
            self.admin_console.wait_for_completion()

            status = self.sp_init_saml_login(self.tcinputs['saml user1'], self.tcinputs['user1 pwd'])
            if status:
                raise Exception("new user is auto-created, this should not happen without email address")
            else:
                self.log.info("user auto creation failed! Email is required for user auto-creation")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.saml_obj.delete_app()

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
