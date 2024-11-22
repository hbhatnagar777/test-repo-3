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

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.Security.userhelper import UserHelper
from AutomationUtils.idautils import CommonUtils

class TestCase(CVTestCase):
    """Class for executing Workflow - Operations - Business Logic Workflows with Multiple Message Names"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[WORKFLOW] - Operations - Business Logic Workflows with Multiple Message Names"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.store = None

    def run(self):
        """Main function for test case execution"""

        try:
            self.commcell.workflows.refresh()

            # Class Initializations
            workflow_name = "MultipleMessageNames"
            message_name1 = "App_SetClientPropertiesRequest"
            message_name2 = "App_UpdateSubClientPropertiesRequest"
            workflow_helper = WorkflowHelper(self, workflow_name)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                1. Create non admin user and corresponding commcell object
                2. Validate if the business logic workflow MultipleMessageNames is deployed
                3. Create a new pseudo client
                4. Try setting client description. It should be blocked.
                5. Try setting subclient description. It should be blocked.
                7. Validate if client is deleted
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object
                Validate if the business logic workflow MultipleMessageNames is deployed
                Create a pseudo client
            """)
            client_name = OptionsSelector(self.commcell).get_custom_str()
            self.log.info("Creating a pseudo client [%s]", client_name)
            self.commcell.clients.create_pseudo_client(client_name)

            response = workflow_helper.bl_workflows_setup([workflow_name])
            resultset1 = workflow_helper.get_db_bl_workflow(message_name1, workflow_name)
            resultset2 = workflow_helper.get_db_bl_workflow(message_name2, workflow_name)
            assert len(resultset1) == 1, "FAILED in App_MessageHandler validation. Returned more than a row."
            assert len(resultset2) == 1, "FAILED in App_MessageHandler validation. Returned more than a row."

            user_commcell = response[1]
            user = response[0]
            user_association = {'assoc1':{'userName': [user], 'role': ['Master']}}
            UserHelper(self.commcell).modify_security_associations(user_association, user)

            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Try deleting client from non admin user. It should be blocked by BL Workflow.
            """)
            try:
                self.log.info("""Attempting to set client descriptiom. Should be blocked by workflow [%s]""",
                              workflow_name)
                user_commcell.clients.get(client_name).description = "test"
                raise Exception("Client description update succeeded. Expected to be blocked from BL workflow")
            except Exception as excp:
                if 'Client description update succeeded' in str(excp):
                    self.log.error(str(excp))
                    raise Exception("Client validation failed")
                self.log.info("Error as expected: [%s]", str(excp))
                self.log.info("Client update successfully blocked through business logic workflow.")
                workflow_helper.database.delete_client(client_name)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Try setting subclient description. It should be blocked.
            """)
            try:
                self.log.info("""Attempting to set subclient description. Should be blocked by workflow [%s]""",
                              workflow_name)
                subclient = CommonUtils(user_commcell).get_subclient(self.client.client_name)
                subclient.description = "test"
                raise Exception("Subclient description update succeeded. Expected to blocked via BL workflow")
            except Exception as excp:
                if 'Subclient description update succeeded' in str(excp):
                    self.log.error(str(excp))
                    raise Exception("SubClient validation failed")
                self.log.info("Error as expected: [%s]", str(excp))
                self.log.info("SubClient update successfully blocked through business logic workflow.")

            # ---------------------------------------------------------------------------------------------------------

        except Exception as excp:
            workflow_helper.test.fail(excp)
        finally:
            workflow_helper.cleanup()
            workflow_helper.database.delete_client(client_name)
            UserHelper(self.commcell).delete_user(user_name=user, new_user='admin')
