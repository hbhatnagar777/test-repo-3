# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that suspend and resume of SFULL job where files are backed up extent based

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

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that suspend and resume of SFULL job where files are backed up
    extent based"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Extent based backup - Synthetic full job - Interruption'
        self.show_to_user = False

        self.tcinputs = {
            'StoragePolicyName': None
        }

        self.backupset = None
        self.subclient = None
        self.storage_policy = None

        self.cl_machine = None
        self.cl_delim = None
        self.idx_tc = None
        self.idx_help = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:

            self.backupset_name = self.tcinputs.get('Backupset', 'extent_based_53862')
            self.subclient_name = self.tcinputs.get('Subclient', self.id)
            self.storagepolicy_name = self.tcinputs.get('StoragePolicyName')

            self.cl_machine = Machine(self.client, self.commcell)
            self.cl_delim = self.cl_machine.os_sep

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset(self.backupset_name)

            self.subclient = self.idx_tc.create_subclient(
                name=self.subclient_name,
                backupset_obj=self.backupset,
                storage_policy=self.storagepolicy_name
            )

            self.cl_machine.create_registry(
                'FileSystemAgent', 'bEnableFileExtentBackup', '1', 'DWord')

            self.cl_machine.create_registry(
                'FileSystemAgent', 'mszFileExtentSlabs', '50-1024=4', 'MultiString')

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            sc_content = self.subclient.content

            self.idx_tc.new_testdata(sc_content, large_files=(102400000, 204800000), count=5)
            self.idx_tc.run_backup(self.subclient, 'Full')

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.log.info('********** VERIFICATION 1 - Cycle 1 results **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True
            })

            self.idx_tc.run_interrupt_job(
                self.subclient, 'synthetic_full', phase='Synthetic Full Backup',
                action='suspend_resume', restore=True, wait=12)

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.log.info('********** VERIFICATION 2 - Cycle 2 results **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True
            })

            self.idx_tc.run_interrupt_job(
                self.subclient, 'synthetic_full', phase='Synthetic Full Backup',
                action='suspend_resume', restore=True, wait=12)

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.log.info('********** VERIFICATION 3 - Cycle 3 results **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True
            })

            self.idx_tc.run_interrupt_job(
                self.subclient, 'synthetic_full', phase='Synthetic Full Backup',
                action='kill', wait=12)

            self.idx_tc.run_backup(self.subclient, 'synthetic_full', restore=True)

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        self.backupset.idx.cleanup()
