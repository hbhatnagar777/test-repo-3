# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing job operations on Commcell

JobManager is the only class defined in this file

JobManager:
    __init__(job, commcell)             --  initialize instance of the JobManager class

    __repr__()                          --  Representation string for the instance of the
                                            JobManager class

    wait_for_state()                    --  Waits for the job to go into required state

    wait_for_phase()                    --  Waits for the job to come to the required phase

    modify_job()                        --  Suspend, Resume OR kill a job

    modify_all_jobs()                   --  Suspend, Resume OR Kill all jobs running on Commserver

    kill_active_jobs()                  --  Kills any active jobs for a given client.

    validate_job_state()                --  Validate if the current job state and expected status
                                            matches

    get_filtered_jobs()                 --  Gets job list for all the jobs matching a specific
                                            filtering criterion and waits for these jobs to be
                                            completed based on the argument flag.

    check_job_status                    --  Check Job status for Backup and restore Jobs
                                            when activity is disabled

    get_active_job_object()             --  Gives the first active job object that is running

    wait_for_job_progress()             --  Wait for job progress to reach/exceed percent completion

    @property
        job    -- Sets/Gets job object
"""

import inspect
import time
from pprint import pformat
import re

from cvpysdk.job import Job
from AutomationUtils import logger

from Server.serverhandlers import argtypes
from Server.JobManager import jobmanager_constants

class JobManager(object):
    """JobManager helper class to perform job related operations"""

    def __init__(self, _job=None, commcell=None):
        """Initialize instance of the JobManager class."""

        self.log = logger.get_log()
        self._commcell = commcell
        self._job_map = jobmanager_constants.JOB_MAP
        self._status = jobmanager_constants.JOB_STATUS

        try:
            if _job is not None:
                if isinstance(_job, (str, int)):
                    self._job = self._commcell.job_controller.get(_job)
                elif isinstance(_job, Job):
                    self._job = _job
                else:
                    raise Exception("Incorrect argument type for job to initialize JobManager")
        except Exception as excp:
            raise Exception("Failed to initialize job object for JobManager with exception [{0}]"
                            "".format(excp))

    def __repr__(self):
        """Representation string for the instance of the JobManager class."""
        return "JobManager class instance"

    def wait_for_state(self,
                       expected_state="completed",
                       retry_interval=10,
                       time_limit=75,
                       hardcheck=True,
                       fetch_job_state_in_validate=True):
        """ Waits for the job to go into required state

            Args:
                expected_state    (str/list)
                                           -- Expected job id state. Default = completed.
                                                    suspended/killed/running/completed etc..
                                                    Can be a string OR list of job states
                                                    e.g
                                                    completed
                                                    ['waiting', 'running']

                retry_interval    (int)    -- Interval (in seconds) after which job state
                                                    will be checked in a loop. Default = 10

                time_limit        (int)    -- Time limit after which job status check shall be
                                                aborted if the job does not reach the desired
                                                 state. Default (in minutes) = 75

                hardcheck         (bool)   -- If True, function will exception out in case the job
                                                does not reaches the desired state.
                                              If False, function will return with non-truthy value

                fetch_job_state_in_validate
                                  (bool)   -- If True, job state is fetched again in validate_job_state()
                                              If False, job state is passed as input and it is not fetched
                                                again in validate_job_state()

            Returns:
                True/False        (bool)   -- In case job reaches/does not reaches the desired
                                                state.

            Raises:
                Exception if :

                    - failed during execution of module

            Example:
                job_manager = JobManager(job, self._commcell)

                job_manager.wait_for_state(['waiting', 'running'])

                job_manager.wait_for_state('suspended')

                job_manager.wait_for_state('running')

                job_manager.wait_for_state('completed')

                job_manager.wait_for_state('killed')
        """
        try:
            job = self._job
            jobid = str(job.job_id)

            if isinstance(expected_state, str):
                expected_state = [expected_state]

            job_status = job.status.lower()

            self.log.info("Current job [{0}] status = [{1}],  Waiting for job to go into "
                          "state: {2}".format(jobid, job_status, expected_state))

            time_limit = time.time()+time_limit*60
            while True:
                job_status = job.status.lower()
                if (job_status in expected_state or time.time() >= time_limit or
                        job_status in ['killed', 'failed', 'completed w/ one or more errors']):
                    if fetch_job_state_in_validate:
                        self.validate_job_state(expected_state, hardcheck=hardcheck)
                    else:
                        self.validate_job_state(expected_state, job_status, hardcheck=hardcheck)
                    break
                else:
                    self.log.info("Sleep [{0}] secs. Job state: [{1}], phase [{2}], "
                                  "Progress: [{4}%], Delay reason: [{3}] ".format(retry_interval,
                                                                                 job.status,
                                                                                 job.phase,
                                                                                 job.delay_reason,
                                                                                 job.summary.get('percentComplete')))
                    time.sleep(retry_interval)

            if job_status not in expected_state:
                if not hardcheck:
                    return False
                if fetch_job_state_in_validate:
                    self.validate_job_state(expected_state)
                else:
                    self.validate_job_state(expected_state, job_status)

            self.log.info("Job id [{0}] status = [{1}]".format(jobid, job.status.lower()))

            return True

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def wait_for_phase(self, phase='backup', total_attempts=50, check_frequency=5):
        """Waits for the job to come to the required phase

            Args:
                phase               (str)   --  The phase of the job to wait for

                total_attempts      (int)   --  Total attempts to check the job phase

                check_frequency     (int)   --  The interval in secs between every check for phase

            Returns:
                None    --      If job comes to the expected phase

            Raises:
                If the job is already finished or attempts got exhausted

        """

        attempt = 1
        phase = phase.lower()

        if self._job.is_finished:
            self.log.info('Job [%s] already finished before waiting for phase.', self._job.job_id)
            return

        while not self._job.phase.lower() == phase:
            self.log.info(
                'Waiting for job [{0}] to come to [{1}] phase. Current phase [{2}]. '
                'Attempt [{3}/{4}]'.format(
                    self._job.job_id, phase, self._job.phase, attempt, total_attempts))
            time.sleep(check_frequency)

            if self._job.is_finished:
                raise Exception('Job already finished while waiting for phase')

            attempt += 1
            if attempt == total_attempts:
                raise Exception(
                    'Attempts exhausted while waiting for the job to come to the required phase')

    def modify_job(self, set_status=None, wait_for_state=True, hardcheck=True):
        """ Suspend, Resume OR kill a job

            Args:
                set_status        (str)    -- job id state. Default = None
                                                Job state will be changed to this state.
                                                Options:
                                                    suspend/resume/kill

                wait_for_state    (int)    -- True/False: Whether to wait for the job to go in the
                                                required state or not.

                hardcheck         (bool)   -- If True, function will exception out in case the job
                                                does not reaches the desired state.
                                              If False, function will return with non-truthy value

            Returns:
                True/False        (bool)   -- In case job reaches/does not reaches the desired
                                                state.

            Raises:
                Exception if :

                    - Unsupported job state passed to the module

                    - failed during execution of module

            Example:
                job_manager = JobManager(job, self._commcell)

                job_manager.modify_job('suspend')

                job_manager.modify_job('resume')

                job_manager.modify_job('kill')
        """
        try:

            if set_status not in self._job_map:
                raise Exception("Unsupported job state passed to modify_job")

            job = self._job
            jobid = str(job.job_id)

            self.log.info("{0} job id: [{1}],   Current status: [{2}]"
                          "".format(self._job_map[set_status]['message'], jobid, job.status.lower()))

            getattr(job, self._job_map[set_status]['module'])(wait_for_state)

            self.log.info("Successfull.! Job id [{0}] status = [{1}]".format(jobid, job.status.lower()))

            if job.status.lower() != self._job_map[set_status]['status']:
                if not hardcheck:
                    return False
                raise Exception("Failed to [{0}] job: [{1}]".format(set_status, jobid))

            return True
        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def modify_all_jobs(self, operation_type=None):
        """ Suspend, Resume OR Kill all jobs running on Commserver

            Args:
                operation_type        (str)    -- All jobs on commcell will be changed to this
                                                    state.
                                                    Options:
                                                        suspend/resume/kill

            Returns:
                None

            Raises:
                Exception if :

                    - Unsupported operation_type passed to the module

                    - failed during execution of module

            Example:
                job_manager = JobManager(job, self._commcell)

                job_manager.modify_all_jobs('suspend')

                job_manager.modify_all_jobs('resume')

                job_manager.modify_all_jobs('kill')
        """
        try:
            if operation_type not in self._job_map:
                raise Exception("Supported values for operation_type:{0}"
                                "".format(self._job_map.keys()))

            if self._commcell is None:
                raise Exception("Commcell object is set to None.")

            self.log.info("{0} all jobs".format(self._job_map[operation_type]['message']))

            jobcontroller = self._commcell.job_controller

            getattr(jobcontroller, self._job_map[operation_type]['module_all'])()

            self.log.info("Successfully {0} all jobs on commcell".format(self._job_map[operation_type]['post_message']))

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def kill_active_jobs(self, client):
        """ Kills any active jobs on the client

            Args:
                client        (str)    -- Client name

            Returns:
                True - IF no such client exist on commcell

            Raises:
                Exception if :
                    - Failed to kill the active jobs
        """
        try:
            if not self._commcell.clients.has_client(client):
                self.log.info("No such client [{0}] exist on Commcell".format(client))
                return True

            jobcontroller = self._commcell.job_controller
            active_jobs = jobcontroller.active_jobs(client_name=client, job_filter="Backup")
            self.log.info("Active jobs for client [{0}] are {1}".format(client, active_jobs))
            for jobid in active_jobs.keys():
                try:
                    _ = JobManager(jobid, commcell=self._commcell).modify_job("kill")
                except Exception as exp:
                    if exp.args[0] != '\n modify_job Job kill failed\nError: \
                    "Operation failed. Job cannot be suspended/killed/resumed."':
                        raise exp


        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def validate_job_state(self, expected_state=None, job_status=None, hardcheck=True):
        """ Validate if the current job state and expected status matches

            Args:
                expected_state    (str/list)    -- Expected job id state.
                                                    suspended/killed/running/completed etc..
                                                    Can be a list or string with job states

                job_status        (str)         -- current job status. If passed job status
                                                   is not fetched again.

                hardcheck         (bool)        -- If True, function will exception out in case the job
                                                do not reach the desired state.

            Returns:
                None

            Raises:
                Exception if :

                    - Expected job state (expected_state) is not equal to current job state

                    - failed during execution of module

            Example:
                validate_job_state('running')

                validate_job_state('suspended')

                validate_job_state('running')
        """
        try:
            job = self._job
            jobid = str(job.job_id)
            if not job_status:
                job_status = job.status.lower()

            if isinstance(expected_state, str):
                expected_state = [expected_state]

            self.log.info("Validation: Current job [{0}] state: [{1}],   Expected: {2}"
                          "".format(jobid, job_status, expected_state))

            if hardcheck:
                assert job_status in expected_state, \
                    f"Job [{jobid}] validation failed: Expected state [{expected_state}], Current state [{job_status}]"

        except AssertionError as excp:
            raise Exception("\n Stack - {0}, Error - {1}".format(inspect.stack()[0][3], str(excp)))

    def get_filtered_jobs(self,
                          client,
                          current_state=None,
                          expected_state='completed',
                          lookup_time=1,
                          job_filter='backup',
                          hardcheck=True,
                          time_limit=30,
                          retry_interval=10,
                          backup_level=None,
                          **kwargs):
        """ Gets job list for all the jobs matching a specific filtering criterion and waits
                for these jobs to be completed (based on expected_state flag)

            Args:

                client_name     (str)   --  name of the client to filter out the jobs for

                current_state   (str/list)
                                        --  Expected current state of the jobs being fetched.
                                                default: All jobs matching the filtering criterion
                                                            and current status as running

                current_state and expected_state go hand in hand.
                    Basically we are looking for active jobs to match current_state and then wait
                        for job to reach expected_state

                expected_state  (list/str)
                                        --  Wait for the jobs to reach any of the required state
                                                default: None
                                                By default just return all the jobs and do not
                                                wait. If provided then wait for all jobs to wait
                                                for a certain state.

                                                Options:
                                                    'completed'
                                                    'failed'
                                                    'suspended'
                                                    'waiting'
                                                    'pending'

                lookup_time     (int)   --  get all the jobs executed within the number of hours
                                                default: 5 Hours

                job_filter      (str)   --  type of jobs to filter
                                            for multiple filters, give the values
                                            **comma(,)** separated

                                            List of Possible Values:
                                                Backup
                                                Restore
                                                AUXCOPY
                                                WORKFLOW
                                                etc..

                                            default: Backup

                hardcheck       (bool)   -- If true, will throw exception in case of failed
                                                client validation.
                                              If false, will return False if validation fails

                retry_interval  (int)    -- Interval (in seconds) after which job state
                                                    will be checked in a loop. Default = 10

                time_limit      (int)    -- Time limit after which job status check shall be
                                                aborted if the job does not reach the desired
                                                 state. Default (in minutes) = 30

                backup_level    (str)    -- The level of backup.
                                            Valid values are Full, Incremental, Differential, Synthetic Full

                kwargs          (dict)  --  dict of key-word arguments

                Available kwargs Options:

                    limit           (int)   --  total number of jobs list that are to be returned
                                                    default: 20

                    show_aged_job   (bool)  --  boolean specifying whether to include aged jobs in
                                                    the result or not
                                                    default: False

                    clients_list    (list)  --  list of clients to return the jobs for
                                                    default: []

                    job_type_list   (list)  --  list of job operation types
                                                    default: []

            Returns:
                (bool, dict/list)    -- Tuple of boolean value based on module return value
                                            and job dictionary or list based on filtered criterion

            Raises
                Exception
                    - if Invalid argument passed.
                    - Time out waiting to get valid jobs to meet filtered criterion
                    - Failed during module execution
        """
        try:
            if current_state is None:
                current_state = ['running', 'waiting']
            elif isinstance(current_state, str):
                current_state = [current_state.lower()]
            elif isinstance(current_state, list):
                current_state = [_state.lower() for _state in current_state]

            jobcontroller = self._commcell.job_controller

            self.log.info("""Getting list of all [{0}] jobs for
                Client:            {1}
                Within last:       {2} hours
                State:    {3}
                Backup Level:      {4}
                Filters:           {5}""".format(job_filter, client, lookup_time, current_state, backup_level, kwargs))

            jobs = jobcontroller.all_jobs(client, lookup_time, job_filter, **kwargs)
            if backup_level:
                job_list = list(jobs.keys())
                for job in job_list:
                    if not jobs[job]['backup_level'].lower() == backup_level.lower():
                        jobs.pop(job)

            self.log.info("Jobs fetched: [{0}]".format(pformat(jobs)))

            if expected_state is None:
                return (True, jobs)

            time_limit = time.time()+time_limit*60
            while True:
                if jobs:
                    # Check if any of the jobs have state as [current_state]. If not continue
                    if not any(jobs[_id].get('status').lower() in current_state for _id in jobs):
                        jobs.clear()
                        continue

                    job_ids = []
                    for _id in jobs:
                        if jobs[_id]['status'].lower() in current_state:
                            job_ids.append(_id)
                            self.log.info("Job matching filtering criterion: [{0}]: [{1}]"
                                          "".format(_id, pformat(jobs[_id])))

                    # Wait for the jobs to reach the required expected state
                    for jobid in job_ids:
                        response = JobManager(jobid, self._commcell).wait_for_state(
                            expected_state, retry_interval, time_limit, hardcheck)

                    return (response, job_ids)
                else:
                    jobs = jobcontroller.all_jobs(client, lookup_time, job_filter, **kwargs)
                    if backup_level:
                        job_list = list(jobs.keys())
                        for job in job_list:
                            if not jobs[job]['backup_level'].lower() == backup_level.lower():
                                jobs.pop(job)

                    if time.time() >= time_limit:
                        self.log.error("Timed out waiting to get valid jobs which meets the filtered criterion")
                        if hardcheck:
                            raise Exception("Timed out waiting to get valid jobs to meet filtered criterion")

                        return (False, jobs)
                    else:
                        self.log.info("Waiting for [{0}] seconds ".format(retry_interval))
                        time.sleep(retry_interval)

        except Exception as excp:
            raise Exception("\nFailed [{0}]: {1}".format(inspect.stack()[0][3], str(excp)))

    def get_active_job_object(self, client_name, time_limit=5, retry_interval=1):
        ''' Gives the first active job object that is running
        args:
        client_name : {str} client name on which to check the active job list

        returns
        job_obj (list)  : returns the first active job object '''

        time_limit = time.time()+time_limit*60
        jobcontroller = self._commcell.job_controller
        active_jobs = jobcontroller.active_jobs(client_name=client_name, job_filter="Backup")
        while not active_jobs:
            active_jobs = jobcontroller.active_jobs(client_name=client_name, job_filter="Backup")
            if not active_jobs:
                if time.time() >= time_limit:
                    raise Exception("Timed out waiting to get valid active jobs")
                else:
                    self.log.info("Waiting for [{0}] seconds ".format(retry_interval))
                    time.sleep(retry_interval)
        lap_job_id = list(active_jobs.keys())[0]
        jm_obj = jobcontroller.get(lap_job_id)
        return jm_obj

    def check_job_status(self,
                         host_name,
                         subclient_obj,
                         _name,
                         entity_name='client',
                         backup=True,
                         client_1=True):
        """Check Job status for Backup and restore Jobs when activity is disabled.

            Args:
                host_name (str)           --  client hostname

                subclient_obj(object)     --  client object

                _name(str)                -- client/IDA/Subclinet objects name

                entity_name(str)          -- client/IDA/Subclient

                backup(flag)              --  True if backup, False if restore

                client_1(flag)            --  True if it is client1, False if client2

            Raises:
                Exception:
                    if job status and delay reason is not correct

        """
        job_object = self._job
        if client_1:
            str_ida = 'Windows File System'
            if entity_name.lower() == 'client':
                if backup:
                    result_bkp = self._status[entity_name]['backup'].format(_name)
                else:
                    result_bkp = self._status[entity_name]['restore'].format(host_name)
            if entity_name.lower() == 'ida':
                if backup:
                    result_bkp = self._status[entity_name]['backup'].format(str_ida, _name)
                else:
                    result_bkp = self._status[entity_name]['restore'].format(str_ida, host_name)
            if entity_name.lower() == 'subclient':
                if backup:
                    _obj = subclient_obj.subclient_name
                    result_bkp = self._status[entity_name]['backup'].format(_obj, _name, str_ida)

            if job_object.status != 'Queued':
                raise Exception("job {0} Status other than \"Queued\" for {1} "
                                .format(job_object.job_id, _name))
            else:
                self.log.info("Job is in Queued state as Queue job is enabled")
                if str(job_object.delay_reason).split("<br>")[0].find(result_bkp) >= 0:
                    self.log.info("Job Fired with Correct Failure reason: {0}"
                                  .format(job_object.delay_reason))
                else:
                    raise Exception("Activity is disabled on Client, but no failure reason")
        else:
            if job_object.status == 'Queued':
                raise Exception("job {0} is in \"Queued\" state for {1}"
                                .format(job_object.job_id, _name))
            self.log.info("Job is not in Queued state as activity is not disabled on {0}"
                          .format(_name))

    @property
    def job(self):
        """Treats the job object as a read-only attribute."""
        return self._job

    @job.setter
    def job(self, job_object):
        """Sets the job object for the instance

        Args:
            job_object    (job object)    -- Job instance of SDK Job class

        """

        if not isinstance(job_object, Job):
            raise Exception("Value [{0}] should be instance of SDK Job class".format(job_object))
        else:
            self._job = job_object

    def wait_for_job_progress(self, percent_complete=20, timeout=3600):
        """Wait till job progress reaches/exceed percent_complete
            Args:
                percent_complete    (int)   --  Percentage the job has completed
                timeout             (int)   -- timeout in seconds to wait for job progress

            Returns:
                True if job progress reaches percent_complete

            Raise:
                Exception if job does not progress within timeout seconds
        """

        if self._job.is_finished:
            self.log.info('Job [%s] already finished before waiting for job progress.', self._job.job_id)
            return

        time_start = time.time()
        while self._job.summary.get('percentComplete') <= percent_complete:

            if time.time() - time_start >= timeout:
                raise Exception(
                    f"Timed out waiting for job progress to reach [{percent_complete}%]. "
                    f"Pending Reason [{self._job.summary.get('pendingReason')}]"
                )

            self.log.info(
                f"Waiting 15 seconds for job progress to update. "
                f"Percent complete [{self._job.summary.get('percentComplete')}]%"
            )
            time.sleep(15)

        self.log.info(
            f"Percent complete [{self._job.summary.get('percentComplete')}]%"
        )

        return True
    
    def validate_job_errors(self, expected_errors):
        """
        For restore jobs which complete with errors, validates the errors in the job with the expected errors
        This is done by checking if the errors in the job are a subset of the expected errors

        Args:
            expected_errors (list of regexes or strings) : List of errors that are expected in the job
        
        Returns:
            True if the errors in the job are a subset of the expected errors, False otherwise
        """
        job = self._job
        for vm_status in job.details['jobDetail']['clientStatusInfo']['vmStatus']:
            errors = vm_status['FailureReason'].split('\n')
            if errors == ['']:
                continue
            for error in errors:
                error_found = False
                for expected_error in expected_errors:
                    if re.match(expected_error, error):
                        error_found = True
                        break
                if not error_found:
                    return False
        return True