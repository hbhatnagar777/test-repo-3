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

Steps:
 •	NDMP Backup
•	Snapshot cataloguing.
•	Create C2C copy with SVM Cloud target mappings .
•	Run Aux copy.
•	Run OOP directory restore to different SVM (NDMP copy restore), and validate.
•	Run OOP files restore to different volume in same SVM (API restore), and validate.
•	Run inplace files restore to same volume (API restore), and validate.
•	Delete C2C copy.

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.basicacceptance import BasicAcceptance


class TestCase(CVTestCase):
    """Class for executing Basic acceptance for vserver as a client test case"""

    def __init__(self):
        """Initializes testCase object"""
        super(TestCase, self).__init__()
        self.name = "SnapShot Replication: Verifies NetApp Cloud Target Copy Replication for NDMP Agent"
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
            self.log.info("Started executing %s testcase", self.id)

            basic_acceptance = BasicAcceptance(self, is_cluster=True, c2c=True)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
