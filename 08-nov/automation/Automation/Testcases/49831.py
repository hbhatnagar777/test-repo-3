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
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):
    """Class for executing client side operations through Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Perform client side operations through client activities"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True

        # Inherited class attributes
        self._workflow = None
        self._workflow_client = None
        self._workflow_ma = None
        self._test_req = ("""Test case requirements not met.
                             Req 1. Client with Media Agent not installed.
                             Req 2. Client with media agent installed but no
                                libraries configured""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_client_operations")

        # Get smart inputs for the Workflow
        self._workflow_client = self._workflow.database.get_client('non_ma')
        self._workflow_ma = self._workflow.database.get_ma('diskless', ready=False)

        if not self._workflow_client or not self._workflow_ma:
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:

            # Start workflow execution
            self._workflow.execute(
                {
                    'INP_DOCK_CLIENTS': self._workflow_client,
                    'INP_DELETE_CLIENTS': self._workflow_client,
                    'INP_DELETE_DATAGENT_CLIENT': self._workflow_client,
                    'INP_CLIENT_GRP_CLIENTS': self._workflow_client,
                    'INP_MEDIA_AGENTS_LIST': self._workflow_ma
                }
            )

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
