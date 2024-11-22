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
    """Make sure Workflow using Webservices activities work fine"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Make sure Workflow using Webservices activities work fine"
        self.show_to_user = False

        # Inherited class attributes
        self._workflow = None

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, "wf_web_services")
        self._log = self._workflow.log

    def run(self):
        """Main function for test case execution"""

        try:
            self._workflow.execute()

        except Exception as excp:
            self._workflow.test.fail(excp)
        finally:
            self._workflow.cleanup()
