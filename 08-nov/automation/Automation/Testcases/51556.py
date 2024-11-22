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
    """Class for executing - Validate Enable/Disable a Business logic workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Enable/Disable a Business logic workflow"
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
            workflow_helper = WorkflowHelper(self, workflow_name)
            # ---------------------------------------------------------------------------------------------------------

            workflow_helper.test.log_step("""
                a) Create non admin user and corresponding commcell object
                b) Enable the Business Logic workflow and create backupset
                c) If message name is "App_DeleteBackupset" for the BL workflow, try to delete backupset
                    Try deleting backupset from non admin user. It should be blocked by BL Workflow.
                d) Disable the business logic workflow and try deleting backupset. Backupset deletion should go through
            """, 200)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object
                Create backupset
                Enable the Business Logic workflow
            """)
            user_helper.create_user(user_name=user, full_name=user, email='test@commvault.com',
                                    password=password, local_usergroups=[USERGROUP.MASTER])
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            self.log.info("Enabling workflow [{0}]".format(workflow_name))
            workflow_helper.workflow_obj.enable()
            backupset_inputs = {
                'backupset':
                {
                    'client': self.client.client_name,
                    'agent': "File system",
                    'instance': "defaultinstancename"
                }
            }
            backupset_props = entities.create(backupset_inputs)
            backupset = backupset_props['backupset']['name']

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                If message name is "App_DeleteBackupset" for the BL workflow, try to delete backupset
                Try deleting backupset from non admin user. It should be blocked by BL Workflow.
            """)
            try:
                backupsets = user_commcell.clients.get(self.client.client_name).agents.get("File system").backupsets
                self.log.info(
                    "Attempting to delete backupset. Should be blocked by workflow [{0}]".format(workflow_name)
                )
                backupsets.delete(backupset)
                raise Exception("Backupset deletion succeeded. Expected to be blocked from business logic workflow")
            except Exception as excp:
                if 'Backupset deletion is blocked by Business Logic Workflow' in str(excp):
                    self.log.info("Error as expected: [{0}]".format(str(excp)))
                    self.log.info("Backupset deletion successfully blocked through business logic workflow.")
                else:
                    self.log.error(str(excp))
                    raise Exception("Backupset validation failed")
                assert backupsets.has_backupset(backupset), "BackupSet deleted unexpectedly. Test Failed"

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Disable the business logic workflow and try deleting backupset. Backupset deletion should go through.
            """)
            OptionsSelector(self.commcell).sleep_time(5)
            workflow_helper.workflow_obj.disable()
            entities.delete(backupset_props)

        except Exception as excp:
            workflow_helper.test.fail(excp)
        finally:
            workflow_helper.cleanup()
            user_helper.delete_user(user_name=user, new_user='admin')
            entities.cleanup()
