"""
To run execute the following command:
    python path\vcloud_entities.py path\sample.json
Input JSON Values:
login:
Purpose:Login to vcloud as system admin
Variables:
    Mandatory:
        hostname           (str): Host name of VCloud Director
        username           (str): system admin username
        password            (str): system admin password

providerVDC:
Purpose: Creation of Provider vdc
Variables:
    Mandatory:
        vimServerName         (str):  vim_server_name (VC name).
        resourcePoolNames     (list): list of resource_pool_names.
        storageProfiles        (list): list of storageProfile names.
        pvdcName               (str):  name of PVDC to be created.
    Non Mandatory:
        isEnabled              (bool): True to enable and False to disable.
        description             (str):  description of pvdc.
        highestHwVers         (str):  highest supported hw version number.
        vxlanNetworkPool      (str):  name of vxlan_network_pool.
        nsxtManagerName       (str):  name of nsx-t manager.

organization:
Purpose: Creating an organization
Variables:
    Mandatory:
        orgName            (str):  name of the organization
        fullOrgName       (str):  Full name of the organization
    Non mandatory:
        isEnabled          (str):  enable organization if True

orgVdc:
Purpose: To create new organization vdc
Varaibles:
    Mandatory:
        orgName            (str): Name of the organization
        vdcName           (str):  Name of the new organization vdc
        providerVDCName  (str):  Name of an existing provider vdc
        networkPoolName  (str):  Name to a network pool in the provider vdc that this org vdc should use
        storageProfile   (list): List of provider vdc storage profiles to add to this vdc. Each item is a
                                    dictionary that should include the following elements:

                                    name      (str):  Name of the PVDC storage profile
                                    enabled    (bool): True if the storage profile is enabled for this vdc
                                    units      (str):  Units used to define limit. One of MB or GB
                                    limit      (int):  Max number of units allocated for this storage profile
                                    default    (bool): True if this is default storage profile for this vdc
    Non Mandatory:
        description        (str):  description of the new org vdc
        allocationModel   (str):  Allocation model used by this vdc
                                        Accepted values are 'AllocationVApp', 'AllocationPool' or 'ReservationPool'
        cpuUnits          (str):  Unit for compute capacity allocated to this vdc
                                        Accepted values are 'MHz' or 'GHz'
        cpuAllocated      (int):  Capacity that is committed to be available
        cpuLimit          (int):  Capacity limit relative to the value specified for allocation
        memUnits          (str):  Unit for memory capacity allocated to this vdc
                                        Acceptable values are 'MB' or 'GB'
        memAllocated      (int):  Memory capacity that is committed to be available
        memLimit          (int):  Memory capacity limit relative to the value specified for allocation
        nicQuota          (int):  Maximum number of virtual NICs allowed in this vdc.
                                    0 specifies an unlimited number
        networkQuota      (int):  Maximum number of network objects that can be deployed in this vdc. Defaults to 1000
        vmQuota           (int):  Maximum number of VMs that can be created in this vdc. Defaults to 100
        resourceGuaranteedMemory (float):    Percentage of allocated CPU resources guaranteed to vApps deployed in
                                    this vdc.
        resourceGuaranteedCPU    (float):    Percentage of allocated memory resources guaranteed to vApps deployed
                                    in this vdc.
        vcpuInMhz            (int):  Specifies the clock frequency, in MegaHertz, for any virtual CPU that is
                                    allocated to a VM.
        isThinProvision      (bool): True to request thin provisioning.
        usesFastProvisioning (bool): True to request fast provisioning
        overCommitAllowed    (bool)   : False to disallow creation of the VDC if the AllocationModel is
                                     AllocationPool or ReservationPool and the ComputeCapacity specified is greater than 
                                     what the backing provider VDC can supply.
        vmDiscoveryEnabled   (bool): True, if discovery of vCenter VMs is enabled for resource pools backing this vdc
        isEnabled             (bool): True, if this vdc is enabled for use by the organization users

vApp:
Purpose: Create a VApp from existing VApp template
Note:
    If customization parameters are provided, it will customize the vm and guest OS, taking some assumptions.

    A general assumption is made by this method that customization parameters are applicable only if there is
    only one vm in the vApp. And, the vm has a single NIC.

    In case of a vApp template having multiple VMs having multiple NICs in any of the VM, none of the optional
    parameters will be considered. vApp template will be instantiated with default settings.
Variable:
    Mandatory:
        orgName            (str):  Name of the organization
        vdcName            (str):  Name of the Organization VDC in which the vApp is to be created.
        vAppName           (str):  Name of the new vApp.
        catalogName        (str):  Name of the catalog.
        templateName       (str):  Name of the vApp template.
    Non Mandatory:
        description         (str):  Description of the new vApp.
        network             (str):  Name of a vdc network. When provided, connects the vm to the network.
        fenceMode          (str):  Fence mode. Possible values are:
                                    pyvcloud.vcd.client.FenceMode.BRIDGED.value and
                                    pyvcloud.vcd.client.FenceMode.NAT_ROUTED.value.
        ipAllocationMode  (str):  ip allocation mode. Acceptable values are `pool`, `dhcp` and `manual`.
        deploy              (bool): If True deploy the vApp after instantiation.
        powerOn            (bool): If True, power on the vApp after instantiation.
        acceptAllEulas    (bool): True, confirms acceptance of all EULAs in a vApp template.
        memory              (int):  Size of memory of the first vm.
        cpu                 (int):  Number of cpus in the first vm.
        diskSize           (int):  Size of the first disk of the first vm.
        password            (int):  Admin password of the guest os on the first vm.
        custScript         (str):  Guest customization to run on the vm.
        vmName             (str):  When provided, sets the name of the vm.
        ipAddress          (str):  When provided, sets the ip_address of the vm.
        hostname            (str):  when provided, sets the hostname of the guest OS.
        storageProfile     (str):  Name of storage profile
        networkAdapterType(str):  One of the values in :
                                    VMXNET,VMXNET2,VMXNET3,E1000,E1000E,VLANCE

deletevApp:
Purpose: To delete VApp
Note: VApps should be deleted before deleting Organization.
Variables:
    Mandatory:
        orgName            (str):  Name of the organization
        vdcName            (str):  Name of the Organization VDC in which the vApp is to be created.
        vAppName           (str):  Name of the new vApp.

deleteOrg:
Purpose: Delete all entities in an organization(except vapp) recursiely.
Variable:
    orgName            (str):  Name of the organization
"""

