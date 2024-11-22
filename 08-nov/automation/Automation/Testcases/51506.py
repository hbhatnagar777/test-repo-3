# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51490

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

    """Class for validating Encrypted String input"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Encrypted String input"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_COMPARE_ENCRYPTED_STRING'
        self.sqlobj = None

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name, deploy=False)


    def run(self):
        """Main function of this testcase execution"""
        try:
            self.log.info("Exporting and Deploying the workflow [%s]", self.workflow_name)

            # true case
            password_1 = '3a28e69ab3084fa9b7b7d8d4939b655ef'
            password_2 = password_1

            self._workflowhelper.deploy()
            workflow_job_obj = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'password_1': str(password_1),
                    'password_2': str(password_2)}
                )
            self._workflowhelper.cleanup()
            self._workflowhelper = WorkflowHelper(self, self.workflow_name)
            # False case
            password_1 = '3a28e69ab3084fa9b7b7d8d4939b655ef'
            password_2 = '3fc7db51c802230cab5b805a58d49991d'

            workflow_job_obj = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'password_1': str(password_1),
                    'password_2': str(password_2)},
                wait_for_job=False
            )

            self.log.info("Check whether job status is failed or completed")
            workflow_job_obj.wait_for_completion()

            if workflow_job_obj.status.lower() != 'failed':
                raise Exception("Validation of comparision is wrong")


        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
