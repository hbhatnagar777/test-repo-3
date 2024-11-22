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
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMWARE Full Snap backup
    and Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE SNAP Full Backup and Restore Cases for v2 indexing"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.ind_status = True
        self.failure_msg = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = backup_options = None
            self.log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            if self.tcinputs.get('del_disk_delete', None):
                try:
                    auto_subclient.disk_cleanup_before_backup()
                except Exception as ex:
                    self.ind_status = False
                    self.failure_msg = str(ex)
                    self.log.exception('Failing during disk cleanup before backup {}'. format(self.failure_msg))

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from snap: Parent Level")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                if "SourceIP" and "DestinationIP" in self.tcinputs:
                    vm_restore_options.source_ip = self.tcinputs["SourceIP"]
                    vm_restore_options.destination_ip = self.tcinputs["DestinationIP"]
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from snap")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_from_backup_copy = False
                file_restore_options.browse_from_snap = True
                if "browse_ma" in self.tcinputs:
                    file_restore_options.browse_ma = self.tcinputs["browse_ma"]
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from backup copy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores"
                                                  " - v2 Indexing from backup copy: Child level")
                vm_restore_options.browse_from_snap = False
                vm_restore_options.browse_from_backup_copy = True
                vm_restore_options.unconditional_overwrite = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