import sys
import json
import time
import logging
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import FenceMode
from pyvcloud.vcd.system import System
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.platform import Platform
import requests


class Test:
    def __init__(self):
        self.client = None
        self.system = None
        self.data = None
        self.log = None

    def setup(self, data):
        requests.packages.urllib3.disable_warnings()
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename="entity_vcloud.log",
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger()
        self.log.info("------------Initializing JSON File------------")
        self.data = data
        keys = self.data.keys()
        if "login" in self.data.keys():
            self.system_login(self.data["login"])
        else:
            sys.exit(0)
        if "organization" in keys:
            self.create_org(self.data["organization"])
        if "providerVDC" in keys or False:
            self.create_provider_vdc(self.data)
        if "orgVdc" in keys:
            self.create_org_vdc(self.data["orgVdc"])
            self.log.info("log to wait for 60 second for the orgVDC to get created")
            time.sleep(60)
        if "vApp" in keys:
            self.create_vapp_from_template(self.data["vApp"])
        if "deletevApp" in keys:
            self.delete_vapp(self.data["deletevApp"])
        if "deleteOrg" in keys:
            self.delete_org(self.data["deleteOrg"]["orgName"])
        self.log.info("------------Process ended------------")

    def system_login(self, data):
        self.log.info("------------Logging as System user------------")
        keys = data.keys()
        if "hostname" in keys:
            host_name = data["hostname"]
        else:
            self.log.info("Mandatory value hostname not entered: Enter hostname")
            sys.exit(0)
        if "username" in keys:
            user_name = data["username"]
        else:
            self.log.info("Mandatory value username not entered: Enter hostname")
            sys.exit(0)
        if "password" in keys:
            password = data["password"]
        else:
            self.log.info("Mandatory value password not entered: Enter password")
            sys.exit(0)
        try:
            self.client = Client(host_name,
                                 verify_ssl_certs=False,
                                 log_requests=False,
                                 log_headers=False,
                                 log_bodies=False)
            self.client.set_credentials(BasicLoginCredentials(user_name, "System", password))
            self.system = System(self.client, admin_resource=self.client.get_admin())
            self.log.info("Login successful")
        except Exception as exp:
            self.log.info("Exception while logging in. Check credentials")
            raise exp

    def create_org(self, data):
        self.log.info("------------Creating new Organization------------")
        keys = data.keys()
        if "orgName" in keys:
            org_name = data["orgName"]
        else:
            self.log.info("Mandatory value 'orgName' not entered: Enter 'orgName'")
            sys.exit(0)
        if "fullOrgName" in keys:
            full_org_name = data["fullOrgName"]
        else:
            self.log.info("Mandatory value 'fullOrgName' not entered: Enter 'fullOrgName'")
            sys.exit(0)
        if "isEnabled" in keys:
            is_enabled = data["isEnabled"]
        else:
            self.log.info("Value for 'isEnabled' not entered: Default value set to True")
            is_enabled = True
        try:
            try:
                self.client.get_org_by_name(org_name)
                self.log.info("Organization already exists")
                print("Organization already exists")
            except:
                self.system.create_org(org_name=org_name, full_org_name=full_org_name,
                                       is_enabled=is_enabled)
                self.log.info("Orgnization creation successful")
        except Exception as exp:
            self.log.info("Exception while creating organizaiton")
            self.log.info(exp)

    def create_org_vdc(self, data):
        self.log.info("------------Creating new Organization VDC------------")
        try:
            keys = data.keys()
            if "orgName" in keys:
                org_name = data["orgName"]
            else:
                self.log.info("Mandatory value 'orgName' not entered: Enter 'orgName'")
                sys.exit(0)
            if "vdcName" in keys:
                vdc_name = data["vdcName"]
            else:
                self.log.info("Mandatory value 'vdcName' not entered: Enter 'vdcName'")
                sys.exit(0)
            if "providerVDCName" in keys:
                provider_vdc_name = data["providerVDCName"]
            else:
                self.log.info("Mandatory value 'providerVDCName' not entered: Enter 'providerVDCName'")
                sys.exit(0)
            if "networkPoolName" in keys:
                network_pool_name = data["networkPoolName"]
            else:
                self.log.info("Mandatory value 'networkPoolName' not entered: Enter 'networkPoolName'")
                sys.exit(0)
            if "storageProfile" in keys:
                storage_profiles = data["storageProfile"]
            else:
                self.log.info("Mandatory value 'storageProfile' not entered: Enter 'storageProfile'")
                sys.exit(0)
            if "description" in keys:
                description = data["description"]
            else:
                self.log.info("Value for 'description' not entered: Default value set to ''")
                description = ""
            if "allocationModel" in keys:
                allocation_model = data["allocationModel"]
            else:
                self.log.info("Value for 'allocationModel' not entered: Default value set to 'AllocationPool'")
                allocation_model = "AllocationPool"
            if "cpuUnits" in keys:
                cpu_units = data["cpuUnits"]
            else:
                self.log.info("Value for 'cpuUnits' not entered: Default value set to 'MHz'")
                cpu_units = "MHz"
            if "cpuAllocated" in keys:
                cpu_allocated = data["cpuAllocated"]
            else:
                self.log.info("Value for 'cpuAllocated' not entered: Default value set to '1'")
                cpu_allocated = 1
            if "cpuLimit" in keys:
                cpu_limit = data["cpuLimit"]
            else:
                self.log.info("Value for 'cpuLimit' not entered: Default value set to '1'")
                cpu_limit = 1
            if "memUnits" in keys:
                mem_units = data["memUnits"]
            else:
                self.log.info("Value for 'memUnits' not entered: Default value set to 'MB'")
                mem_units = "MB"
            if "memAllocated" in keys:
                mem_allocated = data["memAllocated"]
            else:
                self.log.info("Value for 'memAllocated' not entered: Default value set to '1000'")
                mem_allocated = 1000
            if "memLimit" in keys:
                mem_limit = data["memLimit"]
            else:
                self.log.info("Value for 'memLimit' not entered: Default value set to '0'")
                mem_limit = 0
            if "nicQuota" in keys:
                nic_quota = data["nicQuota"]
            else:
                self.log.info("Value for 'nicQuota' not entered: Default value set to '0'")
                nic_quota = 0
            if "networkQuota" in keys:
                network_quota = data["networkQuota"]
            else:
                self.log.info("Value for 'networkQuota' not entered: Default value set to '1000'")
                network_quota = 1000
            if "vmQuota" in keys:
                vm_quota = data["vmQuota"]
            else:
                self.log.info("Value for 'vmQuota' not entered: Default value set to '100'")
                vm_quota = 100
            if "resourceGuaranteedMemory" in keys:
                resource_guaranteed_memory = data["resourceGuaranteedMemory"]
            else:
                self.log.info("Value for 'resourceGuaranteedMemory' not entered: Default value set to 'None'")
                resource_guaranteed_memory = None
            if "resourceGuaranteedCPU" in keys:
                resource_guaranteed_cpu = data["resourceGuaranteedCPU"]
            else:
                self.log.info("Value for 'resourceGuaranteedCPU' not entered: Default value set to 'None'")
                resource_guaranteed_cpu = None
            if "vcpuInMhz" in keys:
                vcpu_in_mhz = data["vcpuInMhz"]
            else:
                self.log.info("Value for 'vcpuInMhz' not entered: Default value set to 'None'")
                vcpu_in_mhz = None
            if "isThinProvision" in keys:
                is_thin_provision = data["isThinProvision"]
            else:
                self.log.info("Value for 'isThinProvision' not entered: Default value set to 'True'")
                is_thin_provision = True
            if "usesFastProvisioning" in keys:
                uses_fast_provisioning = data["usesFastProvisioning"]
            else:
                self.log.info("Value for 'usesFastProvisioning' not entered: Default value set to 'None'")
                uses_fast_provisioning = None
            if "overCommitAllowed" in keys:
                over_commit_allowed = data["overCommitAllowed"]
            else:
                self.log.info("Value for 'overCommitAllowed' not entered: Default value set to 'None'")
                over_commit_allowed = None
            if "vmDiscoveryEnabled" in keys:
                vm_discovery_enabled = data["vmDiscoveryEnabled"]
            else:
                self.log.info("Value for 'vmDiscoveryEnabled' not entered: Default value set to 'None'")
                vm_discovery_enabled = None
            if "isEnabled" in keys:
                is_enabled = data["isEnabled"]
            else:
                self.log.info("Value for 'isEnabled' not entered: Default value set to 'True'")
                is_enabled = True

            org = None
            try:
                org_record = self.client.get_org_by_name(org_name)
                org = Org(self.client, href=org_record.get("href"))
            except:
                self.log.info("Organization not found")
                return
            elem = org.get_vdc(vdc_name)
            if elem is not None:
                self.log.info("OrgVDC already exists")
            else:

                org.create_org_vdc(vdc_name,
                                   provider_vdc_name,
                                   description,
                                   allocation_model,
                                   cpu_units,
                                   cpu_allocated,
                                   cpu_limit,
                                   mem_units,
                                   mem_allocated,
                                   mem_limit,
                                   nic_quota,
                                   network_quota,
                                   vm_quota,
                                   storage_profiles,
                                   resource_guaranteed_memory,
                                   resource_guaranteed_cpu,
                                   vcpu_in_mhz,
                                   is_thin_provision,
                                   network_pool_name,
                                   uses_fast_provisioning,
                                   over_commit_allowed,
                                   vm_discovery_enabled,
                                   is_enabled)

                org.reload()
                self.log.info("OrgVDC created successfully")
        except Exception as exp:
            self.log.info("Exception while creating Organization VDC")
            self.log.info(exp)

    def create_vapp_from_template(self, data):
        self.log.info("------------Creating new VApp------------")
        try:
            keys = data.keys()
            if "orgName" in keys:
                org_name = data["orgName"]
            else:
                self.log.info("Mandatory value 'orgName' not entered: Enter 'orgName'")
                sys.exit(0)
            if "vdcName" in keys:
                vdc_name = data["vdcName"]
            else:
                self.log.info("Mandatory value 'vdcName' not entered: Enter 'vdcName'")
                sys.exit(0)
            if "vAppName" in keys:
                vapp_name = data["vAppName"]
            else:
                self.log.info("Mandatory value 'vAppName' not entered: Enter 'vAppName'")
                sys.exit(0)
            if "catalogName" in keys:
                catalog_name = data["catalogName"]
            else:
                self.log.info("Mandatory value 'catalogName' not entered: Enter 'catalogName'")
                sys.exit(0)
            if "templateName" in keys:
                template_name = data["templateName"]
            else:
                self.log.info("Mandatory value 'templateName' not entered: Enter 'templateName'")
                sys.exit(0)
            if "description" in keys:
                description = data["description"]
            else:
                self.log.info("Value for 'description' not entered: Default value set to ''")
                description = ""
            if "network" in keys:
                network = data["network"]
            else:
                self.log.info("Value for 'network' not entered: Default value set to 'None'")
                network = None
            if "fenceMode" in keys:
                fence_mode = data["fenceMode"]
            else:
                self.log.info("Value for 'fenceMode' not entered: Default value set to 'FenceMode.BRIDGED.value'")
                fence_mode = FenceMode.BRIDGED.value
            if "ipAllocationMode" in keys:
                ip_allocation_mode = data["ipAllocationMode"]
            else:
                self.log.info("Value for 'ipAllocationMode' not entered: Default value set to 'dhcp'")
                ip_allocation_mode = "dhcp"
            if "deploy" in keys:
                deploy = data["deploy"]
            else:
                self.log.info("Value for 'deploy' not entered: Default value set to 'True'")
                deploy = True
            if "powerOn" in keys:
                power_on = data["powerOn"]
            else:
                self.log.info("Value for 'powerOn' not entered: Default value set to 'True'")
                power_on = True
            if "acceptAllEulas" in keys:
                accept_all_eulas = data["acceptAllEulas"]
            else:
                self.log.info("Value for 'acceptAllEulas' not entered: Default value set to 'False'")
                accept_all_eulas = False
            if "memory" in keys:
                memory = data["memory"]
            else:
                self.log.info("Value for 'memory' not entered: Default value set to 'None'")
                memory = None
            if "cpu" in keys:
                cpu = data["cpu"]
            else:
                self.log.info("Value for 'cpu' not entered: Default value set to 'None'")
                cpu = None
            if "diskSize" in keys:
                disk_size = data["diskSize"]
            else:
                self.log.info("Value for 'diskSize' not entered: Default value set to 'None'")
                disk_size = None
            if "password" in keys:
                password = data["password"]
            else:
                self.log.info("Value for 'password' not entered: Default value set to 'None'")
                password = None
            if "custScript" in keys:
                cust_script = data["custScript"]
            else:
                self.log.info("Value for 'description' not entered: Default value set to ''")
                cust_script = None
            if "vmName" in keys:
                vm_name = data['vmname']
            else:
                self.log.info("Value for 'vmName' not entered: Default value set to 'None'")
                vm_name = None
            if "hostname" in keys:
                hostname = data['hostname']
            else:
                self.log.info("Value for 'hostname' not entered: Default value set to 'None'")
                hostname = None
            if "ipAddress" in keys:
                ip_address = data["ipAddress"]
            else:
                self.log.info("Value for 'ipAddress' not entered: Default value set to 'None'")
                ip_address = None
            if "storageProfile" in keys:
                storage_profile = data["storageProfile"]
            else:
                self.log.info("Value for 'storageProfile' not entered: Default value set to 'None'")
                storage_profile = None
            if "networkAdapterType" in keys:
                network_adapter_type = data["networkAdapterType"]
            else:
                self.log.info("Value for 'networkAdapterType' not entered: Default value set to 'None'")
                network_adapter_type = None

            org = None
            vdc = None
            try:
                org_record = self.client.get_org_by_name(org_name)
                if org_record is None:
                    self.log.info("Organization doesnot exist")
                    sys.exit(0)
                org = Org(self.client, href=org_record.get("href"))
                vdc_resource = org.get_vdc(vdc_name)
                if vdc_resource is None:
                    self.log.info("Organization VDC doesnot exist")
                    sys.exit(0)
                vdc = VDC(self.client, resource=vdc_resource)
                vapp = None
                try:
                    vapp = vdc.get_vapp(vapp_name)
                except:
                    self.log.info("VApp name is available")
                if vapp is not None:
                    self.log.info("Vapp with given name already exists")
                    raise Exception
                vdc.instantiate_vapp(vapp_name,
                                     catalog_name,
                                     template_name,
                                     description,
                                     network,
                                     fence_mode,
                                     ip_allocation_mode,
                                     deploy,
                                     power_on,
                                     accept_all_eulas,
                                     memory,
                                     cpu,
                                     disk_size,
                                     password,
                                     cust_script,
                                     vm_name,
                                     hostname,
                                     ip_address,
                                     storage_profile,
                                     network_adapter_type)
                self.log.info("VApp creation successful")
            except Exception as exp:
                self.log.info(exp)

        except Exception as exp:
            self.log.info(exp)

    def create_provider_vdc(self, data):
        self.log.info("------------Creating new Organization PVDC ------------")
        try:
            keys = data.keys()
            if "vimServerName" in keys:
                vim_server_name = data["vimServerName"]
            else:
                self.log.info("Mandatory value 'vimServerName' not entered: Enter 'vimServerName'")
                sys.exit(0)
            if "resourcePoolNames" in keys:
                resource_pool_names = data["resourcePoolNames"]
            else:
                self.log.info("Mandatory value 'resourcePoolNames' not entered: Enter 'resourcePoolNames'")
                sys.exit(0)
            if "storageProfiles" in keys:
                storage_profiles = data['storageProfiles']
            else:
                self.log.info("Mandatory value 'storageProfiles' not entered: Enter 'storageProfiles'")
                sys.exit(0)
            if "pvdcName" in keys:
                pvdc_name = data["pvdcName"]
            else:
                self.log.info("Mandatory value 'pvdcName' not entered: Enter 'pvdcName'")
                sys.exit(0)
            if "isEnabled" in keys:
                is_enabled = data["isEnabled"]
            else:
                self.log.info("Value for 'isEnabled' not entered: Default value set to 'True'")
                is_enabled = True
            if 'description' in keys:
                description = data["description"]
            else:
                self.log.info("Value for 'description' not entered: Default value set to ''")
                description = ""
            if "highestHwVers" in keys:
                highest_hw_vers = data["highestHwVers"]
            else:
                self.log.info("Value for 'highestHwVers' not entered: Default value set to 'None'")
                highest_hw_vers = None
            if "vxlanNetworkPool" in keys:
                vxlan_network_pool = data["vxlanNetworkPool"]
            else:
                self.log.info("Value for 'vxlanNetworkPool' not entered: Default value set to 'None'")
                vxlan_network_pool = None
            if "nsxtManagerName" in keys:
                nsxt_manager_name = data["nsxtManagerName"]
            else:
                self.log.info("Value for 'nsxtManagerName' not entered: Default value set to 'None'")
                nsxt_manager_name = None
            platform = Platform(self.client)

            platform.create_provider_vdc(vim_server_name,
                                         resource_pool_names,
                                         storage_profiles,
                                         pvdc_name,
                                         is_enabled,
                                         description,
                                         highest_hw_vers,
                                         vxlan_network_pool,
                                         nsxt_manager_name)
            self.log.info("PVDC creation successful")
        except Exception as exp:
            self.log.info("Exception while creating Provider VDC")
            self.log.info(exp)

    def delete_vapp(self, data):
        try:
            keys = data.keys()
            if "orgName" in keys:
                org_name = data["orgName"]
            else:
                self.log.info("Mandatory value 'orgName' not entered: Enter 'orgName'")
                sys.exit(0)
            if "vdcName" in keys:
                vdc_name = data["vdcName"]
            else:
                self.log.info("Mandatory value 'vdcName' not entered: Enter 'vdcName'")
                sys.exit(0)
            if "vAppName" in keys:
                vapp_name = data["vAppName"]
            else:
                self.log.info("Mandatory value 'vAppName' not entered: Enter 'vAppName'")
                sys.exit(0)
            org = None
            vdc = None
            try:
                org_record = self.client.get_org_by_name(org_name)
                if org_record is None:
                    self.log.info("Given Organization does not exist")
                    sys.exit(0)
                org = Org(self.client, href=org_record.get("href"))
                vdc_resource = org.get_vdc(vdc_name)
                if vdc_resource is None:
                    self.log.info("Given Organization VDC doesnt exists")
                    sys.exit(0)
                vdc = VDC(self.client, resource=vdc_resource)
                vapp = None
                try:
                    vapp = vdc.get_vapp(vapp_name)
                    vdc.delete_vapp(vapp_name, force=True)
                    self.log.info("vapp deleted successfully")
                except:
                    self.log.info("Given VApp does not exists")
            except Exception as exp:
                raise exp
        except Exception as exp:
            self.log.info(exp)

    def delete_org(self, org_name):
        try:
            self.client.get_org_by_name(org_name)
            self.system.delete_org(org_name, force=True, recursive=True)
            self.log.info("Organization deleted successfully")
        except:
            self.log.info("Given organization does not exists")


if len(sys.argv) > 1:
    json_input = str(sys.argv[1])
    with open(json_input) as json_file:
        data = json.load(json_file)
        ob = Test()
        ob.setup(data)
else:
    print("Pass JSON file as argument")
