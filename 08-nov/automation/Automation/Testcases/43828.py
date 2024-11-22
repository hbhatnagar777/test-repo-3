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
                            Snapbackup and Aux copy
    backup_cycle()      --  Method to run one full cycle
    validate_selective()--  Method to verify if correct list of full jobs are aux copied based on seletive Rule

    TC Steps:
    1. Add primary, secondary arrays. Create library, Storage Policy with Replica copy(hourly full)
        and create a subclient
    2. Run two cycles of snapbackup and sleep for an hour then run two cycles of snapbackups again
    3. Run Aux copy and validate if right list of jobs are aux copies based on hourly selective rule
    4. Delete all created snapshots and entities
                            """
import datetime
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Selective Aux copy"""

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
        self.snaphelper = None

    def backup_cycle(self):
        """ Runs three backup cycles"""
        self.snapconstants.backup_level = 'FULL'
        full_job = self.snaphelper.snap_backup()
        hour_full_job = datetime.datetime.fromtimestamp(full_job.start_timestamp).hour
        self.snapconstants.backup_level = 'INCREMENTAL'
        inc_job = self.snaphelper.snap_backup()
        self.log.info("Successfully completed backup cycle")
        return full_job.job_id, inc_job.job_id, hour_full_job

    def validate_selective(self, selected_jobs):
        """Validates if jobs are backup copied based on selective copy"""
        aux_copied_jobs = []
        sp_copy = self.snaphelper.spcopy_obj(self.snapconstants.first_node_copy)
        copied_jobs = self.snapconstants.execute_query\
            (self.snapconstants.get_auxcopied_jobs, {'a': self.snapconstants.subclient.subclient_id,
                                                     'b': sp_copy.copy_id})
        for jobid_list in copied_jobs:
            for jobid in jobid_list:
                if jobid not in aux_copied_jobs:
                    aux_copied_jobs.append(jobid)
        self.log.info("List of Jobs to be selected for Aux copy {0}".format(selected_jobs))
        self.log.info("List of jobs Aux copied during the TC {0}".format(aux_copied_jobs))
        if aux_copied_jobs == selected_jobs:
            self.log.info("Only hourly full jobs are copied as per selective copy rule")
        else:
            raise Exception("Copied jobs are not as per selective copy rule")

    def run(self):
        """Main function for test case execution
        run function of this test case calls SnapHelper Class to execute and Validate"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.tcinputs['ReplicationType'] = "pv_replica"
            self.tcinputs['selectiveRule'] = "262144"

            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("Initializing pre-requisites setup for this test case")


            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
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
            if self.snapconstants.target_config is not None:
                self.snaphelper.edit_array(self.snapconstants.arrayname,
                                           self.snapconstants.target_config,
                                           self.snapconstants.config_update_level,
                                           array_access_node=self.snapconstants.array_access_nodes_to_edit)

            self.snaphelper.setup()

            # Running two cycles back to back to verify only first full selected for Aux Copy
            full1_job, inc1_job, hour_full1_job = self.backup_cycle()
            full2_job, inc2_job, hour_full2_job = self.backup_cycle()
            self.log.info("Sleeping for 1 hour to get next full selected for Aux copy")
            time.sleep(3600)
            # Running two more cycles where full3 should be picked for Aux copy
            full3_job, inc3_job, hour_full3_job = self.backup_cycle()
            full4_job, inc4_job, hour_full4_job = self.backup_cycle()
            all_snap_job = [full1_job, inc1_job, full2_job, inc2_job, full3_job, inc3_job, full4_job, inc4_job]
            self.snaphelper.aux_copy()

            """making a list of jobs which should be picked for Aux copy based on hourly full
                and validate against jobs aux copied"""
            selected_jobs = [full1_job]
            if hour_full1_job != hour_full2_job:
                selected_jobs.append(full2_job)
            selected_jobs.append(full3_job)
            if hour_full3_job != hour_full4_job:
                selected_jobs.append(full4_job)

            self.validate_selective(selected_jobs)

            # delete all snaps created during the TC
            [self.snaphelper.delete_snap(snap_job, self.snapconstants.snap_copy_name) for snap_job in all_snap_job]
            [self.snaphelper.delete_snap(snap_job, self.snapconstants.first_node_copy) for snap_job in all_snap_job]

            self.log.info("****Cleanup of Snap Entities****")
            self.snaphelper.cleanup()
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snaphelper.delete_array()
            self.log.info("TestCase completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
