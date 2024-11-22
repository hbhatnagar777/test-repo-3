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
"49053": {
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

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils


class TestCase(CVTestCase):
    """Class for executing VSA Full Backup and Full Replication when replication job is killed"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - VMW - Live sync - FULL VM backup," \
                    " and Replication Validation when replication job is killed"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.live_sync_options = None
        self.live_sync_utils = None

    def run(self):
        """Main function for test case execution"""

        auto_subclient = None
        backup_options = None
        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)

            self.log.info('Sleeping for 30 seconds')
            time.sleep(30)

            self.live_sync_options = OptionsHelper.LiveSyncOptions(auto_subclient, self)
            self.live_sync_options.unconditional_overwrite = True
            self.live_sync_options.schedule_name = "VMWLiveSyncName"

            # Configure New Live Sync with name : VMWLiveSyncName
            auto_subclient.configure_live_sync(self.live_sync_options)

            source_vms = [vm_name for vm_name in auto_subclient.hvobj.VMs]

            self.log.info('Sleeping for 120 seconds')
            time.sleep(120)

            self.live_sync_utils = LiveSyncUtils(auto_subclient, self.live_sync_options.schedule_name)

            # Get latest replication job from schedule
            job = self.live_sync_utils.get_recent_replication_job()

            # Kill Replication Job
            self.log.info(f"Replication Job: {job.job_id}")
            try:
                job.kill(wait_for_job_to_kill=True)
                self.log.info(f"Killed Replication Job with Job ID: {job.job_id}")
            except Exception as exp:
                self.log.info(exp)
                raise Exception("Failed to kill replication Job")

            dest_auto_vsa_instance = self.live_sync_options.dest_auto_vsa_instance

            # Destination VM names are obtained by adding prefix to source_vms, destination vms can only be obtained
            # from the hypervisor after successful completion of first replication job
            destination_vms = ["LiveSync_" + vm_name for vm_name in source_vms]

            # Sleep to allow update status of deleted VM
            self.log.info("Sleeping for 60s")
            time.sleep(60)
            # Check if destination VMs with given name don't exist
            assert dest_auto_vsa_instance.hvobj.check_vms_absence(destination_vms), "Destination VMs/VM Exist" \
                                                                                    ", Validation Failed"

            # Check if source VM exists
            assert auto_subclient.hvobj.check_vms_exist(source_vms), "Source VMs Deleted, Validation Failed"
            self.log.info("Validation Complete")

        finally:
            try:
                if auto_subclient and backup_options:
                    auto_subclient.cleanup_testdata(backup_options)
                if self.live_sync_options:
                    self.log.info("Attempting Live Sync Cleanup")
                    # No destination VM exists, hence only cleaning up schedule
                    auto_subclient.subclient._client_object.schedules.delete(self.live_sync_options.schedule_name)
                    self.log.info("Completed Live Sync Cleanup")
            except Exception as exp:
                self.log.warning("Testcase cleanup was not completed")
                self.log.warning(exp)
