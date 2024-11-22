# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of users in Admin console.

functions over,
1. Creation of users based on different criteria's passed as
   arguments to the test case and base files.
2. Validates if the users are created successfully and the values are
   retained correctly.
3. Deletes the users created & verified in above steps.

Tcinputs (Mandatory):
    service_commcell    (str)   -   hostname of a service commcell to test on

Tcinputs (Optional):
    plan    (str)   -   name of a plan to add while creating user
                        default: None
    user_groups (str)   -   comma seperated, no spaces, names of user groups to add user
                            default: randomly selects from existing user groups
    negative_test (str) -   give 'false' to avoid testing negative scenario
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

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.UserHelper import UserMain
from Reports.utils import TestCaseUtils
from random import randint, sample

from cvpysdk.commcell import Commcell

CONFIG = get_config()


class TestCase(CVTestCase):
    """ Basic Acceptance test for Users from Global"""

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Global CC]: Validate Security - Users Functionality"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.global_console = None
        self.user_obj = None
        self.utils = TestCaseUtils(self)
        self.server_details = CONFIG.Security.LDAPs.Active_Directory3._asdict()
        self.tcinputs = {}
        self.service_commcell = None

    def random_user_groups(self):
        local_user_groups = [
            ug for ug in self.service_commcell.user_groups.non_system_usergroups()
            if ('\\' not in ug and len(ug) <= 15)  # avoid long user group names that get truncated in UI
               and ('group1_' not in ug)  # avoid intersecting with tc53712
        ]
        if len(local_user_groups) > 5:
            local_user_groups = list(sample(local_user_groups, 5))
        self.log.info(f"generated random user groups: {local_user_groups}")
        return ",".join(local_user_groups)

    def run(self):
        self.service_commcell = Commcell(
            self.tcinputs['service_commcell'],
            authtoken=self.commcell.get_saml_token(), is_service_commcell=True
        )

        errors = []

        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        rand = randint(1, 100)

        self.global_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.global_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
        self.global_console.navigator.switch_service_commcell('Global')
        self.user_obj = UserMain(self.global_console, self.service_commcell)

        # TABLE DB VALIDATION TO BE ADDED

        # CREATE TEST
        try:
            self.user_obj.user_name = "user1_{}".format(rand)
            self.user_obj.full_name = "user1_{}".format(rand)
            self.user_obj.email = "user1_{}@cv.com".format(rand)
            self.user_obj.password = self.inputJSONnode['commcell']['commcellPassword']
            self.user_obj.add_new_local_user(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("User Creation completed. validating User...")

            # READ TEST
            self.user_obj.validate_user()
            self.log.info("Initial User validation completed")

            # UPDATE TEST
            self.user_obj.new_user_name = "new_user1_{}".format(rand)
            self.user_obj.full_name = "new_user1_{}".format(rand)
            self.user_obj.email = "new_user1_{}@cv.com".format(rand)
            self.user_obj.user_groups = (self.tcinputs.get('user_groups') or self.random_user_groups()).split(',')
            self.user_obj.user_enabled = False
            self.user_obj.plan = self.tcinputs.get('plan') or None
            self.user_obj.admin_password = self.inputJSONnode['commcell']['commcellPassword']
            self.log.info("Now proceeding to edit user details")
            self.user_obj.edit_local_user_details(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("User editing completed")

            # READ TEST
            self.user_obj.validate_user()

            # REMOVE TEST
            self.user_obj.delete_user()

        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during local user CRUD: {exp}")

        self.log.info("User validation after editing completed."
                      " Adding new user with system password enabled")

        # CREATE TEST WITH SYSTEM PASSWORD
        try:
            self.user_obj.user_name = "user2_{}".format(rand)
            self.user_obj.full_name = "user2_{}".format(rand)
            self.user_obj.email = "user2_{}@cv.com".format(rand)
            self.user_obj.user_groups = (self.tcinputs.get('user_groups') or self.random_user_groups()).split(',')
            self.user_obj.system_password = True
            self.user_obj.invite_user = True
            self.user_obj.add_new_local_user()
            self.log.info("Local User with system password created successfully."
                          " Adding an external User")
        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during system password user creation: {exp}")

        # CREATE TEST FROM AD
        try:
            if not self._commcell.domains.has_domain(self.server_details.get('NETBIOSName')):
                self.commcell.domains.add(
                    domain_name=self.server_details.get('DomainName'),
                    netbios_name=self.server_details.get('NETBIOSName'),
                    user_name=self.server_details.get('UserName'),
                    password=self.server_details.get('Password'),
                    company_id=0
                )
            self.user_obj.external_provider = self.server_details.get('NETBIOSName')
            self.user_obj.user_name = self.server_details.get('UserName')
            self.user_obj.email = None
            self.user_obj.user_groups = (self.tcinputs.get('user_groups') or self.random_user_groups()).split(',')
            self.user_obj.invite_user = False
            self.user_obj.add_new_external_user(negative_case=self.tcinputs.get('negative_test') != 'false')
            self.log.info("External User created successfully.")
            self.log.info("User creation, editing and validation succeeded. Deleting created users.")
        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during AD user creation: {exp}")

        if errors:
            self.log.info(">>>>>>> TESTCASE FAILED! <<<<<<<<<")
            self.status = constants.FAILED
            self.result_string = '\n'.join(errors)

    def tear_down(self):
        """ To clean up the test case environment created"""
        self.user_obj.delete_user_api()
        AdminConsole.logout_silently(self.global_console)
        Browser.close_silently(self.browser)
