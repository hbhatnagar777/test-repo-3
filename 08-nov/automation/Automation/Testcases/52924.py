# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 52924

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
#Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating Export workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Workflow - Retrieve Workflow Definition in Export format using command"
        self._workflow = None
        self.workflow_name = 'WF_EMAIL'
        self.tcinputs = {
            'ExportPath': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)

    def run(self):
        """Main function of this testcase"""
        try:
            workflow_xml = self._workflow.export_workflow(self.tcinputs['ExportPath'])
            self.log.info("Successfully Exported the workflow %s", self.workflow_name)
            self.log.info("Exported in location %s", workflow_xml)
            self._workflow.delete(workflow_name=self.workflow_name)
            self.log.info("Successfully deleted the workflow %s", self.workflow_name)
            self._workflow.import_workflow(workflow_xml=workflow_xml,
                                           workflow=self.workflow_name)
            self._workflow.deploy_workflow(workflow_xml=workflow_xml,
                                           workflow=self.workflow_name)
            self.log.info("Successfully deployed the workflow %s using export xml",
                          self.workflow_name)

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
