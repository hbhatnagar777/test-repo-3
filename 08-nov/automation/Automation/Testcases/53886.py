# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies delete data operation

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
from AutomationUtils import commonutils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies delete data browse feature"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Delete Data By Browse'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.index_db = None
        self.to_erase_items = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset('delete_data_auto', for_validation=True)

            self.subclient = self.idx_tc.create_subclient(
                name='sc_delete_data',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs['StoragePolicy']
            )

            self.sc_content = self.subclient.content

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Run FULL backup
                2) Checkpoint the DB
                3) Run INC backup
                4) Do delete data operation
                5) Verify browse and restore if deleted data is not shown
                6) Run SFULL and verify if deleted data is not backed up
                7) Verify transaction ID
                8) Run checkpoint to backup the live logs and verify committed transaction ID
                9) Delete DB and live logs and do browse to start playback
                10) Verify browse if playback had completed, live logs are applied and delete data is not shown

        """

        try:

            self.log.info('********** Creating testdata **********')
            self.idx_tc.new_testdata(self.sc_content, count=1)
            self.create_data_to_delete('erase_1')

            self.log.info('********** Running FULL **********')
            inc_job = self.idx_tc.run_backup(self.subclient, 'Full', verify_backup=False)

            self.log.info('********** Checkpointing the DB **********')
            if self.idx_help.get_agent_indexing_level(self.agent) == 'subclient':
                self.index_db = index_db.get(self.subclient)
            else:
                self.index_db = index_db.get(self.backupset)

            self.index_db.checkpoint_db()

            self.do_delete_data()

            self.idx_tc.edit_testdata(self.sc_content)
            self.create_data_to_delete('erase_2')
            self.idx_tc.run_backup(self.subclient, 'incremental', verify_backup=False)

            self.do_delete_data()

            self.log.info('********** Verifying result of backupset **********')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'path': "/**/*",
                'show_deleted': True,
                'restore': {'do': False}
            })

            self.log.info('********** Running SFULL **********')
            self.idx_tc.run_backup(self.subclient, 'synthetic_full', verify_backup=False)

            self.log.info('********** Verifying result of backupset after SFULL **********')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'path': "/**/*",
                'show_deleted': True,
                'restore': {'do': False}
            })

            self.log.info('********** Checking transaction ID in dbInfo file **********')
            transaction_id = self.index_db.get_db_info_prop('transactionId')
            self.log.info('Transaction ID is [{0}]'.format(transaction_id))
            if transaction_id == 2:
                self.log.info('Transaction ID 2 is correct and verified')
            else:
                raise Exception('Transaction ID is incorrect')

            self.log.info('********** Running checkpoint to backup live logs **********')
            self.index_db.checkpoint_db(registry_keys=False)

            if len(self.index_db.get_index_db_live_log_checkpoints()) == 1:
                self.log.info('Live logs are checkpointed')
            else:
                raise Exception('Live log is not checkpointed')

            committed_tid = self.index_db.committed_transaction_id
            if committed_tid == '2':
                self.log.info('2 transactions are checkpointed and verified')
            else:
                raise Exception('Committed transaction ID is not updated after checkpoint')

            self.log.info('********** Killing IndexServer, deleting DB and live logs **********')
            self.index_db.isc_machine.kill_process('cvods')
            self.index_db.delete_db()
            self.index_db.delete_live_logs()

            self.log.info('********** Verifying result after playback **********')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'path': "/**/*",
                'to_time': commonutils.convert_to_timestamp(inc_job.end_time),
                'show_deleted': True,
                'restore': {'do': False}
            })

            self.log.info('********** Delete data automation verified **********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def create_data_to_delete(self, name='erase'):
        """Creating files and folder to delete data"""

        items = []

        for path in self.sc_content:
            erase_dir = self.cl_machine.os_sep.join([
                path, name + '_dir'
            ])

            erase_file = self.cl_machine.os_sep.join([
                path, name + '_file.txt'
            ])

            self.cl_machine.create_file(erase_file, '1')
            self.idx_tc.create_only_files(path, base_dir=(name + '_dir'), count=2)

            items.append(erase_dir)
            items.append(erase_file)

        self.to_erase_items.append(items)  # [[file1, dir1], [file2, dir2]]

    def do_delete_data(self):
        """Performs delete data operation, updates the validation DB and deletes the items from the source"""

        for items in self.to_erase_items:
            self.log.info('Deleting items [{0}]'.format(items))

            self.log.info('********** Doing delete data operation **********')
            self.backupset.delete_data(items)

            self.log.info('********** Marking items deleted in validation DB **********')
            self.backupset.idx.do_delete_items(items)

            self.log.info('********** Deleting the items from the source **********')
            for item in items:
                self.log.info('Item [{0}]'.format(item))
                if '.txt' in item:
                    self.cl_machine.delete_file(item)
                else:
                    self.cl_machine.remove_directory(item)

        self.to_erase_items.clear()

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        self.log.info('Cleaning validation DB data for backupset')
        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
