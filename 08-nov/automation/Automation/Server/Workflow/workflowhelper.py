# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing workflow operations on Commcell

WorkflowHelper is the only class defined in this file

WorkflowHelper:    Provides functionality to deploy and execute workflows on
                    WorkflowEngine.

WorkflowHelper:
    __init__()                  --  initialize instance of the WorkflowHelper class

    __repr__()                  --  Representation string for the instance of the
                                    WorkflowHelper class

    has_workflow()              -- Checks if a workflow exists in the commcell with the input workflow name

    download_workflow_from_store()
                                -- Downloads workflow from Software Store

    execute()                   --  Deploy and execute the workflow on the WorkflowEngine
                                    and wait for the workjflow job completion.
                                    If workflow is not deployed or imported, it imports/deploys
                                    the workflow.
                                    Also deploys any dependent custom created activities

    deploy()                    -- Imports and deploys workflow and dependent(embedded)
                                    workflows on WFEngine.
                                    Also deploys custom activities which the workflow requires.

    deploy_workflow()           -- Deploy a workflow

    import_workflow()           -- Import a workflow

    delete()                    -- Deletes a workflow from the Commcell

    user_interactions()         -- Returns all the pending interactions from a specific user as a list

    submit_interaction()        -- Submit user interaction for user input activity

    modify_workflow_configuration()
                                -- Modify workflow configuration [ Under properties tab ]

    process_user_requests()     -- Approves user requests and wait for workflow job to complete.

    bl_workflows_setup()        -- Pre setup steps for Business logic workflow related test cases for softwarestore

    is_deployed()               -- Returns True if workflow is deployed

    workflow_job_status()       -- Validates the status of jobId for the workflow executed

    get_client_name_and_hostname_based_on_configuration()
                                -- To get clientname and hostname based on the workflow configuration

    export_workflow()           -- Export the workflow xml

    execute_api()               -- Executes the workflow which is in API Mode using a given API

    clone()                     -- Clones the workflow

    enable_workflow()           -- Enables the workflow

    disable_workflow()          -- Disables the workflow

    hidden_workflow()           -- Get Workflow object for specific workflows

    schedule_workflow():        -- Creates a schedule for a workflow

    set_auto_deploy_property()
                                -- Sets the auto deploy property of the workflow

    cleanup()                   -- Cleanup the testcase workflows

    get_db_bl_workflow()        -- Gets the App_messagehandler table data for the given message name and workflow name
    
Attributes:

    **workflow_name**   -- Returns the name of the workflow

