# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies indexing operations like browse, find, restore and synthetic full in Indexing V1 mode
for regression.

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
    """This testcase verifies regression for indexing v1 backup, browse and restore.

        Steps:
            1) Run FULL, INC, SFULL, INC, SFULL
            2) Verify find, browse and restore operations.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - V1 regression'

        self.tcinputs = {
            'TestDataPath': None,
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        if self.idx_help.get_agent_indexing_version(self.client) != 'v1':
            raise Exception('Please use a indexing V1 client for this testcase')

        self.backupset = self.idx_tc.create_backupset('v1_auto', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='v1_auto_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            register_idx=True
        )

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.new_testdata(paths=self.subclient.content)
        self.idx_tc.run_backup(self.subclient, 'FULL', verify_backup=True)

        self.idx_tc.edit_testdata(self.subclient.content)
        self.idx_tc.run_backup(self.subclient, 'INCREMENTAL', verify_backup=True)

        self.idx_tc.edit_testdata(self.subclient.content)
        self.idx_tc.run_backup(self.subclient, 'SYNTHETIC_FULL', verify_backup=True, restore=True)

        self.idx_tc.edit_testdata(self.subclient.content)
        self.idx_tc.run_backup(self.subclient, 'INCREMENTAL', verify_backup=True)

        self.log.info('Verifying BROWSE operation')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'browse',
            'path': '\\',
            'from_time': 0,
            'to_time': 0
        })

        self.idx_tc.edit_testdata(self.subclient.content)
        self.idx_tc.run_backup(self.subclient, 'SYNTHETIC_FULL', verify_backup=True, restore=True)
