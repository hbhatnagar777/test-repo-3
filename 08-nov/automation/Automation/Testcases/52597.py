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

    """Class for validating Workflow - Operations - Business Logic Workflows with Module"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow - Operations - Business Logic Workflows with Module - evmgrs, webserver REQUEST"
        self.workflow_name = "WF_BUSINESS_LOGIC_REQUEST"
        self.workflow_message = "App_CreateUserRequest"
        self.wf_helper = None
        self.custom_name = None
        self.user_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)

    def database_validation(self):
        """ Validating if workflow entry is found in database """
        resultset = self.wf_helper.get_db_bl_workflow(self.workflow_message, self.workflow_name)
        if len(resultset[0]) == 1:
            raise Exception("Workflow entry not found in database for modules evmgrs, webserver REQUEST")
        self.log.info("Workflow entry found in database for modules evmgrs, webserver REQUEST")

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.database_validation()
            self.custom_name = OptionsSelector(self.commcell).get_custom_str()
            try:
                self.log.info("Trying to create user, should be blocked by workflow [%s]"
                              , self.workflow_name)
                self.user_helper = UserHelper(commcell=self.commcell)
                self.user_helper.create_user(user_name=self.custom_name,
                                             email="{0}@cv.com".format(self.custom_name),
                                             password=self.custom_name)
                raise Exception("User created successfully. Expected to be blocked from BL workflow")
            except Exception as exp:
                if 'Blocked by workflow' not in str(exp):
                    raise Exception("Workflow validation failed for modules evmgrs, webserver REQUEST")
                self.log.info("Error as expected: [%s]", (str(exp)))
                self.log.info("Workflow validation successful")

        except Exception as exp:
            self.wf_helper.test.fail(exp)

        finally:
            self.wf_helper.delete(self.workflow_name)
            if self.commcell.users.has_user(self.custom_name):
                self.log.info("Deleting the created user")
                self.user_helper.delete_user(self.custom_name, "admin")