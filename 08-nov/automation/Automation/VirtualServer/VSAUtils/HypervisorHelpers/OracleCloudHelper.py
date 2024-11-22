# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Oracle Cloud """

import requests
import re
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils import OracleCloudServices


class OracleCloudHelper(Hypervisor):
    """
    Main class for performing all operations on Oracle Cloud Classic Hypervisor
    """

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):
        """
        Initialize the Oracle Cloud Hypervisor Helper Options

        Args:
            server_host_name    (str)    --  the hostname of the oracle cloud server

            host_machine        (str)    --  the hostname of the client where the scripts
                                                    will be executed

            user_name           (str)    --  the user name of the client

            password            (str)    --  the password of the client

            instance_type       (str)    --  the type of instance

            commcell            (object)        --  the commcell object

        """
        super(OracleCloudHelper, self).__init__(server_host_name,
                                                user_name,
                                                password,
                                                instance_type,
                                                commcell,
                                                host_machine)

        self.vm_dict = {}
        if 'Compute' not in self.user_name:
            self.user_name = "Compute-{0}".format(self.user_name)
        self._identity_domain = self.user_name.split("/")[0]
        self._services = OracleCloudServices.get_services(self.server_host_name)
        self._headers = {
            'Accept': 'application/oracle-compute-v3+json',
            'Content-type': 'application/oracle-compute-v3+json',
        }

        self._vm_services = OracleCloudServices.get_vm_services(self.server_host_name,
                                                                self._identity_domain)
        self.instances_json = None
        self.get_all_vms_in_hypervisor()

    def _compute_login(self):
        """
        Does login to the Oracle Cloud Hypervisor

        Raises:
            Exception:
                if login to the Oracle Cloud end point fails

        """

        try:
            payload = {'user': self.user_name, 'password': self.password}
            flag, response = self._make_request('POST', self._services['LOGIN'], payload)
            if flag:
                self._headers['Cookie'] = response.headers['Set-Cookie']

        except Exception as err:
            self.log.exception("An exception occurred while logging in to the end point")
            raise Exception(err)

    def _make_request(self, method, url, payload=None, attempts=0, directory=False):
        """Makes the request of the type specified in the argument 'method'

        Args:
            method    (str)  --  http operation to perform, e.g.; GET, POST, PUT, DELETE

            url       (str)  --  the web url or service to run the HTTP request on

            payload   (dict / str)  --  data to be passed along with the request
                default: None

            attempts  (int)         --  number of attempts made with the same request
                default: 0

        Returns:
            tuple:
                (True, response) -- in case of success

                (False, response) -- in case of failure

        Raises:
            Oracle Cloud SDK Exception:
                if the method passed is incorrect/not supported

            requests Connection Error   --  requests.exceptions.ConnectionError

        """
        try:
            headers = self._headers

            if directory:
                headers['Accept'] = 'application/oracle-compute-v3+directory+json'

            if method == 'POST':
                response = requests.post(url, headers=headers, json=payload)
            elif method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=payload)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise Exception('HTTP method {} not supported'.format(method))

            if response.status_code == 401 and response.headers['Set-Cookie'] is not None:
                if attempts < 3:
                    self._compute_login()
                    return self._make_request(method, url, attempts + 1)
                else:
                    # Raise max attempts exception, if attempts exceeds 3
                    raise Exception('Error', '103')

            elif response.status_code == 200:
                return True, response

            elif response.status_code == 204 and response.headers['Set-Cookie'] is not None:
                return True, response

            else:
                return False, response

        except requests.exceptions.ConnectionError as con_err:
            raise Exception(con_err)

    def get_all_vms_in_hypervisor(self, server=None, pattern="", c_type=""):
        """
        Get all the vms for Oracle Cloud

        Args:
            server (str)   --  User for which all the VMs has to be fetched

            pattern (str)   -- Pattern to fetch the vms

            c_type            (str):  Type of content

        Returns:
           _all_vm_list    (list)   --   List of VMs in the host of the pseudoclient

        Raises:
              Exception:
                    if there is an exception in getting all the VMs in the user

       """

        try:
            if 'Cookie' not in self._headers.keys():
                self._compute_login()
            _temp_vm_list = []
            vm_list = []
            url = self._vm_services['GET_INSTANCES']
            if server:
                url = url + "/" + server
            flag, response = self._make_request('GET', url)
            if flag:
                vm_list_response = response.json()['result']
                self.instances_json = vm_list_response
                for vm_name in vm_list_response:
                    self.vm_dict[vm_name['label']] = vm_name['name']
                    _temp_vm_list.append(vm_name['label'])

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
            self.log.exception("An exception {0} occurred getting VMs from Oracle Cloud".format(
                err))
            raise Exception(err)

    def _get_user_list(self):
        """
        Get the list of users in the Identity Domain of Oracle Cloud

        Returns:
            _compute_users_list	(list)	-- List of all users in the identity domain

        Raises:
            Exception:
                if there is an error in getting the list of all users in the endpoint.

        """
        try:
            _compute_users_list = []

            flag, response = self._make_request('GET', self._vm_services['GET_INSTANCES'],
                                                directory=True)
            if flag:
                user_list_response = response.json()['result']
                for user in user_list_response:
                    _compute_users_list.append(user)
            return _compute_users_list
        except Exception as err:
            self.log.exception("An exception {0} occurred getting users from the "
                               "identity domain".format(err))
            raise Exception(err)

    def _get_security_list(self):
        """
        Gets the list of all security lists of Oracle Cloud

        Returns:
             _security_list  (list)  --  list of all security lists in Oracle Cloud

        Raises:
            Exception:
                if there is an exception is getting all the security lists in the endpoint.

        """
        try:
            _security_list = []

            flag, response = self._make_request('GET', self._vm_services['GET_SECLIST'])
            if flag:
                security_list_response = response.json()['result']
                for sec in security_list_response:
                    _security_list.append(sec)
            return _security_list
        except Exception as exp:
            self.log.exception("An exception occurred getting security lists. {0}".format(exp))
            raise Exception(exp)

    def _get_instance_user_name(self, instance_name):
        """
        Get the user name of the instance in Oracle Cloud

        Args:
                instance_name (str)  --   name of the instance whose username has
                                                to be obtained

        Returns:
                instance_user_name	(str)    -- username to which the instance belongs

        Raises:
            Exception:
                if there is an error in getting the user name of an instance

        """
        try:
            instance_user_name = None

            for vm_name in self.instances_json:
                if vm_name['label'] == instance_name:
                    instance_user_name = vm_name['name'].split(vm_name['label'])[0].split(
                        self._identity_domain)[1].replace('/', '')
            return instance_user_name
        except Exception as err:
            self.log.exception(
                "An exception {0} occurred getting the user name of the instance".format(err)
            )
            raise Exception(err)

    def _get_security_list_of_instance(self, instance_name):
        """
        Get the security list associated with the instance

        Args:
                instance_name (str)  --   name of the instance whose security list
                                                    has to be obtained

        Returns:
            security_lists  (list)  --  list of all security lists associated with the instance

        Raises:
            Exception:
                if there is an error in getting the security lists associated with the instance

        """
        try:
            security_lists = []

            for vm_name in self.instances_json:
                if vm_name['label'] == instance_name:
                    for key, value in vm_name['networking'].items():
                        security_lists += [x.rsplit("/", 1)[-1] for x in value['seclists']]
            return security_lists
        except Exception as exp:
            self.log.exception("An exception occurred while getting the security list of the"
                               "instance. {0}".format(str(exp)))
            raise Exception(exp)

    def _get_ssh_keys_of_instance(self, instance_name):
        """
        Get the ssh keys associated with the instance

        Args:
                instance_name (str)  --  name of the instance whose ssh keys has
                                                to be obtained

        Returns:
            ssh_keys  (list)  --  list of all ssh keys associated with the instance

        Raises:
            Exception:
                if there is an error in getting the list of all ssh keys associated with instance

        """
        try:
            ssh_keys = []

            for vm_name in self.instances_json:
                if vm_name['label'] == instance_name and vm_name['sshkeys']:
                    ssh_keys += [x.rsplit("/", 1)[-1] for x in vm_name['sshkeys']]
            return ssh_keys
        except Exception as exp:
            self.log.exception("An exception occurred while getting the ssh keys of the"
                               "instance. {0}".format(str(exp)))
            raise Exception(exp)

    def compute_free_resources(self, proxy_list, vm_list):
        """
        compute the free Resource of the Vcenter based on free memory and cpu

        Args:

                proxy_list  (list)  --  list of all proxies

                vm_list		(list)  --  list of Vms to be restored

        Returns:
                security_list   (list)  --   the security lists to be attached to the instances

                host_name       (str)   --   the host where instances are to be restored

                ssh_keys        (str)  --   The ssh keys to be attached to the instances

        Raises:
            Exception:
                if there is an error in computing the resources of the endpoint.

        """
        try:
            security_list = []
            ssh_keys = []
            host_name = min(proxy_list, key=proxy_list.count)

            for vm_name in vm_list:
                security_list += self._get_security_list_of_instance(vm_name)
                ssh_keys += self._get_ssh_keys_of_instance(vm_name)

            return security_list, host_name, ssh_keys

        except Exception as err:
            self.log.exception("An exception {0} occurred in computing free resources"
                               " for restore".format(err))
            raise Exception(err)
