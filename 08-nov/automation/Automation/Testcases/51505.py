# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 52605

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating HTTPClient activity"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate HTTPCLient activity"
        self._workflow = None
        self.workflow_name = 'WF_HTTPCLIENT'

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self.commcell_machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.log.info("adding registry under commserver")

            self.commcell_machine.update_registry('WFEngine', value='UseHTTPProxy', data=1, reg_type='DWord')

            _ = self._workflowhelper.execute(
                 {
                     'INP_WORKFLOW_NAME': self.workflow_name,
                 })


        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
            self.commcell_machine.remove_registry(key='WFEngine', value='UseHTTPProxy')
