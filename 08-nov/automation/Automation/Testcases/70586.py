# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of user groups in Admin console.

functions over,
1. Creation of user group based on criteria passed as
   arguments to the test case and base files.
2. Validates if the user group is created successfully and the values are
   retained correctly.
3. Edits the user group details for created  group and also adds users to it and
    re-validates against the user inputs.
4. Removes the users associated in step 4.
5. Deletes the user group created.

TestCase:
    __init__()      --  Method to initialize TestCase class

    run()           --  Method to run the functionality of this test case

    tear_down()     --  Method to do cleanup and close open processes

Tcinputs (Mandatory):
    service_commcell    (str)   -   hostname of a service commcell to test on

Tcinputs (Optional):
    users   (str)   -   comma seperated, no spaces, names of users to add to group
                        default: random users from available
    negative_test (str) - give 'false' to avoid testing negative scenario
                          default: True
    table_validation_attempts (int) -   number of retries for validating users table
                                        default: 1,
                                        give 0 to skip table validation

Requires:
    CONFIG.Security.LDAPs.Active_Directory3 must have the AD details

"""
import traceback

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.UserGroupHelper import UserGroupMain
from random import randint, sample

from Reports.utils import TestCaseUtils
from cvpysdk.commcell import Commcell

CONFIG = get_config()


class TestCase(CVTestCase):
    """ Basic Acceptance test for User Groups"""

    def __init__(self):
        """
        Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.service_commcell = None
        self.domain_ug = 'None'
        self.name = "[Global CC]: Validate Security - User Groups Functionality"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.global_console = None
        self.user_group_obj = None
        self.tcinputs = {}
        rand = randint(1, 100)
        self.server_details = CONFIG.Security.LDAPs.Active_Directory3._asdict()
        self.ug1 = 'group1_{}'.format(rand)
        self.ug2 = 'new_group1_{}'.format(rand)

    def random_users(self):
        self.commcell.user_groups.refresh()
        user_group_sdk = self.commcell.user_groups.get(self.user_group_obj.group_name)
        users_for_group = [
            username for username in user_group_sdk.available_users_for_group()
            if len(username) <= 15  # avoid long usernames, that get truncated in UI
               and 'user1_' not in username and 'user2_' not in username  # avoid intersecting with tc53652
        ]

        if len(users_for_group) > 5:
            users_for_group = list(sample(users_for_group, 5))
        self.log.info(f"generated random users list {users_for_group}")
        return ",".join(users_for_group)

    def run(self):
        self.service_commcell = Commcell(
            self.tcinputs['service_commcell'],
            authtoken=self.commcell.get_saml_token(), is_service_commcell=True
        )
        errors = []
        self.log.info("Started executing %s test case", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.global_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.global_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
        self.global_console.navigator.switch_service_commcell('Global')
        self.user_group_obj = UserGroupMain(
            self.global_console, CommServDatabase(self.service_commcell), self.service_commcell
        )

        # TABLE DB VALIDATIONS TO BE DONE

        try:
            # CREATE TEST
            self.user_group_obj.group_name = self.ug1
            self.user_group_obj.description = self.ug1
            self.user_group_obj.add_new_user_group(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("User group creation completed. validating User group...")

            # READ TEST
            self.user_group_obj.validate_user_group()
            self.log.info("Initial User group validation completed. Editing Details")

            # UPDATE TEST
            self.user_group_obj.user_list = (self.tcinputs.get('users') or self.random_users()).split(',')
            self.user_group_obj.group_name = self.ug2
            self.user_group_obj.description = self.ug2
            self.user_group_obj.quota = False
            self.user_group_obj.group_enabled = False
            self.user_group_obj.laptop_admins = True
            self.user_group_obj.edit_user_group_details(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("User group editing completed. validating User group...")

            # READ TEST
            self.user_group_obj.validate_user_group()
            self.log.info("Post Editing validation completed. Removing associated users"
                          "from user group")

            # REMOVE USER
            self.user_group_obj.remove_users_from_user_group()
            self.user_group_obj.validate_user_group()
            self.log.info("Users are removed successfully. Deleting user group now")

            # DELETE TEST
            self.user_group_obj.delete_user_group()
        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during UserGroups CRUD: {exp}")

        # AD USERGROUP TEST
        try:
            if not self._commcell.domains.has_domain(self.server_details.get('NETBIOSName')):
                self.commcell.domains.add(
                    domain_name=self.server_details.get('DomainName'),
                    netbios_name=self.server_details.get('NETBIOSName'),
                    user_name=self.server_details.get('UserName'),
                    password=self.server_details.get('Password'),
                    company_id=0
                )
            self.user_group_obj.group_name = self.server_details.get('NETBIOSName').lower() + "\\Domain Users"
            self.domain_ug = self.user_group_obj.group_name
            self.user_group_obj.local_group = ['master']
            self.user_group_obj.add_new_ad_group(negative_case=self.tcinputs.get('negative_test') != 'false')

        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during AD UserGroup Creation: {exp}")

        if errors:
            self.log.info(">>>>>>> TESTCASE FAILED! <<<<<<<<<")
            self.status = constants.FAILED
            self.result_string = '\n'.join(errors)

    def tear_down(self):
        """ To clean up the test case environment created """
        try:
            self.commcell.user_groups.refresh()
            for ug in [self.ug1, self.ug2, self.domain_ug]:
                if self.commcell.user_groups.has_user_group(ug):
                    self.log.info(f"Deleting user group: {ug}")
                    self.commcell.user_groups.delete(ug, 'admin')
        except Exception as exp:
            self.log.error(f"Error during teardown: {exp}")
        AdminConsole.logout_silently(self.global_console)
        Browser.close_silently(self.browser)
