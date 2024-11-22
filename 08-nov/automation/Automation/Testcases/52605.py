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

    """Class for validating Run as API Mode"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Run as API Mode"
        self._workflow = None
        self.workflow_name = 'WF_EMAILAPI'

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self.commcell_machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            self.log.info("1. Running workflow using REST API :  (POST) /wapi/{workflowName")
            _ = self._workflowhelper.execute_api(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                })

            self.log.info("2. Running workflow using REST API :  (GET) /wapi/{workflowName")
            _ = self._workflowhelper.execute_api(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                }, method_type ='GET')

            self.log.info("3. Running workflow using REST API :  (POST)  /Workflow/{workflowName}/Action/Execute")
            _ = self._workflowhelper.execute_api(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                }, api='EXECUTE_WORKFLOW_API')

            self.log.info("4. Running workflow using using qcommand")
            self.commcell_machine.execute_command(r'qoperation exxecute -af "C:\wfexecute.xml"')

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
