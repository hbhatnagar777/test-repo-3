# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This Testcase tries to check if the results from each of the Synthetic full job are
returned during browse/find and are restored accurately

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    verify_syn_full()                         --    Verifies if RFC is created for
                                                    the Synthetic Full job and validates
                                                    it's browse and restore results.
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This Testcase tries to check if the results from each of the Synthetic full job are
        returned during browse/find and are restored accurately

        Steps:
            1) Create backupset and subclient
            2) Run FULL, INC, INC, SFULL, INC, INC, SFULL (Here SFULL is single stream synthetic full job)
            3) Verify job based browse/find and restore results from every SFULL job
            4) Verify if RFC afile is created
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Acceptance'
        self.tcinputs = {
            'StoragePolicy': None,
        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_acceptance', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""

        self.log.info('******* Run Backup Sequence *******')
        self.idx_tc.run_backup_sequence(
            subclient_obj=self.subclient,
            steps=['New', 'Full', 'Edit', 'Incremental', 'Differential', 'Edit', 'Incremental'],
            verify_backup=True
        )

        syn_job1 = self.idx_tc.run_backup(
            subclient_obj=self.subclient,
            backup_level='Synthetic_full',
            verify_backup=True,
            restore=True
        )

        self.idx_tc.verify_synthetic_full_job(syn_job1, self.subclient)

        self.idx_tc.run_backup_sequence(
            subclient_obj=self.subclient,
            steps=['Edit', 'Incremental', 'Differential', 'Edit', 'Incremental'],
            verify_backup=True
        )

        syn_job2 = self.idx_tc.run_backup(
            subclient_obj=self.subclient,
            backup_level='Synthetic_full',
            verify_backup=True,
            restore=True,
            advanced_options={
                'use_multi_stream': True,
                'use_maximum_streams': True,
                'max_number_of_streams': 3
            }
        )

        self.idx_tc.verify_synthetic_full_job(syn_job2, self.subclient)
