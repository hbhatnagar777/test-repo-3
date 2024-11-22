"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating cases in commcell SAML app with name same as AD

Input Example:

    "testCases": {
            "62311": {
                    "IDP URL": "",
                    "IDP admin username": "",
                    "IDP admin password": "",
                    "ADAdmin": "",
                    "ADAdminPass": "",
                    "domain_name": "",
                    "netbios_name": "",
                    "idp_metadata_xml_path": "",
                    "email_suffix": "",
                    "SAML user email": "",
                    "SAML user pwd": "This should be a common pwd for SAML User and SAML user2",
                    "SAML username": "Display name from AD if using Okta",
                    "appname": "app name in IDP",
                    "SAML user2 email": ""
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
        self.name = "Commcell SAML app with same name as AD"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.machine = None
        self.download_directory = None
        self.local_group = None
        self.OKTA_url = None
        self.command_center_url = None
        self.idp_attr_mapping = None
        self.company_name = None
        self.saml_appname = None
        self.attr_mapping = None
        self.cert = None

        self.samlhelper = None
        self.grouphelper = None
        self.userhelper = None
        self.orghelper = None
        self.helper_obj = None

        self.tcinputs = {
            'ADAdminPass': None,
            'ADAdmin': None,
            'netbios_name': None,
            'domain_name': None,
            'IDP URL': None,
            'idp_metadata_xml_path': None,
            'email_suffix': None,
            'SAML user email': None,
            'SAML user pwd': None,
            'SAML username': None,
            'appname': None,
            'SAML user2 email': None
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
            self.samlhelper = SamlHelperMain(self.commcell)
            self.command_center_url = "https://" + self.commcell.webconsole_hostname + "/commandcenter"
            self.OKTA_url = 'https://' + self.tcinputs['IDP URL'] + '/'

            self.attr_mapping = {
                'company name': 'company'
            }
            self.idp_attr_mapping = {'company': None}

            self.local_group = 'g1' + str(datetime.today().microsecond)
            self.company_name = 'test' + str(datetime.today().microsecond)
            self.saml_appname = self.tcinputs['netbios_name']  # Saml app name same as AD

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_AD(self):
        """Creates AD"""
        self.commcell.domains.add(self.tcinputs['domain_name'],
                                  self.tcinputs['netbios_name'],
                                  self.tcinputs['ADAdmin'],
                                  self.tcinputs['ADAdminPass'],
                                  enable_sso=False,
                                  company_id=0)

    @test_step
    def add_AD_group(self):
        """Adds an AD user group"""
        self.grouphelper.create_usergroup('Domain Users', self.tcinputs['netbios_name'],
                                          local_groups=['master'])

    @test_step
    def create_saml_app(self):
        """Creates saml app"""
        self.samlhelper.create_saml_app(self.saml_appname,
                                        self.name,
                                        self.tcinputs['idp_metadata_xml_path'],
                                        auto_generate_sp_metadata=True,
                                        email_suffixes=[self.tcinputs['email_suffix']])

    @test_step
    def create_usergroup(self):
        """Create usergroup"""
        self.grouphelper.create_usergroup(self.local_group)

    @test_step
    def create_company(self):
        """Create a company"""
        self.orghelper.create(self.company_name, company_alias=self.company_name)
        self.idp_attr_mapping = {
            'company': self.company_name
        }

    @test_step
    def add_attr_mappings_to_saml_app(self):
        """Adds attr mappings to saml app"""
        self.samlhelper.modify_attribute_mappings(self.attr_mapping, True)

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

    def run(self):
        try:
            self.init_tc()

            self.create_AD()
            self.add_AD_group()
            self.create_saml_app()
            self.create_usergroup()
            self.create_company()
            self.samlhelper.modify_saml_general_settings(default_usergroups=[self.local_group])

            self.download_certificate()
            self.admin_console.logout()
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper.spmetadata['entityId'],
                                                                    attributes=self.idp_attr_mapping,
                                                                    slo=True,
                                                                    single_logout_url=self.samlhelper.spmetadata[
                                                                        'singleLogoutUrl'],
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

            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user email'], {
                'usergroups': [self.local_group, self.tcinputs['netbios_name']+'\\Domain Users'],
                'login': self.tcinputs['netbios_name'] + '\\' + self.tcinputs['SAML user email'].split('@')[0]
            })

            self.add_attr_mappings_to_saml_app()
            self.samlhelper.validate_attribute_mappings(self.attr_mapping)

            self.helper_obj.initiate_saml_login_with_okta(self.command_center_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user2 email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          True)

            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user2 email'], {
                'login': self.company_name + '\\' + self.tcinputs['SAML user2 email'].split('@')[0],
                'usergroups': [self.company_name + '\\Tenant Users']
            })

            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.samlhelper.delete_saml_app()
            self.log.info('Deleting local user group')
            self.grouphelper.delete_usergroup(self.local_group,
                                              new_user=self.inputJSONnode['commcell']['commcellUsername'])

            if self.cert:
                self.machine.delete_file(self.cert)
            self.log.info('Deleting AD')
            self.commcell.domains.delete(self.tcinputs['netbios_name'])
            self.log.info('Deleting Company')
            self.commcell.organizations.delete(self.company_name)

        finally:
            Browser.close_silently(self.browser)
