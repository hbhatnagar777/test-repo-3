# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51559

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

    """Class for validating import workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Import workflow"
        self._workflow = None
        self.workflow_name = 'WF_EMAIL'
        self.tcinputs = {
            'EmailId': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=False)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.log.info("Importing and Deploying the workflow [%s]", self.workflow_name)
            self._workflow.deploy()
            self._workflow.execute(
                {'INP_EMAIL_ID': self.tcinputs['EmailId'],
                 'INP_WORKFLOW_NAME': self.workflow_name}
            )

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
