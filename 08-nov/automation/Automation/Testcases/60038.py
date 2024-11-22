# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import time
import datetime
from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils import constants
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.Security.securityhelper import OrganizationHelper


class TestCase(CVTestCase):
    """Class for executing testcase to verify company SCG property modification (rules, scope, others)"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Property modification check for default company Smart client group"
        self.tenant_admin = None
        self.company_name = None
        self.company_contact = None
        self.company_alias = None
        self.config_json = config.get_config()
        # Check if config.json has all required properties populated else raise exception
        if(self.config_json.SmartClientGroup.company_email and
           self.config_json.SmartClientGroup.company_user_password and
           self.config_json.SmartClientGroup.company_creator_password):
            self.company_email = self.config_json.SmartClientGroup.company_email
            self.company_user_password = self.config_json.SmartClientGroup.company_user_password
            self.company_creator_password = self.config_json.SmartClientGroup.company_creator_password
        else:
            raise SDKException('ClientGroup', '102', 'Required properties not populated in key '
                                                     '"SmartClientGroup" in config.json')

    def generate_company_name(self):
        """Generates a random company name based on the timestamp"""
        time.sleep(5)  # To make sure two consecutively generated names are unique
        suffix = datetime.datetime.now().strftime("%H%M%S")
        return "comp" + str(suffix)

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        # Creating Users, User1 and User2 and Adding them to a user Group
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
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
        return Commcell(webconsole_hostname, username, password)

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
                                                        username=self.company_alias + "\\" + self.company_email.
                                                        split("@")[0],
                                                        password=self.company_user_password)
            # Initialization smartclienthelper object
            smartclient_helper = SmartClientHelper(commcell_object=self.tenant_admin)

            # Get default company smart client group
            default_company_scg = smartclient_helper.get_client_group(self.company_alias)

            # Try modifiying properties asides from rules or scope -> Should be allowed
            default_company_scg.update_properties(properties_dict={'description': 'New Modified Description'})
            self.log.info("Description modification successful, scenario working as expected")
            default_company_scg.refresh()

            # Try modifiying scope -> Should throw an error and group should remain unchanged
            current_properties = default_company_scg.properties
            # Comparing old and new properties as try catch block doesn't catch it as an exception
            smartclient_helper.update_scope(clientgroup_name=self.company_alias,
                                            client_scope='Clients of Companies',
                                            value=self.company_name)
            default_company_scg.refresh()
            new_properties = default_company_scg.properties
            if current_properties == new_properties:
                self.log.info("Scope change Scenario working as expected, modification not allowed")
            else:
                raise SDKException('ClientGroup', '102', 'Scope modification for Default '
                                   'company clientgroup {0} shouldn\'t be allowed'.format(
                                    default_company_scg.clientgroup_name))

            # Try modifiying rules -> Shouldn't throw any error but group should remain unchanged
            rules_list = []
            # Create dummy rules to test modification
            new_rule1 = smartclient_helper.create_smart_rule(filter_rule='Client',
                                                             filter_condition='equal to',
                                                             filter_value='Installed')
            rules_list.append(new_rule1)
            new_scgrule = smartclient_helper.client_groups.merge_smart_rules(rules_list)
            default_company_scg.update_properties(properties_dict={'scgRule': new_scgrule})
            default_company_scg.refresh()
            new_properties = default_company_scg.properties
            # Comparing old and new properties as try catch block doesn't catch it as an exception
            if current_properties == new_properties:
                self.log.info("Rule change Scenario working as expected, modification not allowed")
            else:
                raise SDKException('ClientGroup', '102', 'Rule modification for Default '
                                   'company clientgroup {0} shouldn\'t be allowed'.format(
                                    default_company_scg.clientgroup_name))

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            self.cleanup_entities()
