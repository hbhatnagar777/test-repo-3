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
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA AzureRM backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA AzureRM Backup and Restore Cases with additional setting for patch restroe"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}
        self.is_regkey_exists = False
        self.vmobj = None
        self.reg_key_path = "VirtualServer"

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = self.tcinputs.get("BackupType", "FULL")
            if self.tcinputs.get("BackupMethod") == "SNAP":
                auto_subclient.subclient.enable_intelli_snap("Virtual Server Agent Snap")
                _adv = {"create_backup_copy_immediately": False}
                backup_options.advance_options = _adv
                backup_options.backup_method = "SNAP"
            else:
                auto_subclient.subclient.disable_intelli_snap()
            auto_subclient.backup(backup_options, skip_backup_job_type_check=False)
            auto_subclient.post_backup_validation(validate_workload=False, skip_snapshot_validation=False)

            try:
                self.log.info("Adding the registry key on the access node.")
                proxy = auto_subclient.auto_vsainstance.proxy_list[0]
                self.log.info("The proxy name is ", proxy)
                self.vmobj = Machine(
                    machine_name=proxy,
                    commcell_object=self.commcell
                )
                self.is_regkey_exists = self.vmobj.check_registry_exists(self.reg_key_path,
                                                                         "bAzureEnableReuseExistingVMRestore")

                if self.is_regkey_exists:
                    self.vmobj.update_registry(self.reg_key_path,
                                          "bAzureEnableReuseExistingVMRestore",
                                          "1",
                                          reg_type='String')
                    self.log.info("Reg Key already exists, updating it!!")
                else:
                    self.vmobj.create_registry(self.reg_key_path,
                                          "bAzureEnableReuseExistingVMRestore",
                                          "1",
                                          reg_type='String')


                self.log.info("Added the registry key successfully on the access node.")

                VirtualServerUtils.decorative_log("FULL VM in Place restores")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.in_place = True
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.is_patch_restore = True
                vm_restore_options.in_place_overwrite = True
                if self.tcinputs.get("BackupMethod") == "SNAP":
                    vm_restore_options.browse_from_snap = True
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

                if not self.is_regkey_exists:
                    VirtualServerUtils.decorative_log("Removing Registry Keys")
                    self.vmobj.remove_registry(
                        key=self.reg_key_path,
                        value="bAzureEnableReuseExistingVMRestore"
                    )
                    self.log.info("Registry key removed.")
                else:
                    self.log.info("Registry key already existed. Not removing.")
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED