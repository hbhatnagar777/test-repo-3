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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):
    """Class for testcase: [Edge upload] : Validate hash and upload"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Edge upload] : Validate hash and upload"
        self.show_to_user = False
        self.tcinputs = {
            'localFilePath': None,
            'contentStoreFolderPath': None,
            'shareType': None,
            'shareId': None,
            'verifyIntegrity': None,
            'corruptChunk': None,
            'corruptChunkHash': None,
        }

    def run(self):
        """Main function for test case execution"""
        try:
            workflow = WorkflowHelper(self, "wf_hashfile")
            for mode in [2, 3]:
                workflow.execute(
                    {
                        'localFilePath': self.tcinputs['localFilePath'],
                        'contentStoreFolderPath': self.tcinputs['contentStoreFolderPath'],
                        'shareType': self.tcinputs['shareType'],
                        'shareId': self.tcinputs['shareId'],
                        'verifyIntegrity': self.tcinputs['verifyIntegrity'],
                        'verifyIntegrityMode': mode,
                        'corruptFile': 'false',
                        'corruptFileHash': 'false',
                        'corruptChunk': self.tcinputs['corruptChunk'],
                        'corruptChunkHash': self.tcinputs['corruptChunkHash'],
                    }
                )

                workflow.execute(
                    {
                        'localFilePath': self.tcinputs['localFilePath'],
                        'contentStoreFolderPath': self.tcinputs['contentStoreFolderPath'],
                        'shareType': self.tcinputs['shareType'],
                        'shareId': self.tcinputs['shareId'],
                        'verifyIntegrity': self.tcinputs['verifyIntegrity'],
                        'verifyIntegrityMode': mode,
                        'corruptFile': 'false',
                        'corruptFileHash': 'true',
                        'corruptChunk': self.tcinputs['corruptChunk'],
                        'corruptChunkHash': self.tcinputs['corruptChunkHash'],
                    }
                )

                # Non share cases
                workflow.execute(
                    {
                        'localFilePath': self.tcinputs['localFilePath'],
                        'contentStoreFolderPath': self.tcinputs['contentStoreFolderPath'],
                        'shareType': self.tcinputs['shareType'],
                        'verifyIntegrity': self.tcinputs['verifyIntegrity'],
                        'verifyIntegrityMode': mode,
                        'corruptFile': 'false',
                        'corruptFileHash': 'false',
                        'corruptChunk': self.tcinputs['corruptChunk'],
                        'corruptChunkHash': self.tcinputs['corruptChunkHash'],
                    }
                )
                workflow.execute(
                    {
                        'localFilePath': self.tcinputs['localFilePath'],
                        'contentStoreFolderPath': self.tcinputs['contentStoreFolderPath'],
                        'shareType': self.tcinputs['shareType'],
                        'verifyIntegrity': self.tcinputs['verifyIntegrity'],
                        'verifyIntegrityMode': mode,
                        'corruptFile': 'false',
                        'corruptFileHash': 'true',
                        'corruptChunk': self.tcinputs['corruptChunk'],
                        'corruptChunkHash': self.tcinputs['corruptChunkHash'],
                    }
                )

        except Exception as excp:
            workflow.test.fail(excp)
