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
from AutomationUtils.machine import Machine
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating undeploying workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate undeploy workflow script"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_EMAIL'
        self.sqlobj = None
        self._utility = OptionsSelector(self._commcell)
        self.tcinputs = {
            'script_location': None,
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name, deploy=True)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)
        if not self.machine.check_file_exists(self.tcinputs['script_location'] + "/RemoveWorkflowDeployment.sqle"):
            raise Exception("Script file is not present in script location")

    def run(self):
        """Main function of this testcase execution"""
        try:

            script_location = self.tcinputs['script_location'] + "/RemoveWorkflowDeployment.sqle"
            self.log.info("Running the qscript RemoveWorkflowDeployment to undeploy the workflow")
            command = r"qscript -f '{0}' -i {1} -i {2}".format(script_location, self.commcell.commserv_name,
                                                               self.workflow_name)
            self.machine.execute_command(command)

            self.log.info("Check whether pending workflow job is killed with the script")

            if not self._workflowhelper.is_deployed(workflow_name=self.workflow_name, hardcheck=False):
                raise Exception("job is still in pending state")

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
