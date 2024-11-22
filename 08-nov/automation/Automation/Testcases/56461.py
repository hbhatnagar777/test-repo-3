"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating default usergroup associations and
            user group attribute mappings in SAML app

Input Example:

    "testCases": {
            "56461": {
                        "ClientName": "venus",
                        "Usergroup": "Domain User",
                        "SMTP" : "test.indigo.com",
                        "IDP URL" : "company.com",
                        "IDP admin username" : "test@commvault.com",
                        "IDP admin password" : "pwd234",
                        "appname" : "AutomationApp",
                        "metadata path" : "C:\\AutomationApp.xml",
                        "SAML user name" : "user1@test.indigo.com",
                        "SAML user pwd" : "pwd1",
                        "SAML user2" : "user2@test.indigo.com",
                        "SAML pwd2" : "pwd2",
                        "SAML user3": "user3@test.indigo.com",
                        "SAML pwd3": "pwd3",
                        "SAML user4": "user4@test.indigo.com",
                        "SAML pwd4": "pwd4"
                        }
                }
"""

from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.UserDetails import UserDetails
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.UserGroupDetails import UserGroupDetails
from Web.AdminConsole.AdminConsolePages.UserGroups import UserGroups
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ Testcase to validate regressions of SAML login"""

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
        self.__navigator = None
        self.helper_obj = None
        self.__table = None
        self.tcinputs = {
            "Usergroup": None,
            "SMTP": None,
            "IDP URL": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "metadata path": None,
            "SAML user name": None,
            "SAML user pwd": None,
            "SAML user2": None,
            "SAML pwd2": None,
            "SAML user3": None,
            "SAML pwd3": None,
            "SAML user4": None,
            "SAML pwd4": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.helper_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
            self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
            self.__navigator = self.admin_console.navigator
            self.__table = Table(self.admin_console)
            self.user = UserDetails(self.admin_console)
            self.ugd_obj = UserGroupDetails(self.admin_console)
            self.company = Companies(self.admin_console)
            self.OKTA_url = "https://" + self.tcinputs['IDP URL']
            self.idp_mappings = {"usergroup": "Domain"}
            self.sp_mappings = {"usergroup": "user groups"}

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_usergroup(self, usergroup):
        """ Adding UserGroup """
        self.ug_obj = UserGroups(self.admin_console)
        self.__navigator.navigate_to_user_groups()
        self.ug_obj.add_user_group(usergroup)

    @test_step
    def add_saml_app(self):
        """ Adding SAML app """
        self.__navigator.navigate_to_identity_servers()
        self.helper_obj.app_name = "test" + str(datetime.today().microsecond)
        self.helper_obj.create_saml_app(self.tcinputs['metadata path'],
                                        self.tcinputs['SMTP'],
                                        self.webconsole_url,
                                        False,
                                        None
                                        )
        self.sso_url = self.helper_obj.get_sso_url()
        self.sp_entity_id = self.helper_obj.get_sp_entity_id()

    @test_step
    def edit_mappings_and_redirect_rule(self):
        """ Editing Attribute Mappings and Redirect rule """
        self.helper_obj.edit_saml_rule_or_mappings(self.tcinputs['appname'], mappings=self.sp_mappings)
        modified_redirect_rule = {"": self.tcinputs['SMTP']}
        self.helper_obj.edit_saml_rule_or_mappings(self.helper_obj.app_name,
                                                   redirect_rule=modified_redirect_rule)

    @test_step
    def verify_user_properties(self, username, usergroup):
        """ Verifies User properties """
        self.__navigator.navigate_to_users()
        self.__table.access_link(username)
        user_details = self.user.get_user_details()
        group = user_details['Group']
        if group == usergroup:
            return True
        else:
            return False

    @test_step
    def saml_logout(self):
        """ SAML logout """
        self.helper_obj.initiate_saml_logout_with_okta(self.commcell.webconsole_hostname)
        self.helper_obj.single_logout(self.OKTA_url)

    @test_step
    def add_company(self):
        """ Adds Company """
        self.__navigator.navigate_to_companies()
        self.company_name = "Company" + "_" + str(datetime.today().microsecond)
        self.company.add_company(self.company_name,
                                 "aaa@commvault.com",
                                 self.company_name,
                                 [],
                                 self.company_name,
                                 "commvault.com", "", "")

    @test_step
    def add_default_usergroup(self, usergroup, add=False, edit=False):
        """ Adding default usergroup to SAML app """
        self.__navigator.navigate_to_identity_servers()
        self.helper_obj.open_saml_app(self.helper_obj.app_name)
        if add:
            self.helper_obj.modify_saml_general_settings(self.helper_obj.app_name,
                                                         add_default_usergroup=True,
                                                         user_group=usergroup)
        if edit:
            self.helper_obj.modify_saml_general_settings(self.helper_obj.app_name,
                                                         modify_user_group=True,
                                                         user_group=usergroup)

    def run(self):
        try:
            self.init_tc()
            self.add_usergroup(self.tcinputs['Usergroup'])
            self.add_saml_app()
            self.edit_mappings_and_redirect_rule()
            self.admin_console.logout()
            self.helper_obj.login_to_okta_and_edit_general_settings(self.OKTA_url,
                                                                    self.tcinputs['IDP admin username'],
                                                                    self.tcinputs['IDP admin password'],
                                                                    self.tcinputs['appname'],
                                                                    self.sso_url,
                                                                    self.sp_entity_id,
                                                                    group_attribute=self.idp_mappings)
            self.helper_obj.logout_from_okta()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user name'],
                                                          self.tcinputs['SAML user pwd'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.saml_logout()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            status = self.verify_user_properties(self.tcinputs['SAML user name'], self.tcinputs['Usergroup'])
            if status is False:
                raise CVTestStepFailure("User not associated to usergroup")

            self.add_company()
            self.add_usergroup(self.company_name + "\\" + self.tcinputs['Usergroup'])
            self.admin_console.logout()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user2'],
                                                          self.tcinputs['SAML pwd2'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.saml_logout()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            status = self.verify_user_properties(self.tcinputs['SAML user2'], self.tcinputs['Usergroup'])
            if status is False:
                raise CVTestStepFailure("User not associated to usergroup")

            self.add_default_usergroup(self.company_name + "\\" + self.tcinputs['Usergroup'], add=True)
            self.helper_obj.delete_mapping(self.sp_mappings)
            self.admin_console.logout()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user3'],
                                                          self.tcinputs['SAML pwd3'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.saml_logout()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            status = self.verify_user_properties(
                self.tcinputs['SAML user3'],
                self.company_name + "\\" + self.tcinputs['Usergroup'])
            if status is True:
                raise CVTestStepFailure("commcell user shouldn't be associated to company usergroup")

            self.add_default_usergroup('master', edit=True)
            self.admin_console.logout()

            self.helper_obj.initiate_saml_login_with_okta(self.webconsole_url,
                                                          self.commcell.webconsole_hostname,
                                                          self.OKTA_url,
                                                          self.tcinputs['SAML user4'],
                                                          self.tcinputs['SAML pwd4'],
                                                          self.tcinputs['appname'],
                                                          False)
            self.saml_logout()

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            status = self.verify_user_properties(self.tcinputs['SAML user4'], 'master')
            if status is False:
                raise CVTestStepFailure("User not associated to usergroup")

            self.admin_console.logout()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.helper_obj.delete_app()

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
