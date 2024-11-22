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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.cifssnapbasicacceptance import CIFSSnapBasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("NewAutomation NetApp - V2 - Windows MA - Basic Acceptance "
		              "Test of CIFS under NAS Intellisnap Backup and Restore for Multisite")
        self.tcinputs = {
            "AuxCopyMediaAgent": None,
            "AuxCopyLibrary": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "FilerRestoreLocation": None,
            "AuxCopyMediaAgent_2": None,
            "AuxCopyLibrary_2": None,
            "CIFSShareUser_2": None,
            "CIFSSharePassword_2": None,
            "FilerRestoreLocation_2": None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase")

            basic_acceptance = CIFSSnapBasicAcceptance(self)
            basic_acceptance.run()
            basic_acceptance.auxcopy_mediaagent = self.tcinputs['AuxCopyMediaAgent_2']
            basic_acceptance.auxcopy_library = self.tcinputs['AuxCopyLibrary_2']
            basic_acceptance.cifsshare_user = self.tcinputs['CIFSShareUser_2']
            basic_acceptance.cifsshare_password = self.tcinputs['CIFSSharePassword_2']
            basic_acceptance.filerrestore_location = self.tcinputs['FilerRestoreLocation_2']
            basic_acceptance.run()



        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
