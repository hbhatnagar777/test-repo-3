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
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerConstants import AZURE_AUTO_VM_CONFIG
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA AzureRM backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA AzureRM Full Backup and Restore Cases Using Unix MA and Win Proxy"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            AZURE_AUTO_VM_CONFIG['disk_encryption']['validate'] = True
            AZURE_AUTO_VM_CONFIG['disk_encryption']['all_disk'] = False
            auto_subclient.validate_inputs(update_qa=True, vm_check=True, validation=AZURE_AUTO_VM_CONFIG)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)
            auto_subclient.post_backup_validation(validate_workload=False, skip_snapshot_validation=False)

            try:
                VirtualServerUtils.decorative_log("File Level restores")
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.metadata_collected = backup_options.collect_metadata
                VirtualServerUtils.set_inputs(self.tcinputs, fs_restore_options)
                auto_subclient.guest_file_restore(fs_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if auto_subclient and backup_options:
                    auto_subclient.cleanup_testdata(backup_options)
                    auto_subclient.post_restore_clean_up(vm_restore_options, status=self.test_individual_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
