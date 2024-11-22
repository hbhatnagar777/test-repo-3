# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for performing Azure pipeline related operations

    AzurePipelineHelper:

        __init__()                          --  Initializes Azure pipeline helper
        perform_pipeline_operations         --  Starts and runs all pipeline related tasks
        run_pipeline                        --  Triggers the release deployment pipeline using Az cli
        run_pipeline_api                    --  Triggers the release deployment pipeline using AZ API
        update_pipeline_definition          --  Updates pipeline definition on devops portal
        update_definition_to_file           --  Updates the pipeline definition file
        get_stage_content                   --  Gets the stage content for new ring
        create_pipeline_variables           --  Creates the required variables in devops for pipeline
        set_orbit_app_CORS_allowed_domain   --  Updates the CORS domain value
        delete_definition_from_file         --  Deletes the ring stage definition file the pipeline Json file
        delete_pipeline_variables           --  Deletes the required variables in devops for pipeline
        remove_orbit_app_CORS_allowed_domain--  Removes the CORS domain value
        delete_resource_group               --  Deletes a given resource group
        resource_group_exists               --  Checks if a given resource group exists
        write_pipeline_definition_to_file   --  Downloads and writes the pipeline definition file
        update_pipeline_variables           --  Updates the required variables in devops for pipeline

