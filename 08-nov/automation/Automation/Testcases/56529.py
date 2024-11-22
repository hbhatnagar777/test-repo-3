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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from AutomationUtils.options_selector import OptionsSelector

# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG4'
        self.user_name1 =  "USER11" + SmartClientHelper.generate_random_username()
        self.user_name2 = "USER22" + SmartClientHelper.generate_random_username()
        self.user_email1 = SmartClientHelper.generate_random_email()
        self.user_email2 = SmartClientHelper.generate_random_email()
        self.user_password = UserHelper.password_generator(3, 12)
        self.usergroup_name = "GROUPHAS12"
        self.options_selector = None

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        # Create User needed for the testcase
        self.user_helper = UserHelper(self.commcell)
        self.usergroup_helper = UsergroupHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self.user_helper.create_user(user_name=self.user_name1,
                                     email=self.user_email1,
                                     password=self.user_password
                                     )
        self.user_helper.create_user(user_name=self.user_name2,
                                     email=self.user_email2,
                                     password=self.user_password
                                     )
        clients_list = self.options_selector.get_ready_clients(self.tcinputs['preview_client_list'])[0]
        self.clients_dict = {"assoc1": {"clientName": clients_list, "role": ["Client Admins"]}}
        self.usergroup_helper.create_usergroup(group_name=self.usergroup_name,
                                               users=[self.user_name1, self.user_name2],
                                               entity_dict=self.clients_dict)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning up testcase entities")
        self.user_helper.delete_user(user_name=self.user_name1,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name2,
                                     new_user="admin")
        self.usergroup_helper.delete_usergroup(group_name=self.usergroup_name,
                                               new_user="admin")
        self.log.info("Testcase Entities Cleaned")

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup testcase entities
            self.setup_entities()
            # Initialize client groups object
            self.log.info("Initializing Client Groups")
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG4',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value=self.usergroup_name)

            # Get a preview of the clients that will be a part of this group
            preview_clients_list = []
            try:
                preview_clients_list = smartclient_helper.preview_clients(value=smartclient_helper.value)
            except Exception as excp:
                self.log.error('Could not get preview client list via stored proc, will use preview client list from tcinput. Error: %s', str(excp))
                preview_clients_list = self.tcinputs['preview_client_list']
            rule_list = []
            self.log.info("""
                            ====================================================
                            Step1:
                            Creating Automatic Client Group with Client installed
                            ====================================================
                            """)
            self.log.info("Creating Rule for Client equal to Installed")
            rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')

            rule_list.append(rule1)

            self.log.info('Creating Client Group %s for testcase %s',smartclient_helper.group_name,self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)

            # Get Generated clients list
            created_clients_list = smartclient_helper.get_clients_list(smartclient_helper.group_name)
            # Validation of Preview clients and Created group clients
            smartclient_helper.validate_clients_list(preview_clients_list, created_clients_list)

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            if smartclient_helper is not None:
                smartclient_helper.smart_client_cleanup()
            self.cleanup_entities()
