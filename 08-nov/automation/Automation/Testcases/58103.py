# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """[WORKFLOW] - Validate JSONToResultSet and ResultSetToJSON Activities"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "[WORKFLOW] - Validate JSONToResultSet and ResultSetToJSON Activities"
        self.workflow_name = "WF_RESULTSETTOJSON"
        self.wf_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.wf_helper.execute()

        except Exception as exp:
            self.wf_helper.test.fail(exp)

        finally:
            self.wf_helper.cleanup()
