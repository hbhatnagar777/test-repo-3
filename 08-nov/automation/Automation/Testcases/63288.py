# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

    This testcase verifies that upon index corruption with certain isam errors, whenever browse with copy precedence is
     performed, the index auto recon is triggered on the copy's MA only if the copy is a disk copy and not a tape copy


TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    corrupt_index()                             --  Corrupts the index on secondary copy ma with isam_error[160]

    is_db_marked_dirty()                        -- Checks if the DB is corrupt by checking the presence of .dirtyDb
                                                   file and the value of isDbCorrupt attribute

    do_browse_to_mark_db_dirty()                -- Performs a browse to mark the corrupted db as dirty

    do_browse_to_trigger_auto_recon()           -- Performs a browse to try and trigger index auto recon

    recover_index()                             -- Deletes the DB and reconstructs it to recover from
                                                   corruption

"""

import os
import time
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """This testcase verifies that upon index corruption with certain isam errors, whenever browse with copy precedence
     is performed, the index auto recon is triggered on the copy's MA only if the copy is disk copy and not a tape copy

        Steps:
            1.	Have a backupset and subclient
            2.	Run 2 cycles of jobs for the subclient
            3.	Corrupt the Index
            4.	Verify the index on the copy's ma is marked dirty
            5. Verify index auto recon is triggered with browse from secondary disk copy
            6. Verify index auto recon is not triggered with browse from secondary tape copy

    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Automatic Reconstruction - with Copy Precedence'
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
        self.enable_create_new_index = None
        self.secondary_disk_copy = None
        self.secondary_tape_copy = None
        self.image_table_path_on_local = None
        self.image_table_size_before_copy = None
        self.secondary_copy_ma_info = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.image_table_path_on_local = self.tcinputs.get('OtherImageTableFilePath')
        self.image_table_size_before_copy = os.path.getsize(self.image_table_path_on_local)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        storage_policy_secondary_copies = self.storage_policy.get_secondary_copies()

        for copy in range(2):
            if 'disk' in storage_policy_secondary_copies[copy].copy_name:
                self.secondary_disk_copy = storage_policy_secondary_copies[copy]
            elif 'tape' in storage_policy_secondary_copies[copy].copy_name:
                self.secondary_tape_copy = storage_policy_secondary_copies[copy]

        self.backupset = self.idx_tc.create_backupset('63288_auto_recon_copy_precedence', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='63288_auto_recon_copy_precedence_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            register_idx=True
        )

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if not self.indexing_level == 'subclient':
            raise Exception('This testcase is specific to subclient level index')

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.log.info('******* Running 2 cycles of jobs *******')
            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full'],
                verify_backup=True
            )

            self.idx_db = index_db.get(self.subclient)
            self.is_machine = self.idx_db.isc_machine
            self.log.info('Index Server Machine is %s', self.is_machine.machine_name)

            self.log.info('******** Case 1 -  Dont trigger Auto recon by browse if primary copy is tape copy ********')
            self.corrupt_index(is_primary_tape_copy=True)
            self.do_browse_to_mark_db_dirty()
            if not self.is_db_marked_dirty(is_primary_tape_copy=True):
                raise Exception('Index is not marked dirty')
            else:
                self.log.info('Index is marked dirty')
                self.log.info(' Verifying that upon triggering an second browse, index is not auto reconstructed'
                              'as the browse is served from a primary tape copy')
            self.do_browse_to_trigger_auto_recon()
            time.sleep(60)
            if self.is_db_marked_dirty(is_primary_tape_copy=True):
                self.log.info('Index is still marked dirty indicating index auto recon was not triggered')
            else:
                raise Exception('Index is not marked dirty indicating that index auto recon has been triggered')

            self.recover_index()

            self.log.info(' Running Aux Copy job ')
            aux_job = self.storage_policy.run_aux_copy()
            jm_obj2 = JobManager(aux_job, self.commcell)
            jm_obj2.wait_for_state(expected_state='completed', retry_interval=30)

            self.log.info('*********** Case 2 -  Triggering Auto recon by browsing from a secondary copy *********')
            copy_type = 'disk'
            copy_precedence_secondary_disk_copy = self.storage_policy.get_copy_precedence(
                copy_name=self.secondary_disk_copy.copy_name)
            self.log.info('Copy precedence of secondary disk copy is %s', copy_precedence_secondary_disk_copy)
            self.log.info('Perform browse to restore index on the copy ma')
            self.subclient.browse(copy_precedence=copy_precedence_secondary_disk_copy)

            self.corrupt_index(copy_type=copy_type)
            self.do_browse_to_mark_db_dirty(copy_precedence=copy_precedence_secondary_disk_copy)

            if self.is_db_marked_dirty(copy_type=copy_type):
                self.log.info('Index is marked as dirty for the disk copy')
            else:
                raise Exception('Index not marked as dirty')

            self.log.info('Performing a second browse to recover the corrupt index with index auto recon')
            time.sleep(60)
            self.do_browse_to_trigger_auto_recon(copy_precedence= copy_precedence_secondary_disk_copy)

            if not self.is_db_marked_dirty(copy_type=copy_type):
                self.log.info('Index is not marked dirty indicating that index auto recon has been triggered')
            else:
                raise Exception('Index is still marked dirty indicating index auto recon was not triggered')

            self.log.info('*********** Case 3 -  Dont trigger Auto recon by browsing from a tape copy ************')
            second_copy_type = 'tape'
            copy_precedence_secondary_tape_copy = self.storage_policy.get_copy_precedence(
                copy_name=self.secondary_tape_copy.copy_name)
            self.log.info('Copy precedence of tape copy is %s', copy_precedence_secondary_tape_copy)
            self.log.info('Perform browse to restore index on the copy ma')
            self.subclient.browse(copy_precedence=copy_precedence_secondary_disk_copy)

            self.corrupt_index(copy_type=second_copy_type)
            self.do_browse_to_mark_db_dirty(copy_precedence=copy_precedence_secondary_tape_copy)

            if self.is_db_marked_dirty(copy_type=second_copy_type):
                self.log.info('Index is marked as dirty for the tape copy')
            else:
                raise Exception('Index not marked as dirty')

            self.log.info(' Verifying that upon triggering an second browse, index is not auto reconstructed'
                          'as the browse is served from a tape copy')
            self.do_browse_to_trigger_auto_recon(copy_precedence=copy_precedence_secondary_tape_copy)

            time.sleep(60)
            if self.is_db_marked_dirty(copy_type=second_copy_type):
                self.log.info('Index is still marked dirty indicating index auto recon was not triggered')
            else:
                raise Exception('Index is not marked dirty indicating that index auto recon has been triggered')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def corrupt_index(self, copy_type='disk', is_primary_tape_copy=False):
        """ Corrupts the index with isam_error[160] by corrupting the image table of index """

        self.log.info('Corrupting the Index')
        if is_primary_tape_copy:

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
        else:

            if copy_type == 'disk':
                self.log.info(' This is a disk copy, so verifying that index auto recon is supported')
                secondary_copy_ma_name = self.secondary_disk_copy.media_agent
            else:
                self.log.info(' This is a tape copy, so verifying that index auto recon is not supported')
                secondary_copy_ma_name = self.secondary_tape_copy.media_agent

            self.log.info('Media agent is %s', secondary_copy_ma_name)
            secondary_copy_ma = self.commcell.media_agents.get(secondary_copy_ma_name)
            secondary_copy_ma_machine = Machine(secondary_copy_ma_name, self.commcell)
            db_path_for_secondary_copy = secondary_copy_ma_machine.join_path(
                secondary_copy_ma.index_cache_path,
                'CvIdxDB',
                self.backupset.guid,
                self.idx_db.db_guid
            )
            self.log.info('DB path on media agent %s for tape copy is %s', secondary_copy_ma_name,
                          db_path_for_secondary_copy)

            self.secondary_copy_ma_info[copy_type] = {
                'copy_ma_machine': secondary_copy_ma_machine,
                'db_path': db_path_for_secondary_copy
            }
            self.log.info(secondary_copy_ma_machine)
            self.log.info('Corrupting the index')
            image_table_path_on_ma = secondary_copy_ma_machine.join_path(db_path_for_secondary_copy, 'ImageTable.dat')
            self.log.info('Deleting image table at %s', image_table_path_on_ma)
            secondary_copy_ma_machine.delete_file(image_table_path_on_ma)
            self.log.info('Uploading a different Image Table at the index path')
            secondary_copy_ma_machine.copy_from_local(
                local_path=self.image_table_path_on_local,
                remote_path=db_path_for_secondary_copy
            )
            image_table_size_after_copy = secondary_copy_ma_machine.get_file_size(
                file_path=image_table_path_on_ma,
                in_bytes=True
            )
            index_path = db_path_for_secondary_copy

        self.log.info('Image table size before copying is %s', self.image_table_size_before_copy)
        self.log.info('Image table size after copying is %s', image_table_size_after_copy)
        if int(image_table_size_after_copy) == self.image_table_size_before_copy:
            self.log.info('Index DB at %s is now corrupted', index_path)
        else:
            raise Exception(' Size of the Imagetable on secondary copy ma after getting copied is not same '
                            'as the original file size')

    def is_db_marked_dirty(self, copy_type='disk', is_primary_tape_copy=False):
        """ Checks if the DB is corrupt by checking the presence of .dirtyDb file """

        self.log.info('Verifying the creation of .dirtyDb')
        if is_primary_tape_copy:
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
        else:
            secondary_copy_ma_machine = self.secondary_copy_ma_info[copy_type]['copy_ma_machine']
            dirty_db_file_path_secondary_ma = secondary_copy_ma_machine.join_path(
                self.secondary_copy_ma_info[copy_type]['db_path'],
                '.dirtyDb'
            )
            if secondary_copy_ma_machine.check_file_exists(file_path=dirty_db_file_path_secondary_ma):
                dirty_db_file_contents = self.is_machine.read_file(file_path=dirty_db_file_path_secondary_ma)
                self.log.info('.dirtyDb file xml info: %s', dirty_db_file_contents)
                return True
            else:
                return False

    def do_browse_to_mark_db_dirty(self, copy_precedence=0):
        """ Performs a browse to mark the corrupted db as dirty """

        self.log.info('Performing a browse with copy precedence: %s', copy_precedence)
        try:
            self.subclient.browse(copy_precedence=copy_precedence)
        except Exception as e:
            self.log.info('Browse fails with the exception %s', e)
            if 'Playback failed for job' not in str(e) and 'Index is corrupted for the db' not in str(e):
                raise Exception('The browse is failing due to a different issue')

    def do_browse_to_trigger_auto_recon(self, copy_precedence=0):
        """ Performs a browse to try and trigger index auto recon """

        try:
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'browse',
                'copy_precedence': copy_precedence,
                'from_time': 0,
                'to_time': 0
            })

        except Exception as e:
            self.log.info('Browse verification fails with the exception %s', e)
            if 'Validation failed' not in str(e):
                raise Exception('The browse is failing due to a different issue')

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
