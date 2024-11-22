# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Helper class for common utilities related function

    CommonUtils:

        __init__()                          --  Initializes CommonUtils helper class
        run_command                         --  Runs a given command on the controller machine
        get_storage_account_access_key      --  Gets the storage account access key for a given storage account4
        get_function_app_app_key            --  Get the function app's app key
        get_pipeline_definition             --  Gets the definition of the given pipeline release
        update_pipeline_definition          --  Updates the pipeline definition using azure APIs
        run_pipeline                        --  Starts the release pipeline deployment
        run_pipeline_api                    --  Starts the release pipeline deployment
        create_pipeline_variables           --  Creates the required variables for successful pipeline deployment
        update_CORS_allowed_origins_value   --  Updates the CORS allowed origins value for a given function app
        get_func_app_object_id              --  Gets the object ID for a given function app
        get_function_code                   --  Gets the function app's function code
        delete_pipeline_variables           --  Deletes the required variables
        remove_CORS_allowed_origins_value   --  Removing the CORS allowed origins value for a given function app
        update_pipeline_variables           --  Updates the required variables for successful pipeline deployment
"""

import json
import requests
from ast import literal_eval
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from MetallicHub.Utils import Constants as cs
from MetallicRing.Utils import Constants as r_cs


class CommonUtils:
    """ helper class for Key Vault Related operations in Metallic Ring"""

    def __init__(self, resource_group, subscription):
        """
        Initializes the Common Utils helper
        Args:
            resource_group(str)     --  Resource group in Azure subscription
            subscription(str)       --  Subscription to be used
        """
        super().__init__()
        self.log = logger.get_log()
        self.log.info(f"Initializing common utils")
        self.resource_group = resource_group
        self.subscription = subscription
        self.local_machine = Machine()
        self.log.info("COmmon utils initialized")

    def run_command(self, command, output_type=r_cs.CMD_FORMATTED_OP):
        """
        Runs a given command on the controller machine
        Args:
            command(str)        --  Command to be executed
            output_type(str)    --  Type of output to be returned
                                    Default - Formatted
        Returns:
            string output of the command executed
        Raises:
            Exception when execution of command fails
        """
        self.log.info(f"Request received to run the following command - [{command}]")
        command_op = self.local_machine.execute_command(command)
        if command_op.exception_message:
            if not cs.BLOWFISH_WARNING_MSG in command_op.exception_message:
                raise Exception(command_op.exception_code,
                                command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        self.log.info(f"Output - [{command_op.output}]."
                      f"Formatted output - [{command_op.formatted_output}]")
        if output_type == r_cs.CMD_FORMATTED_OP:
            return command_op.formatted_output
        else:
            return command_op.output

    def get_storage_account_access_key(self, storage_account_name):
        """
        Gets the storage account access key for a given storage account4
        Args:
            storage_account_name(str)       --  Name of the storage account
        Returns:
            string containing the storage account access key
        Raises:
            Exception
                when the command execution fails with an exception/exception message
                when the storage account doesn't have any storage key configured
        """
        self.log.info(f"Request received to storage account access key - [{storage_account_name}]")
        cmd = f"az storage account keys list --account-name '{storage_account_name}' " \
              f"--resource-group {self.resource_group} --subscription '{self.subscription}'"
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        key_value = json.loads(command_op.output)
        self.log.info(f"Got the required key value")
        if isinstance(key_value, list):
            for key in key_value:
                return key.get("value", None)
        elif isinstance(key_value, dict):
            return key_value.get("value", None)
        else:
            raise Exception("Storage account doesn't have any key configured")

    def get_function_app_app_key(self, function_app_name, key_type=cs.FunctionAppKeyType.DEFAULT):
        """
        Get the function app's app key
        Args:
            function_app_name(str)      --  Name of the function app
            key_type(str)               --  Type of the key to be retrieved
        Returns:
            string output containing the function app's app key
        """
        self.log.info(f"Request received to get function app key - [{function_app_name}]")
        if key_type == cs.FunctionAppKeyType.DEFAULT:
            cmd = f"az functionapp keys list --name '{function_app_name}' --resource-group '{self.resource_group}' " \
                  f"--query functionKeys.default --subscription '{self.subscription}'"
            output = self.run_command(cmd)
            self.log.info("Function app key obtained successfully")
            return output.strip('"')
        else:
            raise NotImplementedError(f"App key type [{key_type}] is not supported")

    def get_pipeline_definition(self, pipeline_name="hub-dev-to-onprem-orbit (M050) - "
                                                    "Hub Automation Release Pipeline Test",
                                organization="https://dev.azure.com/turinnbi", project="ProjectTurin"):
        """
        Gets the definition of the given pipeline release
        Args:
            pipeline_name(str)          --  Name of the pipeline
            organization(str)           --  Organization devops url
            project(str)                --  Name of the project
        Returns:
            dictionary object containing the pipeline definition
        Raises:
            Exception when pipeline definition cli fails
        """
        self.log.info("Request received to get pipeline definition")
        cmd = f"az pipelines release definition show --detect true " \
              f"--name '{pipeline_name}' --organization '{organization}' --project '{project}'"
        output = self.run_command(cmd, output_type="normal")
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        pipeline_def = json.loads(output)
        self.log.info("Pipeline definition obtained successfully")
        return pipeline_def

    def update_pipeline_definition(self, filepath, pipeline_id=322,
                                   organization="turinnbi",
                                   project="ProjectTurin", **kwargs):
        """
        Updates the pipeline definition using azure APIs
        Args:
            filepath(str)       --  Path where the pipeline definition file exists
            pipeline_id(int)    --  ID of the pipeline release in azure dev ops
            organization(str)   --  Name of the organization
            project(str)        --  Name of the project

        kwargs (dict)       --  Dictionary of optional parameters
            username (str)  --  username for the azure devops
            PAT (str)       --  Personal access token for azure devops
        """
        self.log.info(f"Request received to update pipeline definition - [{pipeline_id}], [{filepath}]")
        url = f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/" \
              f"definitions/{pipeline_id}?api-version=7.0"
        username = kwargs.get("username")
        password = kwargs.get("PAT")
        headers = {
            "Content-Type": "application/json"
        }
        with open(filepath, "r") as file:
            json_data = file.read()
        payload = json.loads(json_data)
        self.log.info(f"Pipeline URL: {url}")
        response = requests.put(url, auth=(username, password), headers=headers, json=payload)
        self.log.info(f"Status code: {response.status_code}")
        if response.status_code != 200:
            raise Exception(f"Updating Pipeline definition failed. Response - [{response}]. "
                            f"Content: [{response.content}]")
        self.log.info("Updated the pipeline release definition successfully")

    def run_pipeline(self, pipeline_name="hub-dev-to-onprem-orbit (M050)",
                     organization="https://dev.azure.com/turinnbi", project="ProjectTurin"):
        """
        Starts the release pipeline deployment
        Args:
            pipeline_name(str)          --  Name of the pipeline
            organization(str)           --  URL of the devops organization
            project(str)                --  Name of the project
        """
        self.log.info(f"Request received to run the pipeline. [{pipeline_name}]")
        cmd = f"az pipelines release create --definition-name '{pipeline_name}' " \
              f"--description 'Creating Hub Automation Pipeline Release' --detect true --output json " \
              f"--organization {organization} --project {project} --subscription '{self.subscription}'"
        self.run_command(cmd)

    def run_pipeline_api(self, filepath, pipeline_id, organization, project, **kwargs):
        """
        Starts the release pipeline deployment
        Args:
            filepath(str)       --  Path where the pipeline definition file exists
            pipeline_id(int)    --  ID of the pipeline release in azure dev ops
            organization(str)   --  Name of the organization
            project(str)        --  Name of the project

        kwargs (dict)       --  Dictionary of optional parameters
            username (str)  --  username for the azure devops
            PAT (str)       --  Personal access token for azure devops
            ring_name(str)  --  Name of the ring
        """
        self.log.info("Request received to create release using pipeline release API")
        url = f"https://vsrm.dev.azure.com/{organization}/{project}/_apis/release/releases?api-version=7.0"
        username = kwargs.get("username")
        password = kwargs.get("PAT")
        ring_name = kwargs.get("ring_name")
        headers = {
            "Content-Type": "application/json"
        }
        with open(filepath, "r") as file:
            json_data = file.read()
        stage_data = json.loads(json_data)
        environments = stage_data.get(cs.PIPELINE_FILE_ENVIRONMENTS, None)
        filters = ["App config", "Routing UI", "Global Fn App", ring_name]
        stage_names = [d.get("name") for d in environments]
        stage_to_exclude = [s for s in stage_names if s not in filters]
        payload = {
            "definitionId": pipeline_id,
            "description": "Creating Automation release",
            "artifacts": [
            ],
            "isDraft": False,
            "reason": "none",
            "manualEnvironments": stage_to_exclude
        }
        self.log.info(f"Request URL : [{url}], payload : [{payload}]")
        response = requests.post(url, auth=(username, password), headers=headers, json=payload)
        self.log.info(f"Status code: [{response.status_code}]")
        if response.status_code != 200:
            raise Exception(f"Updating Pipeline definition failed. Response: "
                            f"{response}, Content: [{response.content}]")
        self.log.info("Updated the pipeline release definition successfully")

    def create_pipeline_variables(self, variable_group_id, variables, organization, project):
        """
        Creates the required variables for successful pipeline deployment
        Args:
            variable_group_id(int)          --  ID of the variable group
            variables(list)                 --  List of variables to be added
            organization(str)               --  Name of the organization
            project(str)                    --  Name of the project
        """
        self.log.info("Request received to create pipeline variables")
        variables_str = ""
        for key, value in variables.items():
            variables_str += f"'{key}={value}' "
            self.log.info(f"Creating variable - [{variables_str}]")
            cmd = f"az pipelines variable-group variable create --group-id '{variable_group_id}' " \
                  f"--name '{key}' --value '{value}' --project '{project}' --organization '{organization}'" \
                  f"--subscription '{self.subscription}'"
            self.run_command(cmd)
            self.log.info("Variable created successfully")

    def update_pipeline_variables(self, variable_group_id, variables, organization, project):
        """
        Updates the required variables for successful pipeline deployment
        Args:
            variable_group_id(int)          --  ID of the variable group
            variables(list)                 --  List of variables to be added
            organization(str)               --  Name of the organization
            project(str)                    --  Name of the project
        """
        self.log.info("Request received to update pipeline variables")
        variables_str = ""
        for key, value in variables.items():
            variables_str += f"'{key}={value}' "
            self.log.info(f"Creating variable - [{variables_str}]")
            cmd = f"az pipelines variable-group variable update --group-id '{variable_group_id}' " \
                  f"--name '{key}' --value '{value}' --project '{project}' --organization '{organization}'" \
                  f"--subscription '{self.subscription}'"
            try:
                self.run_command(cmd)
                self.log.info("Variable updated successfully")
            except Exception as e:
                self.log.info("Update of variable failed")

    def delete_pipeline_variables(self, variable_group_id, variables, organization, project):
        """
        Deletes the required variables
        Args:
            variable_group_id(int)          --  ID of the variable group
            variables(list)                 --  List of variables to be added
            organization(str)               --  Name of the organization
            project(str)                    --  Name of the project
        """
        self.log.info("Request received to delete pipeline variables")
        for key in variables:
            self.log.info(f"Deleting variable - [{key}]")
            cmd = f"az pipelines variable-group variable delete --group-id '{variable_group_id}' " \
                  f"--name '{key}' --project '{project}' --organization '{organization}'" \
                  f"--subscription '{self.subscription}' --yes"
            self.run_command(cmd)
            self.log.info("Variable deleted successfully")

    def update_CORS_allowed_origins_value(self, function_app_name, resource_group, allowed_origin):
        """
        Updates the CORS allowed origins value for a given function app
        Args:
            function_app_name(str)      --  Name of the function app
            resource_group(str)         --  Name of the resource group
            allowed_origin(str)         --  Allowed origin value
        Raises:
            Exception when updating allowed origin value fails
        """
        self.log.info(f"Updating CORS allowed origins value for function app - [{function_app_name}], "
                      f"allowed origins - [{allowed_origin}]")
        cmd = f"az functionapp cors add --subscription '{self.subscription}' --resource-group '{resource_group}' " \
              f"--name '{function_app_name}' --allowed-origins '{allowed_origin}'"
        output = self.run_command(cmd)
        op_dict = json.loads(output)
        allowed_origins_list = op_dict.get(cs.CORS_ALLOWED_ORIGINS_KEY, None)
        if allowed_origins_list is not None:
            for origin in allowed_origins_list:
                if allowed_origin == origin:
                    self.log.info("Allowed origin updated successfully")
                    return
        raise Exception(f"Updating allowed origins [{allowed_origin}] failed")

    def remove_CORS_allowed_origins_value(self, function_app_name, resource_group, allowed_origin):
        """
        Removing the CORS allowed origins value for a given function app
        Args:
            function_app_name(str)      --  Name of the function app
            resource_group(str)         --  Name of the resource group
            allowed_origin(str)         --  Allowed origin value
        Raises:
            Exception when updating allowed origin value fails
        """
        self.log.info(f"Removing CORS allowed origins value for function app - [{function_app_name}], "
                      f"allowed origins - [{allowed_origin}]")
        cmd = f"az functionapp cors remove --subscription '{self.subscription}' --resource-group '{resource_group}' " \
              f"--name '{function_app_name}' --allowed-origins '{allowed_origin}'"
        output = self.run_command(cmd)
        op_dict = json.loads(output)
        allowed_origins_list = op_dict.get(cs.CORS_ALLOWED_ORIGINS_KEY, None)
        if allowed_origins_list is not None:
            for origin in allowed_origins_list:
                if allowed_origin == origin:
                    self.log.info("Allowed origin removed successfully")
                    return
        raise Exception(f"Removing allowed origins [{allowed_origin}] failed")

    def get_func_app_object_id(self, name):
        """
        Gets the object ID for a given function app
        Args:
            name(str)       --  Name of the function app
        Returns:
            String containing the function app object ID
        """
        self.log.info(f"Request received to get function app object id - [{name}]")
        cmd = f"az functionapp show --subscription '{self.subscription}' --name {name} " \
              f"--resource-group {self.resource_group} --query 'identity.principalId'" \
              f" --output tsv"
        return self.run_command(cmd)

    def get_function_code(self, function_name, function_app_name):
        """
        Gets the function app's function code
        Args:
            function_name(str)      --  Name of the function in function app
            function_app_name(str)  --  Name of the function name
        Returns:
            string containing the function code
        """
        self.log.info(f"Request received to get function [{function_name}] "
                      f"code for function app- [{function_app_name}]")
        cmd = f"az functionapp function keys list -g {self.resource_group} -n {function_app_name} " \
              f"--function-name {function_name} --query 'default' --subscription {self.subscription}"
        return literal_eval(self.run_command(cmd, output_type=None))


