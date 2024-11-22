# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Xen """

import XenAPI
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor


class XenHelper(Hypervisor):
    """
    Main class for performing all operations on Xen Hypervisor
    """

    def __init__(self,
                 server_host_name,
                 user_name,
                 password,
                 instance_type,
                 auto_commcell,
                 host_machine,
                 **kwargs):

        """
        Initialize XEN Helper class properties


            Args:
                server_host_name    (str):      server list at instance level

                host_machine        (str):      Co-ordinator at instance level

                user_name           (str):      username of Nutanix cluster

                password            (tupple):   consist of password, nutanix cluster
                                                URL

                instance_type       (str):      Instance type of the Nutanix AHV

                commcell            (object):   Commcell object

        """

        super(XenHelper, self).__init__(server_host_name, user_name, password,
                                        instance_type, auto_commcell, host_machine)
        self.username = user_name
        self.password = password
        self.server = server_host_name[0]
        self.url = "http://" + self.server
        self.connection = None
        self._login()

    def _login(self):
        try:
            session = XenAPI.Session(self.url)
            session.xenapi.login_with_password(self.username, self.password, "2.14")
            self.connection = session.xenapi
        except Exception as err:
            self.log.exception("Exception login to {} {}".format(self.url, err))
            raise err

    def get_all_vms_in_hypervisor(self):
        """
        Get information about all VMs.

        Raises:
            Exception:
                Failed to get information about all VMs
        """
        try:
            all_vms = self.connection.VM.get_all()
            vms = []
            for vm in all_vms:
                record = self.connection.VM.get_record(vm)
                vms.append(record['name_label'])
            return vms
        except Exception as err:
            self.log.exception("Exception in getting vms info {}".format(err))
            raise err

    def compute_free_resources(self, vm_list):
        """
        compute the free Resource of the Xen Server based on space

        Args:
                vm_list		        (list): list of Vms to be restored

        Returns:
               _server              (str): Xen server

               _storage              (str):  Storage for the server


        Raises:
            Exception:
                if there is an error in computing the resources of the endpoint.

        """
        try:
            _server, _storage = (None,) * 2
            for vm in vm_list:
                if not _server:
                    _server = self.VMs[vm].host
                else:
                    if _server != self.VMs[vm].host:
                        self.log.exception("VMs are on multiple servers. Please pass the server in input JSON.")
            vbds = self.connection.SR.get_all()
            _datastore_dict = {}
            for vbd in vbds:
                report = self.connection.SR.get_record(vbd)
                if report['type'] in ('lvm', 'lvmoiscsi', 'nfs'):
                    _datastore_dict[report['uuid']] = report['name_label'], report['PBDs'], report['physical_size']
            _max_storage = 0
            _server_details = self.connection.host.get_by_name_label(_server)
            _server_details = self.connection.host.get_record(_server_details[0])
            for _key, _val in _datastore_dict.items():
                if set(_val[1]).issubset(set(_server_details['PBDs'])):
                    if _max_storage == 0:
                        _max_storage = int(_val[2])
                        _storage = _val[0]
                    else:
                        if _max_storage > int(_val[2]):
                            _max_storage = int(_val[2])
                            _storage = _val[0]
            return _server, _storage
        except Exception as err:
            self.log.exception("An exception {0} occurred in computing free resources"
                               " for restore".format(err))
            raise Exception(err)

    def find_vm(self, vm_name):
        """
            Finds the vm and returns its status, host and storage repository

            Args:
                vm_name             (str): Name of the VM to be searched

            Returns:
                vm_detail           (list): VM found status, host and SR

            Raises:
                Exception:
                    Raise exception when failed to get the status of the vm
            """
        try:
            get_all_vms = self.get_all_vms_in_hypervisor()
            vms = dict(filter(lambda elem: vm_name == elem[1], get_all_vms))
            if len(vms) == 0:
                return False, None, None
            if len(vms) == 1:
                for vm in vms:
                    _ds = vm.config.files.logDirectory
                    _ds = _ds[_ds.find("[") + 1:_ds.find("]")]
                    return True, vm.runtime.host.name, _ds
            return 'Multiple', None, None

        except Exception as err:
            self.log.exception("Exception was raised while finding the VM.")
            raise err
