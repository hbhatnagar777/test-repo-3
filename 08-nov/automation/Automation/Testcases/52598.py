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
from AutomationUtils.options_selector import OptionsSelector
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.machine import Machine
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):

    """Class for validating Workflow - Operations - Business Logic Workflows with Module- cvd"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow - Operations - Business Logic Workflows with Module- cvd"
        self.workflow_name = "WF_CVDBL"
        self.workflow_message = "CVInstallManager_ClientSetup"
        self.wf_helper = None
        self.custom_name = None
        self.machine = None
        self.command = None
        self.tcinputs = {
            "MachineHostName": None,
            "CustomInstallationPath": None,
            "ClientNameToBeCreated": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)
        self.machine = Machine(machine_name=self.tcinputs["MachineHostName"],
                               commcell_object=self.commcell)

    def database_validation(self):
        """ Validating if workflow entry is found in database """
        resultset = self.wf_helper.get_db_bl_workflow(self.workflow_message, self.workflow_name)
        if len(resultset[0]) == 1:
            raise Exception("Workflow entry not found in database for module CVD")
        self.log.info("Workflow entry found in database for module CVD")

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.database_validation()
            self.custom_name = OptionsSelector(self.commcell).get_custom_str()
            config_xml = """
                            <CustomString>{0}</CustomString>
                         """.format(self.custom_name)
            self.wf_helper.modify_workflow_configuration(config_xml)
            self.command = "{0}\\WinX64\\Setup.exe /silent /play {0}\\install.xml". \
                format(self.tcinputs["CustomInstallationPath"])
            self.log.info("Creating client with name: {0}".
                          format(self.tcinputs["ClientNameToBeCreated"]))
            self.log.info("Starting installation")
            self.machine.execute_command(command=self.command)
            self.log.info("{0} workflow is expected to change client name to {1}"
                          .format(self.workflow_name, self.custom_name))
            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.tcinputs["ClientNameToBeCreated"]):
                raise Exception("Client created with name {0}, "
                                "name was supposed to be changed by workflow,"
                                "Hence validation failed")
            if not self.commcell.clients.has_client(self.custom_name):
                raise Exception("Client not created")
            self.log.info("Validation Successful")

        except Exception as exp:
            self.wf_helper.test.fail(exp)

        finally:
            self.wf_helper.cleanup()
            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.custom_name):
                self.log.info("Uninstalling software")
                job = self.commcell.clients.get(
                    self.custom_name).uninstall_software()
                JobManager(job, self.commcell).wait_for_state()
            if self.commcell.clients.has_client(self.tcinputs["ClientNameToBeCreated"]):
                self.log.info("Uninstalling software")
                job = self.commcell.clients.get(
                    self.tcinputs["ClientNameToBeCreated"]).uninstall_software()
                JobManager(job, self.commcell).wait_for_state()
