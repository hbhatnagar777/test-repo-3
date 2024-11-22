# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 58807

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
import time
from cvpysdk.client import Client
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating additional setting SendEmailsViaCommserver"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate additional setting SendEmailsViaCommserver"
        self._workflow = None
        self.workflow_name = 'WF_RESTARTSERVICES'
        self.tcinputs = {"client" : None}

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self.client = Client(self._commcell, self.tcinputs['client'])
        self._utility = OptionsSelector(self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            _ = self._workflowhelper.execute(
                {
                    'INP_WORKFLOW_NAME': self.workflow_name,
                    'client': self.tcinputs['client']
                }, wait_for_job=False)
            self._utility.validate_restartservices(self.client)

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self._workflowhelper.cleanup()
