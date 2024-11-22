# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51557

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

    """Class for validating Disable workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Disable a Commcell workflow"
        self._workflow = None
        self.workflow_name = 'WF_EMAIL'
        self.tcinputs = {
            'EmailId': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self._workflow.disable_workflow()
            try:
                self.log.info("Executing disabled workflow [%s]", self.workflow_name)
                self._workflow.execute(
                    {'INP_EMAIL_ID': self.tcinputs['EmailId'],
                     'INP_WORKFLOW_NAME': self.workflow_name}
                )
                self.log.info("Expected the execution of disabled workflow to fail")
                raise Exception("Execution of disabled workflow is succeed. Expected to fail")
            except Exception as excp:
                if 'workflow disabled' in str(excp):
                    self.log.info("Execution of disabled workflow failed as expected")
                else:
                    raise Exception(excp)
            self._workflow.enable_workflow()
            self.log.info("Executing enabled workflow [%s]", self.workflow_name)
            self._workflow.execute(
                {'INP_EMAIL_ID': self.tcinputs['EmailId'],
                 'INP_WORKFLOW_NAME': self.workflow_name}
            )

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
