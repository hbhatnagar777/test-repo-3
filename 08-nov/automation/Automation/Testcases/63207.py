# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies if we are able to browse and restore jobs which are soft aged only in CS DB.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies if we are able to browse and restore jobs which are soft aged only in CS DB.

        Steps:
            1) Create 2 subclients
            2) Assign one to tape based SP and other to disk based SP
            3) Run FULL, INC, SFULL, INC, SFULL for the tape subclient
            4) Run FULL, INC, SFULL for the disk subclient
            5) Delete FULL, INC from the tape subclient
            6) Delete the disk subclient
            7) Run data aging job
            8) Disable the global param "Show aged data during browse and recovery"
            9) Browse FULL, INC of the tape subclient = Browse should not give results
            10) Browse INC job from disk subclient = Browse should give results
            11) Enable the global param
            12) Browse FULL, INC of tape subclient = Browse should give results

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Browse of aged job and deleted subclient'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicyTape': None,
            'StoragePolicyDisk': None,
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.tape_sp = None
        self.tape_sp_copy = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.tape_sp = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicyTape'))
        self.tape_sp_copy = self.tape_sp.get_primary_copy()

        self.backupset = self.idx_tc.create_backupset('aged_data', for_validation=True)

        self.subclient_1 = self.idx_tc.create_subclient(
            name='sc1_tape',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicyTape'),
            delete_existing_testdata=True
        )

        self.subclient_2 = self.idx_tc.create_subclient(
            name='sc2_disk',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicyDisk'),
            delete_existing_testdata=False
        )

        self.log.info('Refreshing subclients object')
        self.backupset.subclients.refresh()

    def run(self):
        """Contains the core testcase logic"""

        sc1_jobs = self.idx_tc.run_backup_sequence(
            self.subclient_1,
            ['new', 'full', 'edit', 'incremental', 'synthetic_full', 'edit', 'incremental'],
            verify_backup=False
        )

        sc2_jobs = self.idx_tc.run_backup_sequence(
            self.subclient_2, ['new', 'full', 'edit', 'incremental'], verify_backup=False
        )

        for job in sc1_jobs[:2]:
            self.log.info('Deleting job [%s] from subclient [%s]', job.job_id, self.subclient_1.name)
            self.tape_sp_copy.delete_job(job.job_id)

        self.log.info('Deleting the disk subclient [%s]', self.subclient_2.name)
        self.backupset.subclients.delete(self.subclient_2.name)

        self.log.info('Disabling global param to browse from aged data')
        self.commcell._set_gxglobalparam_value({
            'name': 'ShowAgedDataForBrowseAndRecovery',
            'value': '0'
        })

        self.log.info('***** Running data aging job *****')
        da_job = self.commcell.run_data_aging()
        if not da_job.wait_for_completion():
            self.log.error('Data Aging job [%s] has failed with [%s]. Ignoring.', da_job.job_id, da_job.delay_reason)
        self.log.info('Data aging job [%s] completed successfully', da_job.job_id)

        self.log.info('***** Browsing from the DELETED SUBCLIENT. Job [%s] *****', sc2_jobs[0].job_id)
        self.log.info('Expected: Job must be browsed from deleted subclient')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'job_id': sc2_jobs[1].job_id,
            'restore': {
                'do': True
            }
        })
        self.log.info('***** Browse WORKED as expected from deleted subclient *****')

        self.log.info('***** Browsing from tape subclient deleted job [%s] *****', sc1_jobs[0].job_id)
        self.log.info('Expected: Deleted job must NOT be browsed since global param is OFF')

        browse_options = {
            'job_id': sc1_jobs[0].job_id
        }

        if self.backupset.idx.validate_browse_restore(browse_options) == 0:
            raise Exception('Aged job was browsed though global param is OFF')
        self.log.info('***** Browse did NOT work as expected for deleted job with param OFF *****')

        self.log.info('Enabling global param to browse from aged data')
        self.commcell._set_gxglobalparam_value({
            'name': 'ShowAgedDataForBrowseAndRecovery',
            'value': '1'
        })

        self.log.info('Expected: Deleted job must be browsed since global param is ON')

        browse_options = {
            'job_id': sc1_jobs[0].job_id
        }

        if self.backupset.idx.validate_browse_restore(browse_options) != 0:
            raise Exception('Aged job was not browsed though global param was ON')
        self.log.info('***** Browse WORKED as expected for deleted job with param ON *****')

        self.log.info('Verifying restore from deleted job')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'job_id': sc1_jobs[0].job_id,
            'restore': {
                'do': True
            }
        })

        self.log.info('Disabling global param finally')
        self.commcell._set_gxglobalparam_value({
            'name': 'ShowAgedDataForBrowseAndRecovery',
            'value': '0'
        })

        self.log.info('Verified all scenarios')
