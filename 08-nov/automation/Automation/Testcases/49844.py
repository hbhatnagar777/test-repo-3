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
    """Class for executing workflow test case"""

    def __init__(self):
        """Class for validating CDR replication through Workflow activities"""
        super(TestCase, self).__init__()
        self.name = "Perform file replication through CDR operations"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.tcinputs = {
            'SourceClient' : None,
            'DestinationClient' : None,
        }

        # Inherited class attributes
        self._workflow = None
        self._test_req = ("""Test case requirements not met.
                            Input 1. Source client with CDR package installed
                            Input 2. Destination Client with CDR package
                                        installed""")

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_replication")

        if (self.tcinputs.get('SourceClient') is None or \
                self.tcinputs.get('DestinationClient') is None):
            raise Exception(self._test_req)

    def run(self):
        """Main function for test case execution"""

        try:
            # Start workflow execution
            self._workflow.execute(
                {
                    'INP_REP_SOURCE_CLIENT' : self.tcinputs['SourceClient'],
                    'INP_DESTINATION_HOST' : self.tcinputs['DestinationClient'],
                    'INP_DATA_AGENT' : "Q_FILE_REPLICATION",
                }
            )

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
