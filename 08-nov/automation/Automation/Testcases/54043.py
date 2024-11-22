# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to verify the Index pruning feature based on days based retention option.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    move_system_time()          --  Moves MA system time ahead

    tear_down()                 --  Deletes old index cache if test case passes
"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase
from Indexing.database import index_db


class TestCase(CVTestCase):
    """Testcase to verify if index pruning works with days based setting enabled"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - Pruning - Days based"
        self.tcinputs = {
            "StoragePolicy": None
        }

        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None
        self.time_changed = False
        self.retained_days = 2

    def setup(self):
        """Setup function of this test case"""

        self.cl_machine = Machine(self.client, self.commcell)
        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        if self.idx_help.get_agent_indexing_level(self.agent) == 'backupset':
            raise Exception('Agent is in backupset level index. Cannot proceed with automation. '
                            'Please move this client-agent to subclient level index')

        self.backupset = self.idx_tc.create_backupset('pruning_days_based', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_pruning_days',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.subclient.index_pruning_type = 'days_based'
        self.subclient.index_pruning_days_retention = self.retained_days

        self.log.info(f'********** Number of days of job to be retained [{self.retained_days}] **********')

    def run(self):
        """Main function for test case execution

            Steps:
                1) Run 2 backup cycles
                2) Run index pruning (initialize dbPruneTime and run first checkpoint)
                3) Run one more cycle.
                2) Move MA time to 2 days ahead
                3) Run index pruning (Add checkpoint to info table and make compaction prune the jobs)
                6) Verify if the first cycle is aged
                4) Reset the MA time.

        """

        try:

            self.jobs = self.idx_tc.run_backup_sequence(self.subclient, [
                'new', 'full',
                'edit', 'incremental',
                'synthetic_full',
            ])

            self.idx_db = index_db.get(self.subclient)

            self.log.info('********** Initializing dbPrune time and running first checkpoint **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            # Running new backup cycle
            self.jobs.extend(self.idx_tc.run_backup_sequence(self.subclient, [
                'edit', 'incremental',
                'synthetic_full'
            ]))

            self.log.info('********** Move time to 2 days and verify job is pruned **********')
            self.move_system_time(self.retained_days)

            self.log.info('********** Populate checkpoint info table and making compaction prune the jobs **********')
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            expected_pruned_jobs = [self.jobs[0].job_id, self.jobs[1].job_id]
            self.idx_help.verify_pruned_jobs(self.idx_db, expected_pruned_jobs)

            # Do browse for one of the pruned job
            self.subclient.idx.validate_browse_restore({
                'job_id': self.jobs[0].job_id,
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

        finally:
            try:
                if self.time_changed:
                    self.log.info('********** Resetting the MA time **********')
                    self.idx_db.isc_machine.change_system_time(-86400 * self.retained_days)
                    self.idx_db.isc_machine.toggle_time_service(stop=False)
                    time.sleep(30)
                    self.log.info(f'After reset machine time [{self.idx_db.isc_machine.current_time()}]')
            except Exception as exp:
                self.log.exception(exp)

    def move_system_time(self, days):
        """Moves MA system time ahead

            Args:
                days        (int)   --      The number of days to move

            Returns:
                None

        """

        self.log.info(f'Current machine time [{self.idx_db.isc_machine.current_time()}]')

        try:
            self.idx_db.isc_machine.toggle_time_service(stop=True)
            self.idx_db.isc_machine.change_system_time(86400 * days)
        except Exception as exp:
            self.log.exception(exp)
            self.log.error('Exception while changing system time. Ignoring and proceeding further')

        self.time_changed = True

        time.sleep(30)
        self.log.info(f'After change machine time [{self.idx_db.isc_machine.current_time()}]')

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        try:
            if self.idx_db and self.idx_db.exported_db:
                self.idx_db.exported_db.cleanup()

            if self.status == constants.PASSED:
                self.backupset.idx.cleanup()
        except Exception as exp:
            self.log.exception(exp)
