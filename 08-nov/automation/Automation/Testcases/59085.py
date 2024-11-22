"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    user group association / dissociation for reseller saml app
                    operator for view for reseller child companies

Input Example:

    "testCases": {
            "59085":{
                    "IDP URL": string,
                    "IDP admin username": string,
                    "IDP admin password": string,
                    "idpmetadata_xml_path": string,
                    "appname": string,
                    "email_suffix": string,
                    "SAML user email": SAML User present in IDP,
                    "SAML user pwd": string
                }
            }
"""
import time
from urllib.parse import quote
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from cvpysdk.commcell import Commcell
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.organizationhelper import OrganizationHelper
from Server.Security.samlhelper import SamlHelperMain
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from AutomationUtils.machine import Machine

from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing SAML login with Azure as IDP and validates the user landing page during IDP init login"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Reseller cases for Schuberg Philis"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None

        self.machine = None
        self.download_directory = None
        self.OKTA_url = None
        self.helper_obj = None
        self.userhelper = None
        self.grouphelper = None
        self.attr_mappings = None
        self.idp_grp_mapping = None
        self.saml_appname = None
        self.reseller_group1 = None
        self.reseller_group2 = None
        self.reseller = None
        self.child1 = None
        self.child2 = None
        self.child1_obj = None
        self.child2_obj = None
        self.reseller_admin_email = None
        self.reseller_admin_password = None
        self.samlhelper = None
        self.cert = None
        self.reseller_commcell = None
        self.orghelper = None

        self.tcinputs = {
            "IDP URL": None,
            "idpmetadata_xml_path": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "email_suffix": None,
            "SAML user email": None,
            "SAML user pwd": None
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

            self.OKTA_url = 'https://' + self.tcinputs['IDP URL'] + '/'

            self.helper_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.grouphelper = UsergroupHelper(self.commcell)
            self.userhelper = UserHelper(self.commcell)
            self.orghelper = OrganizationHelper(self.commcell)

            self.attr_mappings = {
                'user groups': 'usergroup'
            }
            self.idp_grp_mapping = {"usergroup": ""}

            self.reseller = 'reseller' + str(datetime.today().microsecond)
            self.saml_appname = self.reseller  # Company name same as saml app due to user group attribute mapping
            self.reseller_group1 = self.reseller + '\\' + 'g1' + str(datetime.today().microsecond)
            self.reseller_group2 = self.reseller + '\\' + 'g2' + str(datetime.today().microsecond)

            self.child1 = 'child1_' + str(datetime.today().microsecond)
            self.child2 = 'child2_' + str(datetime.today().microsecond)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_reseller_company(self):
        """Create a reseller company"""
        self.orghelper.create(self.reseller, company_alias=self.reseller)
        self.orghelper.edit_company_properties({"general":{"resellerMode": True}})

    @test_step
    def create_reseller_usergroups(self):
        """Create two commcell user groups"""
        self.grouphelper.create_usergroup(self.reseller_group1.split('\\')[1], self.reseller)
        self.grouphelper.create_usergroup(self.reseller_group2.split('\\')[1], self.reseller)

    @test_step
    def create_child_companies(self):
        """Create two child companies"""
        self.orghelper = OrganizationHelper(self.reseller_commcell)
        self.child1_obj = self.orghelper.create(self.child1, company_alias=self.child1)
        self.child2_obj = self.orghelper.create(self.child2, company_alias=self.child2)

    @test_step
    def add_usergroups_as_company_operator(self):
        """Add Reseller groups as operator to each child company"""
        self.child1_obj.add_user_groups_as_operator([self.reseller_group1], 'UPDATE')
        self.child2_obj.add_user_groups_as_operator([self.reseller_group2], 'UPDATE')

    @test_step
    def create_reseller_admin_user(self):
        """Create a tenant admin user for reseller company"""
        user_name = self.reseller + 'admin'
        self.reseller_admin_email = user_name + '@' + self.reseller + '.in'
        self.reseller_admin_password = self.userhelper.password_generator(3,12)
        self.userhelper.create_user(self.reseller + '\\' + user_name,
                                    email=self.reseller_admin_email,
                                    password=self.reseller_admin_password,
                                    local_usergroups=[self.reseller + '\\Tenant Admin'])

    @test_step
    def create_reseller_saml_app(self):
        """Create a SAML app for reseller company"""
        self.samlhelper.create_saml_app(self.saml_appname,
                                        self.name,
                                        self.tcinputs['idpmetadata_xml_path'],
                                        auto_generate_sp_metadata=True,
                                        email_suffixes=[self.tcinputs['email_suffix']])

    @test_step
    def add_usergroup_mapping(self):
        """Add user group mapping to saml app"""
        time.sleep(5)
        self.samlhelper.modify_attribute_mappings(self.attr_mappings, True)

    @test_step
    def download_certificate(self):
        """ Download SAML app certificate """
        encoded = quote(self.saml_appname)
        download_url = self.admin_console.base_url + "downloadSPCertificate.do?appName=" + encoded
        parent_handle = self.admin_console.driver.current_url
        self.admin_console.browser.open_url_in_new_tab(download_url)
        self.admin_console.browser.open_url_in_new_tab(parent_handle)
        self.admin_console.close_popup()
        filename = self.saml_appname + ".cer"
        self.cert = self.download_directory + "\\" + filename
        time.sleep(5)

    @test_step
    def verify_slo(self):
        """Verify SLO"""
        self.admin_console.browser.open_url_in_new_tab(self.OKTA_url)
        if not self.helper_obj.check_slo(self.OKTA_url):
            raise Exception('SLO failed')

    @test_step
    def validate_operator_view(self, present_company=None, absent_company=None):
        """Check if company name is present in switcher"""

        self.admin_console.close_popup()

        self.admin_console.navigator.switch_company_as_operator(present_company)

        try:
            self.admin_console.navigator.switch_company_as_operator(absent_company)
            raise Exception('custom')
        except Exception as exp:
            if exp.args[0] == 'custom':
                raise Exception("company {0} is present in dropdown, raising exception".format(absent_company))

    @test_step
    def reassociate_smtp_to_samlapp(self):
        """Disassociate and associate email suffix back to saml app
            MR : 358030
        """
        self.samlhelper.modify_associations('emailSuffixes', self.tcinputs['email_suffix'], False)
        self.samlhelper.modify_associations('emailSuffixes', self.tcinputs['email_suffix'], True)

    def run(self):
        try:
            self.init_tc()
            self.create_reseller_company()
            self.create_reseller_usergroups()

            self.create_reseller_admin_user()
            self.reseller_commcell = Commcell(self.commcell.webconsole_hostname,
                                              self.reseller_admin_email,
                                              self.reseller_admin_password)

            self.create_child_companies()
            self.add_usergroups_as_company_operator()

            self.samlhelper = SamlHelperMain(self.reseller_commcell)

            self.create_reseller_saml_app()
            self.add_usergroup_mapping()
            self.download_certificate()
            self.admin_console.logout()

            self.idp_grp_mapping.update({'usergroup': self.reseller_group1.split('\\')[1]})
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper.spmetadata['entityId'],
                                                                    attributes=self.idp_grp_mapping,
                                                                    slo=True,
                                                                    single_logout_url=self.samlhelper.spmetadata[
                                                                        'singleLogoutUrl'],
                                                                    sp_issuer=self.samlhelper.spmetadata['entityId'],
                                                                    certificate=self.cert
                                                                    )
            time.sleep(2)
            self.helper_obj.logout_from_okta()
            time.sleep(2)

            self.helper_obj.initiate_saml_login_with_okta(self.admin_console.base_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.validate_operator_view(self.child1, self.child2)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()

            self.idp_grp_mapping.update({'usergroup': self.reseller_group2.split('\\')[1]})
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper.spmetadata['entityId'],
                                                                    attributes=self.idp_grp_mapping)
            time.sleep(2)
            self.helper_obj.logout_from_okta()
            time.sleep(2)

            self.helper_obj.initiate_saml_login_with_okta(self.admin_console.base_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.validate_operator_view(self.child2, self.child1)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()

            self.reassociate_smtp_to_samlapp()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.log.info('Deleting company : ' + self.child1)
            self.reseller_commcell.organizations.delete(self.child1)
            self.log.info('Deleting company : ' + self.child2)
            self.reseller_commcell.organizations.delete(self.child2)
            self.log.info('Deleting company : ' + self.reseller)
            self.commcell.organizations.delete(self.reseller)
            self.machine.delete_file(self.cert)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
