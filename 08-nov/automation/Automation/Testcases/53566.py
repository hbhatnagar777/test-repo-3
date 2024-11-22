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
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2: VSA VMWARE Full backup without Metadata collection " \
                    "with Windows Proxy and Windows MA"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.ind_status = True
        self.failure_msg = ""
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            if not auto_subclient.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1'
                raise Exception(self.failure_msg)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.pre_backup_config_checks['min_proxy_os']['count'] = 1
            backup_options.pre_backup_config_checks['min_proxy_os']['os_list'] = ['windows']
            backup_options.pre_backup_config_checks['ma_os']['count'] = 1
            backup_options.pre_backup_config_checks['ma_os']['os_list'] = ['windows']
            backup_options.pre_backup_config_checks['ma_os']['validate'] = True
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("Disk Restores")
                disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
                auto_subclient.disk_restore(disk_restore_options)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Out of place full vm restore")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                VirtualServerUtils.set_inputs(self.tcinputs, vm_restore_options)
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Inplace full vm restore")
                vm_restore_options.in_place_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Guest file restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
