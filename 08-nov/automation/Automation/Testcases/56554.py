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

import time
import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper

# Class of Testcase is named as TestCase which inherits from CVTestCase


class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Smart Client Group with name SCG9'
        self.tenant_admin = None
        self.company_name = None
        self.company_contact = None
        self.company_alias = None
        self.company_email = SmartClientHelper.generate_random_email()
        self.company_user_password = None
        self.company_creator_password = None

    def generate_company_name(self):
        """Generates a random company name based on the timestamp"""
        time.sleep(5) # To make sure two consecutively generated names are unique
        suffix = datetime.datetime.now().strftime("%H%M%S")
        return "comp" + str(suffix)

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        # Creating Users, User1 and User2 and Adding them to a user Group
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")

        self.company_creator_password = self.inputJSONnode['commcell']['commcellPassword']
        self.company_user_password = UserHelper.password_generator(3, 12)
        # Generate the company name and alias
        self.company_name = self.generate_company_name()
        self.company_contact = self.company_name + "_Contact"
        self.company_alias = self.company_name
        # Create Organization
        self.organization_helper = OrganizationHelper(self.commcell)
        self.organization_helper.create(name=self.company_name,
                                        email=self.company_email,
                                        contact_name=self.company_contact,
                                        company_alias=self.company_alias)
        # Associate clients to Company User
        self.commcell.refresh()
        company_user = self.commcell.users.get(self.company_alias + "\\" + self.company_email.split("@")[0])
        company_user.update_user_password(new_password=self.company_user_password,
                                          logged_in_user_password=self.company_creator_password)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.commcell.organizations.delete(self.company_name)
        self.log.info("Testcase Entities Cleaned")

    def login_company_user(self, webconsole_hostname, username, password):
        """Returns Commcell Object for given user"""
        return Commcell(webconsole_hostname, username, password, verify_ssl=False)

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup testcase entities
            self.setup_entities()
            # Initialize client groups object
            self.log.info("Initializing Client Groups")
            # Login Company Tenant Admin
            self.log.info("Logging in as Company Tenant Admin")
            self.tenant_admin = self.login_company_user(webconsole_hostname=self.commcell.webconsole_hostname,
                                                        username=self.company_alias + "\\" +
                                                        self.company_email.split("@")[0],
                                                        password=self.company_user_password)

            rule_list = []
            self.log.info("""
                          ==========================================================================================
                          Step1:
                          Creating Automatic Client Group with Client installed with Scope "Clients in this Commcell"
                          ==========================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=self.tenant_admin,
                                                   group_name='SCG9',
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
                               f'with scope {smartclient_helper.client_scope}\n Exception {client_creation_excp}')

            self.log.info("""
                          ======================================================================================
                          Step2:
                          Creating Automatic Client Group with Client installed with Scope "Clients of Companies"
                          ======================================================================================
                          """)
            smartclient_helper = SmartClientHelper(commcell_object=self.tenant_admin,
                                                   group_name='SCG9',
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
            smartclient_helper = SmartClientHelper(commcell_object=self.tenant_admin,
                                                   group_name='SCG9',
                                                   description='Test Group',
                                                   client_scope='Clients of User',
                                                   value=self.company_alias + "\\" + self.company_email.split("@")[0])

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
            smartclient_helper = SmartClientHelper(commcell_object=self.tenant_admin,
                                                   group_name='SCG9',
                                                   description='Test Group',
                                                   client_scope='Clients of User Group',
                                                   value=self.company_alias + "\\Tenant Admin")

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
