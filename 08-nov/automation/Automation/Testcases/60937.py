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
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic Acceptance for NDMP Backup and restore: Cluster As a CLient - V1 Unix MA"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance of NDMP Intellisnap Backup & Restore for Cluster as client"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "FilerRestoreLocation": None
        }

    def run(self):
        """Execution method for this test case"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)

            basic_acceptance = SnapBasicAcceptance(self, is_cluster=True)
            basic_acceptance.run()

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
