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
                            Snap Operations - Copy selection during Auxiliary Copy to perfrom mirror or vault.
"""

from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Snap Operations - Copy selection during Auxiliary Copy to perfrom mirror or vault"""

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
        self.name = """Automation : Copy selection during Auxiliary Copy to perfrom mirror or vault"""

    def run(self):
        """Main function for test case execution
        Steps:
            1. Add arrays and create intellisnap entities. set replica type as pvm.
            2. Enable skip catalog and disable inline backup copy and Run Full
               and incremental Snap backup.
            3. Run Auxilliary Copy job to only First Node. Verify the snap are
               replicated to only first node and not on second node.
            4. verify outplace restore from first node copy.
            5. Run Auxilliary Copy job to only Second Node. Verify the snap are
               replicated to second node.
            6. verify inplace restore from Second node copy.
            7. Cleanup entites and remove array entries.
        """

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(
                self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Primary Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snapconstants.username = self.tcinputs['ArrayUserName2']
            self.snapconstants.password = b64encode(
                self.tcinputs['ArrayPassword2'].encode()).decode()
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost2', None)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Second Array" + "*" * 20)
            self.snapconstants.arrayname = self.tcinputs['ArrayName3']
            self.snapconstants.username = self.tcinputs['ArrayUserName3']
            self.snapconstants.password = b64encode(
                self.tcinputs['ArrayPassword3'].encode()).decode()
            self.snapconstants.controlhost = self.tcinputs.get('ArrayControlHost3', None)
            self.snaphelper.add_array()
            self.log.info("*" * 20 + "Successfully Added Third Array" + "*" * 20)
            self.snapconstants.type = "pvm"  #setting pvm
            if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
                self.log.info("*" * 20 + "ADDING OCUM" + "*" * 20)
                self.snapconstants.arrayname = self.tcinputs['OCUMServerName']
                self.snapconstants.username = self.tcinputs['OCUMUserName']
                self.snapconstants.password = b64encode(
                    self.tcinputs['OCUMPassword'].encode()).decode()
                self.snapconstants.is_ocum = True
                self.snaphelper.add_array()
                self.log.info("Successfully Added OCUM Information")
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            full1_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            self.snapconstants.backup_level = 'INCREMENTAL'
            inc1_job = self.snaphelper.snap_backup()
            self.log.info("*" * 20 + "Running Auxilliary Copy job to only First Node" + "*" * 20)
            if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
                self.snaphelper.aux_copy(copy_name=self.snapconstants.first_node_copy)
            else:
                self.snaphelper.aux_copy(copy_name=self.snapconstants.first_node_copy, use_scale=True)
            self.log.info("Verifying if the Snap is created on Second Node")
            query = "SELECT SMVolumeID FROM SMVolume WHERE JobId = {a} AND CopyId = {b}"
            spcopy = self.snaphelper.spcopy_obj(self.snapconstants.second_node_copy)
            volumeid = self.snapconstants.execute_query(query, {'a': full1_job.job_id, 'b': spcopy.copy_id})
            if volumeid[0][0] not in [None, ' ', '']:
                raise Exception("Snap backups are replicated to Second Node too when the Aux copy"
                                "is run only to First node")
            else:
                self.log.info("Snap backups are not replicated to Second Node, we are good!")
            spcopy = self.snaphelper.spcopy_obj(self.snapconstants.first_node_copy)
            volumeid = self.snapconstants.execute_query(query, {'a': full1_job.job_id, 'b': spcopy.copy_id})
            if volumeid[0][0] in [None, ' ', '']:
                raise Exception("Snap backups are not replicated to First Node when the Aux copy"
                                "is run only to First node")
            else:
                self.log.info("Snap backups are replicated to First Node, we are good!")
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            self.log.info("*" * 20 + "Running OutPlace Restore from First Node Copy job" + "*" * 20)
            self.snaphelper.snap_outplace(4)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)

            self.log.info("*" * 20 + "Running Auxilliary Copy job to only Second Node" + "*" * 20)
            if self.snapconstants.type in {"pv", "pm", "pvm", "pmv", "pmm"}:
                self.snaphelper.aux_copy(copy_name=self.snapconstants.second_node_copy)
            else:
                self.snaphelper.aux_copy(copy_name=self.snapconstants.second_node_copy, use_scale=True)
            spcopy = self.snaphelper.spcopy_obj(self.snapconstants.second_node_copy)
            volumeid = self.snapconstants.execute_query(query, {'a': full1_job.job_id, 'b': spcopy.copy_id})
            if volumeid[0][0] in [None, ' ', '']:
                raise Exception("Snap backups are not replicated to Second Node when the Aux copy"
                                "is run only to Second node")
            else:
                self.log.info("Snap backups are replicated to Second Node, we are good!")
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.log.info("*" * 20 + "Running InPlace Restore from Second node Snap Backup" + "*" * 20)
            self.snaphelper.snap_inplace(5, inc1_job.start_time, inc1_job.end_time)
            self.snaphelper.inplace_validation(inc1_job.job_id, self.snapconstants.second_node_copy,
                                               self.snapconstants.test_data_path)

            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName3']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['OCUMServerName']
            self.snaphelper.delete_array()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
