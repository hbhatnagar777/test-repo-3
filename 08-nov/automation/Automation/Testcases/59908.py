from selenium.webdriver.common.by import By
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    - Commcell console GUI option when showGuiConsoleOnSamlLogin key is added
                    - Commcell console GUI option when showGuiConsoleSSO key is added
                    for SAML and local users

Input Example:

    "testCases": {
            "59908":{
                    "ClientName": "stormbreaker",
                    "SMTP" : "gmail.com",
                    "IDP admin username" : "user@company.onmicrosoft.com",
                    "IDP admin password" : "#####",
                    "appname" : "AutomationApp",
                    "metadata path" : "C:\\AutomationApp.xml",
                    "SAML user name" : "user1@test.indigo.com",
                    "SAML user pwd" : "pwd1",
                    }
                }
"""
import time
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Server.Security.userhelper import UserHelper
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """Class for executing SAML login with OKTA as IDP"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAML login with azure IDP"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.sp_entity_id = None
        self.webconsole_url = None
        self.azure_url = None
        self.navigator_obj = None
        self.saml_obj = None
        self.tcinputs = {
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "metadata path": None,
            "SMTP": None,
            "saml user1": None,
            "user1 pwd": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.machine = Machine()
            self.download_directory = self.utils.get_temp_dir()
            self.machine.create_directory(self.download_directory, force_create=True)

            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.web_console = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
            self.navigator_obj = self.admin_console.navigator
            self.azure_url = "https://portal.azure.com/"
            self.user = Users(self.admin_console)
            self.userhelper = UserHelper(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_app(self):
        """ Adding SAML app in commcell with Azure as IDP"""
        self.saml_obj.app_name = "test" + str(datetime.today().microsecond)
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['metadata path'],
                                      description="Created via Automation for verify user landing page",
                                      email_suffix=[self.tcinputs['SMTP']]
                                      )
        self.saml_obj.sp_metadata_values()

    @test_step
    def sp_init_saml_login(self, username, pwd):
        """ Performs SP init SAML login"""
        status = self.saml_obj.initiate_saml_login_with_azure(self.webconsole_url,
                                                              username,
                                                              pwd,
                                                              self.tcinputs['appname'],
                                                              False,
                                                              tab_off_approach=True)
        if not status:
            raise CVTestStepFailure("SP initiated SAML login failed")

    @test_step
    def add_samlapp_in_idp(self):
        """ Adding SAML app in Azure site"""
        self.saml_obj.login_to_azure_and_edit_basic_saml_configuration(self.tcinputs['IDP admin username'],
                                                                       self.tcinputs['IDP admin password'],
                                                                       self.tcinputs['appname'],
                                                                       self.saml_obj.sp_entity_id,
                                                                       self.saml_obj.sso_url,
                                                                       self.saml_obj.slo_url)
        self.saml_obj.logout_from_azure()

    @test_step
    def add_additional_setting(self, key_name):
        """ Adding additional key """
        self.log.info('Additional Setting : {0}'.format(key_name))
        self.commcell.add_additional_setting(category='WebConsole',
                                             key_name=key_name,
                                             data_type='BOOLEAN',
                                             value='True')
        self.log.info('Setting added Successfully')

        self.log.info("Restarting Tomcat service on the CS ...")
        self.client.restart_service(service_name='GxTomcatInstance001')
        time.sleep(240)
        self.log.info('Service Restarted Successfully')

    @test_step
    def check_if_commcell_gui_option_is_visible(self):
        """ Checking if commcell GUI tile is shown in the webconsole applications page"""
        if self.admin_console.check_if_entity_exists('xpath', '//*[@href="../samlWcToGuiSso.do"]'):
            self.log.info("Yes! Commcell console GUI option is availble")
            status = True
        else:
            self.log.info('Nope! Commcell console GUI option is not availble')
            status = False

        return status

    @test_step
    def download_commcell_gui_jnlp(self):
        """Download Commcell GUI from the webconsole applications page"""
        # self.saml_obj.download_gui_console_jnlp()
        self.admin_console.driver.find_element(By.XPATH, '//*[@href="../samlWcToGuiSso.do"]').click()
        time.sleep(5)
        if not self.machine.check_file_exists(self.download_directory):
            raise CVTestStepFailure("JNLP file is not downloaded")

    @test_step
    def saml_login(self):
        """ Do SP init SAML login and check if commcell GUI option is visible"""
        self.sp_init_saml_login(self.tcinputs['saml user1'], self.tcinputs['user1 pwd'])
        status = self.check_if_commcell_gui_option_is_visible()
        if status:
            self.download_commcell_gui_jnlp()
        else:
            raise CVTestStepFailure("Commcell GUI is not visible to SAML user even after setting key")

    @test_step
    def local_user_login(self):
        """ Do local user login to webconsole and check if commcell GUI option is available"""
        self.web_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                               self.inputJSONnode['commcell']['commcellPassword'])
        self.web_console.wait_till_load_complete()
        status = self.check_if_commcell_gui_option_is_visible()
        return status

    def run(self):
        try:
            self.init_tc()
            self.create_saml_app()
            self.admin_console.logout()

            self.commcell.delete_additional_setting(category='WebConsole', key_name='showGuiConsoleSSO')
            self.commcell.delete_additional_setting(category='WebConsole', key_name='showGuiConsoleOnSamlLogin')
            self.add_additional_setting('showGuiConsoleOnSamlLogin')

            self.add_samlapp_in_idp()

            self.saml_login()
            self.saml_obj.sp_init_logout(self.commcell.webconsole_hostname)

            status = self.local_user_login()
            if status:
                raise CVTestStepFailure("Commcell GUI is visible to local user even without showGuiConsoleSSO")

            self.web_console.logout()

            self.commcell.delete_additional_setting(category='WebConsole', key_name='showGuiConsoleOnSamlLogin')
            self.add_additional_setting('showGuiConsoleSSO')

            status = self.local_user_login()
            if status:
                self.download_commcell_gui_jnlp()
            else:
                raise CVTestStepFailure("Commcell GUI is not visible to localuser even after setting showGuiConsoleSSO")

            self.web_console.logout()

            self.saml_login()
            self.saml_obj.sp_init_logout(self.commcell.webconsole_hostname)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.saml_obj.delete_app()
            self.userhelper.delete_user(self.tcinputs['saml user1'],
                                        new_user=self.inputJSONnode['commcell']['commcellUsername'])


        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
