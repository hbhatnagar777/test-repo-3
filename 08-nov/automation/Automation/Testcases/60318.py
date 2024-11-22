# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that multi stream restore job acceptance scenario works as expected.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    do_restore()                --  Starts the restore job and performs the action like kill, interrupt, continue

    run_restores()              --  Starts multiple restore jobs

    verify_restore()            --  Verifies the restore job after completion

    tear_down()                 --  Teardown function for this test case execution

"""

import time
import threading
import random

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that multi stream restore job acceptance scenario works as expected.

        Steps:
            1) Create backupset and subclient
            2) Have huge testdata like 100k - 1 kb items.
            2) Run FULL - INC - INC - INC - INC
            3) Run multistream restore job
            4) While job is running suspend and resume the job.
            5) Repeat #4 multiple times.
            6) Allow the job to complete.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Multi stream restores'

        self.tcinputs = {
            'TestDataPath': None,
            'RestoreLocation': None,
            'CopyData': None,
            'StoragePolicy': None,
            #  Optional 'InterruptWait': 60
            #  Optional 'Streams': 10
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.total_items = 0
        self.total_size = 0
        self.restore_dir = None
        self.tc_passed = True

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('restore_multi_stream', for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_multi_stream',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.restore_dir = self.cl_machine.join_path(
            self.tcinputs.get('RestoreLocation'),
            self.backupset.backupset_name
        )

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.run_backup_sequence(
            self.subclient,
            ['new', 'copy', 'full', 'edit', 'incremental', 'edit', 'incremental'],
            verify_backup=False
        )

        for path in self.subclient.content:
            self.log.info('Path [%s]', path)

            items = self.cl_machine.number_of_items_in_folder(path, include_only='files', recursive=True)
            self.log.info('=> Number of items [%s]', items)
            self.total_items += items

            size = self.cl_machine.get_folder_size(path, in_bytes=True)
            self.log.info('=> Folder size [%s]', size)
            self.total_size += size

        self.log.info('***** Total items in subclient [%s] Total size [%s]', self.total_items, self.total_size)

        self.run_restores()

        if not self.tc_passed:
            raise Exception('Some restore tasks failed or had issues. Failing testcase')

        self.log.info('All restore tasks completed successfully')

    def do_restore(self, restore_id, action):
        """Starts the restore job and performs the action like kill, interrupt, continue

            Args:
                restore_id      (int)       --     The ID of the restore for tracking

                action          (str)       --     The type of action to perform

            Returns:
                None

        """
        interruption_wait = self.tcinputs.get('InterruptWait', 60)
        restore_path = self.cl_machine.join_path(self.restore_dir, str(restore_id))
        rand_time = random.randint(30, 60)

        self.log.info('Doing restore [%s] action [%s] restore path [%s] in [%s] seconds',
                      restore_id, action, restore_path, rand_time)

        try:
            job = self.backupset.restore_out_of_place(
                client=self.client,
                destination_path=restore_path,
                paths=['/'],
                fs_options={
                    'no_of_streams': self.tcinputs.get('Streams', 10)
                }
            )
        except Exception as e:
            self.log.error('Got exception while trying to start restore job [%s]', e)
            self.tc_passed = False
            return

        self.log.info('Started restore job [%s] for [%s]', job.job_id, restore_id)

        time.sleep(rand_time)

        if action == 'kill':
            self.log.info('Killing job [%s]', job.job_id)
            try:
                if not job.is_finished:
                    job.kill(wait_for_job_to_kill=True)
                    self.log.info('Job [%s] killed successfully', job.job_id)
                else:
                    self.log.info('Job [%s] already finished before killing', job.job_id)
                return True

            except Exception as e:
                self.log.error('Failed to kill job [%s]', e)
                return False

        if action == 'interrupt':
            total_attempts = 6
            attempt = 0
            for attempt in range(1, total_attempts):
                try:
                    self.log.info('Attempt [%s/%s]', attempt, total_attempts - 1)
                    time.sleep(interruption_wait)

                    if not job.is_finished:
                        self.log.info('Suspending the job [%s]', job.job_id)
                        job.pause(wait_for_job_to_pause=True)
                    else:
                        self.log.info('Job already completed [%s]', job.status)
                        break

                    time.sleep(interruption_wait)

                    if not job.is_finished:
                        self.log.info('Resuming the job [%s]', job.job_id)
                        job.resume(wait_for_job_to_resume=True)
                    else:
                        self.log.info('Job already completed [%s]', job.status)
                        break

                except Exception as e:
                    self.log.error('Got exception while trying to suspend/resume job. May be job completed [%s]', e)
                    break

            if attempt < 3:
                self.log.error('Job was not suspended/resumed enough times. Required at least [2] times')

            if job.wait_for_completion():
                self.log.info('Job [%s] completed successfully', job.job_id)
            else:
                self.log.error(
                    'Job [%s] failed to complete. Status [%s] JPR [%s]',
                    job.job_id, job.status, job.delay_reason
                )
                self.tc_passed = False
                return False

        if action == 'complete':
            self.log.info('Waiting for job [%s] to complete', job.job_id)
            if job.wait_for_completion():
                self.log.info('Job [%s] completed successfully', job.job_id)
            else:
                self.log.error('Job [%s] failed to complete', job.job_id)
                self.tc_passed = False
                return False

        self.verify_restore(restore_id, restore_path)

    def run_restores(self):
        """Starts multiple restore jobs"""

        time.sleep(10)

        self.log.info('Deleting previous restore directory [%s]', self.restore_dir)
        self.cl_machine.remove_directory(self.restore_dir)

        threads = []
        actions = [
            (1, 'kill'),
            (2, 'interrupt'),
            (3, 'interrupt'),
            (4, 'complete'),
            (5, 'complete'),
        ]

        for action_info in actions:
            exe_thread = threading.Thread(
                target=self.do_restore,
                args=(action_info[0], action_info[1])
            )
            exe_thread.start()
            threads.append(exe_thread)

        for exe_thread in threads:
            exe_thread.join()

    def verify_restore(self, restore_id, restore_path):
        """Verifies the restore job after completion

            Args:
                restore_id      (int)   --      The ID of the restore for tracking

                restore_path    (str)   --      The path where data is restored

            Returns:
                None

        """

        self.log.info('***** Verifying restore data for [%s] Path [%s] *****', restore_id, restore_path)

        items = self.cl_machine.number_of_items_in_folder(restore_path, include_only='files', recursive=True)
        self.log.info('=> Number of items [%s]', items)

        size = self.cl_machine.get_folder_size(restore_path, in_bytes=True)
        self.log.info('=> Folder size [%s]', size)

        if items != self.total_items:
            self.tc_passed = False
            self.log.error(
                'The number of items restored is not as expected. Expected [%s] Actual [%s]. Diff [%s]',
                self.total_items,
                items,
                self.total_items - items
            )

        if size != self.total_size:
            self.tc_passed = False
            self.log.error(
                'Size of restored items is not as expected. Expected [%s] Actual [%s]. Diff [%s]',
                self.total_size,
                size,
                self.total_size - size
            )

        self.log.info('***** Verification complete for restore id [%s] *****', restore_id)

    def tear_down(self):
        """Teardown function for this test case execution"""

        if self.tc_passed:
            try:
                self.log.info('Deleting previous restore directory [%s]', self.restore_dir)
                self.cl_machine.remove_directory(self.restore_dir)
            except Exception as e:
                self.log.error('Got exception while deleting folder [%s]', e)
