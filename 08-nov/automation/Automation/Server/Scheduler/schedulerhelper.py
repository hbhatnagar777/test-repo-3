# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Main file for performing schedule related operations for client/agent/backupset/subclient.

ScheduleCreationHelper: Schedule Creation helper class to perform creation and deletion operations

ScheduleCreationHelper:
__init__(class_object)                              --  initialise object of the
                                                            ScheduleCreationHelper class

add_minutes_to_datetime()                           -- adds minutes to the time provided and
                                                         returns based on the return format

create_schedule()                                   --  creates a schedule

cleanup_schedules()                                 -- cleans up the schedules created as part of
                                                       object and also the ones in the input

get_random_tzone()                                  -- Gets a random timezone

cleanup_steps()                                     -- Cleanup Steps for Scheduler Automation cases

cleanup()                                           -- cleans up the scheduler CS machine

entities_setup()                                    -- entities setup for scheduler.

ScheduleHelper: scheduler helper class to perform schedule related operations

SchedulerHelper:
    __init__(class_object)                              --  initialise object of the
                                                            SchedulerHelper class

    check_job_for_taskid(retry_count, retry_interval)   -- checks if JobId is present for the
                                                            taskId provided and returns Job Obj

    get_jobid_from_taskid()                             -- gets JobId for given taskId

    continuous_schedule_wait()                          -- waits for the continuous schedule's
                                                           Jobs upto the job count specified

    automatic_schedule_wait()                          -- waits for the automatic schedule's
                                                           Job

    get_latest_job()                                    -- returns Job object of the latest
                                                           schedule

