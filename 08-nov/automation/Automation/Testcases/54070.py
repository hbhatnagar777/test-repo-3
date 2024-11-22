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
from NAS.NASUtils.Huaweicifssnapbasicacceptance import HuaweiCIFSSnapBasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of CIFS under NAS Intellisnap 
	   Backup and Restore for Huawei Vstore client """

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("NewAutomation Huawei Vstore - V2 - Windows MA - Basic Acceptance "\
		              "Test of CIFS under NAS Intellisnap Backup and Restore")
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
                    "ClientName": None,
					"SubclientName": None,
					"BackupsetName": None,
                    "AgentName": None,
					"SubclientContent": None,
					"CIFSShareUser": None,
					"CIFSSharePassword":None,
					"FilerRestoreLocation": None,
					"ProxyClient":None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            basic_acceptance = HuaweiCIFSSnapBasicAcceptance(self)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
