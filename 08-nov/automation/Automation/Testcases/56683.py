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

from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.organizationhelper import OrganizationHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from cvpysdk.commcell import Commcell
# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG30'
        self.user_helper = None
        self.usergroup_helper = None
        self.options_selector = None
        self.organization_helper = None
        self.company_name = "COMPANY_56683"
        self.company_contact = "NewCompanyContact56683"
        self.company_alias = "COMPANY_56683"
        self.user_name1 = "USER11"
        self.user_name2 = "USER22"
        self.user_password = UserHelper.password_generator(3, 12)
        self.usergroup_name = "GROUPHAS12"

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        # Create User needed for the testcase
        self.user_helper = UserHelper(self.commcell)
        self.usergroup_helper = UsergroupHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.user_helper.create_user(user_name=self.user_name1,
                                     email=SmartClientHelper.generate_random_email(),
                                     password=self.user_password
                                     )
        self.user_helper.create_user(user_name=self.user_name2,
                                     email=SmartClientHelper.generate_random_email(),
                                     password=self.user_password
                                     )
        # Generating n ready clients for Created usergroup
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.usergroup_clients = {"assoc1":{"clientName":clients_list, "role":["Client Admins"]}}
        self.usergroup_helper.create_usergroup(group_name=self.usergroup_name,
                                               users=[self.user_name1, self.user_name2],
                                               entity_dict=self.usergroup_clients)
        # Creating Company
        self.organization_helper.create(name=self.company_name,
                                        email=SmartClientHelper.generate_random_email(),
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

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup entities
            self.setup_entities()
            # Initialize client groups object
            # Create a Client Group Logged in as Commcell Admin
            self.log.info("Initializing Client Groups")
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG30',
                                                   description='Test Group',
                                                   client_scope='Clients in this Commcell')
            self.log.info("""
                          =========================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients in this Commcell
                          ==========================================================================================
                          """)
            self.log.info("Creating Rule for Client equal to Installed")
            rule_list = []
            rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')
            rule_list.append(rule1)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)

            # Now Try to Update Scopes as Commcell Admin
            # Try and Update scope to "Clients of Companies" as logged in Commcell Admin -> Should be allowed
            smartclient_helper.update_scope(clientgroup_name=smartclient_helper.group_name,
                                            client_scope="Clients of Companies",
                                            value=self.company_alias)
            # Try and Update scope to "Clients of User" as logged in Commcell Admin -> Should be allowed
            smartclient_helper.update_scope(clientgroup_name=smartclient_helper.group_name,
                                            client_scope="Clients of User",
                                            value=self.user_name1)
            # Try and Update scope to "Clients of User Group" as logged in Commcell Admin -> Should be allowed
            smartclient_helper.update_scope(clientgroup_name=smartclient_helper.group_name,
                                            client_scope="Clients of User Group",
                                            value=self.usergroup_name)


        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            if smartclient_helper is not None:
                smartclient_helper.smart_client_cleanup()
            self.cleanup_entities()
