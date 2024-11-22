# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file to perform  AzureHelper Operations

AzureHelper:

    __init__                    --  Initializes instance of AzureHelper class with azure App credentials

AzureResourceGroup:

    __init__                            --  Initializes instance of AzureResourceGroup class

    check_if_resource_group_exists()    --  Method to check if resource group exists

    create_resource_group()             --  Method to create a resource group

    delete_resource_group()             --  Method to delete a resource group

    resource_group_list()               --  Method to return list of resource groups under a subscription

AzureCustomDeployment:

    __init__                    --      Initializes instance of AzureCustomDeployment class

    deploy()                    --      Method to deploy the template to a resource group

    get_deployment_details()    --      Method to get the deployment details

    get_backup_gateway_name()   --      Method to get the vm name from the outputs after the custom deployment

AzureVMOperations:

    __init__                    --      Initializes instance of AzureVMOperations class

    power_on_machine()          --      Method to power on existinng virtual machine
    
AzureAuthToken:

    __init__                            --      Initializes instance of AzureAuthToken class

    generate_auth_token_iam_ad_auth     --      Method to generate auth token for IAM AD App

    generate_auth_token_mi_ad_auth       --     Method to generate Auth token for Azure Managed Identity based authentication
"""

import json
import os
import time
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import Deployment
from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.models import DeploymentProperties
from azure.mgmt.compute import ComputeManagementClient
from AutomationUtils import logger, constants
from AutomationUtils.config import get_config
from msal import ConfidentialClientApplication
from AutomationUtils.machine import Machine

_CONFIG_DATA = get_config()


class AzureHelper:
    """ Helper class to perform Azure SDK common operations """

    def __init__(self):
        """ Initializes instance of AzureHelper class with azure App credentials """
        self.log = logger.get_log()
        self.subscription_id = _CONFIG_DATA.Azure.Subscription
        self.credential = None
        self.client = None

        try:
            self.credential = ClientSecretCredential(
                client_id=_CONFIG_DATA.Azure.App.ApplicationID,
                client_secret=_CONFIG_DATA.Azure.App.ApplicationSecret,
                tenant_id=_CONFIG_DATA.Azure.Tenant
            )

            if self.subscription_id is not None:
                self.client = ResourceManagementClient(
                    self.credential, self.subscription_id)
                self.log.info("Resource Management Client Object creation successful.")

            else:
                raise Exception("Please provide valid Azure subscription ID")

        except Exception as exp:
            self.log.exception("Resource Management Client Object creation failed.")
            raise exp


class AzureResourceGroup(AzureHelper):
    """ class to perform Azure SDK common operations """

    def __init__(self):
        """ Initializes instance of AzureResourceGroup class """
        super().__init__()

    def check_if_resource_group_exists(self, rg_name):
        """
        Method to check if resource group exists
        Args:
            rg_name (str)    --  Name of the resource group

        Returns:
            bool        --  True if Resource group is present
        """
        return self.client.resource_groups.check_existence(rg_name)

    def create_resource_group(self, rg_name, rg_params):
        """
        Method to create a resource group
        Args:
            rg_name     (str)   --  Name of the resource group

            rg_params   (dict)  --  required parameters for resource group
                                    {'location': location} where resource group must be created.
        """
        self.log.info("Creating resource_group")
        rg_response = self.client.resource_groups.create_or_update(rg_name, rg_params)
        self.log.info(f"Provisioned resource group {rg_response.name} in the {rg_response.location} region.")

    def delete_resource_group(self, rg_name):
        """
        Method to delete a resource group
        Args:
            rg_name (str)    --  Name of the resource group
        """
        if self.check_if_resource_group_exists(rg_name):
            self.log.info(f"Resource group {rg_name} deleting...")
            self.client.resource_groups.begin_delete(rg_name).result()
        self.log.info(f"Resource group {rg_name} deleted.")

    def resource_group_list(self):
        """
        Method to return list of resource groups under a subscription
        Returns:
            list        --  List of Resource groups under a subscription
        """
        try:
            resource_groups = list()
            rg_iterator = self.client.resource_groups.list()
            if not rg_iterator:
                raise Exception("Failed to Fetch Resource groups list")
            for group in rg_iterator:
                resource_groups.append(group.name)
            self.log.info(f"Resource groups list {resource_groups} is fetched successfully")
            return resource_groups
        except Exception as exp:
            self.log.error(exp)
            raise exp


class AzureCustomDeployment(AzureHelper):
    """ Class to perform Azure Custom Deployment operations using Azure SDK """

    def __init__(self):
        """ Initializes instance of AzureCustomDeployment class """

        super().__init__()
        timestamp = str(int(time.time()))
        self.deployment_name = f"auto-deployment-{timestamp}"
        self.vm_name = f"auto-{timestamp}"

    def deploy(self, rg_name, authcode, deployment_name=None):
        """
        Method to deploy the template to a resource group
        Args:
            rg_name         (str)   --  Name of the resource group

            authcode        (str)   --  Company Authcode to map the deployed VM

            deployment_name (str)   --  Name of the deployment
        """

        if deployment_name is None:
            deployment_name = self.deployment_name

        path = os.path.join(constants.AUTOMATION_DIRECTORY, 'CoreUtils')

        template_path = os.path.join(path, 'Templates', 'template-azuredb.json')
        with open(template_path, 'r') as template_file_fd:
            template = json.load(template_file_fd)

        user_assigned_identities = dict()

        for identity in _CONFIG_DATA.AzureDB.identities:
            if identity.rg_name and identity.identity_name:
                key = f"/subscriptions/{self.subscription_id}/resourceGroups/{identity.rg_name}/" \
                      f"providers/Microsoft.ManagedIdentity/userAssignedIdentities/{identity.identity_name}"
                user_assigned_identities[key] = {}

        parameters = {
            'location': _CONFIG_DATA.AzureDB.location,
            'vmName': self.vm_name,
            'adminUsername': _CONFIG_DATA.AzureDB.admin_username,
            'adminPassword': _CONFIG_DATA.AzureDB.admin_password,
            'virtualNetworkNewOrExisting': _CONFIG_DATA.AzureDB.virtual_network_new_or_existing,
            'virtualNetworkName': _CONFIG_DATA.AzureDB.virtual_network_name,
            'virtualNetworkResourceGroupName': _CONFIG_DATA.AzureDB.virtual_network_resource_group_name,
            'addressPrefixes': _CONFIG_DATA.AzureDB.address_prefixes,
            'subnetName': _CONFIG_DATA.AzureDB.subnet_name,
            'subnetPrefix': _CONFIG_DATA.AzureDB.subnet_prefix,
            'OSVersion': _CONFIG_DATA.AzureDB.os_version,
            'companyAuthCode': authcode,
            'identity': {
                "type": "UserAssigned",
                "userAssignedIdentities": user_assigned_identities
            }
        }

        parameters = {k: {'value': v} for k, v in parameters.items()}

        deployment_properties = DeploymentProperties(
            mode=DeploymentMode.incremental,
            template=template,
            parameters=parameters
        )

        self.log.info(f"Initiating deployment {deployment_name}")
        deployment_async_operation = self.client.deployments.begin_create_or_update(
            rg_name,
            deployment_name,
            Deployment(properties=deployment_properties)
        )
        deployment_async_operation.wait()
        self.log.info(f"Provisioned vm {self.vm_name} through the deployment {deployment_name} successfully!")

    def get_deployment_details(self, rg_name, deployment_name=None):
        """
        Method to get the deployment details
        Args:
             rg_name         (str)   --  Name of the resource group
             deployment_name (str)   --  Name of the deployment
        Returns:
            dict        --  Returns Input/outputsdeployment_properties object
        """
        if deployment_name is None:
            deployment_name = self.deployment_name
        deployment_properties = self.client.deployments.get(rg_name, deployment_name).properties
        return deployment_properties

    def get_backup_gateway_name(self, rg_name, deployment_name=None):
        """
        Method to get the vm name from the outputs after the custom deployment
        Args:
            rg_name         (str)   --  Name of the resource group

            deployment_name (str)   --  Name of the deployment

        Returns:
            vm_name         (str)   --  Returns name of the vm created by deployment
        """
        deployment_prop = self.get_deployment_details(rg_name, deployment_name)
        backup_gateway_name = deployment_prop.outputs.get('metallicGatewayClientName', '').get('value', '')
        self.log.info(f"Backup Gateway name {backup_gateway_name} fetched from deplyment outputs")
        return backup_gateway_name


class AzureVMOperations(AzureHelper):
    """ class to perform Azure SDK common operations w.r.t Azure VMs """

    def __init__(self):
        """ Initializes instance of AzureVMOperations class """
        super().__init__()
        self.compute_client = None

        if self.subscription_id is not None:
            self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            self.log.info("Compute Management Client Object creation successful.")

    def power_on_machine(self, rg_name, machine_name):
        """
        Power on existing virtual machine
        Args:
            rg_name     (str)   --  Name of the resource group

            machine_name   (str)  --  Name of the VM
        """
        self.log.info(f"Starting up Azure VM {machine_name}.")
        if self.compute_client.virtual_machines.instance_view(rg_name, machine_name).statuses[
            1].display_status == "VM running":
            self.log.info(f"Azure VM {machine_name} is already running.")
        else:
            self.compute_client.virtual_machines.begin_start(rg_name, machine_name)
            self.log.info(f"Started Azure VM {machine_name}, sleeping for 1 minute.")
            time.sleep(60)
    
    def power_off_machine(self, rg_name, machine_name):
        """
        Powers off existing virtual machine
        Args:
            rg_name     (str)   --  Name of the resource group

            machine_name   (str)  --  Name of the VM
        """

        self.log.info(f"Turning off Azure VM {machine_name}.")
        if self.compute_client.virtual_machines.instance_view(rg_name, machine_name).statuses[
            1].display_status.lower() in ("vm stopped", "vm deallocated"):
            self.log.info(f"Azure VM {machine_name} is already stopped.")
        else:
            power_off = self.compute_client.virtual_machines.begin_power_off(rg_name, machine_name)
            power_off.wait()
            self.log.info(f"Stopped Azure VM {machine_name}.")


class AzureAuthToken(AzureHelper):
    """ Class to generate Azure Auth tokens using Azure SDK """

    def __init__(self):
        super().__init__()

    def generate_auth_token_iam_ad_auth(self):
        """
           Method to generate auth token for IAM AD App
           Returns:
               auth_token          (str)   --  Returns auth token for the IAM AD App
        """
        authority = "https://login.microsoftonline.com/" + _CONFIG_DATA.Azure.Tenant
        scope = ["https://ossrdbms-aad.database.windows.net/.default"]
        self.credential = ConfidentialClientApplication(
            client_id=_CONFIG_DATA.Azure.App.ApplicationID,
            authority=authority,
            client_credential=_CONFIG_DATA.Azure.App.ApplicationSecret
        )
        result = self.credential.acquire_token_for_client(scopes=scope)
        access_token = result["access_token"]
        return access_token

    def generate_auth_token_mi_ad_auth(self, backupgateway, commcell):
        """
            Method to generate Auth token for Azure Managed Identity based authentication
                Args:
                            backupgateway   (str)       : backupgateway name
                            commcell        (object)    : object of commcell
                Returns:
                            access_token    (str)       : Authentication Token

        """
        destination_object = commcell.clients.get(backupgateway)
        destination_machine_object = Machine(destination_object)
        token_url = ("http://169.254.169.254/metadata/identity/oauth2/"
                     "token?api-version=2018-02-01&resource=https%3A%2F%2Fossrdbms-aad.database.windows.net&"
                     "client_id=0b7099a1-83be-4992-8b8e-967b5e8fb571")
        os = destination_machine_object.os_info
        if os == 'UNIX':
            headers = f'"{"Metadata"}' + ": " + f'{"true"}"'
            command_2 = "curl -H" + f' {headers}' + f' "{token_url}"'
        else:
            headers = "@{ " + f'"{"Metadata"}"' + " = " + f'"{"true"}"' + " }"
            command_2 = "Invoke-RestMethod -Uri " + f'"{token_url}"' + f" -Headers {headers} -Method Get"
        output = destination_machine_object.execute_command(command_2)
        cmd_output = output.output[17:] if os == 'UNIX' else output.output[21:]
        token = cmd_output.split("client_id")[0].strip()
        access_token = token.replace(" ", "").replace("\t", "").replace("\r", "").replace("\n", "")
        if os == 'UNIX':
            access_token = access_token[:-3]
        return access_token
