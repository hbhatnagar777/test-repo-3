# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 53533

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

    """Class for validating Modifying timeout value"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Modifying timeout value"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_SETTIMEOUT'
        self._utility = OptionsSelector(self._commcell)
        self.sqlobj = None

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            workflow_job_obj = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                }, wait_for_job=False)

            workflow_jobmgr_obj = JobManager(workflow_job_obj)
            workflow_jobmgr_obj.wait_for_state(expected_state="failed")
            if not "exceeded the timeout period of [1] minutes" in workflow_job_obj.delay_reason:
                raise Exception("Job didnt fail due to timeout reason")



        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
