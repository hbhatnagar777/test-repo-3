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
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper, SchedulerHelper
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for validating WORKFLOW - Schedules"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Schedules"
        self.workflow_name = "WF_NEWWORKFLOW"
        self.wf_helper = None
        self.del_schedule = None

    def scheduler(self, schedule_pattern, type_):
        """ Method to create a schedule and validate it"""
        sch_obj = self.wf_helper.schedule_workflow(schedule_pattern)
        self.log.info("Created schedule successfully for type %s", type_)

        job_obj = SchedulerHelper(sch_obj, self.commcell).check_job_for_taskid(
            retry_count=3, retry_interval=45, workflow_task=True)
        self.del_schedule.cleanup_schedules(sch_obj)
        if not JobManager(_job=job_obj[0], commcell=self.commcell).wait_for_state(time_limit=60):
            raise Exception("Job did not succeed for type %s", type_)
        self.log.info("Schedule Validated Successfully for type %s", type_)

    def one_time_scheduler(self):
        """Scheduler method for type one_type"""
        type_ = "one_time"
        self.log.info("Creating schedule with 'one time' frequency")
        schedule_pattern = {
            "freq_type": "one_time",
            "active_start_time": (datetime.today().astimezone(pytz.utc)
                                  + timedelta(minutes=2)).strftime("%H:%M"),
            "time_zone": "UTC"
        }
        self.scheduler(schedule_pattern, type_)

    def daily_scheduler(self):
        """Scheduler method for type daily"""
        type_ = "daily"
        self.log.info("Creating schedule with 'daily' frequency")
        schedule_pattern = {
            "freq_type": "daily",
            "active_start_date": (datetime.today().astimezone(pytz.utc)
                                  + timedelta(minutes=2) - timedelta(days=1)).strftime("%m/%d/%Y"),
            "active_start_time": (datetime.today().astimezone(pytz.utc)
                                  + timedelta(minutes=2) - timedelta(days=1)).strftime("%H:%M"),
            "time_zone": "UTC"
        }
        self.scheduler(schedule_pattern, type_)

    def weekly_scheduler(self):
        """Scheduler method for type weekly"""
        type_ = "weekly"
        self.log.info("Creating schedule with 'weekly' frequency")
        schedule_pattern = {
            "freq_type": "weekly",
            "active_start_date": (datetime.today().astimezone(pytz.utc)
                                  + timedelta(minutes=2) - timedelta(days=7)).strftime("%m/%d/%Y"),
            "active_start_time": (datetime.today().astimezone(pytz.utc)
                                  + timedelta(minutes=2) - timedelta(days=7)).strftime("%H:%M"),
            "time_zone": "UTC",
            "weekdays": [datetime.now().strftime("%A")]
        }
        self.scheduler(schedule_pattern, type_)

    def monthly_scheduler(self):
        """Scheduler method for type monthly"""
        type_ = "monthly"
        self.log.info("Creating schedule with 'monthly' frequency")
        schedule_pattern = {
            "freq_type": "monthly",
            "active_start_date": (((datetime.today().astimezone(pytz.utc)
                                    + timedelta(minutes=2)).replace(day=1) - timedelta(days=1))
                                  .replace(day=datetime.today().astimezone(pytz.utc).day))
                                 .strftime("%m/%d/%Y"),
            "active_start_time": (((datetime.today().astimezone(pytz.utc)
                                    + timedelta(minutes=2)).replace(day=1) - timedelta(days=1))
                                  .replace(day=datetime.today().astimezone(pytz.utc).day))
                                 .strftime("%H:%M"),
            "time_zone": "UTC",
            "on_day": datetime.today().astimezone(pytz.utc).day
        }
        self.scheduler(schedule_pattern, type_)

    def yearly_scheduler(self):
        """Scheduler method for type yearly"""
        type_ = "yearly"
        self.log.info("Creating schedule with 'yearly' frequency")
        schedule_pattern = {
            "freq_type": "yearly",
            "active_start_date": (((datetime.today().astimezone(pytz.utc)
                                    + timedelta(minutes=2)) - timedelta(days=365))
                                  .replace(day=datetime.today().astimezone(pytz.utc).day))
                                 .strftime("%m/%d/%Y"),
            "active_start_time": (((datetime.today().astimezone(pytz.utc)
                                    + timedelta(minutes=2)) - timedelta(days=365))
                                  .replace(day=datetime.today().astimezone(pytz.utc).day))
                                .strftime("%H:%M"),
            "time_zone": "UTC",
            "on_day": datetime.today().astimezone(pytz.utc).day,
            "on_month": datetime.today().astimezone(pytz.utc).strftime("%B"),

        }
        self.scheduler(schedule_pattern, type_)

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)
        self.del_schedule = ScheduleCreationHelper(self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.wf_helper.test.log_step("""
                            1. Create a schedule for a workflow 
                            2. Validate if the schedule is triggered correctly
                            3. Delete the workflow and check if the schedule isn't triggered
                        """, 200)
            self.one_time_scheduler()
            self.daily_scheduler()
            self.weekly_scheduler()
            self.monthly_scheduler()
            self.yearly_scheduler()
            self.log.info("Verifying if schedule doesnt kick after deletion of workflow")
            self.log.info("Creating a schedule for the workflow")
            self.log.info("Creating with 'one time' frequency")
            schedule_pattern = {
                "freq_type": "one_time",
                "active_start_time": (datetime.today().astimezone(pytz.utc)
                                      + timedelta(minutes=2)).strftime("%H:%M"),
                "time_zone": "UTC"
            }
            sch_obj = self.wf_helper.schedule_workflow(schedule_pattern)
            self.log.info("Created schedule successfully")
            self.log.info("Deleting the workflow")
            self.wf_helper.delete(self.workflow_name)
            job_obj = SchedulerHelper(sch_obj, self.commcell).check_job_for_taskid(
                retry_count=4, retry_interval=45, workflow_task=True)
            if job_obj:
                raise Exception("Job initiated for deleted workflow ")
            self.log.info("Schedule did not kick in after deletion of workflow")

        except Exception as exp:
            self.wf_helper.test.fail(exp)

        finally:
            self.wf_helper.delete(self.workflow_name)
