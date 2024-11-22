# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

     This Testcase verifies that single stream synthetic full backup job is successfully
     completed without any data loss after suspending and resuming the job multiple times.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    job_suspend_resume()                        --  Pause and resume a job with waiting time in between


"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.testcase import IndexingTestcase
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """
    This Testcase verifies that single stream synthetic full backup job is successfully
     completed without any data loss after suspending and resuming the job multiple times.

    Steps:
     1) Create backupset and subclient
     2) Have testdata with atleast 100K 1KB items.
     3) Run FULL -> INC -> INC -> INC
     4) Start single stream synthetic full.
     5) Suspend and resume synthetic full job all along the job multiple times in an interval
     6) Verify SFULL completes.

"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Suspend and resume'
        self.tcinputs = {
            'StoragePolicy': None,
            'TestDataPath': None,
            'LargeFilesPath': None,
            'BackupPhaseInterruptions': None,
            'ArchiveIndexPhaseInterruptions': None,
        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None

    def setup(self):
        """All testcase objects have been initialized in this method"""
        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset('sfull_sstream_suspend_resume', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='syn_w_interruptions',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )

    def run(self):
        """Contains the core testcase logic and it is the one executed"""
        try:

            error_threshold = self.tcinputs.get('AppSizeThreshold', 12.0)
            self.idx_tc.new_testdata(paths=self.subclient.content)
            self.log.info('************** Adding 100k files ***************')
            for path in self.subclient.content:
                self.log.info('Copying 100k files to %s', path)
                self.cl_machine.copy_folder(self.tcinputs['LargeFilesPath'], path)

            self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Full', 'Edit', 'Incremental', 'Edit', 'Incremental'],
                verify_backup=True
            )
            ss_syn_job = self.idx_tc.cv_ops.subclient_backup(
                self.subclient,
                backup_type="Synthetic_full",
                wait=False,
                advanced_options={
                    'use_multi_stream': False
                }
            )
            jm_obj = JobManager(ss_syn_job, self.commcell)
            jm_obj.wait_for_phase(phase='Synthetic Full Backup', total_attempts=120, check_frequency=1)
            self.log.info('Job is at backup phase, suspending job in [5] seconds')
            for _ in range(self.tcinputs['BackupPhaseInterruptions']):
                self.job_suspend_resume(ss_syn_job, 5)

            jm_obj.wait_for_phase(phase='Archive Index', total_attempts=120, check_frequency=10)
            self.log.info('Job is at archive index phase, suspending job in [5] seconds')

            for _ in range(self.tcinputs['ArchiveIndexPhaseInterruptions']):
                self.job_suspend_resume(ss_syn_job, 3)

            self.log.info('Job is resumed, waiting for it to complete')
            jm_obj.wait_for_state('completed')
            self.log.info('Job completed successfully')

            self.subclient.idx.record_job(ss_syn_job)
            self.idx_tc.verify_browse_restore(self.backupset, {
                    'operation': 'find',
                    'job_id': ss_syn_job.job_id,
                    'page_size': 1000,
                    'restore': {
                        'do': True
                    }
                })

            app_size = self.idx_tc.get_application_size(job_obj=ss_syn_job)
            size_on_disk = self.idx_tc.get_total_folder_size_disk(self.subclient.content)
            self.log.info('******** Verifying Application Size ********')
            if (abs(app_size - size_on_disk) / size_on_disk) * 100.0 > error_threshold:
                raise Exception('Application size and disk size do not match')
            else:
                self.log.info('Application size verified')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def job_suspend_resume(self, job, timer):
        """To pause and resume the job with waiting time in between"""
        time.sleep(timer)
        self.log.info('Suspending job')
        job.pause(wait_for_job_to_pause=True)

        self.log.info('Job is suspended, resuming it in [1] minutes')
        time.sleep(60)
        self.log.info('Resuming job')
        job.resume(wait_for_job_to_resume=True)
