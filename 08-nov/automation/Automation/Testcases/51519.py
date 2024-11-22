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
    """Class for executing library, client and snap related
    operations through Workflow activities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Qcommand activities"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.tcinputs = {'DiskLibraryName': None,
                         'TapeLibraryName': None,
                         'JobIDwithSnap': None,
                         'TapeBarcode': None,
                         'MediaExportLocation': None,
                         'ClientDisplayName' : None,
                         'ClientHostName' : None,
                         'ClientCVDPort' : None}

        # Inherited class attributes
        self._test_req = ("""Test case requirements not met.
                            Input 1. Disk lib display name
                            Input 2. Tape library display name
                            Input 3. Job ID to which a snap volume is associated
                            Input 4. Barcode of a tape
                            Input 5. Name of an export location(Under Storage Resources->Locations)
                            Input 6,7,8. Display name, hostname, CVD port of a decoupled client
                            Req 1. Must contain atleast 1 disk library.
                            Req 1. Must contain atleast 1 Job ID with snap associated with it.
                            Req 3. Must contain atleast 1 tape library with a tape in it.
                            Req 4. Must contain atleast 1 Export Location.
                            """)

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "QcommandActivites")

    def run(self):
        """Main function for test case execution"""

        try:
            # Start workflow execution
            self._workflow.execute({'LibraryName' :  self.tcinputs['DiskLibraryName'],
                                    'TapeLibraryName':  self.tcinputs['TapeLibraryName'],
                                    'JobIDWithSnap': self.tcinputs['JobIDwithSnap'],
                                    'TapeBarcode': self.tcinputs['TapeBarcode'],
                                    'MediaExportLocation': self.tcinputs['MediaExportLocation'],
                                    'ClientDisplayName': self.tcinputs['ClientDisplayName'],
                                    'ClientHostName': self.tcinputs['ClientHostName'],
                                    'ClientCVDPort': self.tcinputs['ClientCVDPort']})

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
