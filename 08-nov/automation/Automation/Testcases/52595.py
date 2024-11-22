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
from Server.Security.userhelper import UserHelper


class TestCase(CVTestCase):

    """Class for validating Workflow - Operations - Business Logic Workflows with Module-evmgrs"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow - Operations - Business Logic Workflows with Module-evmgrs REQUEST"
        self.child_workflow_name = "WF_BLOCK_USER_CREATION"
        self.parent_workflow_name = "WF_USERCREATION"
        self.workflow_message = "App_CreateUserRequest"
        self.parent_wf_helper = None
        self.child_wf_helper = None
        self.custom_name = None
        self.user_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.parent_wf_helper = WorkflowHelper(self, wf_name=self.parent_workflow_name, deploy=True)
        self.child_wf_helper = WorkflowHelper(self, wf_name=self.child_workflow_name, deploy=False)
        self.child_wf_helper.import_workflow()
        self.user_helper = UserHelper(commcell=self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.custom_name = OptionsSelector(self.commcell).get_custom_str()
            self.log.info("Trying to create user by executing the workflow [%s]",
                          self.parent_workflow_name)
            self.parent_wf_helper.execute(workflow_json_input={
                "WorkflowID": self.commcell.workflows.get(self.child_workflow_name).workflow_id,
                "UserName": self.custom_name})
            self.log.info("Checking if user is created, should have been blocked by workflow [%s]",
                          self.child_workflow_name)
            self.commcell.users.refresh()
            if self.commcell.users.has_user(user_name=self.custom_name):
                raise Exception("User created successfully. Expected to be blocked from BL workflow"
                                "Hence validation failed for module evmgrs")
            self.log.info("Workflow validation successful for module evmgrs")

        except Exception as exp:
            self.parent_wf_helper.test.fail(str(exp))

        finally:
            if self.commcell.users.has_user(self.custom_name):
                self.user_helper.delete_user(self.custom_name, "admin")
            self.parent_wf_helper.delete([self.parent_workflow_name, self.child_workflow_name])
