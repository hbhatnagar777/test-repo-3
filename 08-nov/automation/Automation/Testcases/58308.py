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
                            suspend and resume Open Replication aux copy job.
"""

from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing suspend and resume Open Replication aux copy job"""

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
        self.name = """Automation : suspend and resume Open Replication aux copy job"""

    def run(self):
        """Main function for test case execution
        Steps:
            1. Add arrays and create intellisnap entities. set replica type as pv_replica.
            2. Enable skip catalog and disable inline backup copy and Run Full Snap backup.
            3. Suspends job in each phase of both snap backup and backup copy.
            4. Run incremental snap backup which suspends snap and backup copy in each phase.
            5. Run Open replication Aux copy and after 30 seconds  suspends the job.
               wait for a minute and suspend again. Do this for 3 times.
            6. verify outplace restore from Aux copy.
            7. Set Vault copy as Source for backup copy. and run backup copy.
            8. verify outplace restore from backup copy.
            9. Force delete latest snapshot from snap and replica copy as it.
               may fail with snapmirror dependency.
            10. Set Snap copy as Source for backup copy
            11. Cleanup entites and remove array entries.
        """

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(
                self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.snapconstants.is_suspend_job = True
            self.log.info("Suspend job Option is set as : {0}".format(self.snapconstants.is_suspend_job))
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Primary Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = b64encode(
                self.tcinputs['ArrayPassword2'].encode()).decode()
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Secondary Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snapconstants.type = "pv_replica"
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
            self.snapconstants.skip_catalog = True  #disabling skip catalog
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            full1_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            self.snapconstants.backup_level = 'INCREMENTAL'
            inc1_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Running Auxilliary Copy job" + "*" * 20)
            if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
                self.snaphelper.aux_copy()
            else:
                self.snaphelper.aux_copy(use_scale=True)
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            self.log.info("*" * 20 + "Running OutPlace Restore from Aux Copy job" + "*" * 20)
            self.snaphelper.snap_outplace(4)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)
            self.log.info("*" * 20 + "Setting Vault copy as source for backup copy" + "*" * 20)
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.first_node_copy,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            self.snaphelper.backup_copy()
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(full1_job.job_id, 2)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)

            self.snaphelper.force_delete_snap(inc1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.force_delete_snap(inc1_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Disabling backup copy and snapshot catalogue" + "*" * 20)
            self.snaphelper.update_storage_policy()

            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()

            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
