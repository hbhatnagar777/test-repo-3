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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.nfssnapbasicacceptance import NFSSnapBasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NFS under NAS Intellisnap 
	   Backup and Restore for Huawei Vstore client"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("NewAutomation Huawei Vstore- V2 - Unix MA - Basic Acceptance "\
		              "Test of NFS under NAS Intellisnap Backup and Restore")
        self.tcinputs = {
		            "ClientName": None,
					"SubclientName": None,
					"BackupsetName": None,
                    "AgentName": None,
					"SubclientContent": None,
                    "mount_path":None,
					"ProxyClient":None
            }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            basic_acceptance = NFSSnapBasicAcceptance(self)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
