# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies backup, browse, find and restore for large file extents feature

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies the backup, browse and restore feature for large file extents"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Extent based backup - Browse, find, versions, restore'
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

            self.backupset_name = self.tcinputs.get('Backupset', 'extent_based_53861')
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
            cycle1_start = int(time.time())

            self.idx_tc.new_testdata(sc_content, large_files=(102400000, 204800000))
            self.idx_tc.run_backup(self.subclient, 'Full')

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.log.info('********** VERIFICATION 1 - Find cycle 1 **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True,
                'restore': {'do': True}
            })

            cycle1_end = int(time.time())

            self.idx_help.verify_extents_files_flag(self.backupset, 102400000)

            self.idx_tc.run_backup(self.subclient, 'synthetic_full', restore=True)

            self.idx_help.verify_extents_files_flag(self.backupset, 102400000)

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.idx_tc.edit_testdata(sc_content)
            self.idx_tc.run_backup(self.subclient, 'Incremental')

            self.log.info('********** VERIFICATION 2 - Find cycle 2 **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': False,
                'restore': {'do': True}
            })

            active_file = self.backupset.idx.get_items(
                parent='large_files', name='edit_file', type='file', cycle=2)

            self.log.info('********** VERIFICATION 3 - Restore of single large file **********')
            self.log.info('Large file to be restored [{0}]'.format(active_file))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True,
                'restore': {
                    'do': True,
                    'source_items': [active_file]
                }
            })

            active_dir = self.backupset.idx.get_items(
                name='large_files', type='directory', status='modified', cycle=2)

            self.log.info('********** VERIFICATION 4 - Restore of large files folder **********')
            self.log.info('Large files folder for restore [{0}]'.format(active_dir))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True,
                'restore': {
                    'do': True,
                    'source_items': [active_dir]
                }
            })

            deleted_file = self.backupset.idx.get_items(
                parent='large_files', name='delete_file', type='file', status='deleted', cycle=2)

            self.log.info('********** VERIFICATION 5 - Restore of large deleted file **********')
            self.log.info('Large deleted file for restore [{0}]'.format(deleted_file))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True,
                'restore': {
                    'do': True,
                    'source_items': [deleted_file]
                }
            })

            self.log.info('********** VERIFICATION 6 - Restore of large deleted file **********')
            self.log.info('Large deleted file for restore [{0}]'.format(deleted_file))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'show_deleted': True,
                'restore': {
                    'do': True,
                    'source_items': [deleted_file]
                }
            })

            self.log.info('********** VERIFICATION 7 - Cycle 1 find and restore **********')
            self.log.info('Timerange of cycle 1 [{0}] [{1}]'.format(cycle1_start, cycle1_end))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'from_time': cycle1_start,
                'to_time': cycle1_end,
                'show_deleted': True,
                'restore': {
                    'do': True
                }
            })

            self.log.info('********** VERIFICATION 8 - View all versions of large file and '
                          'restore **********')
            self.log.info('View all versions for file [{0}]'.format(active_file))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'versions',
                'path': active_file,
                'restore': {
                    'do': True,
                    'source_items': [active_file],
                    'select_version': 'all'
                }
            })

            self.log.info('********** VERIFICATION 9 - Restore previous version file **********')
            self.log.info('View all versions for file [{0}]'.format(active_file))

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'versions',
                'path': active_file,
                'restore': {
                    'do': True,
                    'source_items': [active_file],
                    'select_version': 1
                }
            })

            self.idx_tc.run_backup(self.subclient, 'synthetic_full', restore=True)

            self.log.info('********** VERIFICATION 10 - Browse latest cycle **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'browse',
                'path': self.cl_delim,
                'restore': {
                    'do': False
                }
            })

            self.idx_help.verify_quota_size(self.backupset, self.cl_machine)

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        self.backupset.idx.cleanup()
