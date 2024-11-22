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
                            Snap Backup, backup Copy and restores from Tape copy

"""
import json
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):


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
        self.name = """Automation : This case will cover some of the negative and advance cases for Filescan
                    """
        self.fshelper = FSHelper(self)

    def run(self):
        """Main function for test case execution"""


        try:
            self.log.info(f'Started executing {self.id} testcase')
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            self.client_machine = Machine(self.client)
            self.os_name = self.client_machine.os_info

            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            snap_helper.add_array()
            if snapconstants.snap_engine_at_array == "Dell EMC VNX / CLARiiON":
                snapconstants.config_update_level = "subclient"
            if snapconstants.source_config is not None:
                x = json.loads(snapconstants.source_config)
                for config, value in x.items():
                    snap_helper.edit_array(snapconstants.arrayname, config, value,
                                           snapconstants.config_update_level)

            if snapconstants.vplex_engine is True:
                """ Adding First Backeend arrays """
                self.log.info("*" * 20 + "Adding backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName1']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName1']
                snapconstants.password = snapconstants.tcinputs['BackendArrayPassword1']
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendArrayControlHost1', None)
                snapconstants.snap_engine_at_array = snapconstants.tcinputs['BackendSnapEngineAtArray']
                snap_helper.add_array()
                """ Adding Second Backend array """
                self.log.info("*" * 20 + "Adding Second backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName2']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName2']
                snapconstants.password =  snapconstants.tcinputs.get('BackendArrayPassword2')
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendControlHost2', None)
                snap_helper.add_array()
            """ Re-Set arrayname and engine Name as primary """
            snapconstants.arrayname = snapconstants.tcinputs['ArrayName']
            snapconstants.snap_engine_at_array = snapconstants.tcinputs['SnapEngineAtArray']
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            snap_helper.setup()

            #Step 1 Running Backups by Killing one of the Job and restore from Backup copy for Filescan testing
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full1_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full1_job.job_id, snapconstants.snap_copy_name)
            snap_helper.update_test_data(mode='edit')
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Adding new files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            self.log.info("*" * 20 + "Killing Incremental Snap Backup job" + "*" * 20)
            inc1_job = snap_helper.kill_job()
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            inc2_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Running backup copy for the cycle" + "*" * 20)
            snap_helper.backup_copy()
            snapconstants.source_path = snapconstants.test_data_path
            self.log.info("*" * 20 + "Running OutPlace Restore from Incremental Backup" + "*" * 20)
            snap_helper.tape_outplace(inc2_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)

            # Step 2 Running Backup jobs, deleting cjinfo file for one of the job and restore from Backup copy for filescan testing
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full2_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full2_job.job_id, snapconstants.snap_copy_name)
            snap_helper.update_test_data(mode='edit')
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Adding new files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            inc3_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Deleting cjinfo files from JR directory" + "*" * 20)
            self.subclient = snapconstants.subclient
            self.data_access_nodes = None
            jr_delete_path = self.fshelper.subclient_job_results_directory[self.client_machine.machine_name]
            jr_delete_path1 = self.client_machine.join_path(jr_delete_path, "cjinfoinc.cvf")
            jr_delete_path2 = self.client_machine.join_path(jr_delete_path, "cjinfoTot.cvf")
            self.log.info("*" * 20 + "Started Deleting cjinfo files at locations {0} and {1} from JR directory "
                          .format(jr_delete_path1, jr_delete_path2) + "*" * 20)
            self.client_machine.delete_file(file_path=jr_delete_path1)
            self.client_machine.delete_file(file_path=jr_delete_path2)
            if self.client_machine.check_file_exists(jr_delete_path1) and self.client_machine.check_file_exists(jr_delete_path2):
                raise Exception("cjinfo files still exist. Delete files from JR directory")
            self.log.info("*" * 20 + "Successfully Deleted cjinfo files from JR directory" + "*" * 20)
            self.log.info("*" * 20 + "Running Another INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Adding new files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            inc4_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Running backup copy for the cycle" + "*" * 20)
            snap_helper.backup_copy()
            snapconstants.source_path = snapconstants.test_data_path
            self.log.info("*" * 20 + "Running OutPlace Restore from Incremental Backup" + "*" * 20)
            snap_helper.tape_outplace(inc4_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)


            self.log.info("*" * 20 + "Running Data Aging on Snap copy" + "*" * 20)
            snap_helper.run_data_aging(snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Data Aging Validation on Snap copy" + "*" * 20)
            snap_helper.data_aging_validation(snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            snap_helper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            snap_helper.delete_array()
            if snapconstants.vplex_engine is True:
                """Deleting Vplex arrays"""
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName1']
                snap_helper.delete_array()
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName2']
                snap_helper.delete_array()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
            self.log.warning("Testcase and/or Restored vm cleanup was not completed")

