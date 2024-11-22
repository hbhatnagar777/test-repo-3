# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase does all in one regression coverage for basic indexing features.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    do_restore()                --  Starts the restore job and performs the action like kill, interrupt, continue

    run_restores()              --  Starts multiple restore jobs

    verify_restore()            --  Verifies the restore job after completion

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import idautils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase does all in one regression coverage for basic indexing features.

        Steps:
            1) Run Full, INC
            2) Verify job based find and restore
            3) Verify browse
            4) Verify versions of a file
            5) Run SFULL
            6) Verify job based find and restore
            7) Run aux copy
            8) Run index checkpoint
            9) Age FULL, INC jobs & run data aging
            10) Run index compaction
            11) Run INC job
            12) Delete index DB and logs
            13) Verify index checkpoint restore and index log restore and index playback
            14) Verify find with copy precedence 2
            15) Verify delete data operation
            16) Run and verify synthetic full job again

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Complete regression'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.indexing_level = None

        self.storage_policy = None
        self.primary_copy = None
        self.secondary_copy = None
        self.ma1 = None
        self.ma2 = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)
        self.ida_utils = idautils.CommonUtils(self.commcell)

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_complete_regression', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.prepare_storage_policy_info()

        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        self.csdb.execute("select value from GXGlobalParam where name = 'BackupIndexWithFull'")
        row = self.csdb.fetch_one_row()
        self.is_inline_checkpoint_enabled = str(row[0]) == '1'

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.new_testdata(paths=self.subclient.content)
        full_job = self.idx_tc.run_backup(self.subclient, 'FULL', verify_backup=True, restore=True)

        self.verify_inline_checkpoint(full_job)

        self.idx_tc.edit_testdata(self.subclient.content)
        inc1_job = self.idx_tc.run_backup(self.subclient, 'INCREMENTAL', verify_backup=True)

        self.idx_tc.log_section('Verifying BROWSE operation')
        self.idx_tc.verify_browse_restore(self.subclient, {
            'operation': 'browse',
            'path': '\\',
            'from_time': 0,
            'to_time': 0
        })

        self.idx_tc.log_section('Verifying VIEW ALL VERSIONS & RESTORE operation')
        versions_file = self.get_versions_file()
        self.log.info('View all versions file [%s]', versions_file)
        if not versions_file:
            raise Exception('Unable to pick a file for view all versions')

        self.idx_tc.verify_browse_restore(self.subclient, {
            'operation': 'versions',
            'path': versions_file,
            'from_time': 0,
            'to_time': 0,
            'restore': {
                'do': True,
                'source_items': [versions_file],
                'select_version': 'all'
            }
        })

        self.idx_tc.log_section('Verifying SYNTHETIC FULL job')
        sfull_job = self.idx_tc.run_backup(self.subclient, 'SYNTHETIC_FULL', verify_backup=True, restore=True)

        self.verify_inline_checkpoint(sfull_job)

        self.log.info('Running AUX COPY job')
        self.idx_tc.cv_ops.aux_copy(
            storage_policy=self.storage_policy.name,
            sp_copy=self.secondary_copy.copy_name,
            media_agent=self.ma1.name
        )
        self.backupset.idx.do_after_aux_copy(self.storage_policy.name, self.secondary_copy.copy_precedence)

        self.idx_tc.edit_testdata(self.subclient.content)
        inc2_job = self.idx_tc.run_backup(self.subclient, 'INCREMENTAL')

        self.idx_tc.log_section('Verifying MULTI-CYCLE FIND operation')
        self.idx_tc.verify_browse_restore(self.subclient, {
            'operation': 'find',
            'path': '\\**\\*',
            'show_deleted': True,
            'from_time': full_job.start_timestamp,
            'to_time': inc2_job.end_timestamp,
            'restore': {'do': True}
        })

        self.log.info('Getting index db object')
        self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)

        self.idx_tc.log_section('Verifying CHECKPOINT BACKUP, RESTORE & INDEX RECONSTRUCTION')

        self.log.info('Checkpointing the DB')
        if not self.idx_db.checkpoint_db(False):
            raise Exception('DB was not checkpointed')

        self.log.info('Verifying checkpoint restore')
        self.verify_checkpoint_restore()

        self.idx_tc.log_section('Verifying COMPACTION')

        self.log.info('Deleting backup jobs')
        to_be_aged = [inc1_job]

        for job in to_be_aged:
            job_id = job.job_id
            self.log.info('Aging backup job [%s]', job_id)
            self.storage_policy.delete_job(job_id)

            self.log.info('Marking job [%s] as aged in validation DB', job_id)
            self.backupset.idx.do_after_data_aging([job_id])

        self.log.info('Running data aging job')
        self.ida_utils.data_aging(self.storage_policy)

        time.sleep(30)

        self.log.info('Running compaction')
        if not self.idx_db.compact_db():
            raise Exception('Compaction did not happen for the DB')

        self.log.info('Verifying compaction by browsing aged job')
        self.idx_tc.verify_browse_restore(self.subclient, {
            'operation': 'find',
            'path': '\\**\\*',
            'from_time': full_job.start_timestamp,
            'to_time': sfull_job.start_timestamp,
            'restore': {'do': True}
        })

        self.idx_tc.log_section('Verifying browse & restore from SECONDARY COPY')
        self.idx_tc.verify_browse_restore(self.subclient, {
            'operation': 'find',
            'path': '\\**\\*',
            'from_time': full_job.start_timestamp,
            'to_time': inc2_job.end_timestamp,
            'copy_precedence': self.secondary_copy.copy_precedence,
            'restore': {'do': True}
        })

        self.idx_tc.log_section('Verifying DELETE DATA')
        self.verify_delete_data()

        self.idx_tc.log_section('Verifying SYNTHETIC FULL job')
        self.idx_tc.run_backup(self.subclient, 'SYNTHETIC_FULL', verify_backup=True)

        self.log.info('Testcase PASSED successfully')

    def verify_checkpoint_restore(self):
        """Verifies checkpoint restore operation"""

        old_creation_id = self.idx_db.get_db_info_prop('creationId')
        self.log.info('Creation ID [%s] - Before', old_creation_id)

        self.log.info('Deleting the DB [%s]', self.idx_db.db_path)
        self.idx_db.delete_db()

        self.idx_db.idx_cli.do_tools_shutdown_index_server()
        time.sleep(30)

        if self.idx_db.db_exists:
            raise Exception('Index DB exists even before doing checkpoint restore')

        self.log.info('Triggering index checkpoint restore')
        if not self.idx_db.is_upto_date:
            self.log.error('Index is not yet up to date')

        self.log.info('Index is up to date')
        time.sleep(30)

        new_creation_id = self.idx_db.get_db_info_prop('creationId')
        self.log.info('Creation ID [%s] - After checkpoint restore', new_creation_id)

        if old_creation_id != new_creation_id:
            raise Exception('Index checkpoint was not restored')

        self.log.info('Checkpoint restore is verified')

    def verify_inline_checkpoint(self, job_obj):
        """Verifies if inline index backup happened for the DB"""

        self.idx_tc.log_section('Verifying inline checkpoint for job [%s]', job_obj.job_id)

        if self.indexing_level != 'subclient' or not self.is_inline_checkpoint_enabled:
            self.log.warning('Inline checkpoint is not enabled (or) client is at backupset level index')
            return

        query = (f"SELECT * FROM archFile WHERE appid = '{self.subclient.subclient_id}' "
                 f"AND isValid = 1 AND jobId = '{job_obj.job_id}' "
                 f"AND name like '%IdxCheckPoint%'")

        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(row)

        if not row[0]:
            raise Exception(f'Inline checkpoint did not happen for the job [{job_obj.job_id}]')

        self.log.info('Inline checkpoint verified for the job')

    def verify_delete_data(self):
        """Verifies the delete data operation"""

        erase_file = self.cl_machine.os_sep.join([
            self.subclient.content[0], 'erase_file.txt'
        ])

        self.cl_machine.create_file(erase_file, '1')

        self.idx_tc.run_backup(self.subclient, 'INCREMENTAL', verify_backup=True)

        self.log.info('Doing delete data operation for file [%s]', erase_file)
        self.backupset.delete_data([erase_file])

        self.log.info('Marking items deleted in validation DB')
        self.backupset.idx.do_delete_items([erase_file])

        self.log.info('Verifying delete data result')
        self.idx_tc.verify_browse_restore(self.backupset, {
            'operation': 'find',
            'path': "/**/*",
            'show_deleted': True,
            'restore': {'do': True}
        })

    def prepare_storage_policy_info(self):
        """Uses storage policy properties to find primary and secondary MAs and their copy precedence"""

        sp_name = self.tcinputs.get('StoragePolicy')
        self.storage_policy = self.commcell.storage_policies.get(sp_name)

        self.primary_copy = self.storage_policy.get_primary_copy()
        ma1_name = self.primary_copy.media_agent

        secondary_copies = self.storage_policy.get_secondary_copies()
        if not secondary_copies:
            raise Exception('There are no secondary copies in this storage policy')

        self.secondary_copy = secondary_copies[0]  # Pick the first secondary copy MA for this testcase
        ma2_name = self.secondary_copy.media_agent

        self.ma1 = self.commcell.clients.get(ma1_name)
        self.ma2 = self.commcell.clients.get(ma2_name)

        self.log.info('=> Primary copy MA [%s] - Precedence [%s]', ma1_name, self.primary_copy.copy_precedence)
        self.log.info('=> Secondary copy MA [%s] - Precedence [%s]', ma2_name, self.secondary_copy.copy_precedence)

    def get_versions_file(self, subclient=None, from_time=0, to_time=0):
        """Gets a random file to do view all versions"""

        if to_time == 0:
            to_time = int(time.time())

        query = ("select path from indexing where jobendtime between '{0}' and '{1}' {2} and "
                 "type = 'file' and status in ('modified', 'new') and name like '%.txt' "
                 "order by jobid desc limit 1")

        sc_query = " and subclient = '{0}'".format(subclient) if subclient is not None else ''
        query = query.format(from_time, to_time, sc_query)

        response = self.backupset.idx.db.execute(query)

        random_file = ''
        if response.rowcount != 0:
            random_file = response.rows[0][0]

        return random_file
