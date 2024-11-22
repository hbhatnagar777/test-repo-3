"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating UI options of SAML app

Input Example:

    "testCases": {
            "62593": {
                    'idpmetadata_xml_path': None,
                    'dummy_idpmetadata_xml_path': "dummy metadata file",
                    'sp_alias': "https://domain:port/endpoint",
                    'email_suffix': None,
                    'ad_host_name': "hostname of AD machine (IP does not work for IDP init url for ADFS)",
                    'ad_machine_user': None,
                    'ad_machine_password': None,
                    'SAML user email': None,
                    'SAML user pwd': None,
                    'jks_file_path': "keystore.jks file path",
                    'key_password': None,
                    'keystore_password': None,
                    'keystore_alias_name': None
                }
"""

import time
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from AutomationUtils.machine import Machine
from Server.Security.userhelper import UserHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):
    """ Testcase to validate associations of SAML app"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SAML UI Validations"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.download_directory = None
        self.sp_metadata_file = None

        self.saml_browser = None
        self.saml_admin_console = None
        self.saml_login_helper = None
        self.machine = None
        self.saml_obj = None
        self.command_center_url = None
        self.sp_entity_id = None
        self.navigator_obj = None
        self.userhelper = None

        self.tcinputs = {
            'idpmetadata_xml_path': None,
            'dummy_idpmetadata_xml_path': None,
            'sp_alias': None,
            'email_suffix': None,
            'ad_host_name': None,
            'ad_machine_user': None,
            'ad_machine_password': None,
            'SAML user email': None,
            'SAML user pwd': None,
            'jks_file_path': None,
            'key_password': None,
            'keystore_password': None,
            'keystore_alias_name': None
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

            self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.userhelper = UserHelper(self.commcell)
            self.command_center_url = "https://" + self.commcell.webconsole_hostname.lower() + "/commandcenter"
            self.sp_entity_id = "https://" + self.commcell.webconsole_hostname.lower() + ":443/identity"
            self.navigator_obj = self.admin_console.navigator

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_browser(self):
        """Creates a new instance of browser for making saml logins"""
        self.saml_browser = BrowserFactory().create_browser_object()
        self.saml_browser.open()
        self.saml_admin_console = AdminConsole(self.saml_browser, self.commcell.webconsole_hostname)

        self.saml_admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                      self.inputJSONnode['commcell']['commcellPassword'])
        self.saml_login_helper = IdentityServersMain(self.saml_admin_console)
        self.saml_admin_console.logout()

    @test_step
    def create_saml_app(self):
        """Create a Commcell SAML app"""
        self.saml_obj.app_name = "samlapp" + str(datetime.today().microsecond)
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(idp_metadata_path=self.tcinputs['dummy_idpmetadata_xml_path'],
                                      sp_endpoint="https://dummyhost:443/identity",
                                      email_suffix=[self.tcinputs['email_suffix']])
        time.sleep(3)

    @test_step
    def edit_sp_entityid(self):
        """Edit SP Entity Id of saml app"""
        self.saml_obj.edit_sp_entity_id(self.sp_entity_id)

    @test_step
    def upload_idp_metadata(self):
        """Upload IDP Metadata to Saml App"""
        self.saml_obj.edit_saml_idp(app_name=self.saml_obj.app_name,
                                    idp_meta_path=self.tcinputs['idpmetadata_xml_path'])

    @test_step
    def download_sp_metadata(self):
        """Download SP metadata"""
        self.sp_metadata_file = self.saml_obj.download_spmetadata(self.download_directory)

    @test_step
    def edit_adfs_samlapp(self, operation='Create'):
        """edit saml app in adfs side
            Args : Operation    (string) 'Create' / 'Delete'
        """
        self.saml_obj.edit_trust_party_adfs(app_name=self.saml_obj.app_name,
                                            ad_host_ip=self.tcinputs['ad_host_name'],
                                            ad_machine_user=self.tcinputs['ad_machine_user'],
                                            ad_machine_password=self.tcinputs['ad_machine_password'],
                                            sp_metadata_location=self.sp_metadata_file,
                                            operation=operation)
        self.log.info("ADFS SAML app %s operation successful", operation)

    @test_step
    def perform_saml_test_login(self, command_center_url, expected=True):
        """Method to perform saml test login"""
        status = self.saml_obj.initiate_saml_login(is_idp_initiated=False,
                                                   ad_name=self.tcinputs['ad_host_name'],
                                                   command_center_url=command_center_url,
                                                   adfs_app_name=self.saml_obj.app_name,
                                                   user=self.tcinputs['SAML user email'],
                                                   password=self.tcinputs['SAML user pwd'],
                                                   verify_sso=False,
                                                   is_test_login=True)
        if status != expected:
            raise Exception('Saml login status [{0}] but expected [{1}]'.format(status, expected))

    @test_step
    def saml_login(self, command_center_url, expected):
        """Performs a saml login"""
        status = self.saml_login_helper.initiate_saml_login(is_idp_initiated=False,
                                                            ad_name=self.tcinputs['ad_host_name'],
                                                            command_center_url=command_center_url,
                                                            adfs_app_name=self.saml_obj.app_name,
                                                            user=self.tcinputs['SAML user email'],
                                                            password=self.tcinputs['SAML user pwd'],
                                                            verify_sso=False)
        if status != expected:
            raise Exception('Saml login status [{0}] but expected [{1}]'.format(status, expected))

    @test_step
    def add_sp_alias(self):
        """Add a new sp alias to saml app"""
        self.saml_obj.add_sp_alias(self.tcinputs['sp_alias'])

    def run(self):
        self.init_tc()
        try:
            # Creating another instance of browser for saml logins
            self.create_saml_browser()
            self.create_saml_app()

            # edit SP entity id from dummy to provided in TC inputs
            self.edit_sp_entityid()

            # upload idp metadata provided in TC inputs
            self.upload_idp_metadata()

            self.download_sp_metadata()

            # Creating SAML app on ADFS
            self.edit_adfs_samlapp('Create')

            # Perform SAML Test login to enable SAML app in CC
            self.perform_saml_test_login(self.command_center_url, True)

            # Perform SAML login to CC with expected result as True
            self.saml_login(self.command_center_url, True)

            # Perform SAML logout from CC, logout should be successful
            self.saml_login_helper.initiate_saml_logout(False, ad_name=self.tcinputs['ad_host_name'],
                                                        command_center_url=self.command_center_url)

            # adding IP Address as SP alias to saml app in CC
            self.add_sp_alias()

            # Downloading new SP metadata with updated SP alias
            self.download_sp_metadata()

            # Deleting and recreating saml app on ADFS with new SP metadata
            self.edit_adfs_samlapp('Delete')
            self.edit_adfs_samlapp('Create')

            # Perform SAML login to CC with expected result as True using SP alias as login url
            self.saml_login(self.tcinputs['sp_alias'], True)
            try:
                # Perform SAML logout from CC, it will only logout CC session, but IDP session will be Present
                self.saml_login_helper.initiate_saml_logout(False, ad_name=self.tcinputs['ad_host_name'],
                                                            command_center_url=self.tcinputs['sp_alias'])
            except Exception as exc:
                self.log.info('Known issue related to landing page when attempting slo from sp alias url. %s', exc)

            # adding Public & Private Certificates created using java keytool
            self.saml_obj.edit_saml_idp(app_name=self.saml_obj.app_name,
                                        jks_file_path=self.tcinputs['jks_file_path'],
                                        key_password=self.tcinputs['key_password'],
                                        keystore_password=self.tcinputs['keystore_password'],
                                        alias_name=self.tcinputs['keystore_alias_name'])

            # Downloading new SP metadata with new certificates
            self.download_sp_metadata()

            # saml login will fail because of new certificates are added to CC saml app not on IDP side
            self.saml_login(self.command_center_url, False)
            # not handling adfs session in browser, let subsequent logins take care

            # Deleting and recreating saml app on ADFS with new SP metadata with new certificates in SP metadata
            self.edit_adfs_samlapp('Delete')
            self.edit_adfs_samlapp('Create')

            # Perform SAML login to CC with expected result as True using CC endpoint
            self.saml_login(self.command_center_url, True)

            # Perform SAML logout from CC, logout should be successful
            self.saml_login_helper.initiate_saml_logout(False, ad_name=self.tcinputs['ad_host_name'],
                                                        web_console_url=self.command_center_url)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.log.info("Deleting ADFS SAML app")
            self.edit_adfs_samlapp('Delete')

            self.saml_obj.delete_app()

            if self.sp_metadata_file:
                self.log.info("Deleting SP metadata file")
                self.machine.delete_file(self.sp_metadata_file)

            self.userhelper.delete_user(self.tcinputs['SAML user email'],
                                        new_user=self.inputJSONnode['commcell']['commcellUsername'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.saml_browser)
