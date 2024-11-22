# --------------------------------------------------------------------------
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

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA AzureStack backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azurestack Full Snap Backup and Restore Cases"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:

            log.info("Started executing %s testcase" % self.id)
            log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            try:
                log.info(
                    "-" * 25 + " Backup " + "-" * 25)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_method = "SNAP"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            log.info("*" * 25 + " Restores from Snap " + "*" * 25)
            try:
                log.info(
                    "-" * 25 + " Files restores from Snap " + "-" * 25)
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.browse_from_snap = True
                auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info(
                    "-" * 15 + " FULL VM out of Place restores from Snap " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info(
                    "-" * 15 + " FULL VM in Place restores from Snap " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.in_place_overwrite = True
                vm_restore_options.browse_from_snap = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)


            log.info("*" * 25 + " Restores from Backup Copy " + "*" * 25)

            try:
                log.info(
                    "-" * 25 + " Files restores from BackupCopy " + "-" * 25)
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                auto_subclient.guest_file_restore(file_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)


            try:
                log.info(
                    "-" * 15 + " FULL VM out of Place restores from Backup copy " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.in_place_overwrite = False
                vm_restore_options.browse_from_backup_copy = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)


            try:
                log.info(
                    "-" * 15 + " FULL VM in Place restores from Backup copy " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.in_place_overwrite = True
                vm_restore_options.browse_from_backup_copy = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
                