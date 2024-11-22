# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.Security.securityhelper import RoleHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing basic security case to validate acceptance
        case for Security - Role Operations"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Test for Security-Role"
        super(TestCase, self).__init__()
        self.name = "Security - Role Operations"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SECURITYANDROLES
        self.commcell_obj = None
        self._roles_helper = None
        self._server_tc = None
        self.log = None
        self.commcell_obj = None
        self.result_string = 'Successful'

    def setup(self):
        """Setup function of this test case"""
        self.commcell_obj = self._commcell
        self._server_tc = ServerTestCases(self)
        self.log = logger.get_log()
        self._roles_helper = RoleHelper(self.commcell_obj)

    def run(self):
        """Test case Execution starts from here """
        self._server_tc.log_step(
            """
            Test Case
            1) Creates Role with random permissions and category names
            2) Modifying the Role properties like 'name', 'description', 'status', 'capability'
            3) Overwriting or deleting capabilities
            4) Delete Role
            """, 200
        )
        # Define role name to be used for this test case
        role_name = 'Role_'+str(self.id)
        self._server_tc.log_step("""Precautionary cleaning""")
        # delete role if it already exists on commcell
        self.log.info("deleting the role if it is already exist on the commcell with same name ")
        self._roles_helper.delete_role(role_name)

        try:
            # Attempt to create role
            self._server_tc.log_step("""step 1: Creating role""")
            self._roles_helper.create_role(role_name=role_name, random_permission='True')

            # Modify Role properties
            self._server_tc.log_step("""step 2: Modifying Role Properties: Name,
            Description, status and capabilities""")
            new_name = role_name+'_test'
            description = "created by automation testcase 48636"
            self._roles_helper.update_role_properties(modification_request='Update', name=new_name,
                                                      description=description, status=False)
            self.log.info("Reverting back the name and status of role")
            self._roles_helper.update_role_properties(modification_request='Update',
                                                      name=role_name, status=True)
            self.log.info("Updating Role with more permissions and categories")
            self._roles_helper.update_role_properties(modification_request='Update',
                                                      random_flag=True)
            self._server_tc.log_step("""step 3: Overwriting and deleting capabilities""")
            permission_list, category_list = self._roles_helper.generate_permissions_categories()
            self._roles_helper.update_role_properties(modification_request='Overwrite',
                                                      permissions_list=permission_list,
                                                      category_list=category_list)
            self.log.info("deleting capabilities that are updated in last operation")
            self._roles_helper.update_role_properties(modification_request='Delete',
                                                      permissions_list=permission_list,
                                                      category_list=category_list)
            self.log.info("successfully deleted capabilities on role")
            self._server_tc.log_step("""step 4: Deleting Role""")
            self._roles_helper.delete_role(role_name)
            self.log.info("Test-case Execution completed successfully")
        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self._server_tc.log_step("""Test Case FAILED""", 200)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self._roles_helper.delete_role(role_name)
            self._roles_helper.delete_role('Role_48636_test')
