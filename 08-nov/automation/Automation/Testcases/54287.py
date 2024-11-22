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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

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
        self.name = "HyperV live sync configuration and monitoring"

        self.schedule_helper = None
        self.live_sync_options = None

        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.live_sync_utils = None

        self.tcinputs = {
            'AuxCopyName': None
        }

    def source_vm_object_creation(self):
        """To create basic VSA SDK objects"""
        self.vsa_commcell = AutoVSACommcell(self.commcell, self.csdb)
        self.vsa_client = AutoVSAVSClient(self.vsa_commcell, self.client)
        self.vsa_instance = AutoVSAVSInstance(self.vsa_client, self.agent, self.instance)
        self.vsa_backupset = AutoVSABackupset(self.vsa_instance, self.backupset)
        self.vsa_subclient = AutoVSASubclient(self.vsa_backupset, self.subclient)
        self.aux_copy_name = self.tcinputs.get('AuxCopyName')

    def run(self):
        """Main function for test case execution"""
        try:
            # To create basic SDK objects for VSA
            self.source_vm_object_creation()

            # To run a aux copy job
            storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
            job = storage_policy.run_aux_copy(self.aux_copy_name)

            if not job.wait_for_completion():
                raise Exception(
                    "Aux copy Job failed with error: " + job.delay_reason
                )
            self.log.info('Aux copy job: %s completed successfully', job.job_id)

            # To run a basic Full backup before configuring
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            self.vsa_subclient.backup(backup_options, msg='FULL BACKUP')

            # To run another aux copy job
            job = storage_policy.run_aux_copy(self.aux_copy_name)

            if not job.wait_for_completion():
                raise Exception(
                    "Aux copy Job failed with error: " + job.delay_reason
                )
            self.log.info('Aux copy job: %s completed successfully', job.job_id)

            copy_precedence = storage_policy.get_copy(self.aux_copy_name).get_copy_Precedence()

            # To get live sync options
            self.live_sync_options = OptionsHelper.LiveSyncOptions(self.vsa_subclient, self)

            self.live_sync_options.copy_precedence = copy_precedence
            self.live_sync_options.unconditional_overwrite = True

            # To configure live sync
            schedule = self.vsa_subclient.configure_live_sync(self.live_sync_options)

            # To create a schedule helper object
            self.schedule_helper = SchedulerHelper(schedule, self.commcell)

            self.live_sync_utils = LiveSyncUtils(self.vsa_subclient, self.live_sync_options.schedule_name)
            self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                            int(self.vsa_subclient.backup_job.job_id),
                                                            monitor_job=True)
            # To validate live sync
            self.live_sync_utils.validate_live_sync(schedule=schedule)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.vsa_subclient.cleanup_testdata(backup_options)
            except Exception as err:
                self.log.warning("Testcase cleanup was not completed %s", err)

    def tear_down(self):
        """Main function to perform cleanup operations"""
        self.live_sync_utils.cleanup_live_sync()
