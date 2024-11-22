from selenium.webdriver.common.by import By
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    Single logout with OKTA as IDP
Input Example:

    "testCases": {
            "56615":{
                    "ClientName": "venus",
                    "SMTP" : "color.indigo.com",
                    "IDP URL" : "dev-709216.okta.com",
                    "IDP admin username" : "testadmin@commvault.com",
                    "IDP admin password" : "pwd",
                    "appname" : "AutomationApp",
                    "metadata path" : "C:\\AutomationApp.xml",
                    "SAML user name" : "user1@color.indigo.com",
                    "SAML user pwd" : "pwd1"
                    }
                }
"""
import time
from datetime import datetime
import urllib.parse as urlparse
from urllib.parse import parse_qs, quote

from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.AdminConsolePages.identity_server_details import IdentityServerDetails
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SAML login with OKTA as IDP"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.sp_entity_id = None
        self.webconsole_url = None
        self.OKTA_url = None
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
            factory = BrowserFactory()
            try:
                self.machine = Machine(self.client)
                self.download_directory = self.utils.get_temp_dir()
                self.machine.create_directory(self.download_directory)
            except Exception as exp:
                if str(exp == "Directory already exists"):
                    self.log.info("Directory already exists")

            self.browser = factory.create_browser_object(Browser.Types.FIREFOX)
            self.browser.set_downloads_dir(self.download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.driver = self.admin_console.driver
            self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.saml_details = IdentityServerDetails(self.admin_console)
            self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
            self.navigator_obj = self.admin_console.navigator
            self.OKTA_url = "https://" + self.tcinputs['IDP URL'] + "/"

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_app(self):
        """ Adds SAML app """
        self.saml_obj.app_name = "test" + str(datetime.today().microsecond)
        self.__navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['metadata path'],
                                      self.tcinputs['SMTP'],
                                      self.webconsole_url,
                                      False,
                                      None)
        self.sso_url = self.saml_obj.get_sso_url()
        self.sp_entity_id = self.saml_obj.get_sp_entity_id()
        parsed = urlparse.urlparse(self.sso_url)
        query_param = parse_qs(parsed.query)['samlAppKey']
        self.appkey = ""
        self.appkey = self.appkey.join(query_param)
        self.slo_url = self.webconsole_url + "/server/SAMLSingleLogout?samlAppKey=" + self.appkey

    @test_step
    def __navigate_to_identity_servers(self):
        """ navigating to Identity servers page """
        global_search = self.driver.find_element(By.XPATH, "//input[@id='nav-search-field']")
        global_search.clear()
        global_search.send_keys(self.admin_console.props['label.nav.identityServers'])
        self.admin_console.wait_for_completion()
        self.driver.find_element(By.XPATH, 
            f"//nav[@class='nav side-nav navigation']//a[@id='navigationItem_musers']/span").click()
        self.admin_console.wait_for_completion()
        self.driver.find_element(By.ID, "tileMenuSelection_identityServers").send_keys(Keys.RETURN)
        self.admin_console.wait_for_completion()

    @test_step
    def download_certificate(self):
        """ Download SAML app certificate """
        encoded = quote(self.saml_obj.app_name)
        download_url = "https://" + self.commcell.webconsole_hostname +"/adminconsole/downloadSPCertificate.do?appName=" + encoded
        parent_handle = self.driver.current_url
        self.browser.open_url_in_new_tab(download_url)
        self.browser.switch_to_tab(parent_handle)
        Filename = self.saml_obj.app_name + ".cer"
        self.cert = self.download_directory + "\\" + Filename

    @test_step
    def saml_logout(self):
        """ SAML Logout """
        self.saml_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
        self.saml_obj.single_logout(self.OKTA_url)

    def run(self):
        try:
            self.init_tc()
            self.create_saml_app()
            self.download_certificate()
            self.admin_console.logout()
            self.saml_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                  self.tcinputs['IDP admin username'],
                                                                  self.tcinputs['IDP admin password'],
                                                                  self.tcinputs['appname'],
                                                                  self.sso_url,
                                                                  self.sp_entity_id,
                                                                  slo=True,
                                                                  single_logout_url=self.slo_url,
                                                                  sp_issuer=self.sp_entity_id,
                                                                  certificate=self.cert)
            self.saml_obj.logout_from_okta()
            self.saml_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                        self.commcell.webconsole_hostname,
                                                        self.OKTA_url,
                                                        self.tcinputs['SAML user name'],
                                                        self.tcinputs['SAML user pwd'],
                                                        self.tcinputs['appname'],
                                                        False
                                                        )
            time.sleep(5)
            self.saml_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
            self.browser.open_url_in_new_tab(self.OKTA_url)
            status = self.saml_obj.check_slo(self.OKTA_url)
            if status:
                self.log.info("Single Logout is successful")
            else:
                raise CVTestStepFailure("Single Logout failed")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Deleting the app ")
            self.__navigate_to_identity_servers()
            self.saml_obj.open_saml_app(self.saml_obj.app_name)
            self.saml_details.delete_saml_app()

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
