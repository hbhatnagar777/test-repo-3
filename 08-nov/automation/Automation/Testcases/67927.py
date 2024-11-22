# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection Full
        This executes test case 52631 with optimized scan
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("File System Data Protection - Full")
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Loading test case module 67929")
            test_case = CVTestCase.loadTestcaseObject("67929")
            test_case.id = self.id
            test_case.commcell = self.commcell
            self.tcinputs['VerifyDC'] = True
            self.tcinputs['SkipClassic'] = True
            self.tcinputs['OnlyFull'] = True
            self.tcinputs['OnlyDC'] = True
            self.tcinputs['NoOfStreams'] = 10
            self.tcinputs['FolderTimeStamp'] = False
            self.tcinputs['SkipLink'] = True
            test_case.tcinputs = self.tcinputs
            self.log.info("Executing test case 67929 with Scan Optimization")
            test_case.execute()
            self.result_string = test_case.result_string
            self.status = test_case.status

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
