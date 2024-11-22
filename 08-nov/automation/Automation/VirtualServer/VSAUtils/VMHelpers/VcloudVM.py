# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Vcloud vm"""

import json
import time

import xmltodict
import requests
from AutomationUtils import logger
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils.VirtualServerConstants import VCLOUD_API_HEADER, vcloud_vm_status, VCLOUD_API_HEADER_JSON


class VMwareDisk:
    """
    Data class for storing parameters related to a hard disk attached to a vCloud VM
    """
    def __init__(self, descriptor):
        """
            Initialize VMwareDisk object.

            Arguments:
                descriptor      (RASDItem+json)
        """
        self.__host_resources = descriptor['hostResource'][0]['otherAttributes']
        self.parent = descriptor["parent"]["value"]
        self.address_on_parent = descriptor["addressOnParent"]["value"]
        self.type = descriptor.get("resourceType", {}).get("value", None)
        self.description = descriptor["description"]["value"]
        self.element_name = descriptor["elementName"]["value"]
        self.instance_id = descriptor["instanceID"]["value"]
        self.capacity = self._get_host_resource('capacity')
        self.storage_profile = self._get_host_resource('storageProfileHref')
        self.bus_subtype = self._get_host_resource('busSubType')
        self._config = None

    @property
    def config(self):
        """
        Get configuration of the disk within the VM in the form `Controller (Bus : Type)`
        """
        if not self._config:
            _key = int(self.instance_id)
            if _key // 32000:
                _ctr, _id = int(_key % 32000 / 15), _key % 32000 % 15
                self._config = 'NVME ({}:{})'.format(_ctr, _id)
            elif _key // 16000:
                _ctr, _id = int(_key % 16000 / 30), _key % 16000 % 30
                self._config = 'SATA ({}:{})'.format(_ctr, _id)
            elif _key // 2000:
                _ctr, _id = int(_key % 2000 / 16), _key % 2000 % 16
                self._config = 'SCSI ({}:{})'.format(_ctr, _id)
        
        return self._config

    def _get_host_resource(self, resource):
        """
            Internal method for fetching host resources for a disk.

            Arguments:
                resource        (str)   -       Resource name
            Returns:
                (obj)                   -       Return host resouce as stored in RASDItem
        """
        return self.__host_resources.get("{http://www.vmware.com/vcloud/v1.5}" + resource, "")

    def __eq__(self, other):
        "Compare capacity and busstype for two VMwareDisk objects"

        return self.capacity == other.capacity and self.bus_subtype == other.bus_subtype

    def __str__(self):
        """
        Return string representation
        """
        return "InstanceID={} Parent={} AddressOnParent={} capacity={: ^8} BusType={: ^15} storage_profile={} " \
                .format(self.instance_id, self.parent, self.address_on_parent, self.capacity,
                        self.bus_subtype, self.storage_profile["name"])


class VMwareDiskController:
    """
        Data class for storing parameters related to Disk Controllers attached to a vCloud VM
    """
    def __init__(self, descriptor):
        """
            Initialize a VMwareDiskController object

            Arguments:
                descriptor      (RASDItem+json)
        """
        self.address = descriptor["address"]["value"]
        self.instance_id = descriptor["instanceID"]["value"]
        self.resource_subtype = descriptor.get("resourceSubType", {}).get("value", None) if descriptor['resourceSubType'] != None else ""
        self.resource_type = descriptor.get("resourceType", {}).get("value", "")
        self.description = descriptor["description"]["value"]
        self.element_name = descriptor["elementName"]["value"]
        self._type = None
    
    @property
    def type(self):
        """
        Retrieve type of controller to match with `pyvmomi` class names for virtual hardware devices.
        """
        if not self._type:
            controller_map = {
                "buslogic": "VirtualBusLogicController",
                "lsilogic": "VirtualLsiLogicController",
                "lsilogicsas": "VirtualLsiLogicSASController", 
                "VirtualSCSI": "ParaVirtualSCSIController",
                "vmware.sata.ahci": "VirtualSATAController"
            }
            if self.resource_subtype in controller_map.keys():
                self._type = controller_map[self.resource_subtype]

            if not self.resource_subtype:
                self._type = "VirtualIDEController"

        return self._type

    def __str__(self):
        """
        Return string representation.
        """
        return "InstanceID={} Address={} ElementName={} ResourceType={} ResourceSubType={}" \
                .format(self.instance_id, self.address, self.element_name, self.resource_type,
                        self.resource_subtype)


