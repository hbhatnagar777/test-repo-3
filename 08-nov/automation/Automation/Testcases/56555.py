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
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper

# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG10'
        self.user_helper = None
        self.organization_helper = None
        self.user_name = "LOCALUSER22" + SmartClientHelper.generate_random_username()
        self.user_email = SmartClientHelper.generate_random_email()
        self.user_password = None
        self.company_name = "NEW_TEST_COMPANY"
        self.company_email = SmartClientHelper.generate_random_email()
        self.company_contact = "TEST_CONTACT"
        self.company_alias = "NEW_TEST_COMPANY"
        self.options_selector = None

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        self.user_password = UserHelper.password_generator(3, 12)
        self.user_helper = UserHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        # Generating n ready clients for Created user
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.user_clients = {"assoc1": {"clientName": clients_list, "role": ["Client Admins"]},
                             "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Client Group Owner"]}}
        self.user_helper.create_user(user_name=self.user_name,
                                     email=self.user_email,
                                     password=self.user_password,
                                     security_dict=self.user_clients)
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
        self.user_helper.delete_user(user_name=self.user_name,
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
            self.log.info("Setup Testcase Entities")
            self.setup_entities()
            # Login as created User
            self.log.info("Logging in as {0}".format(self.user_name))
            user_commcell = self.login_user(self.commcell.webconsole_hostname,
                                            self.user_name,
                                            self.user_password)
            # Initialize client groups object
            self.log.info("Initializing Client Groups")

            rule_list = []
            self.log.info("""
                          ==========================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients in this Commcell"
                          ==========================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG10',
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
                               f'with scope {smartclient_helper.client_scope} \n Encountered Exception :'
                               f' {client_creation_excp}')

            self.log.info("""
                          ======================================================================================
                          Step2:
                          Creating Automatic Client Group with Client installed with Scope "Clients of Companies"
                          ======================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG10',
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
                    f'with scope {smartclient_helper.client_scope} \n Encountered Exception : {client_creation_excp}')

            self.log.info("""
                          ==================================================================================
                          Step3:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User"
                          ==================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=user_commcell,
                                                   group_name='SCG10',
                                                   description='Test Group',
                                                   client_scope='Clients of User',
                                                   value=self.user_name)

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
                                                   group_name='SCG10',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value='master')

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            try:
                smartclient_helper.create_smart_client(smart_rule_list=rule_list)
                smartclient_helper.smart_client_cleanup()
            except Exception as client_creation_excp:
                self.log.error(
                    f'Failed to create client group {smartclient_helper.group_name} '
                    f'with scope {smartclient_helper.client_scope}')
                self.log.error('Encountered Exception %s', client_creation_excp)

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.cleanup_entities()
