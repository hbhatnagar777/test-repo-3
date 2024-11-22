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
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount, Unmount,
                            Delete for SRDF Metro/HDS GAD/ Infinidat active-active replication.
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaptemplates import SNAPTemplate
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class TestCase(CVTestCase):
    """Class for executing acceptance test of IntelliSnap VMAX SRDF/Metro or Infinidat Active-Active or
     Hitachi GAD replication"""

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


    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)

            if self.tcinputs['SnapEngineAtArray'] == 'Dell EMC PowerMAX / VMAX / Symmetrix':
                self.name = """Automation : Verifies SRDF/Metro Replication backup using snap engine {0}""".format(
                    self.tcinputs['SnapEngineAtSubclient']
                )
            elif self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
                self.name = """Automation : Verifies GAD Replication backup using snap engine {0}""".format(
                    self.tcinputs['SnapEngineAtSubclient']
                )
            elif self.tcinputs['SnapEngineAtArray'] == 'INFINIDAT':
                self.name = "Automation :Verifies Infindat active-active replication backup using snap engine {0}""".format(
                    self.tcinputs['SnapEngineAtSubclient'])
            elif self.tcinputs['SnapEngineAtArray'] == 'Pure Storage FlashArray':
                self.name = "Automation :Verifies Pod volume secondary snapshot backup using snap engine {0}""".format(
                    self.tcinputs['SnapEngineAtSubclient'])

            snap_template = SNAPTemplate(
                self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            snap_template.snap_template5()

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
