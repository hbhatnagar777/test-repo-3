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

    run()               --   run function of this test case calls SnapHelper Class to execute and
                            Validate  Below Operations:
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount Unmount
                            Revert Delete etc."""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Skip catalog
       and Restore for Snap engine"""

    test_step = TestStep()

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
        self.name = """Template for Basic Acceptance Test of IntelliSnap backup and Restore for
                        Skip catalog and deferred catalog in the same cycle"""
        self.snapconstants = None
        self.snap_helper = None
    @test_step
    def backup_cycle(self):
        """ Runs three backup cycles"""

        self.snapconstants.backup_level = 'FULL'
        self.snap_helper.update_test_data(mode='add')
        full_job = self.snap_helper.snap_backup()
        self.snapconstants.backup_level = 'INCREMENTAL'
        self.snap_helper.update_test_data(mode='add')
        inc_job = self.snap_helper.snap_backup()
        self.log.info("**snap backup cycles run success**")
        return full_job, inc_job

    @test_step
    def restore_and_validate(self):
        """Outplace Restore and validation"""
        self.snap_helper.snap_outplace(1)
        self.snap_helper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                             self.snap_helper.client_machine)

    @test_step
    def tape_restore_and_validate(self, jobid, precedence, from_time, end_time):
        """Outplace Restore from tape copy and validation"""
        self.snap_helper.tape_outplace(jobid, precedence, from_time, end_time)
        self.snap_helper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                             self.snapconstants.windows_restore_client)

    @test_step
    def delete_and_validate(self, jobid, snap_copy_name):
        """Delete snap and validate"""
        self.snap_helper.delete_snap(jobid, snap_copy_name)
        self.snap_helper.delete_validation(jobid, snap_copy_name)

    def run(self):
        """Main function for test case execution
        run function of this test case calls SnapHelper Class to execute and Validate"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("Initializing pre-requisites setup for this test case")
            self.snap_helper.setup()
            self.snap_helper.update_storage_policy(enable_backup_copy=True, source_copy_for_snap_to_tape='Snap',
                                                   enable_snapshot_catalog=True,
                                                   source_copy_for_snapshot_catalog='Snap')
            self.snap_helper.add_array()
            self.snap_helper.add_test_data_folder()
            full1_job, inc1_job = self.backup_cycle()
            full2_job, inc2_job = self.backup_cycle()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.restore_and_validate()
            self.snap_helper.snapshot_cataloging()
            self.restore_and_validate()
            self.snap_helper.update_storage_policy(enable_backup_copy=True, source_copy_for_snap_to_tape='Snap')
            full3_job, inc3_job = self.backup_cycle()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.restore_and_validate()
            self.snap_helper.backup_copy()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.tape_restore_and_validate(inc3_job.job_id, 2, full3_job.start_time, inc3_job.end_time)
            self.snap_helper.aux_copy()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.tape_restore_and_validate(inc3_job.job_id, 3, full3_job.start_time, inc3_job.end_time)
            self.snapconstants.backup_level = 'FULL'
            self.snap_helper.update_test_data(mode='add')
            full4_job = self.snap_helper.snap_backup()
            self.snapconstants.skip_catalog = False
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snap_helper.update_test_data(mode='add')
            inc4_job = self.snap_helper.snap_backup()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.restore_and_validate()
            self.snap_helper.backup_copy()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.tape_restore_and_validate(inc4_job.job_id, 2, full4_job.start_time, inc4_job.end_time)
            self.snap_helper.aux_copy()
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.tape_restore_and_validate(inc4_job.job_id, 3, full4_job.start_time, inc4_job.end_time)
            self.delete_and_validate(inc4_job.job_id, self.snapconstants.snap_copy_name)
            self.log.info("****Cleanup of Snap Entities****")
            self.snap_helper.cleanup()
            self.snap_helper.delete_array()
            self.log.info("TestCase completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
