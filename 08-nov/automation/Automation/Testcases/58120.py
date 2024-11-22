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

    validate_nic_details()      -- To validate if network configuration

"""

import time

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
        self.name = "Virtual Server - Azure - Live sync - Basic INC backup," \
                    " after backup replication and validation"

        self.schedule_helper = None

        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
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

    def validate_nic_details(self, nic_details_incrbkp, nic_details_fullbkp):
        """
            does network interface validation

            Agrs :
                nic_details_incrbkp  (list): list of network interface
                                             after incremental backup

                nic_details_fullbkp  (list) : list of network interface
                                               before incremental backup
        """
        try:
            for nic_fullbkp, nic_incrbkp in zip(nic_details_fullbkp, nic_details_incrbkp):
                if nic_fullbkp['name'] != nic_incrbkp['name']:
                    return False
                if nic_fullbkp['allocation'] != nic_incrbkp['allocation']:
                    return False
            return True
        except Exception as exp:
            self.log.error('Error in network interface  validation :%s', exp)
            raise Exception(exp)

    def run(self):
        """Main function for test case execution"""
        try:
            # To create basic SDK objects for VSA
            self.source_vm_object_creation()
            self.subclient.live_sync.refresh()
            live_sync_pair = self.subclient.live_sync.get(self.schedule_name)
            vm_pairs = live_sync_pair.vm_pairs
            vm_pair = live_sync_pair.get(next(iter(vm_pairs)))

            destination_client = self.commcell.clients.get(vm_pair.destination_client)

            dest_auto_client = AutoVSAVSClient(self.vsa_commcell, destination_client)

            agent = destination_client.agents.get('virtual server')
            instance = agent.instances.get(vm_pair.destination_instance)

            dest_auto_vsa_instance = AutoVSAVSInstance(dest_auto_client, agent, instance)
            dest_vm_state = {}

            for vm_pair in vm_pairs:
                dest_vm_name = live_sync_pair.get(vm_pair).destination_vm
                dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
                dest_vm = dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]
                dest_vm.get_nic_info()
                dest_vm.get_nic_details()
                dest_vm_state[vm_pair] = dest_vm.nic_details
                dest_vm.power_off()

            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.backup_type = "INCREMENTAL"
            self.vsa_subclient.backup(backup_options, msg='INCREMENTAL BACKUP')
            self.live_sync_utils = LiveSyncUtils(self.vsa_subclient, self.schedule_name)
            # To get the latest replication job
            self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                            int(self.vsa_subclient.backup_job.job_id),
                                                            monitor_job=True)
            self.live_sync_utils.validate_live_sync(schedule=self.schedule_helper.schedule_object)

            for vm_pair in vm_pairs:
                dest_vm_name = live_sync_pair.get(vm_pair).destination_vm
                dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
                dest_vm = dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]
                dest_vm.get_nic_info()
                dest_vm.get_nic_details()
                prev_nic_details = dest_vm_state[vm_pair]
                dest_vm.power_off()
                check_nics = self.validate_nic_details(dest_vm.nic_details, prev_nic_details)
                if not check_nics:
                    self.log.error('NIC validation failed for vm pair "%s"', vm_pair)
                    raise Exception("Live sync network interface validation failed")
            self.log.info('Network interface validation for incremental job successful')

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


