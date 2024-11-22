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
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.database_helper import MSSQL
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating autoRestarts of Workflow job"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Workflow - registry key to enable/disable auto restart of workflow jobs"
        self._workflow = None
        self.workflow_name = 'WF_FOREACH_JSON'
        self.tcinputs = {
            'SQLUserName': None,
            'SQLPassword': None
        }
        self.idautils = None
        self.job = None
        self.mssql = None

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)
        db_server = "{0}{1}".format(self.commcell.commserv_hostname, "\\Commvault")
        self.mssql = MSSQL(db_server, self.tcinputs['SQLUserName'], self.tcinputs['SQLPassword'], 'WFEngine')
        self.idautils = CommonUtils(self)

    def update_db(self, job_id):
        """Updates the status as 1 for a jobId in WF_Process table"""
        query = "update WF_Process set status=1 where jobId={0}".format(job_id)
        self.mssql.execute(query)
        self.log.info("Updated the status as 1 for workflow jobId [%s]", job_id)

    def modify_additional_settings(self, value='False'):
        """Updates the value of additional settings 'autoRestartJobs' """
        self.log.info("Updating the additional settings [autoRestartJobs] with value [%s]", value)
        self.idautils.modify_additional_settings('autoRestartJobs', value, 'WFEngine', 'BOOLEAN')

    def test_step(self, expect_suspend=True, autorestartjobs_value=False, additional_setting_require=False,
                  update_db=True):
        """Test steps"""
        self.job = self._workflow.execute({'INP_EMAIL_ID': self._workflow.email}, wait_for_job=False)
        self.log.info("JobId for workflow [%s] execution is %s", self.workflow_name, self.job.job_id)
        self.job.pause(wait_for_job_to_pause=True)
        job_id = self.job.job_id
        self.log.info("Workflow JobID %s is suspended", job_id)
        if update_db:
            self.update_db(job_id)
        if additional_setting_require:
            self.modify_additional_settings(value=autorestartjobs_value)
            self.commcell.commserv_client.restart_service("CVJavaWorkflow(Instance001)")
        self.log.info("Restarting WFEngine services")

        self.log.info("Initiating the process to sleep for 10 minutes")
        time.sleep(600)
        self.job.refresh()
        status = self.job.status
        self.log.info("After autorestarts interval(10 mins), the status of JobID [%s] is %s",
                      self.job.job_id, status)
        if expect_suspend:
            if 'Suspended' not in status:
                raise Exception("Expected the workflow jobID {0} to be in suspended state. Found status as {1}".
                                format(job_id, status))
            self.job.kill(wait_for_job_to_kill=True)
        else:
            if 'Suspended' in status:
                raise Exception("Expected the workflow jobID {0} to autorestarted. Found status as {1}".
                                format(job_id, status))

    def run(self):
        """Main function of this testcase execution"""
        try:

            self.log.info("*************************STEP 1 ****************************")
            self.log.info("Initialising the workflow [%s] job execution to validate"
                          "1. Suspend workflow job, update status as 1"
                          "2. Set additional setting value as True"
                          "3. After 10 minutes, the workflow job should be autorestarted (resume) ",
                          self.workflow_name)
            self.test_step(expect_suspend=False, autorestartjobs_value='True', additional_setting_require=True)

            self.idautils.delete_additional_settings('autoRestartJobs', 'WFEngine')
            self.log.info("*************************STEP 2 ****************************")
            self.log.info("Initialising the workflow [%s] job execution to validate"
                          "1. Suspend workflow job, update status as 1"
                          "2. After 10 minutes, the workflow job shouldnt be autorestarted (resume) ",
                          self.workflow_name)
            self.test_step(expect_suspend=True, autorestartjobs_value='False', additional_setting_require=False)

            self.log.info("*************************STEP 3 ****************************")
            self.log.info("Initialising the workflow [%s] job execution to validate"
                          "1. Suspend workflow job, update autoRestartJobs as True"
                          "2. After 10 minutes, the workflow job shouldnt be autorestarted (resume) ",
                          self.workflow_name)
            self.test_step(expect_suspend=True, autorestartjobs_value='True', additional_setting_require=True,
                           update_db=False)

            self.job = None

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
            if self.job:
                self.job.kill(wait_for_job_to_kill=True)
            if self.idautils:
                self.idautils.delete_additional_settings('autoRestartJobs', 'WFEngine')
