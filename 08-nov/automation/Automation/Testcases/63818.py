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
                            Snap Backup with content as Mountpath, backup Copy, using Recursive scan and restores from Tape copy

"""
import json
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
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
        self.name = """Automation : IFind Test cases for Intellisnap Backups using Recursive scan and mount path as content
                    """


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
            for path in snapconstants.subclient_content.split(","):
                if self.os_name.upper() == 'WINDOWS':
                    if len(path) < 4 or path.startswith("\\"):
                        raise Exception(
                            "Subclient Content Should be Mount Path not a Drive Letter and shouldn't start with \\\\,"
                            "add Mount path as content")
                else:
                    if not path.startswith("\\"):
                        raise Exception(
                            "Subclient Content Should be Mount Path not a Drive Letter, add Mount path as content")
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            snap_helper.setup()
            self.log.info("*" * 20 + "Setting the scan type as Recursive" + "*" * 20)
            snapconstants.subclient.scan_type = (1)

            #Step 1 Backups using Recursive scan and restore from Backup copy
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full1_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full1_job.job_id, snapconstants.snap_copy_name)

            snap_helper.update_test_data(mode='edit')
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Adding new files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            inc1_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Running backup copy for the cycle" + "*" * 20)
            snap_helper.backup_copy()
            snapconstants.source_path = snapconstants.test_data_path
            self.log.info("*" * 20 + "Running OutPlace Restore from Incremental Backup" + "*" * 20)
            snap_helper.tape_outplace(inc1_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)


            #Step 2: Cycle having empty incremental backup

            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full2_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full2_job.job_id, snapconstants.snap_copy_name)

            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job with no contents to backup" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            inc2_job = snap_helper.snap_backup()
            snap_helper.update_test_data(mode='edit')
            snap_helper.update_test_data(mode='add')
            self.log.info("*" * 20 + "Running Second INCREMENTAL Snap Backup after adding & modifying files" + "*" * 20)
            inc3_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Running backup copy for the cycle" + "*" * 20)
            snap_helper.backup_copy()
            self.log.info("*" * 20 + "Running OutPlace Restore from Tape Copy using latest browse" + "*" * 20)
            snap_helper.tape_outplace(inc3_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)



            #Step 3: Cycle having Differential Backup

            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full3_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full3_job.job_id, snapconstants.snap_copy_name)

            snap_helper.update_test_data(mode='edit')
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Adding new files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            inc4_job = snap_helper.snap_backup()
            snap_helper.update_test_data(mode='copy', path=snapconstants.test_data_path)
            snapconstants.backup_level = 'DIFFERENTIAL'
            self.log.info("*" * 20 + "Adding new files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            inc5_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Running backup copy for the cycle" + "*" * 20)
            snap_helper.backup_copy()
            # snapconstants.source_path = snapconstants.test_data_path
            self.log.info("*" * 20 + "Running OutPlace Restore from Incremental Backup" + "*" * 20)
            snap_helper.tape_outplace(inc4_job.job_id, 2, inc4_job.start_time, inc4_job.end_time)
            snap_helper.compare(snap_helper.client_machine,
                                snapconstants.windows_restore_client,
                                snapconstants.copy_content_location[0],
                                snapconstants.tape_outplace_restore_location)
            snap_helper.update_test_data(mode='delete', path=snapconstants.copy_content_location)
            self.log.info("*" * 20 + "Running OutPlace Restore from Differential Backup" + "*" * 20)
            snap_helper.tape_outplace(inc5_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)


            #Step 4 Restore of Deleted items

            self.log.info("*" * 20 + "Running Full Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'FULL'
            snap_helper.update_test_data(mode='add', path=snapconstants.test_data_path)
            full4_job = snap_helper.snap_backup()
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='copy', path=snapconstants.test_data_path)
            snap_helper.update_test_data(mode='delete', path=snapconstants.test_data_path)
            snap_helper.update_test_data(mode='add', path=snapconstants.test_data_path)
            inc6_job = snap_helper.snap_backup()
            snap_helper.backup_copy()

            i = 0
            for path in snapconstants.test_data_path:
                snapconstants.source_path = [path]
                self.log.info("*" * 20 + "Running OutPlace Restore from backup copy with "
                                         "Source Path: {0}".format(path) + "*" * 20)
                snap_helper.tape_outplace(inc6_job.job_id, 2, fs_options=True)
                snap_helper.compare(snap_helper.client_machine,
                                    snapconstants.windows_restore_client,
                                    snapconstants.copy_content_location[i],
                                    snapconstants.tape_outplace_restore_location)

                i = i + 1
            self.log.info("*" * 20 + "Restore of deleted data and Validation is "
                                     "Successful " + "*" * 20)
            snap_helper.update_test_data(mode='edit')
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            inc7_job = snap_helper.snap_backup()
            snap_helper.backup_copy()
            self.log.info("*" * 20 + "Running OutPlace Restore from Incremental Backup" + "*" * 20)
            snap_helper.tape_outplace(inc7_job.job_id, 2)
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
                """ Deleting Vplex arrays"""
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
