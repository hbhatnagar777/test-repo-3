# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from cvpysdk.commcell import Commcell
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG28'
        self.user_helper = None
        self.usergroup_helper = None
        self.options_selector = None
        self.test_email = "TestAutomation3@commvault.com"
        self.test_password = UserHelper.password_generator(3, 12)
        self.user_name1 = SmartClientHelper.generate_random_username()
        self.user_name2 = SmartClientHelper.generate_random_username()
        self.usergroup_name1 = "GROUP_12"
        self.user_name3 = SmartClientHelper.generate_random_username()
        self.user_name4 = SmartClientHelper.generate_random_username()
        self.usergroup_name2 = "GROUP_34"

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        # Creating Users, User1 and User2
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")

        self.user_helper = UserHelper(self.commcell)
        self.usergroup_helper = UsergroupHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        # Generating n ready clients for Created Users user11,user22,user33,user44
        users_clients_list = {"assoc1": {"commCellName":  [self.commcell.commserv_name], "role":  ["Client Group Owner"]}}
        self.user_helper.create_user(user_name=self.user_name1,
                                     email=SmartClientHelper.generate_random_email(),
                                     password=self.test_password,
                                     security_dict=users_clients_list)
        self.user_helper.create_user(user_name=self.user_name2,
                                     email=SmartClientHelper.generate_random_email(),
                                     password=self.test_password,
                                     security_dict=users_clients_list)
        # Creating a User Group and adding User1, User2 as part of it
        # Generating n ready clients for Created usergroup12
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.usergroup_clients = {"assoc1": {"clientName": clients_list, "role": ["Client Admins"]},
                                  "assoc2": {"commCellName":  [self.commcell.commserv_name], "role": ["Client Group Owner"]}}
        self.usergroup_helper.create_usergroup(group_name=self.usergroup_name1,
                                               users=[self.user_name1, self.user_name2],
                                               entity_dict=self.usergroup_clients)

        # Creating Users, User3 and User4
        self.user_helper.create_user(user_name=self.user_name3,
                                     email=SmartClientHelper.generate_random_email(),
                                     password=self.test_password,
                                     security_dict=users_clients_list)
        self.user_helper.create_user(user_name=self.user_name4,
                                     email=SmartClientHelper.generate_random_email(),
                                     password=self.test_password,
                                     security_dict=users_clients_list)
        # Creating a User Group and adding User3, User4 as part of it
        # Generating n ready clients for Created usergroup34
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.usergroup_clients = {"assoc1": {"clientName": clients_list, "role": ["Client Admins"]},
                                  "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Client Group Owner"]}}
        self.usergroup_helper.create_usergroup(group_name=self.usergroup_name2,
                                               users=[self.user_name3, self.user_name4],
                                               entity_dict=self.usergroup_clients)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.user_helper.delete_user(user_name=self.user_name1,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name2,
                                     new_user="admin")
        self.usergroup_helper.delete_usergroup(group_name=self.usergroup_name1,
                                               new_user="admin")

        self.user_helper.delete_user(user_name=self.user_name3,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name4,
                                     new_user="admin")
        self.usergroup_helper.delete_usergroup(group_name=self.usergroup_name2,
                                               new_user="admin")
        self.log.info("Testcase Entities Cleaned")

    def login_user(self, hostname, username, password):
        """Used to return Commcell object for another user with credentials provided in tcinputs"""
        commcell = Commcell(hostname, username, password, verify_ssl=False)
        return commcell

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup Testcase Entities
            self.setup_entities()
            # Login as Created User1
            self.log.info("Logging in as {0}".format(self.user_name1))
            user1 = self.login_user(self.commcell.webconsole_hostname,
                                    self.user_name1,
                                    self.test_password)
            self.log.info("Logged in as {0}".format(self.user_name1))
            # Initialize client groups object
            # Create a Client Group Logged in as Commcell Admin
            self.log.info("Initializing Client Groups")
            smartclient_helper = SmartClientHelper(commcell_object=user1,
                                                   group_name='SCG28',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value=self.usergroup_name1)
            self.log.info("""
                          =======================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User Group
                          ========================================================================================
                          """)
            self.log.info("Creating Rule for Client equal to Installed")
            rule_list = []
            rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')
            rule_list.append(rule1)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)

            # Now Try to Update Scope as User3
            self.log.info('Logging in User3')
            user3 = self.login_user(hostname=self.commcell.webconsole_hostname,
                                    username=self.user_name3,
                                    password=self.test_password)
            self.log.info('Logged in as User3')

            smartclient_helper_user3 = SmartClientHelper(user3)
            # Try and Update scope to "Clients of User Group : User34" as User3 -> Should be allowed
            smartclient_helper_user3.update_scope(clientgroup_name=smartclient_helper.group_name,
                                                  client_scope="Clients of User Group",
                                                  value=self.usergroup_name2)
            # Try and Update scope to "Clients of User Group : User12" as User3 -> Should not be allowed
            try:
                smartclient_helper_user3.update_scope(clientgroup_name=smartclient_helper.group_name,
                                                      client_scope="Clients of User Group",
                                                      value=self.usergroup_name1)
            except Exception as modification_excp:
                self.log.error('Could not modify scope')
                self.log.error(f'Encountered Exception {modification_excp}')


        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            if smartclient_helper:
                smartclient_helper.smart_client_cleanup()
            self.cleanup_entities()
