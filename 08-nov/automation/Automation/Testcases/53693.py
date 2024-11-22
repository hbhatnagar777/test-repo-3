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
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.basicacceptance import BasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic Acceptance for NDMP Backup and restore: Cluster As a CLient on HP-UX MA"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Cluster As a client on HP-UX MA"
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
        
        try:
            self.log.info(f"Started executing {self.id} testcase")
            basic_acceptance = BasicAcceptance(self, is_cluster=True)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error(f'Failed with error:{exp} ')
            self.result_string = str(exp)
            self.status = constants.FAILED
