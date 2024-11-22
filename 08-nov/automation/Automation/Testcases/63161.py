# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

    This testcase verifies that upon index corruption with certain isam errors, whenever consistency check
    is triggered index is marked as dirty first and then is reconstructed with latest cycle jobs to recover.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    corrupt_index()                             --  Corrupts the index with isam_error[160]

    is_db_marked_dirty()                        -- Checks if the DB is corrupt by checking the presence of .dirtyDb
                                                   file and the value of isDbCorrupt attribute

    verify_db_state_after_auto_recon()          -- Checks if DB after index auto recon is not marked as dirty

    do_browse_to_mark_db_dirty()                -- Performs a browse to mark the DB as dirty

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
    """This testcase verifies that upon index corruption with certain isam errors, whenever consistency check
        is triggered index is marked as dirty first and then is reconstructed with latest cycle jobs to recover.

        Steps:
            1.	Have a backupset and subclient
            2.	Run 2 cycles of jobs for the subclient
            SCENARIO #1
            3.	Corrupt the Index
            4.	Do a browse, verify that the dirty file is created and isdbcorrupt prop is updated in dbprop file while browse fails
            5.	Do another browse, verify that it does auto recon, isdbcorrupt flag is updated and dirty db file is deleted.
            6.	Verify browse returned the right results
            7.  Verify cross cycle browse
            SCENARIO #2
            8.	Corrupt db
            9.	Run a Inc job, verify job completes but it's not played back, marks db as dirty
            10.	Run another Inc to recon the index, and do browse from last two Inc to verify both jobs are played back after recon
            SCENARIO #3
            10.	Corrupt db
            11.	Run sfull, verify that job goes to pending marks db as dirty, suspend and resume the job
            another attempt starts and does recon, ob finishes.
            12.	Do a browse to verify sfull results
            SCENARIO #4
            13.	Corrupt db
            14.	Do a browse, mark the index as dirty with dirty file
            15.	Run index backup to trigger auto recon
            16.	Verify browse restore

    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Automatic Reconstruction - Acceptance'
        self.tcinputs = {
            'StoragePolicy': None,
            'OtherImageTableFilePath': None,
            'VerifyAutoReconWithCreateNewIndex': None,
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
        self.image_table_path_on_local = None
        self.image_table_size_before_copy = None
        self.last_auto_recon_time = 0

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.image_table_path_on_local = self.tcinputs.get('OtherImageTableFilePath')
        self.image_table_size_before_copy = os.path.getsize(self.image_table_path_on_local)
        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))

        self.backupset = self.idx_tc.create_backupset('63161_auto_recon_acceptance', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='63161_auto_recon_acceptance_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            register_idx=True
        )

        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if not self.indexing_level == 'subclient':
            raise Exception('This testcase is specific to subclient level index')

        self.enable_create_new_index = self.tcinputs['VerifyAutoReconWithCreateNewIndex']
        if self.enable_create_new_index:
            self.subclient.index_pruning_type = 'cycles_based'
            self.subclient.index_pruning_cycles_retention = 1
        else:
            self.subclient.index_pruning_cycles_retention = 2

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:
            self.log.info('******* Running 2 cycles of jobs *******')

            jobs = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full', 'Edit', 'Incremental'],
                verify_backup=True
            )
            self.idx_db = index_db.get(self.subclient)
            self.is_machine = self.idx_db.isc_machine
            self.log.info('Index Server Machine is %s', self.is_machine.machine_name)

            self.log.info('****************** Case 1 -  Triggering Auto recon by browse *****************')
            self.corrupt_index()
            self.do_browse_to_mark_db_dirty()
            if not self.is_db_marked_dirty():
                raise Exception('Index is not marked dirty')
            else:
                self.log.info('Index is marked dirty')

            self.log.info('Performing a second browse to recover the corrupt index with index auto recon')
            try:
                self.idx_tc.verify_browse_restore(self.backupset, {
                        'operation': 'browse',
                        'from_time': 0,
                        'to_time': 0
                })
            except Exception as e:
                self.log.info('Browse verification fails with the exception %s', e)
                if 'Index is corrupted for the db' not in e:
                    raise Exception('The browse is failing due to a different issue')
            self.verify_db_state_after_auto_recon()

            self.log.info('Verify that only latest cycle jobs are reconstructed when auto recon is triggered')
            last_cycle_job_ids = []
            for job in jobs[::-1]:
                if job.backup_level == 'Synthetic Full' or job.backup_level == 'Full':
                    last_cycle_job_ids.append(job.job_id)
                    break
                elif job.backup_level == 'Incremental':
                    last_cycle_job_ids.append(job.job_id)
            image_table = self.idx_db.get_table(table='ImageTable')
            image_table_job_ids = image_table.get_column(column='JobId')
            self.log.info('The jobs in the index are %s', image_table_job_ids)
            self.log.info(last_cycle_job_ids)
            if image_table_job_ids[::-1] == last_cycle_job_ids:
                self.log.info('Index auto recon has successfully reconstructed the latest cycle of jobs')
            else:
                raise Exception('Index auto recon has reconstructed the wrong number of cycles')

            self.log.info('Verifying cross cycle browse')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'from_time': jobs[0].start_time,
                'to_time': jobs[3].end_time
            })

            self.log.info('*********** Case 2 -  Triggering Auto recon by running an index backup job ************')
            self.corrupt_index()
            self.do_browse_to_mark_db_dirty()
            self.log.info('Running an index backup job to trigger auto recon')
            self.idx_db.checkpoint_db()
            self.verify_db_state_after_auto_recon()

            self.log.info('************** Case 3 -  Triggering Auto recon by running incremental jobs **************')
            self.corrupt_index()
            jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Edit', 'Incremental', 'Edit', 'Incremental'],
                verify_backup=False
            ))
            self.verify_db_state_after_auto_recon()
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'from_time': 0,
                'to_time': 0
            })

            self.log.info('*********** Case 4 -  Triggering Auto recon by running a synthetic full job ***************')
            self.corrupt_index()
            syn_job = self.idx_tc.cv_ops.subclient_backup(
                self.subclient,
                backup_type="Synthetic_full",
                wait=False,
                advanced_options={
                    'use_multi_stream': True
                }
            )
            jm_obj = JobManager(syn_job, self.commcell)
            jm_obj.wait_for_state(expected_state='pending', retry_interval=10)
            self.log.info('Synthetic full job is in pending state')

            self.log.info('Suspending job')
            syn_job.pause(wait_for_job_to_pause=True)
            self.log.info('Job is suspended, resuming it in [1] minutes')
            time.sleep(60)
            self.log.info('Resuming job')
            syn_job.resume(wait_for_job_to_resume=True)

            jm_obj.wait_for_state(expected_state='completed', retry_interval=30)
            self.log.info('Synthetic full job is completed now')

            self.verify_db_state_after_auto_recon()
            self.subclient.idx.record_job(syn_job)
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'find',
                'job_id': syn_job.job_id,
                'restore': {
                    'do': True
                }
            })

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
        time.sleep(60)
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
                self.log.info('isDBCorrupt attribute is updated as 1')
                return True
            else:
                self.log.info('isDBCorrupt attribute is not updated as expected')
                return False
        else:
            self.log.info('.dirtyDb file not found at %s', dirty_db_file_path)
            return False

    def verify_db_state_after_auto_recon(self):
        """ Checks if DB after index auto recon is not marked as dirty """

        if self.is_db_marked_dirty():
            raise Exception('Index is still marked dirty indicating index auto recon was not triggered')
        else:
            updated_last_auto_recon = self.idx_db.get_db_info_prop(property_name='lastAutomaticIndexRecon')
            if updated_last_auto_recon > self.last_auto_recon_time:
                self.last_auto_recon_time = updated_last_auto_recon
                self.log.info('Timestamp when the index was last auto reconstructed is %s', self.last_auto_recon_time)
                self.log.info('Index auto recon was triggered as the lastAutoRecon time is rightly updated')
            else:
                raise Exception('Index auto recon is not triggered as the lastAutoRecon time is not rightly updated ')
            self.log.info('Index is not marked dirty after index auto recon has been triggered as expected')

    def do_browse_to_mark_db_dirty(self):
        """ Performs a browse to mark the corrupted db as dirty """

        self.log.info('Doing a browse to mark the DB as dirty')
        try:
            self.subclient.browse()
        except Exception as e:
            self.log.info('Browse fails with the exception %s', e)
            if 'Playback failed for job' not in str(e) and 'Index is corrupted for the db' not in str(e):
                raise Exception('The browse is failing due to a different issue')
