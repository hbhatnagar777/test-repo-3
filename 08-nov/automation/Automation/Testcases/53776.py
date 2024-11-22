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
from AutomationUtils import constants
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Snap and backup-copy backup and
        Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA HyperV SYNTHETIC_FULL Snap Backup and Restore Cases with Linux MA"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "Browse_MA": None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.log.info("-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_type = "SYNTHETIC_FULL"
            backup_options.run_incremental_backup = "BEFORE_SYNTH"
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options)

            self.log.info("*" * 25 + " Restores from Snap " + "*" * 25)

            self.log.info("-" * 25 + " Files restores from Snap " + "-" * 25)
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
            file_restore_options.browse_from_snap = True
            if "Browse_MA" in self.tcinputs:
                file_restore_options.browse_ma = self.tcinputs["Browse_MA"]
            if "FBRMA" in self.tcinputs:
                file_restore_options.fbr_ma = self.tcinputs["FBRMA"]
            auto_subclient.guest_file_restore(file_restore_options)

            import time
            time.sleep(800)
            self.log.info("-" * 25 + " Disk restores from Snap " + "-" * 25)
            disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
            disk_restore_options.browse_from_snap = True
            auto_subclient.disk_restore(disk_restore_options)

            self.log.info("-" * 15 + " FULL VM out of Place restores from Snap " + "-" * 15)
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.power_on_after_restore = False
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = True
            auto_subclient.virtual_machine_restore(vm_restore_options)

            self.log.info("-" * 15 + " FULL VM in Place restores from Snap " + "-" * 15)
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.in_place_overwrite = True
            vm_restore_options.browse_from_snap = True
            vm_restore_options.power_on_after_restore = True
            auto_subclient.virtual_machine_restore(vm_restore_options)

            self.log.info("*" * 25 + " Restores from Backup Copy " + "*" * 25)

            self.log.info("-" * 25 + " Files restores from BackupCopy " + "-" * 25)
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
            file_restore_options.browse_from_snap = False
            file_restore_options.browse_from_backup_copy = True
            auto_subclient.guest_file_restore(file_restore_options)

            self.log.info("-" * 25 + " Disk restores from Backup copy " + "-" * 25)
            disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
            disk_restore_options.browse_from_backup_copy = True
            auto_subclient.disk_restore(disk_restore_options)

            self.log.info("-" * 15 + " FULL VM out of Place restores from Backup copy " + "-" * 15)
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_backup_copy = True
            vm_restore_options.power_on_after_restore = False
            auto_subclient.virtual_machine_restore(vm_restore_options)

            self.log.info("-" * 15 + " FULL VM in Place restores from Backup copy " + "-" * 15)
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.in_place_overwrite = True
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.browse_from_backup_copy = True
            auto_subclient.virtual_machine_restore(vm_restore_options)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
