"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating regression cases on Reseller SAML app

Input Example:

    "testCases": {
            "62309": {
                    "IDP URL": "",
                    "idpmetadata_xml_path": "",
                    "IDP admin username": "",
                    "IDP admin password": "",
                    "IDP usergroup": "",
                    "appname": "appname in IDP",
                    "email_suffix": "",
                    "SAML user email": "",
                    "SAML user pwd": "",
                    "SAML user new email": "user.secondEmail from Okta",
                    "SAML user guid": "user.objectGUID from Okta",
                    "SAML user new login": "user.displayName from Okta",
                    "SAML user fullname": "user.firstName from Okta",
                    "SAML user2 email": "",
                    "SAML user2 pwd": "",
                    "SAML user2 new email": "",
                    "SAML user2 guid": "",
                    "SAML user2 new login": "",
                    "SAML user2 fullname": ""
                }
"""
import time
from datetime import datetime
from urllib.parse import quote
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from cvpysdk.commcell import Commcell
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.samlhelper import SamlHelperMain
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ Testcase to validate regressions of Reseller SAML login"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SAML Regression for a Reseller SAML app"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.sso_url = None
        self.sp_entity_id = None
        self.command_center_url = None
        self.OKTA_url = None
        self.attr_mappings = None
        self.idp_attr_mappings = None
        self.idp_grp_mapping = None
        self.cert = None
        self.download_directory = None
        self.reseller_company = None
        self.reseller_group1 = None
        self.reseller_group2 = None
        self.saml_appname = None
        self.reseller_admin_email = None
        self.reseller_admin_password = None
        self.child = None

        self.helper_obj = None
        self.orghelper = None
        self.userhelper = None
        self.samlhelper = None
        self.samlhelper2 = None
        self.child_obj = None
        self.grouphelper = None
        self.machine = None
        self.reseller_commcell = None

        self.tcinputs = {
            "IDP URL": None,
            "idpmetadata_xml_path": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "IDP usergroup": None,
            "appname": None,
            "email_suffix": None,
            "SAML user email": None,
            "SAML user pwd": None,
            "SAML user new email": None,
            "SAML user guid": None,
            "SAML user new login": None,
            "SAML user fullname": None,
            "SAML user2 email": None,
            "SAML user2 pwd": None,
            "SAML user2 new email": None,
            "SAML user2 guid": None,
            "SAML user2 new login": None,
            "SAML user2 fullname": None,
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
            self.samlhelper = SamlHelperMain(self.commcell)
            self.orghelper = OrganizationHelper(self.commcell)
            self.userhelper = UserHelper(self.commcell)
            self.grouphelper = UsergroupHelper(self.commcell)
            self.command_center_url = "https://" + self.commcell.webconsole_hostname + "/commandcenter"
            self.OKTA_url = 'https://' + self.tcinputs['IDP URL'] + '/'
            self.idp_grp_mapping = {"usergroup": self.tcinputs['IDP usergroup']}
            self.idp_attr_mappings = {
                'email': 'user.secondEmail',
                'un': 'user.displayName',
                'fname': 'user.firstName',
                'guid': 'user.objectGUID',
                'company': None
            }
            self.attr_mappings = {
                'Email': 'email',
                'user name': 'un',
                'full name': 'fname',
                'user guid': 'guid',
                'user groups': 'usergroup'
            }

            self.reseller_company = 'reseller' + str(datetime.today().microsecond)
            self.saml_appname = 'samlapp_reseller' + str(datetime.today().microsecond)
            self.reseller_group1 = 'g1' + str(datetime.today().microsecond)
            self.reseller_group2 = self.idp_grp_mapping['usergroup']
            self.child = 'child_' + str(datetime.today().microsecond)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_reseller_company(self):
        """Create a reseller company"""
        self.orghelper.create(self.reseller_company, company_alias=self.reseller_company)
        self.orghelper.edit_company_properties({"general": {"resellerMode": True}})
    
    @test_step
    def create_reseller_admin_user(self):
        """Create a tenant admin user for reseller company"""
        user_name = self.reseller_company + 'admin'
        self.reseller_admin_email = user_name + '@' + self.reseller_company + '.in'
        self.reseller_admin_password = self.userhelper.password_generator(complexity_level=3, min_length=12)
        self.userhelper.create_user(self.reseller_company + '\\' + user_name,
                                    email=self.reseller_admin_email,
                                    password=self.reseller_admin_password,
                                    local_usergroups=[self.reseller_company + '\\Tenant Admin'])

    @test_step
    def create_child_company(self):
        """Create a child company"""
        self.orghelper = OrganizationHelper(self.reseller_commcell)
        self.child_obj = self.orghelper.create(self.child, company_alias=self.child)
        self.idp_attr_mappings.update({'company': self.child})

    @test_step
    def create_saml_app(self):
        """Create a SAML app"""
        self.samlhelper2 = SamlHelperMain(self.reseller_commcell)
        self.samlhelper2.create_saml_app(self.saml_appname,
                                         self.name,
                                         self.tcinputs['idpmetadata_xml_path'],
                                         auto_generate_sp_metadata=True,
                                         email_suffixes=[self.tcinputs['email_suffix']])

    @test_step
    def create_usergroups(self):
        """Create reseller company usergroups"""
        self.grouphelper.create_usergroup(self.reseller_group1, self.reseller_company)
        self.grouphelper.create_usergroup(self.reseller_group2, self.reseller_company)

    @test_step
    def add_attr_mappings_to_saml_app(self):
        """Adds attr mappings to saml app"""
        self.samlhelper2.modify_attribute_mappings(self.attr_mappings, True)

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
    def delete_usergroups(self):
        """Deletes user groups"""
        self.grouphelper.delete_usergroup(self.reseller_group1,
                                          new_user=self.inputJSONnode['commcell']['commcellUsername'])
        self.grouphelper.delete_usergroup(self.reseller_group2,
                                          new_user=self.inputJSONnode['commcell']['commcellUsername'])

    def run(self):
        try:
            self.init_tc()

            self.create_reseller_company()
            self.create_reseller_admin_user()
            self.reseller_commcell = Commcell(self.commcell.webconsole_hostname,
                                              self.reseller_admin_email,
                                              self.reseller_admin_password,
                                              verify_ssl=False)
            self.create_child_company()
            self.create_saml_app()

            self.create_usergroups()
            self.samlhelper2.modify_saml_general_settings(default_usergroups=[(self.reseller_company + '\\'
                                                                              + self.reseller_group1)])

            self.download_certificate()
            self.admin_console.logout()
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper2.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper2.spmetadata['entityId'],
                                                                    group_attribute=self.idp_grp_mapping,
                                                                    attributes=self.idp_attr_mappings,
                                                                    slo=True,
                                                                    single_logout_url=self.samlhelper2.spmetadata['singleLogoutUrl'],
                                                                    sp_issuer=self.samlhelper2.spmetadata['entityId'],
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

            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user email'], {
                'usergroups': [self.reseller_company + '\\' + self.reseller_group1],
                'login': self.tcinputs['SAML user email'],
                'upn': self.tcinputs['SAML user email']
            })

            self.add_attr_mappings_to_saml_app()
            self.samlhelper2.validate_attribute_mappings(self.attr_mappings)

            self.helper_obj.initiate_saml_login_with_okta(self.command_center_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          True)
            self.admin_console.close_popup()
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()

            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user new email'], {
                'login': self.tcinputs['SAML user new login'],
                'userGuid': self.tcinputs['SAML user guid'],
                'usergroups': [self.reseller_company + '\\' + self.reseller_group2],
                'name': self.tcinputs['SAML user fullname'],
                'upn': self.tcinputs['SAML user email']
            })

            self.log.info('Add company mapping to saml app')
            self.samlhelper2.modify_attribute_mappings({'company name': 'company'}, True)
            time.sleep(5)
            self.log.info('Remove user group mapping from saml app')
            self.samlhelper2.modify_attribute_mappings({'user groups': 'usergroup'}, False)
            self.helper_obj.initiate_saml_login_with_okta(self.command_center_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user2 email'],
                                                          self.tcinputs['SAML user2 pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()
            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user2 new email'], {
                "login": self.child + '\\' + self.tcinputs['SAML user2 new login'],
                "usergroups": [self.child + '\\Tenant Users'],
                "userGuid": self.tcinputs['SAML user2 guid'],
                "name": self.tcinputs['SAML user2 fullname'],
                "upn": self.tcinputs['SAML user2 email']
            })

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            if self.cert:
                self.machine.delete_file(self.cert)
            self.log.info('Deleting company {0}'.format(self.child))
            self.reseller_commcell.organizations.delete(self.child)
            self.log.info('Deleting company {0}'.format(self.reseller_company))
            self.commcell.organizations.delete(self.reseller_company)

        finally:
            Browser.close_silently(self.browser)
