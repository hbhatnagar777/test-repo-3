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
    """Class for executing Basic acceptance test of IntelliSnap replication cases for
    Hitachi Thin Image (CCI) engine"""

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
        self.name = """Automation : SnapShot Replication: Verifies replication cases
        for Hitachi Thin Image (CCI) engine"""

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        self.tcinputs['ReplicationType'] = "pv_replica"
        self.tcinputs['skip_revert'] = True # setting revert flag to skip revert operation for this engine

        try:
            log.info("Started executing {0} testcase".format(self.id))
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_template = SNAPTemplate(
                self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            snap_template.snap_template2()


        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED