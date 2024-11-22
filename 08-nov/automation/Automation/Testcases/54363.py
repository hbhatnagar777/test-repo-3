# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 54363

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

    """Class for validating testcase of ForEachJSON activity"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[WORKFLOW] Validate ForEachJson activity"
        self._workflow = None
        self.workflow_name = 'WF_FOREACH_JSON'
        self.tcinputs = {
            'EmailId': None
        }

    def setup(self):
        """Setup function of this testcase"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)

    def run(self):
        """Main function of this testcase"""
        try:
            # start workflow execution
            self._workflow.execute(
                {'INP_EMAIL_ID': self.tcinputs['EmailId']}
            )

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
