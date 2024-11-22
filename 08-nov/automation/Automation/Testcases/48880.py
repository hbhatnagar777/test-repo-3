# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.serverhelper import ServerTestCases
from Server.Security.userhelper import UserHelper, UserProperties
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.securityhelper import SecurityHelper, RoleHelper
from Server.Security.securityoperationshelper import SecurityOperationsHelper
from AutomationUtils import config


class TestCase(CVTestCase):
    """Class for executing Sanity Check test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Security - Media Agent Operations User"
        self.product = self.products_list.USERDEFINED
        self.feature = self.features_list.USERDEFINED
        self._user_helper = None
        self._role_helper = None
        self._usergroup_helper = None
        self._security_helper = None
        self._operations_helper = None
        self._server_tc = None
        self.count = 0
        self.result_string = "Successful"
        self.password = None
        self.log = None
        self._user_list = None
        self._role1 = 'Automation_role1_48880'
        self._role2 = 'Automation_role2_48880'
        self._permission_list1 = ['MediaAgent Management']
        self._permission_list2 = ['Create Storage Policy']
        self.show_to_user = True
        self._security_dict = None
        self.config_json = None
        self._email = None

    def setup(self):
        """Setup function of this test case"""
        self._user_helper = UserHelper(self.commcell)
        self._usergroup_helper = UsergroupHelper(self.commcell)
        self._role_helper = RoleHelper(self.commcell)
        self._security_helper = SecurityHelper(self.commcell)
        self._server_tc = ServerTestCases(self)
        self.config_json = config.get_config()
        self._email = self.config_json.Security.email_id
        self.password = self._user_helper.password_generator()
        user1 = UserProperties(name='TestUser_48880', cs_host=self.commcell.commserv_hostname,
                               password=self.password, full_name='Test User created by automation')
        self._user_list = [user1]
        self._security_dict = {
            'asso1': {
                'mediaAgentName': [self.client if self.tcinputs.get('ClientName') else
                                   self.commcell.commserv_name],
                'role': [self._role1]
            },
            'asso2': {
                'commCellName': [self.commcell.commserv_name],
                'role': [self._role2]
            }
        }

    def run(self):
        """Main function for test case execution"""

        self._server_tc.log_step(
            """
            Test Case
            1) Creates User with provided security associations
            2) Analysing security associations and fetching valid and invalid operations for user
            3) Perform all valid and invalid operations
            4) Analyse all the operations output and compare with intended results
            5) Generating report on success and failure of operations
            """, 200
        )
        self.log.info("This test verifies that a Media Agent Operations user can perform only "
                      "Operations such as creating library/storage Policy "
                      "(implemented as initial operation) on the MA")
        try:
            self._server_tc.log_step("""step 1: Creates User with provided security associations""")
            for user in self._user_list:
                self._user_helper.delete_user(user.username, new_user='admin')
                self._role_helper.delete_role(self._role1)
                self._role_helper.delete_role(self._role2)
                self._role_helper.create_role(role_name=self._role1,
                                              permission_list=self._permission_list1)
                self._role_helper.create_role(role_name=self._role2,
                                              permission_list=self._permission_list2)
                self._user_helper.create_user(user_name=user.username,
                                              password=user.password, email='test48880@test.com',
                                              security_dict=self._security_dict)
                self._operations_helper = SecurityOperationsHelper(self.commcell,
                                                                   user.username, self.password)
                self.commcell.refresh()
                self._server_tc.log_step(
                    """step 2: Analysing security associations and fetching valid and invalid
                     operations for user""")
                operations = self._operations_helper.fetch_operations_for_user(username=user.username)
                self._server_tc.log_step(
                    """step 3: Perform all valid and invalid operations""")
                result_dict = self._operations_helper.perform_operations(
                    operation_dictionary=operations)
                self._server_tc.log_step(
                    """step 4: Analyse all the operations output and compare with intended results
                    """)
                final_result, self.count = self._operations_helper.operation_validator(
                    intended_result=operations, actual_result=result_dict)
                self._server_tc.log_step(
                    """step 5:Generating report on success and failure of operations""")
                self._operations_helper.operations_result_generator(operations_list=final_result,
                                                                    reciever=[self._email])
            if self.count:
                self.log.info("TestCase execution FAILED!!!")
                raise Exception("{0} operations failed to perform by user,"
                                "check valid operations report sent to recipient:{1}".
                                format(self.count, self._email))
            else:
                self.log.info("All operations are successfully performed by user")

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self._server_tc.log_step("""Test Case FAILED""", 200)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self._operations_helper.clear_cache_tables()
            for user in self._user_list:
                self._user_helper.delete_user(user.username, new_user='admin')
            self._role_helper.delete_role(self._role1)
            self._role_helper.delete_role(self._role2)
