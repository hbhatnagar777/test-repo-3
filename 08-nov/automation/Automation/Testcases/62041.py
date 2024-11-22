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
    __init__()          --  initialize TestCase class

    setup()             --  Setup function of this test case"

    run()               --  run function of this test case calls SnapHelper Class to execute
                            and Validate Below Operations.
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount, Unmount,
                            Delete for Pure Storage 3DC feature.
"""

from base64 import b64encode
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from VirtualServer.VSAUtils import VirtualServerUtils

class TestCase(CVTestCase):
    """Class for executing acceptance test of Pure Storage 3DC functionality"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None
            }

    def setup(self):
        """Setup function of this test case"""
        self.tcinputs['ReplicationType'] = "pv_replica"
        self.tcinputs['skip_revert'] = True
        self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
        self.snaphelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
        self.name = "Automation : Verification of Pure Storage 3DC Fuctionality using snap engine {0}".format(
            self.tcinputs['SnapEngineAtSubclient'])

    def run(self):
        """Main function for test case execution

        Here are the steps performed in this test case
        Steps:
        1. Call pre-cleanup
        2. Add Primary metro array, secondary metro array and replica Array in array management
        3. Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, backupset, subclient, snap, aux copy and replica/ vault/mirror copies
           and enable intellisnap on subclient.
        4. Configure the replication target on the primary metro array and secondary metro array’s snap config
           at SC level        .
        5. Add test data folder in the subclient content
        6. Run Full job and Verify Snaps are created on all the 3 nodes of the 3DC configuration
        7. Run out of place restore from snap and validate
        8. Mount snapshot from Primary and validate. Unmount the snap and validate
        9. Run backup copy of Full job
        10. Set the array controller on the secondary array to validate mounting of snap from secondary array
        11. Add\edit test data folder in the subclient content
        12. Run incremental job and Verify Snaps are created on all the 3 nodes of the 3DC configuration
        13. Run in place restore from snap and validate
        14. Mount snapshot from Secondary array and validate. Unmount the snap and validate
        16. Run backup copy of Incremental job
        17. Run out of place restore from backup copy precedence
        18. Update storage policy to change the source of backup copy to Replica copy
        19. Add\edit test data folder in the subclient content
        20. Run incremental job and Verify Snaps are created on all the 3 nodes of the 3DC configuration
        21. Run aux copy to copy the index in the replica copy and then run backup copy. Make sure that during backup
            copy snaps from replica array are mounted
        22. Mount snaps from replica array and validate. Unmount the snap and validate
        23. Delete snaps from primary and replica array and validate
        24. Validate data aging and delete remaining snaps
        25. Cleanup entities
        26. Delete array entries
        """

        try:

            self.log.info("Started executing {0} testcase".format(self.id))
            self.snaphelper.pre_cleanup()
            access_node_primary = {self.client.client_name: 'add'}
            if self.snapconstants.proxy_client is not None:
                access_node_secondary = {self.snapconstants.proxy_client: 'add'}
            else:
                access_node_secondary = {self.client.client_name: 'delete'}
            VirtualServerUtils.decorative_log("Adding Arrays")
            self.snaphelper.add_array()
            self.snaphelper.edit_array(self.snapconstants.arrayname,
                                       array_access_node=access_node_primary)
            VirtualServerUtils.decorative_log("Successfully Added Primary Metro Array")
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = b64encode(
                self.tcinputs['ArrayPassword2'].encode()).decode()
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
            self.snaphelper.add_array()
            VirtualServerUtils.decorative_log("Successfully Added Secondary Metro Array")
            self.snaphelper.edit_array(self.snapconstants.arrayname,
                                       array_access_node=access_node_secondary)
            self.snapconstants.arrayname = self.tcinputs['ArrayName3']
            self.snapconstants.username = self.tcinputs['ArrayUserName3']
            self.snapconstants.password = b64encode(
                self.tcinputs['ArrayPassword3'].encode()).decode()
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost3', None)
            self.snaphelper.add_array()
            VirtualServerUtils.decorative_log("Successfully Added Replica Array")

            VirtualServerUtils.decorative_log("Setup of Intellisnap Entities")
            self.snaphelper.setup()
            VirtualServerUtils.decorative_log("Updating Snap Config to enable 3DC configuration at subclient level")
            self.snapconstants.config_update_level = 'subclient'
            self.snapconstants.snap_configs = self.snapconstants.source_config
            self.snaphelper.update_metro_config()
            VirtualServerUtils.decorative_log("Successfully updated the snap config")
            self.snaphelper.add_test_data_folder()
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            VirtualServerUtils.decorative_log("Running FULL Snap Backup job")

            self.snapconstants.skip_catalog = True
            full1_job = self.snaphelper.snap_backup()
            self.snaphelper.aux_copy(use_scale=True)
            self.snaphelper.verify_3dc_backup(full1_job)
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            VirtualServerUtils.decorative_log("Running OutPlace Restore from Snap Backup job")
            self.snaphelper.snap_outplace(1)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)
            VirtualServerUtils.decorative_log("Mount Snap and its Validation from FIRST node")
            self.snaphelper.mount_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.mount_validation(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.metro_mount_validation(full1_job.job_id, self.snaphelper.ctrlhost_array1,
                                                   self.tcinputs['ArrayName'])
            VirtualServerUtils.decorative_log("UnMount Snap and its Validation from FIRST node")
            self.snaphelper.unmount_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.unmount_validation(full1_job.job_id, self.snapconstants.snap_copy_name)
            VirtualServerUtils.decorative_log("Running Backup copy from Storage Policy")
            self.snaphelper.backup_copy()

            if self.snapconstants.proxy_client:
                VirtualServerUtils.decorative_log("Changing proxy on the subclient to verify mounting of snapshot from "
                                                  "secondary site during backup copy and mount operation")
                proxy_options = {
                    'snap_proxy': self.snapconstants.proxy_client,
                    'backupcopy_proxy': self.snapconstants.proxy_client,
                    'use_source_if_proxy_unreachable': True
                }
                self.snapconstants.subclient.enable_intelli_snap(
                    self.snapconstants.snap_engine_at_subclient, proxy_options)
                self.log.info("Successfully changed the proxy on the subclient")

            else:
                VirtualServerUtils.decorative_log("Changing array controller on secondary array to verify mounting of snapshot"
                                     " from secondary site during backup copy and mount operation")
                self.snaphelper.edit_array(self.tcinputs['ArrayName'],
                                           snap_configs=None,
                                           config_update_level="array",
                                           array_access_node=access_node_secondary)
                self.snaphelper.edit_array(self.tcinputs['ArrayName2'],
                                           snap_configs=None,
                                           config_update_level="array",array_access_node=access_node_primary)

            VirtualServerUtils.decorative_log("Running INCREMENTAL Snap Backup job")
            self.snapconstants.backup_level = 'INCREMENTAL'
            if self.snapconstants.problematic_data:
                self.snaphelper.update_test_data(mode='edit',
                                                path=self.snapconstants.test_data_folder + self.snapconstants.delimiter + "dir1")
            else:
                self.snaphelper.update_test_data(mode='edit', path=self.snapconstants.test_data_folder)
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            inc1_job = self.snaphelper.snap_backup()
            self.snaphelper.aux_copy(use_scale=True)
            self.snaphelper.verify_3dc_backup(inc1_job)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            VirtualServerUtils.decorative_log("Running InPlace Restore from Snap Backup job")
            self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
            self.snaphelper.snap_inplace(1)
            self.snaphelper.inplace_validation(inc1_job.job_id,
                                             self.snapconstants.snap_copy_name,
                                            self.snapconstants.test_data_path)

            VirtualServerUtils.decorative_log("Mount Snap and its Validation from Secondary Array")
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
            self.snaphelper.metro_mount_validation(inc1_job.job_id, self.snaphelper.ctrlhost_array2,
                                                   self.tcinputs['ArrayName2'])
            VirtualServerUtils.decorative_log("UnMount Snap and its Validation from Second nodey")
            self.snaphelper.unmount_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.unmount_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)

            VirtualServerUtils.decorative_log("Running Backup copy from Storage Policy")
            self.snaphelper.backup_copy()
            VirtualServerUtils.decorative_log("Running OutPlace Restore from Backup Copy")
            self.snaphelper.tape_outplace(inc1_job.job_id, 2)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            VirtualServerUtils.decorative_log("Updating Storage Policy to make Replica copy as source for backup copy")
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.first_node_copy,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.snap_copy_name)
            VirtualServerUtils.decorative_log("Running SECOND INCREMENTAL Snap Backup job")
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            inc2_job = self.snaphelper.snap_backup()
            self.snaphelper.aux_copy(use_scale=True)
            self.snaphelper.verify_3dc_backup(inc2_job)
            VirtualServerUtils.decorative_log("Running Backup copy from Storage Policy with source as Replica copy")
            self.snaphelper.backup_copy()
            VirtualServerUtils.decorative_log("Mount Snap and its Validation from replica Array")
            self.snaphelper.mount_snap(inc2_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.mount_validation(inc2_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.metro_mount_validation(inc2_job.job_id, self.snaphelper.ctrlhost_array3,
                                                   self.tcinputs['ArrayName3'])
            VirtualServerUtils.decorative_log("UnMount Snap and its Validation from Second node")
            self.snaphelper.unmount_snap(inc2_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.unmount_validation(inc2_job.job_id, self.snapconstants.first_node_copy)
            VirtualServerUtils.decorative_log("Running OutPlace Restore from Replica Copy")
            self.snaphelper.snap_outplace(4)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)
            self.log.info("Verifying delete operation on Copy: {0}".format(
                self.snapconstants.snap_copy_name))
            self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(inc2_job.job_id, self.snapconstants.snap_copy_name)

            self.log.info("Verifying delete operation on Copy: {0}".format(
                self.snapconstants.first_node_copy))
            self.snaphelper.delete_snap(inc2_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(inc2_job.job_id, self.snapconstants.first_node_copy)
            VirtualServerUtils.decorative_log("Data Aging Validation on Snap copy")
            self.snaphelper.data_aging_validation(self.snapconstants.snap_copy_name)
            VirtualServerUtils.decorative_log("Deleting all the remaning snap from replica copy")
            self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(full1_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(inc1_job.job_id, self.snapconstants.first_node_copy)

        except Exception as excp:
            self.log.error(f'Failed with error: {excp}')
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                VirtualServerUtils.decorative_log("Disabling backup copy and snapshot catalogue")
                self.snaphelper.update_storage_policy()
                VirtualServerUtils.decorative_log("Cleanup of Snap Entities")
                self.snaphelper.cleanup()
                VirtualServerUtils.decorative_log("Deletion of Arrays")
                self.snapconstants.arrayname = self.tcinputs['ArrayName']
                self.snaphelper.delete_array()
                self.snapconstants.arrayname = self.tcinputs['ArrayName2']
                self.snaphelper.delete_array()
                self.snapconstants.arrayname = self.tcinputs['ArrayName3']
                self.snaphelper.delete_array()
                VirtualServerUtils.decorative_log("SUCCESSFULLY COMPLETED THE TEST CASE")

        except exception as excp:
            self.log.error(f'Failed with error: {excp}')
            self.result_string = str(excp)
            self.status = constants.FAILED


