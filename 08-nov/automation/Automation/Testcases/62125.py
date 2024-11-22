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
                            Snap Backup, backup Copy,  Synthetic full backup and restores and verifies TrueUp
                            Functionality
"""
import json
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of True Up validation for Snap file system backups test case
    """

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
        self.name = """Automation : True Up validation for Snap file system backups
                    """


    def run(self):
        """Main function for test case execution"""


        try:
            self.log.info(f'Started executing {self.id} testcase')
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            self.client_machine = Machine(self.client)
            self.os_name = self.client_machine.os_info
            self.log.info("*" * 20 + "Adding Additional settings to enable Synth Full feature for Intellisnap" + "*" * 20)
            self.commcell.add_additional_setting("CommServDB.Console", "bEnableFSSnapSyntheticFull", "BOOLEAN", "true")
            self.commcell.add_additional_setting("CommServDB.GxGlobalParam", "FSSnapSCSynthFull", "INTEGER", "1")
            if self.os_name == 'WINDOWS':
                self.client.add_additional_setting("FileSystemAgent", "bRunTrueUpJob", "INTEGER", "0")
                self.log.info("Successfully added the Additional Settings")
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
                snapconstants.password = b64encode(snapconstants.tcinputs['BackendArrayPassword1'].encode()).decode()
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendArrayControlHost1', None)
                snapconstants.snap_engine_at_array = snapconstants.tcinputs['BackendSnapEngineAtArray']
                snap_helper.add_array()
                """ Adding Second Backend array """
                self.log.info("*" * 20 + "Adding Second backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName2']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName2']
                snapconstants.password = b64encode(snapconstants.tcinputs['BackendArrayPasswd2'].encode()).decode()
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendControlHost2', None)
                snap_helper.add_array()
            """ Re-Set arrayname and engine Name as primary """
            snapconstants.arrayname = snapconstants.tcinputs['ArrayName']
            snapconstants.snap_engine_at_array = snapconstants.tcinputs['SnapEngineAtArray']
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            snap_helper.setup()
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snapconstants.inline_bkp_cpy = True
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full1_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full1_job.job_id, snapconstants.snap_copy_name)
            self.log.info("Validating job to check if TrueUp is run")
            trueup_check = snap_helper.verify_trueup(full1_job)
            if trueup_check:
                self.log.info("TrueUp ran for Full job. Failing the TC")
                raise Exception("Failing the test case. Please check the logs")
            else:
                self.log.info("TrueUp didnt run for Full job. This is expected")

            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            self.log.info("*" * 20 + "Renaming files and folders before the backup" + "*" * 20)
            snap_helper.update_test_data(mode='edit', rename=True)
            inc1_job = snap_helper.snap_backup()
            self.log.info("Validating job to check if TrueUp is run")
            trueup_check = snap_helper.verify_trueup(inc1_job)
            if trueup_check:
                self.log.info("TrueUp ran for Inc job. Failing the TC")
                raise Exception("Failing the test case. Please check the logs")
            else:
                self.log.info("TrueUp didnt run for Inc job as expected")
            snapconstants.backup_level = 'Synthetic_full'
            self.log.info("*" * 20 + "Running Synthetic Full backup" + "*" * 20)
            snapconstants.inline_bkp_cpy = False
            full2_job = snap_helper.snap_backup()
            self.log.info("Validating job to check if TrueUp is run for Synth Full job")
            trueup_check = snap_helper.verify_trueup(full2_job)
            if trueup_check:
                self.log.info("TrueUp ran for Inc job. Failing the TC")
                raise Exception("Failing the test case. Please check the logs")
            else:
                self.log.info("TrueUp didnt run for Inc job as expected")
            self.log.info(
                "*" * 20 + "Running Incremental Snap backup with Inline Backup copy after Synth Full" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snapconstants.inline_bkp_cpy = True
            snap_helper.update_test_data(mode='add')
            self.log.info("*" * 20 + "Deleting data using index browse" + "*" * 20)
            bkupset = self.agent.backupsets.get(snapconstants.backupset_name)
            for path in snapconstants.test_data_path:
                bkupset.delete_data(path)
            inc2_job = snap_helper.snap_backup()
            self.log.info("Validating job to check if TrueUp is run")
            trueup_check = snap_helper.verify_trueup(inc2_job)
            if trueup_check:
                self.log.info("TrueUp ran for Inc job as this is first incremental after Synth full")
            else:
                self.log.info("TrueUp didnt run for Inc job")
                raise Exception("Failing the test case as first incremental after "
                                "synth full didnt run trueUp. Please check the self.logs")
            snapconstants.source_path = snapconstants.test_data_path
            self.log.info("*" * 20 + "Running OutPlace Restore from Tape Copy" + "*" * 20)
            snap_helper.tape_outplace(inc2_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)
            if self.os_name == 'WINDOWS':
                self.log.info("*" * 20 + "Deleting data using index browse" + "*" * 20)
                bkupset = self.agent.backupsets.get(snapconstants.backupset_name)
                for path in snapconstants.test_data_path:
                    bkupset.delete_data(path)
                self.log.info("Successfully deleted the data from index")
                self.log.info("*" * 20 + "Running Second INCREMENTAL Snap Backup with Inline Backup copy job" + "*" * 20)
                snapconstants.backup_level = 'INCREMENTAL'
                snap_helper.update_test_data(mode='edit')
                self.log.info("*" * 20 + "Adding Additional settings to run TrueUp job" + "*" * 20)
                self.client.add_additional_setting("FileSystemAgent", "bRunTrueUpJob", "INTEGER", "1")
                self.log.info("Successfully added the Additional Settings")
                inc3_job = snap_helper.snap_backup()
                trueup_check = snap_helper.verify_trueup(inc3_job)
                if trueup_check:
                    self.log.info("TrueUp ran for Inc job as Additional setting is set,")
                else:
                    self.log.info("TrueUp didnt run for Inc job")
                    raise Exception(
                        "Failing the test case as trueUp didnt run . Please check the logs")
                snapconstants.source_path = snapconstants.test_data_path
                self.log.info("*" * 20 + "Running OutPlace Restore from Incremetnal Backup" + "*" * 20)
                snap_helper.tape_outplace(inc3_job.job_id, 2, inc3_job.start_time, inc3_job.end_time)
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

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            try:
                self.log.info("*" * 20 + "Cleaning up the additional settings" + "*" * 20)
                self.commcell.delete_additional_setting("CommServDB.Console", "bEnableFSSnapSyntheticFull")
                self.commcell.delete_additional_setting("CommServDB.GxGlobalParam", "FSSnapSCSynthFull")
                if self.os_name == 'WINDOWS':
                    self.client.delete_additional_setting("FileSystemAgent", "bRunTrueUpJob")
                self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
