# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Google Cloud """

import json
import requests
import time
from base64 import urlsafe_b64encode
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils import VMHelper
from VirtualServer.VSAUtils.VirtualServerUtils import get_details_from_config_file
from AutomationUtils import logger


class GoogleCloudHelper(Hypervisor):
    """
    Main class for performing all operations on Google Hyperviosr

    Methods:
            get_all_vms_in_hypervisor     - gets a list of all the vms in the hypervisor

            compute_free_resources        - returns the closest bucket to the proxy for restore

            _get_all_buckets              - finds alll the buckets associated with the hypervisor

            get_proxy_zone                - returns the zone of a proxy

            _find_proxy                   - finds the region and zone of a proxy

            _make_request                 - makes http rest api requests to google servers

            _get_access_token             - retrieves an authetnication access token

            refresh_token                 - refreshes access token

    """

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):

        super(GoogleCloudHelper, self).__init__(server_host_name,
                                                user_name,
                                                password,
                                                instance_type,
                                                commcell,
                                                host_machine)

        # TODO: figure out way to integrate service account JSON/p12 from user
        self.service_account = get_details_from_config_file('gcp', 'service_account')
        with open(self.service_account, 'r') as f:
            self.credentials_dict = json.load(f)
        self.access_token = self._get_access_token()
        self._headers = {
            'Authorization': 'Bearer ' + self.access_token
        }
        self.google_session = requests.Session()
        self._base_compute_uri = 'https://www.googleapis.com/compute/v1/projects/'
        self._base_storage_uri = 'https://www.googleapis.com/storage/v1/b'
        self.google_projects_url = "https://cloudresourcemanager.googleapis.com/v1/projects"
        self._iam_google_url = "https://iam.googleapis.com/v1/projects/"
        self.vm_details = []
        self.project = ''
        self.project_list = []
        self.vm_id_dict = self._fetch_all_vms()[1]
        self.log = logger.get_log()
        self.restore_project = kwargs.get("project_id", '')
        self.replica_zone = kwargs.get("replica_zone", '')
        self.vm_custom_metadata = kwargs.get("vm_custom_metadata", '')
        self.vm_service_account = kwargs.get("service_account")
        self.public_reserved_ip = kwargs.get("public_ip_address", "")
        self.private_reserved_ip = kwargs.get("private_ip_address", "")
    @property
    def Projects(self):
        """ Returns list of all projects."""
        try:
            if not self.project_list:
                data = self._execute_google_api(self.google_projects_url)
                for project in data['projects']:
                    self.project_list.append(project['projectId'])
            return self.project_list

        except Exception as err:
            self.log.exception("Exception in _fetch_all_projects: {0}".format(str(err)))
            raise Exception(err)

    @property
    def VMs(self):
        """Returns List of VMs. It is read onlyt attribute"""
        return self._VMs

    @VMs.setter
    def VMs(self, vm_list):
        """Creates VMObject for list of VM passed
        Args:
            vmList    (list) - list of VMs for creating VM object
        """

        try:
            if isinstance(vm_list, list):
                for each_vm in vm_list:
                    if each_vm.isdigit():
                        each_vm = self._get_vm_name_by_id(each_vm)
                    self._VMs[each_vm] = VMHelper.HypervisorVM(self, each_vm)

            else:
                if vm_list.isdigit():
                    vm_list = self._get_vm_name_by_id(vm_list)
                self._VMs[vm_list] = VMHelper.HypervisorVM(self, vm_list)
                self.log.info("VMs are %s" % self._VMs)

        except Exception as err:
            self.log.exception(
                "An exception occurred in creating object %s" % err)
            raise Exception(err)

    def _get_access_token(self):
        """
        Retrieves access token for authorization

        Returns:
            access_token    (str)       -   token that authorizes requests to Google server

        """

        now_in_seconds = int(time.time())
        expiry_in_seconds = now_in_seconds + (3540)

        header = {'typ': 'JWT', 'alg': 'RS256'}

        claim_set = {
            "iss": self.credentials_dict['client_email'],
            "scope": "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/"
                     "auth/compute",
            "aud": "https://www.googleapis.com/oauth2/v4/token",
            "exp": expiry_in_seconds,
            "iat": now_in_seconds
        }

        json_claim_set = json.dumps(
            claim_set,
            separators=(',', ':'),
        ).encode('utf-8')

        json_header = json.dumps(
            header,
            separators=(',', ':'),
        ).encode('utf-8')

        segments = [urlsafe_b64encode(json_header), urlsafe_b64encode(json_claim_set)]
        private_key = self.credentials_dict['private_key']
        key = backend.load_pem_private_key(private_key.encode('utf-8'), password=None, unsafe_skip_rsa_key_validation=False)
        signing_input = b'.'.join(segments)
        signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        segments.append(urlsafe_b64encode(signature))
        JWT = b'.'.join(segments)
        grant_type = 'urn:ietf:params:oauth:grant-type:jwt-bearer'

        response = requests.post('https://www.googleapis.com/oauth2/v4/token',
                                 data={'grant_type': grant_type,
                                       'assertion': JWT})
        access_token = response.json()['access_token']

        return access_token

    def refresh_token(self):
        """
        Updates access token value in case of expiration

        """

        self.access_token = self._get_access_token()

        self._headers = {
            'Authorization': 'Bearer ' + self.access_token
        }

    def _execute_google_api(self, api_url, method='get'):
        """
        Executes the google api url
        Args:
            api_url (str):   The api url to be exceuted

        Returns:
            The response of the api call

        Raise:
            Exception:
                If the response status is not 200
        """
        try:
            attempts = 0
            while attempts < 3:
                if method == 'get':
                    response = self.google_session.get(api_url, headers=self._headers)
                elif method == 'post':
                    response = self.google_session.post(api_url, headers=self._headers)
                elif method == 'delete':
                    response = self.google_session.delete(api_url, headers=self._headers)
                if response.status_code == 401:
                    attempts = attempts + 1
                    self.refresh_token()
                if response.status_code == 200:
                    return response.json()
                attempts += 1
            if attempts == 3 and response.status_code == 401:
                raise Exception("Cannot establish the connection ")
            else:
                raise Exception(
                    "Api did not return the correct response : Status Code {0}".format(str(response.status_code)))
        except Exception as err:
            self.log.exception("Exception in executing google cloud api : {0}".format(str(err)))
            raise Exception(err)

    def _get_vm_name_by_id(self, vm_id):
        """
        Returns the vm name corrresponding to the given id

        Args:
            vm_id (str) : VM Id for which vm name has to be looked for
            project (bastring) : Name of the project

        Returns:
            VM name corresponding to given id

        Raises:
            Exception:
                When VM is not found
        """
        try:
            for project in self.Projects:
                for instance_list in self.vm_id_dict[project]:
                    if vm_id in instance_list:
                        self.project = project
                        self.vm_details.append(instance_list)
                        self.log.info("Instance list is : {0}".format(str(instance_list)))
                        return instance_list[0]
        except Exception as err:
            self.log.exception("Exception in _get_vm_name_by_id: {0}".format(str(err)))
            raise Exception(err)

    def _get_vm_location(self, vm_name, project=None):
        """
        Returns the vm location corresponding to the given vm name

        Args:
            vm_name (str) : Vm name for which location has to be looked for

        Returns:
            VM location corresponding to given vm name

        Raises:
            Exception:
                When VM is not found
        """
        try:
            vm_location = []
            for instance_list in self.vm_details:
                if vm_name in instance_list:
                    vm_location.append(instance_list[3])
                    vm_location.append(instance_list[2])
                    return vm_location
            if project:
                for instance_list in self.vm_id_dict[project]:
                    if vm_name in instance_list:
                        vm_location.append(instance_list[3])
                        vm_location.append(instance_list[2])
                        return vm_location
            else:
                for prj in self.Projects:
                    for instance_list in self.vm_id_dict[prj]:
                        if vm_name in instance_list:
                            self.project = prj
                            vm_location.append(instance_list[3])
                            vm_location.append(instance_list[2])
                            return vm_location
        except Exception as err:
            self.log.exception("Exception in _get_vm_location: {0}".format(str(err)))
            raise Exception(err)

    def get_proxy_location(self, ip):
        """
        Returns the proxy location corresponding to the given proxy ip

        Args:
            ip  : proxy ip for which location has to be looked for

        Returns:
            Proxy location corresponding to given proxy IP

        Raises:
            Exception:
                When Proxy is not found
        """
        try:
            vm_location = []
            for prj in self.Projects:
                for instance_list in self.vm_id_dict[prj]:
                    if ip in instance_list:
                        self.project = prj
                        vm_location.append(instance_list[3])
                        vm_location.append(instance_list[2])
                        return vm_location
        except Exception as err:
            self.log.exception("Exception in get_proxy_location: {0}".format(str(err)))
            raise Exception(err)


    def _fetch_all_vms(self):
        """
        Returns vm list and vm id dictionary for all vms in all projects

        Raises:
             Exception:
                When Api returns error
        """
        try:
            vm_list = []
            vm_name_id_dict = {}
            for project in self.Projects:
                vm_name_id_dict.update({project: []})
                google_url = self._base_compute_uri + "{0}/regions/".format(project)
                response = self._execute_google_api(google_url)
                region_list = response['items']
                for region in region_list:
                    for zone in region['zones']:
                        zone_name = zone.rpartition('/')[2]
                        google_url = self._base_compute_uri + "{0}/zones/{1}/instances".format(
                            project, zone_name)
                        response = self._execute_google_api(google_url)
                        if 'items' in response:
                            vm_data = response['items']
                            for instance in vm_data:
                                vm_list.append(instance['name'])
                                vm_custom_metadata = []
                                if instance.get('metadata'):
                                    if instance['metadata'].get('items'):
                                        for metadata in instance['metadata']['items']:
                                            if 'automation' in metadata['key']:
                                                vm_custom_metadata.append(metadata)
                                if instance.get("serviceAccounts"):
                                    sa_email = instance["serviceAccounts"][0].get("email")
                                    google_sa_url = self._iam_google_url + "{0}/serviceAccounts/{1}".format(
                                        project, sa_email)
                                    sa_info = self._execute_google_api(google_sa_url)

                                else:
                                    sa_info = {}
                                vm_name_id_dict[project].append(
                                    [instance['name'], instance['id'], zone_name, region['name'],
                                     instance['networkInterfaces'][0]["networkIP"], vm_custom_metadata,
                                     sa_info]
                                    )
            return [sorted(vm_list), vm_name_id_dict]
        except Exception as err:
            self.log.exception("An exception occurred getting VMs from Google Cloud: {0}".format(str(err)))
            raise Exception(err)

    def get_all_vms_in_hypervisor(self):
        """
        Gets all the vms in the hypervisor

        Returns:
            vm_list     (list)      -     A list of all the names of the vms in the hypervisor

        Raises:
            Exception:
                If the list of vms cannot be found

        """

        return self._fetch_all_vms()[0]

    def compute_free_resources(self, vm):
        """
        Finds nearest bucket to proxy for restore

        Args:
            vm    (str)   -   google cloud  vm

        Returns:
            bucket_id   (str)   -   The name of the bucket closest to the proxy_vm

        Raises:
            Exception:
                if a bucket cannot be found for the proxy

        """

        try:
            vm_region = self._get_vm_location(vm)[0]

            for bucket in self._get_all_buckets():
                if bucket['location'] == vm_region.upper():
                    return bucket['id']
            for bucket in self._get_all_buckets():
                if bucket['location'] == vm_region.partition('-')[0].upper():
                    return bucket['id']
            return self._get_all_buckets()[0]['id']

        except Exception as err:
            self.log.exception("An exception occurred finding a bucket from Google Cloud: {0}".format(str(err)))
            raise Exception(err)

    def update_hosts(self):
        """
        Update the VM data Information

        Raises:
            Exception:
                Failed to fetch information from cloud portal
        """
        self.vm_id_dict = self._fetch_all_vms()[1]

    def _get_all_buckets(self):
        """
        Finds all the buckets associated with the hypervisor

        Returns:
            bucket_list     (list)      -      A list of all the bucket objects

        """

        try:
            flag, response = self._make_request(
                'GET', self._base_storage_uri + '?project=' + self.project)

            if flag:
                bucket_list = response.json()['items']
                return bucket_list

        except Exception as err:
            self.log.exception("An exception occurred getting buckets from Google Cloud: {0}".format(str(err)))
            raise Exception(err)

    def get_vm_zone(self, vm, project=None):
        """
        Finds the zone in which a proxy is stored

        Args:
            vm    (str)   -   the proxy that is trying to be found

        Returns:
            zone        (str)   -   the name of the zone where the proxy is stored
        """
        return self._get_vm_location(vm, project)[1]

    def _get_custom_metadata(self, vm_name, project):
        """
                Finds list of all custom Metadata associated with a VM

                Args:
                    vm_name    (str)   -   the proxy that is trying to be found
                    project (str)   -   the project of the vm

                Returns:
                    custom Metadata     (list)      -      A list of all custom Metadata dictionaries

                """
        try:
            for instance_list in self.vm_details:
                if vm_name in instance_list:
                    return instance_list[5]
            if project:
                for instance_list in self.vm_id_dict[project]:
                    if vm_name in instance_list:
                        return instance_list[5]
            else:
                for prj in self.Projects:
                    for instance_list in self.vm_id_dict[prj]:
                        if vm_name in instance_list:
                            return instance_list[5]
        except Exception as err:
            self.log.exception("Exception in _get_custom_metadata: {0}".format(str(err)))
            raise Exception(err)

    def get_vm_custom_metadata(self, vm, project=None):
        """
        Finds the custom Metadata for the vm in a project

        Args:
            vm    (str)   -   the proxy that is trying to be found
            project (str)  -   the project of the VM

        Returns:
            Custom Metadata     (str)   -   a List of Custom Metadata
        """
        return self._get_custom_metadata(vm, project)

    def _get_service_account(self, vm_name, project):
        """
        Finds list of all custom Metadata associated with a VM

        Args:
            vm_name    (str)   -   the proxy that is trying to be found
            project (str)   -   the project of the vm

        Returns:
            custom Metadata     (list)      -      A list of all custom Metadata dictionaries

        """
        try:
            for instance_list in self.vm_details:
                if vm_name in instance_list:
                    return instance_list[6]
            if project:
                for instance_list in self.vm_id_dict[project]:
                    if vm_name in instance_list:
                        return instance_list[6]
            else:
                for prj in self.Projects:
                    for instance_list in self.vm_id_dict[prj]:
                        if vm_name in instance_list:
                            return instance_list[6]
        except Exception as err:
            self.log.exception("Exception in _get_service_account: {0}".format(str(err)))
            raise Exception(err)

    def get_vm_service_account(self, vm, project=None):
        """
        Finds the Service account of VM

        Args:
            vm    (str)   -   instance machine
            project (str) - Project Name
        Returns:
            Service Account        (str)   -   a list of dictionary
        """
        return self._get_service_account(vm, project)

    def _get_specified_service_account(self, project, email):
        """
        Returns all the info about Default or specified Service Account

        Args:
            project (str)   -   the project of the vm
            email   (str)   -   email of the service account

        Returns:
            service Account     (dic)      -      dictionary of service account info

        """
        if email:
            google_sa_url = self._iam_google_url + "{0}/serviceAccounts/{1}".format(
                project, email)
            sa_info = self._execute_google_api(google_sa_url)
            return sa_info

        else:
            google_sa_url = self._iam_google_url + project+"/serviceAccounts"
            sa_list = self._execute_google_api(google_sa_url)
            accounts = sa_list.get("accounts")
            for sa in accounts:
                if sa.get("displayName") in ["Compute Engine default service account"]:
                    return sa
            return ""

    def get_specified_service_account(self, project, email=None):
        """
        Finds the Default Service Account in a specific Project
        Args:
            project    (str)   -   instance machine
            email      (str)   -   service account email

        Returns:
            Service Account        (str)   -   a list of dictionary
        """
        return self._get_specified_service_account(project, email)

    def _get_all_snapshots(self):
        """
        Fetches all snapshot from all projects

        Returns:
            Snapshots   (list) : List containing names of all snapshots
        """
        snapshot_names = []
        for project_name in self.Projects:
            try:
                response_dict = self._execute_google_api(
                    self._base_compute_uri + f'{project_name}/global/snapshots')
                if 'items' in response_dict:
                    snapshot_details = response_dict['items']
                    for snapshot_detail in snapshot_details:
                        snapshot_names.append(snapshot_detail['name'])

            except Exception as err:
                self.log.exception(f"An exception occurred while fetching "
                                   f"snapshots of project: {project_name}")
                self.log.info(f"Exception: {err}")
                raise Exception(err)
        return snapshot_names

    def _get_disks_by_project(self, project_name):
        """
        Fetch disks by project_name

        Args:
            project_name    (str):  Name of project to fetch disks from

        Raises:
            Exception   :   If disks cannot be fetched
        """
        disk_names = []
        try:
            response_dict = self._execute_google_api(
                self._base_compute_uri + f'{project_name}/aggregated/disks')
            if 'items' in response_dict:
                for region in response_dict['items']:
                    if 'disks' in response_dict['items'][region]:
                        disks_details = response_dict['items'][region]['disks']
                        for disk_detail in disks_details:
                            disk_names.append(disk_detail['name'])
            return disk_names
        except Exception as err:
            self.log.exception(f"An exception occurred while fetching "
                               f"disks of project: {project_name}")
            self.log.info(f"Exception: {err}")
            raise Exception(err)

    def _get_all_disks(self):
        """
        Fetches all disks from all projects

        Returns:
            Disks   (list) : List containing names of all disks
        """
        disk_names = []
        for project_name in self.Projects:
            disk_names.extend(self._get_disks_by_project(project_name))
        return disk_names

    def check_snapshot_pruning(self, snapshot_prefix):
        """
        Check if snapshot containing snapshot_prefix is pruned

        Args:
            snapshot_prefix  (str):  prefix containing job_id and type of job
             to check snapshots for

        Returns:
            True    (bool): Snapshot containing snapshot_prefix is pruned
            False   (bool): Snapshot containing snapshot_prefix is not pruned
        """
        snapshot_names = self._get_all_snapshots()
        for snapshot_name in snapshot_names:
            if snapshot_prefix in snapshot_name:
                return False
        return True

    def check_disk_pruning(self, disk_prefix, project_name=None):
        """
        Check if disk containing disk_prefix is pruned

        Args:
            disk_prefix  (str)/(list):  prefix containing job_id
             and type of job to check for

            project_name (str): project in which the disks are to be searched,
            if not set - disk is searched in all projects

        Returns:
            True    (bool): Disk containing disk_prefix is pruned
            False   (bool): Disk containing disk_prefix is not pruned
        """
        if not isinstance(disk_prefix, list):
            disk_prefix = [disk_prefix]

        if project_name:
            disk_names = self._get_disks_by_project(project_name)
        else:
            disk_names = self._get_all_disks()

        for disk_name in disk_names:
            for pref in disk_prefix:
                if pref in disk_name:
                    return False
        return True

    def get_project_by_instance_name(self, instance_name):
        """
        Get project name of the given instance name

        Args:
            instance_name   (str):  Name of instance,
             for which the project name is to be found

        Returns:
            project_name    (str): Name of project
        """
        for project_name in self.Projects:
            for instance_list in self.vm_id_dict[project_name]:
                if instance_name in instance_list:
                    return project_name
        return False

    def check_disk_pruning_by_description(self, project_name, job_id):
        """
        Check if any disk in the project contains job_id in its description

        Args:
            project_name    (str):      Name of project to fetch disks from
            job_id          (str/int):  Job ID to check in the description

        Returns:
            True    :   If disk pruning was successful
            False   :   If disk pruning failed

        """
        try:
            response_dict = self._execute_google_api(
                self._base_compute_uri + f'{project_name}/aggregated/disks')
            if 'items' in response_dict:
                for region in response_dict['items']:
                    if 'disks' in response_dict['items'][region]:
                        disks_details = response_dict['items'][region]['disks']
                        for disk_detail in disks_details:
                            if 'description' in disk_detail:
                                if f'Job {job_id}' in disk_detail['description']:
                                    return False
            return True
        except Exception as err:
            self.log.exception(f"An exception occurred while fetching "
                               f"disk description of project: {project_name}")
            self.log.info(f"Exception: {err}")
            raise Exception(err)
