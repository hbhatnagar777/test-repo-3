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
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):

    """Workflow Configuration - Enabling Job Distribution Between Workflow Engines"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow Configuration - Enabling Job Distribution Between Workflow Engines"
        self.workflow_name_parent = "WF_RANDOMWFENGINE"
        self.workflow_name_child = "WF_NEWWORKFLOW"
        self.wf_helper_parent = None
        self.wf_helper_child = None
        self.workflow_id = None
        self.machine = None
        self.command = None
        self.option_selector = None
        self.paccess = None
        self.pexecaccess = None
        self.instance = None
        self.tcinputs = {
            "MachineHostName": None,
            "CustomInstallationPath": None,
            "WorkflowEngineName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper_child = WorkflowHelper(self, wf_name=self.workflow_name_child)
        self.wf_helper_parent = WorkflowHelper(self, wf_name=self.workflow_name_parent)
        self.option_selector = OptionsSelector(self.commcell)
        self.machine = Machine(machine_name=self.tcinputs["MachineHostName"],
                               commcell_object=self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.command = "{0}\\WinX64\\Setup.exe /silent /play {0}\\install.xml". \
                format(self.tcinputs["CustomInstallationPath"])
            self.log.info("Starting installation")
            self.machine.execute_command(command=self.command)
            self.commcell.workflows.refresh()
            self.wf_helper_child.deploy_workflow(workflow_engine=self.tcinputs['WorkflowEngineName'], deployment_check=False)
            self.commcell.add_additional_setting(category="CommServ",
                                                 key_name="RandomWorkflowEngine",
                                                 data_type="INTEGER", value="1")
            self.workflow_id = self.commcell.workflows.get(self.workflow_name_child).workflow_id
            self.wf_helper_parent.execute(workflow_json_input={"ChildWorkflowId": self.workflow_id})

        except Exception as exp:
            self.wf_helper_parent.test.fail(exp)

        finally:
            self.wf_helper_parent.cleanup()
            self.wf_helper_child.cleanup()
            self.commcell.delete_additional_setting(category="CommServ",
                                                    key_name="RandomWorkflowEngine")
            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.tcinputs["WorkflowEngineName"]):
                self.log.info("Uninstalling client")
                job = self.commcell.clients.get(self.tcinputs["WorkflowEngineName"]).uninstall_software()
                JobManager(job, self.commcell).wait_for_state()

