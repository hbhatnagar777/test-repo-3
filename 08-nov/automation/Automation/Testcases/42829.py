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

Steps:

1. create entities with protection_type for default vault Replica
2. Run snap backup
3. restore using 0 precedence from snap copy and validate

4. Run Aux copy 
5. set PV copy as source for backup copy
5. delete primary snapshot 
6. run DA, wait for primary snap to age
7. restore using 0 precedence from vault copy

8. Run backup copy from Vault
9. delete vault snapshot 
10. Run DA, wait for vault snap to age.
11. restore using 0 precedence from backup copy

12. set spool option on Backup copy - 0,0,0
13. Run aux copy to synchronous copy
14. Run DA, wait for tape job to age
15. restore using 0 precedence from aux copy

16. disable backup copy to age vault copy.
17. delete entities.

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Restores from default precedence"""

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
        self.name = """Automation : Basic Acceptance Test for IntelliSnap Restores from default precedence"""

    def run(self):
        """Main function for test case execution"""

        self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
        self.snaphelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)

        try:
            self.snapconstants.type = "pv_replica"
            self.name = self.name.format(self.tcinputs.get("SnapEngineAtArray"))
            self.log.info("Started executing {0} testcase".format(self.id))

            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added First Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs.get('ArrayName2')
            self.snapconstants.username = self.tcinputs.get('ArrayUserName2')
            self.snapconstants.password = self.tcinputs.get('ArrayPassword2')
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)

            self.snapconstants.arrayname = self.tcinputs.get('ArrayName')
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            self.log.info("*" * 20 + "Running FIRST FULL Snap Backup job" + "*" * 20)
            full1_job = self.snaphelper.snap_backup()
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job using Precedence 0" + "*" * 20)
            self.snaphelper.snap_outplace(0)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)

            self.log.info("*" * 20 + "Running Aux copy to Vault" + "*" * 20)
            self.snaphelper.aux_copy(use_scale=True)
            self.log.info("*" * 20 + "Setting vault copy as Source for backup copy" + "*" * 20)
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.first_node_copy,
                enable_snapshot_catalog=True,
                source_copy_for_snapshot_catalog=self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Deleting Primary Snapshot" + "*" * 20)
            self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.snaphelper.delete_validation(full1_job.job_id, self.snapconstants.snap_copy_name)
            self.log.info("*" * 20 + "Running Data Aging" + "*" * 20)
            self.snaphelper.run_data_aging()
            self.log.info("*" * 20 + "Sleeping for 5minutes" + "*" * 20)
            time.sleep(300)
            self.log.info("*" * 20 + "Running OutPlace Restore from Vault job using Precedence 0" + "*" * 20)
            self.snaphelper.snap_outplace(0)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)

            self.log.info("*" * 20 + "Running Backup Copy from vault" + "*" * 20)
            self.snaphelper.backup_copy()
            self.log.info("*" * 20 + "Deleting Vault Snapshot" + "*" * 20)
            self.snaphelper.delete_snap(full1_job.job_id, self.snapconstants.first_node_copy)
            self.snaphelper.delete_validation(full1_job.job_id, self.snapconstants.first_node_copy)
            self.log.info("*" * 20 + "Running Data Aging" + "*" * 20)
            self.snaphelper.run_data_aging()
            self.log.info("*" * 20 + "Sleeping for 5minutes" + "*" * 20)
            time.sleep(300)
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup copy job using Precedence 0" + "*" * 20)
            self.snaphelper.tape_outplace(full1_job.job_id, 0)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)

            self.log.info("*" * 20 + "Setting spool option on Primary Copy" + "*" * 20)
            copy_name = "Primary"
            spcopy = self.snaphelper.spcopy_obj(copy_name)
            spcopy.copy_retention = (0, 0, 0)
            self.log.info("*" * 20 + "Running Aux copy to sync copy" + "*" * 20)
            self.snaphelper.aux_copy()
            self.log.info("*" * 20 + "Running Data Aging" + "*" * 20)
            self.snaphelper.run_data_aging()
            self.log.info("*" * 20 + "Sleeping for one minute" + "*" * 20)
            time.sleep(60)
            self.log.info("*" * 20 + "Running OutPlace Restore from Aux copy job using Precedence 0" + "*" * 20)
            self.snaphelper.tape_outplace(full1_job.job_id, 0)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            self.log.info("*" * 20 + "Setting back snap copy as Source for backup copy" + "*" * 20)
            self.snaphelper.update_storage_policy()

            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()

            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
