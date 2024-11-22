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
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of  NDMP backup and Restore from Replica Copy test case"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("Snap Mirror - NDMP - Basic acceptance")
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
            replication_acceptance = SnapBasicAcceptance(self, is_cluster=True)
            replication_acceptance.replication_template(replica_type="pm_replica")
        except Exception as exp:
            self.log.error(f'Failed with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED
