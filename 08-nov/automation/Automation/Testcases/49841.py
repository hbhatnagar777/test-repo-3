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
    """Class for executing library related operations through Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Perform library related operations through activities "
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True

        # Inherited class attributes
        self._workflow = None
        self._workflow_ma = None
        self._test_req = ("""Test case requirements not met.
                            Req 1. Client with windows media agent installed""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_library_operations")

        # Fetch smart inputs for the workflow
        self._workflow_ma = self._workflow.database.get_ma('windows')

        if not self._workflow_ma:
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:
            # Start workflow execution
            self._workflow.execute({'INP_MEDIA_AGENT' : self._workflow_ma})

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
