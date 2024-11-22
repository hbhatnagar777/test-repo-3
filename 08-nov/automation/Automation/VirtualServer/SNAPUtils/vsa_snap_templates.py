# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# gitlab
# --------------------------------------------------------------------------

"""Template file for performing IntelliSnap operations for Virtual Server Agent

VSASNAPTemplates is the only class defined in this file

VSASNAPTemplates: Template class to perform IntelliSnap operations

VSASNAPTemplates:

    __init__()                   --  initializes VSASNAPTemplates object

    vsasnap_template_v1()        --  Template to Perform Snap backup, backup copy and Full VM Restore
                                     operations for VSA V1 client.
    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Out of place full vm restore from snap.
        4. In place full vm restore from backup copy

    vsasnap_template_v1_guestfile() -- Template to Perform Snapbackup, backup copy and Guest File
                                        Restore operations for VSA V1 client
    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Guest file restore from Snap (live Browse).
        4. Guest file restore from backup copy.

    vsasnap_template_v1_disk() -- Template to Perform Snapbackup, backup copy and Disk
                                        Restore operations for VSA V1 client

        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Disk restore from Snap.
        4. Disk restore from backup copy



    vsasnap_template_v2()        --  Template to Perform Snap backup, backup copy and Restore
                                     operations for VSA V2 client.

    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Out of place full vm restore from snap (parent job)
        4. In place full vm restore from backup copy

    vsasnap_template_v2_fullvm_client()        --  Template to Perform Snap backup, backup copy and Restore
                                     operations for VSA V2 client.

    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. FULL VM In Place restores : v2 Indexing from snap
        4. FULL VM out of Place restores - v2 Indexing from backup copy

    vsasnap_template_v2_guestfile()        --  Template to Perform Snap backup, backup copy and Restore
                                     operations for VSA V2 client.

    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Guest Files restores - v2 Indexing from snap
        4. Guest Files restores - v2 Indexing from backup copy

    vsasnap_template_v2_disk()        --  Template to Perform Snap backup, backup copy and Restore
                                     operations for VSA V2 client.

    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Backup copy of that VM.
        3. Disk restore from Snap.
        4. Disk restore from backup copy


    vsasnap_template_replica_v1()       -- Template to Perform Snap backup with replication,
                                        backup copy and Restore from replica for VSA V1 client
    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Run Aux copy
        3. Run backup copy
        4. Guest file restore from Replica copy
        5. Full VM out of place restore from Replica copy

    vsasnap_template_replica_v2()       -- Template to Perform Snap backup with replication,
                                        backup copy and Restore from replica for VSA V2 client
    Steps:
        1. Snap Backup of VM coming from a particular snap vendor array
        2. Run Aux copy
        3. Run backup copy
        4. Guest file restore from Replica copy
        5. Full VM out of place restore from Replica copy


"""
import logging
import time
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.SNAPUtils.vsa_snaphelper import VSASNAPHelper
from VirtualServer.SNAPUtils.vsa_snapconstants import VSASNAPConstants



