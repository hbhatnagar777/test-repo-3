# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 51560

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
import os
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating export workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate export workflow"
        self._workflow = None
        self._workflowengine2_obj = None
        self.workflow_name = 'WF_EMAIL'
        self._utility = OptionsSelector(self._commcell)
        export_location = None
        self.tcinputs = {
            'Commcellclient': None,
            'Commcellclientuser': None,
            'CommcellclientPassword': None
        }

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            self.log.info("Exporting and Deploying the workflow on anotehr Commcell [%s]", self.tcinputs['Commcellclient'])
            export_location = os.path.join(constants.AUTOMATION_DIRECTORY, constants.TEMP_DIR, self._id)
            self._utility.create_directory(self.machine, export_location)
            exported_wf = self._workflow.export_workflow(export_location, self.workflow_name)
            commcell2_obj = Commcell(self.tcinputs['Commcellclient'], self.tcinputs['Commcellclientuser'],
                                     self.tcinputs['CommcellclientPassword'])
            self.wf_obj2 = WorkflowHelper(self, self.workflow_name, deploy=False, commcell=commcell2_obj)

            self.wf_obj2.import_workflow(workflow_xml=exported_wf, workflow=self.workflow_name)
            self.wf_obj2.deploy_workflow(workflow_xml=exported_wf, workflow=self.workflow_name)
            self.wf_obj2.execute(
                {
                    'workflowEngine': self.tcinputs['Commcellclient'],
                    'INP_EMAIL_ID': self._workflow.email,
                    'INP_WORKFLOW_NAME': self.workflow_name
                }
            )

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self.wf_obj2.cleanup()
            self._workflow.cleanup()
            self._utility.remove_directory(self.machine, export_location)
