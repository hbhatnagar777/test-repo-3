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
                            Snap Backup, backup Copy, Restores etc.
"""

from AutomationUtils import constants
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
            "Tape_lib_name": None,
            "drive_pool": None,
            "scratch_pool": None
            }
        self.name = """Automation : New Copy Creation Wizard with SP/Copy Created Using tape
                    library"""

    def run(self):
        """Main function for test case execution"""

        self.tcinputs['tape_lib'] = True
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_template = SNAPTemplate(
                self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            snap_template.snap_template4()


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
