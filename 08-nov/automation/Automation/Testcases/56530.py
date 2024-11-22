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
from AutomationUtils.options_selector import OptionsSelector
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
        self.name = 'Testcase for Creation of Smart Client Group with name SCG8'
        self.user_helper = None
        self.organization_helper = None
        self.user_name = "LOCALUSER11" + SmartClientHelper.generate_random_username()
        self.user_email = SmartClientHelper.generate_random_email()
        self.user_password = UserHelper.password_generator(3, 12)
        self.company_name = "NEW_COMP_007"
        self.company_email = SmartClientHelper.generate_random_email()
        self.company_contact = "NewCompany7" + SmartClientHelper.generate_random_username()
        self.company_alias = "NEW_COMP_007" + SmartClientHelper.generate_random_username()
        self.options_selector = None

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        self.user_helper = UserHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        # Generating n ready clients for Created user and Company Tenant Admin User
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        self.user_clients = {"assoc1": {"clientName": clients_list, "role": ["Client Admins"]}}
        clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients), num=3)[0]
        # make it a negative check
        self.company_clients = {"assoc1": {"clientName": clients_list, "role": ["Client Admins"]}}
        # Creating User
        self.user_helper.create_user(user_name=self.user_name,
                                     email=self.user_email,
                                     password=self.user_password,
                                     security_dict=self.user_clients)

        self.organization_helper.create(name=self.company_name,
                                        email=self.company_email,
                                        contact_name=self.company_contact,
                                        company_alias=self.company_alias)

        # Associate clients to Company User
        self.commcell.users.refresh()
        self.log.info(str(self.commcell.users._get_users()))
        company_user = self.commcell.users.get(self.company_alias + "\\" + self.company_email.split("@")[0].lower())
        # We are trying to give security association of a company client to a different company user, It should fail
        try:
            company_user.update_security_associations(entity_dictionary=self.company_clients,
                                                      request_type="UPDATE")
        except Exception as e:
            self.log.info('Handing occured %s', e)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.user_helper.delete_user(user_name=self.user_name,
                                     new_user="admin")
        self.commcell.organizations.delete(self.company_name)
        self.log.info("Testcase Entities Cleaned")

    def run(self):
        """Main function for test case execution"""
        try:
            # Setting up entities
            self.setup_entities()
            # Initialize client groups object
            self.log.info("Initializing Client Groups")

            self.log.info("""
                          ==========================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients in this Commcell"
                          ==========================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG8',
                                                   description='Test Group',
                                                   client_scope='Clients in this Commcell')
            self.log.info("Creating Rule for Client equal to Installed")
            rule_list = []
            rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')

            rule_list.append(rule1)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)
            smartclient_helper.smart_client_cleanup()

            self.log.info("""
                          ======================================================================================
                          Step2:
                          Creating Automatic Client Group with Client installed with Scope "Clients of Companies"
                          ======================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG8',
                                                   description='Test Group',
                                                   client_scope='Clients of Companies',
                                                   value=self.company_alias)

            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)
            smartclient_helper.smart_client_cleanup()

            self.log.info("""
                          ==================================================================================
                          Step3:
                          Creating Automatic Client Group with Client installed with Scope "Clients of User"
                          ==================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG8',
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
            smartclient_helper = SmartClientHelper(commcell_object=self.commcell,
                                                   group_name='SCG8',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value='master')

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
