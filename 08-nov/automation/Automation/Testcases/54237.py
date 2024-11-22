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
                            Snap Backup, backup Copy,  Synthetic full backup and restores
"""
import json
from base64 import b64encode
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants

class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Synthetic full backup and Restore test case
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
        self.name = """Automation : Basic Acceptance Test for Synthetic backup and restore
                    """

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, snapconstants)

            log.info("*" * 20 + "Adding Additional settings to enable Synth Full feature for Intellisnap" + "*" * 20)
            self.commcell.add_additional_setting("CommServDB.Console", "bEnableFSSnapSyntheticFull", "BOOLEAN", "true")
            self.commcell.add_additional_setting("CommServDB.GxGlobalParam", "FSSnapSCSynthFull", "INTEGER", "1")
            log.info("Successfully added the Additional Settings")
            log.info("*" * 20 + "Adding Arrays" + "*" * 20)
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
                log.info("*" * 20 + "Adding backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName1']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName1']
                snapconstants.password = b64encode(snapconstants.tcinputs['BackendArrayPassword1'].encode()).decode()
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendArrayControlHost1', None)
                snapconstants.snap_engine_at_array = snapconstants.tcinputs['BackendSnapEngineAtArray']
                snap_helper.add_array()
                """ Adding Second Backend array """
                log.info("*" * 20 + "Adding Second backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName2']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName2']
                snapconstants.password = b64encode(snapconstants.tcinputs['BackendArrayPasswd2'].encode()).decode()
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendControlHost2', None)
                snap_helper.add_array()
            """ Re-Set arrayname and engine Name as primary """
            snapconstants.arrayname = snapconstants.tcinputs['ArrayName']
            snapconstants.snap_engine_at_array = snapconstants.tcinputs['SnapEngineAtArray']
            log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            snap_helper.setup()
            log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            snapconstants.skip_catalog = True
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full1_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full1_job.job_id, snapconstants.snap_copy_name)
            log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            inc1_job = snap_helper.snap_backup()
            log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            snap_helper.backup_copy()
            snapconstants.backup_level = 'Synthetic_full'
            full2_job = snap_helper.snap_backup()
            snapconstants.source_path = snapconstants.test_data_path
            log.info("*" * 20 + "Running OutPlace Restore from Synth Full Backup" + "*" * 20)
            snap_helper.tape_outplace(full2_job.job_id, 2, full2_job.start_time, full2_job.end_time)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)
            log.info(
                "*" * 20 + "Running Incremental Snap backup with Inline Backup copy after Synth Full" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snapconstants.inline_bkp_cpy = True
            snap_helper.update_test_data(mode='add')
            inc2_job = snap_helper.snap_backup()
            log.info("*" * 20 + "Running OutPlace Restore from Tape Copy" + "*" * 20)
            snap_helper.tape_outplace(inc2_job.job_id, 2)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)
            
            log.info("*" * 20 + "Running Second INCREMENTAL Snap Backup with Inline Backup copy job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            inc3_job = snap_helper.snap_backup()
            log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
            snap_helper.aux_copy()
            snapconstants.inline_bkp_cpy = False
            snapconstants.backup_level = 'Synthetic_full'
            full3_job = snap_helper.snap_backup()
            snapconstants.source_path = snapconstants.test_data_path
            log.info("*" * 20 + "Running OutPlace Restore from Synth Full Backup" + "*" * 20)
            snap_helper.tape_outplace(full3_job.job_id, 2, full3_job.start_time, full3_job.end_time)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)
            log.info(
                "*" * 20 + "Running Incremental Snap backup with Skip catalog and Inline Backup copy job after Synth Full" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snapconstants.inline_bkp_cpy = True
            snap_helper.update_test_data(mode='add')
            inc4_job = snap_helper.snap_backup()
            log.info("*" * 20 + "Running Second INCREMENTAL Snap Backup with Skip catalog and Inline Backup copy job" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            inc5_job = snap_helper.snap_backup()
            snapconstants.inline_bkp_cpy = False
            snapconstants.backup_level = 'Synthetic_full'
            full4_job = snap_helper.snap_backup()
            snapconstants.source_path = snapconstants.test_data_path
            log.info("*" * 20 + "Running OutPlace Restore from Synth Full Backup" + "*" * 20)
            snap_helper.tape_outplace(full4_job.job_id, 2, full4_job.start_time, full4_job.end_time)
            snap_helper.outplace_validation(snapconstants.tape_outplace_restore_location,
                                            snapconstants.windows_restore_client)
            log.info("*" * 20 + "Running Data Aging on Snap copy" + "*" * 20)
            snap_helper.run_data_aging(snapconstants.snap_copy_name)
            log.info("*" * 20 + "Data Aging Validation on Snap copy" + "*" * 20)
            snap_helper.data_aging_validation(snapconstants.snap_copy_name)
            log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            snap_helper.cleanup()
            log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            snap_helper.delete_array()
            if snapconstants.vplex_engine is True:
                """ Deleting Vplex arrays"""
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName1']
                snap_helper.delete_array()
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName2']
                snap_helper.delete_array()
            self.commcell.delete_additional_setting("CommServDB.Console", "bEnableFSSnapSyntheticFull")
            self.commcell.delete_additional_setting("CommServDB.GxGlobalParam", "FSSnapSCSynthFull")
            log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
