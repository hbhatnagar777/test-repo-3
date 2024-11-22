# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the checkpoint and compaction operation for subclient level index DBs

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

     run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import commonutils
from AutomationUtils import idautils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db

from cvpysdk.policies.storage_policies import StoragePolicyCopy


class TestCase(CVTestCase):
    """This testcase verifies that the checkpoint and compaction operation for subclient level index DBs"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Subclient level index - Checkpoint and compaction'

        self.tcinputs = {
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.index_db = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            if self.idx_help.get_agent_indexing_level(self.agent) == 'backupset':
                raise Exception('Agent is in backupset level index. Cannot proceed with automation. '
                                'Please move this client-agent to subclient level index')

            self.storage_policy_copy = StoragePolicyCopy(self.commcell, self.tcinputs.get('StoragePolicy'), 'primary')
            self.ida_utils = idautils.CommonUtils(self.commcell)

            self.backupset = self.idx_tc.create_backupset('sli_chk_cmpct', for_validation=True)

            self.subclient = self.idx_tc.create_subclient(
                name='sc_sli_chk_cmpct',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy')
            )

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Run 3 cycles of backup jobs
                2) Run checkpoint. Verify if checkpoint is successful
                3) Age some jobs in the backupset, run data aging.
                4) Run compaction and verify if it completes successfully
                5) Do browse for the entire backupset and check if data from aged jobs are not shown.

        """
        try:

            sc_content = self.subclient.content

            self.log.info('Creating testdata')
            self.idx_tc.new_testdata(self.subclient.content)

            # FULL
            full_job = self.idx_tc.run_backup(self.subclient, backup_level='Full', verify_backup=False)

            # INC
            self.idx_tc.edit_testdata(sc_content)
            inc1_job = self.idx_tc.run_backup(self.subclient, 'incremental', verify_backup=False)

            # SFULL
            sfull1_job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', verify_backup=False)

            # INC
            self.idx_tc.edit_testdata(sc_content)
            inc2_job = self.idx_tc.run_backup(self.subclient, 'incremental', verify_backup=False)

            # SFULL
            sfull2_job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', verify_backup=False)

            # INC
            self.idx_tc.edit_testdata(sc_content)
            inc3_job = self.idx_tc.run_backup(self.subclient, 'incremental', verify_backup=False)

            self.log.info('********** Getting index db object **********')
            self.index_db = index_db.get(self.subclient)

            self.log.info('********* Checkpointing the DB first *********')
            if not self.index_db.checkpoint_db(False):
                raise Exception("Failed to complete index checkpoint")

            self.log.info('********** Deleting backup jobs **********')
            to_be_aged = [inc1_job, sfull1_job, inc2_job]

            for job in to_be_aged:
                job_id = job.job_id
                self.log.info('********** Aging backup job [{0}] **********'.format(job_id))
                self.storage_policy_copy.delete_job(job_id)

                self.log.info('********** Marking job as aged in validation DB **********'.format(job_id))
                self.backupset.idx.do_after_data_aging([job_id])

            self.log.info('********** Running data aging job **********')
            self.ida_utils.data_aging(self.storage_policy_copy.storage_policy, 'primary')

            self.log.info('********* Running compaction *********')
            if not self.index_db.compact_db():
                raise Exception('Failed to perform index compaction')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'path': "/**/*",
                'from_time': commonutils.convert_to_timestamp(full_job.start_time),
                'to_time': commonutils.convert_to_timestamp(sfull2_job.end_time),
                'show_deleted': True,
                'restore': {'do': True}
            })

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
