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
from NAS.NASUtils.nfssnapbasicacceptance import NFSSnapBasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("NewAutomation NetApp C mode - V2 - Unix MA - Basic Acceptance "\
		              "Test of NFS under NAS Intellisnap Backup and Restore")
        self.show_to_user = True
        self.tcinputs = {
            "BackupsetName": None,
            "ClientName": None,
            "mount_path": None,
            "ProxyClient": None,
            "SubclientContent": None,
			"SubclientName": None
            }

    def run(self):
        """Main function for test case execution"""
        
        try:
            self.log.info(f"Started executing {self.id} testcase")
            basic_acceptance = NFSSnapBasicAcceptance(self)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED
