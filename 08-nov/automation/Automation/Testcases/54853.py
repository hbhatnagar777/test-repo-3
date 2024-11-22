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

import time
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils, OptionsHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Test of RDM snap backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE RDM Full Snap Backup and Restore Cases: RDM-YES,Independent-YES"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            auto_subclient.validate_all_disks_present()
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True,
                    'backup_copy_type': 'USING_LATEST_CYLE'}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options, rdm=True)
            rdm_type = 3

            try:
                VirtualServerUtils.decorative_log("Validating RDM disks from snap")
                disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
                disk_restore_options.browse_from_snap = True
                auto_subclient.validate_rdm_disks(disk_restore_options.copy_precedence, rdm_type)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Validating RDM disks from Backup Copy")
                disk_restore_options.browse_from_backup_copy = True
                auto_subclient.validate_rdm_disks(disk_restore_options.copy_precedence, rdm_type)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            VirtualServerUtils.decorative_log("Restores from Snap")
            try:
                VirtualServerUtils.decorative_log("Files restores from Snap")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                if "browse_ma" in self.tcinputs:
                    file_restore_options.browse_ma = self.tcinputs["browse_ma"]
                file_restore_options.browse_from_snap = True
                auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from Snap")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            VirtualServerUtils.decorative_log("Restores from Backup Copy")
            try:
                VirtualServerUtils.decorative_log("Files restores from BackupCopy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from Backup copy")
                vm_restore_options.in_place_overwrite = False
                vm_restore_options.browse_from_backup_copy = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options, status=self.test_individual_status)
            except NameError:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
