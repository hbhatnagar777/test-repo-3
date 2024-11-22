# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This test verifies that UNC data playback and restore works without issue in Indexing V2 DB.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed


"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This test verifies that UNC data playback and restore works without issue in Indexing V2 DB.

        Steps:
            1. Create a subclient and associate UNC dataset and regular FS dataset.
            2. Run backup jobs ( FULL, INC, SFULL ) with two or more cycles.

        Verification:
            1. Browse and restore both the UNC data and regular FS data from cycle 1 and 2 separately.
            3. View all version for a file
            4. Time range browse and restore of UNC data and FS data covering both cycle 1 and cycle 2
            5. Filtered find

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - UNC testdata"
        self.tcinputs = {
            'StoragePolicy': None,
            'TestDataPath': None,
            'UNCPath': None,
            'UNCUserName': None,
            'UNCPassword': None
        }
        self.cl_machine = None
        self.idx_tc = None
        self.storage_policy = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.storage_policy = self.tcinputs['StoragePolicy']
        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(name='unc_auto', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='unc_auto_sub',
            backupset_obj=self.backupset,
            storage_policy=self.storage_policy
        )

        sc_content = self.subclient.content
        sc_content.append(self.tcinputs['UNCPath'])
        self.subclient.content = sc_content

        self.backupset.idx.register_subclient(self.subclient)

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('Content paths of subclient [%s]', self.subclient.content)

        self.log.info('Performing a login to the UNC path')
        self.cl_machine.list_shares_on_network_path(
            self.tcinputs['UNCPath'],
            self.tcinputs['UNCUserName'],
            self.tcinputs['UNCPassword']
        )

        self.log.info('*** Starting Jobs ***')
        jobs_ran = self.idx_tc.run_backup_sequence(
            self.subclient,
            [
                'NEW', 'Full', 'Edit', 'Incremental', 'Edit', 'Incremental', 'Synthetic_full',
                'Edit', 'Incremental', 'Edit', 'Incremental'
            ]
        )

        self.log.info('***** ALL Jobs are completed, now starting all validations *****')

        self.log.info('*** Starting latest cycle browse-restore validation on FS and UNC data ***')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'browse',
            'restore': {
                'do': True
            }
        })

        self.log.info('*** Timerange browse and restore of FS and UNC data ***')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'from_time': jobs_ran[1].start_timestamp,
            'to_time': jobs_ran[4].end_timestamp,
            'restore': {
                'do': True
            }
        })

        unc_path_with_prefix = 'UNC-NT_' + self.tcinputs['UNCPath'][2:]

        self.log.info(f'*** Scanning UNC path for a test file ***')
        test_file = None
        for file_info in self.cl_machine.scan_directory(self.tcinputs['UNCPath']):
            if file_info['type'] == 'file':
                test_file = file_info['path']
                break
        if test_file is None:
            self.log.info(
                'No file is present under UNC path [%s]. Please include/create files under UNC path',
                unc_path_with_prefix
            )
            raise Exception('No files inside UNC path / Cannot pick files from scan directory')

        self.log.info('Selected test file [%s] for Individual file restore validations', test_file)

        test_file = 'UNC-NT_' + test_file[2:]
        self.log.info('*** Starting Individual file find-restore validations for file [%s] ***', test_file)
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'path': test_file,
            'restore': {
                'do': True,
                'source_items': [test_file]
            }
        })

        self.log.info(f'*** Starting versions validation for file - {test_file} ***')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'versions',
            'path': test_file,
            'restore': {
                'do': False
            }
        })

        self.log.info('Selected [%s] for folder browse-restore validation', unc_path_with_prefix)

        self.log.info(
            '*** Starting Individual folder browse-restore validations for file [%s] ***',
            unc_path_with_prefix
        )

        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'browse',
            'path': unc_path_with_prefix,
            'restore': {
                'do': True,
                'source_items': [unc_path_with_prefix]
            }
        })

        self.log.info('*** Starting filter find validations for file .txt text files ***')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'filters': [('FileName', '*.txt')],
            'restore': {
                'do': True
            }
        })

        self.log.info('**** Completed all validations ****')