"""

import json
import os
from time import sleep

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicHub.Utils import Constants as cs
from MetallicHub.Utils.common_utils import CommonUtils

_CONFIG = get_config(json_path=cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub


class AzurePipelineHelper:
    """ contains helper class for running the pipeline in Azure portal"""

    def __init__(self, ring_name, rid, config=_CONFIG.azure_credentials):
        """
        Initializes Azure pipeline helper
        Args:
            ring_name(str)      --  Name of the ring
            rid(str)            --  ID of the Ring
            config(dict)        --  Dictionary having azure credentials
        """
        super().__init__()
        self.log = logger.get_log()
        self.log.info("Initializing Azure Pipeline Helper")
        self.ring_name = ring_name
        self.rid = rid
        self.release_pipeline_path = cs.HUB_RELEASE_PIPELINE_PATH % self.ring_name
        self.pipeline_stage_blob_path = cs.METALLIC_HUB_STAGE_BLOB_FILE_PATH
        self.branch_name = f"automation_{self.ring_name}_branch"
        self.git_util = None
        self.config = config
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET
        self.subscription_id = config.SUBSCRIPTION_ID
        self.tenant_id = config.TENANT_ID
        self.access_key = config.ACCESS_KEY
        self.pipeline = config.PIPELINE
        self.pipeline_phase_two = config.PIPELINE_PHASE_TWO
        self.organization = config.ORGANIZATION
        self.organization_name = config.ORGANIZATION_NAME
        self.project = config.PROJECT
        self.pipeline_id = config.PIPELINE_ID
        self.pipeline_id_phase_two = config.PIPELINE_ID_PHASE_TWO
        self.username = config.AZ_USERNAME
        self.pat = config.AZ_PAT
        self.filename = cs.HUB_PIPELINE_RELEASE_JSON_FILE % self.ring_name
        self.common_utils = CommonUtils(cs.RESOURCE_GROUP_NAME, self.subscription_id)
        self.local_machine = Machine()
        self.retry_attempt = 0
        os.environ["ARM_CLIENT_ID"] = self.client_id
        os.environ["ARM_CLIENT_SECRET"] = self.client_secret
        os.environ["ARM_SUBSCRIPTION_ID"] = self.subscription_id
        os.environ["ARM_TENANT_ID"] = self.tenant_id
        os.environ["ARM_ACCESS_KEY"] = self.access_key
        os.environ["AZURE_DEVOPS_EXT_PAT"] = self.pat
        self.log.info("Initialized Azure Pipeline helper")
        # self.common_utils.perform_az_login()

    def perform_pipeline_operations(self):
        """
        Starts and runs all pipeline related tasks
        """
        self.log.info("Request received to perform pipeline operations")
        if not os.path.exists(self.release_pipeline_path):
            os.makedirs(self.release_pipeline_path)
        os.chdir(self.release_pipeline_path)
        # self.common_utils.perform_az_login()
        self.set_orbit_app_CORS_allowed_domain()
        self.create_pipeline_variables()
        self.update_definition_to_file()
        self.update_pipeline_definition()
        self.run_pipeline()
        self.log.info("Pipeline operations complete")

    def run_pipeline(self):
        """
        Triggers the release deployment pipeline using Az cli
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Request received to run the pipeline - [{self.pipeline_phase_two}] ")
            self.common_utils.run_pipeline(self.pipeline_phase_two, self.organization, self.project)
            status = cs.PASSED
            self.log.info("Pipeline create release task complete. Sleeping for 2 hours to complete "
                          "running the create pipeline. ")
            sleep(1 * 60 * 60)
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def run_pipeline_api(self):
        """
        Triggers the release deployment pipeline using AZ API
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Starting pipeline deployment - [{self.pipeline_phase_two}] from filepath - [{self.filename}]")
            os.chdir(self.release_pipeline_path)
            self.common_utils.run_pipeline_api(self.filename, self.pipeline_id_phase_two,
                                               self.organization_name, self.project, username=self.username,
                                               PAT=self.pat, ring_name=self.ring_name.upper())
            self.log.info("Pipeline deployment started successfully. sleeping for 45 minutes")
            sleep(45 * 60)
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def update_pipeline_definition(self):
        """
        Updates pipeline definition on devops portal
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Updating pipeline definition - [{self.pipeline_phase_two}] from filepath - [{self.filename}]")
            os.chdir(self.release_pipeline_path)
            self.common_utils.update_pipeline_definition(self.filename, self.pipeline_id_phase_two,
                                                         self.organization_name, self.project, username=self.username,
                                                         PAT=self.pat)
            self.log.info("Pipeline updated successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def update_definition_to_file(self):
        """
        Updates the pipeline definition file
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Updating pipeline definition file")
            if not os.path.exists(self.release_pipeline_path):
                self.log.info(f"File path - [{self.release_pipeline_path}] doesn't exist. Create new one")
                os.makedirs(self.release_pipeline_path)
            self.log.info("Changing cwd")
            os.chdir(self.release_pipeline_path)
            self.log.info(f"CWD set to [{self.release_pipeline_path}]")
            pipeline_def = self.common_utils.get_pipeline_definition(self.pipeline_phase_two, self.organization, self.project)
            environments = pipeline_def.get(cs.PIPELINE_FILE_ENVIRONMENTS, None)
            max_rank = max(environments, key=lambda x: x[cs.PIPELINE_FILE_RANK])
            stage_content = self.get_stage_content()
            stage_content[cs.PIPELINE_FILE_RANK] = max_rank[cs.PIPELINE_FILE_RANK] + 1
            self.log.info(f"Stage content is [{stage_content}]. Updating the same to file")
            if environments is None:
                pipeline_def[cs.PIPELINE_FILE_ENVIRONMENTS] = stage_content
            else:
                pipeline_def[cs.PIPELINE_FILE_ENVIRONMENTS].append(stage_content)
            with open(self.filename, 'w') as file:
                json.dump(pipeline_def, file, indent=4)
            self.log.info("Updated pipeline definition to file")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def write_pipeline_definition_to_file(self):
        """
        Downloads and writes the pipeline definition file
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Downloading pipeline definition file")
            if not os.path.exists(self.release_pipeline_path):
                self.log.info(f"File path - [{self.release_pipeline_path}] doesn't exist. Create new one")
                os.makedirs(self.release_pipeline_path)
            self.log.info("Changing cwd")
            os.chdir(self.release_pipeline_path)
            self.log.info(f"CWD set to [{self.release_pipeline_path}]")
            pipeline_def = self.common_utils.get_pipeline_definition(self.pipeline_phase_two, self.organization, self.project)
            with open(self.filename, 'w') as file:
                json.dump(pipeline_def, file, indent=4)
            self.log.info("Wrote pipeline definition to file")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_definition_from_file(self,  pipeline):
        """
        Deletes the ring stage definition file the pipeline Json file
        Args:
            pipeline(str)           --  Name of the release pipeline to delete stage from
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Deleting pipeline stage definition from file")
            if not os.path.exists(self.release_pipeline_path):
                self.log.info(f"File path - [{self.release_pipeline_path}] doesn't exist. Create new one")
                os.makedirs(self.release_pipeline_path)
            self.log.info("Changing cwd")
            os.chdir(self.release_pipeline_path)
            self.log.info(f"CWD set to [{self.release_pipeline_path}]")
            pipeline_def = self.common_utils.get_pipeline_definition(pipeline, self.organization, self.project)
            environments = pipeline_def.get(cs.PIPELINE_FILE_ENVIRONMENTS, None)
            if environments is not None:
                max_rank_stage = max(environments, key=lambda x: x[cs.PIPELINE_FILE_RANK])
                stage_to_delete = [stage for stage in environments if stage.get(cs.PIPELINE_STAGE_NAME) == self.ring_name.upper()]
                if len(stage_to_delete) >= 1:
                    max_rank_stage[cs.PIPELINE_FILE_RANK] = stage_to_delete[0][cs.PIPELINE_FILE_RANK]
                    pipeline_def[cs.PIPELINE_FILE_ENVIRONMENTS] = \
                        [stage for stage in environments if stage.get(cs.PIPELINE_STAGE_NAME) != self.ring_name.upper()]
            with open(self.filename, 'w') as file:
                json.dump(pipeline_def, file, indent=4)
            self.log.info("Updated pipeline definition to file")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_definition_from_file_phase_two(self):
        """
        Deletes the ring stage definition file the pipeline Json file
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Deleting pipeline stage definition from file")
            if not os.path.exists(self.release_pipeline_path):
                self.log.info(f"File path - [{self.release_pipeline_path}] doesn't exist. Create new one")
                os.makedirs(self.release_pipeline_path)
            self.log.info("Changing cwd")
            os.chdir(self.release_pipeline_path)
            self.log.info(f"CWD set to [{self.release_pipeline_path}]")
            pipeline_def = self.common_utils.get_pipeline_definition(self.pipeline_phase_two, self.organization, self.project)
            environments = pipeline_def.get(cs.PIPELINE_FILE_ENVIRONMENTS, None)
            if environments is not None:
                max_rank_stage = max(environments, key=lambda x: x[cs.PIPELINE_FILE_RANK])
                stage_to_delete = [stage for stage in environments if
                                   stage.get(cs.PIPELINE_STAGE_NAME) == self.ring_name.upper()]
                if len(stage_to_delete) >= 1:
                    max_rank_stage[cs.PIPELINE_FILE_RANK] = stage_to_delete[0][cs.PIPELINE_FILE_RANK]
                    pipeline_def[cs.PIPELINE_FILE_ENVIRONMENTS] = \
                        [stage for stage in environments if stage.get(cs.PIPELINE_STAGE_NAME) != self.ring_name.upper()]
            with open(self.filename, 'w') as file:
                json.dump(pipeline_def, file, indent=4)
            self.log.info("Updated pipeline definition to file")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def get_stage_content(self):
        """
        Gets the stage content for new ring
        Returns:
            JSON blob of the stage for new ring
        """
        self.log.info(f"Request received to get stage content for pipeline release - [{self.pipeline_phase_two}]")
        filename = self.pipeline_stage_blob_path
        with open(filename, 'r') as file:
            content = file.read()
            content = content.replace(cs.REPLACE_STR_RNAME, self.ring_name.upper())
            self.log.info(f"Returning back the content - [{content}]")
            return json.loads(content)

    def create_pipeline_variables(self):
        """
        Creates the required variables in devops for pipeline
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create pipeline variables")
            variable_group_id = self.config.VARIABLE_GROUP_ID
            variables_dict = {cs.VARIABLE_DEV_CC_NAME_NAME % self.ring_name.upper():
                                  cs.VARIABLE_CC_NAME_VALUE % self.ring_name.lower(),
                              cs.VARIABLE_DEV_CC_ENDPOINT_NAME % self.ring_name.upper():
                                  cs.VARIABLE_CC_ENDPOINT_VALUE % self.ring_name.lower(),
                              cs.VARIABLE_DEV_CC_RESOURCE_GROUP_NAME % self.ring_name.upper():
                                  cs.VARIABLE_CC_RESOURCE_GROUP_VALUE}
            self.log.info(f"Variables dictionary - [{variables_dict}]. Group Id - [{variables_dict}]")
            self.common_utils.create_pipeline_variables(variable_group_id, variables_dict,
                                                        self.organization, self.project)
            self.log.info("Pipeline variables created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def update_pipeline_variables(self):
        """
        Updates the required variables in devops for pipeline
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete pipeline variables")
            variable_group_id = self.config.VARIABLE_GROUP_ID
            variables_dict = {cs.VARIABLE_DEV_CC_RESOURCE_GROUP_NAME % self.ring_name.upper():
                                  cs.VARIABLE_CC_RESOURCE_GROUP_VALUE,
                              cs.VARIABLE_CC_RESOURCE_GROUP_NAME % self.ring_name.upper():
                                  cs.VARIABLE_CC_RESOURCE_GROUP_VALUE}
            self.log.info(f"Variables dictionary - [{variables_dict}]. Group Id - [{variables_dict}]")
            self.common_utils.update_pipeline_variables(variable_group_id, variables_dict,
                                                        self.organization, self.project)
            self.log.info("Pipeline variables created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_pipeline_variables(self, variable_name_list):
        """
        Deletes the required variables in devops for pipeline
        Args:
            variable_name_list(list)    --  List of variables to delete
        Returns:
            status(str)                 --  Passed/Failed based on the result of operation
            message(str)                --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete pipeline variables")
            variable_group_id = self.config.VARIABLE_GROUP_ID
            variables_list = []
            for var in variable_name_list:
                variables_list.append(var % self.ring_name.upper())
            self.log.info(f"Variables dictionary - [{variables_list}]. Group Id - [{variables_list}]")
            self.common_utils.delete_pipeline_variables(variable_group_id, variables_list,
                                                        self.organization, self.project)
            self.log.info("Pipeline variables deleted successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def set_orbit_app_CORS_allowed_domain(self):
        """
        Updates the CORS domain value
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to update CORS domain value")
            self.common_utils.update_CORS_allowed_origins_value(self.config.ORBIT_FUNCTION_APP,
                                                                self.config.ORBIT_RESOURCE_GROUP,
                                                                cs.CORS_ALLOWED_DOMAIN_ORBIT_APP_VALUE %
                                                                self.ring_name.lower())
            self.log.info("Updated CORS allowed origins value successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def remove_orbit_app_CORS_allowed_domain(self):
        """
        Removes the CORS domain value
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to remove CORS domain value")
            self.common_utils.remove_CORS_allowed_origins_value(self.config.ORBIT_FUNCTION_APP,
                                                                self.config.ORBIT_RESOURCE_GROUP,
                                                                cs.CORS_ALLOWED_DOMAIN_ORBIT_APP_VALUE %
                                                                self.ring_name.lower())
            self.log.info("Removed CORS allowed origins value successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Pipeline helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message
