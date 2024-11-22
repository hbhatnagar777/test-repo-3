# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Nutanix """

import requests
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor


class NutanixHelper(Hypervisor):
    """
    Main class for performing all operations on Nutanix AHV Hypervisor
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
        Initialize Nutanix AHV Helper class properties


            Args:
                server_host_name    (str):      server list at instance level

                host_machine        (str):      Co-ordinator at instance level

                user_name           (str):      username of Nutanix cluster

                password            (tupple):   consist of password, nutanix cluster
                                                URL

                instance_type       (str):      Instance type of the Nutanix AHV

                commcell            (object):   Commcell object

        """

        super(NutanixHelper, self).__init__(server_host_name,
                                            user_name,
                                            password,
                                            instance_type,
                                            commcell,
                                            host_machine)
        self.nutanix_cluster = password[1]
        self.username = user_name
        self.password = password[0]
        self.rest = r"api/nutanix/v0.8/"
        self.restv2 = "PrismGateway/services/rest/v2.0/"
        self.restv3 = "api/nutanix/v3/"
        self.BaseUrl = "https://" + self.nutanix_cluster + ":9440/"
        self.url = self.BaseUrl + self.rest
        self.v2url = self.BaseUrl + self.restv2
        self.v3url = self.BaseUrl + self.restv3
        self.vmlist = {}
        self.nutanixsession = requests.Session()
        self.nutanixsession.auth = (self.username, self.password)
        self.nutanixsession.headers.update({'Content-Type': 'application/json; charset=utf-8'})

    def all_vm_info(self):
        """
        Get information about all VMs.

        Raises:
            Exception:
                Failed to get information about all VMs
        """
        try:
            vm_info_url = self.url + 'vms' + '/?includeVMDiskSizes=true&includeAddressAssignments=true'
            data = self.nutanixsession.get(vm_info_url, verify=False).json()
            self.log.info("Dump VMInfoURL: " + vm_info_url)
            self.vmlist = data["entities"]

        except:
            self.log.exception("Exception in all_vm_info")

    def get_nic_info(self, nicuuid):
        """
        Get all network Info related to the given network interface.

        Raises:
            Exception:
                Failed to fetch network details
        """
        try:
            nic_info_url = self.url + 'networks/' + nicuuid + '/snapshots?includeSnapshots=true'
            self.log.info("Dump NicInfoURL: " + nic_info_url)
            data = self.nutanixsession.get(nic_info_url, verify=False)
            response = data.json()
            self.log.info("Dump NicInfo: " + str(response))
            if data.status_code == 200:
                return response

        except Exception as err:
            self.log.exception("Exception in get_nic_info")
            raise Exception(err)

    def get_snap_info(self, vm_guid):
        """
        Get all Snapshot Info related to the given VM.

        Raises:
            Exception:
                Failed to get snapshot related information
        """
        try:
            snap_info_url = self.url + 'vms/' + vm_guid + '/snapshots?includeSnapshots=true'
            self.log.info("Dump SnapInfoURL: " + snap_info_url)
            data = self.nutanixsession.get(snap_info_url, verify=False)
            response = data.json()
            self.log.info("Dump SnapInfo: " + str(response))
            if data.status_code == 200:
                return response

        except Exception as err:
            self.log.exception("Exception in get_snap_info")
            raise Exception(err)

    def get_v3snap_count(self, vm_guid):
        """
        Get Snapshot count of the given VM using v3 api

        Raises:
            Exception:
                Failed to get snapshot related information
        """
        try:
            snap_info_url = self.v3url + 'vm_snapshots/list'
            self.log.info("Dump SnapInfoURL: " + snap_info_url)
            d = {"filter": "entity_uuid==" + vm_guid + ""
                , "kind": "vm_snapshot", "sort_order": "ASCENDING"}
            data = self.nutanixsession.post(snap_info_url, json=d, auth=('admin', 'password'), verify=False)
            response = data.json()
            self.log.info("Dump response: " + str(response))

            for x in response["entities"]:
                self.log.info("list of snapshots: {} ".format(x["metadata"]["uuid"]))
            snap_count = (len(response["entities"]))

            return snap_count

        except Exception as err:
            self.log.exception("Exception in get_snap_names")
            raise Exception(err)

    def compute_free_resources(self, vm_name):
        """
            compute the free Resource of the Vcenter based on free memory and cpu

            Args:
                    vm_name		(list)  --  list of Vms to be restored

            Returns:
                   vm_container (str)   --  storage container of VM

            Raises:
                Exception:
                    if there is an error in computing the resources of the endpoint.

            """
        try:
            vm = vm_name[0]
            for disks in self.VMs[vm].disk_info:
                if "containerId" in disks:
                    self.container_uuid = disks["containerUuid"]
                    container_url = self.v2url + 'storage_containers/' + self.container_uuid
                    data = self.nutanixsession.get(container_url, verify=False).json()
                    self.log.info("Dump VMInfoURL: " + container_url)
                    self.vm_container = data["name"]
                    break
                else:
                    self.log.info("checking for other disk")

            return self.vm_container

        except Exception as err:
            self.log.exception("An exception {0} occurred in computing free resources"
                               " for restore".format(err))
            raise Exception(err)
