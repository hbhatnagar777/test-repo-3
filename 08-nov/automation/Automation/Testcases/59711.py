# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that during the scale backup job running index checkpoint and compaction operations does not
affect the number of items added to the index and the playback process.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    validates_items_in_index()  --  Validates if the number of items in the index is as expected

    validate_restore()          --  Validates the number of items restored

    compact_using_cli()         --  Runs compaction on the DB using IdxCLI

"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.commonutils import get_int

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db
from Indexing.tools import idxcli


class TestCase(CVTestCase):
    """This testcase verifies that during the scale backup job running index checkpoint and compaction operations
    does not affect the number of items added to the index and the playback process.

        Steps:
            1) Start FULL backup for huge dataset (50 million items)
            2) Wait for some items to be added to the index.
            3) Forcefully run index checkpoint operation for the DB.
            4) Forcefully run compaction operation for the DB.
            5) Repeat steps 3 & 4 multiple times.
            6) Wait for the job to complete.
            7) Verify if the items in the index is correct as expected.
            8) Perform restore for a folder and validate the number of items restored.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Scale test - Parallel checkpoint and compaction'

        self.tcinputs = {
            'TestData': None,
            'RestoreLocation': None,
            'StoragePolicy': None,
            'TotalInterrupts': None,
            'TotalItems': None,
            'ToRestoreFolder': None,
            'InterruptInterval': None
            # Optional - JobQueryFrequency - default=60 secs
            # Optional - JobTimeLimit - default=300 mins
            # Optional - ThresholdItems - default=100
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.testdata = None
        self.restore_location = None
        self.idx_db = None
        self.idx_cli = None

        self.full_job = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)
        self.testdata = self.tcinputs.get('Testdata')

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        if self._subclient is None:
            self.log.info('***** Creating backupset and subclient since not given as input ****')
            self.backupset = self.idx_tc.create_backupset('scale_test_maintenance', for_validation=False)

            self.subclient = self.idx_tc.create_subclient(
                name='sc1_scale_maintenance',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy')
            )

            self.log.info('***** Running DUMMY FULL backup to set IndexServer *****')
            dummy_job = self.subclient.backup('Full')
            self.log.info('Dummy FULL job [%s] started', dummy_job.job_id)
            self.log.info('Waiting for job to complete')
            dummy_job.wait_for_completion()
            self.log.info('Dummy job [%s] completed successfully')

            self.subclient.trueup_option = True
            self.subclient.scan_type = 2

        self.log.info('***** Setting huge dataset as testdata *****')
        self.testdata = self.tcinputs.get('TestData')
        self.subclient.content = self.testdata.split(';')

        self.log.info('***** Getting IndexServer for the backupset *****')
        self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
        self.log.info(f'IndexServer MA is [{self.idx_db.index_server.client_name}]')

        self.idx_cli = idxcli.IdxCLI(self.idx_db.index_server)

    def run(self):
        """Contains the core testcase logic"""
        try:

            job_query_freq = get_int(self.tcinputs.get('JobQueryFrequency', 60), 60)  # Seconds
            job_time_limit = get_int(self.tcinputs.get('JobTimeLimit', 300), 300)  # Minutes

            self.log.info('***** Starting FULL backup *****')
            self.full_job = self.subclient.backup('Full')

            jm_obj = JobManager(self.full_job)
            jm_obj.wait_for_phase('backup', check_frequency=job_query_freq)
            self.log.info('***** Job is at backup phase now *****')

            total_interrupts = get_int(self.tcinputs.get('TotalInterrupts'), 4)
            interrupt_interval = get_int(self.tcinputs.get('InterruptInterval'), 120)

            for attempt in range(total_interrupts):

                self.log.info(f'***** Attempt [{attempt+1}/{total_interrupts}] *****')
                self.log.info(f'Job status [{self.full_job.status}]. Waiting for [{interrupt_interval}] seconds.')
                time.sleep(interrupt_interval)

                if 'waiting' in self.full_job.status.lower():
                    self.full_job.resume(wait_for_job_to_resume=True)
                    self.log.info('Job is resumed')
                    time.sleep(30)

                if self.full_job.is_finished:
                    self.log.error('Job already completed ahead (before interruption)')
                    break

                try:
                    self.log.info('Doing browse in-between')
                    results = self.subclient.browse()
                    self.log.info(f'Browse result {results}')
                except Exception as e:
                    self.log.error('Got exception while doing browse, ignoring.')
                    self.log.exception(e)

                self.idx_db.checkpoint_db(by_all_index_backup_clients=False)

                self.compact_using_cli()

            jm_obj.wait_for_state('completed', retry_interval=job_query_freq, time_limit=job_time_limit)

            if self.idx_db.is_upto_date:
                self.log.info('Index is upto date')

            self.log.info('***** Verifying the number of items in index *****')
            self.validate_items_in_index()

            self.log.info('***** Verifying restore of data *****')
            self.validate_restore()

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

        finally:
            if self.full_job and not self.full_job.is_finished:
                self.log.error('Killing job as testcase raised exception')
                self.full_job.kill(wait_for_job_to_kill=True)

    def validate_items_in_index(self):
        """Validates if the number of items in the index is as expected

            Returns:
                None

            Raises:
                  Exception, if the number of items in index is over the allowed_diff

        """

        items_in_index = self.idx_help.get_items_in_index(self.subclient)
        total_items = get_int(self.tcinputs.get('TotalItems'))
        threshold_items = get_int(self.tcinputs.get('ThresholdItems', 100))
        difference = abs(items_in_index - total_items)

        self.log.info(
            'Items in index [%s] Expected items [%s] Difference [%s]',
            items_in_index, total_items, difference
        )

        if difference > threshold_items:
            raise Exception(
                f'Some items are missing in the index. In Index [{items_in_index}]. Expected [{total_items}]. '
                f'Difference [{difference}]'
            )
        else:
            self.log.info('Expected number of items are present in the index')

    def validate_restore(self):
        """Validates the number of items restored

            Returns:
                None

            Raises:
                Exception, if the number of items of restored is not equal to the items in the ToRestore folder

        """

        restore_location = self.tcinputs.get('RestoreLocation')
        to_restore = self.tcinputs.get('ToRestoreFolder')

        self.log.info(f'Deleting the previous restore directory [{restore_location}]')
        self.cl_machine.remove_directory(restore_location)

        self.idx_tc.cv_ops.subclient_restore_out_of_place(
            destination_path=restore_location,
            paths=[to_restore],
            client=self.client,
            subclient=self.subclient
        )

        expected_restore = self.cl_machine.number_of_items_in_folder(
            to_restore, recursive=True, include_only='files')
        actual_restore = self.cl_machine.number_of_items_in_folder(
            restore_location, recursive=True, include_only='files')
        self.log.info(f'Restore stats. Expected: [{expected_restore}] Actual: [{actual_restore}]')

        if abs(expected_restore - actual_restore) > 1:
            raise Exception('Number of items restored is not equal to the expected')
        else:
            self.log.info('Restore is verified')

    def compact_using_cli(self):
        """Runs compaction on the DB using IdxCLI"""

        self.log.info(f'***** Compacting DB using idxCLI [{self.idx_db.db_path}] *****')

        try:
            if self.idx_cli.do_db_compaction(self.idx_db.db_path):
                self.log.info('Compaction is successful for the DB')
            else:
                self.log.error('Compaction failed/did not happen for the DB')
        except Exception as e:
            self.log.exception(e)
