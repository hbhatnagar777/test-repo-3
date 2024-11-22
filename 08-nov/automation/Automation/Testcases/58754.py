# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    source_vm_object_creation() --  To create basic VSA SDK objects

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.Scheduler.schedulerhelper import SchedulerHelper
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils
from VirtualServer.VSAUtils.VirtualServerHelper import (
    AutoVSACommcell,
    AutoVSAVSClient,
    AutoVSAVSInstance,
    AutoVSABackupset,
    AutoVSASubclient
)


class TestCase(CVTestCase):
    """Class for configuring and monitoring Live Sync of VSA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Virtual Server - AzureRM - Live sync - Basic Before Synthetic full backup,"
                     " after backup replication and validation")

        self.schedule_helper = None

        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.live_sync_utils = None
        self.schedule_name = None

        self.tcinputs = {
            'ScheduleName': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # To create a schedule helper object
        self.schedule_name = self.tcinputs.get('ScheduleName')
        schedule = self.client.schedules.get(self.schedule_name)
        self.schedule_helper = SchedulerHelper(schedule, self.commcell)

    def source_vm_object_creation(self):
        """To create basic VSA SDK objects"""
        self.vsa_commcell = AutoVSACommcell(self.commcell, self.csdb)
        self.vsa_client = AutoVSAVSClient(self.vsa_commcell, self.client)
        self.vsa_instance = AutoVSAVSInstance(self.vsa_client, self.agent, self.instance)
        self.vsa_backupset = AutoVSABackupset(self.vsa_instance, self.backupset)
        self.vsa_subclient = AutoVSASubclient(self.vsa_backupset, self.subclient)

    def run(self):
        """Main function for test case execution"""
        try:
            # To create basic SDK objects for VSA
            self.source_vm_object_creation()

            # To run a basic Synthetic Full backup before configuring
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.backup_type = "SYNTHETIC_FULL"
            backup_options.run_incremental_backup = "BEFORE_SYNTH"
            backup_options.run_incr_before_synth = False
            backup_job = self.subclient.backup(backup_options.backup_type,
                                               backup_options.run_incr_before_synth,
                                               backup_options.incr_level,
                                               backup_options.collect_metadata,
                                               backup_options.advance_options)

            if not backup_job.wait_for_completion():
                raise Exception(
                    "Synthetic backup Job failed with error: " + backup_job.delay_reason
                )
            self.log.info('Synthetic job: %s completed successfully', backup_job.job_id)
            live_sync_pair = self.subclient.live_sync.get(self.schedule_name)
            time.sleep(90)
            for vm_pair in live_sync_pair.vm_pairs:
                vm_pair_obj = live_sync_pair.get(vm_pair)
                assert str(vm_pair_obj.last_synced_backup_job) != str(backup_job.job_id), \
                    f"Replication Job started for Synthetic full, failing case"
                self.log.info('Replication run not started for Synthetic, validation successful')
                # To validate sync status
                assert vm_pair_obj.status == 'IN_SYNC', \
                    f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation success"'
                self.log.info('Sync status validation successful for vm pair: "%s"', vm_pair)

            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.backup_type = "INCREMENTAL"
            self.vsa_subclient.backup(backup_options, msg='INCREMENTAL BACKUP')
            self.live_sync_utils = LiveSyncUtils(self.vsa_subclient, self.schedule_name)
            # To get the latest replication job
            self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                            int(self.vsa_subclient.backup_job.job_id),
                                                            monitor_job=True)
            self.live_sync_utils.validate_live_sync(schedule=self.schedule_helper.schedule_object)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.live_sync_utils.cleanup_live_sync(power_off_only=True)
                self.vsa_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")