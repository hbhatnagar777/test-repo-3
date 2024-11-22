# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating Clone workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Clone a workflow"
        self._workflow = None
        self.workflow_name = 'WF_EMAIL'
        self.clone_workflow_name = None
        self.clone_workflow = None
        self.tcinputs = {
            'EmailId': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)

    def run(self):
        """Main function of this testcase execution"""
        try:
            utility = OptionsSelector(self.commcell)
            self.clone_workflow_name = utility.get_custom_str(presubstr=str(self.id))
            self.log.info("Cloning workflow %s with name as %s", self.workflow_name,
                          self.clone_workflow_name)
            self.log.info("Initialising the clone workflow")
            self._workflow.clone(self.clone_workflow_name)
            self.log.info("Successfully cloned the workflow with workflow name [%s]",
                          self.clone_workflow_name)
            self.commcell.refresh()
            self.clone_workflow = WorkflowHelper(self, self.clone_workflow_name, deploy=False)
            self.clone_workflow.deploy_workflow()
            self.log.info("Initialising to execute the cloned workflow %s", self.clone_workflow_name)
            self.clone_workflow.execute(
                {'INP_EMAIL_ID': self.tcinputs['EmailId'],
                 'INP_WORKFLOW_NAME': self.clone_workflow_name})
            self.log.info("Successfully executed the cloned workflow")
        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)
        finally:
            self._workflow.delete(self.workflow_name)
            self._workflow.delete(self.clone_workflow_name)
