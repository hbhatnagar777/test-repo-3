# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that multi stream synthetic full backup with huge dataset completes successfully without issues
when it is interrupted (suspended/resumed) multiple times.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    validates_items_in_index()  --  Validates if the number of items in the index is as expected

    validate_restore()          --  Validates the number of items restored

    tear_down()                 --  Tear down function of the testcase

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


class TestCase(CVTestCase):
    """This testcase verifies that multi stream synthetic full backup with huge dataset completes successfully without
    issues when it is interrupted (suspended/resumed) multiple times.

        Steps:
            1) Run FULL backup for huge dataset (50 million items)
            2) Run INC backup
            3) Start multi stream synthetic full backup.
            4) Suspend and resume the job multiple times
            5) Do restore and validate the restored items count.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Scale test - Multistream synthetic full'

        self.tcinputs = {
            'TestData': None,
            'StoragePolicy': None,
            'RestoreLocation': None,
            'TotalInterrupts': None,
            'TotalItems': None,
            'ToRestoreFolder': None,
            'InterruptInterval': None,
            # Optional - JobQueryFrequency - default=60 secs
            # Optional - JobTimeLimit - default=300 mins
            # Optional - ThresholdItems - default=100
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.restore_location = None
        self.idx_db = None

        self.sfull_job = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        self.testdata = self.tcinputs.get('TestData').split(';')

        if self._subclient is None:
            self.log.info('***** Creating backupset and subclient since not given as input ****')
            self.backupset = self.idx_tc.create_backupset('scale_test_msfull', for_validation=False)

            self.subclient = self.idx_tc.create_subclient(
                name='sc1_scale',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy'),
                content=self.testdata
            )
            self.subclient.trueup_option = True
            self.subclient.scan_type = 2

            self.run_full_job()

        else:
            self.log.info('***** Subclient is already given as input, continuing to use that ****')
            try:
                last_job = self.idx_tc.get_last_job(self.subclient)
                self.log.info('Subclient has backup jobs. Last job [%s]. Continuing to run INC job', last_job.job_id)
            except Exception as e:
                self.log.error('Subclient does not have any backup job [%s]', e)
                self.log.info('***** Setting huge dataset as testdata *****')
                self.subclient.content = self.testdata
                self.run_full_job()

        self.log.info('***** Getting IndexServer for the backupset *****')
        self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
        self.log.info(f'IndexServer MA is [{self.idx_db.index_server.client_name}]')

    def run(self):
        """Contains the core testcase logic"""
        try:

            job_query_freq = get_int(self.tcinputs.get('JobQueryFrequency', 60), 60)  # Seconds
            job_time_limit = get_int(self.tcinputs.get('JobTimeLimit', 300), 300)  # Minutes

            self.log.info('***** Creating testdata to run INC job *****')
            self.idx_tc.create_only_files(self.subclient.content, count=2)
            self.idx_tc.run_backup(self.subclient, backup_level='incremental', verify_backup=False,
                                   retry_interval=job_query_freq, time_limit=job_time_limit)

            self.log.info('***** Starting Multi-stream synthetic FULL backup *****')
            self.sfull_job = self.subclient.backup(backup_level='synthetic_full', advanced_options={
                'use_multi_stream': True,
                'use_maximum_streams': False,
                'max_number_of_streams': 50
            })

            jm_obj = JobManager(self.sfull_job)
            jm_obj.wait_for_phase('Synthetic Full Backup', check_frequency=job_query_freq)
            self.log.info('***** Job is at backup phase now *****')

            total_interrupts = get_int(self.tcinputs.get('TotalInterrupts'), 4)
            interrupt_interval = get_int(self.tcinputs.get('InterruptInterval'), 120)

            for attempt in range(total_interrupts):

                self.log.info(f'***** Attempt [{attempt+1}/{total_interrupts}] *****')
                self.log.info(f'Job status [{self.sfull_job.status}]. Waiting for [{interrupt_interval}] seconds.')
                time.sleep(interrupt_interval)

                if 'waiting' in self.sfull_job.status.lower():
                    self.sfull_job.resume(wait_for_job_to_resume=True)
                    self.log.info('Job is resumed')
                    time.sleep(30)

                if self.sfull_job.is_finished:
                    self.log.error('Job already completed ahead (before interruption)')
                    break

                self.log.info('Suspending the job')
                self.sfull_job.pause(wait_for_job_to_pause=True)
                time.sleep(30)

                self.log.info('Resuming the job')
                self.sfull_job.resume(wait_for_job_to_resume=True)

            jm_obj.wait_for_state('completed', retry_interval=job_query_freq, time_limit=job_time_limit)

            if self.idx_db.is_upto_date:
                self.log.info('Index is up to date')

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
            if self.sfull_job and not self.sfull_job.is_finished:
                self.log.error('Killing job as testcase raised exception')
                self.sfull_job.kill(wait_for_job_to_kill=True)

    def run_full_job(self):
        """Run FULL job and wait for it to complete"""

        job_time_limit = get_int(self.tcinputs.get('JobTimeLimit', 300), 300)  # Minutes

        self.log.info('***** Running scale FULL backup *****')
        full_job = self.subclient.backup('Full')
        jm_obj = JobManager(full_job)
        jm_obj.wait_for_state('completed', retry_interval=300, time_limit=job_time_limit)  # Retry every 5 min

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

    def tear_down(self):
        """Tear down function of the testcase"""

        if self.status == constants.FAILED:
            new_name = self.backupset.backupset_name + '_' + str(int(time.time()))
            self.log.info('Testcase failed, renaming backupset for later analysis. New name [%s]', new_name)
            self.backupset.backupset_name = new_name
