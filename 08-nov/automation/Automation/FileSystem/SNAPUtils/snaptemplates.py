# -*-  coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Template file for performing IntelliSnap operations

SNAPTemplate is the only class defined in this file

SNAPTemplate: Template class to perform IntelliSnap operations

SNAPTemplate:

    __init__()                   --  initializes Snap constant object

    Snap_Template1()             --  Template to Perform Snap backup and Restore opertaions
    Steps:
        1. Add hardware Array details to array management and update the snapconfig details.
        2. Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, backupset, subclient, snap and aux copy and enable intellisnap
           on subclient.
        3. add test data folder in the subclient content.
        4. start a Full snap backup job and kill it after snap phase completes to verify snap aging
        5. Raun DA.
        6. Run Full Snapbackup job with catalog, Vplex validations for vplex engines.
        7. Outplace restore from snap backup and validation.
        8. Modify data on the source, and Run Incremental snap job with catalog.
        9. Inplace restore from snap backup and validation.
        10. Mount snap and validate.
        11. Unmount snap and validate.
        12. Run backup copy.
        13. Outplace restore from backup copy and validation.
        14. Second Full Snap backup with catalog and inline backup copy.
        15. Delete source data and Run Incremental snap backup with catalog and inline backup copy.
        16. Outplace restore from snap backup using 'show deleted items' enabled for each path
            and Validation.
        17. Outplace restore of entire path from snap backup and validation.
        18. Run Aux copy and Outplace restore from aux copy with validation.
        19. Revert Snap for supported Engines and validation.
        20. Delete Snap and validations.
        21. Aging validation on snap copy.
        22. Cleanup entites which is been created in step 2.
        23. Delete Hardware array from array management.


    snap_template2()             --  Template to Perform Intellisnap Replication operations
    Steps:
        1. Add source and target hardware Array and OCUM details in case of NetApp to array
           management and update the snapconfig details on source and target.
        2. Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, backupset, subclient, snap, aux copy and replica/ vault/mirror copies
           and enable intellisnap on subclient.
        3. add test data folder in the subclient content.
        4. Run Full Snapbackup job with skip catalog.
        5. Outplace restore from snap backup and validation.
        6. Run Incremental Snapbackup job with skip catalog.
        7. Run Aux Copy.
        8. Mount Snap and its Validation from FIRST node copy and validation.
        9. UnMount Snap and its Validation from FIRST node copy and validation.
        10. Mount Snap and its Validation from SECOND node copy in 3 node configurations
            and validation.
        11. UnMount Snap and its Validation from SECOND node copy in 3 node configurations
            and validation.
        12. Revert snap from primary Snap and validation for supported engines.
        13. OutPlace Restore from FIRST node Snap backup and validations.
        14. InPlace Restore from FIRST node Snap Backup and validations.
        15. Enable backup copy and snapshot cataloging on the storage policy.
        16. Run Snapshot Cataloging.
        17. OutPlace Restore from First node Snap backup after Catalog and validation.
        18. Run SECOND FULL and SECOND INCREMENTAL Snap Backup job.
        19. Run Aux Copy.
        20. Outplace restore from second node copy and validation.
        21. Run THIRD FULL and THIRD INCREMENTAL Snap Backup job in 3 node configs.
        22. Run aux copy.
        23. Run Backup copy from Storage Policy.
        24. Run OutPlace Restore from Backup Copy and validations.
        25. Run Snapshot Cataloging and aux copy from Storage Policy.
        26. Delete snap from Primary/ first node / second node copies and validations.
        27. Force delete snap in case of open replication as it will fail with snapmirror
            dependency.
        28. data aging validations on primary/ first/ second node copies.
        29. cleanup of entities created in step2.
        30. delete arrays and ocum details from the array management.


    snap_template3()             --  Template to Perform Intellisnap Replication operations for
                                     Netapp FANOUT and All Copies Configuration
    Steps:
        1. Add source and target hardware Array and OCUM details in case of NetApp to array
           management and update the snapconfig details on source and target.
        2. Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, backupset, subclient, snap, aux copy and replica/ vault/mirror copies
           and enable intellisnap on subclient.
        3. add test data folder in the subclient content.
        4. Run Full Snapbackup job with skip catalog.
        5. Run Incremental Snapbackup job with skip catalog.
        6. Run Aux copy.
        7. Restore from each fanout secondary snap copies and validate.
        8. enable backup copy and snapshot catalog on the storage policy.
        9. Run backup copy on storage policy.
        10. Run OutPlace Restore from Backup Copy and validations.
        11. Run SECOND full and SECOND incremental snap backup with skip catalog.
        12. Run Aux copy.
        13. Run Snapshot catalog.
        14. Run Inplace restore from First node copy after snapshot catalog and validation.
        15. Run Backup copy.
        16. delete snapshots from each copy and validate.
        17. Force delete snaps in case of Open Replication as it will fail with snapmirror
            dependency.
        18. data aging validations on Primary snap and all the secondary snap fanout copies.
        19. cleanup of entities created in step2.
        20. delete arrays and ocum details from the array management.


    snap_template4()             --  Snap Template4 to Perform New Copy Creation Wizard and Snap
                                     Operations using Tape, NAS attached, Mag libraries.
                                     Deduplication and Non-deduplication pools. with and with out
                                     On Command System Manager etc
    Steps:
        1. Create Storage policy using above said libraries.
        2. Create Snap Copy if OCUM Server is not provided else not.
        3. Create Vault/Replica Copy if OCUM Server is not provided else Create Vault copy using
           Resource Pool and Provisioning Policy.
        4. Enable Backup copy option if OCUM Server is provided else not.
        5. Create Backupset, Subclient and Enable Intellisnap on Subclient.
           Add data to the subclient content.
        6. Run Full Snap Backup Followed by Aux Copy and Backup Copy.
        7. Browse and Restore from Snap followed by from Backup Copy and Aux Copy.
        8. Delete backupset, Storage Policy.

    snap_template5()             -- Snap Template5 to Perform verification of Snap
                                    ActiveActive/Metro configuurations
    Steps:
        1. Add source and target hardware Array
        2. Enable snap config to support Active Active snap creation
        3. Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, backupset, subclient, snap, aux copy and replica/ vault/mirror copies
           and enable intellisnap on subclient.
        4. add test data folder in the subclient content.
        5. Run Full Snapbackup job with skip catalog.
        6. Verify Snaps are created on both nodes of the Metro Cluster
        7. Outplace restore from snap backup and validation.
        8. Mount Snap and its Validation from FIRST node copy and validate
           if snap is mounted frmom Primary Array
        9. UnMount Snap and its Validation from FIRST node copy and validation.
        10. Run Backup Copy
        11. Change Array Access node to secondary Array
        12. Run incremental Snap and verify if snap created on both nodes of Metro Cluster
        13. Run Restore and validate data
        14. Mount snap and validate Snap is mounted from Secondary Array
        15. Validate Unmount
        16. Run Backup copy
        17. Disable Active Active Snap creation using Snap config
        18. Run Full Snap and Verify snap is created only on Primary Array
        19. Run Backup copy
        20.Cleanup
