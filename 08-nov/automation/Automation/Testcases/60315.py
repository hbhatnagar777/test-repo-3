# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies multi stream synthetic full's has issues when one of it's stream is interrupted during
the backup job.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    switch_data_path()          --  Switches the default datapath and adds it to the list

    interrupt_stream()          --  Restarts the service of the MA

    interrupt_streams()         --  Interrupt the MA while the job is running

"""

import time
import threading
import random

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies multi stream synthetic full's has issues when one of it's stream is interrupted
    during the backup job.

        Steps:
            1) Create backupset and subclient
            2) Assign a storage policy which has multiple datapaths.
            3) Run FULL -> INC -> INC -> INC
            4) Make sure every INC backup is adding 100k 1KB items atleast.
            5) Before every backup, switch the default datapath of the primary copy and ensure every job goes into
            different consecutive MA.
            6) Start multistream synthetic full job.
            7) While job is in backup phase, restart one of the service of MA to interrupt that stream.
            8) Repeat #7 multiple times for different MAs.
            9) Allow SFULL job to complete.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Stream interruption'

        self.tcinputs = {
            'TestDataPath': None,
            'RestoreLocation': None,
            'CopyData': None,
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.storage_policy = None
        self.primary_copy = None
        self.mas_used = []

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.primary_copy = self.storage_policy.get_primary_copy()

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_stream_interrupt', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.run_backup_sequence(self.subclient, ['new', 'copy', 'full'], verify_backup=True)

        self.switch_data_path()
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.switch_data_path()
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.switch_data_path()
        self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

        self.switch_data_path()
        job = self.idx_tc.cv_ops.subclient_backup(
            self.subclient,
            backup_type='Synthetic_full',
            wait=False,
            advanced_options={
                'use_multi_stream': True,
                'use_maximum_streams': False,
                'max_number_of_streams': 10
            }
        )
        jm_obj = JobManager(job, self.commcell)

        self.log.info('Trying to interrupt job at Backup phase')
        jm_obj.wait_for_phase(phase='Synthetic Full Backup', total_attempts=120, check_frequency=1)

        self.log.info('Interrupting streams while job is running')
        self.interrupt_streams()

        try:
            if not job.is_finished:
                self.log.info('Resuming the job')
                job.resume(wait_for_job_to_resume=True)
        except Exception as e:
            self.log.error('Unable to resume the job [%s]', e)

        jm_obj.wait_for_state('completed')
        self.log.info('Job completed successfully')

        self.backupset.idx.record_job(job)

        self.idx_tc.verify_synthetic_full_job(job, self.subclient)

    def switch_data_path(self):
        """Switches the default datapath and adds it to the used MA list"""

        new_ma = self.idx_tc.rotate_default_data_path(self.primary_copy)
        if new_ma not in self.mas_used:
            self.mas_used.append(new_ma)

    def interrupt_stream(self, ma_name):
        """Restarts the service of the MA

            Args:
                ma_name         (str)       --      The name of the MA to restart services

        """

        ma_obj = self.commcell.clients.get(ma_name)

        for attempt in range(2):
            rand_int = random.randint(5, 20)
            self.log.info('Restarting MA services [%s] in [%s] seconds. Attempt [%s/2]', ma_name, rand_int, attempt+1)
            time.sleep(rand_int)
            ma_obj.restart_services()
            time.sleep(5)
            self.log.info('Successfully restarted services')

    def interrupt_streams(self):
        """Interrupt the MA while the job is running"""

        self.log.info('MAs used in the latest cycle %s', self.mas_used)
        time.sleep(10)

        threads = []

        for ma_name in self.mas_used:
            exe_thread = threading.Thread(
                target=self.interrupt_stream,
                args=(ma_name,)
            )
            exe_thread.start()
            threads.append(exe_thread)

        for exe_thread in threads:
            exe_thread.join()
