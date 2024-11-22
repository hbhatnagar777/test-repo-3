# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase will verify that queued synthetic full jobs backup the correct data as expected

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    enable_job_queue()          --  Enables the job queue global parameter on the commcell

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase will verify that queued synthetic full jobs backup the correct data as expected

        Steps:
            1) Run FULL backup
            2) Start INC backup, while it is running, start synthetic full backup
            3) Once INC job completes, synthetic full backup will resume and complete.
            4) Verify the results of the synthetic full job.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Queueing Synthetic full job'

        self.tcinputs = {
            'StoragePolicy': None,
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.default_queue_status = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.enable_job_queue()

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('queue_sfull', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_queue_sfull',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

    def run(self):
        """Contains the core testcase logic"""

        try:

            self.idx_tc.run_backup_sequence(
                self.subclient, ['new', 'full', 'edit', 'incremental', 'edit'], verify_backup=True
            )

            queued_jobs = []
            to_queue_jobs = ['incremental', 'synthetic_full']

            for job_type in to_queue_jobs:
                self.log.info('Starting [%s] job to queue', job_type)
                job_obj = self.subclient.backup(job_type)
                self.log.info('[%s] job [%s] started', job_type, job_obj.job_id)
                queued_jobs.append(job_obj)
                self.log.info('[%s] job is [%s]', job_type, job_obj.status)

            for job in queued_jobs:
                self.log.info('Waiting for job [%s] to complete', job.job_id)
                if job.wait_for_completion():
                    self.log.info('Job [%s] completed successfully', job.job_id)
                    self.subclient.idx.record_job(job)

            for job in queued_jobs:
                self.log.info('***** Verifying cycle number and sequence *****')
                self.csdb.execute(f"select fullCycleNum, cycleSequence from jmbkpstats where jobid = '{job.job_id}'")
                query_data = self.csdb.fetch_one_row()
                self.log.info('Cycle, sequence num for job [%s] [%s] is [%s]', job.job_id, job.backup_level, query_data)

                if not query_data:
                    raise Exception('Cannot get cycle number and sequence for job')

                expected_data = {
                    'synthetic full': ['2', '1'],
                    'incremental': ['2', '2']
                }

                cycle_num, cycle_seq = expected_data.get(job.backup_level.lower())
                if str(query_data[0]) != cycle_num or str(query_data[1]) != cycle_seq:
                    raise Exception('Incorrect cycle number/sequence for [%s] job [%s]', job.backup_level, job.job_id)
                self.log.info('Cycle number and sequence matches as expected')

            self.idx_tc.run_backup_sequence(
                self.subclient, ['edit', 'incremental', 'synthetic_full'], verify_backup=True
            )

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if self.default_queue_status is not None and self.default_queue_status != '1':
                self.log.info('Resetting job queue global param to [%s]', self.default_queue_status)
                self.commcell._set_gxglobalparam_value({
                    'name': 'JobsQueuedIfJobsRunning',
                    'value': self.default_queue_status
                })

    def enable_job_queue(self):
        """Enables the job queue global parameter in the commcell"""

        global_param_val = self.commcell.get_gxglobalparam_value('JobsQueuedIfJobsRunning')
        self.default_queue_status = '0' if global_param_val is None else global_param_val
        self.log.info('Default job queue status is [%s]', self.default_queue_status)

        if self.default_queue_status != '1':
            self.log.info('Setting JobsQueuedIfJobsRunning global param to 1')
            self.commcell._set_gxglobalparam_value({
                'name': 'JobsQueuedIfJobsRunning',
                'value': '1'
            })

            if self.commcell.get_gxglobalparam_value('JobsQueuedIfJobsRunning') == '1':
                self.log.info('Job queue global param has been set successfully')
            else:
                raise Exception('Failed to enable job queue global parameter')
