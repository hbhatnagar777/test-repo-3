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
import random
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.Scheduler.schedulerhelper import SchedulerHelper
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils import VirtualServerUtils
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

        self.name = "Virtual Server - HyperV - Live sync - Delete Existing " \
                    "Change the memory and cpu count of source vm" \
                    "Replicated Vm Before INCR replication job"
        self.name = "Virtual Server - HyperV - Live sync - Delete Existing " \
                    "Replicated Vm Before INCR replication job"

        self.schedule_helper = None
        self.live_sync_options = None
        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.count = None
        self.memory = None
        self.live_sync_utils = None
        self.tcinputs = {
            'Count': None,
            'StartupMemory': None
        }

    def source_vm_object_creation(self):
        """To create basic VSA SDK objects"""
        self.vsa_commcell = AutoVSACommcell(self.commcell, self.csdb)
        self.vsa_client = AutoVSAVSClient(self.vsa_commcell, self.client)
        self.vsa_instance = AutoVSAVSInstance(self.vsa_client, self.agent, self.instance)
        self.vsa_backupset = AutoVSABackupset(self.vsa_instance, self.backupset)
        self.vsa_subclient = AutoVSASubclient(self.vsa_backupset, self.subclient)

        self.count = random.choice(self.tcinputs.get('Count'))
        self.memory = random.choice(self.tcinputs.get('StartupMemory'))

    def run(self):
        """Main function for test case execution"""
        try:
            # To create basic SDK objects for VSA
            self.source_vm_object_creation()

            # To run a basic Full backup before configuring
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            self.vsa_subclient.backup(backup_options, msg='FULL BACKUP')

            # To get live sync options
            self.live_sync_options = OptionsHelper.LiveSyncOptions(self.vsa_subclient, self)
            self.live_sync_options.unconditional_overwrite = True
            self.live_sync_options.network = self.tcinputs.get('network', "New")

            # To configure live sync
            schedule = self.vsa_subclient.configure_live_sync(self.live_sync_options)
            time.sleep(120)
            # To create a schedule helper object
            self.schedule_helper = SchedulerHelper(schedule, self.commcell)
            self.live_sync_utils = LiveSyncUtils(self.vsa_subclient, self.live_sync_options.schedule_name)
            self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                            int(self.vsa_subclient.backup_job.job_id),
                                                            monitor_job=True)

            self.subclient.live_sync.refresh()
            live_sync_pair = self.subclient.live_sync.get(self.live_sync_options.schedule_name)
            vm_pairs = live_sync_pair.vm_pairs
            vm_pair = live_sync_pair.get(next(iter(vm_pairs)))

            destination_client = self.commcell.clients.get(vm_pair.destination_client)

            dest_auto_client = AutoVSAVSClient(self.vsa_commcell, destination_client)

            agent = destination_client.agents.get('virtual server')
            instance = agent.instances.get(vm_pair.destination_instance)

            dest_auto_vsa_instance = AutoVSAVSInstance(dest_auto_client, agent, instance)

            for vm_pair in vm_pairs:
                dest_vm_name = live_sync_pair.get(vm_pair).destination_vm
                dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
                dest_vm = dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]

                output = dest_vm.delete_vm(dest_vm_name)
                if output:
                    self.log.info('Successfully deleted the replicated VM : "%s"', dest_vm_name)
                else:
                    raise Exception(f'Failed to delete the VM {dest_vm_name} please check the logs')

                # To wait for the VM to get deleted
                self.log.info('Sleeping for 30 seconds')
                time.sleep(30)

            # change the memory and no of processor
            for vm_pair in vm_pairs:
                source_vm = self.vsa_instance.hvobj.VMs[vm_pair]

                # To set the processor count of VM
                source_vm.set_no_of_cpu = self.count

                self.log.info('Successfully set the processor of VM : "%s" to "%s"'
                              , vm_pair, str(self.count))

                # To set the Startup memory of VM
                source_vm.set_memory = self.memory
                self.log.info('Successfully set the Memory of VM : "%s" to "%s"', vm_pair, str(self.memory))

                # To poweron the VM
                source_vm.power_on()
                self.log.info('Successfully powered on VM: "%s"', source_vm)
                # Wait for IP to be generated
                wait = 10

                while wait:
                    self.log.info('Waiting for 60 seconds for the IP to be generated')
                    time.sleep(60)
                    try:
                        source_vm.update_vm_info('All', os_info=True, force_update=True)
                    except Exception:
                        pass

                    if source_vm.ip and VirtualServerUtils.validate_ip(source_vm.ip):
                        break
                    wait -= 1
                else:
                    self.log.error('Valid IP not generated within 10 minutes')
                    raise Exception(f'Valid IP for VM: {vm_pair} not generated within 5 minutes')
                self.log.info('IP is generated')

            # To run a basic INCREMENTAL backup job
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.backup_type = "INCREMENTAL"
            self.vsa_subclient.backup(backup_options, msg='INCREMENTAL BACKUP')

            self.live_sync_utils.get_recent_replication_job(backup_jobid=
                                                            int(self.vsa_subclient.backup_job.job_id),
                                                            monitor_job=True)

            # To validate live sync
            self.live_sync_utils.validate_live_sync(schedule=schedule, check_replication_size=False)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.vsa_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")

    def tear_down(self):
        """Main function to perform cleanup operations"""
        self.live_sync_utils.cleanup_live_sync()
