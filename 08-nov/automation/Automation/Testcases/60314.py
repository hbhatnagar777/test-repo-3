# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies multi stream synthetic full's suspend and resume scenario

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    suspend_resume_job()        --  Suspends and resumes a job multiple times

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies multi stream synthetic full's suspend and resume scenario

        Steps:
            1) Create backupset and subclient
            2) Have testdata with atleast 100K 1KB items.
            3) Run FULL -> INC -> INC -> INC
            4) Start multi stream synthetic full.
            5) Suspend and resume synthetic full job all along the job multiple times in an interval
            6) Verify SFULL completes.
            7) Verify if SFULL completes successfully.
            8) Verify browse and restore from SFULL job.
            9) Verify application size and total number of items backed up.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Suspend and resume'

        self.tcinputs = {
            'TestDataPath': None,
            'RestoreLocation': None,
            'CopyData': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.storage_policy = None
        self.primary_copy = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.primary_copy = self.storage_policy.get_primary_copy()

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_suspend_resume', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.run_backup_sequence(self.subclient, ['new', 'copy', 'full'], verify_backup=True)

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.idx_tc.rotate_default_data_path(self.primary_copy)

        job = self.idx_tc.cv_ops.subclient_backup(
            self.subclient,
            backup_type='Synthetic_full',
            wait=False
        )
        jm_obj = JobManager(job, self.commcell)

        self.log.info('Trying to interrupt job at Backup phase')
        jm_obj.wait_for_phase(phase='Synthetic Full Backup', total_attempts=120, check_frequency=1)
        self.log.info('Job is at backup phase, suspending job in [5] seconds')
        self.suspend_resume_job(job, 6)

        self.log.info('Trying to interrupt job at Archive index phase')
        jm_obj.wait_for_phase(phase='Archive Index', total_attempts=120, check_frequency=10)
        self.log.info('Job is at archive index phase, suspending job in [5] seconds')
        self.suspend_resume_job(job, 6)

        jm_obj.wait_for_state('completed')
        self.log.info('Job completed successfully')

        self.backupset.idx.record_job(job)

        self.idx_tc.verify_job_find_results(job, self.backupset.idx, restore=True)
        self.idx_tc.verify_synthetic_full_job(job, self.subclient)

    def suspend_resume_job(self, job, total_attempts=6):
        """Suspends and resumes a job multiple times

            Args:
                job             (obj)   --      The job object to suspend and resume

                total_attempts  (int)   --      The number of attempts to interrupt

            Returns:
                None

        """

        self.log.info('Trying to suspend and resume job [%s]', job.job_id)
        attempt = 0

        for attempt in range(1, total_attempts):
            try:
                self.log.info('Attempt [%s/%s]', attempt, total_attempts-1)
                time.sleep(10)

                if not job.is_finished:
                    self.log.info('Suspending the job [%s]', job.job_id)
                    job.pause(wait_for_job_to_pause=True)
                else:
                    self.log.info('Job already completed [%s]', job.status)
                    break

                self.idx_tc.rotate_default_data_path(self.primary_copy)
                time.sleep(10)

                if not job.is_finished:
                    self.log.info('Resuming the job [%s]', job.job_id)
                    job.resume(wait_for_job_to_resume=True)
                else:
                    self.log.info('Job already completed [%s]', job.status)
                    break

            except Exception as e:
                self.log.error('Got exception while trying to suspend/resume job. May be job completed [%s]', e)
                break

        if attempt < 3:
            self.log.error('Job was not suspended/resumed enough times. Required at least [2] times')
