# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51522

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
#Test Suite Imports
import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating testcase of ForEachJSON activity"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate ForEachXML,SwitchToJob,TransferToken Activities"
        self._workflow = None
        self.workflow_name = 'WF_FOREACHXML_SWITCHTOJOB'
        self.tcinputs = {
            'EmailId': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)

    def run(self):
        """Main function of this testcase"""
        try:
            #start workflow execution
            self._workflow.execute(
                {'INP_EMAIL_ID': self.tcinputs['EmailId']}, wait_for_job=False
            )
            time.sleep(30)
            self._workflow.workflow_job_status(self.workflow_name)

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
