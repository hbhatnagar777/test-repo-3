# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Azure Stack
    AzureStackHelper:

        compute_free_resources                  - compute all free resources required

"""

import requests
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from .AzureHelper import AzureHelper


class AzureStackHelper(AzureHelper, Hypervisor):
    """
        Main class for performing all operations on AzureStack Hypervisor
    """

    def __init__(self,
                 server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):
        """
        Initialize Azurestack Helper class properties


            Args:
                server_host_name    (str):      server list at instance level

                host_machine        (str):      Co-ordinator at instance level

                user_name           (str):      App_ID of Azurestack subscription

                password            (tupple):   consist of password, subscriptionID,
                                                tenantID

                instance_type       (str):      Instance type of the Azurestack

                commcell            (object):   Commcell object

        """

        super(AzureStackHelper, self).__init__(server_host_name,
                                               user_name,
                                               password,
                                               instance_type,
                                               commcell,
                                               host_machine)

        self.azure_baseURL = 'https://management.local.azurestack.external'
        metadata = requests.get(self.azure_baseURL + "/metadata/endpoints?api-version=2015-01-01", verify=False)
        endpoints = metadata.json()
        self.azure_adauthorityURL = 'https://management.adfs.azurestack.local/d53eb5b4-5817-4301-a98c-88a9a533ce52'
        self.azure_resourceURL = 'https://management.adfs.azurestack.local/d53eb5b4-5817-4301-a98c-88a9a533ce52'
        self.authentication_endpoint = 'https://adfs.local.azurestack.external/adfs/'
        self.azure_resourceURL = endpoints["authentication"]["audiences"][0]
        if self.tenant_id:
            self.get_access_token()
        else:
            self.get_adfs_access_token()
        self.collect_all_resource_group_data()
        self.collect_all_vm_data()

    def get_adfs_access_token(self):
        """
        Get access token for any first authorization

        Raises:

            Exception:
                Failed to get access token while logging into Azure
        """
        try:
            self.log.info("Logging into Azure Stack ADFS to get access token")

            import adal
            from OpenSSL.crypto import load_certificate, FILETYPE_PEM
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            context = adal.AuthenticationContext(self.authentication_endpoint, False)

            with open("C:\certificate.pem", 'rb') as cert_file:
                pem_data = cert_file.read()

            with open("C:\key1.pem", 'rb') as key_file:
                key_data = key_file.read()
                key_data1 = key_data.decode("utf-8")

            cert = load_certificate(FILETYPE_PEM, pem_data)
            sha1 = (cert.digest("sha1")).decode("utf-8")
            token_response = context.acquire_token_with_client_certificate(self.azure_resourceURL, self.app_id,
                                                                           key_data1, sha1)

            self.access_token = access_token = token_response.get('accessToken')
            self.log.info("Access Token is %s" % self.access_token)

        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def compute_free_resources(self, vm_name, resource_group=None):
        """

        Compute the free Resource of the subscription based on region

        Args:
            vm_name             (list):  list of Vms to be restored

            resource_group      (str):  resource group if specified explicitly

        Returns:
            resource_group	    (str):  The resource group where restore can be performed

            storage_account     (str):  Storage account where restore has to be performed

        Raises:
            Exception:
                Not able to get resource group or storage account or all

        """
        try:
            resource_group = self.get_resourcegroup_name(vm_name[0])

            storage_account_url = self.azure_baseURL + "/subscriptions/" + \
                                  self.subscription_id + "/resourceGroups/" + \
                                  resource_group + "/providers/Microsoft.Storage/storageAccounts?" \
                                  + self.azure_apiversion + "2016-01-01"
            self.log.info("Trying to get list of VMs usign post %s" % storage_account_url)
            data = self.azure_session.get(storage_account_url, headers=self.default_headers, verify=False)
            if data.status_code == 200:
                storage_account_data = data.json()
                sa_value = storage_account_data["value"]
                if sa_value != []:
                    for each_sa in storage_account_data["value"]:
                        sa_name = each_sa["name"]
                        break
                else:
                    self.log.info("Failed to get SA details for this Resource Group")
            else:
                self.log.info("Failed to get SA details for this Resource Group")

            return resource_group, sa_name

        except Exception as err:
            self.log.exception("An exception occurred in ComputeFreeResources")
            raise err