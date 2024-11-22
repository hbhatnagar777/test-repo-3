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
from Server.Security.securityhelper import SecurityHelper
from AutomationUtils import logger


class TestCase(CVTestCase):
    """Class for executing SAAS Sanity Check test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Security - User and UserGroup Operations"
        self.product = self.products_list.USERDEFINED
        self.feature = self.features_list.USERDEFINED
        self.commcell_obj = None
        self._user_helper = None
        self._usergroup_helper = None
        self._security_helper = None
        self._server_tc = None
        self.log = None
        self._user_list = None
        self._group_list = None
        self.show_to_user = True
        self.result_string = "Successful"
        self.tcinputs = {
            "AD-User": None,
            "AD-User-Password": None,
            "Domain": None,
            "AD-UserGroup": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commcell_obj = self._commcell
        self._user_helper = UserHelper(self.commcell_obj)
        self._usergroup_helper = UsergroupHelper(self.commcell_obj)
        self._security_helper = SecurityHelper(self.commcell_obj)
        self._server_tc = ServerTestCases(self)
        self.log = logger.get_log()
        password = self._user_helper.password_generator()
        user1 = UserProperties(name='TestUser_48755', cs_host=self.commcell_obj.commserv_hostname,
                               password=password, full_name='Test User created by automation')
        user2 = UserProperties(name=self.tcinputs["AD-User"],
                               cs_host=self.commcell_obj.commserv_hostname,
                               password=self.tcinputs["AD-User-Password"],
                               full_name='Test Usercreated by automation',
                               domain=self.tcinputs["Domain"])
        self._user_list = [user1, user2]
        self._group_list = ["{0}\\{1}".format(self.tcinputs["Domain"],
                                              self.tcinputs["AD-UserGroup"]), "TestGroup_48755"]

    def run(self):
        """Main function for test case execution"""

        self._server_tc.log_step(
            """
            Test Case
            1) Creates User with random entities and role
            2) Validating Security Associations
            3) Modify Security Associations on User
            4) Validating Modified Security Associations
            5) Delete the User and Verify
            6) Repeating Above steps for User Group
            """, 200
        )
        self.log.info("This Test case is used to perform various Operations such as Creation,"
                      "Modification and deletion of User and Usergroups")
        try:
            for user in self._user_list:
                if user.domain:
                    domain_user = "{0}\\{1}".format(user.domain, user.username)
                    user.username = domain_user
                # delete user if already exists
                self._user_helper.delete_user(user.username, new_user='admin')
                self._server_tc.log_step("""Step 1: Creates User with random entities and role""")
                dictionary = self._security_helper.gen_random_entity_types_dict(
                    no_of_entity_types=2, no_of_assoc=2, commcell=True)
                self._user_helper.create_user(user_name=user.username,
                                              password=user.password, email='test48755@test.com',
                                              security_dict=dictionary)
                self._server_tc.log_step("""Step 2: Validating Security Associations""")
                self._security_helper.validate_security_associations(
                    entity_dict=dictionary, name=user.username, isuser=1)
                self._server_tc.log_step("""Step 3: Modify Security Associations on User""")
                new_dict = self._security_helper.gen_random_entity_types_dict(no_of_entity_types=1, commcell=True)
                self._user_helper.modify_security_associations(entity_dict=new_dict,
                                                               user_name=user.username,
                                                               request='UPDATE')
                self._server_tc.log_step("""Step 4: Validating Modified Security Associations""")
                self._security_helper.validate_security_associations(entity_dict=new_dict,
                                                                     name=user.username,
                                                                     isuser=1)
                self._server_tc.log_step("""Step 5: Delete the User and Verify""")
                self._user_helper.delete_user(user_name=user.username, new_user='admin')

            self._server_tc.log_step("""Step 6: Repeating Above steps for User Group""")

            for usergroup in self._group_list:
                self._usergroup_helper.delete_usergroup(usergroup, 'admin')

                dictionary = self._security_helper.gen_random_entity_types_dict(
                    no_of_entity_types=2, no_of_assoc=2, commcell=True)
                self._usergroup_helper.create_usergroup(group_name=usergroup,
                                                        entity_dict=dictionary)
                self._security_helper.validate_security_associations(entity_dict=dictionary,
                                                                     name=usergroup,
                                                                     isuser=0)
                new_dict = self._security_helper.gen_random_entity_types_dict(no_of_entity_types=1,
                                                                              no_of_assoc=1, commcell=True)
                self._usergroup_helper.modify_security_associations(entity_dict=new_dict,
                                                                    group_name=usergroup,
                                                                    request='UPDATE')
                self._security_helper.validate_security_associations(entity_dict=new_dict,
                                                                     name=usergroup, isuser=0)

                self._usergroup_helper.delete_usergroup(usergroup, 'admin')
            self.log.info("Successful")

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self._server_tc.log_step("""Test Case FAILED""", 200)
            self.result_string = str(exp)
            self.status = constants.FAILED
