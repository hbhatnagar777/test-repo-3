# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks for login to webconsole adminconsole java interface

Steps in this test case:
    Create a test user

    Assign View ALL permissions to that user

    Login to WebConsole or AdminConsole using the test user.

    Delete the test user.

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.Security.userhelper import UserHelper, UserProperties
from Server.serverhelper import ServerTestCases
from Server.Security.userconstants import USERGROUP, WebConstants


class TestCase(CVTestCase):
    """Class for executing Sanity Check test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Sanity Checks for login to commcell interfaces (WC, AC, UI)"
        self.commcell_obj = None
        self._server_tc = None
        self._user_helper = None
        self.log = None
        self._user_list = None
        self.show_to_user = True
        self.result_string = "Successful"
        self.tcinputs = {
            "email": None,
            "AD-User": None,
            "AD-Password": None,
            "Domain": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commcell_obj = self._commcell
        self._server_tc = ServerTestCases(self)
        self._user_helper = UserHelper(self.commcell_obj)
        user1 = UserProperties(name='Test_53600', cs_host=self.commcell_obj.commserv_hostname,
                               email=self.tcinputs["email"], password='######',
                               full_name='Test User')
        user2 = UserProperties(name=self.tcinputs["AD-User"],
                               cs_host=self.commcell_obj.commserv_hostname,
                               email=self.tcinputs["email"], password=self.tcinputs["AD-Password"],
                               domain=self.tcinputs["Domain"])
        self._user_list = [user1, user2]

    def run(self):
        """Main function for test case execution"""

        self._server_tc.log_step(
            """
            Test Case
            1) Creates User and adds him to local group
            2) Login to Admin Console and Web Console
            3) Login to Java GUI
            4) Enable Two Factor Authentication
            5) TFA Login to Admin Console and Web Console
            6) TFA Login to Java GUI
            """, 200
        )

        for user in self._user_list:
            if user.domain:
                domain_user = "{0}\\{1}".format(user.domain, user.username)
                user.username = domain_user
            # delete user if already exists
            self._user_helper.delete_user(user.username, new_user='admin')
            #create new user with same name
            self._server_tc.log_step("""step 1: Creates User and adds him to local group""")
            self._user_helper.create_user(user_name=user.username,
                                          full_name=user.full_name,
                                          email=user.email,
                                          password=user.password,
                                          local_usergroups=[USERGROUP.MASTER])
            self.log.info("Performing login operations for user: %s", user.username)
            try:
                #Constants to be used in this test case
                web = WebConstants(self.commcell._headers['Host'])
                self._server_tc.log_step("""step 2: Login to Admin Console and Web Console""")
                self._user_helper.web_login(user_name=user.username, password=user.password,
                                            web=web)
                self._server_tc.log_step("""step 3: Login to Java GUI""")
                self._user_helper.gui_login(cs_host=user.cs_host, user_name=user.username,
                                            password=user.password)
                self._server_tc.log_step("""step 4: Enable Two Factor Authentication""")
                self._user_helper.enable_tfa()
                self._server_tc.log_step("""step 5: TFA Login to Admin Console and Web Console""")
                self._user_helper.web_login(user_name=user.username, password=user.password,
                                            web=web)
                self._server_tc.log_step("""step 6: TFA Login to Java GUI""")
                self._user_helper.gui_login(cs_host=user.cs_host, user_name=user.username,
                                            password=user.password)
                self.log.info("**********Test-case Execution completed successfully**********")

            except Exception as exp:
                self._log.error('Failed to execute test case with error: ' + str(exp))
                self._server_tc.log_step("""Test Case FAILED""", 200)
                self.result_string = str(exp)
                self.status = constants.FAILED
            finally:
                self._server_tc.log_step("""clean up phase""")
                self._user_helper.disable_tfa()
                self._user_helper.delete_user(user.username, new_user='admin')
