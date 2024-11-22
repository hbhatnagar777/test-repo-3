# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""helper class for creating Azure resources and resources related operations

    AzureResourceHelper:

        __init__()                          --  Initializes Azure resource helper
        create_resources                    --  Creates all the required resources in Azure portal
        perform_clone_task                  --  Performs git clone task
        perform_checkout_task               --  Performs git checkout task
        wait_for_pr_complete                --  Waits for Pull Request to complete
        check_if_pr_complete                --  Checks if PR is complete
        perform_update_task                 --  Updates the terraform backend and variable files
        create_resources_with_terraform     --  Create resources with terraform tool
        perform_git_push_tasks              --  Performs git push task
        set_root_dir                        --  Sets the working directory
        set_terraform_dir                   --  Sets terraform directory as working directory
        update_file_content                 --  Updates the contents for a given file
        run_terraform_command               --  Runs a given terraform command
        execute_terraform_config            --  Starts with creating resources using terraform on Azure
        terraform_init                      --  Initializes terraform config file
        terraform_validate                  --  Validates terraform config file
        terraform_plan                      --  Plans terraform config resource deployment
        terraform_apply                     --  Creates the required resources in the terraform config file
        readd_backend_pool_target           --  Re-adds the backend pools target
        create_backend_pool                 --  Creates the required backend pools
        create_health_probe                 --  Creates health probe
        create_backend_settings             --  Creates the required backend settings
        create_listeners                    --  Creates the required listeners
        create_rules                        --  Creates the required rules in azure
        create_dns_records                  --  Creates the required DNS Records
        terraform_destroy                   --  Destroys the required resources in the terraform config file
        delete_backend_pool                 --  Deletes the backend pools
        delete_health_probe                 --  Deletes the health probe
        delete_backend_settings             --  deletes the backend settings
        delete_listeners                    --  Deletes the azure listeners
        delete_rules                        --  Deletes the rules in azure app gateway
        delete_dns_records                  --  Deletes the DNS Records in Azure Private DNS Zone
        app_exists                          --  Check if a given function app name already exists
        delete_resource_group               --  Deletes a given resource group
        resource_group_exists               --  Checks if a given resource group exists
