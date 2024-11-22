"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating default usergroup associations and
            attribute mappings in company SAML app with name same
            as company

Input Example:

    "testCases": {
            "62981": {
                    "idpmetadata_xml_path": "",
                    "IDP admin username": "",
                    "IDP admin password": "",
                    "appname": "appname in IDP ",
                    "email_suffix": "",
                    "SAML user email": "",
                    "SAML user pwd": "",
                    "IDP usergroup": "",
                    "SAML user new email": "user.secondEmail from Okta",
                    "SAML user guid": "user.objectGUID from Okta",
                    "SAML user new login": "user.displayName from Okta",
                    "SAML user fullname": "user.firstName from Okta"
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
        self.OKTA_url = None
        self.name = "Locked company saml regression when saml app name different than company name"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.sso_url = None
        self.sp_entity_id = None
        self.command_center_url = None
        self.saml_appname = None
        self.company_name = None
        self.tenant_admin_email = None
        self.tenant_admin_name = None
        self.tenant_admin_password = None
        self.company_group1 = None
        self.company_group2 = None
        self.idp_grp_mapping = None
        self.attr_mappings = None
        self.idp_attr_mappings = None
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
            "idpmetadata_xml_path": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "email_suffix": None,
            "SAML user email": None,
            "SAML user pwd": None,
            "IDP usergroup": None,
            "SAML user new email": None,
            "SAML user guid": None,
            "SAML user new login": None,
            "SAML user fullname": None
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

            self.idp_grp_mapping = {"usergroup": self.tcinputs['IDP usergroup']}
            self.attr_mappings = {
                "user name": "un",
                "Email": "email",
                "user guid": "guid",
                "full name": "fname",
                "user groups": "usergroup"
            }
            self.idp_attr_mappings = {
                "un": "user.displayName",
                "email": "user.secondEmail",
                "guid": "user.objectGUID",
                "fname": "user.firstName"
            }

            self.company_name = 'test' + str(datetime.today().microsecond)
            self.company_group1 = self.company_name + '\\g1' + str(datetime.today().microsecond)
            self.company_group2 = self.company_name + '\\' + self.idp_grp_mapping['usergroup']
            self.saml_appname = 'samlapp' + str(datetime.today().microsecond)  # Saml app name different as company name

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
    def create_saml_app(self):
        """Create a company saml app with name same as company name"""
        self.samlhelper.create_saml_app(self.saml_appname,
                                        self.name,
                                        self.tcinputs['idpmetadata_xml_path'],
                                        auto_generate_sp_metadata=True,
                                        email_suffixes=[self.tcinputs['email_suffix']])

    @test_step
    def create_company_usergroups(self):
        """Create company usergroups"""
        self.grouphelper.create_usergroup(self.company_group1.split('\\')[1], self.company_name)
        self.grouphelper.create_usergroup(self.company_group2.split('\\')[1], self.company_name)

    @test_step
    def add_attr_mappings_to_saml_app(self):
        """Adds attr mappings to saml app"""
        self.samlhelper.modify_attribute_mappings(self.attr_mappings, True)

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
            self.log.info("Skipping SLO verfication & logging out manually at Okta")
            self.helper_obj.logout_from_okta(admin_user=False)

    def enable_privacy_settings(self):
        company = self.ta_commcell.organizations.get(self.company_name)
        company.enable_company_data_privacy()

    def run(self):
        try:
            self.init_tc()

            self.create_company()
            self.create_tenant_admin_user()
            self.log.info("Logging in as tenant admin")
            self.ta_commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                        commcell_username=self.tenant_admin_email,
                                        commcell_password=self.tenant_admin_password,
                                        verify_ssl=False)
            self.samlhelper = SamlHelperMain(self.ta_commcell)
            self.create_saml_app()

            self.create_company_usergroups()
            self.enable_privacy_settings()

            self.samlhelper.modify_saml_general_settings(default_usergroups=[self.company_group1])

            self.download_certificate()
            self.admin_console.logout()
            (self.helper_obj.
             login_to_okta_and_edit_general_settings(okta_url=self.OKTA_url,
                                                     username=self.tcinputs['IDP admin username'],
                                                     pwd=self.tcinputs['IDP admin password'],
                                                     app_name=self.tcinputs['appname'],
                                                     sso_url=self.samlhelper.spmetadata['singleSignOnUrl'],
                                                     sp_entity_id=self.samlhelper.spmetadata['entityId'],
                                                     group_attribute=self.idp_grp_mapping,
                                                     attributes=self.idp_attr_mappings,
                                                     slo=True,
                                                     single_logout_url=self.samlhelper.spmetadata['singleLogoutUrl'],
                                                     sp_issuer=self.samlhelper.spmetadata['entityId'],
                                                     certificate=self.cert
                                                     ))
            time.sleep(2)
            self.helper_obj.logout_from_okta()

            self.helper_obj.initiate_saml_login_with_okta(command_center_url=self.command_center_url,
                                                          hostname=self.commcell.webconsole_hostname,
                                                          okta_url=self.OKTA_url,
                                                          username=self.tcinputs['SAML user email'],
                                                          pwd=self.tcinputs['SAML user pwd'],
                                                          app_name=self.tcinputs['appname'],
                                                          is_idp_initiated=False)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()

            self.samlhelper2.validate_samluser_properties(user_email=self.tcinputs['SAML user email'],
                                                          props={
                                                              'usergroups': [self.company_group1],
                                                              'login': self.tcinputs['SAML user email'],
                                                              'upn': self.tcinputs['SAML user email']
                                                          })

            self.add_attr_mappings_to_saml_app()
            self.samlhelper.validate_attribute_mappings(self.attr_mappings)

            self.helper_obj.initiate_saml_login_with_okta(command_center_url=self.command_center_url,
                                                          hostname=self.commcell.webconsole_hostname,
                                                          okta_url=self.OKTA_url,
                                                          username=self.tcinputs['SAML user email'],
                                                          pwd=self.tcinputs['SAML user pwd'],
                                                          app_name=self.tcinputs['appname'],
                                                          is_idp_initiated=True)
            self.helper_obj.initiate_saml_logout_with_okta(hostname=self.commcell.webconsole_hostname)
            self.verify_slo()

            self.samlhelper2.validate_samluser_properties(user_email=self.tcinputs['SAML user new email'],
                                                          props={
                                                              'login': self.tcinputs['SAML user new login'],
                                                              'userGuid': self.tcinputs['SAML user guid'],
                                                              'usergroups': [self.company_group2],
                                                              'name': self.tcinputs['SAML user fullname'],
                                                              'upn': self.tcinputs['SAML user email']
                                                          })

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.commcell.organizations.delete(self.company_name)
            if self.cert:
                self.machine.delete_file(self.cert)

        finally:
            Browser.close_silently(self.browser)
