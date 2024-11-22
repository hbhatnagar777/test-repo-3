# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import datetime
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.commcell import Commcell
from cvpysdk.security.user import Users
from Server.Security.access_token_validator import AccessTokenValidator
from Server.Security.userhelper import UserHelper
from AutomationUtils import config

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.new_commcell_obj = None
        self.password = None
        self.username = None
        self.validator = None
        self.admin_console = None
        self.browser = None
        self.__user_obj = None
        self.name = """[Access Tokens] : [Validate access token scope]"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SECURITYANDROLES
        self.show_to_user = True
        self.config_json = config.get_config()
        self.tcinputs = {}
        self.server = ServerTestCases(self)

    def _create_user(self,
                     username=None,
                     password=None):
        """creates a user in master group to create access token
                Args:
                    username       <str>  --   Name of the user to be created
                    password       <str>  --   Password of the user to be created
                Returns:
                    username       <str>  --   Name of the user created
                    password       <str>  --   Password of the user created
        """
        if username is None:
            username = "user_" + ('{date:%d-%m-%Y_%H_%M_%S}'.
                                  format(date=datetime.datetime.now()))
        if password is None:
            password = UserHelper(self.commcell).password_generator()

        self.__user_obj.add(user_name=username, email=username + "@gmail.com",
                            password=password, local_usergroups=['master'])

        return username, password

    def _delete_user(self, name):
        """
            Args:
                username       <str>  --   Name of the user to be deleted
            Returns:
                None
        """
        self.log.info("Deleting user %s" % name)
        self.__user_obj.delete(user_name=name, new_user="admin")


    def setup(self):
        """Setup function of this test case"""
        self.__user_obj = Users(self.commcell)
        self.username, self.password = self._create_user()
        self.new_commcell_obj = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                         commcell_username=self.username, commcell_password=self.password,
                                         verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.username, password=self.password)
        self.validator = AccessTokenValidator(self.new_commcell_obj, self.admin_console, self.username)

    def run(self):
        """Run function of this test case"""
        try:
            self.validator.validate_scope()
        except Exception as exp:
            handle_testcase_exception(self, exp)


    def tear_down(self):
        """Tear down function of this test case"""
        self._delete_user(self.username)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)


