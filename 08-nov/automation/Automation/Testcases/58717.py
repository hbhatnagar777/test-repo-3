# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that pagination in browse/find results is working as expected.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    tear_down()                 --  Cleans the data created for Indexing validation

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import commonutils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that pagination in browse/find results is working as expected.

        Steps:
            1) Backup some items (example: 1500 files+folders combined)
            2) Run FULL backup.
            3) Set page size to 1000 and do browse operation.
            4) First page should list 1000 and second page should list 500 items.
            5) Repeat 3) for find operation.
            6) Repeat 3) for find but with filter set.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Pagination of browse & find results'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy': None,
            'PageSize': None,
            'FileNameFilter': None,
            'CopyData': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

        self.page_size = None
        self.subclient2 = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('PAGINATION_TEST', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_pagination',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.subclient2 = self.idx_tc.create_subclient(
            name='sc1_pagination2',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.page_size = commonutils.get_int(self.tcinputs.get('PageSize'), 1000)

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""
        try:

            self.idx_tc.copy_testdata(self.subclient.content, self.tcinputs.get('CopyData'))
            self.idx_tc.copy_testdata(self.subclient2.content, self.tcinputs.get('CopyData'))

            self.idx_tc.run_backup(self.subclient, verify_backup=False)
            self.idx_tc.run_backup(self.subclient2, verify_backup=False)

            self.log.info('********** Verifying pagination in BROWSE operation *****')
            self.backupset.idx.validate_browse_restore({
                'operation': 'browse',
                'path': self.cl_machine.os_sep,
                'page_size': self.page_size,
                'restore': {
                    'do': False
                }
            })
            self.log.info('********** BROWSE pagination verified *****')

            self.log.info('********** Verifying pagination in FIND operation *****')
            self.backupset.idx.validate_browse_restore({
                'operation': 'find',
                'page_size': self.page_size,
                'restore': {
                    'do': False
                }
            })
            self.log.info('********** FIND pagination verified *****')

            self.log.info('********** Verifying pagination in FIND + filters operation *****')
            self.backupset.idx.validate_browse_restore({
                'operation': 'find',
                'page_size': 100,
                'filters': [('FileName', self.tcinputs.get('FileNameFilter', '*00*'))],
                'restore': {
                    'do': False
                }
            })
            self.log.info('********** FIND + filters pagination verified *****')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
