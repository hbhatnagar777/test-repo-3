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
from VirtualServer.VSAUtils import VirtualServerUtils
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
        self.name = "Virtual Server - HyperV - Live sync - changing Memory and" \
                    " Number of CPU with Replication and validation "

        self.schedule_helper = None
        self.live_sync_options = None
        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.count = None
        self.memory = None

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
        self.count = int(self.tcinputs.get('Count'))
        self.memory = int(self.tcinputs.get('StartupMemory'))

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

            # To configure live sync
            schedule = self.vsa_subclient.configure_live_sync(self.live_sync_options)

            # To create a schedule helper object
            self.schedule_helper = SchedulerHelper(schedule, self.commcell)

            # To sleep for 30 seconds for the schedule to be triggered
            self.log.info('Sleeping for 30 seconds')
            time.sleep(30)

            # To get the latest replication job
            job = self.schedule_helper.get_jobid_from_taskid()

            if not job.wait_for_completion():
                raise Exception(
                    "Replication Job failed with error: " + job.delay_reason
                )
            self.log.info('Replication job: %s completed successfully', job.job_id)

            self.subclient.live_sync.refresh()
            live_sync_pair = self.subclient.live_sync.get(self.live_sync_options.schedule_name)
            vm_pairs = live_sync_pair.vm_pairs


            for vm_pair in vm_pairs:
                source_vm = self.vsa_instance.hvobj.VMs[vm_pair]

                # To set the processor count of VM
                output = source_vm.setprocessor(count=self.count)
                if output:
                    self.log.info('Successfully set the processor of VM : '
                                  '"%s" to "%s"', vm_pair, str(self.count))
                else:
                    raise Exception(f'Failed to set processor count of the VM {vm_pair} please check the logs')
                # To set the Startup memory of VM
                output = source_vm.setmemory(self.memory)
                if output:
                    self.log.info('Successfully set the Memory of VM :'
                                  ' "%s" to "%s"', vm_pair, str(self.memory))
                else:
                    raise Exception(f'Failed to set Memory of the VM {vm_pair} please check the logs')

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

            # To sleep for 30 seconds for the schedule to be triggered
            self.log.info('Sleeping for 30 seconds')
            time.sleep(30)

            # To get the latest replication job
            job = self.schedule_helper.get_jobid_from_taskid()

            if not job.wait_for_completion():
                raise Exception(
                    "Replication Job failed with error: " + job.delay_reason
                )

            self.log.info('Replication job: %s completed successfully', job.job_id)

            # To validate live sync
            self.vsa_subclient.validate_live_sync(self.live_sync_options.schedule_name,
                                                  schedule=schedule)

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
        self.vsa_subclient.cleanup_live_sync(self.live_sync_options.schedule_name)
