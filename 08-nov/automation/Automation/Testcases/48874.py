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
"48874": {
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
    """Class for executing VSA Backup and Replication Validation Testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - VMW - Live sync - INCR VM backup," \
                    " after backup replication and validation"
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
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)

            self.live_sync_options = OptionsHelper.LiveSyncOptions(auto_subclient, self)
            self.live_sync_options.unconditional_overwrite = True
            self.live_sync_options.schedule_name = "VMWLiveSyncName"

            auto_subclient.configure_live_sync(self.live_sync_options)

            self.log.info('Sleeping for 120 seconds')
            time.sleep(120)

            self.live_sync_utils = LiveSyncUtils(auto_subclient, self.live_sync_options.schedule_name)

            # Get latest replication job from schedule
            job = self.live_sync_utils.get_recent_replication_job()

            self.log.info(f"Replication Job: {job.job_id}")
            if not job.wait_for_completion():
                self.log.info(f"Replication job with job id: {job.job_id} failed")
                raise Exception("Replication Failed")

            try:
                self.live_sync_utils.validate_live_sync(check_replication_size=False)
            except Exception as exp:
                self.log.error(exp)
                raise Exception("Failed to complete live sync validation.")

        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.status = constants.FAILED
            raise exp

        finally:
            try:
                if auto_subclient and backup_options:
                    auto_subclient.cleanup_testdata(backup_options)
                if self.live_sync_options:
                    self.log.info("Attempting Live Sync Cleanup")
                    self.live_sync_utils.cleanup_live_sync()
                    self.log.info("Completed Live Sync Cleanup")
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
