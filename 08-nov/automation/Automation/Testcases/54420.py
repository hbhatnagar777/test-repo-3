# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      -- initialize TestCase class

    setup()         -- initial settings for the test case

    run()           -- run function of this test case
"""

from datetime import datetime, timezone
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from Server.Scheduler.schedulepolicyhelper import SchedulePolicyHelper
from Server.Scheduler import schedulerhelper


class TestCase(CVTestCase):
    """Class for executing JobStartTime Check test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Test Case for Client JobStartTime - Daily Schedule"
        self.log = None
        self.show_to_user = False
        self.csdb = None
        self.machine_obj = None
        self.utility = None
        self.schedule_policy = None
        self.schedule_creator = None
        self.windows_client = None
        self.new_plan = None
        self.plan_name = None
        self.taskname = None
        self.backupset_name = None
        self.job_id = None
        self.job_object = None
        self.tcinputs = {
            "ClientName": None,
            "StoragePoolName": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.machine_obj = Machine(self.tcinputs["ClientName"])
        self.utility = OptionsSelector(self.commcell)
        self.schedule_policy = SchedulePolicyHelper(self.commcell)
        self.schedule_creator = schedulerhelper.ScheduleCreationHelper(self)
        self.windows_client = self.commcell.clients.get(self.tcinputs['ClientName'])

    def run(self):
        """Follows the following steps
        1) Create a plan with 24 hour RPO
        2) Retrieve plan's associated Schedule Policy Name & Id
        3) Delete "Continuous Incremental" schedule from Schedule Policy
        4) Calculate & Update JobStartTime for Client to 15 min wrt current time
        5) Add a daily Schedule with "ClientTimeZone" & Start time set to 10 min wrt current time
        6) Create a backupset for client with the plan associated
        7) Check if any jobs are trigerred for the default subclient of the created backupset
        8) Wait 20 min for job initiation before Failing the Test Case
        """

        try:

            self.plan_name = "plan{0}".format(datetime.now())
            self.log.info("Step 1: Creating plan: %s", self.plan_name)

            self.new_plan = self.commcell.plans.add(
                self.plan_name, 'Server', self.tcinputs["StoragePoolName"], 1440
            )

            self.log.info("Step 2: Retrieving plan's associated Schedule Policy Name")
            self.taskname = self.new_plan.schedule_policies

            self.schedule_policy.schedule_policy_obj = self.commcell.schedule_policies \
                .get(self.taskname)

            self.log.info("Step 3: Deleting 'Continuous Incremental' schedule from Schedule Policy")
            self.schedule_policy.delete_schedule_from_policy(
                schedule_name='Continuous Incremental')

            time_on_machine = self.machine_obj.get_system_time().split(':')
            job_start_time_value = (int(time_on_machine[0])*60*60) + \
                                   (int(time_on_machine[1])*60) + 900
            self.log.info("Updated Job Start time: %s", job_start_time_value)

            self.log.info("Step 4: Updating JobStartTime for Client: %s",
                          (self.tcinputs['ClientName']))
            self.windows_client.set_job_start_time(job_start_time_value)

            self.log.info("Step 5: Adding daily Schedule to Schedule policy...")
            schedule_start_time = str(self.machine_obj.add_minutes_to_system_time(10).strip())
            self.log.info("Schedule created with Start time: %s", schedule_start_time)

            self.schedule_policy.add_schedule_to_policy({
                'pattern':
                    {'schedule_name': self.plan_name,
                     'active_start_time': schedule_start_time,
                     'time_zone': 'Client Time Zone'},
                'options':
                    {'backupLevel': 'Full'}})

            if not self.windows_client.is_ready:
                self.log.error("        Check readiness for the windows client failed")

            self.backupset_name = self.plan_name
            self.agent.backupsets.add(backupset_name=self.backupset_name, plan_name=self.plan_name)

            self.utility.sleep_time(900)
            self.log.info("Step 6: Check if any jobs got trigerred for "
                          "default subclient of the created backupset")

            sch_obj = self.client.schedules.get(self.plan_name)
            sch_helper = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)

            job_id_list = sch_helper.check_job_for_taskid(retry_count=10, retry_interval=60)
            self.job_id = ((str(job_id_list[0])).split("\""))[1]
            self.job_object = self.commcell.job_controller.get(self.job_id)

            if self.job_object.backupset_name != self.backupset_name:
                raise Exception("Job did not get triggered for BackupSet as"
                                " per JobStartTime set at client level")

            job_start_time_obj = datetime.strptime(self.job_object.start_time, '%Y-%m-%d %H:%M:%S')
            job_start_time_obj = job_start_time_obj.replace(tzinfo=timezone.utc).astimezone(tz=None)
            job_time = ((job_start_time_obj.time()).strftime('%H:%M')).split(':')
            actual_job_start_time = (int(job_time[0]) * 60 * 60) + (int(job_time[1]) * 60)

            if actual_job_start_time >= job_start_time_value:
                self.log.info("Validation: Job got triggered as per the"
                              " Job Start Time set at client level")
            else:
                raise Exception("Job did not get triggered as per JobStartTime set at client level")

        except Exception as exp:
            self.log.error(str(exp))
            self.log.error("Test Case FAILED")
            self.status = constants.FAILED
            self.result_string = str(exp)

        finally:
            if self.job_object.status.lower() in ['running', 'queued', 'waiting', 'suspended']:
                try:
                    self.job_object.kill()
                    self.utility.sleep_time(60)
                    self.agent.backupsets.delete(self.backupset_name)
                    self.commcell.plans.delete(self.plan_name)
                    self.log.info("Entity cleanup succeeded...")
                except Exception as exp:
                    self.log.error(str(exp))
                    self.log.error("Entity cleanup failed - "
                                   "delete testcase created entities manually.")
