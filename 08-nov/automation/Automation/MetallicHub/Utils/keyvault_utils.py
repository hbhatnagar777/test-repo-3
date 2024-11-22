# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Helper class for azure keyvault related function

    KeyVaultUtils:
        __init__()                      --  Initializes Keyvault helper util class
        create_secret                   --  Create the required secret in keyvault
        check_if_secret_exists          --  Checks if a given secret exists in keyvault
        get_secret_url                  --  Gets the secret URL
        set_access_policy               --  Sets the required access policy given object ID in Azure portal

"""
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from MetallicHub.Utils import Constants as cs


class KeyVaultUtils:
    """ helper class for Key Vault Related operations"""

    def __init__(self, vault_name):
        """
        Initializes Azure key vault helper
        Args:
            vault_name(str)         --  Name of the key vault
        """
        super().__init__()
        self.log = logger.get_log()
        self.vault_name = vault_name
        self.local_machine = Machine()

    def create_secret(self, secret_name, value):
        """
        Create the required secret in keyvault
        Args:
            secret_name(str)        --  Name of the secret
            value(str)              --  Value of the secret
        Raises:
            Exception if secret creation fails
        """
        # if self.check_if_secret_exists(secret_name):
        self.log.info(f"Creating secret with name [{secret_name}], [{value}]")
        cmd = f"az keyvault secret set --vault-name {self.vault_name} --name {secret_name} --value '{value}'"
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        self.log.info("Secret created successfully")

    def check_if_secret_exists(self, secret_name):
        """
        Checks if a given secret exists in keyvault
        Args:
            secret_name(str)        --  name of the secret
        Returns:
            Boolean                 --  True if secret exists
                                        Else False
        Raises:
            Exception when exception is thrown with AZ cli command to show secret
        """
        self.log.info("Checking if secret exists")
        cmd = f"az keyvault secret show --vault-name {self.vault_name} --name {secret_name}"
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            if cs.SECRET_NOT_FOUND_EXCEPTION in command_op.exception_message:
                self.log.info("Secret not found")
                return False
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        self.log.info("Secret is already present")
        return True

    def get_secret_url(self, secret_name):
        """
        Gets the secret URL
        Args:
            secret_name(str)        --  Name of the secret
        Returns:
            string containing the secret URL
        Raises:
            Exception when command execution fails
        """
        self.log.info(f"Request received to get secret URL for secret name - [{secret_name}]")
        cmd = f"az keyvault secret show --name {secret_name} --vault-name {self.vault_name} --query 'id'"
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        return command_op.formatted_output.strip('"')

    def set_access_policy(self, object_id, subscription_id):
        """
        Sets the required access policy given object ID in Azure portal
        Args:
            object_id(str)          --  ID of the object
            subscription_id(str)    --  Azure subscription ID
        Returns:
            string output for the execution of the set access policy command
        Raises:
            Exception when command execution fails
        """
        cmd = f"az keyvault set-policy --name {self.vault_name} --object-id {object_id} " \
              "--secret-permissions get list " \
              f"--key-permissions get list --subscription {subscription_id}"
        command_op = self.local_machine.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        return command_op.formatted_output
