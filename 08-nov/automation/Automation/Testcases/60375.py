# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies that synthetic full job does not run when there are no INC/DIFF jobs in the cycle

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This testcase verifies that synthetic full job does not run when there are no INC/DIFF jobs in the cycle

        Steps:
            1) Create backupset and subclient
            2) Run FULL backup
            3) Start SFULL backup
            4) Verify SFULL backup does not start/fail without completing successfully.
            5) Run INC
            6) Run SFULL (this should complete)

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - Synthetic full - Without INC"
        self.tcinputs = {
            'StoragePolicy': None,
        }
        self.storage_policy = None
        self.idx_tc = None
        self.cl_machine = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.storage_policy = self.tcinputs['StoragePolicy']

        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(name=f'{self.id}_sfull_without_inc', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.storage_policy
        )

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.run_backup_sequence(self.subclient, ['New', 'Full'])
        self.log.info('Full backup is done! now immediately running synthetic full without incremental')

        self.log.info('*** Starting Synthetic Full After Full ***')
        sfull_ran = False

        try:
            self.idx_tc.run_backup(self.subclient, backup_level='Synthetic_full')
            sfull_ran = True
        except Exception as e:
            self.log.info('Synthetic full job failed as expected [%s]', e)

        if sfull_ran:
            raise Exception('Synthetic full ran after full job without incremental')

        self.log.info('Running incremental')
        self.idx_tc.run_backup_sequence(self.subclient, ['Edit', 'Incremental'])

        self.log.info('*** Starting Synthetic Full After Incremental ***')
        try:
            self.idx_tc.run_backup(self.subclient, backup_level='Synthetic_full', advanced_options={
                'use_multi_stream': False,
                'use_maximum_streams': False
            })
            self.log.info('Synthetic full ran after running Incremental')
        except Exception as e:
            raise Exception('Synthetic Full job is not running even after Incremental [%s]', e)
