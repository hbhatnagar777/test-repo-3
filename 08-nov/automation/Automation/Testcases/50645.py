# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    run()               --   run function of this test case calls SnapHelper Class to execute and
                            Validate  Below Operations:
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount Unmount
                            Revert Delete etc."""
import datetime
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Selective backup copy"""

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
        self.name = """Test Case for Basic Acceptance Test of IntelliSnap selective copy"""
        self.snapconstants = None
        self.snap_helper = None

    def backup_cycle(self):
        """ Runs three backup cycles"""
        self.snapconstants.backup_level = 'FULL'
        full_job = self.snap_helper.snap_backup()
        hour_full_job = datetime.datetime.fromtimestamp(full_job.start_timestamp).hour
        self.snapconstants.backup_level = 'INCREMENTAL'
        inc_job = self.snap_helper.snap_backup()
        self.log.info("Successfully completed backup cycle")
        return full_job.job_id, inc_job.job_id, hour_full_job

    def validate_selective(self, selected_jobs):
        """Validates if jobs are backup copied based on selective copy"""
        backup_copied_jobs = []
        copied_jobs = self.snapconstants.execute_query\
            (self.snapconstants.get_backupcopied_jobs, {'a': self.snapconstants.subclient.subclient_id})
        for jobid_list in copied_jobs:
            for jobid in jobid_list:
                backup_copied_jobs.append(jobid)
        self.log.info("List of Jobs to be selected for Backup copy {0}".format(selected_jobs))
        self.log.info("List of jobs Backup copied during the TC {0}".format(backup_copied_jobs))
        if backup_copied_jobs == selected_jobs:
            self.log.info("Only hourly full jobs are copied as per selective copy rule")
        else:
            raise Exception("Copied jobs are not as per selective copy rule")

    def run(self):
        """Main function for test case execution
        run function of this test case calls SnapHelper Class to execute and Validate"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("Initializing pre-requisites setup for this test case")
            self.snap_helper.setup()

            self.log.info("Updating Storage Policy to have hourly full selective copy")
            self.snap_helper.update_storage_policy(enable_backup_copy=True, source_copy_for_snap_to_tape='Snap',
                                                   enable_selective_copy=10)
            self.snap_helper.add_array()
            # Running two cycles back to back to verify only first full selected for backup copy
            full1_job, inc1_job, hour_full1_job = self.backup_cycle()
            full2_job, inc2_job, hour_full2_job = self.backup_cycle()
            self.log.info("Sleeping for 1 hour to get next full selected for backup copy")
            time.sleep(3600)
            # Running two more cycles where full3 should be picked for backup copy
            full3_job, inc3_job, hour_full3_job = self.backup_cycle()
            full4_job, inc4_job, hour_full4_job = self.backup_cycle()
            all_snap_job = [full1_job, inc1_job, full2_job, inc2_job, full3_job, inc3_job, full4_job, inc4_job]
            self.snap_helper.backup_copy()

            """making a list of jobs which should be picked for backup copy based on hourly full
                and validate against jobs backup copied"""
            selected_jobs = [full1_job]
            if hour_full1_job != hour_full2_job:
                selected_jobs.append(full2_job)
            selected_jobs.append(full3_job)
            if hour_full3_job != hour_full4_job:
                selected_jobs.append(full4_job)

            self.validate_selective(selected_jobs)

            # delete all snaps created during the TC
            [self.snap_helper.delete_snap(snap_job, self.snapconstants.snap_copy_name) for snap_job in all_snap_job]

            self.log.info("****Cleanup of Snap Entities****")
            self.snap_helper.cleanup()
            self.snap_helper.delete_array()
            self.log.info("TestCase completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
