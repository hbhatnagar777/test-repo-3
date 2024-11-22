# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This test case verifies pruning of index DBs restored from old checkpoints

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initialized in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import time
import xmltodict

from datetime import datetime
from datetime import timedelta

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This test case verifies pruning of index DBs restored from old checkpoints"""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Pruning - Clean up of Index DBs restored from old checkpoints'

        self.tcinputs = {
            'StoragePolicy': None,
        }

        self.backupset_name = None
        self.subclient_name = None

        self.cl_machine = None
        self.idx_tc = None
        self.idx_helper = None
        self.indexing_level = None
        self.idx_db = None

        self.jobs = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.backupset_name = f'PRUNING_CLEANUP_RESTORED_CHECKPOINTS'
        self.subclient_name = f'SUBCLIENT_1'

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.idx_helper = IndexingHelpers(self.commcell)

        self.indexing_level = self.idx_helper.get_agent_indexing_level(self.agent)
        if self.indexing_level != 'subclient':
            raise Exception(f'TestCase valid only for subclient level index.')

        self.backupset = self.idx_tc.create_backupset(name=self.backupset_name, for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name=self.subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )

        # Modify index retention criteria
        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 2

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1 - Run backup jobs
                2 - Prune Db
                3 - Browse a pruned job
                4 - Verify if checkpoint was restored
                5 - Modify restored db's date to 7 days ago
                6 - Restart services on index-server
                7 - Verify if restore db was cleared

        """

        try:
            self.log.info('*********** Running backup jobs and pruning***********')
            self.jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'edit', 'Incremental', 'Synthetic_full', 'edit', 'Incremental', 'Synthetic_full'])
            )
            self.idx_db = index_db.get(self.subclient)
            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            self.jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['edit', 'Incremental', 'Synthetic_full'])
            )

            if not self.idx_db.prune_db():
                raise Exception('Index pruning failed.')

            pruned_job = self.jobs[0]

            self.log.info(f'Doing browse and restore on job: {pruned_job.job_id}')
            self.subclient.browse({'job_id': int(pruned_job.job_id)})

            self.log.info(f'Get checkpoint for job: {pruned_job.job_id}')
            checkpoint = self.idx_helper.get_checkpoint_by_job(index_db=self.idx_db, job=pruned_job)
            if checkpoint is None:
                raise Exception(f'No checkpoint found for job: {pruned_job.job_id}.')

            idx_db_name = f"{checkpoint['dbName']}_{checkpoint['commCellId']}" \
                          f"_{checkpoint['startTime']}_{checkpoint['endTime']}"
            idx_db_path = self.idx_db.isc_machine.os_sep.join([self.idx_db.backupset_path, idx_db_name])

            if not self.idx_db.isc_machine.check_directory_exists(idx_db_path):
                raise Exception('Checkpoint was not restored.')

            self.log.info(f'Db restored at {idx_db_path}')
            self.log.info('Change access time for restored db.')
            idx_db_info_path = self.idx_db.isc_machine.os_sep.join([idx_db_path, '.dbInfo'])
            self.log.info(f'Reading dbInfo file {idx_db_info_path}')

            if self.idx_db.isc_machine.check_file_exists(idx_db_info_path):
                contents = self.idx_db.isc_machine.read_file(idx_db_info_path)
                db_dict = xmltodict.parse(contents)
            else:
                raise Exception(f'Db info file {idx_db_info_path} does not exist')

            if 'Indexing_DbProps' not in db_dict and not isinstance(db_dict['Indexing_DbProps'], dict):
                raise Exception('Failed to access Indexing_DbProps inside dbinfo file')
            old_timestamp = db_dict.get('Indexing_DbProps', {}).get('@lastAccessTime')
            if not old_timestamp:
                raise Exception('Failed to get access time of the DB, dbinfo is missing lastaccesstime attribute')
            new_timestamp = (datetime.fromtimestamp(int(old_timestamp)) - timedelta(days=7)).timestamp()
            db_dict['Indexing_DbProps']['@lastAccessTime'] = int(new_timestamp)
            dbinfo_xml = xmltodict.unparse(db_dict)
            self.log.info(f'Saving dbInfo file with content {dbinfo_xml}')
            self.idx_db.isc_machine.create_file(idx_db_info_path, dbinfo_xml)

            self.log.info('********** Restarting services on index-server. **********')
            self.idx_db.index_server.restart_services()

            self.log.info('************* Wait for restored db to be cleared. *************')
            total_attempts = 3
            for attempt_number in range(1, total_attempts + 1):
                self.log.info(f'Waiting 120 seconds before attempt {attempt_number}/{total_attempts}')
                time.sleep(120)
                if self.idx_db.isc_machine.check_directory_exists(idx_db_path):
                    if attempt_number == total_attempts:
                        raise Exception('Restored db from checkpoint not cleared.')
                else:
                    break

            self.log.info('**************** SUCCESS, restored dbs were cleared as expected. ****************')

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.result_string = str(e)
            self.status = constants.FAILED
            self.log.exception(e)
