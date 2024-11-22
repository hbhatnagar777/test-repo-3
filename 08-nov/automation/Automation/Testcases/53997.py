# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to verify the Index pruning feature based on cycle based retention option.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Deletes old index cache if test case passes
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase
from Indexing.database import index_db


class TestCase(CVTestCase):
    """Testcase to verify if index pruning works with cycles based setting enabled"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - Pruning - Cycle based"
        self.tcinputs = {
            "StoragePolicy": None
        }

        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None

    def setup(self):
        """Setup function of this test case"""

        self.cl_machine = Machine(self.client, self.commcell)
        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        if self.idx_help.get_agent_indexing_level(self.agent) == 'backupset':
            raise Exception('Agent is in backupset level index. Cannot proceed with automation. '
                            'Please move this client-agent to subclient level index')

        self.backupset = self.idx_tc.create_backupset('pruning_cycle_based', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_pruning_cycle',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        retained_cycles = 3
        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = retained_cycles

        self.log.info(f'********** Number of cycles to be retained [{retained_cycles}] **********')

    def run(self):
        """Main function for test case execution

            Steps:
                1) Run 3 backup cycles
                2) Run pruning (Initialize the dbPrune time and run first checkpoint)
                3) Verify no jobs are pruned
                4) Run 1 more backup cycle
                5) Run pruning (Add checkpoint to info table and make compaction prune the jobs)
                6) verify the first cycle is pruned
                7) Run 1 more backup cycle
                8) Run pruning (Add checkpoint to info table and make compaction prune the jobs)
                9) Verify the second cycle is pruned
                10) Do browse of the first cycle and check if results come as expected.

        """

        try:

            self.jobs = self.idx_tc.run_backup_sequence(self.subclient, [
                'new', 'full', 'edit', 'incremental',
                'synthetic_full', 'edit', 'incremental',
                'synthetic_full', 'edit', 'incremental'
            ])

            self.idx_db = index_db.get(self.subclient)

            self.log.info('********** Initializing dbPrune time and running first checkpoint **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            # Expecting no jobs to be pruned
            expected_pruned_jobs = []
            self.idx_help.verify_pruned_jobs(self.idx_db, expected_pruned_jobs)
            self.log.info('********** #0 - No jobs are pruned as expected **********')

            # Running one more backup cycle
            self.jobs.extend(self.idx_tc.run_backup_sequence(self.subclient, [
                'synthetic_full', 'edit', 'incremental'
            ]))

            self.log.info('********** Populate checkpoint info table and making compaction prune the jobs **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            # First 2 jobs are expected to be pruned
            expected_pruned_jobs = [self.jobs[0].job_id, self.jobs[1].job_id]
            self.idx_help.verify_pruned_jobs(self.idx_db, expected_pruned_jobs, refresh=True)
            self.log.info('********** #1 - Jobs are pruned as expected **********')

            # Running one more backup cycle
            self.jobs.extend(self.idx_tc.run_backup_sequence(self.subclient, [
                'synthetic_full', 'edit', 'incremental'
            ]))

            self.log.info('********** Populate checkpoint info table and making compaction prune the jobs **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            # Add one more cycle to the prune job list and check if it is pruned
            expected_pruned_jobs.extend([self.jobs[2].job_id, self.jobs[3].job_id])
            self.idx_help.verify_pruned_jobs(self.idx_db, expected_pruned_jobs, refresh=True)
            self.log.info('********** #2 - Jobs are pruned as expected **********')

            # Do browse for one of the pruned job
            self.subclient.idx.validate_browse_restore({
                'job_id': self.jobs[1].job_id,
                'restore': {
                    'do': False
                }
            })

            self.log.info('********** All tests PASSED **********')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: {0}'.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        try:
            if self.idx_db and self.idx_db.exported_db:
                self.idx_db.exported_db.cleanup()

            if self.status == constants.PASSED:
                self.backupset.idx.cleanup()
        except Exception as exp:
            self.log.exception(exp)
