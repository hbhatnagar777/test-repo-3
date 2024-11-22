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

Sample Inputs:
"49357": {
      "ClientName": "SKVMWareClient",
      "AgentName": "Virtual Server",
      "InstanceName": "VMWare",
      "BackupsetName": "defaultbackupset",
      "SubclientName": "vmw-sdk-case-sub",
      "Datastore": "VM's",
      "Network": "VM Network",
      "Host": "172.16.64.105"
}
"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - VMW - Live sync -" \
                    " Change and validate VM RAM and No. of CPU"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.dest_auto_vsa_instance = None
        self.live_sync_options = None
        self.live_sync_utils = None

    def _get_memory_lst(self, auto_vsa_instance):
        """Memory list of VMs in auto_vsa_instance"""
        memory_lst = []
        try:
            for _vm in auto_vsa_instance.hvobj.VMs.values():
                memory_lst.append(_vm.memory)
            return memory_lst
        except Exception as exp:
            self.log.info("Failed to get memory information of all VMs")
            raise exp

    def _get_cpu_lst(self, auto_vsa_instance):
        """CPU number list of VMs in auto_vsa_instance"""
        cpu_lst = []
        try:
            for _vm in auto_vsa_instance.hvobj.VMs.values():
                cpu_lst.append(_vm.no_of_cpu)
            return cpu_lst
        except Exception as exp:
            self.log.info("Failed to get CPU information of all VMs")
            raise exp

    def _change_num_cpu(self, auto_vsa_instance, updated_cpu_lst):
        """"Change number of CPU"""
        try:
            for _vm, updated_cpu in zip(auto_vsa_instance.hvobj.VMs.values(), updated_cpu_lst):
                _vm.change_num_cpu(updated_cpu)
        except Exception as exp:
            self.log.info("Failed to update VM CPU cores")
            raise exp

    def _change_memory(self, auto_vsa_instance, updated_memory_lst):
        """"Change memory"""
        try:
            for _vm, updated_mem in zip(auto_vsa_instance.hvobj.VMs.values(), updated_memory_lst):
                _vm.change_memory(updated_mem)
        except Exception as exp:
            self.log.info("Failed to update VM Memory")
            raise exp

    def run(self):
        """Main function for test case execution"""
        auto_subclient = None
        backup_options = None

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            # Do a full backup
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)

            self.live_sync_options = OptionsHelper.LiveSyncOptions(auto_subclient, self)
            self.live_sync_options.unconditional_overwrite = True
            self.live_sync_options.schedule_name = "VMWLiveSyncName"

            # Configure New Live Sync with name : VMWLiveSyncName
            auto_subclient.configure_live_sync(self.live_sync_options)

            self.log.info(f"Configured Live Sync: {self.live_sync_options.schedule_name}")

            # Get destination vsa instance object
            dest_auto_vsa_instance = self.live_sync_options.dest_auto_vsa_instance

            self.log.info('Sleeping for 120 seconds')
            time.sleep(120)

            self.live_sync_utils = LiveSyncUtils(auto_subclient, self.live_sync_options.schedule_name)

            # Get latest replication job from schedule
            job = self.live_sync_utils.get_recent_replication_job()

            self.log.info(f"Replication Job: {job.job_id}")
            if not job.wait_for_completion():
                self.log.info(f"Replication job with job id: {job.job_id} failed")
                raise Exception("Replication Failed")

            # Get Source VMs Memory and CPU
            source_lst_memory = self._get_memory_lst(auto_subclient)
            source_lst_cpu = self._get_cpu_lst(auto_subclient)

            # Get Destination VMs Memory and CPU
            dest_lst_memory = self._get_memory_lst(dest_auto_vsa_instance)
            dest_lst_cpu = self._get_cpu_lst(dest_auto_vsa_instance)

            # Check source memory should be equal to destination memory
            assert source_lst_memory == dest_lst_memory, "Source and Destination Memory not equal after replication"

            # Check source num of cpu and destination num of cpu
            assert source_lst_cpu == dest_lst_cpu, "Source and Destination CPU not equal after replication"
            self.log.info("Source and destination CPU and memory configuration is same")

            # Power Off Source VMs to enable configuration change
            auto_subclient.hvobj.power_off_all_vms()

            # Change memory and cpu of source VMs, add to earlier
            updated_cpu_lst = [cpu + 2 for cpu in source_lst_cpu]
            updated_mem_lst = [mem + 1 for mem in source_lst_memory]
            self._change_memory(auto_subclient, updated_mem_lst)
            self._change_num_cpu(auto_subclient, updated_cpu_lst)

            self.log.info(f"Changed CPU and Memory")
            self.log.info("Powering source VMs back On")
            auto_subclient.hvobj.power_on_all_vms()

            time.sleep(240)

            # Do FULL backup
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)

            self.log.info('Sleeping for 120 seconds')
            time.sleep(120)

            # Get latest replication job from schedule
            job = self.live_sync_utils.get_recent_replication_job()

            if not job.wait_for_completion():
                self.log.info(f"Replication job with job id: {job.job_id} failed")
                raise Exception("Replication Failed")

            # Get Destination VMs Memory and CPU after replication
            dest_lst_memory_ar = self._get_memory_lst(dest_auto_vsa_instance)
            dest_lst_cpu_ar = self._get_cpu_lst(dest_auto_vsa_instance)

            assert dest_lst_memory_ar == updated_mem_lst, "Memory in Destination VMs," \
                                                          "is not equal to Source VMs"
            self.log.info("Memory validation successful")
            assert dest_lst_cpu_ar == updated_cpu_lst, "No. of CPU in Destination VMs," \
                                                       "is not equal to Source VMs"
            self.log.info("CPU validation successful")
            self.log.info("Changing back to original configuration")

            # Change back memory and cpu to original configuration
            self._change_memory(auto_subclient, source_lst_memory)
            self._change_num_cpu(auto_subclient, source_lst_cpu)

            self.log.info("Changed VM configurations back to original")

        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if auto_subclient and backup_options:
                    auto_subclient.cleanup_testdata(backup_options)
                if self.live_sync_options:
                    self.log.info("Attempting Live Sync Cleanup")
                    self.live_sync_utils.cleanup_live_sync()
                    self.log.info("Completed Live Sync Cleanup")

            except Exception as exp:
                self.log.warning(f"Testcase cleanup was not completed: {exp}")
