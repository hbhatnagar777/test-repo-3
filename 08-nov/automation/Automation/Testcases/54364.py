# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Basic acceptance test case for Roles in AdminConsole

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

Tcinputs (Optional):

    number_of_permissions       -   number of random permissions to add to role
                                    default: 5
    negative_test (str)         -   give 'false' to avoid testing negative scenario
                                    default: True
    table_validation_attempts (int) -   number of retries for validating users table
                                        default: 1,
                                        give 0 to skip table validation
"""
import traceback

from AutomationUtils import database_helper, constants
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.roles_helper import RolesMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.num_permissions = 5
        self.name = "Basic Acceptance Test - CommCell level Roles CRUD Validation in CC"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.tcinputs = {}
        self.browser = None
        self.admin_console = None
        self.roles_helper = None

    def setup(self):
        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.num_permissions = int(self.tcinputs.get('number_of_permissions', 5))
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.roles_helper = RolesMain(self.admin_console, commcell= self.commcell, csdb=self.csdb)
        if self.commcell.roles.has_role("test_role"):
            self.commcell.roles.delete("test_role")
        if self.commcell.roles.has_role("new_test_role"):
            self.commcell.roles.delete("new_test_role")

    def run(self):
        """
        Test Case
        1) Creates Role with given permissions and category names
        2) Modifying the Role name, Overwriting or deleting permissions
        3) Delete Role
        """
        errors = []

        # TABLE DB VALIDATION
        retries = int(self.tcinputs.get('table_validation_attempts', 1))

        for attempt in range(retries):
            try:
                self.roles_helper.validate_listing_company_filter()
                break
            except Exception as exp:
                self.log.error(exp)
                self.log.error(traceback.format_exc())
                if attempt == retries - 1:
                    errors.append(f"Error during Roles listing company filter: {exp}")

        try:
            # CREATE TEST
            self.roles_helper.role_name = "test_role"
            self.roles_helper.new_role_name = "new_test_role"
            self.roles_helper.enable_role = True
            self.roles_helper.visible_to_all = False
            self.roles_helper.add_security_roles(
                self.num_permissions,
                negative_case=self.tcinputs.get('negative_test') != 'false'
            )

            # READ TEST
            self.roles_helper.validate_security_role()

            # UPDATE TEST
            self.roles_helper.enable_role = not self.roles_helper.enable_role
            self.roles_helper.visible_to_all = not self.roles_helper.visible_to_all
            self.roles_helper.edit_security_role(
                self.num_permissions,
                negative_case=self.tcinputs.get('negative_test') != 'false'
            )

            # READ TEST
            self.roles_helper.validate_security_role()

            # DELETE TEST
            self.roles_helper.delete_security_role()
        except Exception as exp:
            self.log.error(exp)
            self.log.error(traceback.format_exc())
            errors.append(f"Error during Roles CRUD: {exp}")

        if errors:
            self.log.info(">>>>>>> TESTCASE FAILED! <<<<<<<<<")
            self.status = constants.FAILED
            self.result_string = '\n'.join(errors)

    def tear_down(self):
        """ To clean up the test case environment created"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
