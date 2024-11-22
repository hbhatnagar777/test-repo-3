# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51502

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

    """Class for validating the output return by the embedded workflow in the parent workflow when
        executed as separate job """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate the output return by the embedded workflow in the parent workflow\
                     when executed as separate job"
        self._workflow = None
        self.workflow_name = 'WF_Parent'
        self.embeddedworkflow_name = 'WF_EmbeddedScript'

    def setup(self):
        """Setup function of this test case"""
        self._embeddedworkflowhelper = WorkflowHelper(self, self.embeddedworkflow_name)
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            _ = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                })


        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
            self._embeddedworkflowhelper.cleanup()
