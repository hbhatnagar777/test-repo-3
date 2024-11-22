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

import datetime
import time
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
        self.name = 'Testcase for Creation of Smart Client Group with name SCG26'
        self.organization_helper = None
        self.company_name1 = None
        self.company_contact1 = None
        self.company_alias1 = None
        self.company_name2 = None
        self.company_contact2 = None
        self.company_alias2 = None
        self.company1_email = SmartClientHelper.generate_random_email()
        self.company2_email = SmartClientHelper.generate_random_email()
        self.company_user_password1 = None
        self.company_user_password2 = None
        self.company_creator_password = None

    def generate_company_name(self):
        """Generates a random company name based on the timestamp"""
        time.sleep(5) # To make sure two consecutively generated names are unique
        suffix = datetime.datetime.now().strftime("%H%M%S")
        return "comp" + str(suffix)

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        # Sets up Two organizations and changes their passwords for later access
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")

        self.company_user_password1 = UserHelper.password_generator(3, 12)
        self.company_user_password2 = self.company_user_password1
        self.company_creator_password = self.inputJSONnode['commcell']['commcellPassword']

        # Initialize company name, alias, contact
        self.company_name1 = self.generate_company_name()
        self.company_contact1 = self.company_name1 + "_Contact"
        self.company_alias1 = self.company_name1
        self.company_name2 = self.generate_company_name()
        self.company_contact2 = self.company_name2 + "_Contact"
        self.company_alias2 = self.company_name2

        self.organization_helper = OrganizationHelper(self.commcell)
        # Creating Organization needed for testcase
        self.organization_helper.create(name=self.company_name1,
                                        email=self.company1_email,
                                        contact_name=self.company_contact1,
                                        company_alias=self.company_alias1)
        self.organization_helper.create(name=self.company_name2,
                                        email=self.company2_email,
                                        contact_name=self.company_contact2,
                                        company_alias=self.company_alias2)
        # Change passwords of created organization users for access
        # For Company user1
        self.log.info("Updating Passwords for Organizations {0}, {1}".format(self.company_name1, self.company_name2))
        company_user1 = self.commcell.users.get(self.company_alias1 + "\\" + self.company1_email.split("@")[0])
        company_user1.update_user_password(new_password=self.company_user_password1,
                                           logged_in_user_password=self.company_creator_password)
        # For Company user2
        company_user2 = self.commcell.users.get(self.company_alias2 + "\\" + self.company2_email.split("@")[0])
        company_user2.update_user_password(new_password=self.company_user_password2,
                                           logged_in_user_password=self.company_creator_password)
        self.log.info("Passwords Updated Succesfully")
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.commcell.organizations.delete(self.company_name1)
        self.commcell.organizations.delete(self.company_name2)
        self.log.info("Testcase Entities Cleaned")

    def login_user(self, hostname, username, password):
        """Used to return Commcell object for another user with credentials provided in tcinputs"""
        commcell = Commcell(hostname, username, password, verify_ssl=False)
        return commcell

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup testcase entities
            self.setup_entities()
            # Logging in as user username1
            company_user1 = self.login_user(self.commcell.webconsole_hostname,
                                            self.company_alias1 + "\\" + self.company1_email.split("@")[0],
                                            self.company_user_password1)
            # Initialize client groups object
            self.log.info("Initializing Client Groups")
            smartclient_helper = SmartClientHelper(commcell_object=company_user1,
                                                   group_name='SCG26',
                                                   description='Test Group',
                                                   client_scope='Clients of Companies',
                                                   value=self.company_alias1)
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
            self.log.info('Creating Client Group %s for testcase %s', smartclient_helper.group_name, self.id)
            # Posting Client Group Make request
            smartclient_helper.create_smart_client(smart_rule_list=rule_list)

            # Login from different user
            user2 = self.login_user(self.commcell.webconsole_hostname,
                                    self.company_alias2 + "\\" + self.company2_email.split("@")[0],
                                    self.company_user_password2)
            smartclient_helper2 = SmartClientHelper(commcell_object=user2)

            # Check if created group is visible to this user but not to another company tenant admin
            if not smartclient_helper2.has_client_group(smartclient_helper.group_name):
                if smartclient_helper.has_client_group(smartclient_helper.group_name):
                    self.log.info(f'Created client group {smartclient_helper.group_name} not visible to another user')

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            if smartclient_helper is not None:
                smartclient_helper.smart_client_cleanup()
            self.cleanup_entities()
