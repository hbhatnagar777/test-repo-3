# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    wait_for_job_completion()   --  Waits for completion of job

    is_blocklevel_enabled()     --  method to find if block level backup is enabled from
                                    subclient properties

    get_job_obj()               --  method to fetch active job object according to specifications

    move_last_month_jobs()      --  method to move jobs in the last month(or schedule specific
                                    period) back by that amount of time

    exxecute_update_query()     --  method to execute update query on CSDB

    move_job_start_time()       --  method to move job's start time by input seconds

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59265": {
                    "ClientName": "XXX",
                    "AgentName": "XXX",
                    "InstanceName": "XXX",
                    "BackupsetName": "XXX",
                    "SubclientName": "XXX",
                    "SqlSaPassword": "XXX"
                }
            }

"""

import time
import datetime
import sys
from cvpysdk.schedules import Schedules
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL, get_csdb
from Database.dbhelper import DbHelper
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ Class for validation of synthetic full schedule for DB agents"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DB agents - check synthetic full schedule triggers backups"
        self.dbhelper_object = None
        self.synth_full_run_after = None
        self.agents_with_backupset = ['postgresql', 'db2']
        self.synthfull_enabled = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "SubclientName": None,
            "SqlSaPassword": None
        }

    def setup(self):
        self.dbhelper_object = DbHelper(self.commcell)
        self.synth_full_run_after = Schedules(self.subclient).get(
            "synthetic fulls").automatic['days_between_synthetic_full']
        self.synthfull_enabled = self.tcinputs['AgentName'] in\
                                 ['mysql', 'postgresql', 'oracle'] and self.is_blocklevel_enabled()

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def is_blocklevel_enabled(self):
        """
        Method to check if subclient has block level enabled
        """
        csdb = get_csdb()
        query = f"select attrVal from app_subclientprop where" \
            f" componentnameid = {self.subclient.subclient_id} and" \
            f" attrname like 'Use block level backup'"
        csdb.execute(query)
        val = csdb.fetch_one_row()[0]
        if val:
            return int(val)
        return 0

    @test_step
    def get_job_obj(self, schedule=None, synthfull=False, time_limit=300, time_interval=10,
                    wait_till=None):
        """Gets the job object from active jobs of commcell
            Args:
                schedule: schedule which triggered the job
                    default: None
                synthfull:  True if job to be searched for is a
                            Synthetic full(full if not applicable) job
                time_limit: Time limit to wait for job in seconds
                time_interval: Time interval to wait for before checking
                            for jobs again
                wait_till:  If not null, checks for ctive jobs till input epoch
            Returns: Job object or False if no job found
        """
        active_job = None
        time_limit = wait_till or time.time() + time_limit
        self.log.info(time.strftime("Waiting till %I:%M:%S %p for job",
                                    time.localtime(time_limit)))
        while time.time() <= time_limit and active_job is None:
            self.log.info("Waiting for %s seconds before checking for active job", time_interval)
            time.sleep(time_interval)
            active_jobs = self.commcell.job_controller.active_jobs(
                client_name=self.tcinputs['ClientName'])
            for job_id in active_jobs:
                job = self.commcell.job_controller.get(job_id)
                job_of_backupset = True
                if self.tcinputs['AgentName'] in self.agents_with_backupset:
                    job_of_backupset = job.backupset_name == self.tcinputs["BackupsetName"]
                job_of_schedule = True
                if schedule:
                    job_of_schedule = False
                    if 'scheduleName' in job.details['jobDetail']['generalInfo']:
                        job_of_schedule = \
                            job.details['jobDetail']['generalInfo']['scheduleName'] == schedule
                job_of_backup_level = True
                if synthfull:
                    if self.synthfull_enabled:
                        job_of_backup_level = job.backup_level == "Synthetic Full"
                    else:
                        job_of_backup_level = "Full" in job.backup_level
                if job.subclient_name == self.tcinputs["SubclientName"] and \
                        job.instance_name == self.tcinputs["InstanceName"] and \
                        job_of_backupset and job_of_schedule and job_of_backup_level:
                    active_job = job
                    break
        if active_job:
            self.log.info("Found job %s", active_job.job_id)
        return active_job

    @test_step
    def move_last_month_jobs(self, reduce_seconds):
        """Move all full jobs in the last month back by 30 days"""
        jobs_in_past = self.commcell.job_controller.finished_jobs(
            client_name=self.tcinputs['ClientName'],
            lookup_time=self.synth_full_run_after*24, limit=sys.maxsize)
        for job_id in jobs_in_past:
            job = self.commcell.job_controller.get(job_id)
            if self.tcinputs['AgentName'] in self.agents_with_backupset:
                job_of_backupset = job.backupset_name == self.tcinputs["BackupsetName"]
            else:
                job_of_backupset = True
            if job.subclient_name == self.tcinputs["SubclientName"] and \
                    job.instance_name == self.tcinputs["InstanceName"] and \
                    job_of_backupset and (job.backup_level.endswith('Full')):
                self.move_job_start_time(job_id, reduce_seconds)

    @test_step
    def execute_update_query(self, query):
        """

        Executes update query on CSDB
        Args:
            query (str) -- update query that needs to be run on CSDB

        Return:
            Response / exception
        """
        try:
            dbobject = MSSQL(self.commcell.commserv_hostname + "\\commvault",
                             "sa", self.tcinputs['SqlSaPassword'], "CommServ", False, True)
            response = dbobject.execute(query)
            if response.rows is None:
                return bool(response.rowcount == 1)
            return response

        except Exception as err:
            raise CVTestStepFailure("failed to execute query {}".format(err))

    @test_step
    def move_job_start_time(self, job_id, reduce_seconds):
        """
        runs script to change job time based on number of days in arguments
        Args:
            job_id (int) -- Job ID that needs to be moved with time
            reduce_seconds (int) -- number of seconds to reduce the job time

        Return:
            (Bool) -- True/False
        """
        self.log.info("Moving job %s back by %s", job_id,
                      datetime.timedelta(seconds=reduce_seconds))
        sql_script = """
        DECLARE @curCommCellId INTEGER
        SET @curCommCellId = 0

        DECLARE @curJobId INTEGER
        SET @curJobId = {0}

        DECLARE @i_seconds INTEGER
        SET @i_seconds = {1}

        SELECT @curCommCellId = commcellId
        FROM JMBkpStats
        where jobId = @curJobId

        UPDATE JMBkpStats
        SET servStartDate = servStartDate - @i_seconds,
        servEndDate = servEndDate - @i_seconds
        WHERE jobId = @curJobId
        AND commCellId = @curCommCellId
        """.format(job_id, reduce_seconds)
        retcode = self.execute_update_query(sql_script)
        if retcode:
            return True
        raise CVTestStepFailure("failed to run the script to move job time")

    def run(self):
        """ Main function for test case execution """
        try:
            if 'planEntity' not in self.subclient.properties:
                raise Exception('Ensure subclient is associated with a plan')
            self.move_last_month_jobs(self.synth_full_run_after*24*3600)

            self.log.info("Starting Full backup job")
            full_job = self.dbhelper_object.run_backup(self.subclient, "full")

            if self.synthfull_enabled:
                full_job_log = self.dbhelper_object.get_snap_log_backup_job(full_job.job_id)
                self.log.info("Log backup job with ID:%s is now completed", full_job_log.job_id)

                if "native" in self.subclient.snapshot_engine_name.lower():
                    self.log.info(
                        (
                            "Native Snap engine is being run. Backup "
                            "copy job will run inline to snap backup"))
                    self.log.info("Getting the backup job ID of backup copy job")
                    job = self.dbhelper_object.get_backup_copy_job(full_job.job_id)
                    self.log.info("Job ID of backup copy Job is: %s", job.job_id)

                else:
                    self.log.info(
                        "Running backup copy job for storage policy: %s",
                        self.subclient.storage_policy)
                    self.dbhelper_object.run_backup_copy(self.subclient.storage_policy)

                # run incremental backup
                self.log.info("Starting Incremental backup job")
                inc_job = self.dbhelper_object.run_backup(
                    self.subclient, "incremental", inc_with_data=True)
                # Wait for log backup to complete
                inc_job_log = self.dbhelper_object.get_snap_log_backup_job(inc_job.job_id)
                self.log.info("Log backup job with ID:%s is now completed", inc_job_log.job_id)

                if "native" in self.subclient.snapshot_engine_name.lower():
                    self.log.info(
                        (
                            "Native Snap engine is being run. Backup "
                            "copy job will run inline to snap backup"))
                    self.log.info("Getting the backup job ID of backup copy job")
                    job = self.dbhelper_object.get_backup_copy_job(inc_job.job_id)
                    self.log.info("Job ID of backup copy Job is: %s", job.job_id)
                else:
                    self.log.info(
                        "Running backup copy job for storage policy: %s",
                        self.subclient.storage_policy)
                    self.dbhelper_object.run_backup_copy(self.subclient.storage_policy)
            else:
                self.log.info("Waiting out any active jobs before continuing")
                active_job = self.get_job_obj(time_limit=120)
                while active_job:
                    self.log.info("Waiting for job %s to complete", active_job.job_id)
                    self.wait_for_job_completion(int(active_job.job_id))
                    active_job = self.get_job_obj(time_limit=120)
                self.log.info("Starting Incremental backup job")
                inc_job = self.dbhelper_object.run_backup(
                    self.subclient, "incremental")
            etc = time.mktime(time.localtime(inc_job.summary['lastUpdateTime'] + 5 * 60))
            delta = self.synth_full_run_after * 24 * 3600 + \
                time.mktime(time.localtime(full_job.summary['jobStartTime'])) - etc
            self.move_last_month_jobs(delta)

            wait_time = time.mktime(time.localtime(full_job.summary['lastUpdateTime']))\
                + self.synth_full_run_after * 24 * 3600 + 20 * 60
            synth_full_job = self.get_job_obj(schedule="Synthetic Fulls",
                                              synthfull=True, wait_till=wait_time,
                                              time_interval=30)
            if not synth_full_job:
                raise Exception("Search for job triggered by synthetic full schedule timed out")

        except Exception as exp:
            handle_testcase_exception(self, exp)
