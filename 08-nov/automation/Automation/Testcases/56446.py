from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing SAML login with OKTA as IDP"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAML login with OKTA as IDP"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.sp_entity_id = None
        self.webconsole_url = None
        self.OKTA_url = None
        self.company_name = None
        self.navigator_obj = None
        self.loaded_url = None
        self.saml_obj = None
        self.tcinputs = {
            "IDP URL": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "metadata path": None,
            "SMTP": None,
            "SAML user name": None,
            "SAML user pwd": None
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

            self.company = Companies(self.admin_console)
            self.user = Users(self.admin_console)
            self.email = "User459461@commvault.com"
            self.pwd = "#####"
            self.OKTA_url = "https://" + self.tcinputs['IDP URL']

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_company(self):
        """ Creates a Company """
        self.company_name = "Company" + "_" + str(datetime.today().microsecond)
        self.navigator_obj.navigate_to_companies()
        self.company.add_company(self.company_name,
                                 "abc@commvault.com",
                                 self.company_name,
                                 [],
                                 self.company_name,
                                 "commvault.com", "", "")

    @test_step
    def create_user(self):
        """ Creates User """
        self.user_name = "User" + str(datetime.today().microsecond)
        self.full_name = self.company_name + "\\" + self.user_name
        self.email = self.user_name + "@commvault.com"
        self.pwd = "#####"
        self.user_group = self.company_name + "\\" + "Tenant Admin"
        self.navigator_obj.navigate_to_users()
        self.user.add_local_user(self.email,
                                 self.full_name,
                                 self.user_name,
                                 [self.user_group],
                                 False,
                                 self.pwd,
                                 invite_user=False)

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

    @test_step
    def saml_logout(self):
        """ SAML Logout """
        self.saml_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
        self.saml_obj.single_logout(self.OKTA_url)

    def run(self):
        try:
            self.init_tc()
            self.create_company()
            self.create_user()
            self.admin_console.logout()
            self.admin_console.login(self.email, self.pwd)
            self.create_saml_app()
            self.admin_console.logout()
            self.saml_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                  self.tcinputs['IDP admin username'],
                                                                  self.tcinputs['IDP admin password'],
                                                                  self.tcinputs['appname'],
                                                                  self.sso_url,
                                                                  self.sp_entity_id)
            self.saml_obj.logout_from_okta()

            self.saml_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                        self.commcell.webconsole_hostname,
                                                        self.OKTA_url,
                                                        self.tcinputs['SAML user name'],
                                                        self.tcinputs['SAML user pwd'],
                                                        self.tcinputs['appname'],
                                                        True)

            self.saml_logout()

            self.saml_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                        self.commcell.webconsole_hostname,
                                                        self.OKTA_url,
                                                        self.tcinputs['SAML user name'],
                                                        self.tcinputs['SAML user pwd'],
                                                        self.tcinputs['appname'],
                                                        False)

            self.saml_logout()

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
