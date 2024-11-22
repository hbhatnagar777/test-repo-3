# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

    This testcase verifies that upon index corruption of a backupset level index, automatic reconstruction of the index
    doesn't happen.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    corrupt_index()                             --  Corrupts the index with isam_error[160]

    is_db_marked_dirty()                        -- Checks if the DB is corrupt by checking the presence of .dirtyDb
                                                   file and the value of isDbCorrupt attribute

    recover_index()                             -- Deletes the DB and reconstructs it to recover from
                                                   corruption

    verify_auto_recon_not_triggered()           -- Checks if DB is still marked as dirty as the index auto recon won't be triggered

"""

import os
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """
    This testcase verifies that upon index corruption of a backupset level index, automatic reconstruction of the index
    doesn't happen.

        Steps:
            1.	Have a backupset and a subclient
            2.	Run 2 cycles of jobs for the subclient
            3.	Corrupt the Index
            4.	Do a browse, verify that the .dirtyDb is created, isDbCorrupt prop is updated in dbprop
                file and browse fails
            5.	Do another browse, verify that it doesn't perform automatic reconstruction of the index and browse
                fails again
            6. Do 3 and run an INC to verify that it marks the DB as corrupt
            7. Trigger another INC job and this job shouldn't trigger the auto recon

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Automatic Reconstruction - BLI'
        self.tcinputs = {
            'StoragePolicy': None,
            'OtherImageTableFilePath': None,
        }
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.indexing_level = None
        self.current_is = None
        self.is_machine = None
        self.idx_db = None
        self.image_table_path_on_local = None
        self.image_table_size_before_copy = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.image_table_path_on_local = self.tcinputs.get('OtherImageTableFilePath')
        self.image_table_size_before_copy = os.path.getsize(self.image_table_path_on_local)
        self.backupset = self.idx_tc.create_backupset('63224_auto_recon_bli', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='63224_auto_recon_bli_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            register_idx=True
        )

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if self.indexing_level == 'subclient':
            raise Exception('This testcase is specific to backupset level index')

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.log.info('******* Running 2 cycles of jobs *******')
            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental'],
                verify_backup=True
                    )

            self.idx_db = index_db.get(self.backupset)
            self.is_machine = self.idx_db.isc_machine

            self.log.info('************ Case 1 -  Triggering Auto recon by browse **************')
            self.corrupt_index()
            self.log.info('Doing a browse to mark the DB as dirty')
            try:
                self.subclient.browse()
            except Exception as e:
                self.log.info('Browse fails with the exception %s', e)
                if 'Playback failed for job' not in str(e):
                    raise Exception('The browse is failing due to a different issue')
            if not self.is_db_marked_dirty():
                raise Exception('Index is not marked dirty even though index is physically corrupt')
            else:
                self.log.info('Index is marked dirty as expected')

            self.log.info('Performing a second browse to verify index auto recon '
                          'is not triggered as index is backupset level index')
            try:
                self.idx_tc.verify_browse_restore(self.backupset, {
                    'operation': 'browse',
                    'from_time': 0,
                    'to_time': 0
                })
            except Exception as e:
                self.log.info('Browse verification fails with the exception %s', e)
                if 'Validation failed. Please refer mismatch in browse/restore results' not in str(e):
                    raise Exception('The browse is failing due to a different issue')
            self.verify_auto_recon_not_triggered()
            self.recover_index()

            self.log.info('************* Case 2 -  Triggering Auto recon by running incremental jobs ****************')
            self.corrupt_index()
            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Edit', 'Incremental', 'Edit', 'Incremental'],
                verify_backup=False
            )
            self.verify_auto_recon_not_triggered()
            self.recover_index()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def corrupt_index(self):
        """ Corrupts the index with isam_error[160] by corrupting the image table of index """

        self.log.info('Corrupting the Index')
        index_path = self.idx_db.db_path
        self.log.info('Replacing Image table file in the index with Image table file of some other index')
        image_table_path = self.is_machine.join_path(index_path, 'ImageTable.dat')
        self.log.info('Deleting image table at %s', image_table_path)
        self.is_machine.delete_file(image_table_path)
        self.log.info('Uploading a different Image Table at the index path')
        self.is_machine.copy_from_local(
            local_path=self.image_table_path_on_local,
            remote_path=index_path
        )
        image_table_size_after_copy = self.is_machine.get_file_size(file_path=image_table_path, in_bytes=True)
        self.log.info('Image table size before copying is %s', self.image_table_size_before_copy)
        self.log.info('Image table size after copying is %s', image_table_size_after_copy)
        if int(image_table_size_after_copy) == self.image_table_size_before_copy:
            self.log.info('Index DB at %s is corrupted', index_path)
        else:
            raise Exception('Size of the Imagetable after getting copied is not same as the original'
                            'file size')

    def is_db_marked_dirty(self):
        """ Checks if the DB is corrupt by checking the presence of .dirtyDb file and
            the value of isDbCorrupt attribute """

        dirty_db_file_path = self.is_machine.join_path(self.idx_db.db_path, '.dirtyDb')
        if self.is_machine.check_file_exists(file_path=dirty_db_file_path):
            self.log.info('.dirtyDb file is created at %s', dirty_db_file_path)
            dirty_db_file_contents = self.is_machine.read_file(file_path=dirty_db_file_path)
            self.log.info('.dirtyDb file xml info: %s', dirty_db_file_contents)
            if int(self.idx_db.get_db_info_prop(property_name='isDbCorrupt')) == 1:
                self.log.info('isDBCorrupt attribute is updated as 1 which is expected')
                return True
            else:
                self.log.info('isDBCorrupt attribute is not updated as expected')
                return False
        else:
            self.log.info('.dirtyDb file not found at %s', dirty_db_file_path)
            return False

    def recover_index(self):
        """ Deletes the DB and reconstructs it to recover from corruption """

        self.idx_db.delete_db()
        self.log.info('Doing a browse to reconstruct the Index after deleting it')
        try:
            self.subclient.browse()
        except Exception as e:
            self.log.info('Browse fails with the exception %s', e)
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'browse',
            'from_time': 0,
            'to_time': 0,
        })

    def verify_auto_recon_not_triggered(self):
        """ Checks if DB is still marked as dirty as the index auto recon won't be triggered"""

        if not self.is_db_marked_dirty():
            raise Exception('Index is not marked dirty indicating that index auto recon is triggered')
        else:
            self.log.info('Index is still marked dirty which is expected for backupset level index'
                          'as index auto recon is not triggered')
