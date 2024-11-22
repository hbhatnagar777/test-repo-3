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
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMWare Full Snap backup and SAN Restore test case
    Windows proxy, Windows MA, Windows backup vm without metadata collection"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Full Snap Backup and Full VM Restore using SAN mode"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options)

            VirtualServerUtils.decorative_log("Restore from Snap")

            try:
                VirtualServerUtils.decorative_log("Out of place full VM SAN restore")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                try:
                    VirtualServerUtils.decorative_log("Adding registry key to enable this feature")
                    reg_key = self.tcinputs.get("reg_key")
                    auto_subclient.add_registry_key(reg_key, vm_restore_options.proxy_client)
                except Exception as exp:
                    self.log.error("Failed with error: %s", str(exp))
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
                VirtualServerUtils.decorative_log("Removing registry key")
                reg_key = self.tcinputs.get("reg_key")
                auto_subclient.delete_registry_key(reg_key, vm_restore_options.proxy_client)
            except Exception as exp:
                self.log.error("Failed with error: %s", str(exp))
            try:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
