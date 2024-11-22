# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Open Stack """

from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils import OpenStackWrapper


class OpenStackHelper(Hypervisor):
    """
    Main class for performing all operations on OpenStack
    """

    def __init__(self, server_host_name,
                 host_machine,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 **kwargs):
        """
        Initialize the OpenStack instance

        Args:
            server_host_name    (str)    --  the hostname of the openstack server

            user_name           (str)    --  the user name of the openstack server

            password            (str)    --  the password of the openstack server

            instance_type       (str)    --  the type of instance

            commcell            (object)        --  the commcell object


        """

        super(OpenStackHelper, self).__init__(server_host_name, host_machine,
                                              user_name, password, instance_type, commcell)
        self.OpenStackHandler = OpenStackWrapper.OpenStackVMops(self.server_host_name, self.user_name, self.password)
        self.vm_dict = {}
        self.instances_json = None
        self.get_all_vms_in_hypervisor()

    def get_all_vms_in_hypervisor(self, server=None):
        """
        Get all the vms from Openstack server

        Args:
            server (str)   --  User for which all the VMs has to be fetched

        Returns:
           _all_vm_list    (list)   --   List of VMs in the host of the pseudoclient

        Raises:
              Exception:
                    if there is an exception in getting all the VMs in the user

       """

        try:
            self.vm_dict = self.OpenStackHandler.get_instance_list()
            _vmlist = self.vm_dict.keys()
            return _vmlist

        except Exception as err:
            self.log.exception("An exception {0} occurred getting VMs from Oracle Cloud".format(
                err))
            raise Exception(err)

    def compute_free_resources(self, vm_name, project_name=None, securityGroups=None, esxHost=None):
        """
            compute the free Resource of the Vcenter based on free memory and cpu

            Args:

                    proxy_list  (list)  --  list of all proxies

                    vm_list		(list)  --  list of Vms to be restored

                    project_name (string) -- Name of the project the selected Openstack VM is in

                    securityGroups (string) -- The security groups present in the selected Openstack VM

                    esxHost (string) -- The availability_zone of the selected Openstack VM

            Returns:
                   dictionary of Datacenter -> Project, cluster ->zone, Datastore -> volumeType, networkname -> ,
                   esxServerName -> OShostname, esxHost -> zone,

            Raises:
                Exception:
                    if there is an error in computing the resources of the endpoint.

            """
        try:
            restoreObj = {}
            # Set datacenter to Project name
            if project_name:
                restoreObj["Datacenter"] = project_name
            else:
                restoreObj["Datacenter"] = self.OpenStackHandler.projectName
            # Security groups
            restoreObj["securityGroups"] = securityGroups
            # Availability zone to restore the VM to
            restoreObj["AZ"] = self.VMs[vm_name].volumelist[0]['availability_zone']
            # Get volumetype from openstack server
            restoreObj["Datastore"] = self.OpenStackHandler.get_volume_typefrom_volid \
                (self.VMs[vm_name].volumelist[0]['id'])
            # esxServername is openstack server hostname
            restoreObj["esxServerName"] = self.server_host_name
            # esxHost will be set to zone
            if esxHost:
                restoreObj["esxHost"] = esxHost
            else:
                restoreObj["esxHost"] = self.VMs[vm_name].volumelist[0]['availability_zone']
            # Cluster will be set to the RegionName from the openstack server
            restoreObj["Cluster"] = self.OpenStackHandler.get_region()

            return restoreObj

        except Exception as err:
            self.log.exception("An exception {0} occurred in computing free resources"
                               " for restore" + str(err))
            raise Exception(err)

