# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies that synthetic full job with multiple MAs involved during backup testcase scenario

TestCase:
    __init__()                      --  Initializes the TestCase class

    setup()                         --  All testcase objects are initializes in this method

    run()                           --  Contains the core testcase logic and it is the one executed

    get_default_ma()                --  Gets the default primary copy MA of storage policy

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This testcase verifies that synthetic full job with multiple MAs involved during backup testcase scenario

        Steps:
            1) Create backupset and subclient
            2) Assign a storage policy which has multiple datapaths.
            3) Run FULL
            4) Switch another datapath as default and run INC.
            5) Repeat #4 for 2-3 jobs making sure every job gets a different MA for backup.
            6) Run single stream SFULL.

        Verification:
            1) Verify each consecutive INC job goes to different MA and not to the same.
            2) SFULL completes successfully
            3) Verify browse and restore results.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - Synthetic full - Multiple MA involved"
        self.tcinputs = {
            'StoragePolicy': None,
        }
        self.storage_policy = None
        self.storage_policy_obj = None
        self.idx_tc = None
        self.cl_machine = None
        self.primary_copy = None

    def setup(self):
        """All testcase objects are initialized in this method"""
        self.cl_machine = Machine(self.client)  # Used by IndexingTestcase class

        self.storage_policy = self.tcinputs['StoragePolicy']
        self.storage_policy_obj = self.commcell.storage_policies.get(self.storage_policy)
        self.primary_copy = self.storage_policy_obj.get_primary_copy()

        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(name=f'{self.id}_sfull_multi_mas', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.storage_policy,
        )

    def run(self):
        """Contains the core testcase logic"""

        jobs_ran = []
        mas_used = [self.get_default_ma()]

        self.log.info('+++ Using [%s] for Full backup +++', mas_used[-1])
        full_job = self.idx_tc.run_backup_sequence(self.subclient, ['New', 'Full'])
        jobs_ran.extend(full_job)

        for i in range(3):
            self.idx_tc.rotate_default_data_path(self.primary_copy)
            mas_used.append(self.get_default_ma())

            if mas_used[-2] == mas_used[-1]:
                self.log.error('MA not changed after rotating default data path')
                self.log.error('Same MA [%s] is used for previous job [%s]', mas_used[-1], jobs_ran[-1].job_id)
                raise Exception(f'Default MA {mas_used[-1]} remained same after rotating default path')

            self.log.info('+++ Using [%s] for Incremental [%s] backup +++', mas_used[-1], i)
            inc = self.idx_tc.run_backup_sequence(self.subclient, ['Edit', 'Incremental'])
            jobs_ran.extend(inc)

        self.log.info('*** Performing a browse restore validation Before Synthetic full ***')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'restore': {
                'do': True,
            }
        })

        self.log.info('+++ Waiting 60 secs before running synthetic full +++')
        self.idx_tc.rotate_default_data_path(self.primary_copy)
        mas_used.append(self.get_default_ma())

        if mas_used[-2] == mas_used[-1]:
            self.log.error('MA not changed after rotating default data path')
            self.log.error('Same MA [%s] is used for previous job [%s]', mas_used[-1], jobs_ran[-1].job_id)
            raise Exception(f'Default MA {mas_used[-1]} remained same after rotating default path')

        self.log.info('+++ Using [%s] for Synthetic full backup +++', mas_used[-1])
        sfull_job = self.idx_tc.run_backup(
            subclient_obj=self.subclient,
            backup_level='Synthetic_full',
            verify_backup=True,
            restore=True
        )

        self.idx_tc.verify_synthetic_full_job(sfull_job, self.subclient)

    def get_default_ma(self):
        """Gets the default primary copy MA of storage policy

            Returns:
                string      -    Name of the primary copy MA

        """
        self.primary_copy.refresh()
        ma_name = self.primary_copy.media_agent
        self.log.info('Current default MA is [%s]', ma_name)
        return ma_name
