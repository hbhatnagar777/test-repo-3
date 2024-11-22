# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51500

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
import os
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating onworkflowcomplete utility with job killed"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate the OnWorkflowComplete execution with the workflow job killed"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_ONWORKFLOWCOMPLETE'
        self._utility = OptionsSelector(self._commcell)
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=False)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            testfile_location = os.path.join(constants.AUTOMATION_DIRECTORY, constants.TEMP_DIR,
                                             self._id)
            self._utility.create_directory(self.machine, testfile_location)
            self._workflow.deploy()
            workflow_job_obj = self._workflow.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name}, wait_for_job=False
            )
            workflow_jobmgr_obj = JobManager(workflow_job_obj)
            workflow_jobmgr_obj.wait_for_state(expected_state="pending")
            workflow_jobmgr_obj.modify_job("kill")
            self.log.info("Validate whether Onworkflowcomplete script executed or not")
            if not self.machine.check_file_exists(testfile_location + r"\wftest.txt"):
                raise Exception("OnWorkflowComplete script didnt complete")

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
            self._utility.remove_directory(self.machine, testfile_location)