"""

import time
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from AutomationUtils import logger
from FileSystem.SNAPUtils.snapconstants import SnapConfig_level
importError = False
try:
    from FileSystem.SNAPUtils.snaparrayhelper import SNAPverify
except ImportError:
    importError = True


class SNAPTemplate(object):
    """Helper class to perform snap operations"""

    def __init__(self, commcell, client, agent, tcinputs, snapconstants):
        """Initializes Snaphelper object and gets the commserv database object if not specified

            Args:
                commcell        (object)    --  commcell object

                client          (object)    --  client object

                agent           (object)    --  agent object

                tcinputs        (dict)      --  Test case inputs dictionary

                snapconstants   (object)    --  snapconstants object

        """

        self.snaphelper = SNAPHelper(commcell, client, agent, tcinputs, snapconstants)
        self.commcell = commcell
        self.client = client
        self.agent = agent
        self.snapconstants = snapconstants
        self.tcinputs = tcinputs
        self.log = logger.get_log()
        self.multisite = None
        if not importError:
            self.snapverify = SNAPverify(commcell, client, agent, tcinputs, self.snapconstants)
        else:
            self.log.info("Skipping Verification due to import error. Please check library imports in snaparrayhelper "
                          "file")

    def snap_template1(self):
        """ Snap Template1 to Perform Snap backup and Restore opertaions
        """
        self.snaphelper.pre_cleanup()
        if not self.snapconstants.multisite:
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            if self.snapconstants.snap_engine_at_array in ["Dell EMC VNX / CLARiiON", "Fujitsu ETERNUS AF / DX"]:
                self.snapconstants.config_update_level = "subclient"
            if self.snapconstants.config_update_level == "array":
                if self.snapconstants.source_config is not None:
                    self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=self.snapconstants.array_access_nodes_to_edit)

            if self.snapconstants.vplex_engine is True:
                """ Adding First Backeend arrays """
                self.log.info("*" * 20 + "Adding backend array for Snap Engine: {0}".format(
                    self.tcinputs['BackendSnapEngineAtArray']))
                self.snapconstants.arrayname = self.tcinputs['BackendArrayName1']
                self.snapconstants.username = self.tcinputs['BackendArrayUserName1']
                self.snapconstants.password = self.tcinputs.get('BackendArrayPassword1')
                self.snapconstants.controlhost = self.tcinputs.get('BackendArrayControlHost1', None)
                self.snapconstants.snap_engine_at_array = self.tcinputs['BackendSnapEngineAtArray']
                self.snaphelper.add_array()

                """ Adding Second Backend array """
                self.log.info("*" * 20 + "Adding Second backend array for Snap Engine: {0}".format(
                    self.tcinputs['BackendSnapEngineAtArray']))
                self.snapconstants.arrayname = self.tcinputs['BackendArrayName2']
                self.snapconstants.username = self.tcinputs['BackendArrayUserName2']
                self.snapconstants.password = self.tcinputs.get('BackendArrayPassword2')
                self.snapconstants.controlhost = self.tcinputs.get('BackendControlHost2', None)
                self.snaphelper.add_array()

            """ Re-Set arrayname and engine Name as primary """
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snapconstants.snap_engine_at_array = self.tcinputs['SnapEngineAtArray']
        self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
        self.snaphelper.setup()
        self.snaphelper.add_test_data_folder()
        if self.snapconstants.config_update_level == "subclient":
            if self.snapconstants.source_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           int(self.snapconstants.subclient.subclient_id),
                                           array_access_node=self.snapconstants.array_access_nodes_to_edit)
        self.log.info("*" * 20 + "Kill Job Verification" + "*" * 20)
        self.snaphelper.kill_job()
        self.log.info("*" * 20 + "Kill Job Verification Completed" + "*" * 20)
        snapshot_engine_id = self.snapconstants.execute_query(
            self.snapconstants.get_snapengine_id,
            {'a': self.snapconstants.snap_engine_at_subclient}, fetch_rows='one')
        if snapshot_engine_id in ['2', '16', '33', '50']:
            spcopy = self.snaphelper.spcopy_obj(self.snapconstants.snap_copy_name)
            spcopy.copy_retention = (0, 1, 0)
            self.snaphelper.run_data_aging(self.snapconstants.snap_copy_name)
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
        full1_job = self.snaphelper.snap_backup()
        vendor = self.snapconstants.snap_engine_at_array
        if not importError:
            self.snapverify.verify_snap_creation(vendor, full1_job.job_id, self.snapconstants.snap_copy_name)
        if self.snapconstants.vplex_engine is True:
            self.snaphelper.vplex_snap_validation(
                full1_job.job_id, self.snapconstants.snap_copy_name)
        self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
        self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
        self.snaphelper.snap_outplace(1)
        self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                            self.snaphelper.client_machine)
        self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        if self.snapconstants.problematic_data:
            self.snaphelper.update_test_data(mode='edit', path=[self.snapconstants.test_data_folder[0]+self.snapconstants.delimiter+"dir1"])
        else:
            self.snaphelper.update_test_data(mode='edit', path=self.snapconstants.test_data_folder)
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc1_job = self.snaphelper.snap_backup()
        if not importError:
            self.snapverify.verify_snap_creation(vendor, inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.log.info("*" * 20 + "Running InPlace Restore from Snap Backup job" + "*" * 20)
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.snap_inplace(1)
        self.snaphelper.inplace_validation(inc1_job.job_id,
                                           self.snapconstants.snap_copy_name,
                                           self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Mount Snap and its Validation" + "*" * 20)
        self.snaphelper.mount_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.mount_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "UnMount Snap and its Validation" + "*" * 20)
        self.snaphelper.unmount_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.unmount_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()
        self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.snaphelper.tape_outplace(inc1_job.job_id, 2, inc1_job.start_time, inc1_job.end_time)
        self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                            self.snapconstants.windows_restore_client)
        self.log.info("*" * 20 + "Running Second FULL Inline Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'FULL'
        self.snapconstants.inline_bkp_cpy = True
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        full2_job = self.snaphelper.snap_backup()
        if not importError:
            self.snapverify.verify_snap_creation(vendor, full2_job.job_id, self.snapconstants.snap_copy_name)
        if snapshot_engine_id in ['2', '16', '33', '50']:
            self.log.info("Snap Engine: {0} supports only 3 snaps. "
                          "Need to age the previous cycle".format(
                              self.snapconstants.snap_engine_at_subclient))
            self.snaphelper.run_data_aging(self.snapconstants.snap_copy_name)
        else:
            self.log.info("Snap Engine: {0} Supports more than 3 snaps. "
                          "No Need to age the previous cycle".format(
                              self.snapconstants.snap_engine_at_subclient))
        self.log.info("*" * 20 + "Running Second INCREMENTAL Inline Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.update_test_data(mode='delete', path=self.snapconstants.test_data_path)
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc2_job = self.snaphelper.snap_backup()
        if not importError:
            self.snapverify.verify_snap_creation(vendor, inc2_job.job_id, self.snapconstants.snap_copy_name)
        i = 0
        for path in self.snapconstants.test_data_path:
            self.snapconstants.source_path = [path]
            if self.snapconstants.skip_catalog:
                self.log.info("*" * 20 + "Running OutPlace Restore from backup copy with "
                        "Source Path: {0}".format(path) + "*" * 20)
                self.snaphelper.tape_outplace(inc2_job.job_id, 2, fs_options=True)
                self.snaphelper.compare(self.snaphelper.client_machine,
                                        self.snapconstants.windows_restore_client,
                                        self.snapconstants.copy_content_location[i],
                                        self.snapconstants.tape_outplace_restore_location)
            else:
                self.log.info("*" * 20 + "Running OutPlace Restore from SnapBackup with "
                                        "Source Path: {0}".format(path) + "*" * 20)
                self.snaphelper.snap_outplace(1, fs_options=True)
                self.snaphelper.compare(self.snaphelper.client_machine,
                                        self.snaphelper.client_machine,
                                        self.snapconstants.copy_content_location[i],
                                        self.snapconstants.snap_outplace_restore_location)
            i = i + 1
        self.log.info("*" * 20 + "Restore of deleted data and Validation is "
                      "Successful " + "*" * 20)
        self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.snaphelper.snap_outplace(1, full2_job.start_time, full2_job.end_time)
        self.snaphelper.inplace_validation(full2_job.job_id,
                                           self.snapconstants.snap_copy_name,
                                           self.snapconstants.snap_outplace_restore_location)
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        self.snaphelper.aux_copy()
        self.log.info("*" * 20 + "Running OutPlace Restore from Aux Copy job" + "*" * 20)
        self.snaphelper.tape_outplace(inc2_job.job_id, 3, inc2_job.start_time, inc2_job.end_time)
        self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                            self.snapconstants.windows_restore_client)
        if self.snapconstants.revert_support is True:
            self.log.info("************* REVERT IS NOT SUPPORTED FOR ENGINE: {0}, "
                                                  "skipping this operation *********".format(
                                                      self.snapconstants.snap_engine_at_subclient))
        else:
            self.log.info("*" * 20 + "Revert Snap and its Validation" + "*" * 20)
            self.snaphelper.revert_snap(full2_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.revert_validation(full2_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Delete Snap and its Validation" + "*" * 20)
        if not importError:
            self.snapverify.run_and_verify_snap_deletion(vendor, inc2_job.job_id, self.snapconstants.snap_copy_name)
        else:
            self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.delete_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)
        if not importError:
            self.snapverify.run_and_verify_reconcile(vendor, full2_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Data Aging Validation on Snap copy" + "*" * 20)
        self.snaphelper.data_aging_validation(self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
        self.snaphelper.cleanup()
        self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
        self.snaphelper.delete_array()
        if self.snapconstants.vplex_engine is True:
            """ Deleting Vplex arrays"""
            self.snapconstants.arrayname = self.tcinputs['BackendArrayName1']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['BackendArrayName2']
            self.snaphelper.delete_array()
        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

    def snap_template2(self, v1_indexing=False):
        """Snap Template2 to Perform Snapshot Replication Operations
        """
        self.snaphelper.pre_cleanup()
        self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pv_replica", "pm_replica", "fanout"}:
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
            if self.snapconstants.snap_engine_at_array == "Fujitsu ETERNUS AF / DX":
                self.snapconstants.config_update_level = "subclient"
            if self.snapconstants.source_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=self.snapconstants.array_access_nodes_to_edit)

            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)
            if self.snapconstants.snap_engine_at_array == "Fujitsu ETERNUS AF / DX":
                self.snapconstants.config_update_level = "subclient"
            if self.snapconstants.target_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.target_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=self.snapconstants.array_access_nodes_to_edit)
        else:
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName3']
            self.snapconstants.username = self.tcinputs['ArrayUserName3']
            self.snapconstants.password = self.tcinputs.get('ArrayPassword3')
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Third Array" + "*" * 20)

        if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
            self.log.info("*" * 20 + "ADDING OCUM" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['OCUMServerName']
            self.snapconstants.username = self.tcinputs['OCUMUserName']
            self.snapconstants.password = self.tcinputs.get('OCUMPassword')
            self.snapconstants.is_ocum = True
            self.snaphelper.add_array()
            self.log.info("Successfully Added OCUM Information")
        self.snapconstants.arrayname = self.tcinputs['ArrayName']
        self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
        self.snaphelper.setup()
        self.snaphelper.add_test_data_folder()
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running FIRST FULL Snap Backup job" + "*" * 20)
        self.snapconstants.skip_catalog = True
        full1_job = self.snaphelper.snap_backup()
        self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
        self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
        self.snaphelper.snap_outplace(1)
        self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                            self.snaphelper.client_machine)
        self.log.info("*" * 20 + "Running FIRST INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
            self.snaphelper.aux_copy()
        else:
            self.snaphelper.aux_copy(use_scale=True)
        self.log.info("*" * 20 + "Mount Snap and its Validation from FIRST node" + "*" * 20)
        self.snaphelper.mount_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
        self.snaphelper.mount_validation(inc1_job.job_id, self.snapconstants.first_node_copy)
        self.log.info("*" * 20 + "UnMount Snap and its Validation from FIRST node" + "*" * 20)
        self.snaphelper.unmount_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
        self.snaphelper.unmount_validation(inc1_job.job_id, self.snapconstants.first_node_copy)
        if self.snapconstants.type not in {"pv", "pv_replica", "pm", "pm_replica"}:
            self.log.info("*" * 20 + "Mount Snap and its Validation from SECOND node" + "*" * 20)
            self.snaphelper.mount_snap(full1_job.job_id, self.snapconstants.second_node_copy)
            self.snaphelper.mount_validation(full1_job.job_id, self.snapconstants.second_node_copy)
            self.log.info("*" * 20 + "UnMount Snap and its Validation from SECOND node" + "*" * 20)
            self.snaphelper.unmount_snap(full1_job.job_id, self.snapconstants.second_node_copy)
            self.snaphelper.unmount_validation(full1_job.job_id,
                                               self.snapconstants.second_node_copy)
        if self.snapconstants.revert_support is True:
            self.log.info("************* REVERT IS NOT SUPPORTED FOR ENGINE: {0}, "
                                                  "skipping this operation *********".format(
                                                      self.snapconstants.snap_engine_at_subclient))
        else:
            self.log.info("*" * 20 + "Revert Snap and its Validation" + "*" * 20)
            self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
            self.snaphelper.revert_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.revert_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Running OutPlace Restore from FIRST node Snap backup" + "*" * 20)
        self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
        self.snaphelper.snap_outplace(4, full1_job.start_time, inc1_job.end_time)
        self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                            self.snaphelper.client_machine)
        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.log.info("*" * 20 + "Running InPlace Restore from FIRST node Snap Backup" + "*" * 20)
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.snap_inplace(4, inc1_job.start_time, inc1_job.end_time)
        self.snaphelper.inplace_validation(inc1_job.job_id, self.snapconstants.first_node_copy,
                                           self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Storage Policy Update" + "*" * 20)
        if self.snapconstants.type in {"pv", "pv_replica", "pm", "pm_replica"}:
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.first_node_copy,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.first_node_copy)
        else:
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.second_node_copy,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.first_node_copy)
        if not v1_indexing:
            self.log.info("*" * 20 + "Running Snapshot Cataloging from Storage Policy" + "*" * 20)
            self.snaphelper.snapshot_cataloging()
            self.log.info("*" * 20 + "Running OutPlace Restore from First node Snap backup after "
                          "Catalog" + "*" * 20)
            self.snaphelper.snap_outplace(4)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)

        if self.snapconstants.type not in {"pv", "pv_replica", "pm", "pm_replica"}:
            self.log.info("*" * 20 + "Running SECOND FULL Snap Backup job" + "*" * 20)
            self.snapconstants.backup_level = 'FULL'
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            full2_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Running SECOND INCREMENTAL Snap Backup job" + "*" * 20)
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            inc2_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
            if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
                self.snaphelper.aux_copy()
            else:
                self.snaphelper.aux_copy(use_scale=True)
            self.log.info("*" * 20 + "Running OutPlace Restore from SECOND node Snap" + "*" * 20)
            self.snaphelper.snap_outplace(5)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)
        if self.snapconstants.type not in {"pv", "pv_replica", "pm", "pm_replica"}:
            self.log.info("*" * 20 + "Running THIRD FULL Snap Backup job" + "*" * 20)
        else:
            self.log.info("*" * 20 + "Running SECOND FULL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'FULL'
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        full3_job = self.snaphelper.snap_backup()
        if self.snapconstants.type not in {"pv", "pv_replica", "pm", "pm_replica"}:
            self.log.info("*" * 20 + "Running THIRD INCREMENTAL Snap Backup job" + "*" * 20)
        else:
            snapshot_engine_id = self.snapconstants.execute_query(
                self.snapconstants.get_snapengine_id,
                {'a': self.snapconstants.snap_engine_at_subclient}, fetch_rows='one')
            if snapshot_engine_id in ['2', '16', '33', '50']:
                self.log.info("Snap Engine: {0} supports only 3 snaps. "
                              "Need to age the previous cycle".format(
                                  self.snapconstants.snap_engine_at_subclient))
                self.snaphelper.aux_copy(use_scale=True)
                self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
                self.snaphelper.backup_copy()
                spcopy = self.snaphelper.spcopy_obj(self.snapconstants.snap_copy_name)
                spcopy.copy_retention = (0, 1, 0)
                self.snaphelper.run_data_aging(self.snapconstants.snap_copy_name)
                spcopy = self.snaphelper.spcopy_obj(self.snapconstants.first_node_copy)
                spcopy.copy_retention = (0, 1, 0)
                self.snaphelper.run_data_aging(self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Running SECOND INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc3_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
            self.snaphelper.aux_copy()
        else:
            self.snaphelper.aux_copy(use_scale=True)
        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()
        self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
        self.snaphelper.tape_outplace(full3_job.job_id, 2)
        self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                            self.snapconstants.windows_restore_client)
        if not v1_indexing:
            self.log.info("*" * 20 + "Running Snapshot Cataloging from Storage Policy" + "*" * 20)
            self.snaphelper.snapshot_cataloging()
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
            self.snaphelper.aux_copy()
        else:
            self.snaphelper.aux_copy(use_scale=True)

        self.log.info("*" * 20 + "DELETE VALIDATIONS" + "*" * 20)
        self.log.info("Verifying delete operation on Primary Snap Copy")
        self.snaphelper.delete_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.delete_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)

        if self.snapconstants.type in {"pv", "pmv", "pv_replica", "pmv_replica", "pvv_replica"}:
            if self.snapconstants.type in {"pv", "pv_replica"}:
                self.log.info("Verifying delete operation on First Node Copy")
                self.snaphelper.delete_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
                self.snaphelper.delete_validation(
                    inc1_job.job_id, self.snapconstants.first_node_copy)
            elif self.snapconstants.type in {"pmv", "pmv_replica"}:
                self.log.info("Verifying delete operation on First Node Copy")
                self.snaphelper.delete_snap(
                    full1_job.job_id,
                    self.snapconstants.first_node_copy,
                    is_mirror=True,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name)
                self.snaphelper.delete_validation(full1_job.job_id,
                                                  self.snapconstants.first_node_copy)
                self.log.info("Verifying delete operation on Second Node Copy")
                self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.second_node_copy)
                self.snaphelper.delete_validation(inc2_job.job_id,
                                                  self.snapconstants.second_node_copy)
            else:
                self.log.info("Verifying delete operation on First Node Copy")
                self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.first_node_copy)
                self.snaphelper.delete_validation(inc2_job.job_id,
                                                  self.snapconstants.first_node_copy)
                self.log.info("Verifying delete operation on Second Node Copy")
                self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.second_node_copy)
                self.snaphelper.delete_validation(inc2_job.job_id,
                                                  self.snapconstants.second_node_copy)
        else:
            if self.snapconstants.type in {"pm", "pm_replica"}:
                self.log.info("Verifying delete operation on First Node Copy")
                self.snaphelper.delete_snap(
                    full1_job.job_id, self.snapconstants.first_node_copy,
                    is_mirror=True,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name)
                self.snaphelper.delete_validation(full1_job.job_id,
                                                  self.snapconstants.first_node_copy)
            elif self.snapconstants.type in {"pvm", "pvm_replica"}:
                self.log.info("Verifying delete operation on First Node Copy")
                self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.first_node_copy)
                self.snaphelper.delete_validation(inc2_job.job_id,
                                                  self.snapconstants.first_node_copy)
                self.log.info("Verifying delete operation on Second Node Copy")
                self.snaphelper.delete_snap(
                    full2_job.job_id,
                    self.snapconstants.second_node_copy,
                    is_mirror=True,
                    source_copy_for_mirror=self.snapconstants.first_node_copy)
                self.snaphelper.delete_validation(full2_job.job_id,
                                                  self.snapconstants.second_node_copy)
            else:
                self.log.info("Verifying delete operation on First Node Copy")
                self.snaphelper.delete_snap(
                    full1_job.job_id,
                    self.snapconstants.first_node_copy,
                    is_mirror=True,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name)
                self.snaphelper.delete_validation(full1_job.job_id,
                                                  self.snapconstants.first_node_copy)
                self.log.info("Verifying delete operation on Second Node Copy")
                self.snaphelper.delete_snap(
                    full2_job.job_id,
                    self.snapconstants.second_node_copy,
                    is_mirror=True,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name)
                self.snaphelper.delete_validation(full2_job.job_id,
                                                  self.snapconstants.second_node_copy)
        self.log.info("*" * 20 + "DELETE VALIDATIONS COMPLETED" + "*" * 20)

        self.log.info("*" * 20 + "FORCE DELETE SNAPSHOTS FROM PRIMARY" + "*" * 20)
        if self.snapconstants.type in {"pv", "pv_replica", "pm", "pm_replica"} and self.snapconstants.snap_engine_at_subclient == "NetApp":
            self.log.info("force deleting the latest snapshot of jobid :{0} from primary snap "
                          "copy which may fail with snapmirror dependency error".format(
                              inc3_job.job_id))
            self.snaphelper.force_delete_snap(inc3_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(inc3_job.job_id, self.snapconstants.snap_copy_name)
        elif self.snapconstants.type not in {"pv", "pv_replica", "pm", "pm_replica"} and self.snapconstants.snap_engine_at_subclient == "NetApp":
            self.log.info("force deleting the latest snapshot of jobid :{0} from primary snap "
                          "copy which may fail with snapmirror dependency error".format(
                              inc3_job.job_id))
            self.snaphelper.force_delete_snap(inc3_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(inc3_job.job_id, self.snapconstants.snap_copy_name)
            self.log.info("force deleting the latest snapshot of jobid :{0} from primary snap "
                          "copy which may fail with snapmirror dependency error".format(
                              inc2_job.job_id))
            self.snaphelper.force_delete_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)
        else:
            self.log.info("This is non-NetApp array, not force deleting snaps")

        self.log.info("Disabling backup copy and snapshot catalogue")
        self.snaphelper.update_storage_policy()

        self.log.info("*" * 20 + "DATA AGING VALIDATIONS" + "*" * 20)
        self.snaphelper.data_aging_validation(self.snapconstants.snap_copy_name)
        if self.snapconstants.type in {"pv", "pmv", "pv_replica", "pmv_replica", "pvv_replica"}:
            if self.snapconstants.type in {"pv", "pv_replica"}:
                self.log.info("Verifying Aging on First Node Copy: {0}".format(
                    self.snapconstants.first_node_copy))
                self.snaphelper.data_aging_validation(
                    self.snapconstants.first_node_copy, vault=True)
            elif self.snapconstants.type in {"pmv", "pmv_replica"}:
                self.log.info("Verifying Aging on First Node Copy: {0}".format(
                    self.snapconstants.first_node_copy))
                self.snaphelper.data_aging_validation(
                    self.snapconstants.first_node_copy,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name,
                    mirror=True)
                self.log.info("Verifying Aging on Second Node Copy: {0}".format(
                    self.snapconstants.second_node_copy))
                self.snaphelper.data_aging_validation(self.snapconstants.second_node_copy,
                                                      vault=True)
            else:
                self.log.info("Verifying Aging on First Node Copy: {0}".format(
                    self.snapconstants.first_node_copy))
                self.snaphelper.data_aging_validation(self.snapconstants.first_node_copy,
                                                      vault=True)
                self.log.info("Verifying Aging on Second Node Copy: {0}".format(
                    self.snapconstants.second_node_copy))
                self.snaphelper.data_aging_validation(self.snapconstants.second_node_copy,
                                                      vault=True)
        else:
            if self.snapconstants.type in {"pm", "pm_replica"}:
                self.log.info("Verifying Aging on First Node Copy: {0}".format(
                    self.snapconstants.first_node_copy))
                self.snaphelper.data_aging_validation(
                    self.snapconstants.first_node_copy,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name,
                    mirror=True)
            elif self.snapconstants.type in {"pvm", "pvm_replica"}:
                self.log.info("Verifying Aging on First Node Copy: {0}".format(
                    self.snapconstants.first_node_copy))
                self.snaphelper.data_aging_validation(self.snapconstants.first_node_copy,
                                                      vault=True)
                self.log.info("Verifying Aging on Second Node Copy: {0}".format(
                    self.snapconstants.second_node_copy))
                self.snaphelper.data_aging_validation(
                    self.snapconstants.second_node_copy,
                    source_copy_for_mirror=self.snapconstants.first_node_copy,
                    mirror=True)
            else:
                self.log.info("Verifying Aging on First Node Copy: {0}".format(
                    self.snapconstants.first_node_copy))
                self.snaphelper.data_aging_validation(
                    self.snapconstants.first_node_copy,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name,
                    mirror=True)
                self.log.info("Verifying Aging on Second Node Copy: {0}".format(
                    self.snapconstants.second_node_copy))
                self.snaphelper.data_aging_validation(
                    self.snapconstants.second_node_copy,
                    source_copy_for_mirror=self.snapconstants.snap_copy_name,
                    mirror=True)
        self.log.info("*" * 20 + "DATA AGING VALIDATIONS COMPLETED" + "*" * 20)

        self.log.info("*" * 20 + "FORCE DELETE SNAPSHOTS FROM SECONDARY" + "*" * 20)
        if self.snapconstants.type in {"pv", "pv_replica", "pvm", "pvm_replica"} and self.snapconstants.snap_engine_at_subclient == "NetApp":
            self.log.info("force deleting the latest snapshot of jobid :{0} from First node Vault "
                          "copy which may fail with snapmirror dependency error".format(
                              inc3_job.job_id))
            self.snaphelper.force_delete_snap(inc3_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(inc3_job.job_id, self.snapconstants.first_node_copy)
        elif self.snapconstants.type in {"pmv", "pmv_replica"} and self.snapconstants.snap_engine_at_subclient == "NetApp":
            self.log.info("force deleting the latest snapshot of jobid :{0} from second node "
                          "Vault copy which may fail with snapmirror dependency error".format(
                              inc3_job.job_id))
            self.snaphelper.force_delete_snap(inc3_job.job_id, self.snapconstants.second_node_copy)
            self.snaphelper.delete_validation(inc3_job.job_id, self.snapconstants.second_node_copy)
        elif self.snapconstants.type == "pvv_replica" and self.snapconstants.snap_engine_at_subclient == "NetApp":
            self.log.info("force deleting the latest snapshot of jobid :{0} from First node Vault "
                          "copy which may fail with snapmirror dependency error".format(
                              inc3_job.job_id))
            self.snaphelper.force_delete_snap(inc3_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(inc3_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("force deleting the latest snapshot of jobid :{0} from second node "
                          "Vault copy which may fail with snapmirror dependency error".format(
                              inc3_job.job_id))
            self.snaphelper.force_delete_snap(inc3_job.job_id, self.snapconstants.second_node_copy)
            self.snaphelper.delete_validation(inc3_job.job_id, self.snapconstants.second_node_copy)
        else:
            self.log.info("Not Force deleting snapshot of PM,PM_replica,PMM,PMM_replica "
                          "since it is already deleted OR its a non-NetApp array")

        self.log.info("*" * 20 + "Deleting REST of the snapshots before deleting copies" + "*" * 20)
        if self.snapconstants.snap_engine_at_subclient != "NetApp":
            self.log.info("Verifying delete operation on First Node Copy")
            self.snaphelper.delete_snap(inc3_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(inc3_job.job_id,
                                              self.snapconstants.first_node_copy)
            self.log.info("Verifying delete operation on Primary Snap Copy")
            self.snaphelper.delete_snap(inc3_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(inc3_job.job_id,
                                              self.snapconstants.snap_copy_name)

        if self.snapconstants.type in {"pv", "pv_replica", "pvm", "pvm_replica"}:
            self.log.info("Verifying delete operation on First Node Copy")
            self.snaphelper.delete_snap(full3_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(full3_job.job_id,
                                              self.snapconstants.first_node_copy)
        elif self.snapconstants.type in {"pmv_replica", "pmv"}:
            self.log.info("Verifying delete operation on Second Node Copy")
            self.snaphelper.delete_snap(full3_job.job_id, self.snapconstants.second_node_copy)
            self.snaphelper.delete_validation(full3_job.job_id,
                                              self.snapconstants.second_node_copy)
        elif self.snapconstants.type == "pvv_replica":
            self.log.info("Verifying delete operation on First Node Copy")
            self.snaphelper.delete_snap(full3_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(full3_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("Verifying delete operation on Second Node Copy")
            self.snaphelper.delete_snap(full3_job.job_id, self.snapconstants.second_node_copy)
            self.snaphelper.delete_validation(full3_job.job_id,
                                              self.snapconstants.second_node_copy)

        self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
        self.snaphelper.cleanup()

        self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pv_replica", "pm_replica"}:
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()
        else:
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName3']
            self.snaphelper.delete_array()
        if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
            self.snapconstants.arrayname = self.tcinputs['OCUMServerName']
            self.snaphelper.delete_array()
        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

    def snap_template3(self):
        """Snap Template2 to Perform NetApp Snapshot Replication Operations for FanOut
           Configuration
        """
        self.snaphelper.pre_cleanup()
        self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
        self.snaphelper.add_array()
        self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
        self.snapconstants.arrayname = self.tcinputs['ArrayName2']
        self.snapconstants.username = self.tcinputs['ArrayUserName2']
        self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
        self.snaphelper.add_array()
        self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)
        if self.snapconstants.type == "all":
            self.snapconstants.arrayname = self.tcinputs['ArrayName3']
            self.snapconstants.username = self.tcinputs['ArrayUserName3']
            self.snapconstants.password = self.tcinputs.get('ArrayPassword3')
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Third Array" + "*" * 20)
        if self.snapconstants.ocum_server:
            self.log.info("*" * 20 + "ADDING OCUM" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['OCUMServerName']
            self.snapconstants.username = self.tcinputs['OCUMUserName']
            self.snapconstants.password = self.tcinputs.get('OCUMPassword')
            self.snapconstants.is_ocum = True
            self.snaphelper.add_array()
            self.log.info("Successfully Added OCUM Information")
        self.snapconstants.arrayname = self.tcinputs['ArrayName']
        self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
        self.snaphelper.setup()
        self.snaphelper.add_test_data_folder()
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running FIRST FULL Snap Backup job" + "*" * 20)
        self.snapconstants.skip_catalog = True
        full1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running FIRST INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        if self.snapconstants.ocum_server:
            self.snaphelper.aux_copy()
        else:
            self.snaphelper.aux_copy(use_scale=True)
        self.log.info("*" * 20 + "RESTORING FROM EACH SECONDARY SNAP COPY" + "*" * 20)
        self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
        for copy in self.snapconstants.fanout_copies_vault:
            precedence = self.snapconstants.storage_policy.get_copy_precedence(copy.lower())
            self.snaphelper.snap_outplace(precedence)
            self.snaphelper.outplace_validation(
                self.snapconstants.snap_outplace_restore_location, self.snaphelper.client_machine)
            self.log.info("*" * 20 + "Successfully Completed Restore Validation from copy: {0} "
                          "".format(copy))

        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        for copy in self.snapconstants.fanout_copies_mirror:
            precedence = self.snapconstants.storage_policy.get_copy_precedence(copy.lower())
            self.snaphelper.snap_inplace(precedence, inc1_job.start_time, inc1_job.end_time)
            self.snaphelper.inplace_validation(
                inc1_job.job_id, copy, self.snapconstants.test_data_path)
            self.log.info("*" * 20 + "Successfully Completed Restore Validation from copy: {0} "
                          "".format(copy))
        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED RESTORING FROM EACH SECONDARY SNAP "
                             "COPY" + "*" * 20)
        self.snaphelper.update_storage_policy(
            enable_backup_copy=True,
            source_copy_for_snap_to_tape=self.snapconstants.fanout_copies_vault[0],
            enable_snapshot_catalog=True,
            source_copy_for_snapshot_catalog=self.snapconstants.fanout_copies_mirror[0])
        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()
        self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
        self.snaphelper.tape_outplace(full1_job.job_id, 2)
        self.snaphelper.outplace_validation(
            self.snapconstants.tape_outplace_restore_location,
            self.snapconstants.windows_restore_client)
        self.log.info("*" * 20 + "Running SECOND FULL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'FULL'
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        full2_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running SECOND INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc2_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        if self.snapconstants.ocum_server:
            self.snaphelper.aux_copy()
        else:
            self.snaphelper.aux_copy(use_scale=True)
        self.log.info("*" * 20 + "Running Snapshot Cataloging from Storage Policy" + "*" * 20)
        self.snaphelper.snapshot_cataloging()
        self.log.info("*" * 20 + "Running InPlace Restore from First node Snap backup after "
                      "Catalog" + "*" * 20)
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.snap_inplace(6)
        self.snaphelper.inplace_validation(
            inc2_job.job_id,
            self.snapconstants.fanout_copies_vault[0],
            self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running Backup copy of Remaining jobs" + "*" * 20)
        self.snaphelper.backup_copy()

        self.log.info("*" * 20 + "DELETE VALIDATIONS" + "*" * 20)
        # primary
        self.log.info("Verifying delete operation on Copy: {0}".format(
            self.snapconstants.snap_copy_name))
        self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.delete_validation(full1_job.job_id, self.snapconstants.snap_copy_name)
        # Vault
        self.log.info("Verifying delete validation on Vault copies")
        for copy in self.snapconstants.fanout_copies_vault:
            self.log.info("Verifying delete operation on Copy: {0}".format(copy))
            self.snaphelper.delete_snap(inc1_job.job_id, copy)
            self.snaphelper.delete_validation(inc1_job.job_id, copy)
            self.snaphelper.delete_snap(full1_job.job_id, copy)
            self.snaphelper.delete_validation(full1_job.job_id, copy)
        self.log.info("*" * 20 + "Successfully completed delete validation on Vault copies" + "*" * 20)
        # Mirror
        self.log.info("Verifying delete validation on Mirror copies")
        for copy in self.snapconstants.fanout_copies_mirror:
            self.log.info("Verifying delete validation on Copy: {0}".format(copy))
            self.snaphelper.delete_validation(full1_job.job_id, copy)
        self.log.info("*" * 20 + "Successfully completed delete validation on Mirror copies" + "*" * 20)

        self.log.info("*" * 20 + "FORCE DELETE SNAPSHOTS" + "*" * 20)
        self.log.info("force deleting the latest snapshot of jobid :{0} from primary snap copy "
                      "which may fail with snapmirror dependency error".format(inc2_job.job_id))
        self.snaphelper.force_delete_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.delete_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.force_delete_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.delete_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)

        self.log.info("force deleting the latest snapshot of jobid :{0} from Vault Copies "
                      "which may fail with snapmirror dependency error".format(inc2_job.job_id))
        for copy in self.snapconstants.fanout_copies_vault:
            self.log.info("Force deleting snap of job: {0} on Copy: {1}".format(
                inc2_job.job_id, copy))
            self.snaphelper.force_delete_snap(inc2_job.job_id, copy)
            self.snaphelper.delete_validation(inc2_job.job_id, copy)

        self.log.info("*" * 20 + "DATA AGING VALIDATIONS" + "*" * 20)
        self.snaphelper.data_aging_validation(self.snapconstants.snap_copy_name)

        for copy in self.snapconstants.fanout_copies_vault:
            self.log.info("Verifying Aging on Copy: {0}".format(copy))
            self.snaphelper.data_aging_validation(copy, vault=True)
        self.log.info("*" * 20 + "Completed Aging Validations on All Vault Copies" + "*" * 20)

        if self.snapconstants.type == "fanout":
            for copy in self.snapconstants.fanout_copies_mirror:
                self.log.info("Verifying Aging on Copy: {0}".format(copy))
                self.snaphelper.data_aging_validation(
                    copy, source_copy_for_mirror=self.snapconstants.snap_copy_name, mirror=True)
        elif self.snapconstants.type == "all":
            self.log.info("Verifying Aging on Copy: {0}".format(
                self.snapconstants.fanout_copies_mirror[0]))
            self.snaphelper.data_aging_validation(
                self.snapconstants.fanout_copies_mirror[0],
                source_copy_for_mirror=self.snapconstants.snap_copy_name,
                mirror=True)
            self.log.info("Verifying Aging on Copy: {0}".format(
                self.snapconstants.fanout_copies_mirror[1]))
            self.snaphelper.data_aging_validation(
                self.snapconstants.fanout_copies_mirror[1],
                source_copy_for_mirror=self.snapconstants.fanout_copies_vault[0],
                mirror=True)
            self.log.info("Verifying Aging on Copy: {0}".format(
                self.snapconstants.fanout_copies_mirror[2]))
            self.snaphelper.data_aging_validation(
                self.snapconstants.fanout_copies_mirror[2],
                source_copy_for_mirror=self.snapconstants.snap_copy_name,
                mirror=True)
            self.log.info("Verifying Aging on Copy: {0}".format(
                self.snapconstants.fanout_copies_mirror[3]))
            self.snaphelper.data_aging_validation(
                self.snapconstants.fanout_copies_mirror[3],
                source_copy_for_mirror=self.snapconstants.snap_copy_name,
                mirror=True)

        self.log.info("*" * 20 + "Completed Aging Validations on All Mirror Copies" + "*" * 20)
        self.log.info("*" * 20 + "Deleting REST of the snapshots before deleting SP" + "*" * 20)
        for copy in self.snapconstants.fanout_copies_vault:
            self.log.info("Deleting Rest of the snapshots from Copy: {0}".format(copy))
            self.snaphelper.delete_snap(full2_job.job_id, copy)
            self.snaphelper.delete_validation(full2_job.job_id, copy)
        self.log.info("Successfully Deleting Rest of the snapshots from Vault copies")
        self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
        self.snaphelper.cleanup()

        self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
        self.snaphelper.delete_array()
        self.snapconstants.arrayname = self.tcinputs['ArrayName2']
        self.snaphelper.delete_array()
        self.snapconstants.arrayname = self.tcinputs['ArrayName3']
        self.snaphelper.delete_array()
        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

    def snap_template4(self):
        """Snap Template4 to Perform New Copy Creation Wizard and Snap Operations using Following
        type of libraries and policies.
        Tape, NAS attached, Mag libraries. Deduplication and Non-deduplication pools etc.
        """

        self.snaphelper.create_locations()
        if self.tcinputs.get('tape_lib') is True:
            lib_name = self.tcinputs['Tape_lib_name']
            media_agent = self.tcinputs['MediaAgent']
        elif self.tcinputs.get('nas_attached_lib') is True:
            lib_name = self.tcinputs.get('NAS_attached_lib_name')
            media_agent = self.tcinputs.get('NAS_MediaAgent')
        else:
            lib_name = self.tcinputs['Mag_lib_name']
            media_agent = self.tcinputs['MediaAgent']

        if self.tcinputs.get('sp_using_pool') is True:
            if self.tcinputs.get('dedup') is True:
                kwargs = {'global_policy_name' : self.tcinputs['pool_name'],
                          'global_dedup_policy' : True}
            else:
                kwargs = {'global_policy_name' : self.tcinputs['pool_name'],
                          'global_dedup_policy' : False}
            self.log.info("Creating storage policy")
            self.snapconstants.storage_policy = self.commcell.storage_policies.add(
                self.snapconstants.storage_policy_name,
                self.tcinputs['Mag_lib_name'],
                self.tcinputs['MediaAgent'],
                ocum_server=self.snapconstants.ocum_server,
                **kwargs)
            self.log.info("Successfully created storage policy :{0} using Mag lib".format(
                self.snapconstants.storage_policy.storage_policy_name))

        else:
            self.log.info("Creating storage policy")
            self.snapconstants.storage_policy = self.commcell.storage_policies.add_tape_sp(
                self.snapconstants.storage_policy_name,
                lib_name,
                media_agent,
                self.tcinputs['drive_pool'],
                self.tcinputs['scratch_pool'],
                ocum_server=self.snapconstants.ocum_server)
            self.log.info("Successfully created storage policy :{0} using Tape lib".format(
                self.snapconstants.storage_policy.storage_policy_name))

        if self.snapconstants.ocum_server:
            self.log.info("*" * 20 +"This is OCUM SP, Not creating Snap primary Copy"+ "*" * 20)
            self.snapconstants.snap_copy_name = "Primary"
        else:
            self.log.info("Creating Snap Copy")
            self.snaphelper.create_snap_copy(self.snapconstants.snap_copy_name, False, True,
                                             lib_name,
                                             media_agent)
            self.log.info("Successfully created Snap Copy :{0}".format(self.snapconstants.snap_copy_name))
            self.snaphelper.delete_bkpcpy_schedule()

        if self.snapconstants.ocum_server:
            self.log.info("Creating Vault Copy")
            self.snapconstants.first_node_copy = "Vault"
            self.snaphelper.create_snap_copy(self.snapconstants.first_node_copy, False, True,
                                             lib_name,
                                             media_agent,
                                             self.snapconstants.snap_copy_name,
                                             self.snapconstants.prov_policy_vault,
                                             self.snapconstants.resource_pool_vault)
            self.log.info("Successfully created Vault Copy :{0}".format(self.snapconstants.first_node_copy))

        else:
            self.log.info("Creating Vault/Replica Copy")
            self.snapconstants.first_node_copy = "Replica"
            self.snaphelper.create_snap_copy(self.snapconstants.first_node_copy, False, True,
                                             lib_name,
                                             media_agent,
                                             self.snapconstants.snap_copy_name,
                                             is_replica_copy=True)
            self.log.info("Successfully created Vault/Replica Copy :{0}".format(self.snapconstants.first_node_copy))
            if self.snapconstants.snap_engine_at_array == "NetApp":
                self.snaphelper.svm_association(self.snapconstants.first_node_copy,
                                                self.snapconstants.arrayname,
                                                self.tcinputs['ArrayName2'])
            self.snaphelper.disable_auxcpy_schedule()

        self.snaphelper.entities.create({'backupset':self.snapconstants.entity_properties['backupset']})
        sc_obj = self.snaphelper.entities.create({'subclient':self.snapconstants.entity_properties['subclient']})
        self.snapconstants.subclient = sc_obj['subclient']['object']

        self.snapconstants.subclient.enable_intelli_snap(self.snapconstants.snap_engine_at_subclient)
        self.log.info("*" * 20 + "Storage Policy Update" + "*" * 20)
        if self.snapconstants.ocum_server:
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.snap_copy_name,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.snap_copy_name)

        self.snaphelper.add_test_data_folder()
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
        full1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
        if self.snapconstants.ocum_server:
            self.snaphelper.aux_copy()
        else:
            self.snaphelper.aux_copy(use_scale=True)
        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()
        self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.snaphelper.snap_outplace(1)
        self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                            self.snaphelper.client_machine)
        self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
        self.snaphelper.tape_outplace(full1_job.job_id, 2, full1_job.start_time, full1_job.end_time)
        self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                            self.snapconstants.windows_restore_client)
        self.log.info("*" * 20 + "Running InPlace Restore from Vault/Replica job" + "*" * 20)
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.snap_inplace(3)
        self.snaphelper.inplace_validation(full1_job.job_id,
                                           self.snapconstants.snap_copy_name,
                                           self.snapconstants.test_data_path)
        if not self.snapconstants.ocum_server:
            self.snaphelper.force_delete_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.force_delete_snap(full1_job.job_id, self.snapconstants.first_node_copy)
        time.sleep(60)
        self.agent.backupsets.delete(self.snapconstants.backupset_name)
        self.log.info("successfully deleted backupset : {0}".format(self.snapconstants.backupset_name))
        try:
            self.log.info("deleting storage policy: {0}".format(self.snapconstants.storage_policy.storage_policy_name))
            self.commcell.storage_policies.delete(self.snapconstants.storage_policy.storage_policy_name)
        except Exception as e:
            self.log.info("deleting Storage policy failed with err: " + str(e))
            self.log.info("treating it as soft failure")
        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

    def snap_template5(self):
        """Snap Template5 to perform IntelliSnap Metro Operations
        """
        access_node_primary = {self.client.client_name: 'add'}
        if self.snapconstants.proxy_client is not None:
            access_node_secondary = {self.snapconstants.proxy_client: 'add'}
        else:
            access_node_secondary = {self.client.client_name: 'delete'}

        self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
        self.snaphelper.add_array()
        self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
        self.snaphelper.edit_array(self.snapconstants.arrayname,
                                   self.snapconstants.source_config,
                                   self.snapconstants.config_update_level,
                                   array_access_node=access_node_primary)

        self.snapconstants.arrayname = self.tcinputs['ArrayName2']
        self.snapconstants.username = self.tcinputs['ArrayUserName2']
        self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
        self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
        self.snaphelper.add_array()
        self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)
        self.snaphelper.edit_array(self.tcinputs['ArrayName2'],
                                   self.snapconstants.target_config,
                                   self.snapconstants.config_update_level,
                                   array_access_node=access_node_secondary)
        if self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
            if self.snapconstants.vsm_array_name1:
                self.snapconstants.arrayname = self.tcinputs['VSMArrayName1']
                self.snapconstants.username = self.tcinputs['ArrayUserName']
                self.snapconstants.password = self.tcinputs.get('ArrayPassword')
                self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost', None)
                self.snaphelper.add_array(self.snapconstants.source_config_add_array)
                self.log.info("*" * 20 + "Successfully Added First VSM Array" + "*" * 20)
                self.snaphelper.edit_array(self.tcinputs['VSMArrayName1'],
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=access_node_primary,
                                           gad_arrayname=self.tcinputs['ArrayName'])
            if self.snapconstants.vsm_array_name2:
                self.snapconstants.arrayname = self.tcinputs['VSMArrayName2']
                self.snapconstants.username = self.tcinputs['ArrayUserName2']
                self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
                self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
                self.snaphelper.add_array(self.snapconstants.target_config_add_array)
                self.log.info("*" * 20 + "Successfully Added Second VSM Array" + "*" * 20)
                self.snaphelper.edit_array(self.tcinputs['VSMArrayName2'],
                                           self.snapconstants.target_config,
                                           self.snapconstants.config_update_level,
                                           level_id=None,
                                           array_access_node=access_node_secondary,
                                           gad_arrayname=self.tcinputs['ArrayName2'])

        """find controlhostid of both arrays to validate snapshot creation"""
        if self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
            if self.snapconstants.vsm_to_vsm:
                ctrlhost_array1 = self.snapconstants.execute_query(
                    self.snapconstants.get_gad_controlhost_id, {'a': self.tcinputs['ArrayName'],
                                                                'b': self.tcinputs['VSMArrayName1']})
                ctrlhost_array2 = self.snapconstants.execute_query(
                    self.snapconstants.get_gad_controlhost_id, {'a': self.tcinputs['ArrayName2'],
                                                                'b': self.tcinputs['VSMArrayName2']})

            else:
                ctrlhost_array1 = self.snapconstants.execute_query(
                    self.snapconstants.get_gad_controlhost_id, {'a': '',
                                                                'b': self.tcinputs['ArrayName']})

                ctrlhost_array2 = self.snapconstants.execute_query(
                    self.snapconstants.get_gad_controlhost_id, {'a': self.tcinputs['ArrayName2'],
                                                                'b': self.tcinputs['VSMArrayName2']})

        else:
            ctrlhost_array1 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName']})
            ctrlhost_array2 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName2']})

        self.snapconstants.arrayname = self.tcinputs['ArrayName']
        self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
        self.snaphelper.setup()
        self.snapconstants.config_update_level = 'subclient'
        """For HDS GAD, enable GAD backup at subclient level"""
        if self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
            self.log.info("Enabling option for GAD backup ")
            self.snapconstants.snap_configs = {"Disable GAD operation for the devices (CCI engines)": "False"}

        elif self.tcinputs['SnapEngineAtArray'] == 'Dell EMC PowerMAX / VMAX / Symmetrix':
            self.snapconstants.snap_configs = {"Do not create SRDF/Metro secondary snap": "False"}
            self.log.info("Enabling option to create SRDF/Metro secondary snap")

        elif self.tcinputs['SnapEngineAtArray'] == 'INFINIDAT':
            self.snapconstants.snap_configs = {"Do not create Active Active remote volume snapshot": "False"}
            self.log.info("Enabling option to create Active Active remote volume snapshot")

        elif self.tcinputs['SnapEngineAtArray'] == 'Pure Storage FlashArray':
            self.log.info("Enabling option to track Pod volume secondary snapshot")
            self.snapconstants.snap_configs = {"Do not track Pod volume secondary snapshots": "False"}

        self.snaphelper.update_metro_config()
        self.log.info("Successfully Enabled Snap Config at subclient level to perform "
                      "metro operations ")

        self.snaphelper.add_test_data_folder()
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running FIRST FULL Snap Backup job" + "*" * 20)
        self.snapconstants.skip_catalog = True
        full1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Verifying Snap on both nodes" + "*" * 20)
        unique_controlhost_id = self.snaphelper.unique_control_host(full1_job)

        if len(unique_controlhost_id) == 2:
            for i in range(len(unique_controlhost_id)):
                if unique_controlhost_id[i][0] not in (ctrlhost_array1[0][0], ctrlhost_array2[0][0]):
                    raise Exception(
                        "Snapshots for job : {0} not created on both Nodes".format(full1_job.job_id))
        else:
            raise Exception(
                "Snapshots for job : {0} not created on both Nodes".format(full1_job.job_id))
        self.log.info("Snaps created on both nodes of Metro Cluster")

        self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
        self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
        self.snaphelper.snap_outplace(1)
        self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                            self.snaphelper.client_machine)
        self.log.info("*" * 20 + "Mount Snap and its Validation from FIRST node" + "*" * 20)
        self.snaphelper.mount_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.mount_validation(full1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("Full job is  {0}".format(full1_job.job_id))
        mnt_controlhost_id = self.snapconstants.execute_query(
            self.snapconstants.get_mount_control_host, {'a': full1_job.job_id})

        if ctrlhost_array1[0][0] == mnt_controlhost_id[0][0]:
            self.log.info("Snap is mounted from Primary Array {0} as expected".format(mnt_controlhost_id[0][0]))
        else:
            raise Exception(
                "Snapshot is not mounted from expected Array")

        self.log.info("*" * 20 + "UnMount Snap and its Validation from FIRST node" + "*" * 20)
        self.snaphelper.unmount_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.unmount_validation(full1_job.job_id, self.snapconstants.snap_copy_name)

        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()

        if self.snapconstants.proxy_client:
            self.log.info("*" * 20 + "Changing proxy on the subclient to verify mounting of snapshot from"
                          " secondary site during backup copy and mount operation" + "*" * 20)
            proxy_options = {
                'snap_proxy': self.snapconstants.proxy_client,
                'backupcopy_proxy': self.snapconstants.proxy_client,
                'use_source_if_proxy_unreachable': True
            }
            self.snapconstants.subclient.enable_intelli_snap(
                self.snapconstants.snap_engine_at_subclient, proxy_options)
            self.log.info("Successfully changed the proxy on the client")

        else:
            self.log.info("*" * 20 + "Changing array controller on secondary array to verify mounting of snapshot"
                                     " from secondary site during backup copy and mount operation" + "*" * 20)
            if self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
                if self.snapconstants.vsm_to_vsm:
                    self.snaphelper.edit_array(self.tcinputs['VSMArrayName1'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_secondary,
                                               gad_arrayname=self.tcinputs['ArrayName'])
                    self.snaphelper.edit_array(self.tcinputs['VSMArrayName2'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_primary,
                                               gad_arrayname=self.tcinputs['ArrayName2'])
                    self.log.info("Successfully updated array controller for the secondary array.")

                else:
                    self.snaphelper.edit_array(self.tcinputs['ArrayName'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_secondary
                                               )
                    self.snaphelper.edit_array(self.tcinputs['VSMArrayName2'],
                                               snap_configs=None,
                                               config_update_level="array",
                                               array_access_node=access_node_primary,
                                               gad_arrayname=self.tcinputs['ArrayName2'])
                    self.log.info("Successfully updated array controller for the secondary array.")
            else:
                self.snaphelper.edit_array(self.tcinputs['ArrayName'],
                                           snap_configs=None,
                                           config_update_level="array",
                                           array_access_node=access_node_secondary)

                self.snaphelper.edit_array(self.tcinputs['ArrayName2'],
                                           snap_configs=None,
                                           config_update_level="array",
                                           array_access_node=access_node_primary)

        self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        if self.snapconstants.problematic_data:
            self.snaphelper.update_test_data(mode='edit',
                                             path=list(self.snapconstants.test_data_folder[0] + self.snapconstants.delimiter + "dir1"))
        else:
            self.snaphelper.update_test_data(mode='edit', path=self.snapconstants.test_data_folder)
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Verifying Snap on both nodes" + "*" * 20)
        unique_controlhost_id = self.snaphelper.unique_control_host(inc1_job)

        if len(unique_controlhost_id) == 2:
            for i in range(len(unique_controlhost_id)):
                if unique_controlhost_id[i][0] not in (ctrlhost_array1[0][0], ctrlhost_array2[0][0]):
                    raise Exception(
                        "Snapshots for job : {0} not created on both Nodes".format(full1_job.job_id))
        else:
            raise Exception(
                "Snapshots for job : {0} not created on both Nodes".format(full1_job.job_id))
        self.log.info("Snaps created on both nodes of Metro Cluster")

        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.log.info("*" * 20 + "Running InPlace Restore from Snap Backup job" + "*" * 20)
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.snap_inplace(1)
        self.snaphelper.inplace_validation(inc1_job.job_id,
                                           self.snapconstants.snap_copy_name,
                                           self.snapconstants.test_data_path)

        self.log.info("*" * 20 + "Mount Snap and its Validation from Second node" + "*" * 20)
        if self.snapconstants.proxy_client:
            self.snaphelper.mount_snap(inc1_job.job_id, self.snapconstants.snap_copy_name,
                                       do_vssprotection=True,
                                       client_name=self.snapconstants.proxy_client,
                                       mountpath=self.snapconstants.mount_path)
            self.snaphelper.mount_validation(inc1_job.job_id, self.snapconstants.snap_copy_name,
                                             self.snapconstants.proxy_client)
        else:
            self.snaphelper.mount_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.mount_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("Incremental job id {0}".format(inc1_job.job_id))
        mnt_controlhost_id = self.snapconstants.execute_query(
            self.snapconstants.get_mount_control_host, {'a': inc1_job.job_id})

        if ctrlhost_array2[0][0] == mnt_controlhost_id[0][0]:
            self.log.info("Snap is mounted from Secondary Array {0} as expected".format(mnt_controlhost_id[0][0]))
        else:
            raise Exception(
                "Snapshot is not mounted from expected Array")

        self.log.info("*" * 20 + "UnMount Snap and its Validation from Second node" + "*" * 20)
        self.snaphelper.unmount_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.unmount_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)

        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()

        if self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
            self.log.info("Disabling option for GAD backup ")
            self.snapconstants.snap_configs = {"Disable GAD operation for the devices (CCI engines)": "True"}

        elif self.tcinputs['SnapEngineAtArray'] == 'Dell EMC PowerMAX / VMAX / Symmetrix':
            self.snapconstants.snap_configs = {"Do not create SRDF/Metro secondary snap": "True"}
            self.log.info("Disabling option to create SRDF/Metro secondary snap")

        elif self.tcinputs['SnapEngineAtArray'] == 'INFINIDAT':
            self.log.info("Disabling option to create SRDF/Metro secondary snap")
            self.snapconstants.snap_configs = {"Do not create Active Active remote volume snapshot": "True"}

        elif self.tcinputs['SnapEngineAtArray'] == 'Pure Storage FlashArray':
            self.log.info("Disabling option to create SRDF/Metro secondary snap")
            self.snapconstants.snap_configs = {"Do not track Pod volume secondary snapshots": "True"}

        self.snaphelper.update_metro_config()
        self.log.info("successfully disabled the option to run metro operations")

        self.log.info("*" * 20 + "Running Second Incremental Snap Backup job" + "*" * 20)
        self.snapconstants.skip_catalog = True
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        inc2_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Verifying if Snap is created only on one node" + "*" * 20)
        unique_controlhost_id = self.snaphelper.unique_control_host(inc2_job)

        if len(unique_controlhost_id) == 1:
            self.log.info("Snap Created only on ControlHost ID {0}".format(unique_controlhost_id[0][0]))
        else:
            raise Exception(
                "Snapshot is not created for primary node alone")

        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()

        self.log.info("*" * 20 + "DELETE VALIDATIONS" + "*" * 20)
        self.log.info("Verifying delete operation on Primary Snap Copy")
        self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.delete_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Data Aging Validation on Snap copy" + "*" * 20)
        self.snaphelper.data_aging_validation(self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
        self.snaphelper.cleanup()

        self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
        self.snapconstants.arrayname = self.tcinputs['ArrayName']
        self.snaphelper.delete_array()
        self.snapconstants.arrayname = self.tcinputs['ArrayName2']
        self.snaphelper.delete_array()
        if self.snapconstants.vsm_array_name1:
            self.snapconstants.arrayname = self.tcinputs['VSMArrayName1']
            self.snaphelper.delete_array()
        if self.snapconstants.vsm_array_name2:
            self.snapconstants.arrayname = self.tcinputs['VSMArrayName2']
            self.snaphelper.delete_array()

        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

    def snap_template6(self):
        """Snap Template6 to verify snap configs
        """

        self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pv_replica", "pm_replica", "fanout"}:
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
            if self.snapconstants.snap_engine_at_array == "Fujitsu ETERNUS AF / DX":
                self.snapconstants.config_update_level = "subclient"
            access_node = {self.client.client_name: 'add'}
            if self.snapconstants.source_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=access_node)

            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)
            if self.snapconstants.snap_engine_at_array == "Fujitsu ETERNUS AF / DX":
                self.snapconstants.config_update_level = "subclient"
            if self.snapconstants.target_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.target_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=access_node)
        else:
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
            if self.snapconstants.snap_engine_at_array == "Fujitsu ETERNUS AF / DX":
                self.snapconstants.config_update_level = "subclient"
            access_node = {self.client.client_name: 'add'}
            if self.snapconstants.source_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=access_node)

            """ Re-Set arrayname and engine Name as primary """
        self.snapconstants.arrayname = self.tcinputs['ArrayName']
        self.snapconstants.snap_engine_at_array = self.tcinputs['SnapEngineAtArray']
        self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
        self.snaphelper.setup()
        self.snaphelper.add_test_data_folder()
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running FIRST FULL Snap Backup job" + "*" * 20)
        full1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Verifiying Snap Configs after snap backup" + "*" * 20)
        if not self.tcinputs['SnapEngineAtArray'] == 'NetApp':
            options = {'prepare', 'create'}
        else:
            options = {'prepare', 'create', 'map', 'unmap'}
        self.snaphelper.snap_configs_validation(full1_job.job_id,
                                                self.snapconstants.primary_snapconfigs_to_validate,
                                                SnapConfig_level.array.value,
                                                options, primary=True)
        if not self.tcinputs['SnapEngineAtArray'] == 'NetApp':
            self.log.info("*" * 20 + "Mounting Snapshot" + "*" * 20)
            mount_job = self.snaphelper.mount_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Verifiying Snap Configs after mounting snapshot" + "*" * 20)
            options = {'map'}
            self.snaphelper.snap_configs_validation(mount_job.job_id,
                                                    self.snapconstants.primary_snapconfigs_to_validate,
                                                    SnapConfig_level.array.value,
                                                    options, primary=True)
            self.log.info("*" * 20 + "UnMounting Snapshot" + "*" * 20)
            unmount_job = self.snaphelper.unmount_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Verifiying Snap Configs after Unmounting snapshot" + "*" * 20)
            options = {'unmap'}
            self.snaphelper.snap_configs_validation(unmount_job.job_id,
                                                    self.snapconstants.primary_snapconfigs_to_validate,
                                                    SnapConfig_level.array.value,
                                                    options, primary=True)
            
        self.log.info("*" * 20 + "Revert Snapshot" + "*" * 20)
        revert_job = self.snaphelper.revert_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Verifiying Snap Configs after Revert Snap" + "*" * 20)
        options = {'revert'}
        self.snaphelper.snap_configs_validation(revert_job.job_id,
                                                self.snapconstants.primary_snapconfigs_to_validate,
                                                SnapConfig_level.array.value,
                                                options, primary=True)
        if self.snapconstants.secondary_snapconfigs_to_validate is not None:
            self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
            if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
                aux_job = self.snaphelper.aux_copy()
            else:
                aux_job = self.snaphelper.aux_copy(use_scale=True)
            self.log.info("*" * 20 + "Verifiying Snap Configs after Aux copy" + "*" * 20)
            options = {'remote-prepare', 'remote-create'}
            self.snaphelper.snap_configs_validation(aux_job.job_id,
                                                    self.snapconstants.secondary_snapconfigs_to_validate,
                                                    SnapConfig_level.array.value,
                                                    options, primary=False)

            self.log.info("*" * 20 + "Mount Snap from FIRST node" + "*" * 20)
            mount_job = self.snaphelper.mount_snap(full1_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Verifiying Snap Configs after mount from first node" + "*" * 20)
            options = {'map'}
            self.snaphelper.snap_configs_validation(mount_job.job_id,
                                                    self.snapconstants.secondary_snapconfigs_to_validate,
                                                    SnapConfig_level.array.value,
                                                    options, primary=False)
            self.log.info("*" * 20 + "UnMount Snap from FIRST node" + "*" * 20)
            unmount_job = self.snaphelper.unmount_snap(full1_job.job_id, self.snapconstants.first_node_copy)
            options = {'unmap'}
            self.snaphelper.snap_configs_validation(unmount_job.job_id,
                                                    self.snapconstants.secondary_snapconfigs_to_validate,
                                                    SnapConfig_level.array.value,
                                                    options, primary=False)
            self.log.info("*" * 20 + "Delete Snap from FIRST node" + "*" * 20)
            delete_job = self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Verifiying Snap Configs after Delete snap from first node" + "*" * 20)
            options = {'delete'}
            self.snaphelper.snap_configs_validation(delete_job.job_id,
                                                    self.snapconstants.secondary_snapconfigs_to_validate,
                                                    SnapConfig_level.array.value,
                                                    options, primary=False)
        self.log.info("*" * 20 + "Delete Snap from Primary Snap copy" + "*" * 20)
        delete_job = self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Verifiying Snap Configs after Delete snap from PRIMARY Snap copy" + "*" * 20)
        options = {'delete'}
        self.snaphelper.snap_configs_validation(delete_job.job_id,
                                                self.snapconstants.primary_snapconfigs_to_validate,
                                                SnapConfig_level.array.value,
                                                options, primary=True)

        self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
        self.snaphelper.cleanup()

        self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
        if self.snapconstants.type in {"pv", "pm", "pv_replica", "pm_replica"}:
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()
        else:
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snaphelper.delete_array()
        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


    def snap_template7(self):
        """Snap Template7 with empty backup cycle followed by backup cycle with data
        """
        self.snaphelper.pre_cleanup()

        self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
        self.snaphelper.setup()

        self.log.info("*" * 20 + "Running FIRST FULL Snap Backup job" + "*" * 20)
        # self.snapconstants.skip_catalog = True
        self.snaphelper.clear_subclient_data()
        full1_job = self.snaphelper.snap_backup()
        self.log.info("*" * 20 + "Running FIRST INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        inc1_job = self.snaphelper.snap_backup()

        self.snaphelper.add_test_data_folder()
        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.snapconstants.backup_level = 'FULL'
        self.log.info("*" * 20 + "Running SECOND FULL Snap Backup job" + "*" * 20)
        full2_job = self.snaphelper.snap_backup()

        self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Running SECOND INCREMENTAL Snap Backup job" + "*" * 20)
        self.snapconstants.backup_level = 'INCREMENTAL'
        inc2_job = self.snaphelper.snap_backup()
        self.snapconstants.source_path = self.snapconstants.test_data_path
        self.log.info("*" * 20 + "Running InPlace Restore from Snap Backup job" + "*" * 20)
        self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
        self.snaphelper.snap_inplace(1)
        self.snaphelper.inplace_validation(inc2_job.job_id,
                                           self.snapconstants.snap_copy_name,
                                           self.snapconstants.test_data_path)
        self.log.info("*" * 20 + "Mount Snap and its Validation" + "*" * 20)
        self.snaphelper.mount_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.mount_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "UnMount Snap and its Validation" + "*" * 20)
        self.snaphelper.unmount_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.snaphelper.unmount_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)
        self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
        self.snaphelper.backup_copy()

        self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
        self.snaphelper.cleanup()

        self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)