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

from cvpysdk.commcell import Commcell

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from Server.Security.userhelper import UserHelper
from Server.Security.userconstants import USERGROUP
from AutomationUtils.config import get_config

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for validating - Deploy Business Logic Workflow from user with/without security privileges"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Deploy Business Logic Workflow from user with/without security privileges"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False

    def run(self):
        """Main function for test case execution"""

        try:
            # Initializations
            workflow_name = 'wf_bl_delete_backupset'
            user = OptionsSelector.get_custom_str()
            password = _STORE_CONFIG.Workflow.ComplexPasswords.CommonPassword
            user_helper = UserHelper(self.commcell)
            entities = CVEntities(self)
            workflow_helper = WorkflowHelper(self, workflow_name, deploy=False)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                - Validate deployment of Business Logic Workflow for the user with Administrative Management
                    permission on the Commcell level.
                - Non Admin user with privledges should be able to enable Business logic workflow
                - Non Admin user with privledges should be able to delete the Business logix workflow
                - Validate deployment of Business Logic Workflow for user
                    (dont have permission on Administrative Management on Commcell level)
                - Deployment should fail for user not having privledges
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object with administrative privledges.
                Deploy/Enable/Delete Business logic Workflow.
            """)
            role = {
                'assoc1': {
                    'commCellName': [self.commcell.commserv_name],
                    'role': ["Master"]
                }
            }
            user_helper.create_user(user_name=user, full_name=user, email='testuser@cv.com',
                                    password=password, security_dict=role)
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            user_workflowhelper = WorkflowHelper(self, workflow_name, deploy=True, commcell=user_commcell)

            self.log.info("Enabling workflow [{0}] for user [{1}]".format(workflow_name, user))
            user_workflowhelper.workflow_obj.enable()
            user_workflowhelper.delete(workflow_name)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                - Delete user and recreate with View All only permissions
                - Validate deployment of Business Logic Workflow for user
                    (dont have permission on Administrative Management on Commcell level)
                - Deployment should fail for user not having privledges
            """)
            user_helper.delete_user(user_name=user, new_user='admin')
            user_helper.create_user(user_name=user, full_name=user, email='testuser@cv.com',
                                    password=password, local_usergroups=["View"])
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            user_workflowhelper = WorkflowHelper(self, workflow_name, deploy=False, commcell=user_commcell)
            try:
                user_workflowhelper.deploy()
                self.log.error("Deployment succeeded. Expected to fail.")
                raise Exception("Deployment was supposed to fail for user with View only permissions.")
            except Exception as excp:
                self.log.info("Deployment successfully blocked for user without enough privledges")

        except Exception as excp:
            workflow_helper.test.fail(excp)
        finally:
            workflow_helper.workflows_obj.refresh()
            workflow_helper.delete(workflow_name)
            user_helper.delete_user(user_name=user, new_user='admin')
