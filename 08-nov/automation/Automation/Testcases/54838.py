# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case
TestCase is the only class definied in this file
TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants

class TestCase(CVTestCase):
    """windows snap testcase for extent level support for backupcopy
        This test case does the following
        Step 1 : Add the array in the array management. 
                 Skip this step if the array is already added
        Step 2 : Create backupset for this testcase if it doesn't exist.
                 Delete the backupset if exists.
        Step 3 : Create subclient.
        Step 4 : Enable intellisnap option on the subclient.
        Step 5 : Run a snapbackup for the subclient with and without catalog
                 and verify it completes without failures.
        Step 6 : Verify the subclientproperties file.
                 Return the value based on the Exten enable option in the file.
        Step 7 : Run a backup copy job.
        Step 8 : Verify the collects for extent validation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Extent based backup with Intellisnap with proxy'
        self.tcinputs = {
            "SubclientContent":None,
            "MediaAgentName": None,
            "SnapEngineAtSubclient": None
            }

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", format(self.id))
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.log.info("completed constants initialization")
            self.log.info("printing inputs %s, %s,%s,%s,%s",self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("completed initialization")
            self.log.info("subclient is %s", self.subclient)
            if self.tcinputs['Snap_Proxy'] == '' or self.tcinputs['Backupcopy_Proxy'] == '':
                self.snap_helper.snap_extent_template(False)
            else:
                self.snap_helper.snap_extent_template(True)
            self.status = constants.PASSED
        except Exception as excp:
            self.log.error('Failed with error: [%s]', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
