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
    """Class for modifying filters and commcell storage entities through
    Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Modify global filters, storage policies and commvault entities"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.tcinputs = {
            'VaultTrackerPolicyName': None,
            'ExportLocation': None,
        }

        # Inherited class attributes
        self._workflow = None
        self._workflow_client = None
        self._workflow_client1 = None
        self._workflow_ma = None
        self._test_req = ("""Test case requirements not met.
                            Input 1. Vault tracker policy name
                            Input 2. Export location
                            Req 1: Two clients required to assign while creating
                                    schedule and adding to schedule
                            Req 2. Media agent client""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_modify")

        # Get smart inputs for the Workflow
        clients = self._workflow.database.get_client(num=2)
        if self.client.client_name is None or self.client.client_id == 2:
            self._workflow_client = clients[0]
        else:
            self._workflow_client = self.client.client_name

        self._workflow_client1 = clients[1]
        self._workflow_ma = self._workflow.database.get_ma('disk')

        if self._workflow_client is None or self._workflow_ma is None:
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:

            # Start workflow execution
            self._workflow.execute(
                {
                    'INP_SPCOPY_MEDIAAGENT' : self._workflow_ma,
                    'INP_SCHPOL_CLIENT_CREATE' : self._workflow_client,
                    'INP_SCHPOL_CLIENT' : self._workflow_client1,
                    'INP_CLIENT_SUBC' : self.commcell.commserv_name,
                    'INP_RUN_VTP' : "true",
                    'INP_VAULT_TRACKER_POLICY' : self.tcinputs['VaultTrackerPolicyName'],
                    'INP_LOCATION_NAME' : self.tcinputs['ExportLocation'],
                }
            )

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
