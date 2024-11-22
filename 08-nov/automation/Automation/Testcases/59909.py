"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating :
                    Creating OpenID app in commcell and in IDP
                    DO Sp init openID login
                    Delete the openID app

Input Example:

    "testCases": {
            "59909":{
                    "ClientName": "stormbreaker",
                    "OKTA url" : "https://test.okta.com",
                    "OKTA admin": "test@okta.com",
                    "pwd": "123456",
                    "appname": "openid_automation",
                    "oidc user": "user1",
                    "user pwd": "qwerty"
            }
"""
from cvpysdk.identity_management import IdentityManagementApps

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing SAML login with Azure as IDP when only username mappings set"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "OpenID login"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.webconsole_url = None
        self.navigator_obj = None
        self.saml_obj = None
        self.client_id = None
        self.secret = None
        self.domain = None
        self.app_key = None
        self.props  = None
        self.tcinputs = {
            "OKTA url" : None,
            "OKTA admin": None,
            "pwd": None,
            "appname": None,
            "oidc user": None,
            "user pwd": None
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
            self.user = Users(self.admin_console)
            self.identity_mngmt = IdentityManagementApps(self.commcell)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_local_user(self):
        """
        Adding a local user in commcell
        """
        self.navigator_obj.navigate_to_users()
        self.user.add_local_user(self.tcinputs['oidc user'],
                                 username=self.tcinputs['oidc user'].split('@')[0],
                                 name=self.tcinputs['oidc user'].split('@')[0],
                                 system_password=False,
                                 password="Qwerty1$")
        self.admin_console.wait_for_completion()
        self.navigator_obj.navigate_to_identity_servers()
        self.admin_console.logout()

    @test_step
    def oidc_login(self):
        """Do OpenID user login"""
        status = self.saml_obj.oidc_login(self.webconsole_url,
                                          self.commcell.webconsole_hostname,
                                          self.tcinputs['OKTA url'],
                                          self.tcinputs['oidc user'],
                                          self.tcinputs['user pwd']
                                          )
        if not status:
            raise CVTestStepFailure("OpenID login failed")

    @test_step
    def get_app_key(self):
        """ Get the openID app key from the DB"""
        _query = "select appKey from App_ThirdPartyApp where appName = '{0}' and " \
                 "appType = 5".format(self.tcinputs['appname'])
        self.csdb.execute(_query)
        app_key = self.csdb.fetch_one_row()
        app_key = ''.join(app_key)
        self.log.info(app_key)
        return app_key

    def run(self):
        try:
            self.init_tc()
            self.add_local_user()

            self.saml_obj.login_to_okta(self.tcinputs['OKTA url'], self.tcinputs['OKTA admin'], self.tcinputs['pwd'])

            self.log.info("Editing the OpenID app in OKTA")
            self.client_id, self.secret, self.domain = self.saml_obj.edit_oidc_app_in_okta(
                self.tcinputs['appname'],
                self.webconsole_url + "/openIdConnectCallback.do"
            )

            self.saml_obj.logout_from_okta()

            self.props = [
                {
                    "name": "clientId",
                    "value": self.client_id
                },
                {
                    "name": "clientSecret",
                    "value": self.secret
                },
                {
                    "name": "endPointUrl",
                    "value": "https://" + self.domain + "/.well-known/openid-configuration"
                },
                {
                    "name": "webConsoleUrls",
                    "values": [
                        self.webconsole_url
                    ]
                }
            ]
            user_to_be_associated = self.tcinputs['oidc user'].split('@')[0]
            self.log.info("Adding the OpenID app in commcell")
            self.identity_mngmt.configure_openid_app(self.tcinputs['appname'],
                                                     self.props,
                                                     [user_to_be_associated])

            self.oidc_login()
            self.saml_obj.oidc_logout(self.commcell.webconsole_hostname)
            self.admin_console.wait_for_completion()

            self.log.info("Delete the OpenID app in commcell")
            self.identity_mngmt.refresh()
            self.identity_mngmt.delete_identity_app((self.tcinputs['appname']).lower())

            app_key = self.get_app_key()
            if app_key == "":
                self.log.info("App is deleted successfully")
            else:
                raise CVTestStepFailure("OpenID app deletion failed")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Deleting the oidc user ")
            self.navigator_obj.navigate_to_users()
            self.user.delete_user(user_name=self.tcinputs['oidc user'].split('@')[0])

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
