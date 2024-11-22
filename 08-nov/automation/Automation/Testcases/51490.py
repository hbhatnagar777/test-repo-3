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
from Server.JobManager.jobmanager_helper import JobManager

class TestCase(CVTestCase):

    """Class for validating Clean KillPending Workflow jobs"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Clean KillPending Workflow jobs script"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_ONWORKFLOWCOMPLETE'
        self.sqlobj = None
        self._utility = OptionsSelector(self._commcell)
        self.tcinputs = {
            'script_location': None,
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name, deploy=False)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)
        if not self.machine.check_file_exists(self.tcinputs['script_location'] + "/RemoveStaleWorkflowJob.sqle"):
            raise Exception("Script file is not present in script location")

    def run(self):
        """Main function of this testcase execution"""
        try:

            self._workflowhelper.deploy()
            workflow_job_obj = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name}, wait_for_job=False
                )
            # Check for pending state
            workflow_jobmgr_obj = JobManager(workflow_job_obj)
            workflow_jobmgr_obj.wait_for_state(expected_state="pending")

            script_location = self.tcinputs['script_location'] + "/RemoveStaleWorkflowJob.sqle"
            self.log.info("Running the qscript RemoveStaleWorkflowJob.sql to kill pending jobs")
            command = r"qscript -f '{0}' -i {1}".format(script_location, workflow_job_obj.job_id)
            self.machine.execute_command(command)

            self.log.info("Check whether pending workflow job is killed with the script")

            if workflow_job_obj._is_valid_job():
                raise Exception("job is still in pending state")


        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()