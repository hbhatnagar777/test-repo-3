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
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.organizationhelper import OrganizationHelper
# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG27'
        self.user_name = "LOCALUSER22" + SmartClientHelper.generate_random_username()
        self.test_email = None
        self.user_password = None
        self.company_name = "TEST_COMPANY_56567"
        self.company_contact = "contactnew005"
        self.company_alias = "TEST_COMPANY_56567"
        self.options_selector = None

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")

        self.test_email = SmartClientHelper.generate_random_email()
        self.user_password = UserHelper.password_generator(3, 12)

        self.user_helper = UserHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        # Generating n ready clients for Created user
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.user_clients = {"assoc1":{"clientName":clients_list, "role":["Client Admins"]},
                             "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Client Group Owner"]}}
        self.user_helper.create_user(user_name=self.user_name,
                                     email=self.test_email,
                                     password=self.user_password,
                                     security_dict=self.user_clients)
        # Creating Organization needed for testcase
        self.organization_helper.create(name=self.company_name,
                                        email=SmartClientHelper.generate_random_email(),
                                        contact_name=self.company_contact,
                                        company_alias=self.company_alias)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.user_helper.delete_user(user_name=self.user_name,
                                     new_user="admin")
        self.commcell.organizations.delete(self.company_name)
        self.log.info("Testcase Entities Cleaned")

    def login_user(self, hostname, username, password):
        """Used to return Commcell object for another user with credentials provided in tcinputs"""
        commcell = Commcell(hostname, username, password, verify_ssl=False)
        return commcell

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup Testcase entities
            self.setup_entities()
            # Login as Created User
            user_commcell = self.login_user(self.commcell.webconsole_hostname,
                                            self.user_name,
                                            self.user_password)
            # Initialize client groups object
            self.log.info("Initializing Client Groups")
            smartclient_helper1 = SmartClientHelper(commcell_object=user_commcell,
                                                    group_name='SCG27',
                                                    description='Test Group',
                                                    client_scope='Clients of User',
                                                    value=self.user_name)
            self.log.info("""
                          ==================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User"
                          ==================================================================================
                          """)
            self.log.info("Creating Rule for Client equal to Installed")
            rule_list = []
            rule1 = smartclient_helper1.create_smart_rule(filter_rule='Client',
                                                          filter_condition='equal to',
                                                          filter_value='Installed')
            rule_list.append(rule1)
            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper1.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper1.create_smart_client(smart_rule_list=rule_list)
            smartclient_helper1.smart_client_cleanup()

            # Try to create Smart client groups with 3 other scopes
            # Creation should fail
            self.log.info("""
                          ==========================================================================================
                          Step2:
                          Creating Automatic Client Group with Client installed with Scope "Clients in this Commcell"
                          ==========================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG26',
                                                   description='Test Group',
                                                   client_scope='Clients in this Commcell')

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
                          Step3:
                          Creating Automatic Client Group with Client installed with Scope "Clients of Companies"
                          ======================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG27',
                                                   description='Test Group',
                                                   client_scope='Clients of Companies',
                                                   value=self.company_alias)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            try:
                smartclient_helper.create_smart_client(smart_rule_list=rule_list)
                smartclient_helper.smart_client_cleanup()
            except Exception as client_creation_excp:
                self.log.error(f'Failed to create client group {smartclient_helper.group_name} '
                               f'with scope {smartclient_helper.client_scope}')

            self.log.info("""
                          =======================================================================================
                          Step4:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User Group"
                          =======================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG27',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value='master')

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            try:
                smartclient_helper.create_smart_client(smart_rule_list=rule_list)
                smartclient_helper.smart_client_cleanup()
            except Exception as client_creation_excp:
                self.log.error(f'Failed to create client group {smartclient_helper.group_name} '
                               f'with scope {smartclient_helper.client_scope}')
                self.log.error('Enountered exception : %s', client_creation_excp)


        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.cleanup_entities()