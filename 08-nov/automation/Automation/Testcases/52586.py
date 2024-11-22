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

    """Workflow Configuration - Enable Workflow Auto-Deploy for New Engine"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow - Enable Workflow Auto-Deploy for New Engine"
        self.workflow_name_old = 'WF_OLDWORKFLOW'
        self.workflow_name_new = 'WF_NEWWORKFLOW'
        self.wf_helper_old = None
        self.wf_helper_new = None
        self.workflow_obj = None
        self.machine = None
        self.command = None
        self.option_selector = None
        self.paccess = None
        self.pexecaccess = None
        self.instance = None
        self.tcinputs = {
            "MachineHostName": None,
            "CustomInstallationPath": None,
            "WorkflowEngineName": None,
            "LogPath": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.option_selector = OptionsSelector(self.commcell)
        self.wf_helper_old = WorkflowHelper(self, wf_name=self.workflow_name_old)
        self.wf_helper_new = WorkflowHelper(self, wf_name=self.workflow_name_new)
        self.machine = Machine(machine_name=self.tcinputs["MachineHostName"],
                               commcell_object=self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.wf_helper_old.set_auto_deploy_property(value=1)
            self.wf_helper_new.set_auto_deploy_property(value=0)
            self.command = "{0}\\WinX64\\Setup.exe /silent /play {0}\\install.xml".\
                format(self.tcinputs["CustomInstallationPath"])
            self.log.info("Starting installation")
            self.machine.execute_command(command=self.command)
            self.option_selector.sleep_time(_time=60)
            time_count = 0
            self.log.info("Waiting for workflow engine deployment to complete..")
            while time_count < 30:
                log_file = self.machine.read_file(
                    file_path=self.tcinputs['LogPath'])
                if self.workflow_name_old in log_file:
                    break
                self.option_selector.sleep_time(_time=60)
                time_count = time_count + 1
            self.commcell.workflows.refresh()
            wf_id_old = self.wf_helper_old.workflow_obj.workflow_id
            wf_id_new = self.wf_helper_new.workflow_obj.workflow_id
            query = "select id from app_client where name = '{0}'" \
                .format(self.tcinputs['WorkflowEngineName'])
            client_id = int(self.option_selector.exec_commserv_query(query)[0][0])
            query = "select COUNT(clientId) from WF_Deploy where WorkflowId = {0} and clientId = {1}"\
                .format(wf_id_old, client_id)
            result1 = int(self.option_selector.exec_commserv_query(query)[0][0])
            query = "select COUNT(clientId) from WF_Deploy where WorkflowId = {0} and clientId = {1}" \
                .format(wf_id_new, client_id)
            result2 = int(self.option_selector.exec_commserv_query(query)[0][0])
            if result1 == 0:
                raise Exception("Auto deploy did not happen on new workflow engine,"
                                " Validation Failed")
            if result2 == 1:
                raise Exception("Auto deploy should not have happened on the new workflow engine as flag was not set,"
                                " Validation Failed")
            self.log.info("Validation of auto deploy feature successful")
            self.wf_helper_old.execute(workflow_json_input={
                'workflowEngine': self.tcinputs["WorkflowEngineName"]})

        except Exception as exp:
            self.wf_helper_old.test.fail(exp)

        finally:
            self.wf_helper_new.set_auto_deploy_property(value=1)
            self.wf_helper_old.cleanup()
            self.wf_helper_new.cleanup()
            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.tcinputs["WorkflowEngineName"]):
                self.log.info("Uninstalling client")
                job = self.commcell.clients.get(self.tcinputs["WorkflowEngineName"]).uninstall_software()
                JobManager(job, self.commcell).wait_for_state()
