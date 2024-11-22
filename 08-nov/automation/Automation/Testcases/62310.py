from selenium.webdriver.common.by import By
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating saml login and default usergroup
            in company SAML app with name same as AD

Input Example:

    "testCases": {
            "62310": {
                "IDP URL": "",
                "idp_metadata_xml_path": "",
                "IDP admin username": "",
                "IDP admin password": "",
                "appname": appname in IDP,
                "email_suffix": "",
                "SAML user email": "",
                "SAML user pwd": "",
                "IDP usergroup": ""
            }
"""
import time
from datetime import datetime
from urllib.parse import quote
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.samlhelper import SamlHelperMain
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ Testcase to validate regressions of SAML login"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Company SAML app with name same as AD"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.sso_url = None
        self.sp_entity_id = None
        self.command_center_url = None
        self.OKTA_url = None
        self.company_name = None
        self.saml_appname = None
        self.tenant_admin_email = None
        self.tenant_admin_name = None
        self.tenant_admin_password = None
        self.ta_commcell = None
        self.cert = None
        self.download_directory = None

        self.helper_obj = None
        self.orghelper = None
        self.userhelper = None
        self.samlhelper = None
        self.samlhelper2 = None
        self.grouphelper = None
        self.machine = None

        self.tcinputs = {
            "IDP URL": None,
            "idp_metadata_xml_path": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "email_suffix": None,
            "SAML user email": None,
            "SAML user pwd": None,
            "IDP usergroup": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.machine = Machine()
            self.download_directory = self.utils.get_temp_dir()
            self.machine.create_directory(self.download_directory, force_create=True)
            self.browser.set_downloads_dir(self.download_directory)

            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.helper_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.orghelper = OrganizationHelper(self.commcell)
            self.userhelper = UserHelper(self.commcell)
            self.grouphelper = UsergroupHelper(self.commcell)
            self.samlhelper2 = SamlHelperMain(self.commcell)  # commcell level object for DB queries
            self.command_center_url = "https://" + self.commcell.webconsole_hostname + "/commandcenter"
            self.OKTA_url = 'https://' + self.tcinputs['IDP URL'] + '/'

            self.saml_appname = self.tcinputs['netbios_name']  # Saml app name same as AD
            self.company_name = 'test' + str(datetime.today().microsecond)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_company(self):
        """Create a company"""
        self.orghelper.create(self.company_name, company_alias=self.company_name)

    @test_step
    def create_tenant_admin_user(self):
        """Create a tenant admin user"""
        user_name = self.company_name + 'admin'
        self.tenant_admin_email = user_name + '@' + self.company_name + '.in'
        self.tenant_admin_password = self.userhelper.password_generator(complexity_level=3, min_length=12)
        self.userhelper.create_user(self.company_name + '\\' + user_name,
                                    email=self.tenant_admin_email,
                                    password=self.tenant_admin_password,
                                    local_usergroups=[self.company_name + '\\Tenant Admin'])

    @test_step
    def create_company_AD(self):
        """Creates AD"""
        self.ta_commcell.domains.add(self.tcinputs['domain_name'],
                                     self.tcinputs['netbios_name'],
                                     self.tcinputs['ADAdmin'],
                                     self.tcinputs['ADAdminPass'],
                                     enable_sso=False,
                                     company_id=0)

    @test_step
    def add_AD_group(self):
        """Adds an AD user group"""
        self.grouphelper.create_usergroup('Domain Users', self.tcinputs['netbios_name'],
                                          local_groups=[self.company_name + '\\Tenant Admin'])

    @test_step
    def create_company_saml_app(self):
        """Create company saml app"""
        self.samlhelper.create_saml_app(self.saml_appname,
                                        self.name,
                                        self.tcinputs['idp_metadata_xml_path'],
                                        auto_generate_sp_metadata=True,
                                        email_suffixes=[self.tcinputs['email_suffix']])

    @test_step
    def download_certificate(self):
        """ Download SAML app certificate """
        encoded = quote(self.saml_appname)
        download_url = "https://" + self.commcell.webconsole_hostname + \
                       "/commandcenter/downloadSPCertificate.do?appName=" + encoded
        self.admin_console.driver.execute_script("window.open('" + download_url + "');")
        parent_handle = self.admin_console.driver.current_url
        filename = self.saml_appname + ".cer"
        self.cert = self.download_directory + "\\" + filename
        time.sleep(5)
        if not self.machine.check_file_exists(self.cert):
            raise CVTestStepFailure("Certificate download failed")
        self.log.info("Certificate downloaded successfully")
        self.admin_console.browser.switch_to_tab(parent_handle)

    @test_step
    def verify_slo(self):
        """Verify SLO"""
        self.admin_console.browser.open_url_in_new_tab(self.OKTA_url)
        if not self.helper_obj.check_slo(self.OKTA_url):
            raise Exception('SLO failed')

    @test_step
    def disable_autocreate_flag(self):
        """Disable Auto Create User Flag of SAML App"""
        self.samlhelper.modify_saml_general_settings(autocreate=False)

    @test_step
    def disable_enabled_flag(self):
        """Disable Enabled Flag of SAML App"""
        self.samlhelper.modify_saml_general_settings(enabled=False)

    @test_step
    def check_redirection_for_user(self, user_email=None):
        """Check Redirection of a User"""
        if not user_email:
            user_email = str(datetime.today().microsecond) + '@' + self.tcinputs['email_suffix']

        self.admin_console.browser.open_url_in_new_tab(self.command_center_url)
        self.admin_console.wait_for_completion()
        self.admin_console.driver.find_element(By.ID, 'username').send_keys(user_email)
        self.admin_console.driver.find_element(By.ID, 'continuebtn').click()
        self.admin_console.wait_for_completion()

        return False if self.admin_console.driver.title == 'Login' else True

    def run(self):
        try:
            self.init_tc()

            self.create_company()
            self.create_tenant_admin_user()
            self.ta_commcell = Commcell(self.commcell.webconsole_hostname,
                                        self.tenant_admin_email,
                                        self.tenant_admin_password,
                                        verify_ssl=False)
            self.samlhelper = SamlHelperMain(self.ta_commcell)
            self.create_company_AD()
            self.add_AD_group()
            self.create_company_saml_app()
            self.download_certificate()
            self.admin_console.logout()
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper.spmetadata['entityId'],
                                                                    slo=True,
                                                                    single_logout_url=self.samlhelper.spmetadata['singleLogoutUrl'],
                                                                    sp_issuer=self.samlhelper.spmetadata['entityId'],
                                                                    certificate=self.cert
                                                                    )
            time.sleep(2)
            self.helper_obj.logout_from_okta()
            self.helper_obj.initiate_saml_login_with_okta(self.command_center_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()

            self.samlhelper2.validate_samluser_properties(self.tcinputs['SAML user email'], {
                'usergroups': [self.tcinputs['netbios_name'] + '\\Domain Users', self.company_name + '\\Tenant Users'],
                'login': self.tcinputs['netbios_name'] + '\\' + self.tcinputs['SAML user email'].split('@')[0]
            })
            self.disable_autocreate_flag()
            if self.check_redirection_for_user():
                raise Exception('Redirection should not happen for new user if autocreate flag is disabled for samlapp')

            if not self.check_redirection_for_user(self.tcinputs['SAML user email']):
                raise Exception('Redirection did not work for existing user {0}'.format(
                    self.tcinputs['SAML user email']
                ))

            self.disable_enabled_flag()
            if self.check_redirection_for_user(self.tcinputs['SAML user email']):
                raise Exception('Redirection should not happen for existing user if saml app is disabled')

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            if self.cert:
                self.machine.delete_file(self.cert)
            self.log.info('Deleting Company')
            self.commcell.organizations.delete(self.company_name)

        finally:
            Browser.close_silently(self.browser)
