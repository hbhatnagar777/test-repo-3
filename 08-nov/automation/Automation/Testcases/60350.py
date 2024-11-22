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
from VirtualServer.VSAUtils import VirtualServerUtils, OptionsHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Custom Attributes for VMware"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMWARE - Backup and Restore of Custom Attributes"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""

        try:
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            backup_vm_custom_attributes = dict()
            for vm in auto_subclient.vm_list:
                self.log.info(f"Fetching Custom Attributes for {vm}")
                backup_vm_custom_attributes[vm] = auto_subclient.hvobj.VMs[vm].get_custom_attributes()
            self.log.info(f"All source VMs custom attributes: {backup_vm_custom_attributes}")

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

                VirtualServerUtils.decorative_log("Validating Custom Attributes")
                restored_vm_custom_attributes = dict()
                for vm in auto_subclient.vm_list:
                    restored_vm = auto_subclient.vm_restore_prefix + vm
                    self.log.info(f"Fetching Custom Attributes for {restored_vm}")
                    restored_vm_custom_attributes[vm] = auto_subclient.hvobj.VMs[restored_vm].get_custom_attributes()
                self.log.info(f"All restored VMs custom attributes: {backup_vm_custom_attributes}")

                for vm in auto_subclient.vm_list:
                    self.log.info(f"Comparing Custom Attributes for Source VM: {vm} and Restored VM: {auto_subclient.vm_restore_prefix + vm}")
                    if backup_vm_custom_attributes.get(vm) != restored_vm_custom_attributes.get(vm):
                        raise Exception("Custom Attributes of source VM and restored VM did not match")

                self.log.info("Source VM and destination VM have same custom attributes")

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options, status=self.test_individual_status)
            except Exception:
                self.log.warning("Testcase and/or Restored VM cleanup was not completed")
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
