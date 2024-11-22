# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This test verifies multi stream synthetic full job

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
    """This test verifies multi stream synthetic full job

        Steps:
            1) Create backupset and subclient
            2) Run FULL, INC, INC, SFULL, INC, INC, SFULL (Here SFULL is multi stream synthetic full job)
            3) Before every backup job switch default datapaths for the storage policy to ensure each job goes to
            different MA.
            4) Verify browse/find and restore results from every SFULL job

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Multi-stream Synthetic full - Acceptance'

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

        self.backupset = self.idx_tc.create_backupset('mssfull_acceptance', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_mssfull',
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
        job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', advanced_options={
            'use_multi_stream': True,
            'use_maximum_streams': False,
            'max_number_of_streams': 50
        })
        self.idx_tc.verify_synthetic_full_job(job, self.subclient)

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', advanced_options={
            'use_multi_stream': True,
            'use_maximum_streams': False,
            'max_number_of_streams': 50
        })
        self.idx_tc.verify_synthetic_full_job(job, self.subclient)
