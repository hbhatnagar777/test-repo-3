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
from Server.Workflow import workflowconstants as WC

class TestCase(CVTestCase):
    """Class for executing Workflow - Operations - Business Logic Workflows with Mode API"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[WORKFLOW] - Operations - Business Logic Workflows with mode API"
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
            workflow_name = "DeleteClientAuthorizationAPI"
            message_name = "App_DeleteClientRequest"
            workflow_helper = WorkflowHelper(self, workflow_name)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                1. Create non admin user and corresponding commcell object
                2. Validate if the business logic workflows DeleteClientAuthorization and
                    GetAndProcessAuthorization are deployed
                3. Create a new pseudo client
                4. Try deleting client from non admin user. It should be blocked.
                5. Approve the workflow user interaction request to delete the client
                6. Get workflow job id for the business logic workflow and wait for it to complete.
                7. Validate if client is deleted
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object
                Validate if the BL workflows DeleteClientAuthorization and GetAndProcessAuthorization are deployed
                Create a pseudo client
            """)
            client_name = OptionsSelector(self.commcell).get_custom_str()
            self.log.info("Creating a pseudo client [%s]", client_name)
            self.commcell.clients.create_pseudo_client(client_name)

            response = workflow_helper.bl_workflows_setup([workflow_name])
            resultset = workflow_helper.get_db_bl_workflow(message_name, workflow_name)
            assert len(resultset) == 1, "FAILED in App_MessageHandler validation. Returned more than a row."

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
                self.log.info("Attempting to delete client. Should be blocked by workflow [%s]", workflow_name)
                user_commcell.clients.delete(client_name)
                raise Exception("Client deletion succeeded. Expected to be blocked from business logic workflow")
            except Exception as excp:
                if 'An email has been sent to the administrator' in str(excp):
                    self.log.info("Error as expected: [%s]", str(excp))
                    self.log.info("Client deletion successfully blocked through business logic workflow.")
                else:
                    self.log.error(str(excp))
                    raise Exception("Client validation failed")
                user_commcell.clients.refresh()
                assert user_commcell.clients.has_client(client_name), "Client deleted unexpectedly. Test Failed"
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Approve the workflow user interaction request to delete the client
                Get workflow job id for the business logic workflow and wait for it to complete.
                Validate if client is deleted
            """)
            workflow_helper.process_user_requests(user, input_xml=WC.WORKFLOW_DEFAULT_USER_INPUTS % user)
            user_commcell.clients.refresh()
            assert not user_commcell.clients.has_client(client_name), "Client still exists. Test Failed"
            self.log.info("Client [%s] deleted via Business logic workflow's [Approve] action", client_name)
            # ---------------------------------------------------------------------------------------------------------

        except Exception as excp:
            workflow_helper.test.fail(excp)
        finally:
            workflow_helper.cleanup()
            workflow_helper.database.delete_client(client_name)
            UserHelper(self.commcell).delete_user(user_name=user, new_user='admin')
