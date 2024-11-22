"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    IDP initiated SAML login with Azure as IDP and validates the landing apge
                    IDP init SAML login when customDefaultApp key is set and valiadte landing apge
                    IDP init SAML login when next param is set and validates landing page

Input Example:

    "testCases": {
            "59905":{
                    "ClientName": "stormbreaker",
                    "SMTP" : "gmail.com",
                    "IDP admin username" : "user@company.onmicrosoft.com",
                    "IDP admin password" : "123456",
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
from Reports.utils import TestCaseUtils
from Server.Security.userhelper import UserHelper
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
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
        self.name = "User landing page on SAML login with azure IDP"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.sso_url = None
        self.webconsole_url = None
        self.navigator_obj = None
        self.saml_obj = None
        self.tcinputs = {
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
            self.userhelper = UserHelper(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_app(self):
        """ Adds SAML app in commcell"""
        self.saml_obj.app_name = "test" + str(datetime.today().microsecond)
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['metadata path'],
                                      description="Created via Automation for verify user landing page",
                                      email_suffix=[self.tcinputs['SMTP']]
                                      )
        self.saml_obj.sp_metadata_values()
        self.sso_url = self.saml_obj.sso_url

    @test_step
    def add_samlapp_in_azure(self):
        """ Editing SAMl app in Azure site"""
        self.log.info("SSO URL is:", self.sso_url)
        self.saml_obj.login_to_azure_and_edit_basic_saml_configuration(self.tcinputs['IDP admin username'],
                                                                       self.tcinputs['IDP admin password'],
                                                                       self.tcinputs['appname'],
                                                                       self.saml_obj.sp_entity_id,
                                                                       self.sso_url,
                                                                       self.saml_obj.slo_url)
        self.saml_obj.logout_from_azure()

    @test_step
    def idp_init_saml_login(self):
        """ Performs IDP init SAML login"""
        status = self.saml_obj.initiate_saml_login_with_azure(self.commcell.webconsole_hostname,
                                                              self.tcinputs['SAML user name'],
                                                              self.tcinputs['SAML user pwd'],
                                                              self.tcinputs['appname'],
                                                              True)
        return status

    @test_step
    def validate_landing_page(self):
        """ Validates the SAML user landing page after redirection from IDP """
        if self.admin_console.check_if_entity_exists('xpath', '//*[@data-ng-if="showUserSettingsDropdown"]'):
            self.log.info("User landed on adminconsole page")
            flag = 0
        elif self.admin_console.check_if_entity_exists('xpath', '//*[@aria-controls="header-username-menu"]'):
            self.log.info("User landed on webconsole page")
            flag = 1
        else:
            raise CVTestStepFailure("Error occurred!!!")
        return flag

    @test_step
    def add_additional_setting(self, value):
        """ Adding additional key and restart required services"""
        self.log.info('Adding Additional Setting')
        self.commcell.add_additional_setting(category='WebConsole',
                                             key_name='customDefaultApp',
                                             data_type='STRING',
                                             value=value)
        self.log.info('Setting added Successfully')
        self.log.info("Restarting Tomcat service ...")
        self.client.restart_service(service_name='GxTomcatInstance001')
        time.sleep(240)
        self.log.info('Services Restarted Successfully')

    @test_step
    def sp_init_logout(self):
        """
        SAML Logout from SP
        """
        status = self.saml_obj.sp_init_logout(self.commcell.webconsole_hostname)

        if not status:
            raise Exception("Error occurred while SAML logout/validation")

    def run(self):
        try:
            self.init_tc()
            self.create_saml_app()
            self.admin_console.logout()

            self.add_samlapp_in_azure()
            self.add_additional_setting('adminconsole')

            status = self.idp_init_saml_login()
            if status:
                flag = self.validate_landing_page()
                if flag != 0:
                    raise Exception("User had to land on command center page but landed on " +
                                    self.admin_console.driver.current_url)

            self.sp_init_logout()

            self.add_additional_setting('webconsole')

            status = self.idp_init_saml_login()
            if status:
                flag = self.validate_landing_page()
                if flag != 1:
                    raise Exception("User had to land on webconsole page but landed on " +
                                    self.admin_console.driver.current_url)

            self.sp_init_logout()

            self.sso_url = self.sso_url + "&next=https%3A%2F%2F"+self.commcell.webconsole_hostname+"%2Fadminconsole%2F"

            self.add_samlapp_in_azure()

            status = self.idp_init_saml_login()
            if status:
                flag = self.validate_landing_page()
                if flag != 0:
                    raise Exception("User had to land on command center page but landed on " +
                                    self.admin_console.driver.current_url)

            self.sp_init_logout()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.commcell.delete_additional_setting('WebConsole', 'customDefaultApp')
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.saml_obj.delete_app()
            self.userhelper.delete_user(self.tcinputs['SAML user name'],
                                        new_user=self.inputJSONnode['commcell']['commcellUsername'])

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
