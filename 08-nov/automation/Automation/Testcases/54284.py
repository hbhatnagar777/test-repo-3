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
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils
from VirtualServer.VSAUtils import OptionsHelper
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
        self.name = "Virtual Server - HyperV - Live sync - INCR backup," \
                    " KILL a INCR replication job and validation"

        self.schedule_helper = None

        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.schedule_name = None
        self.live_sync_utils = None

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

            # To run a basic Full backup
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.backup_type = "INCREMENTAL"
            self.vsa_subclient.backup(backup_options, msg='INCREMENTAL BACKUP')
            self.live_sync_utils = LiveSyncUtils(self.vsa_subclient, self.schedule_name)
            job = self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                                  int(self.vsa_subclient.backup_job.job_id))

            # To kill the replication job
            job.kill(wait_for_job_to_kill=True)

            if job.status.lower() == 'killed':
                self.log.info('Replication job is killed successfully')
            else:
                raise Exception('Replication job is not killed')

            # To validate status after killing the job
            live_sync_pair = self.subclient.live_sync.get(self.schedule_name)
            job_status = job.details['jobDetail']['clientStatusInfo']['vmStatus']
            for vm_pair in live_sync_pair.vm_pairs:
                vm_pair_obj = live_sync_pair.get(vm_pair)
                sync_status = 1
                for _vm in job_status:
                    if _vm['vmName'] != vm_pair_obj.source_vm:
                        continue
                    sync_status = int(_vm['syncStatus'])

                    if sync_status != 1:
                        # To validate sync status
                        assert vm_pair_obj.status == 'NEEDS_SYNC', \
                            f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation failed"'
                self.log.info('Sync status validation successful for vm pair: "%s"', vm_pair)
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.live_sync_utils.cleanup_live_sync(power_off_only=True)
                self.vsa_subclient.cleanup_testdata(backup_options)
            except Exception as err:
                self.log.warning("Testcase cleanup was not completed %s", err)

