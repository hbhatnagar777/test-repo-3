# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Verify cleanup of index logs on non index server MA

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initialized in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

import time

from datetime import datetime
from datetime import timedelta

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """Verify cleanup of index logs on non index server MA"""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Clean up - Index logs on non index server MA'

        self.tcinputs = {
            'StoragePolicy': None,
            'NonIndexServerMediaAgent': None,
        }

        self.backupset_name = None
        self.subclient_name = None

        self.cl_machine = None
        self.idx_tc = None
        self.idx_helper = None
        self.indexing_level = None
        self.idx_db = None

        self.non_index_server_ma_client = None
        self.non_index_server_ma_machine = None

        self.non_index_server_ma_index_cache = None

        self.jobs = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.backupset_name = f'CLEANUP_LOGS'
        self.subclient_name = f'SUBCLIENT_1'

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.idx_helper = IndexingHelpers(self.commcell)

        self.indexing_level = self.idx_helper.get_agent_indexing_level(self.agent)

        self.backupset = self.idx_tc.create_backupset(name=self.backupset_name, for_validation=False)
        self.subclient = self.idx_tc.create_subclient(
            name=self.subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy']
        )

        self.non_index_server_ma_client = self.commcell.clients.get(self.tcinputs['NonIndexServerMediaAgent'])
        self.non_index_server_ma_machine = Machine(self.non_index_server_ma_client)

        self.non_index_server_ma_index_cache = self.idx_helper.get_index_cache(self.non_index_server_ma_client)

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Run backup jobs to create logs on index-server
            2 - Clean cached index-db on non-index server ma
            3 - Restart all services on non-index server ma
            4 - Run browse on backup jobs with non-index server ma
            5 - Check if logs were created on non-index server ma
            6 - Modify log-directories' date to 3 days ago, (non-index server logs are retained for 3 days)
            7 - Restart all services on non-index server ma
            8 - Wait for logs to be cleared

        """

        try:
            self.log.info('************* Running backup jobs *************')
            self.jobs = self.idx_tc.run_backup_sequence(subclient_obj=self.subclient,
                                                        steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full'])

            self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
            if self.idx_db.index_server.name == self.non_index_server_ma_client.name:
                raise Exception(
                    f'Index Server MA and Non-Index Server MA cannot be same. {self.non_index_server_ma_client.name}')

            non_index_server_ma_index_db = self.non_index_server_ma_machine.os_sep.join(
                [self.non_index_server_ma_index_cache, 'CvIdxDB', self.idx_db.backupset_guid, self.idx_db.db_guid])

            job_details = []
            for job in self.jobs:
                path = self.non_index_server_ma_machine.os_sep.join(
                    [self.non_index_server_ma_index_cache, 'CvIdxLogs', str(self.commcell.commcell_id),
                     self.idx_db.backupset_guid, f'J{job.job_id}'])
                job_details.append((job, path))

            self.log.info(f'Removing index db at: {non_index_server_ma_index_db}')
            self.non_index_server_ma_machine.remove_directory(non_index_server_ma_index_db)

            for job, path in job_details:
                self.log.info(f'Removing job logs for job-id {job.job_id} at: {path}')
                self.non_index_server_ma_machine.remove_directory(path)

            self.log.info('Restarting services on non-index server ma')
            self.non_index_server_ma_client.restart_services(implicit_wait=30)

            for job, path in job_details:
                self.log.info(
                    f'Running browse with non-index server ma to copy '
                    f'logs to non-index server ma. Job: {job.job_id}')
                self.subclient.browse(
                    {'job_id': int(job.job_id), 'media_agent': self.tcinputs['NonIndexServerMediaAgent']})

            is_logs_copied = all(
                self.non_index_server_ma_machine.check_directory_exists(path) for job, path in job_details)
            if not is_logs_copied:
                raise Exception('Logs not created on non-index server ma')

            for job, path in job_details:
                self.log.info(f'************ Changing time for job log dir: {path} ************')
                new_datetime = datetime.now() - timedelta(days=3)
                self.non_index_server_ma_machine.modify_item_datetime(path, new_datetime, new_datetime, new_datetime)

            self.log.info('Restarting services on non-index server ma')
            self.non_index_server_ma_client.restart_services()

            self.log.info('****************** Wait for logs to be cleared. ******************')
            total_attempts = 3
            for attempt_number in range(1, total_attempts + 1):
                self.log.info(f'Waiting 120 seconds before attempt {attempt_number}/{total_attempts}')
                time.sleep(120)
                not_all_logs_deleted = any(
                    self.non_index_server_ma_machine.check_directory_exists(path) for job, path in job_details)
                if not_all_logs_deleted:
                    if attempt_number == total_attempts:
                        raise Exception('Logs on non-index server ma not cleared.')
                else:
                    break

            self.log.info('******* SUCCESS, logs were successfully deleted from Non-Index Server Media Agent. *******')

        except Exception as e:
            self.log.error('Failed to execute test case with error: %s', e)
            self.result_string = str(e)
            self.status = constants.FAILED
            self.log.exception(e)