class VSASNAPTemplates(object):
    """Template class to perform vsa snap operations"""

    def __init__(self, testcase):
        """Initializes VSASNAPTemplates object

        Args:

            testcase                        -- test case Object

        """

        VirtualServerUtils.decorative_log("Initialize constant objects")
        self.vsa_snapconstants = VSASNAPConstants(testcase.commcell, testcase.tcinputs)
        VirtualServerUtils.decorative_log("Initialize subclient objects")
        self.vsa_snapconstants.auto_commcell = VirtualServerHelper.AutoVSACommcell(
            testcase.commcell, testcase.csdb)
        self.vsa_snapconstants.auto_client = VirtualServerHelper.AutoVSAVSClient(
            self.vsa_snapconstants.auto_commcell, testcase.client)
        self.vsa_snapconstants.auto_instance = VirtualServerHelper.AutoVSAVSInstance(
            self.vsa_snapconstants.auto_client, testcase.agent, testcase.instance)
        self.vsa_snapconstants.auto_backupset = VirtualServerHelper.AutoVSABackupset(
            self.vsa_snapconstants.auto_instance, testcase.backupset)
        self.vsa_snapconstants.auto_subclient = VirtualServerHelper.AutoVSASubclient(
            self.vsa_snapconstants.auto_backupset, testcase.subclient)
        self.testcase = testcase
        VirtualServerUtils.decorative_log("Initialize helper objects")
        self.vsa_snaphelper = VSASNAPHelper(testcase.commcell, testcase.tcinputs, self.vsa_snapconstants)

    def vsasnap_template_v1(self, vsaproxy_os="", guest_os="", transport_mode="", vmfs_nfs_vm_config=False):
        """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V1 client
        Args:
            vsaproxy_os                (str):  expected os of the proxy
            guest_os                   (str):  expected os of the Guest
            transport_mode             (str):  expected transport mode
            vmfs_nfs_vm_config         (bool): when vm is configured using vmfs and nfs datastores
        """

        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy'):
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.validate_inputs(vsaproxy_os, "", guest_os, True)
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()
        self.vsa_snaphelper.validate_transport_mode(transport_mode)

        if self.testcase.tcinputs["snap_engine"] in ["Cisco HyperFlex Snap"]:
            VirtualServerUtils.decorative_log("Mounting/Unmounting Snapshot..")
            self.testcase.log.info("No hardware snap mount for Cisco engine, so skipping mount/umount steps")
        else:
            VirtualServerUtils.decorative_log("Mounting Snapshot..")
            self.vsa_snaphelper.mount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
            time.sleep(60)
            VirtualServerUtils.decorative_log("UnMounting Snapshot..")
            self.vsa_snaphelper.unmount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)

        vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
        try:
            VirtualServerUtils.decorative_log("Out of place full vm restore from snap")
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = True
            self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Restore from Snap")
        file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
        if vmfs_nfs_vm_config:
            try:
                VirtualServerUtils.decorative_log("Guest file restore from Snap")
                file_restore_options.browse_from_snap = True
                if "browse_ma" in self.testcase.tcinputs:
                    file_restore_options.browse_ma = self.testcase.tcinputs["browse_ma"]
                if "fbr_ma" in self.testcase.tcinputs:
                    file_restore_options.fbr_ma = self.testcase.tcinputs["fbr_ma"]
                self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.testcase.log.error("sleeping 12 minutes for cleanup of mounted snaps")
                time.sleep(720)
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        if self.testcase.tcinputs["snap_engine"] in ["Cisco HyperFlex Snap"]:
            self.testcase.log.info("In-Place Restore is not supported for Cisco snap Engine")
            vm_restore_options.power_on_after_restore = False
        else:
            try:
                VirtualServerUtils.decorative_log("In place full vm restore from backup copy")
                vm_restore_options.in_place_overwrite = True
                vm_restore_options.browse_from_backup_copy = True
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        if vmfs_nfs_vm_config:
            try:
                VirtualServerUtils.decorative_log("Guest file restore from backup copy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Deleting Snapshot..")
        self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_v1_guestfile(self, vsaproxy_os="", guest_os="", transport_mode=""):
        """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V1 client
        Args:
            vsaproxy_os                (str):  expected os of the proxy
        """
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        backup_jobids=[]
        VirtualServerUtils.decorative_log("Full Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy'):
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.validate_inputs(vsaproxy_os, "", guest_os, True)
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()
        self.vsa_snaphelper.validate_transport_mode(transport_mode)

        VirtualServerUtils.decorative_log("Restore from Snap")
        vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
        file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)

        try:
            VirtualServerUtils.decorative_log("Guest file restore from Snap")
            file_restore_options.browse_from_snap = True
            if "browse_ma" in self.testcase.tcinputs:
                file_restore_options.browse_ma = self.testcase.tcinputs["browse_ma"]
            if "fbr_ma" in self.testcase.tcinputs:
                file_restore_options.fbr_ma = self.testcase.tcinputs["fbr_ma"]
            self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options)
        except Exception as exp:
            self.testcase.log.error("sleeping 12 minutes for cleanup of mounted snaps")
            time.sleep(720)
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Incremental Backup")
        backup_options.backup_method = "SNAP"
        backup_options.backup_type = "INCREMENTAL"
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("Restore from backup copy")

        try:
            VirtualServerUtils.decorative_log("Guest file restore from backup copy")
            file_restore_options.browse_from_snap = False
            file_restore_options.browse_from_backup_copy = True
            self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        for jobid in backup_jobids:
            VirtualServerUtils.decorative_log("Deleting Snapshot..")
            self.vsa_snaphelper.delete_snap(jobid, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_v1_disk(self):
            """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V1 client
            """

            if self.vsa_snapconstants.arrayname:
                self.vsa_snaphelper.add_primary_array()
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
            if self.testcase.tcinputs.get('offline_backupcopy'):
                _adv = {"create_backup_copy_immediately": False}
            else:
                _adv = {"create_backup_copy_immediately": True}
            if self.testcase.tcinputs.get('skip_pre_backup_config'):
                backup_options.run_pre_backup_config_checks = False
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            self.vsa_snapconstants.auto_subclient.backup(backup_options)
            if not backup_options.advance_options.get("create_backup_copy_immediately"):
                self.vsa_snaphelper.run_backup_copy()

            disk_restore_options = OptionsHelper.DiskRestoreOptions(self.vsa_snapconstants.auto_subclient)
            try:
                VirtualServerUtils.decorative_log("Disk restore from Snap")
                disk_restore_options.browse_from_snap = True
                self.vsa_snapconstants.auto_subclient.disk_restore(disk_restore_options)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Disk restore from backup copy")
                disk_restore_options.browse_from_backup_copy = True
                self.vsa_snapconstants.auto_subclient.disk_restore(disk_restore_options)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

            VirtualServerUtils.decorative_log("Deleting Snapshot..")
            self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
            return (self.vsa_snapconstants.auto_subclient, backup_options, self.testcase.test_individual_status, self.testcase.test_individual_failure_message)

    def vsasnap_template_v2(self, vsaproxy_os="", guest_os="", transport_mode="", multi_node=False, vmfs_nfs_vm_config=False):
        """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V2 client
        Args:
            vsaproxy_os                (str):  expected os of the proxy
            guest_os                   (str):  expected os of the Guest
            transport_mode             (str):  expected transport mode
            multi_node                 (bool): verify multinode
            vmfs_nfs_vm_config         (bool): when vm is configured using vmfs and nfs datastores

        return:
            vsa_snapconstants.auto_subclient  (obj):  subclient object
            backup_option                     (obj):  backup options object
            vm_restore_option                 (obj):  vm restore options object

        Exceptions:
            test_individual_status     (bool): Test individual opration status
            test_individual_failure_message (bool): individual failure status
        """

        self.testcase.log.info("Started executing %s testcase", self.testcase.id)
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()

        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy') or multi_node:
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.validate_inputs(vsaproxy_os, "", guest_os, True)
        if multi_node:
            self.vsa_snaphelper.multinode_config()
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            if multi_node:
                self.vsa_snaphelper.run_backup_copy(multinode_verify=True,
                                                    snap_job_id=self.vsa_snapconstants.auto_subclient.backup_job.job_id)
            else:
                self.vsa_snaphelper.run_backup_copy()
        if not multi_node:
            self.vsa_snaphelper.validate_transport_mode(transport_mode)

        if self.testcase.tcinputs["snap_engine"] in ["Cisco HyperFlex Snap"]:
            VirtualServerUtils.decorative_log("Mounting/Unmounting Snapshot..")
            self.testcase.log.info("No hardware snap mount for Cisco engine, so skipping mount/umount steps")
        elif not multi_node:
            VirtualServerUtils.decorative_log("Mounting Snapshot..")
            self.vsa_snaphelper.mount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)

            VirtualServerUtils.decorative_log("UnMounting Snapshot..")
            self.vsa_snaphelper.unmount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores from snap")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                if "SourceIP" and "DestinationIP" in self.testcase.tcinputs:
                    vm_restore_options.source_ip = self.testcase.tcinputs["SourceIP"]
                    vm_restore_options.destination_ip = self.testcase.tcinputs["DestinationIP"]
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        if vmfs_nfs_vm_config:
            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from snap")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
                VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
                file_restore_options.browse_from_backup_copy = False
                file_restore_options.browse_from_snap = True
                for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                    self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        if self.testcase.tcinputs["snap_engine"] in ["Cisco HyperFlex Snap"]:
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
            self.testcase.log.info("In-Place Restore is not supported for Cisco snap Engine")
            vm_restore_options.power_on_after_restore = False
        else:
            try:
                VirtualServerUtils.decorative_log("In place full vm restore from backup copy")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.in_place_overwrite = True
                vm_restore_options.browse_from_backup_copy = True
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        if vmfs_nfs_vm_config:
            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing from backup copy")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
                VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                    self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Deleting Snapshot..")
        self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_v2_fullvm_client(self):
        """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V2 client
        """

        self.testcase.log.info("Started executing %s testcase", self.testcase.id)
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()

        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy'):
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
        vm_restore_options.power_on_after_restore = True
        vm_restore_options.unconditional_overwrite = True

        try:
            VirtualServerUtils.decorative_log("FULL VM out of Place restores"
                                              " - v2 Indexing from backup copy")
            vm_restore_options.browse_from_snap = False
            vm_restore_options.browse_from_backup_copy = True
            vm_restore_options.unconditional_overwrite = True
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        if self.testcase.tcinputs["snap_engine"] in ["Cisco HyperFlex Snap"]:
            self.testcase.log.info("In-Place Restore is not supported for Cisco snap Engine")
            vm_restore_options.power_on_after_restore = False
        else:
            try:
                VirtualServerUtils.decorative_log("FULL VM In Place restores : "
                                                  "v2 Indexing from snap")
                vm_restore_options.browse_from_backup_copy = False
                vm_restore_options.browse_from_snap = True
                vm_restore_options.in_place_overwrite = True
                for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                    self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Deleting Snapshot..")
        self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_v2_guestfile(self, vsaproxy_os="", guest_os="", transport_mode="", ma_os=""):
        """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V2 client
        Args:
            vsaproxy_os                (str):  expected os of the proxy
        """

        self.testcase.log.info("Started executing %s testcase", self.testcase.id)
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        backup_jobids=[]
        VirtualServerUtils.decorative_log("Full Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy'):
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.validate_inputs(vsaproxy_os, ma_os, guest_os, True)
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()
        self.vsa_snaphelper.validate_transport_mode(transport_mode)

        try:
            VirtualServerUtils.decorative_log("Files restores - v2 Indexing from snap")
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
            VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
            file_restore_options.browse_from_backup_copy = False
            file_restore_options.browse_from_snap = True
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        try:
            VirtualServerUtils.decorative_log("Incremental Backup")
            backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            backup_options.backup_method = "SNAP"
            backup_options.modify_data = True
            if self.testcase.tcinputs.get('skip_pre_backup_config'):
                backup_options.run_pre_backup_config_checks = False
            self.vsa_snapconstants.auto_subclient.backup(backup_options)
            backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
            if not backup_options.advance_options.get("create_backup_copy_immediately"):
                self.vsa_snaphelper.run_backup_copy()
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        try:
            VirtualServerUtils.decorative_log("Files restores - v2 Indexing from backup copy")
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
            VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
            file_restore_options.browse_from_snap = False
            file_restore_options.browse_from_backup_copy = True
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        for jobid in backup_jobids:
            VirtualServerUtils.decorative_log("Deleting Snapshot..")
            self.vsa_snaphelper.delete_snap(jobid, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, self.testcase.test_individual_status, self.testcase.test_individual_failure_message)

    def vsasnap_template_v2_disk(self):
        """ Template to Perform Snap backup, backup copy and Restore opertaions for VSA V2 client
        """

        self.testcase.log.info("Started executing %s testcase", self.testcase.id)
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()

        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy'):
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        try:
            VirtualServerUtils.decorative_log("Disk restore from Snap")
            disk_restore_options = OptionsHelper.DiskRestoreOptions(self.vsa_snapconstants.auto_subclient)
            disk_restore_options.browse_from_snap = True
            self.vsa_snapconstants.auto_subclient.disk_restore(disk_restore_options)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        try:
            VirtualServerUtils.decorative_log("Disk restore from backup copy")
            disk_restore_options.browse_from_backup_copy = True
            self.vsa_snapconstants.auto_subclient.disk_restore(disk_restore_options)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Deleting Snapshot..")
        self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_replica_v1(self):
        """ Template to Perform Snap backup with replication, backup copy and Restore from replica for VSA V1 client
        """
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        if self.vsa_snapconstants.arrayname2:
            self.vsa_snaphelper.add_primary_array()

        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        backup_options.backup_method = "SNAP"
        _adv = {"create_backup_copy_immediately": False}
        backup_options.advance_options = _adv
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        if backup_options.collect_metadata:
            raise Exception('Metadata collection is enabled')
        self.vsa_snapconstants.auto_subclient.backup(backup_options)

        self.vsa_snaphelper.update_storage_policy(3)
        self.vsa_snaphelper.delete_bkpcpy_schedule()
        self.vsa_snaphelper.run_aux_copy()
        self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("Mounting Snapshot..")
        self.vsa_snaphelper.mount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)

        VirtualServerUtils.decorative_log("UnMounting Snapshot..")
        self.vsa_snaphelper.unmount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)

        for _copy_precedence in self.vsa_snapconstants.secondary_copies:
            VirtualServerUtils.decorative_log(f'Restore from Replica copy {_copy_precedence}')

            try:
                VirtualServerUtils.decorative_log(f'Guest file restore from Replica {_copy_precedence}')
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
                VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
                file_restore_options.browse_from_snap = True
                file_restore_options.copy_precedence = _copy_precedence
                self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.testcase.log.error('sleeping 12 minutes for cleanup of mounted snaps')
                time.sleep(720)
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log(f'Out of place full vm restore from Replica {_copy_precedence}')
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                vm_restore_options.copy_precedence = _copy_precedence
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Deleting Snapshots..")
        self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)
        if self.testcase.tcinputs["snap_engine"] in ["NetApp"]:
            self.vsa_snaphelper.force_delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        else:
            self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options, self.testcase.test_individual_status, self.testcase.test_individual_failure_message)

    def vsasnap_template_replica_v2(self):
        """ Template to Perform Snap backup with replication, backup copy and Restore from replica for VSA V2 client
        """
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        if self.vsa_snapconstants.arrayname2:
            self.vsa_snaphelper.add_secondary_array()

        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        backup_options.backup_method = "SNAP"
        _adv = {"create_backup_copy_immediately": False}
        backup_options.advance_options = _adv
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        if backup_options.collect_metadata:
            raise Exception('Metadata collection is enabled')
        self.vsa_snapconstants.auto_subclient.backup(backup_options)

        self.vsa_snaphelper.update_storage_policy(3)
        self.vsa_snaphelper.delete_bkpcpy_schedule()
        self.vsa_snaphelper.run_aux_copy()
        self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("Mounting Snapshot..")
        self.vsa_snaphelper.mount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)

        VirtualServerUtils.decorative_log("UnMounting Snapshot..")
        self.vsa_snaphelper.unmount_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)

        for _copy_precedence in self.vsa_snapconstants.secondary_copies:
            VirtualServerUtils.decorative_log(f'Restore from Replica copy {_copy_precedence}')
            try:
                VirtualServerUtils.decorative_log(f'Guest file restore from Replica {_copy_precedence}')
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
                VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
                file_restore_options.browse_from_snap = True
                file_restore_options.copy_precedence = _copy_precedence
                for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                    self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.testcase.log.error('sleeping 12 minutes for cleanup of mounted snaps')
                time.sleep(720)
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log(f'Out of place full vm restore from Replica {_copy_precedence}')
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                vm_restore_options.copy_precedence = _copy_precedence
                for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                    self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
            except Exception as exp:
                self.testcase.test_individual_status = False
                self.testcase.test_individual_failure_message = str(exp)

        VirtualServerUtils.decorative_log("Deleting Snapshots..")
        self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)
        if self.testcase.tcinputs["snap_engine"] in ["NetApp"]:
            self.vsa_snaphelper.force_delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        else:
            self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)
        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_v2_synthfull(self):
        """ Template to Perform Snap backup, backup copy, Synthfull and Restore opertaions for VSA V2 client
        """

        self.testcase.log.info("Started executing %s testcase", self.testcase.id)
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        backup_jobids = []

        VirtualServerUtils.decorative_log("Full Snap Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        if self.testcase.tcinputs.get('offline_backupcopy'):
            _adv = {"create_backup_copy_immediately": False}
        else:
            _adv = {"create_backup_copy_immediately": True}
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("First Incremental Snap Backup")
        backup_options.backup_method = "SNAP"
        backup_options.backup_type = "INCREMENTAL"
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("Synth full Backup")
        backup_options.backup_method = "SNAP"
        backup_options.collect_metadata = True
        backup_options.backup_type = "SYNTHETIC_FULL"
        backup_options.incr_level = 'BEFORE_SYNTH'
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("Incremental Snap Backup after synth full")
        backup_options.backup_method = "SNAP"
        backup_options.backup_type = "INCREMENTAL"
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        VirtualServerUtils.decorative_log("Second Synth full Backup")
        backup_options.backup_method = "SNAP"
        backup_options.collect_metadata = True
        backup_options.backup_type = "SYNTHETIC_FULL"
        backup_options.incr_level = 'BEFORE_SYNTH'
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy()

        try:
            VirtualServerUtils.decorative_log("FULL VM out of Place restores"
                                              " - v2 Indexing from Synth full")
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = False
            vm_restore_options.browse_from_backup_copy = True
            vm_restore_options.restore_backup_job = self.vsa_snapconstants.auto_subclient.backup_job.job_id
            if "SourceIP" and "DestinationIP" in self.testcase.tcinputs:
                vm_restore_options.source_ip = self.testcase.tcinputs["SourceIP"]
                vm_restore_options.destination_ip = self.testcase.tcinputs["DestinationIP"]
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        try:
            VirtualServerUtils.decorative_log("Files restores - v2 Indexing from Synth full")
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(self.vsa_snapconstants.auto_subclient)
            VirtualServerUtils.set_inputs(self.testcase.tcinputs, file_restore_options)
            file_restore_options.browse_from_snap = False
            file_restore_options.browse_from_backup_copy = True
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)

        for jobid in backup_jobids:
            VirtualServerUtils.decorative_log("Deleting Snapshot..")
            self.vsa_snaphelper.delete_snap(jobid, 1)

        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options, self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_template_metro_backup(self):
        """ Template to Perform Snap backup with metro configuration, backup copy and Restore for VSA V2 client
        """
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        if self.vsa_snapconstants.arrayname2:
            self.vsa_snaphelper.add_secondary_array()
        access_node_primary = {self.testcase.tcinputs["browse_ma"]: 'add'}
        access_node_secondary = {self.testcase.tcinputs["browse_ma"]: 'delete'}
        self.vsa_snaphelper.edit_array(self.vsa_snapconstants.arrayname,
                                       self.vsa_snapconstants.source_config,
                                       self.vsa_snapconstants.config_update_level,
                                       array_access_node=access_node_primary)
        self.vsa_snaphelper.edit_array(self.testcase.tcinputs['ArrayName2'],
                                       self.vsa_snapconstants.target_config,
                                       self.vsa_snapconstants.config_update_level,
                                       array_access_node=access_node_secondary)
        if self.testcase.tcinputs['snap_engine'] in ['Hitachi Thin Image (CCI)', 'Hitachi Shadow Image (CCI)']:
            if self.vsa_snapconstants.vsm_array_name1:
                self.vsa_snaphelper.edit_array(self.testcase.tcinputs['VSMArrayName1'],
                                               self.vsa_snapconstants.source_config,
                                               self.vsa_snapconstants.config_update_level,
                                               array_access_node=access_node_primary,
                                               gad_arrayname=self.testcase.tcinputs['ArrayName'])
            if self.vsa_snapconstants.vsm_array_name2:
                self.vsa_snaphelper.edit_array(self.testcase.tcinputs['VSMArrayName2'],
                                               self.vsa_snapconstants.target_config,
                                               self.vsa_snapconstants.config_update_level,
                                               level_id=None,
                                               array_access_node=access_node_secondary,
                                               gad_arrayname=self.testcase.tcinputs['ArrayName2'])
        backup_jobids = []
        if self.testcase.tcinputs['snap_engine'] in ['Hitachi Thin Image (CCI)', 'Hitachi Shadow Image (CCI)']:
            if self.vsa_snapconstants.vsm_to_vsm:
                ctrlhost_array1 = self.vsa_snapconstants.execute_query(
                    self.vsa_snapconstants.get_gad_controlhost_id, {'a': self.testcase.tcinputs['ArrayName'],
                                                                'b': self.testcase.tcinputs['VSMArrayName1']})
                ctrlhost_array2 = self.vsa_snapconstants.execute_query(
                    self.vsa_snapconstants.get_gad_controlhost_id, {'a': self.testcase.tcinputs['ArrayName2'],
                                                                'b': self.testcase.tcinputs['VSMArrayName2']})

            else:
                ctrlhost_array1 = self.vsa_snapconstants.execute_query(
                    self.vsa_snapconstants.get_gad_controlhost_id, {'a': '',
                                                                'b': self.testcase.tcinputs['ArrayName']})

                ctrlhost_array2 = self.vsa_snapconstants.execute_query(
                    self.vsa_snapconstants.get_gad_controlhost_id, {'a': self.testcase.tcinputs['ArrayName2'],
                                                                'b': self.testcase.tcinputs['VSMArrayName2']})

        else:
            ctrlhost_array1 = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_controlhost_id, {'a': self.testcase.tcinputs['ArrayName']})
            ctrlhost_array2 = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_controlhost_id, {'a': self.testcase.tcinputs['ArrayName2']})

        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        _adv = {"create_backup_copy_immediately": False}
        backup_options.advance_options = _adv
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        unique_controlhost_id = self.vsa_snaphelper.unique_control_host(
            self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if len(unique_controlhost_id) == 2:
            for i in range(len(unique_controlhost_id)):
                if unique_controlhost_id[i][0] not in (ctrlhost_array1[0][0], ctrlhost_array2[0][0]):
                    raise Exception(
                        f"Snapshots for job : {self.vsa_snapconstants.auto_subclient.backup_job.job_id} "
                        f"not created on both Nodes"
                    )
        else:
            raise Exception(
                f"Snapshots for job : {self.vsa_snapconstants.auto_subclient.backup_job.job_id}"
                f" not created on both Nodes"
            )
        VirtualServerUtils.decorative_log("Snaps created on both nodes of Metro Cluster")
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy(metro_verify=True, ctrlhost_array=ctrlhost_array1,
                                                snap_job_id=self.vsa_snapconstants.auto_subclient.backup_job.job_id)

        if self.testcase.tcinputs['snap_engine'] in ['Hitachi Thin Image (CCI)', 'Hitachi Shadow Image (CCI)']:
            if self.vsa_snapconstants.vsm_to_vsm:
                self.vsa_snaphelper.edit_array(self.testcase.tcinputs['VSMArrayName1'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_secondary,
                                               gad_arrayname=self.testcase.tcinputs['ArrayName'])
                self.vsa_snaphelper.edit_array(self.testcase.tcinputs['VSMArrayName2'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_primary,
                                               gad_arrayname=self.testcase.tcinputs['ArrayName2'])
                VirtualServerUtils.decorative_log("Successfully updated array controller for the secondary array.")

            else:
                self.vsa_snaphelper.edit_array(self.testcase.tcinputs['ArrayName'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_secondary
                                               )
                self.vsa_snaphelper.edit_array(self.testcase.tcinputs['VSMArrayName2'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_primary,
                                               gad_arrayname=self.testcase.tcinputs['ArrayName2'])
                VirtualServerUtils.decorative_log("Successfully updated array controller for the secondary array.")
        else:
            self.vsa_snaphelper.edit_array(self.testcase.tcinputs['ArrayName'],
                                           snap_configs=None,
                                           config_update_level="array",
                                           array_access_node=access_node_secondary)

            self.vsa_snaphelper.edit_array(self.testcase.tcinputs['ArrayName2'],
                                           snap_configs=None,
                                           config_update_level="array",
                                           array_access_node=access_node_primary)

        VirtualServerUtils.decorative_log("First Incremental Snap Backup")
        backup_options.backup_method = "SNAP"
        backup_options.backup_type = "INCREMENTAL"
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        unique_controlhost_id = self.vsa_snaphelper.unique_control_host(
            self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if len(unique_controlhost_id) == 2:
            for i in range(len(unique_controlhost_id)):
                if unique_controlhost_id[i][0] not in (ctrlhost_array1[0][0], ctrlhost_array2[0][0]):
                    raise Exception(
                        f"Snapshots for job : {self.vsa_snapconstants.auto_subclient.backup_job.job_id} "
                        "ot created on both Nodes"
                    )
        else:
            raise Exception(
                f"Snapshots for job : {self.vsa_snapconstants.auto_subclient.backup_job.job_id}"
                f" not created on both Nodes"
            )
        VirtualServerUtils.decorative_log("Snaps created on both nodes of Metro Cluster")
        backup_jobids.append(self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        if not backup_options.advance_options.get("create_backup_copy_immediately"):
            self.vsa_snaphelper.run_backup_copy(metro_verify=True, ctrlhost_array=ctrlhost_array2,
                                                snap_job_id=self.vsa_snapconstants.auto_subclient.backup_job.job_id)

        vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self.testcase)
        try:
            VirtualServerUtils.decorative_log("Out of place full vm restore from snap")
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = True
            self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)
        except Exception as exp:
            self.testcase.test_individual_status = False
            self.testcase.test_individual_failure_message = str(exp)
            
        for jobid in backup_jobids:
            VirtualServerUtils.decorative_log("Deleting Snapshot..")
            self.vsa_snaphelper.delete_snap(jobid, 1)

        return (self.vsa_snapconstants.auto_subclient, backup_options, vm_restore_options,
                self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def vsasnap_sharedsnap(self):
        """ Template to Test VSA-V2 Shared snap deletion """

        self.testcase.log.info("Started executing %s testcase", self.testcase.id)

        # Validating testcase input.

        vm_obj_keys = self.vsa_snapconstants.auto_instance.hvobj.VMs.values()
        vm_ds = []
        vm_list = []
        for vms in vm_obj_keys:
            vm_ds.append(vms.datastore)
            vm_list.append(vms.vm_name)

        if self.testcase.id == '59347':
            dup_ds = set(vm_ds)
            if (len(vm_ds) != len(dup_ds)) or len(vm_list) == 1:
                raise Exception(
                    "Subclient content must be multiple VMs and each VM should belong to single DS"
                )
        else:
            if len(set(vm_ds)) != 1 or len(vm_list) == 1:
                raise Exception(
                    "All VMs in subclient must be from same datastore and must have multiplve VMs"
                )

        # Running Snap backup.
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)

        backup_options.backup_method = "SNAP"
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        self.vsa_snapconstants.auto_subclient.backup(backup_options)

        master_jobid = self.vsa_snapconstants.auto_subclient.backup_job.job_id
        child_jobid = self.vsa_snapconstants.auto_subclient.get_childjob_foreachvm(master_jobid)
        vmjob_ids = tuple(child_jobid.values())
        joblist = [child_jobid[key] for key in child_jobid]
        copyid = self.vsa_snaphelper.spcopy_obj(1).copy_id
        jobs_to_validate = "(%s)" % vmjob_ids[1] if len(vmjob_ids) == 2 else ''.join(vmjob_ids[1:])
        jobid_to_check = joblist[1:]
        query_params = {'a': jobid_to_check}
        if len(jobid_to_check) == 1:
            query_params['a'] = jobid_to_check[0]

        # collecting smvolume and snap list after snap backup
        smsnap_prebk = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_snap_id, {'a': master_jobid})

        # Unpick job for one of the VM and start backup copy operation.
        VirtualServerUtils.decorative_log("Running offline backup copy by unpicking job for VM")
        primary_copy = self.vsa_snaphelper.storage_policy_obj.get_primary_copy()
        primary_copy.do_not_copy_jobs(joblist[0])

        # Run offline backup copy
        self.vsa_snaphelper.run_backup_copy()

        # Validate smvolume and smsnap details for jobs which are back up copied
        self.testcase.log.info("Waiting for 300 sec for snapshot get prune and age")
        time.sleep(300) # waiting until snapshot is marked prune and age

        smvolid_postbkup = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_volumelist_id, {'a': jobs_to_validate, 'b': copyid})

        engine_id = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_snapengine_id, {'a': self.testcase.tcinputs["snap_engine"]})

        # Engine ID : 3 = Netapp, 44 = HPE nimble, 33 = Hitachi Shadow Image (CCI), 34 = Hitachi Thin Image (CCI)
                # 52 = Pure
        engine_id_to_check = ('3', '44', '33', '34', '52')
        if self.testcase.id == '59347':
            smsnap_postbk = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_snap_id, {'a': master_jobid})

            if engine_id[0][0] in engine_id_to_check:
                if smvolid_postbkup[0][0] in [None, ' ', ''] and smsnap_postbk != smsnap_prebk:
                    self.testcase.log.info("snapshot is deleted for Job: %s", list(child_jobid.values())[1])
                else:
                    raise Exception(
                        "Snapshot of jobid: {0} is not yet deleted,"
                        "please check the CVMA logs for any of the job".format(list(child_jobid.values())[1])
                    )
            else:
                if smvolid_postbkup[0][0] in [None, ' ', ''] and smsnap_prebk == smsnap_postbk:
                    self.testcase.log.info("snapshot is logically deleted for Job: %s", list(child_jobid.values())[1])
                else:
                    raise Exception(
                        "Snapshot of jobid: {0} deleted,"
                        "please check the CVMA logs for any of the job".format(list(child_jobid.values())[1])
                    )
        else:
            smsnap_postbk = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_snap_id, query_params)

            if smvolid_postbkup[0][0] in [None, ' ', ''] and smsnap_postbk[0][0] in [None, ' ', '']:
                self.testcase.log.info("snapshot is deleted for Job: %s", list(child_jobid.values())[1])
            else:
                raise Exception(
                    "Snapshot is not yet deleted,"
                    "please check the CVMA logs for any of the job".format(list(child_jobid.values())[1])
                )

        # Re-pick the skipped job and verify snaps are aged successfully after backup copy.
        primary_copy.pick_jobs_for_backupcopy(list(child_jobid.values())[0])
        self.vsa_snaphelper.run_backup_copy()

        self.testcase.log.info("Waiting for 300 sec for snapshot get prune and age")
        time.sleep(300)  # waiting until snapshot is marked prune and age

        ## Check for Logical and physical deletion of snap after backup copy finished
        counter = 0
        while True:
            smvolid_list = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_volumelist_id, {'a': vmjob_ids, 'b': copyid})
            smsnap_list = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_snap_id, {'a': master_jobid})

            if smvolid_list[0][0] in [None, ' ', ''] and smsnap_list[0][0] in [None, ' ', '']:
                self.testcase.log.info("snapshot is logically and physically deleted")
                break
            else:
                self.testcase.log.info("Sleeping for 2 minutes")
                time.sleep(120)
                counter += 1
            if counter > 10:
                raise Exception(
                    "Snapshot of jobid: {0} is not yet deleted,"
                    "please check the CVMA logs for any of the job".vmjob_ids
                )
        return (self.vsa_snapconstants.auto_subclient, backup_options,
                self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)

    def skipped_vm_validation(self, jobid, logfile_name, str_list, client_machine):
        """Skipped VM Validation using logs
            Args:
                jobid           (int)       jobid in which snap config needs to validate
                logfile_name    (str)       log file name in which config needs to validate
                str_list        (list)      String list to search
                client_machine  (obj)       client machine object
        """
        log_output = []
        for string in str_list:
            log_line = client_machine.get_logs_for_job_from_file(jobid, logfile_name, string)
            log_output.append(log_line)
        for output in log_output:
            if output is not None:
                self.testcase.log.info("log lines found are : \n%s", output)
            else:
                raise Exception("*" * 5 + " skipped VM is *NOT* honored during VSA Snap Operation" + "*" * 5)
        self.testcase.log.info("*" * 5 + " Skipped VM is honored during VSA Snap Operation" + "*" * 5)

    def vsasnap_parallel_bkpcpy(self):
        """ Template to Test VSA-Allow Parallel Backup copy to process VM's independently """
        self.testcase.log.info("Started executing %s testcase", self.testcase.id)
        # Running Snap backup.
        if self.vsa_snapconstants.arrayname:
            self.vsa_snaphelper.add_primary_array()
        VirtualServerUtils.decorative_log("Backup")
        backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
        backup_options.backup_method = "SNAP"
        if backup_options.collect_metadata:
            raise Exception("Metadata collection is enabled")
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        backup_jobid = self.vsa_snapconstants.auto_subclient.backup_job.job_id
        child_jobid = self.vsa_snapconstants.auto_subclient.get_childjob_foreachvm(backup_jobid)
        joblist = []
        for keys in child_jobid:
            joblist.append(child_jobid[keys])
        vmjob_ids = tuple(joblist)
        copyid = self.vsa_snaphelper.spcopy_obj(1).copy_id
        # collecting smvolume and snap list after snap backup
        smsnap_prebk = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_snap_id, {'a': backup_jobid})
        # Unpick job for one of the VM and start backup copy operation.
        VirtualServerUtils.decorative_log("Running offline backup copy by unpicking job for VM")
        primary_copy = self.vsa_snaphelper.storage_policy_obj.get_primary_copy()
        primary_copy.do_not_copy_jobs(joblist[0])
        # Run offline backup copy
        backup_copy_jobid = self.vsa_snaphelper.run_backup_copy()
        #Run another Snap backup
        VirtualServerUtils.decorative_log(" Running Next Snap Backup")
        backup_options.backup_method = "SNAP"
        backup_options.backup_type = "INCREMENTAL"
        if self.testcase.tcinputs.get('skip_pre_backup_config'):
            backup_options.run_pre_backup_config_checks = False
        self.vsa_snapconstants.auto_subclient.backup(backup_options)
        # Re-pick the skipped job and verify snaps are aged successfully after backup copy.
        primary_copy.pick_jobs_for_backupcopy(list(child_jobid.values())[0])
        self.vsa_snaphelper.run_backup_copy()
        # Validate that previously successful backup copied VM's are skipped
        str1 = f"{backup_copy_jobid} VSBkpCoordinator::UpdateJobManagerVMList_Restart() - VM - [Skipped] "
        str2 = f"{backup_copy_jobid} is skipped for backup copy as a backup copy job is already running"
        list_str = [str1,str2]
        client_machine = self.testcase.tcinputs["browse_ma"]
        self.skipped_vm_validation(backup_copy_jobid,"vsbkp.log", list_str, client_machine)
        time.sleep(120)  # waiting until snapshot is marked prune and age
        smvolid_list = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_volumelist_id, {'a': vmjob_ids, 'b': copyid})
        smsnap_list = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_snap_id, {'a': backup_jobid})
        return (self.vsa_snapconstants.auto_subclient, backup_options,
                self.testcase.test_individual_status,
                self.testcase.test_individual_failure_message)







