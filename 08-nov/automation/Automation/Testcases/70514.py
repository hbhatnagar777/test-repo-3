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

    run()               --  run function of this test case validate below steps
    
Steps:
1. Create storage policy or plan with primary snap copy and run few snap backups.
2. create  2 vault/replica copies for NetApp fanout relationship.
3. start 2 different aux copy jobs to replicate same primary snap to both vault/replica copies.
4. aux copies should not wait for each other and run in parallel.
5. Validate snaps on replicate copy by Mounting and Unmounting snaps.
6. Cleanup.
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Bparallel auxcopy using different aux copy jobs
        on same Storage Policy from same copy to different target copies"""

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
        self.name = """Automation case for parallel auxcopy using different aux copy jobs
            on same Storage Policy from same copy to different target copies"""
        self.snapconstants = None
        self.snap_helper = None

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        self.tcinputs['ReplicationType'] = "pv_replica"

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("Initializing pre-requisites setup for this test case")
            self.snap_helper.setup()

            #Create another replica copy
            self.log.info("*" * 20 + "Creating another replica copy" + "*" * 20)
            self.snapconstants.second_node_copy = self.snap_helper.create_secondary_snap_copy(
                    self.snapconstants.snap_copy_name, replica_vault=True)
            if self.snapconstants.snap_engine_at_array == "NetApp":
                self.snap_helper.svm_association(self.snapconstants.second_node_copy,
                                     self.snapconstants.arrayname,
                                     self.tcinputs['ArrayName2'])
            self.snap_helper.disable_auxcpy_schedule()

            #Run backups
            self.snap_helper.add_test_data_folder()
            self.snapconstants.backup_level = 'FULL'
            self.snap_helper.update_test_data(mode='add')
            self.log.info("*" * 20 + "Running Full snapbackup job" + "*" * 20)
            full1_job = self.snap_helper.snap_backup()
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snap_helper.update_test_data(mode='add')
            self.log.info("*" * 20 + "Running Incremental snap job" + "*" * 20)
            inc1_job = self.snap_helper.snap_backup()

            #Run Aux copies
            self.log.info("*" * 20 + "Running Auxilliary Copy job for First vault copy" + "*" * 20)
            auxjob1 = self.snapconstants.storage_policy.run_aux_copy(
                self.snapconstants.first_node_copy, str(self.tcinputs['MediaAgent']), use_scale=True)
            self.log.info("*" * 20 + "Running Auxilliary Copy job for Second vault copy" + "*" * 20)
            auxjob2 = self.snapconstants.storage_policy.run_aux_copy(
                self.snapconstants.second_node_copy, str(self.tcinputs['MediaAgent']), use_scale=True)
            self.log.info("Started Aux copy job with job id: " + str(auxjob1.job_id))
            self.log.info("Started Aux copy job with job id: " + str(auxjob2.job_id))
            if not auxjob1.wait_for_completion():
                raise Exception("Failed to run aux copy job with error: " + str(auxjob1.delay_reason))
            if auxjob1.status != 'Completed':
                raise Exception(
                    "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                        auxjob1.job_id, auxjob1.delay_reason)
                )
            self.log.info("Successfully finished Aux copy job: {0}".format(auxjob1.job_id))

            if not auxjob2.wait_for_completion():
                raise Exception("Failed to run aux copy job with error: " + str(auxjob2.delay_reason))
            if auxjob2.status != 'Completed':
                raise Exception(
                    "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                        auxjob2.job_id, auxjob2.delay_reason)
                )
            self.log.info("Successfully finished Aux copy job: {0}".format(auxjob2.job_id))

            #mount/unmount validations from both vaults
            self.log.info("*" * 20 + "Mount Snap and its Validation from FIRST node" + "*" * 20)
            self.snap_helper.mount_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
            self.snap_helper.mount_validation(inc1_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "UnMount Snap and its Validation from FIRST node" + "*" * 20)
            self.snap_helper.unmount_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
            self.snap_helper.unmount_validation(inc1_job.job_id, self.snapconstants.first_node_copy)

            self.log.info("*" * 20 + "Mount Snap and its Validation from SECOND node" + "*" * 20)
            self.snap_helper.mount_snap(full1_job.job_id, self.snapconstants.second_node_copy)
            self.snap_helper.mount_validation(full1_job.job_id, self.snapconstants.second_node_copy)
            self.log.info("*" * 20 + "UnMount Snap and its Validation from SECOND node" + "*" * 20)
            self.snap_helper.unmount_snap(full1_job.job_id, self.snapconstants.second_node_copy)
            self.snap_helper.unmount_validation(full1_job.job_id,
                                               self.snapconstants.second_node_copy)

            #cleanup
            self.snapconstants.type = "fanout"
            self.log.info("****Cleanup of Snap Entities****")
            self.snap_helper.cleanup()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
