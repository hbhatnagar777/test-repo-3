# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" helper class for Creating, configuring VMs and installing Metallic software on a Metallic Ring

    TerraformHelper:

        __init__()                      --  Initializes Terraform Helper

        allow_terraform_provider        --  Enables remote execution of terraform commands in a Hyperv machine

        execute_terraform_config        -- Executes the given terraform config file

        cleanup_terraform_config        -- Cleans up any existing config files present in the config directory

        terraform_init                  -- Initializes terraform config file

        terraform_validate              -- Validates terraform config file

        terraform_plan                  -- Plans terraform config resource deployment

        terraform_apply                 -- Creates the required resources in the terraform config file

        terraform_destroy               -- Destroys the required resources in the terraform config file

        execute_terraform_command       -- Executes the given terraform command

"""
import os
import re
import shutil
from time import sleep
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class TerraformHelper(BaseRingHelper):
    """ helper class for Creating, configuring VMs and installing Metallic software on a Metallic Ring"""

    def __init__(self, config_path, host_type, host_user, host_pass):
        """
        Initializes VM provisioning helper
        """
        super().__init__(ring_commcell=None)
        self.log.info("Initializing Terraform Helper")
        self.config_path = config_path
        self.host_type = host_type
        self.username = host_user
        self.password = host_pass
        self.local_machine = Machine()
        self.terraform_init_attempt = 0
        self.max_attempt = 5

    def execute_terraform_config(self):
        """
        Executes the given terraform config file
        """
        self.log.info("Request received to start the terraform config file execution")
        self.terraform_init()
        self.terraform_validate()
        self.terraform_plan()
        self.terraform_apply()
        self.log.info("Terraform configuration execution complete")

    def cleanup_terraform_config(self):
        """
        Cleans up any existing config files present in the config directory
        """
        path = os.path.dirname(self.config_path)
        exclude = os.path.basename(self.config_path)
        for file_or_folder in os.listdir(path):
            if file_or_folder != exclude:
                file_or_folder_path = os.path.join(path, file_or_folder)
                if os.path.isfile(file_or_folder_path):
                    os.remove(file_or_folder_path)
                else:
                    shutil.rmtree(file_or_folder_path)

    def terraform_init(self):
        """
        Initializes terraform config file
        Raises:
            Exception if terraform initialization fails
        """
        path = self.config_path
        self.log.info("Request received to init terraform config")
        command = f"terraform -chdir='{os.path.dirname(path)}' init"
        result = self.execute_terraform_command(command)
        if cs.TERRAFORM_INIT_SUCCESS.lower() not in result.lower():
            self.terraform_init_attempt += 1
            if self.terraform_init_attempt >= self.max_attempt:
                raise Exception(f"Terraform init failure. [{result}]")
            self.log.info(f"Terraform init failure. Will retry again. Attempt [{self.terraform_init_attempt}]")
            self.terraform_init()
            return
        self.log.info("Terraform init complete")

    def terraform_validate(self):
        """
        Validates terraform config file
        Raises:
            Exception if terraform validation fails
        """
        path = self.config_path
        self.log.info("Validating terraform config")
        command = f"terraform -chdir='{os.path.dirname(path)}' validate"
        result = self.execute_terraform_command(command)
        if cs.TERRAFORM_VALIDATION_SUCCESS.lower() not in result.lower():
            raise Exception(f"Terraform validation failure. [{result}]")
        self.log.info("Terraform validation successful")

    def terraform_plan(self, resources=5):
        """
        Plans terraform config resource deployment
        Args:
            resources(int)      --  Number of resources to plan
        Raises:
            Exception if terraform plan fails
        """
        path = self.config_path
        self.log.info("In terraform plan phase")
        command = f"terraform -chdir='{os.path.dirname(path)}' plan"
        result = self.execute_terraform_command(command)
        plan_result = cs.TERRAFORM_PLAN_SUCCESS % resources
        if plan_result.lower() not in result.lower():
            raise Exception(f"Terraform plan failure. [{result}]")
        self.log.info(f"[{plan_result}]\n\nTerraform plan complete")

    def terraform_apply(self, resources=5):
        """
        Creates the required resources in the terraform config file
        Args:
            resources(int)      --  Number of resources to plan
        Raises:
            Exception if terraform plan fails
        """
        path = self.config_path
        self.log.info("Performing Terraform Apply")
        command = f"terraform -chdir='{os.path.dirname(path)}' apply -auto-approve"
        result = self.execute_terraform_command(command)
        apply_result = cs.TERRAFORM_APPLY_SUCCESS % resources
        if apply_result.lower() not in result.lower():
            raise Exception(f"Terraform Apply failure. [{result}]")
        self.log.info("Sleeping for couple of minutes to let the VMs get initialized")
        sleep(60 * 2)
        self.log.info("Sleep complete. VMs are initialized")

    def terraform_destroy(self, resources=5):
        """
        Destroys the required resources in the terraform config file
        Args:
            resources(int)      --  Number of resources to destroy
        Raises:
            Exception if terraform destroy fails
        """
        path = self.config_path
        self.log.info("Performing Terraform destroy")
        command = f"terraform -chdir='{os.path.dirname(path)}' destroy -auto-approve"
        result = self.execute_terraform_command(command)
        destroy_result = cs.TERRAFORM_DESTROY_SUCCESS % resources
        if destroy_result.lower() not in result.lower():
            raise Exception(f"Terraform destroy failure. [{result}]")
        self.log.info("Destroy complete")

    def execute_terraform_command(self, command):
        """
        Executes the given terraform command
        Args:
            command(str)    --  Command to execute
        Raises:
            Exception,
                If host type is not supported
                If command execution fails with an exception
        """
        cmd = ""
        if self.host_type == cs.VMHost.HYPERV:
            if self.username is not None:
                cmd = f"$env:HYPERV_USER='{self.username}';"
            if self.password is not None:
                cmd += f"$env:HYPERV_PASSWORD='{self.password}';"
        else:
            raise Exception(f"Host Type is not supported - [{self.host_type.name}]")
        cmd += command
        self.log.info(f"Terraform command received is  [{command}]")
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '', command_op.exception_message))
        if command_op.exception:
            raise Exception(command_op.exception_code, re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '',
                                                              command_op.exception))
        if isinstance(command_op.formatted_output, str):
            result = command_op.formatted_output.strip()
            result = re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '', result)
        else:
            result = command_op.output.strip()
        self.log.info(f"Result of terraform command execution: [{result}]")
        return result
