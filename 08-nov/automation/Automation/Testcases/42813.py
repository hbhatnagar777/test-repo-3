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
                            Interruptions during vault or mirror operations due to snapprotect
                            processes issues.
"""

from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Interruptions during vault or mirror operations due
    to snapprotect processes issues"""

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
        self.name = """Automation : Interruptions during vault or mirror
        operations due to snapprotect processes issues"""

    def run(self):
        """Main function for test case execution
        Steps:
            1. Add arrays and create intellisnap entities. set replica type as pv.
            2. Enable skip catalog and disable inline backup copy and Run Full Snap backup.
            3. Run incremental snap backup.
            4. Run Aux copy and after 150 seconds  kill AuxCopy process. wait
               for 30secs and check if the process is killed. Do this for 4 times.
            5. Sleep for 3 minutes and resume the aux copy job.
            6. verify outplace restore from Aux copy.
            7. Cleanup entites and remove array entries.
        """

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(
                self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.snapconstants.is_kill_process = True
            self.log.info("kill process is set to : {0}".format(self.snapconstants.is_kill_process))
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
            self.snapconstants.type = "pv"
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

            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['ArrayName2']
            self.snaphelper.delete_array()
            self.snapconstants.arrayname = self.tcinputs['OCUMServerName']
            self.snaphelper.delete_array()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
