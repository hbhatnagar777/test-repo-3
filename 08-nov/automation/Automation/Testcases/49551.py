# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This test verifies acceptance testcase for the V1-V2 upgrade feature

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    run_backup()                --  Runs backup with start new media option set and records the media used by the job

    get_job_indexing_version()  --  Gets the indexing version of the job based on the afile name

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This test verifies acceptance testcase for the V1-V2 upgrade feature

        Steps:
            1) Convert the client to V1 mode
            2) Run FULL, INC, SFULL, INC, INC
            3) Convert the client to V2 mode
            4) Run INC to trigger V1-V2 migration
            5) Check index logs in index cache and confirm SFULL, INC, INC jobs are migrated to V2
            6) Delete the index DB and logs
            7) Start FULL index reconstruction
            8) Verify migrated index logs again
            9) Start a synthetic full job

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - V1 to V2 upgrade'

        self.tcinputs = {
            'StoragePolicy': None,
            'WaitTime': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None
        self.wait_time = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.wait_time = self.tcinputs.get('WaitTime', 1800)

        current_version = self.idx_help.get_agent_indexing_version(self.client)
        self.log.info('Current indexing version of the client [%s] is [%s]', self.client.client_name, current_version)

        if current_version != 'v1':
            self.log.info('***** Converting the client to V1 mode *****')
            self.idx_help.set_agent_indexing_version('v1', self.client)
            self.log.info('Moved client to V1')
            self.log.info('Waiting for [%s] minutes before running new backup jobs', int(self.wait_time/60))
            time.sleep(self.wait_time)
        else:
            self.log.info('***** Client is already in V1 mode *****')

        self.backupset = self.idx_tc.create_backupset('v1_v2_upgrade', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_upgrade',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('Running backup jobs in V1 mode')
        jobs = self.idx_tc.run_backup_sequence(self.subclient, ['new', 'full'], verify_backup=False)

        self.log.info('Checking if the first FULL job ran in V1 mode')
        full_job_id = jobs[-1].job_id

        job_version = self.get_job_indexing_version(full_job_id)
        if job_version == 'v1':
            self.log.info('Job ran in V1 mode as expected. Continuing with other jobs')
        else:
            raise Exception('Full job did not run in indexing V1 mode')

        jobs.extend(self.idx_tc.run_backup_sequence(
            self.subclient,
            ['edit', 'incremental', 'synthetic_full', 'edit', 'incremental', 'edit', 'incremental'],
            verify_backup=False
        ))

        latest_cycle_jobs = jobs[-3:]
        latest_cycle_job_ids = [job.job_id for job in latest_cycle_jobs]
        self.log.info('Latest cycle jobs before conversion %s', latest_cycle_job_ids)

        self.log.info('***** Converting the client to V2 mode *****')
        self.idx_help.set_agent_indexing_version('v2', self.client)
        self.log.info('Moved client to V2')
        self.log.info('Waiting for [%s] minutes before running backup new jobs', int(self.wait_time / 60))
        time.sleep(self.wait_time)

        v2_inc_job = self.idx_tc.run_backup_sequence(
            self.subclient,
            ['edit', 'incremental'],
            verify_backup=True
        )

        latest_cycle_job_ids.append(v2_inc_job[0].job_id)
        self.log.info(' => Latest cycle jobs are %s', latest_cycle_job_ids)

        job_version = self.get_job_indexing_version(v2_inc_job[0].job_id)
        if job_version == 'v2':
            self.log.info('Job ran in V2 mode as expected. Continuing with testcase')
        else:
            raise Exception('Job did not run in indexing V2 mode')

        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        self.idx_db = index_db.get(self.subclient if indexing_level == 'subclient' else self.backupset)
        migrated_job_ids = self.idx_db.get_logs_in_cache(job_id_only=True)
        self.log.info(' => Migrated jobs are %s', migrated_job_ids)

        if set(migrated_job_ids) != set(latest_cycle_job_ids):
            raise Exception(f'Incorrect jobs migrated. Actual {migrated_job_ids} Expected {latest_cycle_job_ids}')

        self.log.info('***** Verifying browse & restore from the latest cycle *****')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'show_deleted': True,
            'restore': {
                'do': True
            }
        })

        self.log.info('***** Deleting DB and logs to verify if migration happens correctly during full recon *****')
        self.idx_db.rename_logs()
        self.idx_db.delete_db()

        self.log.info('***** Restarting IndexServer [%s] services *****', self.idx_db.index_server.client_name)
        self.idx_db.index_server.restart_services()
        time.sleep(120)

        if self.idx_db.is_upto_date:
            self.log.info('Index is up to date after deleting the index DB and logs')
        else:
            migrated_jobs = self.idx_db.get_logs_in_cache(job_id_only=True)
            self.log.info('Migrated jobs %s', migrated_jobs)
            raise Exception('Index is not up to date after deleting the index DB and logs')

        self.log.info('***** Running synthetic full job *****')
        v2_sfull_job = self.idx_tc.run_backup(self.subclient, 'synthetic_full', restore=True)

        latest_cycle_job_ids.append(v2_sfull_job.job_id)
        self.log.info(' => Latest cycle jobs are %s', latest_cycle_job_ids)

        migrated_job_ids = self.idx_db.get_logs_in_cache(job_id_only=True)
        self.log.info(' => Migrated jobs are %s', migrated_job_ids)

        if set(migrated_job_ids) != set(latest_cycle_job_ids):
            raise Exception(
                f'Incorrect jobs migrated during full reconstruction. '
                f'Actual {migrated_job_ids} Expected {latest_cycle_job_ids}'
            )

        self.log.info('Testcase completed successfully')

    def get_job_indexing_version(self, job_id):
        """Gets the indexing version of the job based on the afile name"""

        self.csdb.execute(f"""select name from archfile where jobid='{job_id}' and fileType=2""")
        row = self.csdb.fetch_one_row()
        self.log.info(row)
        index_afile_name = row[0]

        if index_afile_name == 'Not named':
            return 'v1'

        if index_afile_name == 'IdxLogs_V1':
            return 'v2'

        return ''
