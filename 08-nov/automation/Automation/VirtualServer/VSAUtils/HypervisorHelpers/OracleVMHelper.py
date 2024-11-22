# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on OracleVM """

import requests
import time
from collections import OrderedDict
from operator import itemgetter
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils import VirtualServerUtils


class OracleVMHelper(Hypervisor):
    """
    Main class for performing all operations on OracleVM Hypervisor
    """

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):

        super(OracleVMHelper, self).__init__(server_host_name, user_name, password,
                                             instance_type, commcell, host_machine)

        self.vm_dict = {}
        self._server_host_name = server_host_name[0]
        self._username = user_name
        self._password = password
        self._baseUri = 'https://' + self._server_host_name + ':7002/ovm/core/wsapi/rest'
        self._vm_manager_session = None
        self.server = None
        self.servers_list = []
        self.cluster_repos = None
        self._create_session()
        self.get_all_vms_in_hypervisor()

    def _make_request(self, method, url, payload=None, attempts=0):
        """Makes the request of the type specified in the argument 'method'

        Args:
            method    (str)         --  http operation to perform, e.g.; GET, POST, PUT, DELETE

            url       (str)         --  the web url or service to run the HTTP request on

            payload   (dict / str)  --  data to be passed along with the request
                default: None

            attempts  (int)         --  number of attempts made with the same request
                default: 0

        Returns:
            tuple:
                (True, response) - in case of success

                (False, response) - in case of failure

        Raises:
            OracleVM SDK Exception:
                if the method passed is incorrect/not supported

            requests Connection Error   --  requests.exceptions.ConnectionError

        """
        try:
            _REST_methods = ['POST', 'GET', 'PUT', 'DELETE']

            if str(method).upper() not in _REST_methods:
                raise Exception('HTTP method {} not supported'.format(method))

            if method == 'POST':
                response = self._vm_manager_session.post(url, verify=False, auth=payload)
            elif method == 'GET':
                response = self._vm_manager_session.get(url, verify=False)
            elif method == 'PUT':
                response = self._vm_manager_session.put(url, verify=False, json=payload)
            elif method == 'DELETE':
                response = self._vm_manager_session.delete(url, verify=False)

            if response.status_code == 401:
                """ clear the expired cookies so that requests module will use the username and
                 password for next request and update the session with new cookies"""
                self._vm_manager_session.cookies.clear()
                self._make_request(method, url, payload, attempts)
            elif response.status_code == 200:
                return True, response
            else:
                return False, response
        except requests.exceptions.ConnectionError as con_err:
            raise Exception(con_err)

    def _get_required_resource_for_restore(self, vm_list):
        """
        get the required resource for restore
        Args:
            vm_list             (list): list of Vms for restore

        Returns:
            _vm_total_memory    (int)   -   Total memory required for restoring

            _vm_total_space (int)   -   Total disk space required for restoring

        Raises:
            Exception:
                if it fails to get resource for restore
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
                "An error occurred in getting resource for restoring vm")
            raise err

    def _verify_manager_state(self, manager_json, retry_count=3):
        """
        Safety check to verify if the Oracle VM manager is in running state.
        Args:
            manager_json: Response of the vm manager

            retry_count: number of times the verification should happen if
                        the vm manager is in starting state

        Raises:
            Exception:
                if it fails to verify manager status

        """
        if manager_json["managerRunState"] == "RUNNING":
            self.log.info("VM Manager is running. Session successfully created")
        elif manager_json["managerRunState"] == "STARTING":
            self.log.info("VM Manager is in " + manager_json[
                "managerRunState"] + " state re-checking after one minute")
            if retry_count != 0:
                time.sleep(60)
                new_manager_response = self._vm_manager_session.get(self._baseUri + "/Manager")
                retry_count -= 1
                self._verify_manager_state(new_manager_response.json()[0], retry_count)
            else:
                Exception(
                    "Retry limit reached. VM Manager status is " + manager_json["managerRunState"])
        else:
            Exception(
                "{} invalid running state of VM manager".format(manager_json["managerRunState"]))

    def _create_session(self, force_new=False):
        """Creates session
        Args:
            force_new           (bool):     Force to create a new session

        """

        if self._vm_manager_session is not None and force_new is False:
            return
        else:
            self._vm_manager_session = requests.session()
            self._vm_manager_session.auth = (self._username, self._password)
            self._vm_manager_session.verify = False
            self._vm_manager_session.headers.update(
                {'Accept': 'application/json', 'Content-Type': 'application/json'})
            r = self._vm_manager_session.get(self._baseUri + "/Manager")
            if r.status_code != 200:
                Exception("Oracle VM manager is not responding")
            else:
                self._verify_manager_state(r.json()[0])

    def get_cluster_repositories(self):
        """
        Total available repositories available under the cluster
        Returns:
             self.cluster_repos     (json): list of the repositories for the cluster

        Raises:
            Exception:
                if it fails to get cluster repositories
        """
        if self.cluster_repos is not None:
            return self.cluster_repos
        try:
            flag, response = self._make_request("GET", self._baseUri + '/Repository')
            if flag:
                self.cluster_repos = response.json()
            return self.cluster_repos

        except Exception as err:
            self.log.exception("An exception occurred while retrieving server list")
            raise Exception(err)

    def _get_server_repositories(self, server=None):
        """
        Get Available repos that are under a server
        Args:
            server          (string): Server for which the repos need to be listed

        Returns:
            _server_repositories    (list): list of repository dicts for a server

        """
        _server_repositories = []
        available_repos = self.get_cluster_repositories()
        if server is not None:
            for _repo in available_repos:
                if len(_repo["presentedServerIds"]) > 0:
                    for _presentedServer in _repo["presentedServerIds"]:
                        if _presentedServer["name"] == server:
                            _server_repositories.append(_repo)
        else:
            _server_repositories = available_repos
        return _server_repositories

    def get_servers(self, server=""):
        """
        Get a required server or total servers available
        Args:
            server              (string): name of the server when passed returns only it's dict

        Returns:
            server_list             (list):        list of server(s)

        """
        server_list = []
        try:
            flag, response = self._make_request("GET", self._baseUri + '/Server')
            if flag:
                if server != "":
                    for _server in response.json():
                        if _server["name"] == server:
                            server_list.append(_server)
                else:
                    server_list = response.json()
            return server_list
        except Exception as err:
            self.log.exception("An exception occurred while retrieving server list")
            raise Exception(err)

    def get_all_vms_in_hypervisor(self, server="", pattern="", c_type=""):
        """
        Get the vm's that are available under a requested server
        Args:
            server: (str)    server on which the VMs should be listed

            pattern: (str)   Pattern to fetch the vms

            c_type            (str):  Type of content

        Returns:
            _vm_list        (list):        list of the vms on a given server

        """
        try:
            _vm_list = []
            _available_servers = self.get_servers(server=server)

            for server_dict in _available_servers:
                self.servers_list.append(server_dict["name"])
                for _vm_name in server_dict["vmIds"]:
                    self.vm_dict[_vm_name["name"]] = _vm_name["uri"]
                    _vm_list.append(_vm_name["name"])
            return _vm_list
        except Exception as err:
            self.log.exception("An exception occurred while getting vm's in hypervisor")
            raise Exception(err)

    def update_hosts(self):
        """ Updates the hosts"""
        self.log.info("Updating hosts of OracleVM hypervisor")
        self.get_all_vms_in_hypervisor()

    def _get_fileSystem_details(self, file_system_id):
        """
        Get the response of the given fileSystemId
        Args:
            file_system_id: (str)      UniqueID of the file system

        Returns:
            Response JSON of the file system requested

        Raises:
            Exception:
                if it fails to get file system details

        """
        _file_system_details = {}
        try:
            flag, response = self._make_request("GET",
                                                self._baseUri + '/FileSystem/' + file_system_id)
            if flag:
                _file_system_details = response.json()
            return _file_system_details
        except Exception as err:
            self.log.exception("An exception occurred while obtaining file system details")
            raise Exception(err)

    def _get_datastore_dict(self):
        """
        Get the dict of the datastore available on a given datastore
        Returns:
            _datastore_dict     (dict):     Response JSON of the datastore
        Raises:
            Exception:
                if it fails to get data store dict
        """
        _datastore_dict = {}
        _server_repos = self._get_server_repositories(server=self.server)
        try:
            for _server_repo in _server_repos:
                _file_system_info = self._get_fileSystem_details(
                    file_system_id=_server_repo["fileSystemId"]["value"])
                _datastore_dict[_server_repo["name"]] = VirtualServerUtils.bytesto(
                    _file_system_info["freeSize"], "GB")
            return _datastore_dict
        except Exception as err:
            self.log.info("An exception {0} occurred getting datastore's information".format(err))

    def _get_repository_priority_list(self):
        """
        Returns the descending sorted datastore Dict according to free space
        Returns:
            _sorted_datastore_dict  (dict)  -   Returns the descending sorted datastore dict
                                                according to the free space

        Raises:
            Exception:
                if it fails to get repository priority list
        """
        try:
            _datastore_dict = self._get_datastore_dict()
            _sorted_datastore_dict = OrderedDict(sorted
                                                 (_datastore_dict.items(),
                                                  key=itemgetter(1), reverse=True))
            return _sorted_datastore_dict

        except Exception as err:
            self.log.exception(
                "An exception {0} occurred getting datastore priority list from VRM".format(err))
            raise Exception(err)

    def server_of_vms(self, vm_list):
        """Server of the vms"""
        for vm in vm_list:
            if not self.server:
                self.server = self.VMs[vm].server_name
            else:
                if self.server != self.VMs[vm].server_name:
                    raise Exception("All vms are not in same server")

    def compute_free_resources(self, vm_list):
        """
        compute the free hosting hypervisor and free space for disk in hypervisor

        Args:
            vm_list     - list of Vm to be restored

        Return:
            self.server         (str)    - hypervisor host where vm is to be restored
                                        like esx

            repository          (str)    - diskspace where vm needs to be restored

        Raises:
            Exception:
                if it fails to fetch free resource for restore
        """
        try:
            repository = None
            if not self.server:
                self.server_of_vms(vm_list)
            _repository_priority_dict = self._get_repository_priority_list()
            _total_vm_memory, _total_disk_space = self._get_required_resource_for_restore(vm_list)
            for _repo in _repository_priority_dict.items():
                if _repo[1] > _total_disk_space:
                    repository = _repo[0]
                    break

            return self.server, repository

        except Exception as err:
            self.log.exception(
                "An exception {0} occurred in computing free resources for restore".format(err)
            )
            raise Exception(err)

    def close_session(self):
        """
        Close the VM Manager session
        """
        if self._vm_manager_session is not None:
            self._vm_manager_session.close()
            self.log.info("session closed")