"""
import datetime
import inspect
import calendar
import math

import pytz
from dateutil.relativedelta import *
from cvpysdk.exception import SDKException
from cvpysdk.schedules import Schedules, Schedule
from AutomationUtils import logger, options_selector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from AutomationUtils import config
from Install.install_helper import InstallHelper
from .schedulerconstants import *


class ScheduleCreationHelper(object):
    """Class for Schedule Creation"""

    def __init__(self, init_object):

        """
        Initialises the ScheduleCreationHelper class with the commcell_object
        """

        self.log = logger.get_log()
        self._init_object = init_object
        self.common_utils = CommonUtils(self._init_object)
        self.commcell = self.common_utils._commcell
        self.job_manager = self.common_utils.job_manager
        self.sch_id_list = []
        self.config_json = config.get_config()
        if self.config_json.Schedule.cs_machine_uname and self.config_json.Schedule.cs_machine_password:
            self.cs_machine_obj = Machine(self.commcell.commserv_client.client_hostname,
                                          username=self.config_json.Schedule.cs_machine_uname,
                                          password=self.config_json.Schedule.cs_machine_password)
        else:
            self.log.info('Missing properties [cs_machine_uname, cs_machine_password] for key "Schedule"'
                          ' in config.json. Creating Machine object using commserv_client obj')
            self.cs_machine_obj = Machine(self.commcell.commserv_client)

        self._utility = options_selector.OptionsSelector(self.commcell)
        self._install = InstallHelper(self.commcell)

    @staticmethod
    def add_minutes_to_datetime(time=None, minutes=2):
        """ adds minutes to the time provided and returns based on the return format"""

        if not time:
            time = datetime.datetime.utcnow()
        return ((time.strftime('%m/%d/%Y')),
                (time + datetime.timedelta(minutes=minutes)).strftime('%H:%M'))

    def create_schedule(self, operation, schedule_pattern=None, wait=True, wait_time=120,
                        **kwargs):
        """
        Creates schedule for the provided operation and schedule_pattern
        Args:
            operation  (str) -- operation to be provided

                                All operations in idautils.CommUtils are supported
                                operations: 'subclient_backup','subclient_in_place_restore',
                                            'subclient_out_of_place_restore'

            schedule_pattern  (dict) -- schedule pattern for which the schedule should be created

            wait  (Bool) -- if set to True will wait for the job to trigger

            wait_time  (int) --  Time in seconds until which it waits before checking if a
                                 job is triggered

            **kwargs: All needed inputs for the operation type according to the sdk functions

        Returns: SchedulerHelper Object will be returned to perform
                                         tasks on existing schedules

        Raises:
                Exception if:
                    - failed during execution of module
                      Job not triggered for the schedule in case wait is set to True

        """
        try:
            # # Check if Commserv client is linux
            # if(self.commcell.is_linux_commserv and 'time_zone' in schedule_pattern.keys()):
            #     # Replace time_zone key in schedule pattern with timezone for the commserv client
            #     if(schedule_pattern['time_zone'] == 'UTC'):
            #         schedule_pattern['time_zone'] = SCHEDULER_TIMEZONES['GMT Standard Time']
            #         # Europe/London time is 1 Hour ahead of UTC so add 60 minutes to start_time to cover the lag
            #         new_active_start_time = self.add_minutes_to_datetime(minutes=62)[1]
            #         schedule_pattern['active_start_time'] = new_active_start_time

            schedule_obj = getattr(self.common_utils,
                                   operation.lower())(schedule_pattern=schedule_pattern, **kwargs)
            self.sch_id_list.append(schedule_obj)
            if wait:
                scheduler_helper_obj = SchedulerHelper(schedule_obj, self.commcell)
                # here we need to wait for the time duration post which the job will trigger as currently we start
                # looking for jobs instantly.
                time = schedule_pattern.get("job_interval", 0) * 60   # for continous schedules
                self.log.info(f"Pausing the testcase for {time/60} minutes so that we do not start looking for jobs "
                              f"way before they are triggered.")
                self._utility.sleep_time(time)
                jobs = scheduler_helper_obj.check_job_for_taskid(retry_interval=wait_time)
                if not jobs:
                    raise Exception("Job did not get triggered for the Schedule {0}".format(
                        schedule_obj.schedule_id))
                self.job_manager.job = jobs[0]
                self.common_utils.job_list.append(self.job_manager.job.job_id)
                self.job_manager.wait_for_state('completed')
            return schedule_obj

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def cleanup_schedules(self, schedule=None, hard_check=False):
        """
        Deletes the schedules created as part of this object and in addition the scheduleobjs
        provided

        Args:
            schedule (list) -- scheduleobjs or a single scheduleobj which needs to be deleted

            hard_check  (Bool) -- Boolean variable if set to true will throw exception for
                                  every delete failure, else will continue

        Raises:
                Exception if:
                    - failed during execution of module
        """

        try:
            if isinstance(schedule, list):
                for schedule_obj in schedule:
                    self.sch_id_list.append(schedule_obj)
            elif isinstance(schedule, Schedule):
                self.sch_id_list.append(schedule)

            if self.common_utils.job_list:
                self.common_utils.cleanup_jobs()

            schedules_obj = Schedules(self.commcell)
            for schedule in self.sch_id_list:
                if schedule.schedule_freq_type != 'One_Time':
                    try:
                        self.log.info("Deleting the schedule {0}".format(schedule.schedule_id))
                        schedules_obj.delete(schedule_id=schedule.schedule_id)
                        self.log.info("Successfully deleted the schedule {0}".format(schedule.
                                                                                     schedule_id))
                    except Exception as excp:
                        if not hard_check:
                            self.log.error("Schedule deletion error {0}".format(str(excp)))
                            continue
                        else:
                            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

        except Exception as excp:
            raise Exception("\n {0}".format(str(excp)))

    def get_random_tzone(self):
        """
        Get a Random SChedule Timezone and its python equivalent timezone
        Returns:
                Scheduler timezone and its python timezone equivalent
        """
        tz_query = "SELECT TOP 1 TimeZoneStdName FROM SchedTimeZone ORDER BY NEWID()"
        timezones, cur = self._utility.exec_commserv_query(tz_query)
        return timezones[0], SCHEDULER_TIMEZONES.get(timezones[0], timezones[0])

    def get_client_tzone(self, client):
        """

        Args:
            client: client object for which the timezone should be retrived

        Returns:
            Scheduler timezone and its python timezone equivalent

        """
        if(client._commcell_object.is_linux_commserv):
            tz_query = "SELECT WindowsTimeZoneStdName FROM SchedTimeZone where TimeZoneName='{0}'".format(client.timezone)
        else:
            tz_query = "SELECT TimeZoneStdName FROM SchedTimeZone where TimeZoneName='{0}'".format(client.timezone)
        timezones, cur = self._utility.exec_commserv_query(tz_query)
        return timezones[0], SCHEDULER_TIMEZONES.get(timezones[0], timezones[0])
    def cleanup_steps(self):
        if not self.commcell.is_linux_commserv:
            try:
                self.cs_machine_obj.toggle_time_service(stop=False)
            except Exception as e:
                if "The requested service has already been started" in str(e):
                    pass
                else:
                    raise e
        self.log.info("stopping Commcell Services")

        if(self.commcell.is_linux_commserv):
            self.cs_machine_obj.execute_command("sudo commvault stop")
            self._utility.sleep_time(20)
            # setting time to normal again as we move the time of the setup.
            self.log.info("syncing the time to reset it to the default timezone.")
            #sometimes because of repetetive time change operation the chronyc deamon crashes hence restart.
            self.cs_machine_obj.execute_command("sudo systemctl restart chronyd")
            self._utility.sleep_time()
            self.cs_machine_obj.execute_command("sudo chronyc makestep")
            self._utility.sleep_time(20)
            self.log.info("Deleting certificates directory")
            self._utility.update_commserve_db("update App_ClientCerts set status = 1 where clientId in (2,0)",
                                              user_name=self.config_json.Schedule.db_uname, password=self.config_json.Schedule.db_password)
            self.cs_machine_obj.remove_directory(self.cs_machine_obj.join_path(self.commcell.commserv_client.
                                                                               install_directory, "Base",
                                                                               "certificates"))
            self.log.info("restarting Commcell Services")
            # The Key isTimeShiftDetected is set by software and is dynamically set to 1 when we perform operations, we
            # need to make it as 0 just before starting the services.
            self.cs_machine_obj.execute_command("sudo sed -i 's/^isTimeShiftDetected.*/isTimeShiftDetected=0/' /etc/CommVaultRegistry/Galaxy/Instance001/Cvd/.properties")
            self.cs_machine_obj.execute_command("sudo commvault start")

        else:
            self.cs_machine_obj.execute_command(self.cs_machine_obj.join_path(self.commcell.commserv_client.
                                                                              install_directory, "Base", "GxAdmin.exe").
                                                replace(" ", "' '") + " -consoleMode -stopsvcgrp All -kill")
            self._utility.sleep_time()
            self.log.info("Deleting certificates directory")
            self._utility.update_commserve_db("update App_ClientCerts set status = 1 where clientId in (2,0)",
                                              self.config_json.Schedule.db_uname, self.config_json.Schedule.db_password)
            self.cs_machine_obj.remove_directory(self.cs_machine_obj.join_path(self.commcell.commserv_client.
                                                                               install_directory, "Base", "Certificates"))
            self.log.info("restarting Commcell Services")
            self.cs_machine_obj.execute_command(self.cs_machine_obj.join_path(self.commcell.commserv_client.
                                                                              install_directory, "Base", "GxAdmin.exe").
                                                replace(" ", "' '") + " -consoleMode -restartsvcgrp ALL")
        try:
            self._install.wait_for_services()
        except Exception as e:
            # added iisreset as sometime webserver is not in sync
            if not self.commcell.is_linux_commserv:
                self.cs_machine_obj.restart_iis()

        self.log.info("restarting again to see if cases run")
        if self.commcell.is_linux_commserv:
            self.cs_machine_obj.execute_command("sudo commvault restart")
        else:
            self.cs_machine_obj.execute_command(self.cs_machine_obj.join_path(self.commcell.commserv_client.
                                                                              install_directory, "Base", "GxAdmin.exe").
                                                replace(" ", "' '") + " -consoleMode -restartsvcgrp ALL")
        try:
            self._install.wait_for_services()
        except Exception as e:
            # added iisreset as sometime webserver is not in sync
            if not self.commcell.is_linux_commserv:
                self.cs_machine_obj.restart_iis()
            self._install.wait_for_services()
        self.log.info("Commcell Services restarted successfully")

    def cleanup(self):
        """cleans up the scheduler CS machine."""
        for count in range(0, 3):
            try:
                self.cleanup_steps()
                break
            except Exception as e:
                if count == 2:
                    raise e
                else:
                    self.log.info("Exception during cleanup so retrying" + str(e))
                    continue
        self.log.info("Commcell Services restarted successfully")

    def entities_setup(self, test_case_obj=None, client_name=None):
        """
        Creates required entities for scheduler automation
        Args:
            test_case_obj: (obj) -- test case object to be used for entity creation
            client_name: (str) -- name of the client on which entities have to be created if testcase obj is not passed

        Returns:
            (obj) --subclient object with the required entities

        """
        if not test_case_obj and not client_name:
            raise Exception("Either test_case_obj or client_name should be passed")
        self._entities = options_selector.CVEntities(self.commcell)
        if(self.commcell.is_linux_commserv):
            ready_ma = self._utility.get_ma('disk_linux')
        else:
            ready_ma = self._utility.get_ma()
        # create disk library
        entity_inputs = {
            'target':
                {
                    'client': test_case_obj.client.client_name if test_case_obj else client_name,
                    'agent': test_case_obj.agent.agent_name if test_case_obj else "File system",
                    'instance': test_case_obj.instance.instance_name if test_case_obj else "defaultinstancename",
                    'backupset': test_case_obj.backupset.backupset_name if test_case_obj else "defaultBackupSet",
                    'mediaagent': ready_ma
                },
            'disklibrary': {
                'name': "disklibrary_" + ready_ma,
                'mount_path': self._entities.get_mount_path(ready_ma),
                'cleanup_mount_path': True,
                'force': False,
            },
            'storagepolicy':
                {
                    'name': "storagepolicy_" + ready_ma,
                    'dedup_path': None,
                    'incremental_sp': None,
                    'retention_period': 3,
                    'force': False,
                },
            'subclient':
                {
                    'name': 'testSC' + (str(test_case_obj.id) if test_case_obj else ''),
                    'force': True
                }
        }
        return self._entities.create(entity_inputs)


class SchedulerHelper(object):
    """scheduler helper class to perform schedule related operations"""

    def __init__(self, schedule_object, commcell_object):

        """
        Initialises the schedulerhelper class with the schedule and commcell object

        Args:

            schedule_object  (object) -- Schedule Object returned from any operation

            commcell_object  (object) -- commcell Object of the schedules Commcell

        """

        self.schedule_object = schedule_object
        self._commcell_object = commcell_object
        self.log = logger.get_log()
        self.schedule_name = schedule_object.schedule_name
        if self.schedule_name == '':
            self.schedule_name = schedule_object.schedule_id
        self.schedule_task_id = schedule_object.task_id
        self.schedule_subtask_id = schedule_object.schedule_id
        self.schedule_pattern = eval("self.schedule_object.{0}".format(
            self.schedule_object.schedule_freq_type.lower()))
        self.__machine_obj = None

        self.jobs = []
        self._utility = options_selector.OptionsSelector(commcell_object)
        self.common_utils = CommonUtils(commcell_object)
        self.job_manager = self.common_utils.job_manager
        self.timezone = 'UTC'
        self.client_timezone = ScheduleCreationHelper(self._commcell_object).get_client_tzone(
            self._commcell_object.commserv_client)[1]

    @property
    def machine_obj(self):
        if self.__machine_obj is None:
            self.__machine_obj = Machine(self._commcell_object.commserv_client)
        return self.__machine_obj

    def check_job_for_taskid(self, retry_count=3, retry_interval=30, workflow_task=False):
        """
        This function checks if there is a jobid for the corresponding taskid provided.

        Args:

            retry_count  (int) -- the number of times the check operation should be retried

            retry_interval  (int) -- seconds frequency for the retry to happen

            workflow_task(bool) -- Set True if it is a workflow schedule

        Returns:

            Job object list if job found for task or Empty List.

        """

        self.log.info('Getting the JobId for the taskid: "{0}"'.format(self.schedule_name))
        for count in range(retry_count):
            self._utility.sleep_time(retry_interval)
            try:
                new_job = self.get_jobid_from_taskid(workflow_task)
                if new_job:
                    self.jobs.append(new_job)
                    break
            except Exception as excp:
                self.log.info(
                    'Waiting for backup job to kick off for schedule: "{0}"'.format(
                        self.schedule_name))
        if self.jobs:
            self.log.info('JobIds found for the schedule {0}'.format(self.jobs))
        else:
            self.log.info('No Jobs found for the schedule')
        return self.jobs

    def get_jobid_from_taskid(self, workflow_task=False):

        """
        This function gets the job Id for a taskid

        Args:
            workflow_task(bool) -- Set True if it is a workflow schedule

        Returns:
            Job Object if new Job is present

        Raises:
            SDK Exception of incorrect JobId if the Job id is not present
        """

        try:
            if workflow_task:
                job_id_query = ("select jobId from JMAdminJobStatsTable where subTaskId ={0}"
                                .format(self.schedule_subtask_id))
            else:
                job_id_query = (
                    "select jobId from tm_jobs where jobRequestId in (select jobRequestId "
                    "from TM_JobRequest where taskId = {0} and subtaskId= {1})"
                    "ORDER BY jobId desc"
                    .format(self.schedule_task_id, self.schedule_subtask_id))
            self.log.info('Getting job Id for the schedule task {0}'.format(self.schedule_task_id))
            job_id, job_cur = self._utility.exec_commserv_query(job_id_query)
            if self.jobs:
                previous_jobs = [job.job_id for job in self.jobs]
            else:
                previous_jobs = []
            new_job = set(previous_jobs) ^ set(job_id)
            new_job = sorted(new_job, reverse=True)
            self.log.info(new_job)

            from cvpysdk.job import Job
            if new_job and new_job[0]:
                return Job(self._commcell_object, new_job[0])

        except Exception as excp:
            raise Exception("\n {0}".format(str(excp)))

    def is_exception(self, exception_date):
        """
        Checks if the given date is an exception in the schedule
        Args:
            exception_date (datetime) -- date to be checked for exception

        Returns:
            True/False based on whether the given date is an exception

        """
        exception_dates = self.schedule_object.exception_dates
        exception = False
        if exception_dates:
            if exception_date.day in exception_dates:
                self.log.info("This date is an exception in the schedule, the schedule should not"
                              "be triggered")
                exception = True
            if self.schedule_object.schedule_freq_type == "Weekly":
                if (calendar.day_name[exception_date.weekday()].lower() not in
                        self.schedule_pattern["weekdays"]):
                    exception = True
        return exception

    def is_end_occurrence_exceeded(self, occurrence_date=None):
        """
        Checks if the given date is the end occurrence in the schedule
        Args:
            occurrence_date (datetime) -- date to be checked for end occurence

        Returns:
            True/False based on whether the given date is the last occurrence

        """
        end_date = self.schedule_object.active_end_date
        last_occurrence = False
        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
            end_date = pytz.timezone(self.timezone).localize(end_date)
            if occurrence_date:
                if occurrence_date > end_date:
                    self.log.info("Schedule should not be triggered as the end date has been "
                                  "reached")
                    last_occurrence = True

        if self.schedule_object.end_after:
            if len(self.jobs) >= self.schedule_object.end_after:
                self.log.info("Schedule should not be triggered as the max jobs count has been"
                              " reached")
                last_occurrence = True

        return last_occurrence

    def repeat_pattern(self, repeat_date):
        """
        Checks if there is a repeat pattern and forms the next run time for the schedule
        Args:
            repeat_date (datetime) -- date to be checked for repeat pattern and next run time calc

        Returns:
            True/False to check if the schedule should run or not
            next_run_time (datetime) -- next run time of the schedule

        """
        sch_repeat_pattern = self.schedule_object.repeat_pattern
        if sch_repeat_pattern:
            repeat_every_time = datetime.datetime.strptime(sch_repeat_pattern["repeat_every"],
                                                           "%H:%M")
            repeat_end_time = datetime.datetime.strptime(sch_repeat_pattern["repeat_end"], "%H:%M")
            current_end_time = repeat_date+relativedelta(hour=repeat_end_time.hour,
                                                         minute=repeat_end_time.minute)
            next_run_time = repeat_date+relativedelta(hours=+repeat_every_time.hour,
                                                      minutes=+repeat_every_time.minute)
            return next_run_time > current_end_time, next_run_time
        else:
            return False, None

    def next_run_calculator(self, next_run_time):
        """
        calculates the next run time of the schedule based on the schedule type
        Args:
            next_run_time (datetime) -- current next_run_time of the schedule

        Returns: datetime object with the next run time

        """
        offset_dict = {
            'Daily': 'days',
            'Weekly': 'weeks',
            'Monthly': 'months',
            'Yearly': 'years'
        }

        if self.schedule_object.schedule_freq_type == "Weekly":
            next_run = self.weekly_run_calculator(next_run_time)
        elif self.schedule_object.schedule_freq_type in ("Monthly_Relative", "Yearly_Relative"):
            next_run = self.relative_calculator(next_run_time, rel_type=self.schedule_object.
                                                schedule_freq_type)
        else:
            next_run = eval("next_run_time+relativedelta({0}=+{1})".
                            format(offset_dict[self.schedule_object.schedule_freq_type],
                                   self.schedule_pattern.get("repeat_" +
                                                             offset_dict[
                                                                 self.schedule_object.
                                                                 schedule_freq_type],
                                                             1))
                           )
        return next_run

    @staticmethod
    def weekend_day_calculator(schedule_time, offset):
        """
        calculates the weekend_day based on the offset provided
        Args:
            schedule_time (datetime) -- schedule_time for which the weekend day
            has to be calculated
            offset (int) -- nth weekend offset

        Returns:
            datetime object with the schedule run time

        """
        temp_date = schedule_time.replace(day=1)
        if offset == 5:
            # if its last weekend day
            temp_date = temp_date + relativedelta(months=1, days=-1)
            weekday = temp_date.weekday() + 2
            if 1 < weekday < 7:
                temp_date = temp_date + relativedelta(days=-weekday+1)
            return temp_date
        weekday = temp_date.weekday() + 2
        if weekday == 1:
            offset -= 1
        if offset == 0:
            return temp_date
        day_diff = 7 - weekday
        first_weekend = temp_date + relativedelta(days=day_diff)
        if offset == 1:
            return first_weekend
        div = float(offset) / 2
        if div > int(offset / 2):
            act_date = first_weekend + relativedelta(days=int((offset / 2)) * 7)
        else:
            act_date = first_weekend + relativedelta(days=((int((offset / 2)) - 1) * 7) + 1)
        return act_date

    @staticmethod
    def week_day_calculator(schedule_time, offset):
        """
        calculates the week day based on the offset provided
        Args:
            schedule_time (datetime) -- schedule_time for which the week day has to be
                                                                                    calculated
            offset (int) -- nth week offset

        Returns:
            datetime object with the schedule run time

        """
        temp_date = schedule_time.replace(day=1)
        if offset == 5:
            act_date = temp_date + relativedelta(months=1, days=-1)
            weekday = act_date.weekday()
        else:
            weekday = temp_date.weekday() + 2
            if weekday > 7:
                weekday = 1
            day_diff = offset + int((offset / 5)) * 2
            if weekday == 7:
                day_diff += 2
            elif weekday == 1:
                day_diff += 1
            if 1 < weekday < 7:
                if (weekday + int((offset % 5))) > 6:
                    day_diff += 2
            act_date = temp_date + relativedelta(days=day_diff - 1)
            weekday = act_date.weekday()
        if weekday == 5:
            act_date = act_date + relativedelta(days=-1)
        elif weekday == 6:
            act_date = act_date + relativedelta(days=-2)
        return act_date

    def relative_calculator(self, schedule_time, next_run=True, rel_type="Monthly_Relative"):
        """
        calculates the monthly relative run for the schedule
        Args:
            schedule_time (datetime) -- current schedule run time
            next_run (bool) -- set False if its the first run of the schedule else True
            rel_type (String) -- set the type of Relative schedule Pattern
        Returns:
            datetime object with the schedule run time

        """
        if rel_type == "Monthly_Relative":
            temp_date = schedule_time.replace(day=1)
            sch_month = schedule_time.month
        else:
            sch_month = eval("list(calendar.month_name).index('{0}')".
                             format(self.schedule_pattern["on_month"]))
            temp_date = schedule_time.replace(day=1, month=sch_month)

        if next_run:
            while temp_date < self.machine_obj.current_time(self.timezone):
                if rel_type == "Monthly_Relative":
                    temp_date += relativedelta(months=self.schedule_pattern.get("repeat_months"))
                    sch_month = temp_date.month
                else:
                    temp_date += relativedelta(years=1)

        if WEEK_DAY[self.schedule_pattern["relative_weekday"]] == 8:
            return self.weekend_day_calculator(temp_date,
                                               RELATIVE_DAY[self.schedule_pattern["relative_time"]]
                                              )

        elif WEEK_DAY[self.schedule_pattern["relative_weekday"]] == 7:
            return self.week_day_calculator(temp_date,
                                            RELATIVE_DAY[self.schedule_pattern["relative_time"]]
                                           )
        adj = (WEEK_DAY[self.schedule_pattern["relative_weekday"]] - temp_date.weekday()) % 7
        temp_date += relativedelta(days=adj)
        temp_date += relativedelta(weeks=RELATIVE_DAY[self.schedule_pattern["relative_time"]] - 1)
        if temp_date.month > sch_month:
            temp_date += relativedelta(days=-7)
        return temp_date

    def weekly_run_calculator(self, schedule_time, next_run=True):
        """
        calculates the weekly run for the schedule
        Args:
            schedule_time (datetime) -- current schedule run time
            next_run (bool) -- set False if its the first run of the schedule else True

        Returns:
            datetime object with the schedule run time

        """
        current_weekday = (calendar.day_name[schedule_time.weekday()]).upper()
        weekdays = [x.upper() for x in self.schedule_pattern["weekdays"]]
        if current_weekday in weekdays:
            if next_run:
                if not current_weekday == weekdays[-1]:
                    schedule_time = (schedule_time +
                                     relativedelta(weekday=
                                                   eval("calendar.{0}".
                                                        format(weekdays
                                                               [weekdays.index(current_weekday)
                                                                + 1])),
                                                   hour=schedule_time.hour,
                                                   minute=schedule_time.minute))
                else:
                    schedule_time = (schedule_time +
                                     relativedelta(weekday=eval("calendar.{0}".format(weekdays[0]))
                                                   , weeks=+(self.schedule_pattern.
                                                             get("repeat_weeks") - 1),
                                                   hour=schedule_time.hour,
                                                   minute=schedule_time.minute))
            else:
                schedule_time = (schedule_time +
                                 relativedelta(hour=schedule_time.hour,
                                               minute=schedule_time.minute))

        else:
            # assign first weekday of the schedule as schedule first day
            schedule_time = schedule_time + relativedelta(weekday=eval(
                "calendar.{0}".format(weekdays[0])), hour=schedule_time.hour,
                                                          minute=schedule_time.minute)
        return schedule_time

    @property
    def schedule_start_time(self):
        """
        gets the schedule start time based on the type of the schedule
        Returns: datetime object with the schedule start time

        """
        schedule_time = datetime.datetime.strptime(self.schedule_object.active_start_date+" "
                                                   + self.schedule_object.
                                                   active_start_time, "%m/%d/%Y %H:%M")
        schedule_time = pytz.timezone(self.timezone).localize(schedule_time)
        if self.schedule_object.schedule_freq_type == 'Daily':
            schedule_time = self.machine_obj.current_time(self.timezone)+relativedelta(
                hour=schedule_time.hour, minute=schedule_time.minute)
        elif self.schedule_object.schedule_freq_type == 'Weekly':
            schedule_time = self.weekly_run_calculator(schedule_time, next_run=False)
        elif self.schedule_object.schedule_freq_type == 'Monthly':
            schedule_time = schedule_time+relativedelta(day=self.schedule_pattern["on_day"])
        elif self.schedule_object.schedule_freq_type == 'Yearly':
            schedule_time = schedule_time + relativedelta(day=self.schedule_pattern["on_day"],
                                                          month=eval("calendar.{0}".
                                                                     format(self.schedule_pattern
                                                                            ["on_month"])))
        elif self.schedule_object.schedule_freq_type in ("Monthly_Relative", "Yearly_Relative"):
            schedule_time = self.relative_calculator(
                schedule_time, next_run=False, rel_type=self.schedule_object.schedule_freq_type)
        return schedule_time

    def next_job_wait(self, job_count=1):
        """
        Waits for the next job of the schedule based on the type and number of jobs
        Args:
            job_count (int) -- number of jobs for the schedule to wait

        Raises:
            SDK Exception for any failure while waiting for the job

        """

        try:
            fail = False
            repeat_expired = False
            jobs = self.check_job_for_taskid(retry_count=1, retry_interval=5)
            if not jobs:
                previous_jobs = []
            else:
                previous_jobs = [job.job_id for job in jobs]
            count = 0
            next_run_time = self.schedule_start_time - datetime.timedelta(minutes=1)
            last_success_run = next_run_time
            while count < job_count:
                # if the schedule run time has passed for the same day, time shifted to nextruntime
                # if next_run_time < current_time:
                    # check for repeat pattern
                update_run = False
                while next_run_time < self.machine_obj.current_time(self.timezone):
                    if self.schedule_object.schedule_freq_type == "One_time":
                        raise Exception("One_Time schedule pattern expired")
                    fail, repeat_pattern_time = self.repeat_pattern(next_run_time)
                    if repeat_pattern_time and not repeat_expired:
                        next_run_time = repeat_pattern_time
                        if fail:
                            repeat_expired = True
                    else:
                        # expired or no repeat pattern, we change to next schedule date
                        next_run_time = self.next_run_calculator(last_success_run)
                        repeat_expired = False
                # offset = ((next_run_time - (self.machine_obj.current_time(self.client_timezone))).
                #           total_seconds())
                self.log.info("Current Assumed Next Run Time {0}".format(next_run_time.strftime('%Y-%m-%d %H:%M')))
                local_next_run_time = next_run_time.astimezone(pytz.timezone(self.client_timezone))
                # self.log.info("Time Offset being set is {0}".format(str(offset)))
                self.log.info("Current Assumed Localized Run Time {0}".format(local_next_run_time.strftime('%Y-%m-%d %H:%M')))
                if(self._commcell_object.is_linux_commserv):
                    time_output = self.machine_obj.execute_command('date --set="{}"'.format(
                        local_next_run_time.strftime("%m/%d/%Y %H:%M")))
                    # Sometimes DB does not reflect changes after service restart so restarting MS SQL server.
                    self.machine_obj.execute_command("sudo systemctl restart mssql-server")
                    self._utility.sleep_time()
                else:
                    time_output = self.machine_obj.execute_command('set-date -date "{}"'.format(
                        local_next_run_time.strftime("%m/%d/%Y %H:%M")))

                if (time_output.exit_code != 0 and str(next_run_time.year) not in
                            time_output.output):
                    raise Exception("Next run date was not changed successfully")

                self.log.info("Time Offset set successful")
                self._utility.sleep_time(60)
                self.check_job_for_taskid(retry_interval=30)
                latest_job = self.get_latest_job()
                if not latest_job or latest_job.job_id in previous_jobs:
                    if self.is_exception(next_run_time):
                        self.log.info("The Job has not triggered because there is an exception"
                                      "in the schedule")
                        update_run = True
                        job_count += 1
                    elif self.is_end_occurrence_exceeded(next_run_time):
                        self.log.info("The Schedule's end occurence has exceeded")
                        update_run = True
                    elif fail:
                        self.log.info("The Job has not triggered because repeat pattern's end"
                                      "time has reached")
                        job_count += 1
                    else:
                        raise Exception("Job did not get triggered for the Schedule {0}".format(
                            self.schedule_object.schedule_id))
                else:
                    update_run = True
                    repeat_expired = False
                    self.job_manager.job = latest_job
                    self.common_utils.job_list.append(self.job_manager.job.job_id)
                    self.job_manager.wait_for_state('completed')
                    previous_jobs.append(latest_job.job_id)
                if update_run:
                    last_success_run = next_run_time.replace(hour=self.schedule_start_time.hour,
                                                             minute=self.schedule_start_time.minute
                                                            ) - datetime.timedelta(minutes=1)
                count += 1

        except Exception as excp:
            raise Exception("\n {0}".format(str(excp)))


    def continuous_schedule_wait(self, first_job=None, wait_jobs_count=1):
        """

        Waits for the continuous schedule's jobs with the continuous interval to the number of
        jobs specified

        Args:
            first_job  (Obj) -- first job of the schedule if known

            wait_jobs_count  (int) -- no of continuous jobs to wait

        Raises:
            SDK Exception if the jobs didnt get triggered or completed successfully

        """

        try:
            previous_job = None
            if first_job:
                previous_job = first_job
            continuous_count = 0
            continuous_interval = self.schedule_object.continuous['job_interval']
            while continuous_count < wait_jobs_count:
                if previous_job:
                    _job_finish_time = previous_job.end_time
                    _date_time = datetime.datetime.strptime(_job_finish_time, '%Y-%m-%d %H:%M:%S')
                    _wait_secs = abs((continuous_interval*60) - (
                        datetime.datetime.utcnow() - _date_time).total_seconds())
                    self.log.info("Waiting for {0} seconds to check if the next job started".format
                                  (_wait_secs))
                    self._utility.sleep_time(_wait_secs)
                retry_count = 0
                while retry_count < 3:
                    self.check_job_for_taskid()
                    retry_count += 1
                    if previous_job:
                        if previous_job.job_id != self.get_latest_job().job_id:
                            break
                    elif self.jobs:
                        break
                if previous_job:
                    if previous_job.job_id == self.get_latest_job().job_id:
                        raise Exception("The next Continuous Job has not been triggered for the "
                                        "schedule {0}".format(self.schedule_task_id))
                self.job_manager.job = self.get_latest_job()
                self.log.info("Successfully got Continous Job with JobId {0}".format
                              (self.job_manager.job.job_id))
                self.common_utils.job_list.append(self.job_manager.job.job_id)
                self.job_manager.wait_for_state('completed')
                previous_job = self.job_manager.job
                continuous_count += 1

        except Exception as excp:
            if self.common_utils.job_list:
                self.common_utils.cleanup_jobs()
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def automatic_schedule_wait(self, first_job=None, newcontent=False):
        """

        Waits for the automatic schedule's job with the min backupinterval minutes.

        Args:
            first_job  (Obj) -- first job of the schedule if known
                default - True

        Raises:
            SDK Exception if the jobs didnt get triggered or completed successfully

        """
        try:
            previous_job = None
            wait_count = 0
            if first_job:
                previous_job = first_job
            min_backup_interval = self.schedule_object.automatic['min_interval_minutes']
            self.log.info("Waiting for {0} seconds to get the automatic job to trigger".format(min_backup_interval*60))
            if not newcontent:
                self._utility.sleep_time(min_backup_interval*60)
            self.check_job_for_taskid(retry_count=1, retry_interval=10)

            if previous_job:
                if previous_job.job_id == self.get_latest_job().job_id:
                    self.log.info("The next automatic Job has not been triggered for the"
                                  "schedule: %s", str(self.schedule_task_id))
                    return 0

            if self.get_latest_job():
                self.job_manager.job = self.get_latest_job()
                self.log.info("Successfully got automatic Job with JobId %s", int(self.job_manager.job.job_id))
                self.common_utils.job_list.append(self.job_manager.job.job_id)
                self.job_manager.wait_for_state('completed')
                previous_job = self.job_manager.job

        except Exception as excp:
            if self.common_utils.job_list:
                self.common_utils.cleanup_jobs()
            raise Exception("\n %s %s", str(inspect.stack()[0][3], str(excp)))

        return previous_job

    def get_latest_job(self):
        """

        Returns: Job object of the latest job

        """
        if self.jobs:
            return self.jobs[-1]
        else:
            self.log.info("No Jobs associated with the schedule")
