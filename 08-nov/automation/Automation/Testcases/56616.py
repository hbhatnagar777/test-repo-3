"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    SAML login with Company attribute mapping
                    SAML login when auto create option is disabled
                    SAML login when keystore file is modified

Input Example:

    "testCases": {
            "56616":{
                    "ClientName": "venus",
                    "SMTP" : "test.indigo.com",
                    "IDP URL" : "company.com",
                    "IDP admin username" : "test@company.com",
                    "IDP admin password" : "pwd123",
                    "appname" : "AutomationApp",
                    "metadata path" : "C:\\AutomationApp.xml",
                    "SAML user name" : "user1@test.indigo.com",
                    "SAML user pwd" : "pwd1",
                    "SAML user2" : "user2@test.indigo.com",
                    "SAML pwd2" : "pwd2",
                    "jks file path" : "C:\\mykeystore9.jks",
                    "Keystore Alias name" : "selfsigned",
                    "Keystore password" : "123456",
                    "Key password" : "123456"
                    }
                }
"""

from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ Testcase to validate regressions of SAML login"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Regressions of SAML login"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.sp_entity_id = None
        self.webconsole_url = None
        self.__navigator = None
        self.helper_obj = None
        self.OKTA_url = None
        self.tcinputs = {
            "SMTP": None,
            "IDP URL": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "metadata path": None,
            "SAML user name": None,
            "SAML user pwd": None,
            "SAML user2": None,
            "SAML pwd2": None,
            "jks file path": None,
            "Keystore Alias name": None,
            "Keystore password": None,
            "Key password": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.helper_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
            self.navigator_obj = self.admin_console.navigator
            self.company = Companies(self.admin_console)
            self.company_name = "Company" + "_" + str(datetime.today().microsecond)
            self.OKTA_url = "https://" + self.tcinputs['IDP URL']

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_company(self):
        """ Creates Company """
        self.navigator_obj.navigate_to_companies()
        self.company.add_company(self.company_name,
                                 "abc@commvault.com",
                                 self.company_name,
                                 [],
                                 self.company_name,
                                 "commvault.com", "", "")

    @test_step
    def add_saml_app(self):
        """ Adds SAML app """
        self.navigator_obj.navigate_to_identity_servers()
        self.helper_obj.app_name = "test" + str(datetime.today().microsecond)
        self.helper_obj.create_saml_app(self.tcinputs['metadata path'],
                                        self.tcinputs['SMTP'],
                                        self.webconsole_url,
                                        True,
                                        self.company_name
                                        )
        self.sso_url = self.helper_obj.get_sso_url()
        self.sp_entity_id = self.helper_obj.get_sp_entity_id()

    @test_step
    def modify_saml_app_general_settings(self, auto_create_user=True):
        """ Modifies SAML app general settings """
        self.navigator_obj.navigate_to_identity_servers()
        self.helper_obj.open_saml_app(self.helper_obj.app_name)
        self.helper_obj.modify_saml_general_settings(self.helper_obj.app_name,
                                                     modify_auto_create=True,
                                                     auto_create_user=auto_create_user)

    @test_step
    def add_mappings(self):
        """ Adding Attribute mappings """
        mappings = {'company': self.company_name}
        self.helper_obj.edit_saml_rule_or_mappings(self.helper_obj.app_name,
                                                   mappings=mappings)

    @test_step
    def saml_logout(self):
        """ SAML logout """
        self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
        self.helper_obj.single_logout(self.OKTA_url)

    def run(self):
        try:
            self.init_tc()
            self.create_company()
            self.add_saml_app()
            self.add_mappings()
            self.admin_console.logout()
            attributes = {'company': self.company_name}
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.sso_url,
                                                                    self.sp_entity_id,
                                                                    attributes=attributes)
            self.helper_obj.logout_from_okta()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user name'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False,
                                                          tab_off_approach=True)
            self.saml_logout()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.modify_saml_app_general_settings(auto_create_user=False)

            self.admin_console.logout()

            status = self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                                   self.commcell.webconsole_hostname,
                                                                   self.OKTA_url,
                                                                   self.tcinputs['SAML user2'],
                                                                   self.tcinputs['SAML pwd2'],
                                                                   self.tcinputs['appname'],
                                                                   False,
                                                                   tab_off_approach=True)
            if not status:
                self.log.info("On disabling auto create user option login fails")
            else:
                raise CVTestStepFailure("On disabling auto create user option login succeeded")

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.modify_saml_app_general_settings(auto_create_user=True)

            self.helper_obj.edit_saml_idp(self.helper_obj.app_name,
                                          jks_file_path=self.tcinputs['jks file path'],
                                          alias_name=self.tcinputs['Keystore Alias name'],
                                          keystore_password=self.tcinputs['Keystore password'],
                                          key_password=self.tcinputs['Key password'])
            self.admin_console.logout()

            status = self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                                   self.commcell.webconsole_hostname,
                                                                   self.OKTA_url,
                                                                   self.tcinputs['SAML user name'],
                                                                   self.tcinputs['SAML user pwd'],
                                                                   self.tcinputs['appname'],
                                                                   False,
                                                                   tab_off_approach=True)
            if not status:
                raise CVTestStepFailure("On changing the JKS file, login Failed")

            self.saml_logout()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.helper_obj.delete_app()

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
