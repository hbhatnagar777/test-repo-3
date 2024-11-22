# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Fusion Compute """

import hashlib
import requests
import re
import time
from collections import OrderedDict
from operator import itemgetter
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor


class FusionComputeHelper(Hypervisor):
    """
    Main class for performing all operations on Fusion Compute Hypervisor
    """

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):

        super(FusionComputeHelper, self).__init__(server_host_name, user_name, password,
                                                  instance_type, commcell, host_machine)

        self.vm_dict = {}
        self.port = 7443
        self._headers = {
            'Accept': 'application/json;charset=UTF-8',
            'Content-type': 'application/json; charset=UTF-8',
            'Accept-Language': 'en_US',
            'X-Auth-Token': None
        }
        _services = 'https://{}:{}/service'.format(self.server_host_name, self.port)

        self.services = {
            'GET_VERSION': '{}/versions'.format(_services),
            'LOGIN': '{}/session'.format(_services),
            'GET_SITES': '{}/sites'.format(_services)
        }
        self._compute_login()
        _vm_services = 'https://{}:{}{}'.format(self.server_host_name, self.port, self._get_site_url())

        self.vm_services = {
            'GET_VMS': '{}/vms?offset=%s&limit=%s'.format(_vm_services),
            'GET_DATASTORES': '{}/datastores'.format(_vm_services),
            'GET_HOSTS': '{}/hosts'.format(_vm_services),
            'GET_DATASTORES_HOSTS': '{}/datastores?scope='.format(_vm_services),
            'GET_VMS_HOSTS': '{}/vms?scope='.format(_vm_services),

        }

        self.get_all_vms_in_hypervisor()

    def get_version(self):
        """
        Get the Fusion Compute Hypervisor Version Provided

        Returns:
            version    (str)    : version of the Fusion compute Hypervisor

        """

        try:
            flag, response = self.make_request('GET', self.services['GET_VERSION'])
            if flag:
                latest_version = response.json()["versions"][-1]
                self._headers['Accept'] = 'application/json;version={};charset=UTF-8'.format(
                    latest_version["version"]
                )
                self._compute_login()
                return latest_version["version"]
            raise response.json()

        except Exception as err:
            self.log.exception("An exception {} occurred getting version from VRM".format(err))
            raise Exception(err)

    def _compute_login(self):
        """
         Does login to the Fusion compute Hypervisor
        set the token in headers

        """

        try:

            hash_object = hashlib.sha256(self.password.encode('UTF-8'))
            self._headers['X-Auth-User'] = self.user_name
            self._headers['X-Auth-Key'] = hash_object.hexdigest()
            self._headers['X-Auth-AuthType'] = '0'
            self._headers['X-Auth-UserType'] = '0'
            flag, response = self.make_request('POST', self.services['LOGIN'])
            if flag:
                self._headers['X-Auth-Token'] = response.headers['x-auth-token']
                self._headers.pop('X-Auth-User', None)
                self._headers.pop('X-Auth-Key', None)
                self._headers.pop('X-Auth-AuthType', None)
                self._headers.pop('X-Auth-UserType', None)

        except Exception as err:
            self.log.exception("An exception occurred while logging in to the VRM")
            raise Exception(err)

    def make_request(self, method, url, payload=None, attempts=0, verify=False, json=None):
        """Makes the request of the type specified in the argument 'method'

        Args:
            method    (str)         --  http operation to perform, e.g.; GET, POST, PUT, DELETE

            url       (str)         --  the web url or service to run the HTTP request on

            payload   (dict / str)  --  data to be passed along with the request
                                    default: None

            attempts  (int)         --  number of attempts made with the same request
                                    default: 0

            verify      (bool)      --    verify for certificates

            json        (dict)      --      request body

        Returns:
            tuple:
                (True, response) - in case of success

                (False, response) - in case of failure

        Raises:
            Fusion Compute SDK Exception:
                if the method passed is incorrect/not supported

            requests Connection Error   --  requests.exceptions.ConnectionError

        """
        try:
            headers = self._headers

            if method == 'POST':
                response = requests.post(url, headers=headers,
                                         verify=verify, json=json)
            elif method == 'GET':
                response = requests.get(url, headers=headers, verify=verify)
            elif method == 'PUT':
                response = requests.put(url, headers=headers,
                                        verify=verify, json=payload)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, verify=verify)
            else:
                raise Exception('HTTP method {} not supported'.format(method))

            if response.status_code == 401 and headers['X-Auth-Token'] is not None:
                if attempts < 3:
                    time.sleep(1)
                    self._compute_login()
                    return self.make_request(method, url, attempts + 1)
                else:
                    # Raise max attempts exception, if attempts exceeds 3
                    raise Exception('Error', '103')

            elif response.status_code == 200:
                return True, response
            else:
                return False, response

        except requests.exceptions.ConnectionError as con_err:
            raise Exception(con_err)

    def _get_site_url(self):
        """
        Get the site urn for the Fusion VRM

        Returns:
            site_url        (str)  - site url for querying about VMs

        """

        try:
            flag, response = self.make_request('GET', self.services['GET_SITES'])
            if flag:
                site_url = response.json()['sites'][0]['uri']
            return site_url

        except Exception as err:
            self.log.exception(
                "An exception {} occurred getting sites from the VRM".format(err)
            )
            raise Exception(err)

    def update_hosts(self):
        """
        update the Information of Host
        """
        try:
            offset = 0
            limit = 100
            flag, response = self.make_request('GET', self.vm_services['GET_VMS'] % (offset, limit))
            if flag:
                vm_list_response = response.json()['vms']
                for vm in vm_list_response:
                    self.vm_dict[vm['name']] = vm['uri']
                return
            raise Exception(response.json())

        except Exception as err:
            self.log.exception(
                "An exception {} occurred during updating hots".format(err)
            )
            raise Exception(err)

    def get_all_vms_in_hypervisor(self, server="", pattern="", c_type=""):
        """
       Get all the vms for Fusion Compute

       Args:
            server (str)   -  VRM  for which all the VMs has to be fetched

            pattern (str)  - Pattern to fetch the vms

            c_type            (str):  Type of content

       Returns:
           _all_vm_list    (str)   -   List of VMs in the host of the pseudoclient
       """

        try:
            _temp_vm_list = []
            vm_list = []
            offset = 0
            limit = 100
            stop = True

            while stop:
                _vm_service = self.vm_services['GET_VMS'] % (offset, limit)
                flag, response = self.make_request('GET', _vm_service)
                if flag:
                    vm_list_response = response.json()['vms']
                    if vm_list_response:
                        offset = offset + 100
                        for vm in vm_list_response:
                            self.vm_dict[vm['name']] = vm['uri']
                            _temp_vm_list.append(vm['name'])
                    else:
                        stop = False

            for each_vm in _temp_vm_list:
                if each_vm != "":
                    each_vm = each_vm.strip()
                    if re.match("^[A-Za-z0-9_-]*$", each_vm):
                        vm_list.append(each_vm)
                    else:
                        self.log.info(
                            "Unicode VM are not supported for now")

            return vm_list

        except Exception as err:
            self.log.exception("An exception {} occurred getting all VMs from VRM".format(err))
            raise Exception(err)

    def _get_vm_host(self, vm_name):
        """

        Args:
            vm_name (str)   - name of the VM for which we want to find host

        Returns:
            Host of teh VM where it resides
            None: if it is not in Fusion Compute
        """

        host = None
        vm_list = self.get_all_vms_in_hypervisor()
        _host_dict = self._get_host_dict()
        _host_list = list(_host_dict.keys())
        if vm_name in map(str.lower, vm_list):
            for each_host in _host_list:
                _vm_host_url = self.vm_services['GET_VMS_HOSTS'] + _host_dict[each_host]["urn"]
                flag, response = self.make_request('GET', _vm_host_url)
                if flag:
                    vm_host_list_response = response.json()['vms']
                    for vm_host in vm_host_list_response:
                        if vm_name.lower() == vm_host["name"].lower():
                            host = each_host
                            break

        return host

    def _get_datastore_dict(self, host_name=None):
        """
        Get the list of datastore in a Host in VRM

        Args:
            host_name   (str)   - Name of the host for which datastore has to be fetched

        Returns:
                _disk_size_dict	(dict)	- Datastores with name and free spaces

        """
        try:
            _disk_size_dict = {}
            _host_dict = self._get_host_dict()
            if host_name:
                _host_list = [host_name]
            else:
                _host_list = list(_host_dict.keys())

            for each_host in _host_list:
                _datastore_url = self.vm_services['GET_DATASTORES_HOSTS'] + _host_dict[each_host]["urn"]
                flag, response = self.make_request('GET', _datastore_url)
                if flag:
                    disk_list_response = response.json()['datastores']
                    for disk in disk_list_response:
                        _disk_size_dict[disk['name']] = disk['actualFreeSizeGB']

            return _disk_size_dict

        except Exception as err:
            self.log.exception(
                "An exception {} occurred getting datastores from VRM".format(err)
            )
            raise Exception(err)

    def _get_host_dict(self):
        """
        Get the list of hosts  in VRM

        Return:
                _host_dict	(dict)	- host with name and free memory

        """
        try:
            _host_dict = {}
            flag, response = self.make_request('GET', self.vm_services['GET_HOSTS'])
            if flag:
                _host_dict_response = response.json()['hosts']
                for host in _host_dict_response:
                    _host_dict[host['name']] = {}
                    _host_dict[host['name']]['Memory'] = (host['memQuantityMB']) / 1024
                    _host_dict[host['name']]['urn'] = host['urn']

            return _host_dict

        except Exception as err:
            self.log.exception(
                "An exception {} occurred getting hosts  from VRM".format(err)
            )
            raise Exception(err)

    def _get_datastore_priority_list(self, host_name=None):
        """
        Returns the descending sorted datastore Dict according to free space

        Args:
            host_name   (str)   - Host Name for which datastore has to be fetched

        returns:
                _sorted_datastore_dict  (dict)  -   Returns the descending
                sorted datastore dict according to free space
        """
        try:
            _datastore_dict = self._get_datastore_dict(host_name)
            _sorted_datastore_dict = OrderedDict(sorted
                                                 (_datastore_dict.items(),
                                                  key=itemgetter(1), reverse=True))
            return _sorted_datastore_dict

        except Exception as err:
            self.log.exception("An exception {} occurred getting datastore priority list from VRM".format(err))
            raise Exception(err)

    def _get_host_priority_list(self):
        """
        Returns the descending sorted host Dict according to Memory

        Returns:
                _sorted_host_dict  (dict)  -   Returns the descending
                sorted datastore dict according to Memory
        """
        try:
            _host_dict = self._get_host_dict()
            _host_dict = dict(zip(list(_host_dict.keys()),
                                  [value['Memory'] for name, value in _host_dict.items()]))

            _sorted_host_dict = OrderedDict(sorted
                                            (_host_dict.items(),
                                             key=itemgetter(1), reverse=True))
            return _sorted_host_dict

        except Exception as err:
            self.log.exception("An exception {} occurred getting host priority list from VRM".format(err))
            raise Exception(err)

    def _get_required_resource_for_restore(self, vm_list):
        """
        get the required resource for restore

        Args:
            vm_list             (list):  list of Vms for restore

        Returns:
            _vm_total_memory    (int):  Total memory required for restoring

            _vm_total_space     (int):  Total disk space required for restoring

        """

        try:
            _vm_total_memory = 0
            _vm_total_space = 0
            for _each_vm in vm_list:
                self.VMs[_each_vm].update_vm_info('memory')
                _vm_memory = self.VMs[_each_vm].memory
                self.VMs[_each_vm].update_vm_info('vm_space')
                _vm_space = self.VMs[_each_vm].vm_space
                _vm_total_memory = _vm_total_memory + float(_vm_memory)
                _vm_total_space = _vm_total_space + float(_vm_space)
            return _vm_total_memory, _vm_total_space

        except Exception as err:
            self.log.exception(
                "An error occurred in _get_required_resource_for_restore")
            raise err

    def compute_free_resources(self, vm_list, proxy_client=None):
        """
        compute the free Resource of the Vcenter based on free memory and cpu

        Args:

                vm_list		    (list):     list of Vms to be restored

                proxy_client    (str):      proxy client

        Returns:
                Datastore	    (str):      the Datastore where restore can be performed

                Host            (str):      Host where restore has to be performed

                proxy_client    (str):      Proxy machine used for restore

        """
        try:
            datastore_name = None
            host_name = None
            _total_vm_memory, _total_disk_space = self._get_required_resource_for_restore(vm_list)
            proxy_host = self._get_vm_host(proxy_client)

            _host_priority_dict = self._get_host_priority_list()
            for each_host in _host_priority_dict.items():
                if (each_host[1]) > _total_vm_memory:
                    self.log.info(
                        "the Host %s has higher "
                        "memory than the total VMs" % each_host[0])
                    if proxy_host and proxy_host.lower() == each_host[0].lower():
                        self.log.info("We cannot have same as destination client host as there is known limitation ")
                        continue
                    else:
                        host_name = each_host[0]
                        break
                else:
                    continue

            _datastore_priority_dict = self._get_datastore_priority_list(host_name)
            for each_datastore in _datastore_priority_dict.items():
                if (each_datastore[1]) > _total_disk_space:
                    datastore_name = each_datastore[0]
                    self.log.info(""
                                  "The Datastore %s has more than total"
                                  "disk space in VM" % datastore_name)
                    break
                else:
                    continue

            return datastore_name, host_name

        except Exception as err:
            self.log.exception(
                "An error occurred in compute_free_resources ")
            raise err

    def wait_for_tasks(self, task_url):
        """

        Args:
            task_url            (str):      Task url

        Returns:
                                True:   Task completed successfully
                                False:  Task failed

        """
        try:
            _attempt = 1
            task_uri = 'https://{}:{}{}'.format(self.server_host_name, self.port, task_url)
            while _attempt <= 5:
                flag, response = self.make_request('GET', task_uri)
                status, type, progress = response.json()['status'], response.json()['type'], response.json()['progress']
                # Possible status codes are 'running', 'waiting', 'success', 'failed'
                # Do not return false if task is waiting. Only return false in case task fails.
                _sleep_time = _attempt ** 3
                self.log.info("| Type: [{}] | Status: [{}] | Progress: [{}] | Sleep: [{} sec]".format(type, status, progress, _sleep_time))
                if flag:
                    if status in ['running', 'waiting']:
                        time.sleep(_sleep_time)
                        _attempt += 1
                    elif status == 'success':
                        return True
                    elif status == 'failed':
                        self.log.exception("Task failed. Please check: {}", task_uri)
                        return False
            self.log.exception("wait_for_task timed out. Last known status: {}", status)
            return False
        except Exception as err:
            self.log.exception("An error occurred in getting task detail")
            raise err
