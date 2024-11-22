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
                            suspend and resume Snap Backup without Catalog and Backup Copy.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing suspend and resume Snap Backup without Catalog and Backup Copy"""

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
        self.name = """Automation : suspend and resume Snap Backup without Catalog and Backup Copy"""

    def run(self):
        """Main function for test case execution
        Steps:
            1. Add arrays and create intellisnap entities.
            2. Enable both skip catalog and inline backup copy and Run Full inline Snap backup.
            3. Suspends job in each phase of both snap backup and backup copy.
            4. verify outplace restore from snap backup.
            5. Run inline incremental snap backup which suspends snap and backup copy in each phase.
            6. verify inplace restore from snap.
            7. Enable deffered catalog and run snapshot cataloging which suspends the job in each phase.
            8. disable inline backup and run Full snap backup followed by offline backup copy
                which suspends the job in each phase.
            9. verify outplace restore from backup copy followed by run snapshot cataloging for
                remaining jobs.
            10. Cleanup entites and remove array entries.
        """

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(
                self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("self.is_suspend_job : {0}".format(self.snapconstants.is_suspend_job))
            self.snapconstants.is_suspend_job = True
            self.log.info("Suspend job Option is : {0}".format(self.snapconstants.is_suspend_job))
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Primary Array" + "*" * 20)
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
            self.snapconstants.skip_catalog = True  #enabling skip catalog
            self.snapconstants.inline_bkp_cpy = True  #enabling inline backup copy
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            self.snaphelper.update_test_data(mode='add')
            full1_job = self.snaphelper.snap_backup()
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
            #deferred catalog
            self.log.info("*" * 20 + "Enable deferred catalog" + "*" * 20)
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.snap_copy_name,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Running deferred catalog from Storage Policy" + "*" * 20)
            self.snaphelper.snapshot_cataloging()
            self.snapconstants.inline_bkp_cpy = False  #disable skip catalog
            self.snapconstants.backup_level = 'FULL'
            self.snaphelper.update_test_data(mode='add')
            full2_job = self.snaphelper.snap_backup()
            #Backup copy
            self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            self.snaphelper.backup_copy()
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(full2_job.job_id, 2, full2_job.start_time, full2_job.end_time)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            self.log.info("*" * 20 + "Running deferred catalog from Storage Policy" + "*" * 20)
            self.snaphelper.snapshot_cataloging()
            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.snaphelper.delete_array()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
