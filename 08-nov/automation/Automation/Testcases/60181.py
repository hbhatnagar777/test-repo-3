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
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount Unmount
                            Revert Delete etc.
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaptemplates import SNAPTemplate
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap backup and Restore test case
    for Netapp Array"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None,
            "MediaAgent_2": None,
            "SubclientContent_2": None,
            "SnapAutomationOutput_2": None,
            "SnapEngineAtArray_2": None,
            "SnapEngineAtSubclient_2": None

        }
        self.name = """Automation : Basic Acceptance Test for IntelliSnap backup and restore
                    for Netapp Array"""

    def run(self):
        """Main function for test case execution"""


        try:
            self.log.info("Started executing {0} testcase")


            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_template = SNAPTemplate(self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            snapconstants.multisite = True
            snap_template.snap_template1()
            snapconstants.mediaagent = self.tcinputs['MediaAgent_2']
            snapconstants.subclient_content = self.tcinputs['SubclientContent_2']
            snapconstants.snapautomation_output = self.tcinputs['SnapAutomationOutput_2']
            snapconstants.snap_engine_at_array = self.tcinputs['SnapEngineAtArray_2']
            snapconstants.snap_engine_at_subclient = self.tcinputs['SnapEngineAtSubclient_2']
            snap_template.snap_template1()


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
