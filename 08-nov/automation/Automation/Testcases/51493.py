# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51493

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating Impersonate Login,TransferToken activity"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Impersonate Login,TransferToken activity"
        self._workflow = None
        self.workflow_name = 'WF_TRANSFERTOKEN'
        self.tcinputs = {
            'regcommcell': None,
            'regcommcelluser': None,
            'regcommcellpass': None

        }

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            _ = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'regcommcell': self.tcinputs['regcommcell'],
                    'regcommcelluser': self.tcinputs['regcommcelluser'],
                    'regcommcellpass': self.tcinputs['regcommcellpass'],
                })

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
