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
    """Class for executing Basic Acceptance for encryption for NDMP backups when using proxy MA -
    Media only (MediaAgent side)"""

    def __init__(self):
        """"Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = ("Test encryption for NDMP backups when using proxy MA - "\
                     "Media only (MediaAgent side)")
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
            basic_acceptance = BasicAcceptance(self, is_cluster=False)
            basic_acceptance.run()

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED