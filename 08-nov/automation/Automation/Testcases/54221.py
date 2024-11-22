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
from AutomationUtils.database_helper import MSSQL
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for validating the CommServ has proper deployment records"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Restart WorkflowEngine service " \
                    "need to deploy the default Commcell Workflow if the deployment record is deleted"
        self.show_to_user = False
        self.tcinputs = {
            'SQLInstance': None,
            'SQLUser': None,
            'SQLPassword': None
        }
        self.workflow_helper = None
        self.wf_name = 'Demo_CheckReadiness'

    def setup(self):
        """Setup Function for this testcase"""
        self.workflow_helper = WorkflowHelper(self, 'Demo_CheckReadiness', deploy=False)

    def run(self):
        """Main function for test case execution"""
        try:
            if not self.commcell.workflows.has_workflow(self.wf_name):
                raise Exception("Workflow [{}] provided is not default Commcell Workflow".
                                format(self.wf_name))
            self.log.info("Workflow [%s] is a default Commcell workflow" %self.wf_name)
            delete_deploy_csdb_query = "delete WF_Deploy where WorkflowId=(select " \
                                       "WorkflowId from WF_Definition where name='{}')".format(self.wf_name)
            mssql = MSSQL(self.tcinputs['SQLInstance'], self.tcinputs['SQLUser'],
                          self.tcinputs['SQLPassword'], 'CommServ')
            mssql.execute(delete_deploy_csdb_query)
            self.log.info("Deployment record of workflow [%s] in CommServ DB "
                          "is deleted successfully"%self.wf_name)
            wfengine_instance = self.client.instance
            service_name = 'CVJavaWorkflow({})'.format(wfengine_instance)
            self.client.restart_service(service_name)
            self.log.info("WorkflowEngine service is successfully restarted")
            utility = OptionsSelector(self.commcell)
            utility.sleep_time(_time=180)
            self.commcell.refresh()
            self.workflow_helper.is_deployed(self.wf_name)
            self.workflow_helper.execute(
                {
                    'ClientGroupName': 'Media Agents'
                }
            )

        except Exception as excp:
            self.workflow_helper.test.fail(excp)