class VcloudVM(HypervisorVM):
    """
        This is the main file for all Vcloud VM operations
    """

    def __init__(self, hvobj, vm_name):
        """
        Initialization of Vcloud VM properties

        Args:

            hvobj           (obj):  Hypervisor Object

            vm_name         (str):  Name of the VM

        """

        super(VcloudVM, self).__init__(hvobj, vm_name)

        self.url = self.hvobj.url
        self.username = self.hvobj.username
        self.password = self.hvobj.password
        self._headers = {}
        self._json_headers = {}
        self.vm_list = self.hvobj.vm_list
        self.vapp_name = self.hvobj.vapp_name
        self.vm_name = vm_name
        self.href = self.vm_list[self.vm_name]
        self.memory = 0
        self.no_of_cpu = 0
        self.disk_count = 0
        self.ip_address = None
        self.network_adapter = None
        self.vcloud_auth_token = None
        self._basic_props_initialized = False
        self.network_name = None
        self.guid = None
        self.subnet_id = None
        self.vm_state = None
        self._vm_info = {}
        self.disk_controller_map = {}
        self.disk_config = {}
        self.nic = []
        self.attached_disks = []
        self.disk_dict = None
        self._disk_list = None
        # self.storage_policy=None
        # this is getting mixed up with cv storage policy. needs rename/new attr.
        self.storage_profile = None
        self._controller_list = []
        self.vcenter_vm = None
        self.vcenter_host = None
        self._get_vm_info()
        self.update_vm_info(prop='All')
        self.vm_guest_os = None
        self.is_standalone_vm = self.is_standalone
        self.owner_name = self.get_owner_name()

    def vcloud_request(self, prop, headers='xml', **kwargs):
        """
        Performs an API call based on the endpoint requested, returns json response.

        Args:
            prop        str          -  Property with endpoint in the endpoint map. Otherwise "[METHOD] [URL]"
            headers     'xml'/'json' -  Headers for vCloud calls
            **kwargs    object       -  for body any additional request params
        """
        method_map = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete
        }

        property_endpoint_map = {
            "vm_info": "GET {}",
            "delete_vm": "DELETE {}?force=true",
            "disks": "GET {}/virtualHardwareSection/disks",
            "disks:reconfigure": "PUT {}/virtualHardwareSection/disks",
            "network": "GET {}/networkConnectionSection",
            "cpu": "GET {}/virtualHardwareSection/cpu",
            "memory": "GET {}/virtualHardwareSection/memory",
            "power:on": "POST {}/power/action/powerOn",
            "power:off": "POST {}/power/action/powerOff"
        }

        media_types = {
            'disks:reconfigure': 'application/vnd.vmware.vcloud.rasditemslist+json;version=39.0'
        }

        if prop in property_endpoint_map.keys():
            method, url = property_endpoint_map[prop].format(self.href).split(" ")
        else:
            method, url = prop.split(" ")

        try:

            if headers == 'json':
                request_headers = self.json_headers
            else:
                request_headers = self.headers

            if prop in media_types:
                request_headers.update({"Content-Type": media_types[prop]})

            if method == 'POST':
                response = method_map[method](url, headers=request_headers,
                                              auth=(self.user_name, self.password),
                                              verify=False, **kwargs)

            else:
                response = method_map[method](url, headers=request_headers,
                                              verify=False, **kwargs)

            if headers == 'xml':
                data = xmltodict.parse(response.content)
                content = json.dumps(data)
                data = json.loads(content)
            else:
                data = json.loads(response.content)

            if response.status_code in [200, 202]:
                return data
            else:
                raise Exception("vCloud API Call {} returned with non 200 Status Code"
                                "{}"
                                "{}".format(prop, response.status_code, str(response.raw)))

        except Exception as err:
            raise Exception("Unable to make vCloud API call:\n{}".format(str(err)))

    @property
    def vm_info(self):
        """
            It is used to fetch VM info. This is read only property
        """
        if self._vm_info[self.vm_name] == {}:
            self._get_vm_info()
        return self._vm_info[self.vm_name]

    @vm_info.setter
    def vm_info(self, value):
        """
             This is to set vmname for VM info
        """
        self._vm_info[self.vm_name] = value

    def _get_headers(self, accept=None):
        self.vcloud_auth_token = self.hvobj.check_for_login_validity()

        if accept == 'json':
            return VCLOUD_API_HEADER_JSON

        return VCLOUD_API_HEADER

    @property
    def headers(self):
        """
        provide the default headers required
        """
        self.vcloud_auth_token = self.hvobj.check_for_login_validity()
        self._headers = self._get_headers()
        self._headers.update({"Authorization": f"Bearer {self.vcloud_auth_token}"})
        return self._headers

    @property
    def json_headers(self):
        """
        provide the json header
        """
        self.vcloud_auth_token = self.hvobj.check_for_login_validity()
        self._json_headers = self._get_headers(accept='json')
        self._json_headers.update({"Authorization": f"Bearer {self.vcloud_auth_token}"})
        return self._json_headers

    def get_drive_list(self):
        """
        Returns the drive list for the VM
        """
        try:
            super(VcloudVM, self).get_drive_list()
            del self._drives['E']
            return True

        except Exception as err:
            self.log.exception(
                "An Exception Occurred in Getting the Volume Info for the VM ".format(err))
            return False

    def _get_vm_info(self):
        """
        Get all VM information

        Raises:
            Exception:
                if failed to get information about VM
        """
        try:
            self.log.info("VM information :: Getting all information of VM %s" % self.vm_name)

            data = self.vcloud_request("vm_info")
            self._vm_info[self.vm_name] = data

            self.log.info("vm_info %s of VM %s is successfully obtained " % (data, self.vm_name))

        except Exception as err:
            self.log.info("There was No VM in Name %s , please check the VM name" % self.vm_name)
            self._vm_info = False
            raise Exception(err)

    def get_vcenter_info(self):
        """
        Get information about host vCenter and Name of entity on vSphere
        """

        vm_info_json = self.vcloud_request('vm_info', 'json')

        # Set vCenter host name
        self.vcenter_host = vm_info_json['vCloudExtension'][0]['any'][0]['hostVimObjectRef']['vimServerRef']['name']

        # Set vCenter VM name using backing information of hw files.
        virtual_hw_section = [i for i in vm_info_json['section'] if i['_type'] == 'VirtualHardwareSectionType' ]
        nvram_name = [i for i in virtual_hw_section[0]['any'] if i['_type'] == 'ExtraConfigType' and i['key'] == 'nvram' ]

        self.vcenter_vm = nvram_name[0]['value'].split('.')[0]

    def get_vm_guid(self):
        """
        gets the GUID of VM

        Raises:
            Exception:
                If the guid cannot be retrieved
        """
        try:
            self.log.info("Getting the guid information for VM %s" % self.vm_name)
            data = self._vm_info
            self.guid = data[self.vm_name]['Vm']['@id']

        except Exception as err:
            self.log.exception("Exception in get_vm_guid")
            raise Exception(err)

    def get_storage_profile(self):

        try:
            self.log.info("Getting the os info for VM %s" % self.vm_name)
            data = self.vm_info
            storage_profile = data['Vm']['StorageProfile']['@name']
            self.log.info("storage_profile of the VM is %s" % storage_profile)
            setattr(self, "storage_profile", storage_profile)
            self.log.info("storage_profile is : %s" % self.storage_profile)

        except Exception as err:
            self.log.exception("Exception in Get Storage_policy")
            raise Exception(err)

    def get_disk_configuration(self):
        """
        Parses disk configuration for the VM

        Populates:
            disk_controller_map
            disk_config.

        Raises:
            Exception:
                Failure to retrieve/parse disk information.
        """

        try:
            content = self.vcloud_request("disks", "json")

            self.disk_count = 0

            for item in content['item']:
                if not item['addressOnParent']:
                    # create VMWare Controller obj, add it to dict
                    self.disk_controller_map[item["instanceID"]["value"]] = VMwareDiskController(item)

            for item in content["item"]:
                if item['addressOnParent'] and item["instanceID"]:
                    # create VMware Disk object, add it to dict.
                    new_disk = VMwareDisk(item)
                    new_disk.storage_profile = self.hvobj.storage_profile_info(new_disk.storage_profile)
                    self.disk_config[item["instanceID"]["value"]] = new_disk
                    self.disk_count += 1

            self.log.info("Successfully retrieved disk configuration for the VM. \n"
                          "Controller Config:\n{}\n"
                          "Hard Disks Config:\n{}".format("\n".join([str(i) for i in self.disk_controller_map.values()]),
                                                          "\n".join([str(i) for i in self.disk_config.values()])))
        except Exception as exp:
            self.log.info("Unable to set disk configuration for VM. - {}".format(exp))
            raise Exception(exp)

    def get_disk_info(self):
        """
        Get disk properties of both OS and data disks of VM

        Raises:
            Exception:
                    if failed to disk information of VM
        """
        try:
            self.log.info("VM information :: Getting all Disk information of VM %s" % self.vm_name)
            self.get_disk_configuration()
            data = self.vcloud_request("disks")
            self.disk_dict = data['RasdItemsList']['Item']
        except Exception as err:
            self.log.exception(f"No disks found for VM {self.vm_name}")

    def get_status_of_vm(self):
        """
        Get state of VM. For possible return values, check VirtualServerConstants.vcloud_vm_status

        Raises:
            Exception:
                    if failed to get status of VM
        """
        try:
            self.log.info("Get the Status of VM %s" % self.vm_name)
            data = self._vm_info
            self.vm_state = data[self.vm_name]['Vm']['@status']
            self.log.info("VM status: {}".format(vcloud_vm_status(self.vm_state)))

        except Exception as err:
            self.log.exception("Exception in getStatusofVM")
            raise Exception(err)

    def get_os_type(self):
        """
        Update the OS Type of VM

        Raises:
            Exception:
                    if failed to find OS type of VM
        """

        try:
            self.log.info("Getting the os info for VM %s" % self.vm_name)
            data = self.vm_info
            os_info = data['Vm']['ovf:OperatingSystemSection']['ovf:Description']
            if 'Windows' in os_info:
                guest_os = 'Windows'
            else:
                guest_os = 'Linux'
            self.log.info("os disk detaisl of the VM is %s" % guest_os)
            setattr(self, "guest_os", guest_os)
            self.log.info("OS type is : %s" % self.guest_os)

        except Exception as err:
            self.log.exception("Exception in GetOSType")
            raise Exception(err)

    def get_ip_address(self):
        """
        Get the Ip address and nic of the VM

        Raises:
            Exception:
                    if failed to get IP address of VM
        """
        try:
            # Power on vm and wait for IP to be generated
            if self.vm_state != '4':
                self.log.info("VM {} is not powered on. Powering on VM"
                              .format(self.vm_name))
                self.power_on()

            tries = 0
            while tries < 3:
                self.log.info("Get VM IP details and nic of %s" % self.vm_name)

                data = self.vcloud_request('network', headers='json')

                data = data['networkConnection'][0]

                if 'ipAddress' in data:
                    break

                self.log.info('IP Address not found, waiting 60 seconds')
                time.sleep(60)
                tries += 1

                if tries == 3:
                    raise Exception('Failed to get IP and NIC details for VM {}'.format(self.vm_name))
            self.ip_address = data['ipAddress']
            self.network_name = data['network']
            self.log.info("Ip of vm %s", self.ip_address)
            self.log.info("Network Name of vm %s", self.network_name)
            self.network_adapter = data['networkAdapterType']
            self.log.info("Network Adapter of vm %s", self.network_adapter)

            setattr(self, "host_name", self.network_adapter)
            setattr(self, "ip", self.ip_address)
        except Exception as err:
            self.log.exception("Exception in get_vm_ip_address")
            raise Exception(err)

    def get_cores(self):
        """
        Get number of CPU of VM

        Raises:
            Exception:
                    if failed to get CPU of VM
        """

        try:
            data = self.vcloud_request("cpu", "json")
            self.no_of_cpu = int(data['virtualQuantity']['value'])
        except Exception as err:
            self.log.exception("Exception in get_cores")
            raise Exception(err)

    def get_memory_info(self):
        """
        Get memory of VM

        Raises:
            Exception:
                    if failed to get memory information of VM
        """

        try:
            data = self.vcloud_request("memory", "json")
            self.memory = int(data['virtualQuantity']['value']) / 1024

        except Exception as err:
            self.log.exception("Exception in get_memory_info")
            raise Exception(err)

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
        """
         fetches all the properties of the VM

        Args:
            prop            'Basic' | 'All'     'Basic' - Gets only GUID, Disk Information, VM Status, Storage Profile and IP Address
                                                'All'   - Gets OS, Core, and Memory information as well. Sets VMGuestOS for creating OS Object

            os_info         boolean              TBD
            force_update    boolean              Refresh properties even if properties are initialized.

         Raises:
            Exception:
                 if failed to get all the properties of the VM
         """
        try:
            if self.vm_info:
                if not self._basic_props_initialized or force_update:
                    self.get_vm_guid()
                    self.get_vcenter_info()
                    self.get_disk_info()
                    self.get_status_of_vm()
                    self.get_storage_profile()
                    self.get_ip_address()
                    self._basic_props_initialized = True

                if prop == 'All':
                    self.get_os_type()
                    self.get_cores()
                    self.get_memory_info()
                    self.vm_guest_os = self.guest_os
                    self.get_drive_list()
                elif hasattr(self, prop):
                    return getattr(self, prop, None)

            else:
                self.log.info("VM info was not collected for this VM")
        except Exception as err:
            self.log.exception("Failed to Get  the VM Properties of the VM")
            raise Exception(err)

    def power_on(self):
        """
        Power on a vCloud VM
        """
        self._change_state('on')

    def power_off(self):
        """
        Power off a vCloud VM
        """
        self._change_state('off')

    def _change_state(self, operation):
        """
        Change state of VM.

        Args:
            operation   on | off    --  Power on or power off a VM

        Exception:
            When state change fails.
        """

        # [<api_endpoint>, <desired state>]
        operation_map = {'on': ['power:on', '4'], 'off': ['power:off', '8']}

        action, requested_state = operation_map[operation]

        try:
            if self.vm_state == requested_state:
                self.log.info("VM {} is already in desired state: {}",
                              format(self.vm_name, vcloud_vm_status(self.vm_state)))
                return

            self.log.info("Performing Power Operation '{}' on VM {}".format(action, self.vm_name))

            _data = self.vcloud_request(action)
            self.get_status_of_vm()

        except Exception as exp:
            raise Exception("Exception in Changing State: {}".format(str(exp)))

    def delete_disk(self, instance_ids=[]):
        """
        Deletes disks from the VM
        """
        try:
            if not instance_ids:
                instance_ids = self.attached_disks

            content = self.vcloud_request('disks', headers='json')

            deletion_disks = []

            for idx, disk in enumerate(content['item']):
                if (disk.instance_id if isinstance(disk, VMwareDisk) else disk['instanceID']['value']) in instance_ids:
                    deletion_disks.append(idx)

            for ix in sorted(deletion_disks, reverse=True):
                content['item'].pop(ix)

            _content = self.vcloud_request('disks:reconfigure', headers='json', data=content)
        except Exception as exp:
            self.log.exception("Error deleting disks from VM {}".format(str(exp)))

    def delete_vm(self):
        """
        Delete the VM.

        return:
                True - when Delete is successful

        Exception:
                When Delete failed

        """
        try:
            self.log.info("Deleting the vm {}".format(self.vm_name))
            response = requests.delete(self.href + "?force=true", headers=self.headers,
                                       auth=(self.user_name, self.password), verify=False)
            if response.status_code == 202:
                self.log.info("Deleted the VM")
        except Exception as exp:
            raise Exception("Exception in Deletion:" + str(exp))

    def clean_up(self):
        """
        Clean up the VM resources post restore

        Raises:
             Exception:
                If unable to clean up VM and its resources

        """
        self.log.info("Deleting VMs/Instances after restore")
        self.delete_vm()

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options=None, **kwargs):
            if type(vmobj) == VcloudVM:
                self.vm = vmobj
                self.vm_name = vmobj.vm_name
            else:
                self.vm = vmobj.vm
                self.vm_name = vmobj.vm.vm_name

            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()
        def __eq__(self, other):
            """ Compares the source vm and restored vm """
            try:
                if not self.validate_network(self.vm, other.vm, self.vm_restore_options):
                    raise Exception("Network configuration mismatch")
                if not self.validate_storage_profile(self.vm, other.vm, self.vm_restore_options ):
                    raise Exception("Storage profile mismatch")
                if not self.validate_vm_properties(self.vm, other.vm):
                    raise Exception("VM properties mismatch")
                if not self.validate_standalone(self.vm, other.vm, self.vm_restore_options):
                    raise Exception("Standalone restore failed")
                if not self.validate_owner(self.vm, other.vm, self.vm_restore_options):
                    raise Exception("Owner mismatch")
                self.log.info("Validation successful")
                return True
            except Exception as exp:
                self.log.exception("Exception in VM Validation")
                raise Exception("Exception in VM Validation: " + str(exp))

        def validate_network(self, source_vm, dest_vm, restore_options):
            """
            Validates if the destination VMs have correct network based on the restore options.
            If network not passed in restore options, compares with source VM network value.

            Args:
             source_vm (object): The source VM object.
             dest_vm (object): The destination VM object.
             restore_options (object): The restore options object containing information of restored VM.

            Returns:
              bool: True if the validation passes, False otherwise.
            """
            if not restore_options.destination_network:
                return source_vm.network_name == dest_vm.network_name
            else:
                return restore_options.destination_network == dest_vm.network_name

        def validate_storage_profile(self, source_vm, dest_vm, restore_options):
            """
             Validates if the destination VMs have correct storage profile based on the restore options.
             If storage profile not passed in restore options, compares with source VM storage profile value
            Args:
             source_vm (object): The source VM object.
             dest_vm (object): The destination VM object.

            Returns:
              bool: True if the validation passes, False otherwise.
            """
            if not restore_options.storage_profile:
                return source_vm.storage_profile == dest_vm.storage_profile
            else:
                return restore_options.storage_profile == dest_vm.storage_profile

        def validate_vm_properties(self, source_vm, dest_vm):
            """
            Validates VM properties like CPU, memory, of destination VM are same as source VM.

            Args:
             source_vm (object): The source VM object.
             dest_vm (object): The destination VM object.

            Returns:
              bool: True if the validation passes, False otherwise.
            """
            return (source_vm.no_of_cpu == dest_vm.no_of_cpu and
                    source_vm.memory == dest_vm.memory and
                    source_vm.vm_state == dest_vm.vm_state)

        def validate_standalone(self, source_vm, dest_vm, restore_options):
            """
            Validates if the destination VMs are standalone based on the restore options.

            Args:
             source_vm (object): The source VM object.
             dest_vm (object): The destination VM object.
             restore_options (object): The restore options object containing information of restored VM.

            Returns:
               bool: True if the validation passes, False otherwise.
            """
            if restore_options.standalone:
                return dest_vm.is_standalone_vm
            elif source_vm.is_standalone_vm:
                return source_vm.is_standalone_vm == dest_vm.is_standalone_vm
            else:
                self.log.info("standalone validation not needed")
                return True

        def validate_owner(self, source_vm, dest_vm, restore_options):
            """
            Validates if the destination VMs have correct owner based on the restore options.
            If Owner not passed in restore options, compares with source VM Owner value.

            Args:
             source_vm (object): The source VM object.
             dest_vm (object): The destination VM object.
             restore_options (object): The restore options object containing information of restored VM.

            Returns:
              bool: True if the validation passes, False otherwise.
            """
            if restore_options.owner:
                self.log.info(f"The destination VM owner is: {dest_vm.owner_name}")
                return restore_options.owner == dest_vm.owner_name
            else:
                self.log.info(f"The destination VM owner is: {dest_vm.owner_name}")
                return source_vm.owner_name == dest_vm.owner_name

    @property
    def is_standalone(self):
        """
        Checks if a VM is standalone

        Function checks if a virtual machine (VM) is standalone or not.
        A VM is considered standalone if it is not part of a vApp.

        Raises:
            Exception: If an error occurs while trying to determine if the VM is standalone.

        Returns:
            bool: True if the VM is standalone, False otherwise.
        """
        try:
            links = self.vm_info.get('Vm', {}).get('Link', [])
            parent_vapp_url = next((link['@href'] for link in links if link.get('@rel') == 'up'), None)

            if not parent_vapp_url:
                self.log.error("The URL for the parent vApp could not be found.")
                return False

            parent_vapp_data = self.vcloud_request(prop='GET {}'.format(parent_vapp_url), headers='json')

            auto_nature = parent_vapp_data.get('autoNature', False)

            return auto_nature
        except Exception as e:
            self.log.exception(f"An exception occurred while trying to determine if the VM is standalone: {e}")

    def get_owner_name(self):
        """
       Function retrieves the name of the owner of a virtual machine (VM).

       Raises:
          Exception: If an error occurs while trying to retrieve the owner's name.

       Returns:
          str: The name of the VM's owner. None if the owner's name cannot be found.
       """
        try:
            """ Fetch the parent vApp URL """
            links = self.vm_info.get('Vm', {}).get('Link', [])
            parent_vapp_url = next((link['@href'] for link in links if link.get('@rel') == 'up'), None)

            if not parent_vapp_url:
                self.log.error("The URL for the parent vApp could not be found.")
                return None

            parent_vapp_data = self.vcloud_request(prop='GET {}'.format(parent_vapp_url), headers='json')

            """ Retrieve owner data from parent vApp data """
            owner_data = parent_vapp_data.get('owner', {})
            user_data = owner_data.get('user', {})
            owner_name = user_data.get('name')

            if not owner_name:
                self.log.error("The owner's name could not be found.")
                return None
            return owner_name

        except Exception as e:
            self.log.exception(f"An exception occurred while trying to retrieve the owner's name: {e}")
            raise Exception(e)