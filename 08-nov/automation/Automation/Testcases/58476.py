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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.huaweibasicacceptance import HuaweiBasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("Huawei - V2 - Solaris MA-Basic Acceptance Test of NDMP Backup "
                     "and Restore")
        self.show_to_user = True
        self.tcinputs = {
            "AuxCopyMediaAgent": None,
            "AuxCopyLibrary": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "FilerRestoreLocation": None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info(f"Started executing {self.id} testcase")
            basic_acceptance = HuaweiBasicAcceptance(self)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error(f"Failed with error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED
