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

    run()               --  run function of this test case calls SnapHelper Class to execute
                            and Validate Below Operations.
                            Snap Backup, backup Copy, Restores, Snap Operations like Mount Unmount
                            Revert Delete etc.
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaptemplates import SNAPTemplate
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap Netapp Replication
    for PV Configuration Using Cmode OCUM Server"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None,
            "OCUMServerName": None
            }
        self.name = """V1 Indexing: SnapShot Replication: Verifies Netapp Replication
        for PV Configuration Using Cmode OCUM Server"""

    def run(self):
        """Main function for test case execution"""
        self.tcinputs['ReplicationType'] = "pv" #PV using Cmode OCUM

        try:
            indexing = IndexingHelpers(self.commcell)
            indexing_version = indexing.get_agent_indexing_version(self.client)
            if indexing_version == 'v1':
                self.log.info("Client is v1 indexing, Continuing the test case")
                v1_indexing = True
            else:
                raise Exception('Client is *NOT* v1 indexing, Failing the test case, please use indexing v1 client for this test case')

            self.log.info("Started executing {0} testcase".format(self.id))
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_template = SNAPTemplate(
                self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            snap_template.snap_template2(v1_indexing)


        except Exception as excp:
            self.log.error('Failed with error: %s',excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
