"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    SAML login with email and userGUID mappings

Input Example:

    "testCases": {
            "59906":{
                    "appname": appname in IDP",
                    "email_suffix": saml app email smtp,
                    "IDP admin password": "string",
                    "IDP admin username": "string",
                    "IDP URL": "string",
                    "idpmetadata_xml_path": metadata xml file path,
                    "SAML user email": SAML user email in Okta,
                    "SAML user guid": SAML user guid in Okta,
                    "SAML user secondary email": Secondary email for SAML user in OKta,
                    "SAML user pwd": SAML user pwd in OKta
                    }
                }
"""
from datetime import datetime
import time
from urllib.parse import quote
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Server.Security.samlhelper import SamlHelperMain
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Server.Security.userhelper import UserHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing SAML login with email and userGUID mappings"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAML login with email and userGUID mappings"
        self.browser = None
        self.machine = None
        self.cert = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.sp_entity_id = None
        self.webconsole_url = None
        self.OKTA_url = None
        self.download_directory = None
        self.saml_appname = None
        self.attr_mappings = None
        self.idp_attr_mappings = None

        self.samlhelper = None
        self.utility = None
        self.helper_obj = None
        self.userhelper = None

        self.tcinputs = {
            "idpmetadata_xml_path": None,
            "email_suffix": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "SAML user email": None,
            "SAML user pwd": None,
            "SAML user guid": None,
            "SAML user secondary email": None
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

            self.samlhelper = SamlHelperMain(self.commcell)
            self.utility = OptionsSelector(self.commcell)
            self.helper_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.userhelper = UserHelper(self.commcell)

            self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
            self.OKTA_url = 'https://' + self.tcinputs['IDP URL'] + '/'

            self.saml_appname = 'samlapp' + str(datetime.today().microsecond)

            self.attr_mappings = {
                'Email': 'email',
                'user guid': 'guid'
            }

            self.idp_attr_mappings = {
                'email': 'user.email',
                'guid': 'user.objectGUID'
            }

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_app(self):
        """Create a SAML App"""
        self.samlhelper.create_saml_app(self.saml_appname,
                                        self.name,
                                        self.tcinputs['idpmetadata_xml_path'],
                                        auto_generate_sp_metadata=True,
                                        email_suffixes=[self.tcinputs['email_suffix']])

    @test_step
    def add_attribute_mappings(self):
        """Add Guid and Email mapping to saml app"""
        time.sleep(5)
        self.samlhelper.modify_attribute_mappings(self.attr_mappings, True)

    @test_step
    def unset_nameid_value(self):
        """Unset NameId value from SAML App"""
        query = """Delete from App_ThirdPartyAppProp where attrName = 'NameId Attribute Mapping' and componentNameId in 
        (select id from App_ThirdPartyApp where appName = '{0}')""".format(self.saml_appname)

        self.utility.update_commserve_db(query)

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
        self.init_tc()
        try:
            self.create_saml_app()
            self.add_attribute_mappings()
            self.unset_nameid_value()

            self.download_certificate()
            self.admin_console.logout()
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper.spmetadata['entityId'],
                                                                    attributes=self.idp_attr_mappings,
                                                                    slo=True,
                                                                    single_logout_url=self.samlhelper.spmetadata[
                                                                        'singleLogoutUrl'],
                                                                    sp_issuer=self.samlhelper.spmetadata['entityId'],
                                                                    certificate=self.cert
                                                                    )
            time.sleep(2)
            self.helper_obj.logout_from_okta()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.verify_slo()

            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user email'], {
                'login': self.tcinputs['SAML user email'],
                'userGuid': self.tcinputs['SAML user guid']
            })

            self.idp_attr_mappings.update({'email': 'user.secondEmail'})
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.samlhelper.spmetadata['singleSignOnUrl'],
                                                                    self.samlhelper.spmetadata['entityId'],
                                                                    attributes=self.idp_attr_mappings)
            time.sleep(2)
            self.helper_obj.logout_from_okta()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user email'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)

            self.samlhelper.validate_samluser_properties(self.tcinputs['SAML user secondary email'], {
                'login': self.tcinputs['SAML user email'],
                'userGuid': self.tcinputs['SAML user guid']
            })

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            if self.cert:
                self.machine.delete_file(self.cert)
            self.samlhelper.delete_saml_app()
            self.userhelper.delete_user(self.tcinputs['SAML user email'],
                                        new_user=self.inputJSONnode['commcell']['commcellUsername'])

        finally:
            Browser.close_silently(self.browser)
