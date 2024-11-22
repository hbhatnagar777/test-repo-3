# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating autoRestarts of Workflow job"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Workflow - auto route workflow messages with client id 0 " \
                    "if the deploy request is not having client information"
        self._workflow = None
        self.workflow_name = 'WF_EMAIL'
        self.workflow_id = None

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=False)

    def test_step1(self):
        """Import the workflow definition"""
        self._workflow.import_workflow()
        self.workflow_id = self.commcell.workflows.get(self.workflow_name).workflow_id

    def test_step2(self, deploy_xml):
        """Deploy and Executes the workflow"""
        self.commcell.qoperation_execute(deploy_xml)
        self._workflow.execute(
            {"INP_EMAIL_ID": self._workflow.email}
        )

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.test_step1()
            deploy_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?><Workflow_DeployWorkflow>
            <workflow workflowId="{0}" workflowName="{1}"/></Workflow_DeployWorkflow>""".\
                format(self.workflow_id, self.workflow_name)
            self.test_step2(deploy_xml)
            self._workflow.delete(self.workflow_name)
            self._workflow = WorkflowHelper(self, self.workflow_name, deploy=False)
            self.test_step1()
            deploy_xml_2 = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?><Workflow_DeployWorkflow>
                        <workflow workflowId="{0}" workflowName="{1}"/>
                        <client clientId="{2}" clientName="{3}"/></Workflow_DeployWorkflow>""".\
                format(self.workflow_id, self.workflow_name, self.commcell.commserv_client.client_id,
                       self.commcell.commserv_name)
            self.test_step2(deploy_xml_2)

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
