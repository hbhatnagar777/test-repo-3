# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to verify the Index pruning feature based on infinite retention option.

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
    """Testcase to verify if index pruning works with infinite retention setting enabled"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - Pruning - Infinite retention"
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

        self.backupset = self.idx_tc.create_backupset('pruning_infinite', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_pruning_infinite',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.subclient.index_pruning_type = 'infinite'
        self.subclient.index_pruning_cycles_retention = 2
        self.subclient.index_pruning_days_retention = 2

        self.log.info(f'********** Number of cycles to be retained [Infinite] **********')

    def run(self):
        """Main function for test case execution

            Steps:
                1) Run 3 backup cycles
                2) Run index pruning (Initialize dbPruneTime and run first checkpoint)
                3) Run one more cycle
                4) Run index pruning (Add checkpoint to info table and make compaction prune the jobs)
                5) Verify no jobs are pruned

        """

        try:

            self.jobs = self.idx_tc.run_backup_sequence(self.subclient, [
                'new', 'full',
                'edit', 'incremental',
                'synthetic_full',
                'edit', 'incremental',
                'synthetic_full',
            ])

            self.idx_db = index_db.get(self.subclient)

            self.log.info('********** Initializing dbPrune time and running first checkpoint **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            # Running one more backup cycle
            self.jobs.extend(self.idx_tc.run_backup_sequence(self.subclient, [
                'edit', 'incremental',
                'synthetic_full',
            ]))

            self.log.info('********** Populate checkpoint info table and making compaction prune the jobs **********')
            if not self.idx_db.prune_db():
                self.log.info('dbPruneTime did not change. No pruning should have happened')

            # No jobs are expected to be pruned in this testcase
            self.idx_help.verify_pruned_jobs(self.idx_db, [])
            self.log.info('********** No jobs are pruned as expected **********')

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
