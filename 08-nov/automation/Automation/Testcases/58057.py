"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    login with timestamp difference
                    login with SP initiated link
Input Example:

    "testCases": {
            "56615":{
                    "ClientName": "venus",
                    "SMTP" : "test.indigo.com",
                    "IDP URL" : "company.com",
                    "IDP admin username" : "test@company.com",
                    "IDP admin password" : "#####",
                    "appname" : "AutomationApp",
                    "metadata path" : "C:\\AutomationApp.xml",
                    "SAML user name" : "user1@test.indigo.com",
                    "SAML user pwd" : "pwd1"
                    }
                }
"""
import time
import datetime

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
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

    @test_step
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
            self.OKTA_url = "https://" + self.tcinputs['IDP URL']
            self.options_selector = OptionsSelector(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_saml_app(self):
        """ Adds SAML app """
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.app_name = "testcase5"
        self.saml_obj.create_saml_app(self.tcinputs['metadata path'],
                                      self.tcinputs['SMTP'],
                                      self.webconsole_url,
                                      False,
                                      None
                                      )
        self.sso_url = self.saml_obj.get_sso_url()
        self.sp_entity_id = self.saml_obj.get_sp_entity_id()

    @test_step
    def add_minutes_to_system_time(self, minutes=10):
        """Adds specified number of minutes to current system time
            Args:
                minutes(int)   -- minutes
                    Default - 1

            Raises:
                Exception, if the powershell command execution fails

            Returns:
                String name of the owner result"""
        current = self.cs_machine_obj.current_time()
        self.log.info(current)
        new_date = current + datetime.timedelta(minutes=minutes)
        self.log.info(new_date)
        command = 'set-date -date "{0}"'.format(new_date)
        self.log.info(command)
        output = self.cs_machine_obj.execute_command(command)
        self.log.info(output)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    @test_step
    def change_system_time(self):
        """ Changing System Time """
        self.cs_machine_obj = Machine(self.commcell.commserv_client)
        self.log.info(self.cs_machine_obj)
        self.log.info('Adding time')
        self.add_minutes_to_system_time()
        self.log.info('Added successfully')

    @test_step
    def add_additional_setting(self):
        """ Adding additional key """
        self.log.info('Adding Additional Setting')
        self.commcell.add_additional_setting(category='CommServDB.Console',
                                             key_name='showAssertionSkewTimeControl',
                                             data_type='BOOLEAN',
                                             value='true')
        self.log.info('Setting added Successfully')

    @test_step
    def add_skew_time(self):
        """ Modifies the props in app_thirdpartyApp and adds the skew seconds """

        self.log.info("start adding skew time")

        _query = """UPDATE App_ThirdPartyApp
        SET props.modify('replace value of (/props/nameValues[@value eq "60"]/@value)[1] with "600"')
        WHERE props.exist('/props/nameValues[@name eq "SAMLResponseSkewTimeInSecs"]') = 1 and appName='{0}' and appType=2""".format(self.saml_obj.app_name)

        self.options_selector.update_commserve_db(_query)

        self.log.info("end adding skew time")

        _query2 = "select props from App_ThirdPartyApp where appname = '{0}' and " \
            "appType = 2".format(self.saml_obj.app_name)
        self.csdb.execute(_query2)
        props = self.csdb.fetch_one_row()[0]
        self.log.info(props)

    @test_step
    def restart_services(self):
        """Restart Client Services"""
        self.log.info('Restarting Client Services')
        self.client.restart_services()
        time.sleep(30)
        self.log.info('Services Restarted Successfully')

    def run(self):
        try:
            self.init_tc()
            self.add_saml_app()
            self.admin_console.logout()
            self.saml_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                  self.tcinputs['IDP admin username'],
                                                                  self.tcinputs['IDP admin password'],
                                                                  self.tcinputs['appname'],
                                                                  self.sso_url,
                                                                  self.sp_entity_id)
            self.saml_obj.logout_from_okta()
            self.change_system_time()
            status = self.saml_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                                 self.commcell.webconsole_hostname,
                                                                 self.OKTA_url,
                                                                 self.tcinputs['SAML user name'],
                                                                 self.tcinputs['SAML user pwd'],
                                                                 self.tcinputs['appname'],
                                                                 False
                                                                 )
            if not status:
                self.log.info("Due to the added skew in system time login fails")
            else:
                self.log.info("Even after adding skew time login succeeded")
                self.saml_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)

            self.saml_obj.single_logout(self.OKTA_url)

            self.add_additional_setting()
            self.add_skew_time()

            status = self.saml_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                                 self.commcell.webconsole_hostname,
                                                                 self.OKTA_url,
                                                                 self.tcinputs['SAML user name'],
                                                                 self.tcinputs['SAML user pwd'],
                                                                 self.tcinputs['appname'],
                                                                 False
                                                                 )

            if not status:
                raise CVTestStepFailure("Even after additional key, Login failed")
            else:
                self.saml_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
                self.saml_obj.single_logout(self.OKTA_url)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.saml_obj.delete_app()
            self.commcell.delete_additional_setting(category='CommServDB.Console',
                                                    key_name='showAssertionSkewTimeControl'
                                                    )
            self.restart_services()
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