"""

# Python standard library imports
import os
import inspect
import xmltodict

# Test suite imports
from Server.Workflow import workflowconstants as WC
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.config import get_config


class WorkflowHelper:
    """Workflow helper class to perform workflow related operations"""

    def __init__(self, testcase, wf_name, wf_dict=None, deploy=True, commcell=None):
        """Initialize instance of the WorkflowHelper class.
            Args:
                testcase  (TestCase instance) -- Instance of TestCase class

                wf_name   (str)               -- Workflow name

                wf_dict   (dict)              -- Workflow dictionary containing
                                                 workflow and/or activity xml locations,
                                                 embedded workflows/activities map and
                                                 workflow engine where workflow need to
                                                 be deployed
                                         e.g
                                         {
                                             'wf_engine': 'WorkflowEngineServer',
                                             'workflow_xml_path': 'C:/Workflows',
                                             'workflow_activities_path': 'C:/Activities'
                                             'workflow_map':{
                                                'common_workflows':["wf_email", "wf_pause"],
                                                'wf_acquire_lock_parent': {
                                                    'Child': ["wf_acquire_lock_child"],
                                                            },
                                         }

                deploy ( bool)                -- If deploy is set to True workflow would be deployed if not already
                                                    deployed.

                commcell (object)             -- Commcell object predefined for a specific user.
                                                    Default: Test Framework commcell object
        """
        self._testcase = testcase
        self._workflow_name = wf_name.lower()

        config = get_config()
        self._workflow_email = config.email.email_id
        self.workflow_config = config.Workflow

        # in case the commcell object is defined for specific user
        if commcell is None:
            self._commcell = self._testcase.commcell
        else:
            self._commcell = commcell
        self.workflows_obj = self._commcell.workflows

        self.test = ServerTestCases(testcase)
        self.database = OptionsSelector(self._testcase.commcell)
        self.csdb = CommServDatabase(self._commcell)
        wf_dict = {} if wf_dict is None else wf_dict
        self._workflow_engine = wf_dict.get('wf_engine', self._commcell.commserv_name)
        self._workflow_xml_path = wf_dict.get('workflow_xml_path', WC.WORKFLOWS)
        self._workflow_activities_path = wf_dict.get('workflow_xml_path', WC.ACTIVITIES)
        self._workflow_map = wf_dict.get('workflow_xml_path', WC.WORKFLOW_DEPENDENCY_MAP)
        self.log = self._testcase.log
        self._job = None
        self.sch_obj = None
        self.workflow_obj = None
        self._services = self._commcell._services
        self._EXECUTE_WORKFLOW_API = self._services['EXECUTE_WORKFLOW_API']
        self._EXECUTE_WORKFLOW = self._services['EXECUTE_WORKFLOW']

        if deploy:
            self.deploy()
            if self.workflows_obj.has_workflow(self._workflow_name):
                self.workflow_obj = self.workflows_obj.get(self._workflow_name)
        else:
            if self.workflows_obj.has_workflow(self._workflow_name):
                self.workflow_obj = self.workflows_obj.get(self._workflow_name, get_properties=False)

    def __repr__(self):
        """Representation string for the instance of the WorkflowHelper class."""
        return "WorkflowHelper class instance for testcase: '{0}'".format(
            self._testcase.name
        )

    @property
    def workflow_name(self):
        """
         Returns the name of the workflow

        """
        return self._workflow_name

    @property
    def email(self):
        """

            Returns the emailid from the config

        """
        return self._workflow_email

    @workflow_name.setter
    def workflow_name(self, workflow_name):
        """
        Setter method for workflow_name

        Args:
             workflow_name  (str)   -- Name of the workflow

        """
        self._workflow_name = workflow_name

    def has_workflow(self, workflow_name):
        """
        Checks if a workflow exists in the commcell with the input workflow name

        Args:
            workflow_name   (str)   --  name of the workflow

        Returns:
            bool    -   boolean output whether the workflow exists in the
                        commcell or not

        Raises:
            SDKException:
                if type of the workflow name argument is not string

        """
        if self.workflows_obj.has_workflow(workflow_name):
            self.log.info('Workflow: %s exists', workflow_name)
            return True
        self.log.info('No workflow exists with the name "%s"', workflow_name)
        return False

    def download_workflow_from_store(
            self,
            workflow_name,
            download_location,
            cloud_username,
            cloud_password):
        """
        Downloads workflow from Software Store

        Args:
            workflow_name       (str)   --  name of the workflow to download

            download_location   (str)   --  location to download the workflow at

            cloud_username      (str)   --  username for the cloud account

            cloud_password      (str)   --  password for the above username

        Returns:
            str     -   full path of the workflow XML

        Raises:
            SDKException:
                if type of the workflow name argument is not string

                if HTTP Status Code is not SUCCESS / download workflow failed

        """
        # To download a workflow from the cloud
        workflow_xml = self.workflows_obj.download_workflow_from_store(
            workflow_name=workflow_name,
            download_location=download_location,
            cloud_username=cloud_username,
            cloud_password=cloud_password
        )
        self.log.info(
            'Successfully downloaded workflow: "%s" from the cloud to the location: %s',
            workflow_name, workflow_xml)

        return workflow_xml

    def execute(self, workflow_json_input=None, wait_for_job=True, hidden=False):
        """ Executes workflow on workflow engine.

        If workflow is not deployed already, an attempt is made to deploy the
        workflow.

        Workflow is executed and waits for the job to complete

        Args:

            workflow_json_input    (dict)  --  dictionary consisting of inputs for the workflow

            wait_for_job           (bool)  --  If user has to wait for job to complete
                                                    default: True
            inputs dict format:

                {
                    'input1_name': 'input1_value',
                    'input2_name': 'input2_value'
                }

                e.g.:
                for executing the Demo_CheckReadiness workflow, inputs dict would be:
                {
                    "ClientGroupName": "client_group_value"
                }

            hidden (bool) -- Is workflow hidden True/False?

        Returns:
            job object    (SDK Job class job object for the workflow job)

        Raises:
            Exception - If workflow job fails to execute

        """
        try:

            workflow_name = self._workflow_name
            if workflow_json_input is None:
                workflow_json_input = {
                    'workflowEngine': self._workflow_engine
                }

            self.log.info("Workflow JSON inputs [{}]".format(workflow_json_input))

            self.workflows_obj.refresh()
            if not hidden:
                if self.workflow_obj is None and self.workflows_obj.has_workflow(self._workflow_name):
                    self.workflow_obj = self.workflows_obj.get(self._workflow_name)

                # Deploy workflow if not already deployed on WorkflowEngine
                if 'client' not in self.workflows_obj.all_workflows.get(workflow_name, {}):
                    self.deploy()
            else:
                self.workflow_obj = self.hidden_workflow(workflow_name)

            # Execute workflow
            self.log.info("Executing workflow [{}]".format(workflow_name))
            __, self._job = self.workflow_obj.execute_workflow(workflow_json_input, hidden=hidden)

            if not wait_for_job:
                return self._job

            # Wait for workflow job to complete
            self.log.info("Waiting on workflow jobid [{}] to complete".format(self._job.job_id))

            if not self._job.wait_for_completion():
                raise Exception("Workflow job execution {} with error {}".format(
                    self._job.status, self._job.delay_reason
                ))

        except Exception as exp:
            raise Exception("Failed to execute workflow {}".format(str(exp)))

    def execute_api(self, workflow_json_input=None, hidden=False, method_type='POST', api=None):
        """ Executes workflow on workflow engine.

        If workflow is not deployed already, an attempt is made to deploy the
        workflow.

        Workflow is executed and waits for the job to complete

        Args:

            workflow_json_input    (dict)  --  dictionary consisting of inputs for the workflow

            inputs dict format:

                {
                    'input1_name': 'input1_value',
                    'input2_name': 'input2_value'
                }

                e.g.:
                for executing the Demo_CheckReadiness workflow, inputs dict would be:
                {
                    "ClientGroupName": "client_group_value"
                }

            hidden (bool) -- Is workflow hidden True/False?

            method_type :  method type to be used for the API call
                            POST/GET

            api:         API name that needs to be executed


        Raises:
            Exception - If workflow job fails to execute

        """
        try:

            workflow_name = self._workflow_name
            if workflow_json_input is None:
                workflow_json_input = {
                    'workflowEngine': self._workflow_engine
                }

            self.log.info("Workflow JSON inputs [{}]".format(workflow_json_input))

            self.workflows_obj.refresh()
            # Execute workflow
            self.log.info("Executing workflow in API mode[{}]".format(workflow_name))
            if api is None:
                api = self._EXECUTE_WORKFLOW
            elif api == 'EXECUTE_WORKFLOW_API' :
                api =self._EXECUTE_WORKFLOW_API

            import urllib.parse
            flag, response = self._commcell._cvpysdk_object.make_request(
            method_type, api % urllib.parse.quote(workflow_name), workflow_json_input)

            if flag:
                if response.json():
                    output = response.json().get("outputs", {})

                    if "jobId" in response.json():
                        if response.json()["jobId"] == 0:
                            return output, 'Workflow Execution in API Mode Finished Successfully'
                        else:
                            raise Exception('Job Id is returned when running in API mode')
                    elif "errorCode" in response.json():
                        if response.json()['errorCode'] == 0:
                            return output, 'Workflow Execution Finished Successfully'
                        else:
                            error_message = response.json()['errorMessage']
                            o_str = 'Executing Workflow failed\nError: "{0}"'.format(error_message)

                            raise Exception('Workflow', '102', o_str)
                    else:
                        return output, response.json()
                else:
                    raise Exception('Response', '102')
            else:
                response_string = self.workflow_obj._update_response_(response.text)
                raise Exception('Response', '101', response_string)

        except Exception as exp:
            raise Exception("Failed to execute workflow {}".format(str(exp)))

    def deploy(self):

        """ Imports and deploys workflow and dependent(embedded) workflows on WFEngine.

            Also deploys custom activities which the workflow requires.

            Dependent workflows and activities are fetched from the pre populated

            workflow map defined in the WorkflowConstants module unless otherwise

            provided by the user in the module arguments

        Args:
        None

        Returns:
        None

        Raises:
        Exception - If module execution fails during any step.

        """
        try:

            workflow_name = self._workflow_name
            activity_list = []
            workflow_list = []

            if workflow_name in self._workflow_map:

                # If workflow is dependent on custom activities, deploy
                # activities
                if self._workflow_map.get(workflow_name) is not None:
                    for activity in self._workflow_map[workflow_name].get("Activities", []):
                        # Deploy custom activity if not already deployed
                        activity_list.append(activity.lower())
                        if activity.lower() in self.workflows_obj.all_activities:
                            self.log.info("Custom activity [{}] is already deployed".format(activity))
                            continue
                        activity_xml = os.path.join(self._workflow_activities_path, activity + '.xml')
                        if not os.path.exists(activity_xml):
                            raise Exception("Custom activity XML not found at [{}]".format(activity_xml))
                        self.log.info("Custom activity path [{}]".format(activity_xml))
                        self.log.info("Importing custom activity [{}]".format(activity))
                        self.workflows_obj.import_activity(activity_xml)
                    self.log.info("Dependent custom activities list {}".format(activity_list))

                # Generate a list of dependent(embedded) workflows
                for workflow in self._workflow_map.get("common_workflows", []):
                    workflow_list.append(workflow.lower())

                if self._workflow_map.get(workflow_name) is not None:
                    for workflow in self._workflow_map[workflow_name].get("Child", []):
                        workflow_list.append(workflow.lower())

            workflow_list.append(workflow_name)
            self.log.info("Following workflows will be deployed [{}]".format(workflow_list))

            # For each of the dependent and parent workflow make an attempt to
            # import and deploy the workflow if not already imported/deployed
            # on the WorkflowEngine
            for workflow in workflow_list:
                # Import and deploy workflow if not already imported
                self.import_workflow(workflow=workflow)
                self.deploy_workflow(workflow=workflow)

        except Exception as exp:
            raise Exception("Deployment failed with exception {}".format(str(exp)))

    def deploy_workflow(self, workflow_engine=None, workflow_xml=None, workflow=None, deployment_check = True):
        """Deploys workflow on the Commcell if not already Deployed
            Args:
                workflow_engine (str)     : WorkflowEngine where workflow will be deployed

                workflow_xml (str)        : Workflow xml path with complete path location

                workflow (str)            : Workflow name

                deployment_check(bool)    : Checks if workflow is already deployed

            Raises:
                Exception:
                    if module fails at any step during execution
        """
        try:
            if workflow is None:
                workflow = self._workflow_name
            if workflow_engine is None:
                workflow_engine = self._workflow_engine

            self.workflows_obj.refresh()

            if not self.workflows_obj.has_workflow(workflow):
                if workflow_xml is None:
                    workflow_xml = os.path.join(self._workflow_xml_path, workflow + '.xml')

            if deployment_check:
                if 'client' in self.workflows_obj.all_workflows.get(workflow, {}):
                    self.log.info("Workflow [{}] already deployed".format(workflow))
                else:
                    workflow_obj = self.workflows_obj.get(workflow)
                    self.log.info("Deploying workflow {}".format(workflow))
                    workflow_obj.deploy_workflow(workflow_engine, workflow_xml)
                    self.log.info("Workflow [{}] deployed successfully".format(workflow))
            else:
                workflow_obj = self.workflows_obj.get(workflow)
                self.log.info("Deploying workflow {}".format(workflow))
                workflow_obj.deploy_workflow(workflow_engine, workflow_xml)
                self.log.info("Workflow [{}] deployed successfully".format(workflow))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def import_workflow(self, workflow_xml=None, workflow=None):
        """Imports workflow on the Commcell.
            Args:
                workflow_xml (str)    : Workflow xml path with complete path location

                workflow (str)   : Workflow name

            Raises:
                Exception:
                    if module fails at any step during execution
        """
        try:
            if workflow is None:
                workflow = self._workflow_name

            if workflow_xml is None:
                workflow_xml = os.path.join(self._workflow_xml_path, workflow + '.xml')

            self.workflows_obj.refresh()

            # Import workflow if not already imported
            if not self.workflows_obj.has_workflow(workflow):
                if not os.path.exists(workflow_xml):
                    raise Exception("Workflow not found at [{0}]".format(workflow_xml))

                self.log.info("Importing workflow [{0}] from [{1}]".format(workflow, workflow_xml))
                self.workflows_obj.import_workflow(workflow_xml)
                self.log.info("Imported workflow [{0}] successfully.".format(workflow))
            else:
                self.log.info("Workflow [{0}] is already imported on Commcell".format(workflow))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete(self, workflow_name=None):
        """Deletes a workflow from the Commcell.

            Args:
                workflow_name   (str/list)   --  Workflow(s) to delete from commcell

            Raises:
                Exception:
                    if module fails at any step during execution

            Returns:
                True if workflow is successfully deleted
        """
        try:
            self.workflows_obj.refresh()

            if workflow_name is None:
                workflow_name = self._workflow_name

            workflow_list = []
            if isinstance(workflow_name, str):
                workflow_list.append(workflow_name)
            elif isinstance(workflow_name, list):
                workflow_list = workflow_name
            else:
                raise Exception("Unsupported argument passed to delete() [{0}]".format(workflow_name))

            for workflow in workflow_list:
                if not self.workflows_obj.has_workflow(workflow):
                    self.log.info("[{0}] doesn't exist on Commcell".format(workflow))
                    return True

                # Delete workflow
                self.log.info("Deleting workflow [{0}]".format(workflow))
                self.workflows_obj.delete_workflow(workflow)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def user_interactions(self, username):
        """ Returns all the pending interactions from a specific user as a list

            Args:
                username   (str)   --  User name

            Returns:
                (list)    - Pending interactions for a specific user

            Raises:
                Exception:
                    if module fails at any step during execution
        """
        try:
            pending_interactions = []
            # Seen issues with getting user interactions immediately after BL workflow execution.
            # Adding sleep here to wait for interactions to populate.
            self.database.sleep_time(10)
            interactions = self.workflows_obj.all_interactions()
            for interaction in interactions:
                if interaction['user']['userName'].lower() == username.lower():
                    interaction_id = interaction['interactionId']
                    pending_interactions.append(self.workflows_obj.get_interaction_properties(interaction_id))

            self.log.info("Pending user interactions: {0}".format(pending_interactions))
            return pending_interactions

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def submit_interaction(self, interaction, input_xml, action):
        """ Submits a given interaction with specified action

            Args:
                interaction (dict)    --  Interaction dictionary
                e.g:
                    {
                        "interactionId": 3871,
                        "created": 1547524940,
                        "subject": "Delete Backupset [  ->  ->  ] requested by [ 11111_Automation_45_651 ]",
                        "activityName": "Get Authorization",
                        "flags": 1,
                        "description": "",
                        "sessionId": "a38b32dc-f505-45c5-9d61-3eaee226b50c",
                        "processStepId": 648993,
                        "jobId": 2804488,
                        "status": 0,
                        "workflow": {
                            "workflowName": "GetAndProcessAuthorization",
                            "workflowId": 2095
                        },
                        "commCell": {
                            "commCellName": "WIN-K2DCEJR56MG",
                            "commCellId": 2
                        },
                        "client": {
                            "clientId": 2,
                            "clientName": "WIN-K2DCEJR56MG"
                        },
                        "user": {
                            "userName": "11111_Automation_01-14-2019_23_01_45_651",
                            "userId": 1418
                        }
                    }

                input_xml (str)       --  Input XML string for completing the interaction.
                                            e.g : This is very specific to the user input interaction.
                                                    Construct the input XML based on workflow being executed and send
                                                    to this module.

                action   (str)        --  Interaction action
                                            This is very specific to workflow being executed and the expected options
                                                for the given interaction

            Raises:
                Exception:
                    if module fails at any step during execution
        """
        try:
            interaction_id = str(interaction['interactionId'])
            job_id = str(interaction['jobId'])
            self.log.info("Submitting interaction request [{0}] for job id [{1}]".format(interaction_id, job_id))
            self.workflows_obj.submit_interaction(interaction, input_xml, action)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def modify_workflow_configuration(self, config_xml):
        """ Modify workflow configuration

            Args:
                config_xml    (xml)    : Corresponding workflow configuration tags and their values

            Raises:
                Exception:
                    if module fails at any step during execution
        """
        try:
            self.log.info("""Modifying workflow [{0}] configuration with following configuration tags
                                [{1}]""".format(self._workflow_name, config_xml))
            self.workflow_obj.set_workflow_configuration(config_xml)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def process_user_requests(self, username, action='Accept', input_xml="<inputs></inputs>"):
        """ Common module mainly to proccess the interactive requests and wait for workflow job to complete
            This module is mainly written for modularization and common code handling for multiple testcases.

            Args:
                username    (str)    : Unique username for which to approve the interaction request

                action      (str)    : Action to take while taking user approval
                                            Default: Accept

                input_xml    (str)    : Input xml for the worklow's user interactive request.
                                            Default: <inputs></inputs> (No user inputs to UserInput activity)
                                        e.g
                                        <inputs><requestedBy>a</requestedBy><objectName/><CustomMessage/></inputs>
            Raises
                Exception:
                    If failed at any given step in the module.
        """
        try:
            # It takes some time for user input activity to execute and job to go in Waiting state
            interaction = self.user_interactions(username)[0]
            workflow_jobid = str(interaction['jobId'])
            job_manager = JobManager(workflow_jobid, self._commcell)
            job_manager.wait_for_state('waiting')
            if 'waiting on user input' not in job_manager.job.delay_reason:
                raise Exception("Job id [{0}] failed to reach waiting on user input state".format(workflow_jobid))

            if input_xml is None:
                from Server.Workflow.workflowconstants import WORKFLOW_DEFAULT_USER_INPUTS
                input_xml = WORKFLOW_DEFAULT_USER_INPUTS % (interaction['user']['userName'])

            self.submit_interaction(interaction, input_xml, action)
            job_manager.wait_for_state('completed')

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def bl_workflows_setup(self, workflows, username=None, password=None, usergroup=None):
        """ Pre setup steps for Business logic workflow related test cases for softwarestore
            Create a non admin user in master user group
            Check if the workflow is deployed

        Args:
            workflows (list)    : Workflow list which need to be checked if they are deployed. If not throw Exception

            username  (str)     : Username for the user which will be created

            password  (str)     : Password for the user

            usergroup (str)     : User group to associate the user to

        Returns:
            Tuple - Created user name and Commcell object for the created user

        Raises
            Exception:
                - if workflows are not deployed.
                - if any failiure during Execution.
        """

        from Server.Security.userhelper import UserHelper
        from Server.Security.userconstants import USERGROUP
        from cvpysdk.commcell import Commcell

        try:
            if username is None:
                username = 'workflow_' + OptionsSelector.get_custom_str()
            if password is None:
                password = get_config().Workflow.ComplexPasswords.CommonPassword
            user_helper = UserHelper(self._commcell)
            if usergroup is None:
                local_usergroups = [USERGROUP.MASTER]
            else:
                local_usergroups = [usergroup]
            user_helper.create_user(user_name=username, full_name=username, email=username + '@commvault.com',
                                    password=password, local_usergroups=local_usergroups)
            user_commcell = Commcell(self._commcell.commserv_name, username, password)

            for workflow in workflows:
                self.is_deployed(workflow)

            return (username, user_commcell)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_deployed(self, workflow_name, hardcheck=True):
        """ Checks if the workflow is deployed on WorkflowEngine or not

            Args:
                workflow_name   (str)   --  name of the workflow to check

                hardcheck       (bool)  --  If set to True exception shall be raised if workflow is not deployed or
                                                imported on WorkflowEngine.
                                            If set to False, module will return false.
                                            default: True

            Raises:
                Exception:
                    Workflow is not imported on Commcell [ hardcheck=True ]
                    Workflow [{0}] is imported but not deployed/installed. [ hardcheck=True ]
                    if module fails at any step during execution
        """
        try:
            self.workflows_obj.refresh()

            # Validate if workflow is imported
            if not self.workflows_obj.has_workflow(workflow_name):
                if hardcheck:
                    raise Exception("Workflow [{}] is not imported on Commcell".format(workflow_name))
                return False

            # Validate if the workflows are deployed
            if 'client' in self.workflows_obj.all_workflows.get(workflow_name.lower(), {}):
                self.log.info("Workflow [{0}] is deployed.".format(workflow_name))
                return True
            else:
                if hardcheck:
                    raise Exception("Workflow [{0}] is imported but not deployed".format(workflow_name))
                return False

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def workflow_job_status(self, wf_name, wait_for_job=True, expected_state="completed"):

        """Validate the status of jobId for the workflow executed

        Args:
            wf_name (str)       :   Workflow name for which latest job status required

            expected_state(str) :   Expected state for the workflow job to be validated
                Default : "Completed"

        Raises:
            Exception:
                    -If no latest job available for the workflow
                    -Job status is not completed
        """
        try:
            # Querying CommServ database to retrieve the latest jobId for the workflow
            query = "select  J.JobId from JMAdminJobInfoTable J inner join WF_Definition W " \
                    "on J.workFlowId=W.WorkflowId where J.opType=90 and " \
                    "W.name='{0}' order by JobId desc".format(wf_name)
            self.csdb.execute(query)
            self._job = self.csdb.fetch_one_row()[0]
            if self._job:
                job = JobManager(self._job, self._commcell)
                self.log.info("JobId [{0}] triggered for the workflow [{1}]".format(self._job, wf_name))

                if not wait_for_job:
                    return self._job
                job.wait_for_state(expected_state)

                self.log.info("JobId [{0}] executed successfully".format(self._job))
            else:
                raise Exception("No running JobId found for the workflow [{0}]".format(wf_name))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_client_name_and_hostname_based_on_configuration(
            self,
            client_name=None,
            client_hostname=None,
            config_xml=None,
            organization_name=None,
            username='admin'):
        """
        Returns the clientname and hostname based on the configuration of the pre install workflow

        Args:
            client_name     (str)   -- Name of the client

            client_hostname (str)   -- Hostname of the client installed

            config_xml      (str)   -- dictionary consisting of inputs for the pre install workflow

                                        Example:
                                            <Append>2</Append>
                                            <Append_custom_string>false</Append_custom_string>
                                            <Custom_string></Custom_string>
                                            <Append_username_to_client>false</Append_username_to_client>

            organization_name (str) -- Name of the organization

            username        (str)   -- Commcell username used to install the client
                                        default: admin

        Returns:
            (str,str)   -- Returns tuple of client name and client hostname

        Raises:
            Exception:

                -- if arguments are missing

        """
        config_xml = f"<install>{config_xml}</install>"
        config = xmltodict.parse(config_xml)

        if config.get('install').get('Append') == '1':
            client_name = f"{client_name}_{organization_name}"

        elif config.get('install').get('Append_custom_string') == 'true':
            custom_string = config.get('install').get('Custom_string')
            client_name = f"{client_name}_{custom_string}"

        elif config.get('install').get('Append_username_to_client') == 'true':
            client_name = f"{client_name}_{username}"

        elif config.get('install').get('Append') == '2':
            client_name = f"{client_name}_{organization_name}"
            client_hostname = f"{client_hostname}_{organization_name}"
        else:
            self.log.info('No configuration setting is set as True for the pre install work flow')

        return client_name, client_hostname

    def export_workflow(self, export_location=None, workflow=None):
        """Exports the workflow to the location specified

        Args:
            export_location         (Str)       -- Directory path where the workflow need to be export

        Returns:
            str                     --              Absolute path of the exported workflow xml file

        Raises
            Exception :
                --If workflow is not exists
                --If export location does not exist
                --If failed to write the export workflow definition in file
        """
        try:
            self.workflows_obj.refresh()
            if workflow is None:
                workflow = self._workflow_name

            # Check if workflow exists
            if not self.workflows_obj.has_workflow(workflow):
                raise Exception("Workflow [{0}] not exists on this Commcell".format(workflow))
            self.workflow_obj = self.workflows_obj.get(workflow)
            self.log.info("Exporting workflow [{0}]".format(workflow))
            workflow_xml = self.workflow_obj.export_workflow(export_location=export_location)
            self.log.info("Exported workflow [{0}] successfully.".format(workflow))
            return workflow_xml

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def clone(self, clone_workflow_name, workflow=None):
        """Clones the workflow

            Args:
                clone_workflow_name (str)   :   name to be set for clone workflow

                workflow (str)  :   name of workflow to clone

            Raises:
                Exception:
                    if module fails at any step during execution
        """
        try:
            if workflow is None:
                workflow = self._workflow_name

            # Check if workflow to be clone exists
            if not self.workflows_obj.has_workflow(workflow):
                raise Exception("Workflow [{0}] to be cloned does not exists".format(workflow))
            self.workflow_obj = self.workflows_obj.get(self._workflow_name)
            self.log.info("Cloning workflow [%s] with workflow name as [%s]",
                          self._workflow_name, clone_workflow_name)
            self.workflow_obj.clone_workflow(clone_workflow_name)
            self.log.info("Successfully cloned the workflow")

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def enable_workflow(self, workflow=None):
        """Enables the workflow
        Args:
            workflow            (Str)       -- workflow Name
        Raises
            Exception :
                --If Enable workflow fails
        """
        try:
            self.workflows_obj.refresh()
            if workflow is None:
                workflow = self._workflow_name

            # Check if workflow exists
            if not self.workflows_obj.has_workflow(workflow):
                raise Exception("Workflow [{0}] not exists on this Commcell".format(workflow))
            self.workflow_obj = self.workflows_obj.get(workflow)
            self.log.info("Enabling the workflow [{}]".format(workflow))
            self.workflow_obj.enable()
            self.log.info("Successfully enabled the workflow [{}]".format(workflow))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def disable_workflow(self, workflow=None):
        """Disables the Workflow
        Args:
            workflow            (Str)       -- workflow Name
        Raises
            Exception :
                --If Enable workflow fails
        """
        try:
            self.workflows_obj.refresh()
            if workflow is None:
                workflow = self._workflow_name

            # Check if workflow exists
            if not self.workflows_obj.has_workflow(workflow):
                raise Exception("Workflow [{0}] not exists on this Commcell".format(workflow))
            self.workflow_obj = self.workflows_obj.get(workflow)
            self.log.info("Disabling the workflow [{}]".format(workflow))
            self.workflow_obj.disable()
            self.log.info("Successfully disabled the workflow [{}]".format(workflow))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def hidden_workflow(self, wf_name):
        """ Get Workflow object for specific workflows
            e.g: Hidden Workflows [ Fetch id from DB and create object ]

        Args:
            wf_name (str)       :   Workflow name

        Raises:
            Exception:
                    -If failed to create workflow object
        """
        try:
            if wf_name is None:
                wf_name = self._workflow_name

            # Querying CommServ database to retrieve the Worfklow id
            query = "select WorkflowId from WF_Definition where Name='{0}'".format(wf_name)
            self.csdb.execute(query)
            wf_id = self.csdb.fetch_one_row()[0]
            if wf_id:
                self.log.info("Workflow id [{0}] for workflow [{1}]".format(wf_id, wf_name))
                from cvpysdk.workflow import WorkFlow
                return WorkFlow(self._commcell, wf_name, wf_id)
            else:
                raise Exception("Failed to fetch workflow id for workflow [{0}]".format(wf_name))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_db_bl_workflow(self, message_name, workflow_name=None):
        """Gets the App_messagehandler table data for the given message name and workflow name

        Args:
            message_name (str)  : XML Message name

            workflow_name (str) : Workflow name
                                    Default: workflow object from Class initialized object

        Returns:
            Resultset from the DB execution.

        Raises:
            Exception:
                - If failed to get the data
        """
        try:
            if workflow_name is None:
                workflow_name = self._workflow_name

            # Querying CommServ database to retrieve the latest jobId for the workflow
            query = """select * from App_MessageHandler where messagename='{0}' and workflowname='{1}'
                    """.format(message_name, workflow_name)
            (result, resultset) = self.database.exec_commserv_query(query)
            return resultset

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def schedule_workflow(self, schedule_pattern, workflow_json_input=None):
        """
                     Args:
                          schedule_pattern : {}, -- Please refer SchedulePattern.create_schedule
                          in schedules.py for the types of
                                             pattern to be sent

                                             eg: {
                                                    "freq_type": 'daily',
                                                    "active_start_time": time_in_%H/%S (str),
                                                    "repeat_days": days_to_repeat (int)
                                                 }

                          workflow_json_input(dict) - -  dictionary consisting of inputs for the workflow

                                if inputs are not given, user will be prompted for inputs on the command line

                                default: None

                                inputs dict format:

                                {
                                        'input1_name': 'input1_value',

                                        'input2_name': 'input2_value'
                                }

                          e.g.:

                            for executing the Demo_CheckReadiness workflow, inputs dict would be:

                            {
                                "ClientGroupName": "client_group_value"
                            }

                     Returns:
                         object : An instance of the Schedule class for the schedule created

                    """
        try:
            if workflow_json_input is None:
                workflow_json_input = {
                    'workflowEngine': self._workflow_engine
                }
            self.workflow_obj = self.workflows_obj.get(self._workflow_name)
            self.log.info("Scheduling workflow")
            self.sch_obj = self.workflow_obj.schedule_workflow(schedule_pattern, workflow_json_input)
            return self.sch_obj

        except Exception as exp:
            self.log.error(str(exp))

    def set_auto_deploy_property(self, value):
        """ Sets the auto deploy property of the workflow
            Args:
                    value : Set to 1 to enable the autodeploy property,
                            Set to 0 to disable the autodeploy property
        """
        self.workflow_obj._set_workflow_properties("autoDeploy", value)

    def cleanup(self):
        """Cleanup the testcase workflows

        Raises:
            Exception:
                    -If failed to cleanup(delete) workflow
        """
        try:
            workflow_name = self._workflow_name
            workflow_list = []
            if workflow_name in self._workflow_map:
                if self._workflow_map.get(workflow_name) is not None:
                    # Fetch the child workflows
                    for workflow in self._workflow_map[workflow_name].get("Child", []):
                        workflow_list.append(workflow.lower())
                # Fetch  the dependent(embedded) workflows
                for workflow in self._workflow_map.get("common_workflows", []):
                    workflow_list.append(workflow.lower())
            workflow_list.append(workflow_name)
            self.log.info("Following workflows will be deleted [%s]", format(workflow_list))
            self.delete(workflow_list)
            self.log.info("Workflow cleanup is completed")

        except Exception as exp:
            raise Exception("Workflow cleanup failed with exception {}".format(str(exp)))
