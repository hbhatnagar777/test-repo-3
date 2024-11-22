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

    run()               --  run function of this test case
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.basicacceptance import BasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance for vserver as a client test case"""

    def __init__(self):
        """Initializes testCase object"""
        super(TestCase, self).__init__()
        self.name = "NetApp C mode - V1 - Unix MA - Basic acceptance Test of NDMP Backup \
            and Restore for Vserver as a client with tunneling enabled"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "AuxCopyMediaAgent": None,
            "AuxCopyLibrary": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "FilerRestoreLocation": None
        }

    def run(self):
        """Execution method for this test case"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)

            basic_acceptance = BasicAcceptance(self, is_cluster=True)
            basic_acceptance.run()

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
