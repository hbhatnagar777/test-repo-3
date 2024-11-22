# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Verify cleanup of index logs on index server MA

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initialized in this method

    modify_folder_timestamp()   --  Modifies the timestamp of the Index log file folders

    logs_not_cleanedup()        --  Checks for the presence of the index logs

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
    """Verify cleanup of index logs on Index server MA"""

    def __init__(self):
        """Initializes the TestCase class"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Clean up - Index logs on index server MA'
        self.tcinputs = {
            'StoragePolicy': None
            # Optional 'WaitAfterRestartServices': None,
        }
        self.backupset_name = None
        self.subclient_name = None
        self.cl_machine = None
        self.idx_tc = None
        self.idx_helper = None
        self.indexing_level = None
        self.idx_db = None
        self.ics_machine = None
        self.index_server_ma_index_cache = None
        self.jobs_list1 = []
        self.jobs_list2 = []
        self.job_details_list1 = []
        self.job_details_list2 = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.backupset_name = f'CLEANUP_LOGS_ON_INDEXSERVER_MA'
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

    def modify_folder_timestamp(self, job_details_list, num_of_days=0):
        """Modifies the timestamp of the Index log file folders in the given list on the given client
        Args:
            job_details_list     (list) --  list of tuples (job, it's v2 index log file folder)
            num_of_days          (int)  --  number of days to move timestamp

        Returns:
            Nothing

        Raises:
            Exception:
                if failed to modify timestamp of folders
        """
        try:
            new_datetime = datetime.now() - timedelta(days=num_of_days)
            self.log.info(f"***** Current time is {datetime.now()} and new time is {new_datetime} ******")

            for job, path in job_details_list:
                self.log.info(f'************ Changing time for log dir: {path} to {num_of_days} ago ************')
                self.ics_machine.modify_item_datetime(path, new_datetime, new_datetime, new_datetime)

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def logs_not_cleanedup(self, job_details_list):
        """Checks for the presence of the index logs
          Args:
              job_details_list     (list) --  list of tuples (job, it's v2 index log file folder)

          Returns:
              Nothing

          Raises:
              Exception:
                  if index logs are cleared
          """
        try:
            temp_flag = False
            for job, path in job_details_list:
                if self.ics_machine.check_directory_exists(path):
                    self.log.info(f"Index logs at path {path} are not cleaned..")
                else:
                    temp_flag = True
                    self.log.info(f"Index logs at path {path} are cleaned..")

            if temp_flag:
                raise Exception('Logs which should not be cleaned are cleaned and this is not expected.')

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Run backup jobs to create logs on index-server
            2 - Create checkpoint
            3 - Run few more backup jobs to create logs on Indexserver
            4 - Modify log-directories' date to 3 days ago
            5 - Restart all services on Index server ma
            6 - Verify if we are pruning logs (No logs should be pruned)
            7 - Modify log-directories' date to 7 days ago
            8 - Restart all services on Index server ma
            9 - Verify if we are pruning logs (logs before checkpoint should be pruned after 7 days)
        """

        try:
            self.log.info('************* Running backup jobs *************')
            self.jobs_list1 = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full'])
            self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)

            wait_for_service_restart = self.tcinputs.get('WaitAfterRestartServices', 180)
            self.index_server_ma_index_cache = self.idx_helper.get_index_cache(self.idx_db.index_server)
            self.ics_machine = Machine(self.idx_db.index_server)
            self.log.info("Index server is: {0}".format(self.idx_db.index_server))
            self.log.info("Index Cache is: {0}".format(self.index_server_ma_index_cache))

            self.log.info("Creating checkpoint...")
            if self.idx_db.checkpoint_db():
                self.log.info("Checkpoint created successfully...")
            else:
                raise Exception("Checkpoint has not been created...")

            self.log.info("Running few more backup jobs after checkpoint")
            self.jobs_list2 = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Edit', 'Incremental', 'Edit', 'Incremental', 'Synthetic_full'])

            for job in self.jobs_list1:
                path = self.idx_db.isc_machine.os_sep.join(
                    [self.index_server_ma_index_cache, 'CvIdxLogs', str(self.commcell.commcell_id),
                     self.idx_db.backupset_guid, f'J{job.job_id}'])
                self.job_details_list1.append((job, path))

            for job in self.jobs_list2:
                path = self.idx_db.isc_machine.os_sep.join(
                    [self.index_server_ma_index_cache, 'CvIdxLogs', str(self.commcell.commcell_id),
                     self.idx_db.backupset_guid, f'J{job.job_id}'])
                self.job_details_list2.append((job, path))

            self.log.info("Modifying timestamp for all the folders to 3 days ago")
            self.modify_folder_timestamp(self.job_details_list1, num_of_days=3)
            self.modify_folder_timestamp(self.job_details_list2, num_of_days=3)
            self.log.info("Restarting services on index server ma")
            self.idx_db.index_server.restart_services()
            self.log.info("Waiting for %s minutes after services restart", str(wait_for_service_restart))
            time.sleep(wait_for_service_restart)

            self.log.info("Verify if logs created before checkpoint are cleared after 3 days")
            self.logs_not_cleanedup(self.job_details_list1)
            self.log.info("SUCCESS, Logs created before checkpoint are not cleared after 3 days")

            self.log.info("Verify if logs created after checkpoint are cleared after 3 days")
            self.logs_not_cleanedup(self.job_details_list2)
            self.log.info("SUCCESS, Logs created after checkpoint are not cleared after 3 days")

            self.log.info("Modifying timestamp for all the folders to 7 days ago")
            self.modify_folder_timestamp(self.job_details_list1, num_of_days=7)
            self.modify_folder_timestamp(self.job_details_list2, num_of_days=7)
            self.log.info("Restarting services on index server ma")
            self.idx_db.index_server.restart_services()
            self.log.info("Waiting for %s minutes after services restart", str(wait_for_service_restart))
            time.sleep(wait_for_service_restart)

            self.log.info("Wait for logs created before checkpoint to be cleared after 7 days")
            tmp_flag = False
            for job, path in self.job_details_list1:
                if self.idx_db.isc_machine.check_directory_exists(path):
                    tmp_flag = True
                    self.log.info(f"Index logs at path {path} are not cleaned..")
                else:
                    self.log.info(f"Index logs at path {path} are cleaned..")

            if tmp_flag:
                raise Exception('Logs which should be cleaned are not cleaned and this is not expected.')

            self.log.info("SUCCESS, Logs before checkpoint on index server ma are cleared after 7 days")

            self.log.info("Verify if logs created after checkpoint are not cleared after 7 days")
            self.logs_not_cleanedup(self.job_details_list2)
            self.log.info("SUCCESS, Logs created after checkpoint are not cleared after 7 days on Index server MA")

        except Exception as exp:
            self.log.error("Failed to execute test case with error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)
