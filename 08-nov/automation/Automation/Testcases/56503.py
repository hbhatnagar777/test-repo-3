# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies restore and browse of old checkpoints for indexing feature 'Index pruning'

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initialized in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    browse_verify_job()         --  Browse a pruned job, check only required checkpoint was restored

"""

import random

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This testcase verifies restore and browse of old checkpoints for indexing feature 'Index pruning'"""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Pruning - Restoring and browse of old checkpoints'

        self.tcinputs = {
            'StoragePolicy': None,
        }

        self.backupset_name = None
        self.subclient_name = None

        self.cl_machine = None
        self.idx_tc = None
        self.idx_helper = None
        self.indexing_level = None
        self.idx_db = None

        self.jobs = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.backupset_name = f'PRUNING_BROWSE_RESTORE_OLD_CHECKPOINTS'
        self.subclient_name = f'SUBCLIENT_1'

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.idx_helper = IndexingHelpers(self.commcell)

        self.indexing_level = self.idx_helper.get_agent_indexing_level(self.agent)
        if self.indexing_level != 'subclient':
            raise Exception(f'TestCase valid only for subclient level index.')

        self.backupset = self.idx_tc.create_backupset(name=self.backupset_name, for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name=self.subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )

        # Modify index retention criteria
        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 2

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1 - Create backup jobs and prune db
                2 - Randomly pick jobs are browse
                3 - Check if only the required checkpoint was restored

        """

        try:
            self.log.info('*************** Run backup jobs and pruning ***************')

            self.jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'edit', 'Incremental', 'Synthetic_full', 'edit', 'Incremental', 'Synthetic_full'])
            )
            self.idx_db = index_db.get(self.subclient)
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            self.jobs.extend(
                self.idx_tc.run_backup_sequence(
                    subclient_obj=self.subclient,
                    steps=['edit', 'Incremental', 'Synthetic_full', 'edit', 'Incremental',
                           'Synthetic_full', 'edit', 'Incremental', 'Synthetic_full'])
            )
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            self.jobs.extend(
                self.idx_tc.run_backup_sequence(
                    subclient_obj=self.subclient,
                    steps=['edit', 'Incremental', 'Synthetic_full', 'Full', 'edit', 'Incremental', 'Synthetic_full']
                ))
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            self.log.info('**************** Randomly pick jobs and verify ****************')
            for job in random.sample(self.jobs[:-3], 3):  # Last two cycles are not pruned
                self.browse_verify_job(job)

            self.log.info('**************** SUCCESS, browse and restore works for pruned jobs. ****************')

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.result_string = str(e)
            self.status = constants.FAILED
            self.log.exception(e)

    def browse_verify_job(self, job):
        """Browse a pruned job, check only required checkpoint was restored

            Args:
                job (Job) -- This job will be used for validation

            Raises:
                Exception:
                    If checkpoint was not restored
                    If any extra checkpoint was restored

        """

        self.log.info(f'************* Verify for job with jobId {job.job_id} *************')

        self.log.info(f'Finding checkpoint to be restored for job {job.job_id}')
        checkpoint = self.idx_helper.get_checkpoint_by_job(index_db=self.idx_db, job=job)

        if checkpoint is None:
            raise Exception(f'No checkpoint found for job: {job.job_id}.')

        self.log.info(f"Checkpoint with afileId {checkpoint['afileId']} should be restored.")

        idx_db_name = f"{checkpoint['dbName']}_{checkpoint['commCellId']}_" \
                      f"{checkpoint['startTime']}_{checkpoint['endTime']}"
        idx_db_path = self.idx_db.isc_machine.os_sep.join([self.idx_db.backupset_path, idx_db_name])
        self.log.info(f'Expected IndexDb path: {idx_db_path}')

        scan_dir = self.idx_db.isc_machine.scan_directory

        # expected number of files or folders present after doing a browse on the job
        expected_num_items = len(scan_dir(self.idx_db.backupset_path, recursive=False))
        if not self.idx_db.isc_machine.check_directory_exists(idx_db_path):
            expected_num_items += 1

        self.log.info(f'Performing browse on job: {job.job_id}')
        self.subclient.browse({'job_id': int(job.job_id)})

        self.log.info('Verifying if checkpoint was restored.')
        if not self.idx_db.isc_machine.check_directory_exists(idx_db_path):
            raise Exception(f'Checkpoint was not restored. {idx_db_name}')
        else:
            self.log.info('Checkpoint was restored.')

        self.log.info('Verify if only required checkpoint was restored.')
        num_items_backupset_dir = len(scan_dir(self.idx_db.backupset_path, recursive=False))
        self.log.info('Expected: [%s], Actual in cache: [%s]', expected_num_items, num_items_backupset_dir)

        if num_items_backupset_dir != expected_num_items:
            self.log.error('Unexpected number of items in backupset directory')
