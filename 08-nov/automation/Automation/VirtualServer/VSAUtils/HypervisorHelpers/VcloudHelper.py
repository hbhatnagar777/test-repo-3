# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Vcloud """

import requests
import json
import xmltodict
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VirtualServerConstants import VCLOUD_API_HEADER
from AutomationUtils import config


class VcloudHelper(Hypervisor):
    """
    Main class for performing all operations on Vcloud Hypervisor
    """

    def __init__(self, server_host_name, user_name,
                 password, instance_type, auto_commcell, host_machine, **kwargs):
        """
        Initialize VCloud Helper class properties

        Args:
            server_host_name    (str):      Hostname of the Vcloud

            host_machine        (str):      host  machine

            user_name           (str):      Username of the Vcloud

            password            (str):      Password of the Vcloud

            instance_type       (str):      Instance type of the Vcloud

            auto_commcell       (object):   Commcell object
        """
        self.org_client = int(kwargs.get("org_client", 0) or 0) > 0
        super(VcloudHelper, self).__init__(server_host_name, user_name, password,
                                           instance_type, auto_commcell, host_machine)

        if self.org_client:
            self.login_url = "https://" + server_host_name + "/cloudapi/1.0.0"
            vcloud_creds = config.get_config().Virtualization.vcloud.creds
            creds = vcloud_creds.split(':')
            self.username = creds[0] + '@system'
            self.password = creds[1]
        else:
            self.login_url = "https://" + self.server_host_name + "/cloudapi/1.0.0"
            self.username = user_name + '@system'
            self.password = password
        self.url = "https://" + self.server_host_name + "/api"
        self.vapp_list = {}
        self.vapp_name = None
        self._all_vmdata = {}
        self.vm_dict = {}
        self.vapp_dict = {}
        self.vm_list = {}
        self.disk_extension = [".vmdk"]
        self.verify_cert = False
        self.headers = VCLOUD_API_HEADER
        self.vcloud_auth_token = self.vcd_login()
        self.collect_all_vm_data()

    @property
    def default_headers(self):
        """
        provide the default headers required

        """
        self._default_headers = VCLOUD_API_HEADER
        self._default_headers.update({"Authorization": f"Bearer {self.vcloud_auth_token}"})
        return self._default_headers

    @property
    def all_vmdata(self):
        """
        provide info about all VM's
        """
        if self._all_vmdata is None:
            self.collect_all_vm_data()

        return self._all_vmdata

    @all_vmdata.setter
    def all_vmdata(self, value):
        """
        sets the VM related info
        """
        key, value = value
        self._all_vmdata[key] = value

    def vcd_login(self):
        """
        Perform login to vCloud Director, saving the vcloud auth token to header.
        """
        self.log.info("Trying to fet the authorization code for Vcloud.")
        try:

            response = requests.post(self.login_url + "/sessions/provider", headers=self.headers,
                                     auth=(self.username, self.password), verify=self.verify_cert)
            if response.status_code == 200:
                self.log.info("Auth code is: %s" % response.headers.get('X-VMWARE-VCLOUD-ACCESS-TOKEN'))
                self.vcloud_auth_token = response.headers.get('X-VMWARE-VCLOUD-ACCESS-TOKEN')
                return self.vcloud_auth_token
        except Exception as err:
            self.log.exception("An exception occurred in _vcd_login")
            raise err

    def check_for_login_validity(self):
        """
        This function check if login is expired if yes it will generate one

        Raises:

            Exception:
                Failed to get login
        """
        try:
            is_sessionok = False
            count = 0
            while ((not is_sessionok) and (count < 3)):

                data = requests.post(self.login_url + "/sessions/provider", headers=self.headers,
                                     auth=(self.username, self.password), verify=self.verify_cert)
                if data.status_code == 403:

                    self.log.info("The session is unauthorized, trying to get new token")
                    count = count + 1
                    self.vcd_login()

                elif data.status_code == 200:
                    is_sessionok = True
                    self.log.info("The Session is success no need to create new access token")
                    return self.vcloud_auth_token

                else:
                    self.log.info("There was error even after getting new token")
                    count = count + 1

        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def update_hosts(self):
        """
        Update the VM data Information

        Raises:
            Exception:
                Failed to fetch information from cloud portal
        """
        try:
            self.collect_all_vm_data()

        except Exception as err:
            self.log.exception("An exception occurred in updating Host")
            raise err

    def collect_all_vm_data(self):
        """
            Prepare list of VMs in vapp in Vcloud

            Returns:
            vm_list         (str):  list of all vms

            Raises:
            Exception:
            Failed to get the vms from vcloud
        """
        try:
            vapp_list = self.get_all_vapp()

            for vapp in vapp_list:
                self.vapp_name = vapp
                api_url = vapp_list[vapp]
                response = requests.get(api_url, headers=self.default_headers, verify=self.verify_cert)
                xparse = xmltodict.parse(response.content)
                content = json.dumps(xparse)
                json_object = json.loads(content)
                for vm in json_object:
                    if 'Children' in json_object[vm]:
                        self.vm_dict[vapp] = json_object[vm]['Children']['Vm']
                try:
                     if isinstance(self.vm_dict[vapp], dict):
                        self.vm_dict[vapp] = [self.vm_dict[vapp]]
                     for vmname in self.vm_dict[vapp]:
                         name = vmname['@name']
                         href = vmname['@href']
                         self.vm_list.update({name: href})
                except Exception as exp:
                    pass

        except Exception as err:
            self.log.exception("An exception occurred in get_all_vapp_vms")
            raise err

    def get_all_vms_in_hypervisor(self):
        """
        This function fetches information about all VMs in particular resource group

        Returns:
            _all_vmlist     (list):  list of all VM's

        Raises:
            Exception:
                Failed to get VM information
        """
        try:
            datadict = self.all_vmdata
            for each in datadict:
                name = each['@name']
                href = each['@href']
                self.vm_list.update({name: href})

            return self.vm_list
        except Exception as err:
            self.log.exception("An exception occurred in getting the Access token")
            raise err

    def compute_free_resources(self, vm_list, vapp_name=None):
        """

        Compute the free Resource of Vcloud

        Args:
            vm_name             (str):  list of Vms to be restored

        Returns:
            vapp_name	    (str):  The resource group where restore can be performed

            network_name     (str):  Storage account where restore has to be performed

        Raises:
            Exception:
                Not able to get resource group or storage accountvapp_name or network_name or all

        """
        try:
            self.check_for_login_validity()
            if not isinstance(vm_list, list):
                vm_list = list(vm_list)
            if vapp_name is None:
                for each_vapp in self.vm_dict:
                    for each_vm in self.vm_dict[each_vapp]:
                        if each_vm['@name'].lower() == vm_list[0].lower():
                            vapp_name = each_vapp

                datadict = self.get_all_vms_in_hypervisor()
                for eachdata, eachvalue in datadict.items():
                    if eachdata == vm_list[0]:
                        href = eachvalue

                api_url = href
                response = requests.get(api_url, headers=self.default_headers, verify=self.verify_cert)
                xparse = xmltodict.parse(response.content)
                content = json.dumps(xparse)
                json_object = json.loads(content)
                network_name = json_object['Vm']['NetworkConnectionSection']['NetworkConnection']['@network']
            return vapp_name, network_name

        except Exception as err:
            self.log.exception("An exception occurred in ComputeFreeResources")
            raise err

    def get_all_orgs(self):
        """
        Prepare list of organizations in Vcloud

        Returns:
        org_list         (dict):  list of all resource groups

        Raises:
            Exception:
                Failed to get the organizations from vcloud
        """
        try:
            org_list = {}
            self.log.info("Trying to get list of Organizations")
            self.check_for_login_validity()
            response = requests.get(self.url + "/org", headers=self.default_headers, verify=self.verify_cert)
            data = xmltodict.parse(response.content)
            content = json.dumps(data)
            _all_orgdata = json.loads(content)

            for org in _all_orgdata:
                for each in _all_orgdata[org]['Org']:
                    org_name = each['@name']
                    org_list[org_name] = each['@href']
            return org_list
        except Exception as err:
            self.log.exception("An exception occurred in get_orgs")
            raise err

    def get_all_org_vdc(self):

        """
        Prepare list of VDC in Vcloud

        Returns:
        vdc_list        (dict):  list of all resource groups

        Raises:
            Exception:
                Failed to get the organizations from vcloud
        """

        try:
            self.log.info("Trying to get list of VDC")
            org_list = self.get_all_orgs()
            vdc_list = {}
            for org in org_list:
                api_url = org_list[org]

                # Previous method of fetching org vdc has been deprecated from v36, using vdcRollup API instead
                response = requests.get(api_url + '/vdcRollup/', headers=self.default_headers, verify=self.verify_cert)
                xparse = xmltodict.parse(response.content)
                content = json.dumps(xparse)
                json_object = json.loads(content)

                if 'OrgVdcReference' not in json_object['OrgVdcRollup'].keys():
                    continue

                org_vdc_reference = json_object['OrgVdcRollup']['OrgVdcReference']

                if type(org_vdc_reference) is dict:
                    org_vdc_reference = [org_vdc_reference]

                for each_vdc in org_vdc_reference:
                    vdc_name = each_vdc['@name']
                    vdc_list.update({vdc_name: each_vdc['@href']})

            return vdc_list
        except Exception as err:
            self.log.exception("An exception occurred in get_all_org_vdc()")
            raise err

    def get_all_vapp(self):

        """
            Prepare list of vapp in Vcloud

            Returns:
            vapp         (dict):  list of all resource groups

            Raises:
            Exception:
            Failed to get the vapp from vcloud
        """
        try:
            self.log.info("Trying to get list of Vapps in Vcloud")
            vdc_list = self.get_all_org_vdc()
            for vdc in vdc_list:
                api_url = vdc_list[vdc]
                response = requests.get(api_url, headers=self.default_headers, verify=self.verify_cert)
                xparse = xmltodict.parse(response.content)
                content = json.dumps(xparse)
                json_object = json.loads(content)

                for each_vdc in json_object:
                    if json_object[each_vdc]['ResourceEntities'] is None:
                        continue
                    else:
                        self.vapp_dict[each_vdc] = json_object[each_vdc]['ResourceEntities']['ResourceEntity']
                        if isinstance(self.vapp_dict[each_vdc], dict):
                            self.vapp_dict[each_vdc] = [self.vapp_dict[each_vdc]]

                        for each_vapp in self.vapp_dict[each_vdc]:
                            href = each_vapp['@href']
                            if '/vApp/' in href:
                                name = each_vapp['@name']
                                self.vapp_list.update({name: href})
            return self.vapp_list
        except Exception as err:
            self.log.exception("An exception occurred in get_all_vdc_vapp")
            raise err

    def storage_profile_info(self, storage_profile_url):
        """
        Fetches storage profile information from a URL.

        Arguments:
            storage_profile_url     (str)   -       vCloud API href for storage profile

        Returns:
            (dict)                          -       { id, name }

        Raise:
            Exception:
                If unable to fetch storage profile information.
        """
        try:
            response = requests.get(storage_profile_url, headers=self.default_headers, verify=self.verify_cert)

            xparse = xmltodict.parse(response.content)
            content = json.dumps(xparse)
            json_object = json.loads(content)

            return {'id': json_object['VdcStorageProfile']['@id'], 'name': json_object['VdcStorageProfile']['@name']}

        except Exception as exp:
            self.log.info("Could not fetch storage profile info with execption: {}".format(str(exp)))
            raise Exception(exp)
