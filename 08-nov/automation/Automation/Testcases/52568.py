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
from datetime import datetime, timedelta
import pytz
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.Scheduler.schedulerhelper import SchedulerHelper, ScheduleCreationHelper
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):

    """Class for validating WORKFLOW - Validate Reassociation of workflow schedules - Daily"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Reassociation of workflow schedules - Daily"
        self.old_workflow_name = "WF_OLDWORKFLOW"
        self.new_workflow_name = "WF_NEWWORKFLOW"
        self.wf_helper_old = None
        self.wf_helper_new = None
        self.sch_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper_old = WorkflowHelper(self, wf_name=self.old_workflow_name)
        self.wf_helper_new = WorkflowHelper(self, wf_name=self.new_workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.log.info("Creating schedule with 'daily' frequency")
            schedule_pattern = {
                "freq_type": "daily",
                "active_start_date": (datetime.today().astimezone(pytz.utc)
                                      + timedelta(minutes=2)-timedelta(days=1)).strftime("%m/%d/%Y"),
                "active_start_time": (datetime.today().astimezone(pytz.utc)
                                      + timedelta(minutes=2)-timedelta(days=1)).strftime("%H:%M"),
                "time_zone": "UTC"
            }
            self.sch_obj = self.wf_helper_old.schedule_workflow(schedule_pattern)
            self.log.info("Created schedule successfully for type daily")
            self.commcell._qoperation_execscript(
                "-sn reassociateWorkflowSchedules -si {0} -si {1}".
                format(self.old_workflow_name, self.new_workflow_name))
            job_obj = SchedulerHelper(self.sch_obj, self.commcell).check_job_for_taskid(
                retry_count=3, retry_interval=45, workflow_task=True)
            if not JobManager(_job=job_obj[0], commcell=self.commcell).wait_for_state(time_limit=60):
                raise Exception("Job did not succeed for type daily")
            if job_obj[0].job_type.lower() != self.new_workflow_name.lower():
                raise Exception("Reassociation did not succeed")
            self.log.info("Schedule Validated Successfully for type daily")

        except Exception as exp:
            self.wf_helper_old.test.fail(exp)

        finally:
            self.wf_helper_old.delete([self.old_workflow_name, self.new_workflow_name])
            ScheduleCreationHelper(self.commcell).cleanup_schedules(self.sch_obj)
