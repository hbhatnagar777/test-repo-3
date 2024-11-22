# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase

from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = 'Indexing - VSA - Synthetic full job interruption'
        self.tcinputs = {}

        self.auto_subclient = None

    def run(self):
        """Run function of this test case

            Steps:

                1) Run INC backup twice
                2) Start Synthetic full backup and suspend and resume multiple times.
                3) Do restore and validate the restored VM

        """
        backup_options = None

        try:
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            self.auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info('********** Running INCREMENTAL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'
            self.auto_subclient.backup(backup_options)

            self.log.info('********** Running INCREMENTAL backup **********')
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_type = 'INCREMENTAL'
            self.auto_subclient.backup(backup_options)

            self.log.info('********** Running SYNTHETIC FULL backup **********')
            sfull_jobs = self.subclient.backup(backup_level='SYNTHETIC_FULL')
            self.log.info(f'Started synthetic full jobs [{sfull_jobs}]')

            sfull_job = sfull_jobs[0] if isinstance(sfull_jobs, list) else sfull_jobs  # Picking one SFULL job
            self.log.info(f'Trying to suspend and resume synthetic full job [{sfull_job.job_id}]')
            attempt = 0

            for attempt in range(1, 6):
                try:
                    self.log.info(f'Attempt [{attempt}/5]')
                    time.sleep(10)

                    if not sfull_job.is_finished:
                        self.log.info(f'Suspending the job [{sfull_job.job_id}]')
                        sfull_job.pause(wait_for_job_to_pause=True)
                    else:
                        self.log.info(f'Job already completed [{sfull_job.status}]')
                        break

                    time.sleep(10)

                    if not sfull_job.is_finished:
                        self.log.info(f'Resuming the job [{sfull_job.job_id}]')
                        sfull_job.resume(wait_for_job_to_resume=True)
                    else:
                        self.log.info(f'Job already completed [{sfull_job.status}]')
                        break

                except Exception as e:
                    self.log.error(f'Got exception while trying to suspend/resume job. May be job completed [{e}]')
                    break

            if attempt < 3:
                self.log.error('Job was not suspended/resumed enough times. Required atleast [2] times')

            self.log.info('Waiting for job to complete')
            if not sfull_job.wait_for_completion():
                raise Exception(f'Failed to run backup with error: [{sfull_job.delay_reason}]')

            self.log.info('********** Running RESTORE from SYNTHETIC FULL job **********')

            # Guest file restore is not supported right now from automation. Going with full VM restore
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True

            self.auto_subclient.virtual_machine_restore(vm_restore_options)

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if backup_options is not None:
                    self.auto_subclient.cleanup_testdata(backup_options)
            except Exception as e:
                self.log.error('Got exception while trying to do cleanup [%s]', e)
