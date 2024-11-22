# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that INC in parallel with SFULL testcase works as expected.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    run_sfull_inc_parallel()    --  Runs the incremental backup in parallel with SFULL and does various
    verification after completion

    verify_cycle_number()       --  Verifies the cycle number for the job

    verify_latest_cycle_browse()    --  Verifies browse and restore from latest cycle

    verify_versions_file()      --  Verifies view all versions of a file

    get_versions_file()         --  Gets a random file to do view all versions

    check_job_starts()          --  Checks if a new job starts

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies that INC in parallel with SFULL testcase works as expected.

        Steps:
            1) Create backupset and subclient
            2) Have testdata with atleast 100K 1KB items.
            3) Run FULL -> INC
            4) Start Synthetic full job, suspend it
            5) Run INC -> INC. Resume and complete the synthetic full job.
            6) Verify browse/restore of latest cycle, INC, SFULL jobs
            7) Verify the cycle number of INC job.
            8) Verify view all versions of a file.
            9) Repeat #4 - #8 for 3rd cycle
            10) Delete DB and try full reconstruction
            11) Run new SFULL, suspend it and verify FULL, SFULL is not running.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Parallel INC job with Synthetic Full job'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('parallel_inc_sfull', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_parallel_inc_sfull',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if indexing_level == 'subclient':
            self.subclient.index_pruning_type = 'cycles_based'
            self.subclient.index_pruning_cycles_retention = 4

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('+++++ TESTCASE 1 - Acceptance +++++')

        cycle_first = self.idx_tc.run_backup_sequence(
            self.subclient,
            ['new', 'full', 'edit', 'incremental'],
            verify_backup=False
        )

        self.run_sfull_inc_parallel(inc_cycle='2')
        self.log.info('+++++ TESTCASE 1 - Complete +++++')

        self.log.info('+++++ TESTCASE 2 - Continuing cycle +++++')
        self.run_sfull_inc_parallel(inc_cycle='3')
        self.log.info('+++++ TESTCASE 2 - Complete +++++')

        self.log.info('+++++ TESTCASE 2 - Continuing cycle +++++')

        self.log.info('+++++ TESTCASE 3 - Full reconstruction +++++')

        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        idx_db = index_db.get(self.subclient if indexing_level == 'subclient' else self.backupset)

        self.log.info('Deleting the DB [%s]', idx_db.backupset_path)
        idx_db.delete_db()

        self.log.info('Restarting IndexServer services [%s]', idx_db.index_server.client_name)
        idx_db.index_server.restart_services(wait_for_service_restart=True)

        self.idx_tc.run_backup_sequence(
            self.subclient,
            ['synthetic_full', 'edit', 'incremental'],
            verify_backup=True
        )

        self.log.info('+++++ TESTCASE 3 - Complete +++++')

        self.log.info('+++++ TESTCASE 4 - FULL, SFULL while SFULL is running +++++')

        job = self.idx_tc.cv_ops.subclient_backup(
            self.subclient,
            backup_type='Synthetic_full',
            wait=False,
            advanced_options={
                'use_multi_stream': True,
                'use_maximum_streams': False,
                'max_number_of_streams': 50
            }
        )
        jm_obj = JobManager(job, self.commcell)
        time.sleep(5)

        if not job.is_finished:
            self.log.info('***** Suspending synthetic full job [%s] *****', job.job_id)
            job.pause(wait_for_job_to_pause=True)
        else:
            raise Exception('Synthetic full job completed ahead')

        if self.check_job_starts('Full'):
            raise Exception('Full job started unexpectedly when SFULL is running')
        else:
            self.log.info('Full job did not run as expected')

        if self.check_job_starts('synthetic_full'):
            raise Exception('SFull job started unexpectedly when SFULL is running')
        else:
            self.log.info('SFull job did not run as expected')

        self.log.info('***** Resuming synthetic full job [%s] *****', job.job_id)
        job.resume(wait_for_job_to_resume=True)

        jm_obj.wait_for_state('completed')
        self.log.info('Synthetic full job completed successfully')
        self.backupset.idx.record_job(job)

        self.log.info('+++++ TESTCASE 4 - Complete +++++')

        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'show_deleted': True,
            'from_time': cycle_first[0].start_timestamp,
            'to_time': job.end_timestamp,
            'filters': [('FileName', '*.*')],
            'restore': {
                'do': True
            }
        })

    def run_sfull_inc_parallel(self, inc_cycle):
        """Runs the incremental backup in parallel with SFULL and does various verification after completion

            Args:
                inc_cycle       (str)       --      The cycle number of the INC job which ran in parallel

        """

        self.idx_tc.run_backup_sequence(
            self.subclient,
            ['edit', 'incremental'],
            verify_backup=True
        )

        self.verify_latest_cycle_browse()

        job = self.idx_tc.cv_ops.subclient_backup(
            self.subclient,
            backup_type='Synthetic_full',
            wait=False,
            advanced_options={
                'use_multi_stream': True,
                'use_maximum_streams': False,
                'max_number_of_streams': 50
            }
        )
        jm_obj = JobManager(job, self.commcell)
        time.sleep(5)

        if not job.is_finished:
            self.log.info('***** Suspending synthetic full job [%s] *****', job.job_id)
            job.pause(wait_for_job_to_pause=True)
        else:
            raise Exception('Synthetic full job completed ahead')

        self.log.info('***** Running INC jobs while SFULL is suspended *****')
        inc_jobs = self.idx_tc.run_backup_sequence(
            self.subclient,
            ['edit', 'incremental', 'edit', 'incremental'],
            verify_backup=True
        )

        self.log.info('***** Resuming synthetic full job [%s] *****', job.job_id)
        job.resume(wait_for_job_to_resume=True)

        jm_obj.wait_for_state('completed')
        self.log.info('Synthetic full job completed successfully')
        self.backupset.idx.record_job(job)

        self.idx_tc.verify_synthetic_full_job(job, self.subclient)

        self.log.info('***** Verifying latest cycle browse after finishing SFULL *****')
        self.verify_latest_cycle_browse()

        for inc_job in inc_jobs:
            self.verify_cycle_number(inc_job, inc_cycle)

        self.log.info('***** Verifying versions for a file in latest cycle *****')
        self.verify_versions_file()

    def verify_cycle_number(self, job, expected_cycle):
        """Verifies the cycle number for the job

            Args:
                job                 (obj)       --      The job object to check cycle number

                expected_cycle      (str)       --      The expected cycle number of the job

        """

        self.log.info('***** Verifying cycle no of INC job [%s]. Expected no [%s] *****', job.job_id, expected_cycle)

        self.csdb.execute(f"select fullCycleNum from jmbkpstats where jobid = '{job.job_id}'")
        resp = self.csdb.fetch_one_row()
        self.log.info(resp)

        if resp:
            actual_cycle = resp[0]
            if resp[0] == expected_cycle:
                self.log.info('Cycle number verified for INC job [%s]. Cycle [%s]', job.job_id, expected_cycle)
                return 0
            else:
                raise Exception(f'Mismatch in cycle number. Actual cycle number [{actual_cycle}]')
        else:
            raise Exception(f'Cannot fetch cycle number for the job [{job.job_id}]')

    def verify_latest_cycle_browse(self):
        """Verifies browse and restore from latest cycle"""

        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'show_deleted': True,
            'filters': [('FileName', '*.*')],
            'restore': {
                'do': True
            }
        })

    def verify_versions_file(self):
        """Verifies view all versions of a file"""

        versions_file = self.get_versions_file()

        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'versions',
            'path': versions_file,
            'restore': {
                'do': True,
                'source_items': [versions_file],
                'select_version': -1
            }
        })

    def get_versions_file(self):
        """Gets a random file to do view all versions"""

        query = ("select path from indexing where "
                 "type = 'file' and status in ('modified', 'new') and "
                 "name like 'edit_file%' order by jobid desc limit 1")

        response = self.backupset.idx.db.execute(query)

        if response.rowcount != 0:
            random_file = response.rows[0][0]
            self.log.info('Path of the picked up file with versions is [%s]', random_file)
            return random_file

        raise Exception('No file with versions exists')

    def check_job_starts(self, backup_level):
        """Checks if a new job starts

            Args:
                backup_level        (str)       --      The type of backup job to start

            Returns:
                (bool)      --      True if job starts. False otherwise

        """

        try:
            job = self.subclient.backup(backup_level=backup_level)
            self.log.info('[%s] job starts', backup_level)

            if hasattr(job, 'kill'):
                try:
                    self.log.info('Killing job [%s]', job.job_id)
                    job.kill(wait_for_job_to_kill=True)
                except Exception as e:
                    self.log.error('Failed to kill the job which started unexpectedly')
            return True

        except Exception as e:
            self.log.info('[%s] job did not start. [%s]', backup_level, e)
            return False
