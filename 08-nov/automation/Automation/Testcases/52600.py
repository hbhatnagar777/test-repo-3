# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 52600

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from cvpysdk.security.role import Roles, Role
from cvpysdk.security.user import Users
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.config import get_config

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):

    """Class for validating Security Settings"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Security Settings"
        self.workflow_name = 'WF_EMAIL'

    def setup(self):
        """Setup function of this test case"""
        self._admin_workflowhelper = WorkflowHelper(self, self.workflow_name, deploy=False)

    def create_user_and_role(self, username, password, rolename):
        """Create auser adn role and associates the role to the user

        Args:
            username    : User to be created
            
            password    : Password for the user

            rolename    : Role to be created

        returns:
                    Workflowhelper object with the comcmell object

        Raises:
                Exception when creates user/role"""

        """Create role and user if does not exist"""
        roles = Roles(self.commcell)
        users = Users(self.commcell)
        if roles.has_role(rolename) is False:
            self.log.info("Role does not exist, creating it")
            roles.add(rolename, [rolename], ["Commcell"])
        role = Role(self.commcell, rolename)
        
        if users.has_user(username) is False:
            self.log.info("User does not exist, creating it")
            users.add(
                username,
                username,
                "workflow@testing.com",
                None,
                password
            )

        self._commcell.refresh()
        role.associate_user(rolename, username)
        commcell_obj = Commcell(self.commcell.commserv_name, commcell_username=username, commcell_password=password)
        workflowhelper = WorkflowHelper(self, self.workflow_name, commcell=commcell_obj, deploy=False)
        return workflowhelper

    def run(self):
        """Main function of this testcase execution"""
        try:
            password = _STORE_CONFIG.Workflow.ComplexPasswords.CommonPassword
            self.log.info("1.Importing workflow without edit workflow permissions")
            view_workflowhelper = self.create_user_and_role('test2', password, 'View')
            try:
                view_workflowhelper.deploy()
              
            except Exception as excp:
                self.log.info("Exception raise %s", format(excp))
            
            if view_workflowhelper.has_workflow(self.workflow_name):
                raise Exception("Workflow imported/deployed without permissions")
            
            self.log.info("2.Deploying workflow without edit workflow permissions")
            create_workflowhelper = self.create_user_and_role('test1', password, 'Create Workflow')
            try:
                create_workflowhelper.deploy()
             
            except Exception as excp:
                self.log.info("Exception raise %s", format(excp))
                           
            
            self._admin_workflowhelper.deploy()
            self._commcell.refresh()
            
            self.log.info("3.Disabling workflow without edit workflow permissions")
            
            try:
                create_workflowhelper.disable_workflow(self.workflow_name)
                    
            except Exception as excp:
                self.log.info("Exception raise %s", format(excp))
            
            create_workflowhelper.enable_workflow(self.workflow_name)
            
            self.log.info("4.Executing workflow without edit workflow permissions")
            try:
                view_workflowhelper.execute()
            
            except Exception as excp:
                self.log.info("Exception raise %s", format(excp))

            self.log.info("5.Deleting workflow without edit workflow permissions")
            try:
                create_workflowhelper.delete(self.workflow_name)
            
            except Exception as excp:
                self.log.info("Exception raise %s", format(excp))
             
            if not self._admin_workflowhelper.has_workflow(self.workflow_name):
                raise Exception("workflow has been deleted without permissions")
                
        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._admin_workflowhelper.test.fail(excp)

        finally:
            self._admin_workflowhelper.cleanup()
            
