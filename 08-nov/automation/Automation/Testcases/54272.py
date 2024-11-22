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
import time
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
        self.name = ("Virtual Server - HyperV - Live sync - INCR backup, "
                     "Suspend and Resume INCR replication job and validation")

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

            # To run a basic Incremental backup
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.advance_options = {'testdata_size': 200000}

            backup_options.backup_type = "INCREMENTAL"
            self.vsa_subclient.backup(backup_options, msg='INCREMENTAL BACKUP')
            self.live_sync_utils = LiveSyncUtils(self.vsa_subclient, self.schedule_name)
            job = self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                                  int(self.vsa_subclient.backup_job.job_id))

            for i in range(2):
                self.log.info("Suspending Replication JOB")
                job.pause(wait_for_job_to_pause=True)
                wait = 4
                while wait != 0 and job.status != 'Suspended' and job.status != 'Completed':
                    time.sleep(60)
                    wait = wait - 1
                if 'completed' in job.status.lower():
                    break
                if job.status == 'Suspended':
                    self.log.info("Replication JOB Suspended ")
                time.sleep(60)
                job.resume(wait_for_job_to_resume=True)
                time.sleep(60)
                self.log.info("Replication JOB Resumed ")

            self.live_sync_utils.monitor_job_for_completion(job)
            self.live_sync_utils.validate_live_sync(schedule=self.schedule_helper.schedule_object,
                                                    check_replication_size=False)

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
