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
        self.name = "VSA VMWARE V2 Indexing Snap - Backup Copy : Remote File Cache Pruning cases"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
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
            # auto_subclient.validate_inputs("windows", "windows", "windows", self.update_qa)

            VirtualServerUtils.decorative_log("FULL Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")

            auto_subclient.backup(backup_options)

            _Parent_Snap_jobid = auto_subclient.backup_job.job_id
            _Parent_Backupcopy_jobid = auto_subclient.backupcopy_job_id
            self.log.info("Parent SNAP JobID   : %s ", _Parent_Snap_jobid)
            self.log.info("Parent BKCOPY JobID : %s ", _Parent_Backupcopy_jobid)

            """ Validate and Delete metadata files from RFC for Snap"""
            VirtualServerUtils.decorative_log("Validate and Delete metadata files "
                                              "from RFC for SNAP")
            full_srclist = ['vmcollect_'+str(_Parent_Snap_jobid)+'.cvf', 'backup_'+
                            str(_Parent_Snap_jobid)+'.xml']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
                          "path post validation")
            auto_subclient.validate_rfc_files(_Parent_Snap_jobid, full_srclist, delete_rfc=True)

            """ Validate and Delete metadata files from RFC for Backup Copy"""
            VirtualServerUtils.decorative_log("Validate and Delete metadata files "
				                                          "from RFC for Backup Copy")
            full_srclist = ['vmcollect_'+str(_Parent_Backupcopy_jobid)+
				                        '.cvf', 'backup_'+str(_Parent_Snap_jobid)+'.xml']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
                          "path post validation")
            auto_subclient.validate_rfc_files(_Parent_Backupcopy_jobid, full_srclist,
                                              delete_rfc=True, skip_parent_validation=False,
                                              skip_child_validation=True)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from snap")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                if "SourceIP" and "DestinationIP" in self.tcinputs:
                    vm_restore_options.source_ip = self.tcinputs["SourceIP"]
                    vm_restore_options.destination_ip = self.tcinputs["DestinationIP"]
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from backup copy")
                vm_restore_options.browse_from_snap = False
                vm_restore_options.browse_from_backup_copy = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from snap")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_from_snap = True
                if "browse_ma" in self.tcinputs:
                    file_restore_options.browse_ma = self.tcinputs["browse_ma"]
                file_restore_options.browse_from_backup_copy = False
                file_restore_options.browse_from_snap = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores : "
                                                  "v2 Indexing from snap")
                vm_restore_options.browse_from_backup_copy = False
                vm_restore_options.browse_from_snap = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from backup copy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores"
                                                  " - v2 Indexing from backup copy")
                vm_restore_options.browse_from_snap = False
                vm_restore_options.browse_from_backup_copy = True
                vm_restore_options.unconditional_overwrite = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            VirtualServerUtils.decorative_log("INCREMENTAL Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)

            _Parent_Snap_jobid = auto_subclient.backup_job.job_id
            _Parent_Backupcopy_jobid = auto_subclient.backupcopy_job_id
            self.log.info("Parent SNAP JobID   : %s ", _Parent_Snap_jobid)
            self.log.info("Parent BKCOPY JobID : %s ", _Parent_Backupcopy_jobid)

            """ Validate and Delete metadata files from RFC for Snap"""
            VirtualServerUtils.decorative_log("Validate and Delete metadata files "
				                                          "from RFC for SNAP")
            full_srclist = ['vmcollect_'+str(_Parent_Snap_jobid)+
				                        '.cvf', 'backup_'+str(_Parent_Snap_jobid)+'.xml']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
                          "path post validation")
            auto_subclient.validate_rfc_files(_Parent_Snap_jobid, full_srclist, delete_rfc=True)

            """ Validate and Delete metadata files from RFC for Backup Copy"""
            VirtualServerUtils.decorative_log("Validate and Delete metadata files "
				                                          "from RFC for Backup Copy")
            full_srclist = ['vmcollect_'+str(_Parent_Backupcopy_jobid)+
				                        '.cvf', 'backup_'+str(_Parent_Snap_jobid)+'.xml']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
                          "path post validation")
            auto_subclient.validate_rfc_files(_Parent_Backupcopy_jobid, full_srclist,
                                              delete_rfc=True, skip_parent_validation=False,
                                              skip_child_validation=True)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from snap")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                if "SourceIP" and "DestinationIP" in self.tcinputs:
                    vm_restore_options.source_ip = self.tcinputs["SourceIP"]
                    vm_restore_options.destination_ip = self.tcinputs["DestinationIP"]
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from backup copy")
                vm_restore_options.browse_from_snap = False
                vm_restore_options.browse_from_backup_copy = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from snap")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_from_snap = True
                if "browse_ma" in self.tcinputs:
                    file_restore_options.browse_ma = self.tcinputs["browse_ma"]
                file_restore_options.browse_from_backup_copy = False
                file_restore_options.browse_from_snap = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores : "
                                                  "v2 Indexing from snap")
                vm_restore_options.browse_from_backup_copy = False
                vm_restore_options.browse_from_snap = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from backup copy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores"
                                                  " - v2 Indexing from backup copy")
                vm_restore_options.browse_from_snap = False
                vm_restore_options.browse_from_backup_copy = True
                vm_restore_options.unconditional_overwrite = True
                for vm in auto_subclient.vm_list:
                    auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
