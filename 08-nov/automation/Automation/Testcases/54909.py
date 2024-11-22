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
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validate Client Entity as input"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Client Entity as input"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_CLIENTENTITY'
        self.sqlobj = None
        self._utility = OptionsSelector(self._commcell)
        self.tcinputs = {"client1": None, "client2": None}

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name, deploy=False)

    def run(self):
        """Main function of this testcase execution"""
        try:

            self._workflowhelper.deploy()
            clientlist = [self.tcinputs['client1'], self.tcinputs['client1']]
            workflow_job_obj = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'ClientInput': self.tcinputs['client1'],
                    'ClientList': clientlist
                }
                )

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
