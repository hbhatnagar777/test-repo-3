# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Azure
    AzureHelper:

        get_access_token()		                - Get access token for any first authorization

        check_for_access_token_expiration()     - this function check if access_token is
                                                  expired if yes it will generate one

        copy_test_data_to_each_volume           - copy testdata to each volume in the vm

        update_hosts                            - Update the VM data Information

        collect_all_vm_data                     - Collect all VM Data

        collect_all_resource_group_data         - Collect All RG Info

        get_all_resource_group                  - get resource group info

        get_resourcegroup_name                  - gets the resource group of that VM

        get_resourcegroup_for_region            - get the Resource group for that particular
                                                  region

        compute_free_resources                  - compute all free resources required

         get_storage_access_token               - Gets storage access token

         check_for_storage_access_token_expiration - Checks if storage  access token has expired

         check_vms_exist                            -  Checks VMs exists in the Hypervisor

         get_resource_group_resources               -   Gets the list of resources in resource group

"""
import copy
import datetime
import re
import time
import socket
import requests
import xmltodict
from msal import ConfidentialClientApplication
import json
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VirtualServerUtils import get_details_from_config_file, validate_ipv4, decode_password
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from VirtualServer.VSAUtils.VirtualServerConstants import AZURE_RESOURCE_MANAGER_URL, AZURE_API_VERSION


class AzureHelper(Hypervisor):
    """
        Main class for performing all operations on AzureRM Hypervisor
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
        Initialize AzureRM Helper class properties


            Args:
                server_host_name    (str):      server list at instance level

                host_machine        (str):      Co-ordinator at instance level

                user_name           (str):      App_ID of AzureRM subscription

                password            (tupple):   consist of password, subscriptionID,
                                                tenantID

                instance_type       (str):      Instance type of the AzureRM

                commcell            (object):   Commcell object

        """

        super(AzureHelper, self).__init__(server_host_name,
                                          user_name,
                                          password,
                                          instance_type,
                                          commcell,
                                          host_machine)

        self.disk_extension = [".vhd"]
        self.authentication_endpoint = 'https://login.microsoftonline.com/'
        self.azure_resourceURL = 'https://management.core.windows.net/'
        self.azure_baseURL = 'https://management.azure.com'
        self.azure_apiversion = "api-version="
        self.disk_uri_template = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/disks/{}"
        self.blob_uri_template = "https://{}.blob.core.windows.net/{}/{}"
        self._all_vmdata = {}
        self._all_vmstatus = {}
        self._all_rgdata = {}
        self._subnet_id = ''
        self.msal_app = None
        self._storage_access_token = None
        self._access_token = None
        self._default_headers = None
        self.xmsdate = None
        self.subscription_id = password[1]
        self.app_id = user_name
        self.tenant_id = password[2]
        self.app_password = password[0]
        self.azure_session = requests.Session()
        if instance_type == hypervisor_type.AZURE_V2.value.lower():
            self.collect_all_resource_group_data()
            self.collect_all_vm_data()

    @property
    def subnet_id(self):
        """
        returns the subnet id
        """
        return self._subnet_id

    @subnet_id.setter
    def subnet_id(self, network):
        """
        sets subnet_id as per network_rg and network_name, sent as a tuple (network_rg,network_name)
        """
        try:
            network_rg, network_name = network
        except ValueError:
            raise ValueError("Pass an iterable with (network_rg,network_name)")
        else:
            self._subnet_id = "/subscriptions/" + self.subscription_id + "/resourceGroups/" + \
                              network_rg + "/providers/Microsoft.Network/virtualNetworks/" + \
                              network_name.split("\\")[0] + \
                              "/subnets/" + network_name.split("\\")[1]

    @property
    def default_headers(self):
        """
        provide the default headers required

        """
        self._default_headers = {"Content-Type": "application/json",
                                 "Authorization": "Bearer %s" % self.access_token}
        return self._default_headers

    @property
    def all_vmdata(self):
        """
        provide info about all VM's
        """
        if not bool(self._all_vmdata):
            self.collect_all_vm_data()

        return self._all_vmdata

    @all_vmdata.setter
    def all_vmdata(self, value):
        """
        sets the VM related info
        """
        key, value = value
        self._all_vmdata[key] = value

    @property
    def all_vmstatus(self):
        """
        collects all vms status

        """
        if not bool(self._all_vmstatus):
            self.collect_all_vm_status()

        return self._all_vmstatus

    @all_vmstatus.setter
    def all_vmstatus(self, value):
        """
        sets all vms status

        """
        self._all_vmstatus = value

    @property
    def all_rgdata(self):
        """
        collects all resource group data

        """
        if self._all_rgdata is None:
            self.collect_all_resource_group_data()

        return self._all_rgdata

    @all_rgdata.setter
    def all_rgdata(self, value):
        """
        sets the resource group data

        """
        self._all_rgdata = value

    @staticmethod
    def parse_disk_storage_account(disk_uri):
        """
        Returns the storage account of the disk
        """
        if 'blob.core.windows.net' not in disk_uri:
            return ''
        return re.match(r'.*[:][/][/](?P<storage_account>[^.]*)[.].*', disk_uri).group('storage_account')

    def get_token_for_scopes(self, scopes):
        """
        Get a token for the given scopes.
        Looks for token in cache and sends request only when cache misses.
        Automatically refreshes tokens when they expire.

        Args:
            scopes      (list of str): List of scopes

        Returns:
            token response for the given scopes

        Raises:
            Exception:
                When token cannot be acquired
        """
        if self.app_password == "":
            keys = get_details_from_config_file('azure')
            self.tenant_id, self.app_id, self.app_password = keys.split(":")

        if self.msal_app is None:
            self.msal_app = ConfidentialClientApplication(
                client_id=self.app_id,
                client_credential=self.app_password,
                authority=self.authentication_endpoint + self.tenant_id
            )

        token_response = self.msal_app.acquire_token_for_client(scopes=scopes)
        return token_response

    @property
    def storage_access_token(self):
        """
        Get storage access token.
        """
        token_response = self.get_token_for_scopes(scopes=["https://storage.azure.com/.default"])

        if "access_token" in token_response:
            self._storage_access_token = token_response["access_token"]
            if token_response["token_source"] == "identity_provider":
                self.log.info(f"Acquired new storage access token: {self._storage_access_token}")
            return self._storage_access_token
        else:
            self.log.error("Unable to get storage access token")
            raise Exception(token_response["error"])

    @property
    def access_token(self):
        """
        Get access token.
        """
        token_response = self.get_token_for_scopes(scopes=[self.azure_resourceURL + '.default'])

        if "access_token" in token_response:
            self._access_token = token_response["access_token"]
            if token_response["token_source"] == "identity_provider":
                self.log.info(f"Acquired new access token: {self._access_token}")
            return self._access_token
        else:
            self.log.error("Unable to get access token")
            raise Exception(token_response["error"])

    def update_hosts(self):
        """
        Update the VM data Information

        Raises:
            Exception:
                Failed to fetch information from cloud portal
        """
        try:
            self.collect_all_vm_data()
            self.collect_all_resource_group_data()

        except Exception as err:
            self.log.exception("An exception occurred in updating Host")
            raise err

    def collect_all_vm_data(self):
        """
        Collect all VM Data from each resource group

         Raises:
            Exception:
                Failed to get VM information present in Resource group
        """
        try:
            _allrg = self.get_all_resource_group()
            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                api_date = "?api-version=2016-04-30-preview"
            else:
                api_date = "?api-version=2015-06-15"
            for each_rg in _allrg:
                azure_list_vm_url = "/subscriptions/" + self.subscription_id + "/resourceGroups/" \
                                    + each_rg + "/providers/Microsoft.Compute/virtualMachines"

                _all_data, _ = self.execute_api("GET", azure_list_vm_url, self.default_headers,
                                                api_version=api_date, fail_on_error=False,
                                                suppress_logging=True)
                self.all_vmdata = (each_rg, _all_data)

        except Exception as err:
            self.log.exception("An exception occurred in collect_all_vmdata")
            raise err

    def collect_all_vm_status(self):
        """
        Collect all VM Status from a subscription

         Raises:
            Exception:
                Failed to get VM status data
        """
        try:
            api_date = "?api-version=2024-07-01"
            azure_list_vm_url = "/subscriptions/" + self.subscription_id + "/providers/Microsoft.Compute/virtualMachines"

            _all_status_data, _ = self.execute_api("GET", azure_list_vm_url, self.default_headers,
                                            api_version=api_date, fail_on_error=False,
                                            suppress_logging=True, query_params='&statusOnly=true')
            self._all_vmstatus = _all_status_data

        except Exception as err:
            self.log.exception("An exception occurred in collect_all_vm_status")
            raise err


    def collect_all_resource_group_data(self):
        """
        Collect All Resource group data

        Raises:
            Exception:
                Failed to get information about resource group
        """
        try:
            if self.instance_type == hypervisor_type.AZURE_V2.value.lower():
                api_date = "2014-04-01"
            else:
                api_date = "2018-02-01"

            azure_resource_group_url = self.azure_baseURL + "/subscriptions/" \
                                       + self.subscription_id + "/resourceGroups?" \
                                       + self.azure_apiversion + api_date
            data = self.azure_session.get(azure_resource_group_url, headers=self.default_headers, verify=False)
            self.all_rgdata = data.json()

        except Exception as err:
            self.log.exception("An exception occurred in CollectAllResourceGroupData")
            raise err

    def get_all_resource_group(self):
        """
        Prepare list of resource groups and their corressponding resources

        Returns:
            resource_group     (str):  list of all resource groups

        Raises:
            Exception:
                Failed to sagregate resources groups and its data
        """

        try:
            _allrg_list = []
            datadict = self.all_rgdata
            for eachkey in datadict["value"]:
                rg_name = eachkey["name"]
                _allrg_list.append(rg_name)

            return _allrg_list

        except Exception as err:
            self.log.exception("An exception occurred in collect_all_resource_group_data")
            raise err

    def get_all_vms_in_hypervisor(self, **kwargs):
        """
        This function fetches information about all VMs in particular resource group

        Returns:
            _all_vmlist     (list):  list of all VM's

        Raises:
            Exception:
                Failed to get VM information
        """
        try:
            _all_vmlist = []
            datadict = self.all_vmdata
            filtered_datadict = copy.deepcopy(datadict)
            rgs_to_remove = []

            if "pattern" in kwargs:
                pattern = kwargs["pattern"].split("\n")
                pattern_type = pattern[1].split(":")[1]
                pattern_value = pattern[0].split(":")[1]
                regex = re.compile(pattern_value)

                for rg, vm_list in filtered_datadict.items():

                    if pattern_type == "location":
                        vm_list["value"] = [vm for vm in vm_list["value"] if vm.get("location", "NULL") == pattern_value]

                    elif pattern_type == "tag_name":
                        vm_list["value"] = [vm for vm in vm_list["value"]
                                            if any(regex.fullmatch(tag_name) for tag_name in vm.get("tags", {}).keys())]

                    elif pattern_type == "tag_value":
                        vm_list["value"] = [vm for vm in vm_list["value"]
                                            if any(regex.fullmatch(tag_value) for tag_value in vm.get("tags", {}).values())]

                    elif pattern_type == "resource_group":
                        if not regex.fullmatch(rg):
                            rgs_to_remove.append(rg)

                    elif pattern_type == "vmpowerstate":
                        pattern_value = pattern_value == "1"
                        datadict = self.all_vmstatus
                        filtered_datadict = copy.deepcopy(datadict)

                        for each_vm in filtered_datadict["value"]:
                            status_code = each_vm["properties"]["instanceView"]["statuses"][1]["code"]
                            if (pattern_value and status_code == "PowerState/running") or (not pattern_value and status_code != "PowerState/running"):
                                vm_name = each_vm["name"]
                                _all_vmlist.append(vm_name)

                        return _all_vmlist

                if rgs_to_remove:
                    for rg in rgs_to_remove:
                        del filtered_datadict[rg]

            for eachdata, eachvalue in filtered_datadict.items():
                vm_info_value = eachvalue.get("value", [])
                if vm_info_value != []:
                    for eachkey in vm_info_value:
                        vm_name = eachkey["name"]
                        _all_vmlist.append(vm_name)

            return _all_vmlist

        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def check_vms_exist(self, vm_list):
        """

        Check each VM in vm_list exists in Hypervisor VMs Dict

        Args:
            vm_list (list): List of VMs to check

        Returns:
            True (bool): If All VMs are present

            False (bool): If any VM is absent

        """
        if isinstance(vm_list, str):
            vm_list = [vm_list]
        present_vms = self.get_all_vms_in_hypervisor()
        present_vms = set(present_vms)
        if (set(vm_list) & set(present_vms)) == set(vm_list):
            return True
        else:
            return False

    def get_resourcegroup_name(self, vm_name):
        """
        Get resource group of particular VM

        Args:
            vm_name                 (str):  vm whose information needs to be fetched

        Returns:
            resource_group_name     (str):  Resource group where VM is found

        Raises:
            Exception:
                if it fails to find particular resource group for VM
        """
        try:

            resource_group_name = None

            self.collect_all_vm_data()
            datadict = self.all_vmdata
            for eachdata, each_value in datadict.items():
                if "value" in each_value:
                    vm_info_value = each_value["value"]
                    if vm_info_value != []:
                        for each_key in vm_info_value:
                            _vm_name = each_key["name"]
                            if _vm_name == vm_name:
                                vm_id = each_key["id"]
                                temp_str = vm_id.split("/")
                                resource_group_name = temp_str[temp_str.index("resourceGroups") + 1]
                                break

                else:
                    self.log.info("Cannot collect information for this VM")
            return resource_group_name

        except Exception as err:
            self.log.exception("An exception occurred in getting the Resource group")
            raise err

    def get_resourcegroup_for_region(self, region):
        """
        Get all resource groups of particular Region

        Args:
            region             (str):  region whose resource groups needs to be fetched

        Returns:
            resource_group     (str):  list of all resource groups

        Raises:
            Exception:
                if it fails to find resource groups of particular region
        """
        try:
            resource_group = []
            rg_data = self.all_rgdata
            for eachrg in rg_data["value"]:
                rg_region = eachrg["location"]
                if rg_region == region:
                    resource_group.append(eachrg["name"])

            return resource_group

        except Exception as err:
            self.log.exception("An exception occurred in get_resourcegroup_for_region")
            raise err

    def compute_free_resources(self, vm_name, resource_group=None):
        """

        Compute the free Resource of the subscription based on region

        Args:
            vm_name             (str):  list of Vms to be restored

        Returns:
            resource_group	    (str):  The resource group where restore can be performed

            storage_account     (str):  Storage account where restore has to be performed

        Raises:
            Exception:
                Not able to get resource group or storage account or all

        """
        try:
            sa_name = None
            if resource_group is None:
                datadict = self.all_vmdata
                for eachdata, eachvalue in datadict.items():
                    vm_info_value = eachvalue["value"]
                    if vm_info_value != []:
                        for eachkey in vm_info_value:
                            _vm_name = eachkey["name"]
                            if _vm_name == vm_name[0]:
                                region = eachkey["location"]
                                break

                resource_group = self.get_resourcegroup_for_region(region)

            for each_rg in resource_group:
                storage_account_url = self.azure_baseURL + "/subscriptions/" + \
                                      self.subscription_id + "/resourceGroups/" + \
                                      each_rg + "/providers/Microsoft.Storage/storageAccounts?" \
                                      + self.azure_apiversion + "2017-06-01"
                data = self.azure_session.get(storage_account_url, headers=self.default_headers, verify=False)
                if data.status_code == 200:
                    storage_account_data = data.json()
                    sa_value = storage_account_data["value"]
                    if sa_value != []:
                        for each_sa in storage_account_data["value"]:
                            sa_name = each_sa["name"]
                            resource_group = each_rg
                            break
                    else:
                        self.log.info("Failed to get SA details for this Resource Group")
                else:
                    self.log.info("Failed to get SA details for this Resource Group: %s" % each_rg)
            location = self.get_storage_account_location(sa_name)
            return resource_group, sa_name, location

        except Exception as err:
            self.log.exception("An exception occurred in ComputeFreeResources")
            raise err

    def get_storage_account_location(self, sa_name):
        """
        Returns the location of the storage account

        Args:
            sa_name             (str):  Storage Account name for which location has to be identified

        Returns:
            location            (str):  Returns the location of the storage account

        Raises:
            Exception:
                Not able to get location of storage account

        """
        try:
            return list(filter(lambda x: x['name'] == sa_name, self.get_all_storage_accounts()))[0]['location']
        except:
            self.log.info("Failed to get location details for this Storage Account")

    def get_all_storage_accounts(self):
        """
        Returns all storage accounts associated to subscription
        """
        url = (self.azure_baseURL + f'/subscriptions/{self.subscription_id}'
                                    f'/providers/Microsoft.Storage/storageAccounts?'
               + self.azure_apiversion + "2017-06-01")
        response = self.azure_session.get(url, headers=self.default_headers, verify=False)
        if not response.ok:
            return []
        data = response.json().get('value', [])
        return data

    def get_storage_sas(self, storage_account_name,
                        permission='list', resource_type='container',
                        service_type='blob', expiry_minutes=60):
        """Returns the SAS (str) for the storage account
            Args:
                storage_account_name (str)  : Storage account name to get permission for
                permission (str)            : Permission to be granted.
                            One of read, write, delete, list, add, create, update, process
                resource_type (str)         : Type of resource to get permission for
                            One of service, container, object
                service_type (str)          : Type of service to access from
                            One of blob, queue, table, file
                expiry_minutes (int)        : Number of minutes after which SAS becomes invalid

        """
        storage_accounts = self.get_all_storage_accounts()
        for storage_account in storage_accounts:
            if storage_account.get('name') == storage_account_name:
                storage_account_id = storage_account.get('id')
                break
        else:
            return ''

        url = self.azure_baseURL + storage_account_id + f'/ListAccountSas?{self.azure_apiversion}2017-06-01'
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=expiry_minutes)
        params = {
            'signedExpiry': expiry_time.isoformat() + 'Z',
            'signedPermission': permission.lower()[0],
            'signedResourceTypes': resource_type.lower()[0],
            'signedServices': service_type.lower()[0],
        }
        response = self.azure_session.post(url, json=params, headers=self.default_headers, verify=False)
        if not response.ok or 'accountSasToken' not in response.json():
            return ''
        return response.json().get('accountSasToken', '')

    def get_containers_in_storage_account(self, storage_account_name):
        """
        Returns a list of all containers in storage account

        Args:
            storage_account_name (str) :  Name of storage account
        """
        sas_container_check = self.get_storage_sas(storage_account_name,
                                                   resource_type='service',
                                                   expiry_minutes=5)
        marker = ''
        containers = []
        for _ in range(15):
            container_check_url = (f'https://{storage_account_name}.blob.core.windows.net'
                                   f'/?comp=list&{sas_container_check}')
            if marker:
                container_check_url += f'&marker={marker}'
                marker = ''
            containers_resp = self.azure_session.get(container_check_url, verify=False)
            if containers_resp.ok:
                response_dict = xmltodict.parse(containers_resp.text)
                containers_list = response_dict.get('EnumerationResults', {}).get('Containers', {}).get('Container')
                containers += containers_list if isinstance(containers_list, list) else [containers_list]
                marker = response_dict.get('EnumerationResults', {}).get('NextMarker', '')
            if not marker:
                break
        return containers

    def get_vhds_in_storage_account(self, storage_account_name):
        """
        Returns a list of VHD names in storage account

        Args:
            storage_account_name (str) :  Name of the storage account
        """
        containers = self.get_containers_in_storage_account(storage_account_name)
        vhds_container = [container.get('Name') for container in containers if container.get('Name') == 'vhds']
        if not vhds_container:
            return []
        sas = self.get_storage_sas(storage_account_name, expiry_minutes=5)
        marker = ''
        vhds = []
        for _ in range(15):
            url = f'https://{storage_account_name}.blob.core.windows.net/vhds?restype=container&comp=list&{sas}'
            if marker:
                url += f'&marker={marker}'
                marker = ''
            response = self.azure_session.get(url, verify=False)
            if response.ok:
                response_dict = xmltodict.parse(response.text)
                blobs_list = response_dict.get('EnumerationResults', {}).get('Blobs', {}).get('Blob', [])
                vhds += blobs_list if isinstance(blobs_list, list) else [blobs_list]
                marker = response_dict.get('EnumerationResults', {}).get('NextMarker', '')
            if not marker:
                break
        return vhds

    def check_disk_exists_in_resource_group(self, disk_uri):
        """
        Checks if the disk exists in the resource group
        Args:
            disk_uri (str): The URI of the disk that is to be checked
        Returns:
            True, if the disk exists, False otherwise
        """
        if not disk_uri.startswith(self.azure_baseURL):
            disk_uri = self.azure_baseURL + disk_uri

        response = self.azure_session.get(disk_uri + f'?{self.azure_apiversion}2019-03-01',
                                          headers=self.default_headers)
        return response.ok

    def check_blob_exists_in_storage_account(self, blob_uri):
        """
        Checks if the blob exists on the storage account
        Args:
            blob_uri (str): The URI of the blob that is to be checked

        Returns:
            True, if the blob and storage account exist, False otherwise
        """
        storage_account = self.parse_disk_storage_account(blob_uri)
        # If storage account is invalid, return False
        if not storage_account:
            return False

        sas_token = self.get_storage_sas(storage_account, permission='read',
                                         service_type='blob', resource_type='object', expiry_minutes=1)
        response = self.azure_session.head(blob_uri + '?' + sas_token)
        return response.ok

    def get_storage_account(self, resource_group):
        """
        Returns the storage account name

        Args:
            resource_group (str) :  Resource group for which storage accound has to be looked for
        """
        sa_value = ''
        storage_account_url = self.azure_baseURL + "/subscriptions/" + \
                              self.subscription_id + "/resourceGroups/" + \
                              resource_group + "/providers/Microsoft.Storage/storageAccounts?" \
                              + self.azure_apiversion + "2017-06-01"
        data = self.azure_session.get(storage_account_url, headers=self.default_headers, verify=False)
        if data.status_code == 200:
            storage_account_data = data.json()
            sa_value = storage_account_data["value"]
        return sa_value

    def get_all_available_vm_sizes(self, region=None):
        """Returns a list of all available sizes
        Args:
            region (str): The region of the VM
        Returns:
            sizes (dict): A mapping of VM size to hardware profile
        """
        size_data = {}
        size_url = (f'{self.azure_baseURL}/subscriptions/{self.subscription_id}/providers/Microsoft.Compute'
                    f'/skus?{self.azure_apiversion}2019-04-01')
        if region:
            size_url += f"&$filter=location eq '{region}'"
        data = self.azure_session.get(size_url, headers=self.default_headers, verify=False)
        if data.status_code == 200 and 'value' in data.json():
            for sku_dict in data.json()['value']:
                if sku_dict.get('resourceType') != 'virtualMachines':
                    continue
                name = sku_dict.get('name')
                sku_location = sku_dict.get('locations')[0].lower()
                sku_data = {
                    'capabilities': {v['name']: v['value'] for v in sku_dict['capabilities']},
                    'zones': sku_dict.get('locationInfo', [{}])[0].get('zones', []),
                    'tier': sku_dict.get('tier')
                }
                size_data[(name, sku_location)] = sku_data
        return size_data

    def get_all_vnets_in_resource_group(self, resource_group):
        """Returns a list of all Vnets that are in a resource group
        Args:
            resource_group (str): The name of the resource group
        Returns:
            A list of the following dictionary structure:
                {
                  "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/virtualNetworks/vnet1",
                  "name": "vnet1",
                  "type": "Microsoft.Network/virtualNetworks",
                  "location": "westus",
                  "properties": {
                    "addressSpace": {
                      "addressPrefixes": [
                        "10.0.0.0/8"
                      ]
                    },
                    "dhcpOptions": {
                      "dnsServers": []
                    },
                    "subnets": [
                      {
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/test-1",
                        "name": "test-1",
                        "properties": {
                          "addressPrefix": "10.0.0.0/24",
                          "provisioningState": "Succeeded"
                        }
                      }
                    ],
                    "virtualNetworkPeerings": [],
                    "provisioningState": "Succeeded"
                  }
                },
                {
                  "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/virtualNetworks/vnet2",
                  "name": "vnet2",
                  "type": "Microsoft.Network/virtualNetworks",
                  "location": "westus",
                  "properties": {
                    "addressSpace": {
                      "addressPrefixes": [
                        "10.0.0.0/16"
                      ]
                    },
                    "dhcpOptions": {
                      "dnsServers": [
                        "8.8.8.8"
                      ]
                    },
                    "subnets": [],
                    "virtualNetworkPeerings": [],
                    "provisioningState": "Succeeded"
                  }
                }
        """
        vnets_url = (f'{self.azure_baseURL}/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}'
                     f'/providers/Microsoft.Network/virtualNetworks?{self.azure_apiversion}2019-04-01')
        data = self.azure_session.get(vnets_url, headers=self.default_headers, verify=False)
        if data.json() and 'value' in data.json():
            return data.json()['value']
        return []

    def get_all_nsgs_in_resource_group(self, resource_group):
        """Returns a list of all NSGs that are in a resource group
        Args:
            resource_group (str): The name of the resource group
        Returns:
            A list of the following dictionary structure:
                {
                  "name": "nsg1",
                  "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1",
                  "type": "Microsoft.Network/networkSecurityGroups",
                  "location": "westus",
                  "properties": {
                    "provisioningState": "Succeeded",
                    "securityRules": [],
                    "defaultSecurityRules": [
                      {
                        "name": "AllowVnetInBound",
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1/defaultSecurityRules/AllowVnetInBound",
                        "properties": {
                          "provisioningState": "Succeeded",
                          "description": "Allow inbound traffic from all VMs in VNET",
                          "protocol": "*",
                          "sourcePortRange": "*",
                          "destinationPortRange": "*",
                          "sourceAddressPrefix": "VirtualNetwork",
                          "destinationAddressPrefix": "VirtualNetwork",
                          "access": "Allow",
                          "priority": 65000,
                          "direction": "Inbound"
                        }
                      },
                      {
                        "name": "AllowAzureLoadBalancerInBound",
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1/defaultSecurityRules/AllowAzureLoadBalancerInBound",
                        "properties": {
                          "provisioningState": "Succeeded",
                          "description": "Allow inbound traffic from azure load balancer",
                          "protocol": "*",
                          "sourcePortRange": "*",
                          "destinationPortRange": "*",
                          "sourceAddressPrefix": "AzureLoadBalancer",
                          "destinationAddressPrefix": "*",
                          "access": "Allow",
                          "priority": 65001,
                          "direction": "Inbound"
                        }
                      },
                      {
                        "name": "DenyAllInBound",
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1/defaultSecurityRules/DenyAllInBound",
                        "properties": {
                          "provisioningState": "Succeeded",
                          "description": "Deny all inbound traffic",
                          "protocol": "*",
                          "sourcePortRange": "*",
                          "destinationPortRange": "*",
                          "sourceAddressPrefix": "*",
                          "destinationAddressPrefix": "*",
                          "access": "Deny",
                          "priority": 65500,
                          "direction": "Inbound"
                        }
                      },
                      {
                        "name": "AllowVnetOutBound",
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1/defaultSecurityRules/AllowVnetOutBound",
                        "properties": {
                          "provisioningState": "Succeeded",
                          "description": "Allow outbound traffic from all VMs to all VMs in VNET",
                          "protocol": "*",
                          "sourcePortRange": "*",
                          "destinationPortRange": "*",
                          "sourceAddressPrefix": "VirtualNetwork",
                          "destinationAddressPrefix": "VirtualNetwork",
                          "access": "Allow",
                          "priority": 65000,
                          "direction": "Outbound"
                        }
                      },
                      {
                        "name": "AllowInternetOutBound",
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1/defaultSecurityRules/AllowInternetOutBound",
                        "properties": {
                          "provisioningState": "Succeeded",
                          "description": "Allow outbound traffic from all VMs to Internet",
                          "protocol": "*",
                          "sourcePortRange": "*",
                          "destinationPortRange": "*",
                          "sourceAddressPrefix": "*",
                          "destinationAddressPrefix": "Internet",
                          "access": "Allow",
                          "priority": 65001,
                          "direction": "Outbound"
                        }
                      },
                      {
                        "name": "DenyAllOutBound",
                        "id": "/subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/networkSecurityGroups/nsg1/defaultSecurityRules/DenyAllOutBound",
                        "properties": {
                          "provisioningState": "Succeeded",
                          "description": "Deny all outbound traffic",
                          "protocol": "*",
                          "sourcePortRange": "*",
                          "destinationPortRange": "*",
                          "sourceAddressPrefix": "*",
                          "destinationAddressPrefix": "*",
                          "access": "Deny",
                          "priority": 65500,
                          "direction": "Outbound"
                        }
                      }
                    ]
                  }
                }
        """
        nsgs_url = (f'{self.azure_baseURL}/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}'
                    f'/providers/Microsoft.Network/networkSecurityGroups?{self.azure_apiversion}2019-04-01')
        data = self.azure_session.get(nsgs_url, headers=self.default_headers, verify=False)
        if data.json() and 'value' in data.json():
            return data.json()['value']
        return []

    def get_managed_resource_info_by_id(self, resource_id, api_version='2021-04-01'):
        """
        Gets api resource info by using id
        Args:
            resource_id(str) : id of the resource info to be retrived
                                ex: '/subscriptions/{sub id}/resourceGroups/{resource group}'
            api_version(str) : azure api version to be used

        returns:
            data(dict),status(bool),status code(int): on success returns data,True, status code
                                                    else None, False, status code
        """
        azure_resource_url = f'{self.azure_baseURL}{resource_id}?' + \
                             f'{self.azure_apiversion}{api_version}'
        data = self.azure_session.get(azure_resource_url,
                                      headers=self.default_headers, verify=False)
        if data.status_code == 200:
            return data.json(), True, data.status_code
        return None, False, data.status_code

    def get_proxy_location(self, proxy_ip):
        """
        Gets the region of the vm which has the ip specified

        Args :
            proxy_ip(str): ip / host name of the proxy

        Returns:
            status, region :  True, region of the vm if vm is found
                              else False, None

        """
        try:
            if not validate_ipv4(proxy_ip):
                proxy_ip = socket.gethostbyname_ex(proxy_ip)[2][0]
            vm_id = self.get_vm_id_from_ip(proxy_ip)
            if vm_id:
                details = self.get_managed_resource_info_by_id(vm_id)
                if details[1]:
                    return True, details[0]['location']
            return False, None
        except Exception as err:
            raise Exception("Exception in proxy/VM location restored VM location:{0}".format(err))

    def get_vm_id_from_ip(self, ip):
        """

        Gets the vm id of the vm which has the ip address specified

        Args:
            ip (str) :  ip address for which vm id needs to be fetched
        Returns :
            vm id (str) : id of the vm

        """
        try:
            azure_network_details_uri = f'/subscriptions/{self.subscription_id}/providers/' \
                                        'Microsoft.Network/networkInterfaces'
            details = self.get_managed_resource_info_by_id(azure_network_details_uri)
            if details[1]:
                for each_network in details[0]['value']:
                    for each_ipconfig in each_network.get('properties').\
                            get('ipConfigurations'):
                        if each_ipconfig.get('properties').get('privateIPAddress') == ip and each_network.get(
                                'properties').get('virtualMachine'):
                            return each_network.get('properties').get('virtualMachine')['id']

            azure_public_ip_uri = f'/subscriptions/{self.subscription_id}/providers/' \
                                  'Microsoft.Network/publicIPAddresses'
            details = self.get_managed_resource_info_by_id(azure_public_ip_uri)
            if details[1]:
                for each_public_ip in details[0]['value']:
                    if each_public_ip["properties"].get("ipAddress") and \
                            each_public_ip["properties"].get("ipAddress") == ip:
                        network_interface_id = each_public_ip["properties"]. \
                            get("ipConfiguration")["id"].rsplit('/', 2)[0]

                        network_details = self.get_managed_resource_info_by_id(network_interface_id)
                        if network_details[1]:
                            if network_details[0].get('properties').get('virtualMachine'):
                                return network_details[0].get('properties').get('virtualMachine')['id']
        except Exception as err:
            raise Exception("error occurred while try to find vm from ip address : {0}".format(err))

    def get_network_interfaces_in_resource_group(self, resource_group_name, api_version="2021-05-01"):
        """
        Lists all the network interfaces in resource group
        Args:
            resource_group_name     (str):  Name of resource group to list NICs in
        Returns:
            A list of all network interfaces in the format:
            https://docs.microsoft.com/en-us/rest/api/virtualnetwork/network-interfaces/list#networkinterface
        """
        try:
            azure_network_list_url = (f"{self.azure_baseURL}/subscriptions/{self.subscription_id}/resourceGroups/"
                                      f"{resource_group_name}/providers/Microsoft.Network/"
                                      f"networkInterfaces?{self.azure_apiversion}{api_version}")
            response = self.azure_session.get(azure_network_list_url, headers=self.default_headers, verify=False)
            if response.ok:
                if response.json():
                    return response.json().get("value", [])
                return []
            else:
                raise Exception(response.text)
        except Exception as err:
            raise Exception(f"Error occurred while trying to find NICs in resource group {resource_group_name}: {err}")

    def get_vmname_by_ip(self, ip):
        """
        Get VM name from its IP

        Args:
            ip      (str)    : ip address of the machine

        Returns:
            instance of the machine
        """
        try:
            id = self.get_vm_id_from_ip(ip)
            return id.split('/')[-1]
        except Exception as err:
            raise Exception("error occurred while try to find vm name from ip address : {0}".format(err))

    def execute_api(self, method, api_endpoint, headers, payload=None, wait_sec=300, retry_count=10,
                    api_version=AZURE_API_VERSION, fail_on_error=True, **kwargs):
        """
        Method to execute azure api requests
        Args:
            method          (str): method to called
            api_endpoint    (str): api end point for request
            headers         (dict): header for the request
            payload         (json): payload for the request
            wait_sec        (int): wait time for retires
            retry_count     (int): number of retries
            api_version     (str): api version to be used
            fail_on_error   (bool): raise err on exception
        """
        API_METHOD = {
            "GET": self.azure_session.get,
            "POST": self.azure_session.post,
            "PUT": self.azure_session.put,
            "DELETE": self.azure_session.delete
        }

        payload = json.dumps(payload) if payload else payload

        azure_url = AZURE_RESOURCE_MANAGER_URL + api_endpoint + api_version + kwargs.get("query_params", "")

        for attempt in range(retry_count):
            try:
                if not kwargs.get("suppress_logging", False):
                    self.log.info("Executing Azure API: [{}] {}".format(method.upper(), azure_url))
                response = API_METHOD[method.upper()](azure_url, headers=headers, verify=False, json=payload)

                if response.status_code in [200, 201, 202]:
                    try:
                        return [response.json(), response.status_code]
                    except ValueError:
                        return [{}, response.status_code]
                    break

                elif response.status_code in [404, 204]:
                    self.log.error("Requested resource not found or deleted for API: {}".format(api_endpoint))
                    try:
                        return [response.json(), response.status_code]
                    except ValueError:
                        return [{}, response.status_code]
                    break

                elif response.status_code == 429:
                    self.log.error("Attempt {} for requested API throttled, retrying again after {} min".format(
                        attempt, api_endpoint, wait_sec / 60))
                    time.sleep(wait_sec)
                    continue

                else:
                    if fail_on_error:
                        raise Exception(
                            "API response doesn't indicate Success, received status code: {} with body: {}".format(
                                response.status_code, response.json()
                            ))

                    else:
                        return [response.json(), response.status_code]

                    break

            except Exception as err:
                raise Exception(
                    f"Calling API endpoint {api_endpoint} failed with error {err}")

    def create_nic(self, nic_props, nic_location):
        """
        Creates an Azure NIC in provided Subnet
        Args:
            nic_props     (dict): dict containing nic props
            nic_location  (str): location

        Returns :
            NIC Obj (dict) : rsponse object returned from Azure on creation of NIC
        """
        nic_req_payload = {
            "properties": {
                "disableTcpStateTracking": False,
                "ipConfigurations": [
                    {
                        "name": nic_props["nic_name"],
                        "properties": {
                            "subnet": {
                                "id": nic_props["subnet_id"]
                            }
                        }
                    }
                ]
            },
            "location": nic_location
        }

        azure_nic_api = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/networkInterfaces/{}".format(
            self.subscription_id, nic_props["resourceGroup"], nic_props["nic_name"]
        )

        self.log.info("Creating NIC with name: {}.".format(nic_props["nic_name"]))
        response, _ = self.execute_api("PUT", azure_nic_api, self.default_headers, payload=nic_req_payload)

        retry_count = 0
        while retry_count < 5:
            if response["properties"]["provisioningState"] == "Succeeded":
                self.log.info("Azure NIC: {} created successfully.".format(response["name"]))
                return response

            else:
                retry_count += 1
                if retry_count >= 5:
                    raise Exception("Retry count exceeded waiting for NIC to be created")
                self.log.info("Nic is still being created, waiting for 2 min.")
                time.sleep(120)
                response, _ = self.execute_api("GET", azure_nic_api, self.default_headers)

    def create_vm_from_image(self, vm_props):
        """
        Creates VM from image in Azure
        Args:
            vms_props           (dict):  dict containing vm props

        Returns :
            VM Name (str) : Name of the VM created
        """
        vm_creds = get_details_from_config_file(vm_props["vm_os"].lower()).split(',')[0].split(':')
        vm_creds[1] = decode_password(vm_creds[1])

        vm_req_payload = {
            "location": vm_props["location"],
            "tags": vm_props["tags"],
            "properties": {
                "hardwareProfile": {
                    "vmSize": vm_props.get("vmSize", "Standard_B2s")
                },
                "storageProfile": {
                    "imageReference": {
                        "id": vm_props["image_id"]
                    },
                    "osDisk": {
                        "caching": "ReadWrite",
                        "managedDisk": {
                            "storageAccountType": "Standard_LRS"
                        },
                        "name": vm_props["vm_name"] + "_OSdisk",
                        "createOption": "FromImage"
                    }
                },
                "osProfile": {
                    "adminUsername": vm_creds[0],
                    "computerName": vm_props["vm_name"][:15],
                    "adminPassword": vm_creds[1]
                },
                "networkProfile": {
                    "networkInterfaces": [
                        {
                            "id": self.create_nic(vm_props["nic_props"], vm_props["location"])["id"],
                            "properties": {
                                "primary": True
                            }
                        }
                    ]
                }
            }
        }

        azure_vm_api = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachines/{}".format(
            self.subscription_id, vm_props["resourceGroup"], vm_props["vm_name"]
        )

        self.log.info("Creating VM with name: {}.".format(vm_props["vm_name"]))
        response, _ = self.execute_api("PUT", azure_vm_api, self.default_headers, payload=vm_req_payload,
                                       api_version="?api-version=2022-11-01")

        while True:
            if response["properties"]["provisioningState"] == "Creating":
                self.log.info("Request to create VM: {} submitted.".format(vm_props["vm_name"]))
                time.sleep(60)

            elif response["properties"]["provisioningState"] == "Succeeded":
                self.log.info("VM: {} created successfully.".format(vm_props["vm_name"]))
                break

            response, _ = self.execute_api("GET", azure_vm_api, self.default_headers,
                                           api_version="?api-version=2022-11-01")

        return response["name"]

    def create_image_from_vm(self, image_props):
        """
        Creates VM from image in Azure
        Args:
            image_props           (dict):  dict containing image properties

        Returns :
            Image Name (str) : Name of the image created
        """
        img_req_payload = {
            "location": image_props["location"],
            "tags": image_props["tags"],
            "properties": {
                "sourceVirtualMachine": {
                    "id": image_props.get("vm_id")
                }
            }
        }

        azure_img_api = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/images/{}".format(
            self.subscription_id, image_props["resourceGroup"], image_props["image_name"]
        )

        self.log.info("Creating managed image with name: {}.".format(image_props["image_name"]))
        response, _ = self.execute_api("PUT", azure_img_api, self.default_headers, payload=img_req_payload,
                                       api_version="?api-version=2023-07-01")

        while True:
            if response["properties"]["provisioningState"] == "Creating":
                self.log.info("Request to create image: {} submitted.".format(image_props["image_name"]))
                time.sleep(60)

            elif response["properties"]["provisioningState"] == "Succeeded":
                self.log.info("Image: {} created successfully.".format(image_props["image_name"]))
                break

            response, _ = self.execute_api("GET", azure_img_api, self.default_headers,
                                           api_version="?api-version=2023-07-01")

        return response["name"]

    def copy_managed_disk(self, resource_group, source_disk_id, disk_name, region):
        """Creates a copy of a managed disk
           Args:
               resource_group   (str): Resource group to which the disk needs to be copied
               source_disk_id   (str): source disk id
               disk_name        (str): name of the new disk to be created
               region           (str): region where new disk needs to be created
           Returns:
               name,id          (str): name and id of the disk created

        """
        request_url = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}" \
                      f"/providers/Microsoft.Compute/disks/{disk_name}"
        request_body = {
            "location": f"{region}",
            "properties": {
                "creationData": {
                    "createOption": "Copy",
                    "sourceResourceId": f"{source_disk_id}"
                }
            }
        }
        response = self.execute_api("PUT", request_url, self.default_headers, request_body)
        return response[0].get('name'), response[0].get('id')

    def get_resource_group_resources(self, resource_group_name, api_version='2021-04-01'):
        """
              Gets the list of resources in resource group
              Args:
                  resource_group_name     (str):  Name of resource group
              Returns:
                  A list of all resources in the resource group:

        """

        try:
            azure_resource_group_url = (f"{self.azure_baseURL}/subscriptions/{self.subscription_id}/resourceGroups/"
                                        f"{resource_group_name}/resources?{self.azure_apiversion}{api_version}")
            response = self.azure_session.get(azure_resource_group_url, headers=self.default_headers, verify=False)
            if response.ok:
                if response.json():
                    return response.json().get("value", [])
                return []
            else:
                raise Exception(response.text)

        except Exception as err:

            raise Exception(
                f"Error occurred while trying to get all resources in resource group {resource_group_name}: {err}")

    def delete_disk(self, disk_name, resource_group=None, storage_account=None, path=None):
        """
        Deletes a managed or an unmanaged disk (blob).
        If resource_group is None, then the disk will be considered as an unmanaged disk, else managed disk.

        Args:
            disk_name          (str): Name of the disk
            resource_group     (str): Name of the resource group
            storage_account    (str): Name of the storage account
            path               (str): Path in the storage account where the unmanaged disk is present

        Raises:
            Exception:
                When disk cannot be deleted.
        """
        # If the disk is a managed disk
        if resource_group:
            disk_url = AZURE_RESOURCE_MANAGER_URL + self.disk_uri_template.format(self.subscription_id,
                                                                                  resource_group,
                                                                                  disk_name) + "?api-version=2017-03-30"

            response = self.azure_session.delete(disk_url, headers=self.default_headers, verify=False)

            if response.status_code == 202:
                self.log.info('Managed Disk %s found and deleting' % disk_name)

            elif response.status_code == 404:
                self.log.info('Managed Disk %s not found' % disk_name)

            elif response.status_code == 204:
                self.log.info('Managed Disk %s not found' % disk_name)

            else:
                self.log.error('Azure response [{0}] Status code [{1}]'.format(
                    response.text, response.status_code))
                raise Exception("Managed Disk %s cannot be deleted" % disk_name)
        else:
            # Get SAS (shared access signature) token for deleting the blob
            sas_token = self.get_storage_sas(storage_account, permission='delete',
                                             service_type='blob', resource_type='object', expiry_minutes=1)

            if sas_token != "":
                blob_url = self.blob_uri_template.format(storage_account, path, disk_name)
                response = self.azure_session.delete(blob_url + "?" + sas_token)

                if response.status_code == 202:
                    self.log.info('Unmanaged Disk %s found and deleting' % disk_name)
                elif response.status_code == 404:
                    self.log.info('Unmanaged Disk %s not found' % disk_name)
                elif response.status_code == 204:
                    self.log.info('Unmanaged Disk %s not found' % disk_name)
                else:
                    self.log.error('Azure response [{0}] Status code [{1}]'.format(
                        response.text, response.status_code))
                    raise Exception("Unmanaged Disk %s cannot be deleted" % disk_name)
            else:
                raise Exception("Error in getting SAS token")

    def get_first_virtual_network_id_in_region(self, region):
        """
           Retrieve the ID of the first virtual network in the specified Azure region.

           Args:
               region (str): Azure region name.

           Returns:
               str or None: ID of the first subnet found in the virtual network that matches the region,
                            or None if no virtual network is found in the specified region.

           Raises:
               Exception: If there is an issue with the Azure API request or response.

        """
        azure_list_vnet_url = "/subscriptions/" + self.subscription_id + \
                              "/providers/Microsoft.Network/virtualNetworks"
        _all_vnet_data, _ = self.execute_api("GET", azure_list_vnet_url, self.default_headers,
                                             api_version=AZURE_API_VERSION, fail_on_error=False,
                                             suppress_logging=True)

        if _all_vnet_data:
            for each_vnet in _all_vnet_data['value']:
                if each_vnet.get("location", "") == region:
                    subnet_id = each_vnet["properties"]["subnets"][0]['id']
                    return subnet_id

        return None
