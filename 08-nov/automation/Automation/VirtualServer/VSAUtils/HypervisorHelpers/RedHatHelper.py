# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Red Hat """

from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils import VirtualServerUtils
from collections import OrderedDict
from operator import itemgetter
import ovirtsdk4 as sdk


class RedHatHelper(Hypervisor):
    """
    Main class for performing all operations on Red Hat Hypervisor
    """

    # Call the test method to check the connectivity with the server. If
    # connectivity works this method will return "True". If there is any
    # connectivy problem it will either return "False" or raise an exception
    # if the "raise_exception" parameter is "True".
    def __init__(self,
                 server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):
        """
        Initialize Red Hat Helper class properties

        Args:
            server_host_name    (str):      Hostname of the Red Hat Server

            host_machine        (str):      Red Hat Server name

            user_name           (str):      Username of the Red Hat Server

            password            (str):      Password of the Red Hat Server

            instance_type       (str):      Instance type of the Red Hat Server

            auto_commcell       (object):   Commcell object
        """

        super(RedHatHelper, self).__init__(server_host_name, user_name, password,
                                           instance_type, commcell, host_machine)

        self.vm_dict = {}
        self.server_host_name = server_host_name[0]
        self.server = None
        self.rhev_url = 'https://{0}/ovirt-engine/api'.format(self.server_host_name)
        self.connection = None
        self.rhev_login()

    def rhev_login(self):
        """
        Login and check connection with the Red Hat Server
        """

        self.connection = sdk.Connection(
            ca_file=VirtualServerUtils.get_details_from_config_file('rhev', 'ca_path'),
            url=self.rhev_url,
            username=self.user_name,
            password=self.password
        )
        if self.connection.test(raise_exception=False):
            self.log.info("Connection works. checking VMs")
        else:
            self.log.error("Connection doesn't work.")
        api = self.connection.system_service().get()
        self.log.info("version: {}".format(api.product_info.version.full_version))
        self.log.info("hosts: {}".format(api.summary.hosts.total))
        self.log.info("sds: {}".format(api.summary.storage_domains.total))
        self.log.info("users: {}".format(api.summary.users.total))
        self.log.info("vms: {}".format(api.summary.vms.total))

    def get_all_vms_in_hypervisor(self, server="", pattern="", c_type=""):
        """
        Args:
            server          (str):  RHEV Server for which all the VMs has to be fetched

            pattern         (str):  Pattern to fetch the vms

            c_type            (str):  Type of content

        Returns:
            vms_list        (str):  List of VMs in the host of the RHEV

        Raises:
            Exception:
                Not able to get the vms from RHEV Server
        """
        vms_service = self.connection.system_service().vms_service()
        vms = vms_service.list()
        vms_list = []
        for vm in vms:
            vms_list.append(vm.name)
        return vms_list

    def get_storage_space(self):
        """
        Gets the storage domains with their corresponding available space

        Returns:
            storage_dict    (dict):     a dict of storage domains and
                                        the amount of their free space in GB
        """
        sds_service = self.connection.system_service().storage_domains_service()
        sd = sds_service.list()
        storage_dict = {}
        for sds in sd:
            if sds.available:
                storage_dict.update({sds.name: VirtualServerUtils.bytesto(sds.available, "GB")})
        return storage_dict

    def get_total_disk_size(self, vms):
        """
        Gets the total size of all disks
        Args:
            vms          (str):  Vms's whose total disk size needs to be calculated

        Returns: the sum of the all the disk sizes
        """
        vms_service = self.connection.system_service().vms_service()
        vms_list = vms_service.list()
        disk_size = 0
        for vm in vms_list:
            if vm.name not in vms:
                continue
            vm_service = vms_service.vm_service(vm.id)
            disk_attachments_service = vm_service.disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                disk = self.connection.follow_link(disk_attachment.disk)
                disk_size += VirtualServerUtils.bytesto(disk.actual_size, "GB")
        return disk_size

    def _get_repository_priority_list(self):
        """
        Returns the descending sorted storage according to free space

        Returns:
            _sorted_storage_dict   (dict):  Returns the descending sorted
                                            datacenter list according to free space

        Raises:
            Exception:
                Not able to get datastore priority list
        """
        try:

            storage_dict = self.get_storage_space()
            _sorted_storage_dict = OrderedDict(sorted
                                               (storage_dict.items(), key=itemgetter(1),
                                                reverse=True))
            return _sorted_storage_dict
        except Exception as err:
            self.log.exception(
                "An exception %s occurred getting datastore priority list from VRM", str(err))
            raise Exception(err)

    def compute_free_resources(self, vm_list):
        """
        compute the free hosting hypervisor and free space for disk in hypervisor

        Args:
            vm_list         (str):  Vms's whose destination need to be calculated

        Return:
            _cluster.name   (str):  hypervisor cluster where vm is to be restored

            repository      (str):  datastore where vm is to be restored

        Raises:
            Exception:
                Not able to compute free resource
        """
        try:
            repository = None
            _repository_priority_dict = self._get_repository_priority_list()
            _total_disk_space = self.get_total_disk_size(vm_list)
            sds_service = self.connection.system_service()
            for _repo in _repository_priority_dict.items():
                sd = sds_service.storage_domains_service().list(search='name={}'.format(_repo[0]))[0]
                if sd.type.value == 'iso':
                    continue
                vms_in_sd = self.connection.follow_link(sd.vms)
                for _vm in vms_in_sd:
                    if _vm.name in vm_list:
                        if _repo[1] > _total_disk_space:
                            repository = _repo[0]
                            break
            sd = sds_service.storage_domains_service().list(search='name={}'.format(repository))[0]
            # host_name = sd.storage.address.partition('.')[0]
            host_name = sd.storage.address
            ht = sds_service.hosts_service().list(search='address={}'.format(host_name))
            cl = self.connection.follow_link(ht[0].cluster)
            c_list = sds_service.clusters_service().list()
            for _cluster in c_list:
                if _cluster.data_center.id == cl.data_center.id:
                    return _cluster.name, repository
            raise Exception("No suitable clusters and datastore found")
        except Exception as err:
            self.log.exception(
                "An exception %s occurred in computing free resources for restore", str(err)
            )
            raise Exception(err)
