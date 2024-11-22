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
                            Snapbackup, Aux copy, backup copy and validate if Snapshots are getting deleted

    TC Steps:
    1. Add primary, secondary arrays. Create library, Storage Policy with Replica copy,
        and create a subclient
    2. Set Snap Primary and Snap Replica copy as Spool Copies
    3. Run Aux copy and validate if Snap Primary snapshot is deleted as snap copy was spool
    4. Run Backup copy where source of Backup copy is Replica copy and validate if snaps are
        deleted from Replica copy as it was spool
    5. Cleanup
                            """
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Spool Copy with Replication"""

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
        self.name = """Test Case for Basic Acceptance Test of IntelliSnap Spool copy with Replication"""
        self.snapconstants = None
        self.snaphelper = None

    def validate_spool_deletion(self, jobid, copyid):
        wait_time = 0
        while True:
            volumeid_val = self.snapconstants.execute_query(self.snapconstants.get_volumeid_da,
                                                            {'a': jobid, 'b': copyid})
            if volumeid_val[0][0] in [None, ' ', '']:
                break
            else:
                self.log.info("Sleeping for 2 minutes")
                time.sleep(120)
                wait_time += 2
            if wait_time > 4:
                raise Exception(
                    f'Snapshot of jobid: {jobid} is not yet deleted,'
                    'please check the CVMA logs'
                )



    def run(self):
        """Main function for test case execution
        run function of this test case calls SnapHelper Class to execute and Validate"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.tcinputs['ReplicationType'] = "pv_replica"

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
            spcopy = self.snaphelper.spcopy_obj(self.snapconstants.snap_copy_name)
            replica_copy = self.snaphelper.spcopy_obj(self.snapconstants.first_node_copy)
            # Set Backup copy source as Replica copy
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.first_node_copy)

            # Set Spool retention on both Snap Primary and Snap Replica copy
            spcopy.copy_retention = (0, 0, 0, 0)
            replica_copy.copy_retention = (0, 0, 0, 0)

            job = self.snaphelper.snap_backup()

            # Run Aux Copy and Validate if Snap copy snapshots are deleted within first 2 cleanups
            self.snaphelper.aux_copy()
            self.validate_spool_deletion(job.job_id, spcopy.copy_id)
            self.log.info(f'Snapshot for job {job.job_id} deleted successfully from Snap Copy')

            # Run Backup Copy and Validate if Replica copy snapshots are deleted within first 2 cleanups
            self.snaphelper.backup_copy()
            self.validate_spool_deletion(job.job_id, replica_copy.copy_id)
            self.log.info(f'Snapshot for job {job.job_id} deleted successfully from Replica copy')

            # set replica as non spool so that source of backup copy can be deleted

            replica_copy.copy_retention = (0, 1, 0)
            # Set Backup copy source as Replica copy
            self.snaphelper.update_storage_policy(
                enable_backup_copy=True,
                source_copy_for_snap_to_tape=self.snapconstants.snap_copy_name)

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