"""

import os
import re
import shutil
import subprocess
import time
import requests
from time import sleep

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicHub.Helpers.azure_application_gateway_helper import AzureAppGatewayHelper
from MetallicHub.Utils.git_utils import GitUtils
from MetallicHub.Utils import Constants as cs
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper
from MetallicRing.Helpers.email_helper import EmailHelper
from MetallicRing.DBQueries import Constants as db_cs

_CONFIG = get_config(json_path=cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub


class AzureResourceHelper:
    """ contains helper class for managing Azure resources"""

    def __init__(self, ring_name, rid, subnet_info, config=_CONFIG.azure_credentials):
        """
        Initializes Azure resource helper
        Args:
            ring_name(str)              --  name of the ring
            rid(str)                    --  ID of the ring
            subnet_info(str)            --  subnet information for the azure resources
            config(dict)                --  Azure credentials to be used
        """
        super().__init__()
        self.log = logger.get_log()
        self.log.info("Initializing Azure Resource Helper")
        self.ring_name = ring_name
        self.rid = rid
        self.subnet_info = subnet_info
        self.terraform_clone_path = cs.HUB_TERRAFORM_CLONE_PATH % self.ring_name.lower()
        self.branch_name = f"automation_{self.ring_name}_branch"
        self.pat = config.AZ_PAT
        self.config = config
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET
        self.subscription_id = config.SUBSCRIPTION_ID
        self.tenant_id = config.TENANT_ID
        self.access_key = config.ACCESS_KEY
        os.environ["ARM_CLIENT_ID"] = self.client_id
        os.environ["ARM_CLIENT_SECRET"] = self.client_secret
        os.environ["ARM_SUBSCRIPTION_ID"] = self.subscription_id
        os.environ["ARM_TENANT_ID"] = self.tenant_id
        os.environ["ARM_ACCESS_KEY"] = self.access_key
        os.environ["AZURE_DEVOPS_EXT_PAT"] = self.pat
        self.git_util = GitUtils(cs.HUB_NON_PROD_REPO % self.pat,
                                 self.branch_name, cs.HUB_TERRAFORM_REPO_NAME)
        self.local_machine = Machine()
        self.retry_attempt = 0
        self.tf_pr_clone_path = cs.HUB_TF_CHECK_PR_COMPLETE_PATH % self.ring_name.lower()
        self.agh = AzureAppGatewayHelper(self.rid)
        self.log.info("Azure resource helper initialized")

    def create_resources(self):
        """
        Creates all the required resources in Azure portal
        """
        self.log.info("Request received to create resources in Azure")
        if not os.path.exists(self.terraform_clone_path):
            os.makedirs(self.terraform_clone_path)
        os.chdir(self.terraform_clone_path)
        self.git_util.git_clone()
        os.chdir(cs.HUB_TERRAFORM_CONFIG_FILE_PATH)
        self.git_util.git_checkout()
        shutil.copytree(cs.HUB_TERRAFORM_TEMPLATE_DIR, self.ring_name.lower())
        os.chdir(self.ring_name.lower())
        os.chdir(cs.HUB_TERRAFORM_CORE_DIR)
        self.update_file_content(cs.HUB_TERRAFORM_BACKEND_FILE)
        self.update_file_content(cs.HUB_TERRAFORM_TFVARS_FILE)

        self.execute_terraform_config()

        self.git_util.git_add()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.git_util.git_commit(cs.GIT_COMMIT_HUB_TERRAFORM_MESSAGE % timestamp)
        self.git_util.git_push()
        self.git_util.create_pr(cs.HUB_TERRAFORM_REPO_NAME)
        self.create_backend_pool()
        self.create_health_probe()
        self.create_backend_settings()
        self.create_listeners()
        self.create_rules()
        self.create_dns_records()
        self.log.info("Create resource complete")

    def perform_clone_task(self):
        """
        Performs git clone task
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Request received to perform clone for repo [{cs.HUB_TERRAFORM_REPO_NAME}]")
            self.log.info(f"Checking if the following directory exists [{self.terraform_clone_path}]")
            if not os.path.exists(self.terraform_clone_path):
                self.log.info("path doesn't exist. Creating the directories")
                os.makedirs(self.terraform_clone_path)
                self.log.info("Directories created")
            os.chdir(self.terraform_clone_path)
            self.log.info(f"CWD changes to [{self.terraform_clone_path}]. "
                          f"Checking if [{cs.HUB_TERRAFORM_REPO_NAME}] directory exists ")
            if os.path.exists(cs.HUB_TERRAFORM_REPO_NAME):
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                shutil.move(cs.HUB_TERRAFORM_REPO_NAME, f"{cs.HUB_TERRAFORM_REPO_NAME}_{timestamp}")
                self.log.info("Directory exists. Moving the directory to new path "
                              f"[{cs.HUB_TERRAFORM_REPO_NAME}_{timestamp}]")
            self.git_util.git_clone()
            self.log.info("Clone task complete")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def perform_checkout_task(self):
        """
        Performs git checkout task
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Checkout task received. Branch name = [{self.branch_name}]")
            self.set_root_dir()
            self.git_util.git_checkout()
            self.log.info("Checkout task complete")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def wait_for_pr_complete(self, pr_type=cs.CheckPRType.NEW):
        """
        Waits for Pull Request to complete
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Waiting for PR task to complete. PR type - [{pr_type}]")
            pr_status = False
            email = EmailHelper(self.ring_name, self.ring_name)
            while not pr_status:
                pr_status = self.check_if_pr_complete(pr_type)
                if not pr_status:
                    self.log.info("PR status not complete. Sleeping for 10 mins. Sending mail")
                    email.send_pr_mail()
                    self.log.info("Reminder mail sent successfully.")
                    time.sleep(10 * 60)
                else:
                    self.log.info("PR complete. We are ready to start the pipeline")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def check_if_pr_complete(self, pr_type=cs.CheckPRType.NEW):
        """
        Checks if PR is complete
        Returns:
            Bool    --  True if PR is complete
                        False if PR is not complete
        """
        self.log.info("Request received to check if PR task is complete")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        clone_path = os.path.join(self.tf_pr_clone_path, timestamp)
        if not os.path.exists(clone_path):
            os.makedirs(clone_path)
        self.log.info(f"Cloning to path [{clone_path}]")
        os.chdir(clone_path)
        self.git_util.git_clone()
        self.log.info("Clone complete. Checking for file presence")
        os.chdir(cs.HUB_TERRAFORM_CONFIG_FILE_PATH)
        check_file = os.path.join(self.ring_name.lower(), cs.HUB_TERRAFORM_CORE_DIR, cs.HUB_TERRAFORM_TFVARS_FILE)
        if os.path.exists(check_file):
            self.log.info(f"[{check_file}] is present in the new clone. PR task complete")
            pr_status = True
        else:
            self.log.info(f"[{check_file}] is not present in the new clone. PR task incomplete")
            pr_status = False
        os.chdir(self.tf_pr_clone_path)
        shutil.rmtree(timestamp, ignore_errors=True)
        self.log.info("Cleaned up cloned directory")
        return pr_status

    def perform_update_task(self):
        """
        Updates the terraform backend and variable files
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("updating terraform config files")
            self.set_root_dir()
            shutil.copytree(cs.HUB_TERRAFORM_TEMPLATE_DIR, self.ring_name.lower())
            os.chdir(self.ring_name.lower())
            os.chdir(cs.HUB_TERRAFORM_CORE_DIR)
            self.update_file_content(cs.HUB_TERRAFORM_BACKEND_FILE)
            self.update_file_content(cs.HUB_TERRAFORM_TFVARS_FILE)
            self.log.info("updated terraform logs files")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute  Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_resources_with_terraform(self):
        """
        Create resources with terraform tool
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Creating resources with terraform")
            self.set_terraform_dir()
            self.execute_terraform_config()
            self.log.info("Terraform resources created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute  Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def perform_git_push_tasks(self, add_all=True):
        """
        Performs git push task
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Performing git push tasks. Setting root directory")
            self.set_root_dir()
            self.git_util.git_add(add_all)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            self.git_util.git_commit(cs.GIT_COMMIT_HUB_TERRAFORM_MESSAGE % timestamp)
            self.git_util.git_push()
            self.git_util.create_pr(cs.HUB_TERRAFORM_REPO_NAME)
            self.log.info("Pushed changes to REPO")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute  Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def set_root_dir(self):
        """
        Sets the working directory
        """
        self.log.info(f"setting root directory - [{self.terraform_clone_path}]"
                      f"child dir - [{cs.HUB_TERRAFORM_CONFIG_FILE_PATH}]")
        os.chdir(self.terraform_clone_path)
        os.chdir(cs.HUB_TERRAFORM_CONFIG_FILE_PATH)

    def set_terraform_dir(self):
        """
        Sets terraform directory as working directory
        """
        self.set_root_dir()
        self.log.info(f"Setting terraform dir [{self.ring_name}//{cs.HUB_TERRAFORM_CORE_DIR}]")
        os.chdir(self.ring_name.lower())
        os.chdir(cs.HUB_TERRAFORM_CORE_DIR)

    def update_file_content(self, filename):
        """
        Updates the contents for a given file
        Args:
            filename(str)       --  name of the file
        """
        self.log.info(f"Request received to update file contents - [{filename}]")
        with open(filename, 'r') as file:
            content = file.read()
            content = content.replace(cs.REPLACE_STR_RNAME, self.ring_name.lower())
            content = content.replace(cs.REPLACE_STR_RID, self.rid)
            if filename == cs.HUB_TERRAFORM_TFVARS_FILE:
                sql_helper = SQLiteDBQueryHelper()
                result = sql_helper.execute_query(db_cs.GET_SUBNET_QUERY)
                subnet = result.rows[0][0]
                content = content.replace(cs.REPLACE_STR_SUBNET, subnet)
                sql_helper.execute_query(db_cs.UPDATE_SUBNET_RING_QUERY % (self.ring_name.lower(), subnet))
        with open(filename, 'w') as file:
            # Write the modified content back to the file
            file.write(content)
        self.log.info(f"update file content - [{content}]")

    def run_terraform_command(self, command):
        """
        Runs a given terraform command
        Args:
            command(str)        --  Command to be executed
        Raises:
            Exception when command fails to return expected results
        Returns:
            Command output either formatted or raw output
        """
        self.log.info(f"Request received to run the following command - [{command}]")
        command_op = self.local_machine.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '', command_op.exception_message))
        if command_op.exception:
            raise Exception(command_op.exception_code, re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '',
                                                              command_op.exception))
        if isinstance(command_op.formatted_output, str):
            result = command_op.formatted_output.strip()
        else:
            result = command_op.output.strip()
        result = re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '', result)
        self.log.info(f"Result of terraform command execution: [{result}]")
        return result

    def execute_terraform_config(self):
        """
        Starts with creating resources using terraform on Azure
        """
        self.log.info("Request received to start the terraform config file execution")
        self.terraform_init(os.getcwd())
        self.terraform_validate(os.getcwd())
        self.terraform_plan(os.getcwd())
        self.terraform_apply(os.getcwd())
        self.log.info("Terraform configuration ran successfully")

    def terraform_init(self, path):
        """
        Initializes terraform config file
        Args:
            path(str)           --  path for the terraform config file
        Raises:
            Exception if terraform initialization fails
        """
        try:
            os.chdir(path)
            self.log.info("Initializing terraform configs")
            cmd = "terraform2 init"
            op = self.run_terraform_command(cmd)
            self.log.info(f"Terraform init complete - [{op}]")
        except Exception as exp:
            self.retry_attempt += 1
            self.log.info(f"Exception occurred - [{exp}]. Retrying again")
            if self.retry_attempt < cs.MAX_RETRY_LIMIT:
                self.terraform_init(path)
            else:
                raise exp

    def terraform_validate(self, path):
        """
        Validates terraform config file
        Args:
            path(str)           --  path for the terraform config file
        Raises:
            Exception if terraform validation fails
        """
        os.chdir(path)
        self.log.info("Validating terraform configs")
        cmd = "terraform2 validate"
        op = self.run_terraform_command(cmd)
        self.log.info(f"Terraform validate complete - [{op}]")

    def terraform_plan(self, path):
        """
        Plans terraform config resource deployment
        Args:
            path(str)           --  path for the terraform config file
        Raises:
            Exception if terraform plan fails
        """
        os.chdir(path)
        self.log.info("Planning terraform configs")
        cmd = "terraform2 plan"
        op = self.run_terraform_command(cmd)
        self.log.info(f"Terraform plan complete - [{op}]")

    def terraform_apply(self, path):
        """
        Creates the required resources in the terraform config file
        Args:
            path(str)           --  path for the terraform config file
        Raises:
            Exception if terraform plan fails
        """
        try:
            os.chdir(path)
            self.log.info("Applying terraform configs")
            cmd = "terraform2 apply -parallelism=1 -auto-approve"
            op = self.run_terraform_command(cmd)
            self.log.info(f"Terraform apply complete - [{op}]")
            # TODO: Remove this step once the terraform side code is fixed
            self.log.info("Enabling Vnet integration for function apps")
            self.agh.enable_vnet_integration(cs.CORE_FUNCTION_APP_NAME % self.ring_name.lower())
            self.agh.enable_vnet_integration(cs.BIZ_FUNCTION_APP_NAME % self.ring_name.lower())
            self.agh.enable_vnet_integration(cs.CORE_FUNCTION_APP_NAME % self.ring_name.lower(), is_staging=True)
            self.agh.enable_vnet_integration(cs.BIZ_FUNCTION_APP_NAME % self.ring_name.lower(), is_staging=True)
        except Exception as exp:
            self.log.info(f"Exception occurred - [{exp}]. Sleeping for a minute")
            sleep(60)
            self.retry_attempt += 1
            if self.retry_attempt < cs.MAX_RETRY_LIMIT:
                self.terraform_apply(path)
            else:
                raise exp
        sleep(60 * 2)
        self.log.info("Sleep complete. Resources are initialized")

    def terraform_destroy(self, path, max_retry_limit=2):
        """
        Destroys the required resources in the terraform config file
        Args:
            path(str)           --  path for the terraform config file
        Raises:
            Exception if terraform destroy fails
        """
        try:
            self.log.info("Destroying terraform configs")
            cmd = "terraform2 destroy -parallelism=1 -auto-approve"
            op = self.run_terraform_command(cmd)
            self.log.info(f"Terraform destroy complete - [{op}]")
        except Exception as exp:
            self.log.info(f"Exception occurred - [{exp}]. Sleeping for a minute")
            sleep(60)
            self.retry_attempt += 1
            if self.retry_attempt < max_retry_limit:
                self.terraform_destroy(path)
            else:
                self.log.info("Destroy resources failed. Manually cleanup the resources")
        self.log.info("Resources are destroyed")

    def readd_backend_pool_target(self):
        """
        Re-adds the backend pools target
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to re-add backend pool target")
            ag_biz_bp = cs.AG_BP_BIZ % self.rid
            ag_core_bp = cs.AG_BP_CORE % self.rid
            self.agh.remove_backend_pool_with_target(ag_biz_bp)
            self.agh.add_backend_pool_with_target(ag_biz_bp, cs.AG_AS_BIZ % self.ring_name.lower())
            self.agh.remove_backend_pool_with_target(ag_core_bp)
            self.agh.add_backend_pool_with_target(ag_core_bp, cs.AG_AS_CORE % self.ring_name.lower())
            self.log.info("Backend pools re-added successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_backend_pool(self):
        """
        Creates the required backend pools
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create backend pools")
            ag_biz_bp = cs.AG_BP_BIZ % self.rid
            ag_core_bp = cs.AG_BP_CORE % self.rid
            ag_web_bp = cs.AG_BP_WEB % self.rid
            ag_wec_bp = cs.AG_BP_WEC % self.rid
            self.agh.create_backend_pool(ag_biz_bp)
            self.agh.add_backend_pool_with_target(ag_biz_bp, cs.AG_AS_BIZ % self.ring_name.lower())
            self.agh.create_backend_pool(ag_core_bp)
            self.agh.add_backend_pool_with_target(ag_core_bp, cs.AG_AS_CORE % self.ring_name.lower())
            self.agh.create_backend_pool(ag_web_bp)
            self.agh.add_backend_pool_web_address(cs.STORAGE_CONTAINER_NAME % self.ring_name.lower(), ag_web_bp)
            self.agh.create_backend_pool(ag_wec_bp)
            self.agh.add_backend_pool_with_address(ag_wec_bp, cs.AG_WC_APP)
            self.log.info("Backend pools created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_backend_pool(self):
        """
        Deletes the backend pools
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete backend pools")
            ag_biz_bp = cs.AG_BP_BIZ % self.rid
            ag_core_bp = cs.AG_BP_CORE % self.rid
            ag_web_bp = cs.AG_BP_WEB % self.rid
            ag_wec_bp = cs.AG_BP_WEC % self.rid
            self.agh.delete_backend_pool(ag_biz_bp)
            self.agh.delete_backend_pool(ag_core_bp)
            self.agh.delete_backend_pool(ag_web_bp)
            self.agh.delete_backend_pool(ag_wec_bp)
            self.log.info("Backend pools deleted successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_health_probe(self):
        """
        Creates health probe
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create health probes")
            self.agh.add_health_probe(cs.AG_RING_WC_PROBE % self.rid,
                                      cs.AG_RING_WC_HOST_VALUE % self.ring_name.lower(),
                                      path=cs.AG_HP_WC_ENDPOINT)
            self.log.info("Health probes created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_health_probe(self):
        """
        Deletes the health probe
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete health probes")
            self.agh.delete_health_probe(cs.AG_RING_WC_PROBE % self.rid)
            self.log.info("Health probes deleted successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_backend_settings(self):
        """
        Creates the required backend settings
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create backend settings")
            self.agh.add_backend_settings(cs.AG_BS_WEB % self.rid, 443, "Disabled", enable_probe=1,
                                          probe_name=cs.AG_ORBIT_WEB_PROBE)
            self.agh.add_backend_settings(cs.AG_BS_BIZ % self.rid, 443, "Disabled", "/api/", enable_probe=1,
                                          probe_name=cs.AG_ORBIT_API_PROBE)
            self.agh.add_backend_settings(cs.AG_BS_CORE % self.rid, 443, "Disabled", "/api/", enable_probe=1,
                                          probe_name=cs.AG_ORBIT_API_PROBE)
            self.agh.add_backend_settings(cs.AG_BS_WEC % self.rid, 443, "Enabled", path=None, enable_probe=1,
                                          probe_name=cs.AG_RING_WC_PROBE % self.rid,
                                          affinity_name="ApplicationGatewayAffinity", request_timeout=1800,
                                          override_hostname=0)
            self.log.info("Backend settings created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_backend_settings(self):
        """
        deletes the backend settings
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete backend settings")
            self.agh.delete_backend_settings(cs.AG_BS_WEB % self.rid)
            self.agh.delete_backend_settings(cs.AG_BS_BIZ % self.rid)
            self.agh.delete_backend_settings(cs.AG_BS_CORE % self.rid)
            self.agh.delete_backend_settings(cs.AG_BS_WEC % self.rid)
            self.log.info("Backend settings deleted successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_listeners(self):
        """
        Creates the required listeners
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create listeners")
            self.agh.create_listener(cs.AG_LISTENER_NAME % self.rid,
                                     cs.AG_RING_WC_HOST_VALUE % self.ring_name.lower())
            self.log.info("Listeners created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_listeners(self):
        """
        Deletes the azure listeners
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete listeners")
            self.agh.delete_listener(cs.AG_LISTENER_NAME % self.rid)
            self.log.info("Listeners deleted successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_rules(self):
        """
        Creates the required rules in azure
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create rules")
            ag_web_bp = cs.AG_BP_WEB % self.rid
            ag_wec_bp = cs.AG_BP_WEC % self.rid
            ag_core_bp = cs.AG_BP_CORE % self.rid
            ag_biz_bp = cs.AG_BP_BIZ % self.rid

            ag_web_bs = cs.AG_BS_WEB % self.rid
            ag_wec_bs = cs.AG_BS_WEC % self.rid
            ag_core_bs = cs.AG_BS_CORE % self.rid
            ag_biz_bs = cs.AG_BS_BIZ % self.rid

            wec_rule = cs.PB_WEC_RULE_NAME % self.rid
            web_rule = cs.PB_WEB_RULE_NAME % self.rid
            biz_rule = cs.PB_BIZ_RULE_NAME % self.rid
            core_rule = cs.PB_CORE_RULE_NAME % self.rid
            app_gateway_rule_name = cs.AG_RULE_NAME % self.rid
            self.agh.create_url_path_map(app_gateway_rule_name, wec_rule, ag_wec_bp, ag_wec_bs, cs.PB_WEC_PATH)
            self.agh.create_path_map_rule(biz_rule, app_gateway_rule_name, ag_biz_bp, ag_biz_bs, cs.PB_BIZ_PATH)
            self.agh.create_path_map_rule(core_rule, app_gateway_rule_name, ag_core_bp, ag_core_bs, cs.PB_CORE_PATH)
            self.agh.create_path_map_rule(web_rule, app_gateway_rule_name, ag_web_bp, ag_web_bs, cs.PB_WEB_PATH)
            self.agh.create_rules(app_gateway_rule_name, app_gateway_rule_name, cs.AG_LISTENER_NAME % self.rid,
                                  ag_web_bp, ag_web_bs)
            self.log.info("Rules created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_rules(self):
        """
        Deletes the rules in azure app gateway
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete rules")
            app_gateway_rule_name = cs.AG_RULE_NAME % self.rid
            web_rule = cs.PB_WEB_RULE_NAME % self.rid
            biz_rule = cs.PB_BIZ_RULE_NAME % self.rid
            core_rule = cs.PB_CORE_RULE_NAME % self.rid
            self.agh.delete_rules(app_gateway_rule_name)
            self.agh.delete_path_map_rule(app_gateway_rule_name, biz_rule)
            self.agh.delete_path_map_rule(app_gateway_rule_name, core_rule)
            self.agh.delete_path_map_rule(app_gateway_rule_name, web_rule)
            self.agh.delete_path_map(app_gateway_rule_name)
            self.log.info("Rules deleted successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def create_dns_records(self):
        """
        Creates the required DNS Records
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to create DNS A records")
            dns_zone = self.config.PRIVATE_DNS_ZONE
            resource_group = self.config.P_DNS_RESOURCE_GROUP
            hub_core_fun_app_name = cs.CORE_FUNCTION_APP_NAME % self.ring_name.lower()
            hub_biz_fun_app_name = cs.BIZ_FUNCTION_APP_NAME % self.ring_name.lower()
            hub_core_record_name = cs.DNS_A_REC_CORE % self.ring_name.lower()
            hub_core_scm_record_name = cs.DNS_A_REC_CORE_SCM % self.ring_name.lower()
            hub_biz_record_name = cs.DNS_A_REC_BIZ % self.ring_name.lower()
            hub_biz_scm_record_name = cs.DNS_A_REC_BIZ_SCM % self.ring_name.lower()
            core_address = self.agh.get_function_app_ip_addr(hub_core_fun_app_name)
            biz_address = self.agh.get_function_app_ip_addr(hub_biz_fun_app_name)
            self.agh.create_az_dns_record(hub_core_record_name, core_address, resource_group, dns_zone)
            self.agh.create_az_dns_record(hub_core_scm_record_name, core_address, resource_group, dns_zone)
            self.agh.create_az_dns_record(hub_biz_record_name, biz_address, resource_group, dns_zone)
            self.agh.create_az_dns_record(hub_biz_scm_record_name, biz_address, resource_group, dns_zone)
            self.log.info("Created all the records of DNS")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_dns_records(self):
        """
        Deletes the DNS Records in Azure Private DNS Zone
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to delete DNS A records")
            dns_zone = self.config.PRIVATE_DNS_ZONE
            resource_group = self.config.P_DNS_RESOURCE_GROUP
            hub_core_record_name = cs.DNS_A_REC_CORE % self.ring_name.lower()
            hub_core_scm_record_name = cs.DNS_A_REC_CORE_SCM % self.ring_name.lower()
            hub_biz_record_name = cs.DNS_A_REC_BIZ % self.ring_name.lower()
            hub_biz_scm_record_name = cs.DNS_A_REC_BIZ_SCM % self.ring_name.lower()
            self.agh.delete_az_dns_record(hub_core_record_name, resource_group, dns_zone)
            self.agh.delete_az_dns_record(hub_core_scm_record_name, resource_group, dns_zone)
            self.agh.delete_az_dns_record(hub_biz_record_name, resource_group, dns_zone)
            self.agh.delete_az_dns_record(hub_biz_scm_record_name, resource_group, dns_zone)
            self.log.info("Deleted all the records of DNS")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure resource helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def delete_resource_group(self, rg_name):
        """
        Deletes a given resource group
        Args:
            rg_name(str)        --  Name of the resource group
        """
        if self.resource_group_exists(rg_name):
            cmd = f"az group delete --name {rg_name} --subscription {self.subscription_id} --yes"
            self.agh.run_command(cmd)
            self.log.info("Resource group deleted successfully")
        else:
            self.log.info("Resource group doesn't exist")

    def resource_group_exists(self, rg_name):
        """
        Checks if a given resource group exists
        Args:
            rg_name(str)        --  Name of the resource group
        """
        cmd = f"az group show --name '{rg_name}' --subscription {self.subscription_id} --query id --output tsv 2>$null"
        result = self.agh.run_command(cmd)
        if not result.strip():
            return False
        return True


def app_exists(app_name):
    """
    Check if a given function app name already exists
    Args:
        app_name(str)       --  Name of the function app
    returns:
        bool                -- True if app is present. Else false
    """
    function_endpoint = cs.FUNCTION_APP_DOMAIN % app_name
    try:
        response = requests.get(function_endpoint)
        if response.status_code == 404:
            return False
        return True
    except requests.exceptions.RequestException as e:
        return False
