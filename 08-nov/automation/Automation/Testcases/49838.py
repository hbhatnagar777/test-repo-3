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
    """Class for executing backup/restore and data management related operations
     through Workflow activities """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Perform backup/restore and data validation"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True

        # Inherited class attributes
        self._workflow = None
        self._workflow_ma = None
        self._test_req = ("""Test case requirements not met
                               Req 1. Media agent client is required to create
                                   storage entities""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_qcommand_operations")

        self._workflow_ma = self._workflow.database.get_ma('windows')

        if not self._workflow_ma:
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:

            # Start workflow execution
            self._workflow.execute(
                {
                    'INP_MEDIA_AGENT': self._workflow_ma,
                    'INP_MEDIA_AGENT_SP': self._workflow_ma,
                    'INP_LIBRARY_MEDIA_AGENT': self._workflow_ma,
                    'INP_SPCOPY_MEDIA_AGENT': self._workflow_ma,
                    'INP_CLIENT_BKPSET': self.commcell.commserv_name,
                    'INP_CLIENT_SUBC': self.commcell.commserv_name,
                    'INP_CLIENT_BKPSET_DELETE': self.commcell.commserv_name,
                    'INP_ENCRYPT_CLIENT': self.commcell.commserv_name,
                    'INP_SET_ENCRYPTION_PROPS': "false",
                }
            )

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()