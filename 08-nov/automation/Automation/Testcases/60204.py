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
        self.name = ("NewAutomation NetApp - V2 - Unix MA - Basic Acceptance "
		              "Test of NFS under NAS Intellisnap Backup and Restore for Multisite")
        self.tcinputs = {


            "mount_path" : None,
            "ProxyClient" : None,
            "SubclientContent" : None,
            "mount_path_2": None,
            "ProxyClient_2": None,
            "SubclientContent_2": None,

            }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase")
            basic_acceptance = NFSSnapBasicAcceptance(self)
            basic_acceptance.run()

            basic_acceptance.mount_path = self.tcinputs['MountPath_2']
            basic_acceptance.proxy_client = self.tcinputs['ProxyClient_2']
            basic_acceptance.subclient_content = self.tcinputs['SubclientContent_2']
            basic_acceptance.run()

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
