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
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.Security.securityhelper import OrganizationHelper

# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG11'
        self.user_helper = None
        self.usergroup_helper = None
        self.options_selector = None
        self.user_name1 = "testuser11" + SmartClientHelper.generate_random_username()
        self.user_email1 = SmartClientHelper.generate_random_email()
        self.user_password1 = UserHelper.password_generator(3, 12)
        self.user_name2 = "LOCALUSER22" + SmartClientHelper.generate_random_username()
        self.user_email2 = SmartClientHelper.generate_random_email()
        self.user_password2 = UserHelper.password_generator(3, 12)
        self.usergroup_name = "GROUP_USER_11"
        self.company_name = "companynew005"
        self.company_email = SmartClientHelper.generate_random_email()
        self.company_contact = "contact005"
        self.company_alias = "NEW_COMP_TESTING"

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        # Creating Users
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        self.user_helper = UserHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.usergroup_helper = UsergroupHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        # Getting n ready clients to associate with users 1 and 2
        self.user_clients1 = {"assoc1":{"clientName":[self.commcell.commserv_name], "role":["View"]},
                             "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Client Group Owner"]}}
        self.user_helper.create_user(user_name=self.user_name1,
                                     email=self.user_email1,
                                     password=self.user_password1,
                                     security_dict=self.user_clients1)
        # Creating clients list for user2
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.user_clients2 = {"assoc1":{"clientName":clients_list, "role":["Client Admins"]},
                              "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Client Group Owner"]}}
        self.user_helper.create_user(user_name=self.user_name2,
                                     email=self.user_email2,
                                     password=self.user_password2,
                                     security_dict=self.user_clients2)
        # Creating a User Group and adding User1 as part of it
        # Creating clients list for usergroup
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.usergroup_clients = {"assoc1":{"clientName":clients_list, "role":["Client Admins"]}}
        self.usergroup_helper.create_usergroup(group_name=self.usergroup_name,
                                               users=[self.user_name1],
                                               entity_dict=self.usergroup_clients)
        # Creating Organization needed for testcase
        self.organization_helper.create(name=self.company_name,
                                        email=self.company_email,
                                        contact_name=self.company_contact,
                                        company_alias=self.company_alias)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.user_helper.delete_user(user_name=self.user_name1,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name2,
                                     new_user="admin")
        self.usergroup_helper.delete_usergroup(group_name=self.usergroup_name,
                                               new_user="admin")
        self.commcell.organizations.delete(self.company_name)
        self.log.info("Testcase Entities Cleaned")

    def login_user(self, webconsole_hostname, username, password):
        """Returns Commcell Object for given user"""
        return Commcell(webconsole_hostname, username, password, verify_ssl=False)

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup Testcase entities
            self.setup_entities()
            # Initialize client groups object
            self.log.info("Initializing Client Groups")
            # Login as Created user
            user_commcell = self.login_user(self.commcell.webconsole_hostname,
                                            self.user_name1,
                                            self.user_password1)
            rule_list = []
            self.log.info("""
                          ==========================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients in this Commcell"
                          ==========================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG11',
                                                   description='Test Group',
                                                   client_scope='Clients in this Commcell')

            self.log.info("Creating Rule for Client equal to Installed")
            rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')

            rule_list.append(rule1)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            try:
                smartclient_helper.create_smart_client(smart_rule_list=rule_list)
                smartclient_helper.smart_client_cleanup()
            except Exception as client_creation_excp:
                self.log.error(f'Failed to create client group {smartclient_helper.group_name} '
                               f'with scope {smartclient_helper.client_scope}')

            self.log.info("""
                          ======================================================================================
                          Step2:
                          Creating Automatic Client Group with Client installed with Scope "Clients of Companies"
                          ======================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG11',
                                                   description='Test Group',
                                                   client_scope='Clients of Companies',
                                                   value=self.company_alias)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            try:
                smartclient_helper.create_smart_client(smart_rule_list=rule_list)
                smartclient_helper.smart_client_cleanup()
            except Exception as client_creation_excp:
                self.log.error(
                    f'Failed to create client group {smartclient_helper.group_name} '
                    f'with scope {smartclient_helper.client_scope}')

            self.log.info("""
                          ==================================================================================
                          Step3:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User"
                          ==================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG11',
                                                   description='Test Group',
                                                   client_scope='Clients of User',
                                                   value=self.user_name2)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)
            smartclient_helper.smart_client_cleanup()

            self.log.info("""
                          ========================================================================================
                          Step4:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User Group"
                          ========================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG11',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value=self.usergroup_name)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)
            smartclient_helper.smart_client_cleanup()

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.cleanup_entities()
