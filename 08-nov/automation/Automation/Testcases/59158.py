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

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59158": {
                    "ClientName": "XXX",
                    "AgentName": "XXX",
                    "InstanceName": "XXX",
                    "BackupsetName": "XXX",
                    "SubclientName": "XXX",
                    "SqlSaPassword": "XXX"
                }
            }

"""

import sys
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from MediaAgents.MAUtils.mahelper import MMHelper
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Class for validation of weekly conversion to full backups for DB Agents"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "DB agents - verification of weekly conversion to full jobs"
        self.mmhelper = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "SubclientName": None,
            "SqlSaPassword": None
        }

    def setup(self):
        self.mmhelper = MMHelper(self)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    @test_step
    def get_job_obj(self, schedule=None, time_limit=2):
        """Gets the job object from active jobs of commcell
            Args:
                schedule: schedule which triggered the job
                    default: None
                time_limit: Time limit to wait for job in minutes
                    default: 2
            Returns: Job object
        """
        agents_with_backupset = ['postgresql', 'db2']
        active_job = None
        time_limit = time.time() + time_limit * 60
        while time.time() <= time_limit and active_job is None:
            self.log.info("Waiting for 10 seconds before checking for active job")
            time.sleep(10)
            active_jobs = self.commcell.job_controller.active_jobs(
                client_name=self.tcinputs['ClientName'], job_filter="Backup")
            for job_id in active_jobs:
                job = self.commcell.job_controller.get(job_id)
                job_of_backupset = True
                if self.tcinputs['AgentName'] in agents_with_backupset:
                    job_of_backupset = job.backupset_name == self.tcinputs["BackupsetName"]
                job_of_subclient = job.subclient_name == self.tcinputs["SubclientName"]
                job_of_schedule = True
                if schedule:
                    job_of_schedule = False
                    if 'scheduleName' in job.details['jobDetail']['generalInfo']:
                        job_of_schedule = \
                            job.details['jobDetail']['generalInfo']['scheduleName'] == schedule
                if job_of_subclient and \
                        job.instance_name == self.tcinputs["InstanceName"] and job_of_backupset \
                        and job_of_schedule:
                    active_job = job
                    break
        return active_job

    def run(self):
        """ Main function for test case execution """
        try:
            if 'planEntity' not in self.instance.properties:
                raise Exception('Ensure instance is associated with a plan')
            agents_with_backupset = ['postgresql', 'db2']
            self.log.info("Starting backup job")
            job1 = self.subclient.backup('full')
            self.log.info("Backup job launched with id %s", job1.job_id)
            self.wait_for_job_completion(int(job1.job_id))
            self.log.info("Waiting out any active jobs before moving jobs back")
            active_job = self.get_job_obj(time_limit=2)
            while active_job:
                self.log.info("Waiting for job %s to complete", active_job.job_id)
                self.wait_for_job_completion(int(active_job.job_id))
                active_job = self.get_job_obj()
            jobs_in_past_week = self.commcell.job_controller.finished_jobs(
                client_name=self.tcinputs['ClientName'], lookup_time=168, limit=sys.maxsize)
            for job_id in jobs_in_past_week:
                job = self.commcell.job_controller.get(job_id)
                if self.tcinputs['AgentName'] in agents_with_backupset:
                    job_of_backupset = job.backupset_name == self.tcinputs["BackupsetName"]
                else:
                    job_of_backupset = True
                if job.subclient_name == self.tcinputs["SubclientName"] and\
                        job.instance_name == self.tcinputs["InstanceName"] and\
                        job_of_backupset and job.backup_level.endswith('Full'):
                    self.mmhelper.move_job_start_time(job_id, reduce_days=8)
            self.log.info("Running incremental backup schedule now")
            self.subclient.schedules.get("incremental backup schedule").run_now()
            job = self.get_job_obj(schedule="Incremental backup schedule")
            if not job:
                raise Exception("Search for job timed out")
            self.log.info("%s job is %s backup job", job.job_id, job.backup_level)
            try:
                assert job.backup_level == 'Full'
            except AssertionError:
                self.status = constants.FAILED
                raise Exception("Backup job after 1 week is not converted to Full backup")
            self.log.info('Verified backup job is converted to FULL')

        except Exception as exp:
            handle_testcase_exception(self, exp)
