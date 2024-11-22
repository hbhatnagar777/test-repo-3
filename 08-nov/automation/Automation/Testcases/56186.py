# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this testcase

TestCase is the only class defined in this file


TestCase:
    __init__()          --  Initializes test case class object

    setup()             --  Setup function for this testcase

    create_credential() --  Create Credential of specified type

    modify_credential() --  Updates the credential account's username or password

    update_security()   --  Updates the security association of credential account

    run()               --  Main funtion for testcase execution

"""
# Test Suite Imports
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.Security.credentialmanagerhelper import CredentialHelper
from Server.Security.userhelper import UserHelper
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):
    """Class for executing Software store workflow DBMaintenance"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Workflow - Validate GetCredential Activity"
        self.workflow_name = "WF_CREDENTIAL_MANAGER"
        self.workflow = None
        self.credentials_obj = None
        self.cred_obj = None
        self.cred_username = None
        self.cred_password = None
        self.show_to_user = False
        self.tcinputs = {
            'WindowsClient': None,
            'WindowsCredentialUserName': None,
            'WindowsCredentialPassword': None,
            'EmailId': None,
            'UserWithExecuteWorkflowPermission': None
        }

    def setup(self):
        """Setup function of this testcase"""
        self.workflow = WorkflowHelper(self, self.workflow_name, deploy=True)
        self.credentials_obj = CredentialHelper(self.commcell)

    def create_credential(self, account_type, credential, owner, isuser=1, description=None):
        """Creates the Credential account"""
        self.cred_username = self.tcinputs['WindowsCredentialUserName']
        self.cred_password = self.tcinputs['WindowsCredentialPassword']
        if 'linux' in account_type:
            self.cred_username = self.tcinputs['UnixCredentialUserName']
            self.cred_password = self.tcinputs['UnixCredentialPassword']
        return self.credentials_obj.add(account_type, credential, self.cred_username,
                                        self.cred_password, owner, isuser=isuser, description=description)

    def modify_credential(self, credential, username, password):
        """Modifies the Credential username/password"""
        self.credentials_obj.update_user_credential(credential, username, password)
        self.log.info("Updated the credential username/password")

    def update_security(self, credential, user_or_groupname, isuser=True):
        """Updates the Credential's security property"""
        self.credentials_obj.update_security_property(credential, user_or_groupname, is_user=isuser)
        self.log.info("Updated the credential security properties")

    def run(self):
        """Main function for test case execution"""
        try:
            """Validates the Workflow's GetCredential activity with below steps
            1. Create a credential account and use the credential as input for workflow execution
            2. Share the credential to user (Add a user to security property of credential account) and
            execute the workflow by the shared user.
            3. Updates the credential account with wrong details. Execute the workflow for failure validation
            4. Expecting the CS to have default Credential 'WorkflowAutomation'. Execute the workflow for default
            credential validation
            5. Execute the workflow for random credential account which doesnt exist
            6. Create a credential account by master user (other than admin user). Delete the master user after
            transferring the ownership to user (with Execute Workflow on Workflows & Agent Management on Client).
            Execute the workflow by the ownership transferred user
            """
            is_user = False
            is_win_cred = False
            opt_obj = OptionsSelector(self.commcell)
            win_cred = opt_obj.get_custom_str(presubstr='Automation')
            self.cred_obj = self.create_credential('Windows', win_cred, 'admin', isuser=1, description='Automation')
            is_win_cred = True
            self.log.info("Created Windows credential account [%s] successfully", win_cred)
            self.log.info("Initiating the Execution of workflow using Windows credential")
            self.workflow.execute(
                {
                    "INP_EMAIL_ID": self.tcinputs['EmailId'],
                    "INP_CLIENT": self.tcinputs['WindowsClient'],
                    "INP_CREDENTIAL": win_cred
                }
            )
            self.log.info("Execution of workflow using Windows credential completed")
            user_helper = UserHelper(self.commcell)
            user = '{0}_Automation_User1'.format(self.id)
            password = '######'
            user_helper.create_user(user_name=user, full_name=user, password=password, local_usergroups=['master'],
                                    email=self.tcinputs['EmailId'])
            is_user = True
            self.update_security(win_cred, user)
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            user_workflow = user_commcell.workflows.get(self.workflow_name)
            self.log.info("Initiating the execution of workflow using Windows "
                          "credential as the shared user [%s]", user)
            __, user_wf_job = user_workflow.execute_workflow(
                {
                    "INP_EMAIL_ID": self.tcinputs['EmailId'],
                    "INP_CLIENT": self.tcinputs['WindowsClient'],
                    "INP_CREDENTIAL": win_cred
                }
            )
            # Wait for workflow job to complete
            self.log.info("Waiting on workflow jobid [%s] to complete", user_wf_job.job_id)
            if not user_wf_job.wait_for_completion():
                raise Exception("Workflow job execution {} with error {}".format(
                    user_wf_job.status, user_wf_job.delay_reason
                ))
            self.log.info("Execution of workflow using Windows credential by shared user completed")
            self.modify_credential(win_cred, 'test', password)
            self.log.info("Initiating the Execution of workflow with wrong credentials")
            self.workflow.execute(
                {
                    "INP_EMAIL_ID": self.tcinputs['EmailId'],
                    "INP_CLIENT": self.tcinputs['WindowsClient'],
                    "INP_CREDENTIAL": win_cred,
                    "INP_FAILURE_VALIDATION": True
                }
            )
            self.log.info("Execution of workflow using Windows credential with wrong credential completed")
            self.log.info("Initiating the execution of workflow using Windows credential with wrong "
                          "credential by shared user")
            __, user_wf_job2 = user_workflow.execute_workflow(
                {
                    "INP_EMAIL_ID": self.tcinputs['EmailId'],
                    "INP_CLIENT": self.tcinputs['WindowsClient'],
                    "INP_CREDENTIAL": win_cred,
                    "INP_FAILURE_VALIDATION": True
                }
            )
            # Wait for workflow job to complete
            self.log.info("Waiting on workflow jobid [%s] to complete", user_wf_job2.job_id)
            if not user_wf_job2.wait_for_completion():
                raise Exception("Workflow job execution {} with error {}".format(
                    user_wf_job2.status, user_wf_job2.delay_reason
                ))
            self.log.info(
                "Execution of Workflow using Windows credential with wrong credential by shared user completed")
            default_credential = self.credentials_obj.has_credential('WorkflowAutomation')
            if default_credential:
                self.log.info("Validating Default Credential")
                self.workflow.execute(
                    {
                        "INP_EMAIL_ID": self.tcinputs['EmailId'],
                        "INP_CLIENT": self.tcinputs['WindowsClient'],
                        "INP_CREDENTIAL": win_cred,
                        "INP_DEFAULT_VALIDATION": True
                    }
                )
                self.log.info("Validation of Default credential completed")
            self.log.info("Initiating the workflow execution with non-existing credential")
            self.workflow.execute(
                {
                    "INP_EMAIL_ID": self.tcinputs['EmailId'],
                    "INP_CLIENT": self.tcinputs['WindowsClient'],
                    "INP_CREDENTIAL": win_cred,
                    "INP_NOTAVAIL_VALIDATION": True,
                    "INP_NOTAVAIL_CREDENTIAL": user
                }
            )
            self.log.info("Validation of Non-existing credential completed")
            user_cred_obj = CredentialHelper(user_commcell)
            win_cred_2 = opt_obj.get_custom_str(presubstr='Automation')
            user_cred_obj.add('Windows', win_cred_2, self.tcinputs['WindowsCredentialUserName'],
                              self.tcinputs['WindowsCredentialPassword'], user)
            self.log.info("User [%s] created credential account [%s]", user, win_cred_2)
            transfer_user = self.tcinputs['UserWithExecuteWorkflowPermission']
            user_helper.delete_user(user, transfer_user)
            self.log.info("User [%s] is deleted", user)
            is_user = False
            transfer_user_commcell = Commcell(self.commcell.commserv_name, transfer_user, password)
            transfer_user_workflow = transfer_user_commcell.workflows.get(self.workflow_name)
            self.log.info("Initiating the execution of workflow as transferred ownership user")
            __, user2_wf_job = transfer_user_workflow.execute_workflow(
                {
                    "INP_EMAIL_ID": self.tcinputs['EmailId'],
                    "INP_CLIENT": self.tcinputs['WindowsClient'],
                    "INP_CREDENTIAL": win_cred_2
                }
            )
            # Wait for workflow job to complete
            self.log.info("Waiting on workflow jobid [%s] to complete", user2_wf_job.job_id)
            if not user2_wf_job.wait_for_completion():
                raise Exception("Workflow job execution {} with error {}".format(
                    user2_wf_job.status, user2_wf_job.delay_reason
                ))
            self.log.info("Execution of workflow as transferred ownership user completed")

        except Exception as err:
            self.log.info("Exception raise %s", format(err))
            self.workflow.test.fail(err)
        finally:
            if is_user:
                user_helper.delete_user(user, 'admin')
            if is_win_cred:
                self.credentials_obj.delete(win_cred)
            self.workflow.cleanup()
