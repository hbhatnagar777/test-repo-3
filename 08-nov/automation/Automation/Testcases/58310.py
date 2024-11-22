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

    run()               --  run function of this test case calls SnapHelper Class to execute
                            and Validate Below Operations.
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount, Unmount,
                            Delete for Hitachi Vantara Primary Remote Snap feature.
"""

from base64 import b64encode
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from FileSystem.SNAPUtils.snaphelper import SNAPHelper

class TestCase(CVTestCase):
    """Class for executing acceptance test of Hitachi Vantara Primary Remote Snap feature"""

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

        self.name = "Automation : Verifies Hitachi Vantara Primary Remote Snap feature using snap engine {0}".format(
            self.tcinputs['SnapEngineAtSubclient'])

    def run(self):
        """Main function for test case execution

        Here are the steps performed in this test case
        Steps:
        1. Call pre-cleanup
        2. Add Primary and secondary hardware Array
        3. Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, backupset, subclient, snap, aux copy and replica/ vault/mirror copies
           and enable intellisnap on subclient.
        4. add test data folder in the subclient content.
        5. Do not enable Snap config to create primary remote snaps. Run Full Snap backup job with skip catalog.
        6. Verify Snaps are created on Primary array
        7. Delete the snap from the primary array.
        8. Enable snap config to create primary remote snap on secondary array at subclinet level
        9. Run Full Snap backup job with skip catalog
        10.Verify Snaps are created on Secondary array.
        11. Run out of place restore from snap backup and Validate
        12. Add date to source path and run incremental snap backup
        13. Run inplace restore from snap backup and validate
        14. Mount Snap from secomdary array and its Validation
        15. UnMount Snap and its Validation f
        16. Run Backup Copy from Storage Policy Level
        17. Run Restore from backup copy and validate data
        18. Delete Snashot and its validation
        19. Run Data Aging and its validation
        20. Cleanup entities
        21. Delete array entries
        """
        log = logger.get_log()

        try:
            self.log = logger.get_log()
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snaphelper.pre_cleanup()
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            self.snaphelper.edit_array(self.snapconstants.arrayname,
                                       self.snapconstants.source_config,
                                       self.snapconstants.config_update_level)
            self.log.info("*" * 20 + "Successfully Added Primary Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = b64encode(
                self.tcinputs['ArrayPassword2'].encode()).decode()
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Secondary Array" + "*" * 20)
            self.snaphelper.edit_array(self.snapconstants.arrayname,
                                       self.snapconstants.target_config,
                                       self.snapconstants.config_update_level)
            """find controlhostid of both arrays to validate snapshot creation"""
            ctrlhost_array1 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName']})
            ctrlhost_array2 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName2']})
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            self.snaphelper.update_test_data(mode='add')
            self.snapconstants.skip_catalog = True
            """When Snap config "Create primary snap at replication target site (CCI engines)" is not set,
                the snap should be created on primary array"""
            full1_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Verifying Snap on Primary array {0}".format(self.tcinputs['ArrayName'])
                          + "*" * 20)
            controlhost_id = self.snapconstants.execute_query(
                self.snapconstants.get_control_host, {'a': full1_job.job_id})
            if controlhost_id[0][0] == ctrlhost_array1[0][0]:
                self.log.info("Snaps created on Primary Array {0} as Snap config:"
                    "'Create primary snap at replication target site (CCI engines)'"
                    " is not set for the job".format(self.tcinputs['ArrayName']))
            else:
                raise Exception(
                    "Snapshot is not created on the Primary Array")
            self.log.info("*" * 20 + "Delete the snapshot created on Primary array and validate the operation"
                          + "*" * 20)
            self.log.info("Verifying delete operation on Primary Array")
            self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(full1_job.job_id, self.snapconstants.snap_copy_name)
            """Set the Snap config on Primary array to enable Creation of Primary Remote Snap at replication site"""
            self.snapconstants.source_config = {"Create primary snap at replication target site (CCI engines)":
                                                    self.tcinputs['ArrayName2']}
            self.snapconstants.config_update_level = "subclient"
            if self.snapconstants.source_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.source_config,
                                           self.snapconstants.config_update_level,
                                           int(self.snapconstants.subclient.subclient_id))
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            full2_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Verifying Snap on Secondary array" + "*" * 20)
            controlhost_id = self.snapconstants.execute_query(
                self.snapconstants.get_control_host, {'a': full2_job.job_id})
            if controlhost_id[0][0] == ctrlhost_array2[0][0]:
                self.log.info("Snaps created on Secondary Array {0} as Snap config: "
                              "'Create primary snap at replication target site (CCI engines)' is set on "
                              "Primary array {1}".format(self.tcinputs['ArrayName2'], self.tcinputs['ArrayName']))
                self.log.info("Validation of Primary Remote Snap creation on secondary array completed successfully")
            else:
                raise Exception(
                    "Snapshot is not created on the Secondary Array {0}. "
                    "Please check the configuration".format(self.tcinputs['ArrayName2']))
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
            self.snaphelper.snap_outplace(1)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snaphelper.update_test_data(mode='add')
            inc1_job = self.snaphelper.snap_backup()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.log.info("*" * 20 + "Running InPlace Restore from Snap Backup job" + "*" * 20)
            self.snaphelper.update_test_data(mode='copy')
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
            self.snaphelper.tape_outplace(inc1_job.job_id, 2)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            self.log.info("*" * 20 + "Delete Snap and its Validation" + "*" * 20)
            self.snaphelper.delete_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(inc1_job.job_id, self.snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Data Aging Validation on Snap copy" + "*" * 20)
            self.snaphelper.data_aging_validation(self.snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.log.info("Deleting Primary Array")
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.log.info("Deleting Secondary Array")
            self.snaphelper.delete_array()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
