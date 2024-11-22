# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for OCI vm"""

import time
from AutomationUtils import machine
from AutomationUtils import logger
from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from VirtualServer.VSAUtils import VirtualServerUtils


class OciVM(HypervisorVM):
    """
    This is the main file for all OCI VM operations
    Automation Requirements:
    1.) ICMP traffic needs to be enabled between OCI machine and OCI and testlab machines.
    2.) TCP must be enabled from OCI machines to Testlab machines - For accessing Admin Console
    VMware to OCI conversion
    1.) For conversion we need to have controller in the same subnet as that of restored VM
    2.) To acess Vm in Vcenter for conversion need to enable port no 22 443 and 5985
    """

    def __init__(self, hvobj, vm_name):
        """
        Initialization of OCI vm properties

        Args:
            hvobj               (obj):  Hypervisor Object

            vm_name             (str):  Name of the VM
        """

        super(OciVM, self).__init__(hvobj, vm_name)
        self.oci_config = hvobj.oci_config
        self.server_host_name = hvobj.server_host_name
        self.instance_type = hvobj.instance_type
        self.vm_name = vm_name
        self.vm_info = None
        self._basic_props_initialized = False
        self._all_vm_properties_initialized = False
        self.ip = None
        self.guest_os = None
        self.no_of_cpu = None
        self.memory = None
        self.disk_count = None
        self.instance_id = None
        self.availability_domain = None
        self.region = None
        self.compartment_name = None
        self.compartment_id = None
        self.shape = None
        self.image_id = None
        self.vcn = None
        self.subnet = None
        self.compartment_path = None
        self.vnic_info = dict()
        self.subnet_info = dict()
        self.vcn_details = dict()
        self.boot_volume_info = dict()
        self.block_volume_info = dict()
        self.instance_tags = dict()
        self.disk_dict = dict()
        self.update_vm_info()

    class VmValidation(object):
        def __init__(self, VmValidation_obj, vm_restore_options=None, backup_option=None):
            self.vm = VmValidation_obj.vm
            self.vm_name = self.vm.vm_name
            self.hvobj = self.vm.hvobj
            self.vm_restore_options_obj = vm_restore_options
            self.restore_validation_options = self.vm_restore_options_obj.restore_validation_options
            self._do_restore_validation_options = self.vm_restore_options_obj._do_restore_validation_options
            self.log = logger.get_log()

        def __eq__(self, other):
            if not self.validate_existing_tags(self.vm, other.vm):
                return False
            if self.restore_validation_options.get('tags', None):
                if not self.validate_added_tags(self.vm, other.vm):
                    return False
            if self._do_restore_validation_options['CrossAD_Restore']:
                if not self.validate_cross_ad_restore(other.vm):
                    return False
            return True

        def validate_existing_tags(self,source_vm,destination_vm):
            """
            Validates the presence of all the tags that were present on the source VM and its volumes on the destination VM and its volumes

            Args:
                source_vm       (vm_obj)   - Source VM object
                destination_vm  (vm_obj)   - Destination VM object

            Returns:
                (bool)  - True if tags are same else False
            """
            return self.validate_existing_vm_tags(source_vm,destination_vm) and self.validate_existing_volume_tags(source_vm,destination_vm)
        
        def validate_existing_vm_tags(self,source_vm,destination_vm):
            """
            Validates the presence of all the tags that were present on the source VM on the destination VM

            Args:
                source_vm       (vm_obj)   - Source VM object
                destination_vm  (vm_obj)   - Destination VM object

            Returns:
                (bool)  - Returns True if the restored VM has all the tags as the source VM else False
            """
            self.log.info("Validating existing VM tags")
            for tag_namespace in source_vm.instance_tags.keys():
                for tag_key,tag_value in source_vm.instance_tags[tag_namespace].items():
                    if tag_namespace not in destination_vm.instance_tags.keys() or tag_key not in destination_vm.instance_tags[tag_namespace].keys() or destination_vm.instance_tags[tag_namespace][tag_key] != tag_value:
                        self.log.error("Restored VM does have the tag %s:%s belonging to namespace %s",tag_key,tag_value,tag_namespace)
                        return False
            return True
    
        def validate_existing_volume_tags(self,source_vm,destination_vm):
            """
            Validates the presence of all the tags that were present on the volumes of the source VM on the destination VM

            Args:
                source_vm       (vm_obj)   - Source VM object
                destination_vm  (vm_obj)   - Destination VM object

            Returns:
                (bool)  - Returns True if the restored volumes have the same tags as the source volumes else False
            """
            self.log.info("Validating Boot Volume Tags")
            for tag_namespace in source_vm.boot_volume_info['defined_tags'].keys():
                for tag_key,tag_value in source_vm.boot_volume_info['defined_tags'][tag_namespace].items():
                    if tag_namespace not in destination_vm.boot_volume_info['defined_tags'].keys() or tag_key not in destination_vm.boot_volume_info['defined_tags'][tag_namespace].keys() or destination_vm.boot_volume_info['defined_tags'][tag_namespace][tag_key] != tag_value:
                        self.log.error("Restored Block Volume does have the tag %s:%s belonging to namespace %s",tag_key,tag_value,tag_namespace)
                        return False
            self.log.info("Successfully Validated Boot Volume Tags")
            self.log.info("Validating Block Volume Tags")
            for src_volume_id in source_vm.block_volume_info.keys():
                for dest_volume_id in destination_vm.block_volume_info.keys():
                    if source_vm.block_volume_info[src_volume_id]['display_name'] == destination_vm.block_volume_info[dest_volume_id]['display_name']:
                        self.log.info("Validating Tags for Block Volume %s with display name %s",dest_volume_id,destination_vm.block_volume_info[dest_volume_id]['display_name'])
                        for tag_namespace in source_vm.block_volume_info[src_volume_id]['defined_tags'].keys():
                            for tag_key,tag_value in source_vm.block_volume_info[src_volume_id]['defined_tags'][tag_namespace].items():
                                if tag_namespace not in destination_vm.block_volume_info[dest_volume_id]['defined_tags'].keys() or tag_key not in destination_vm.block_volume_info[dest_volume_id]['defined_tags'][tag_namespace].keys() or destination_vm.block_volume_info[dest_volume_id]['defined_tags'][tag_namespace][tag_key] != tag_value:
                                    self.log.error("Restored Block Volume %s does have the tag %s:%s belonging to namespace %s",dest_volume_id,tag_key,tag_value,tag_namespace)
                                    return False
            self.log.info("Successfully Validated Block Volume Tags")
            return True

        def validate_added_tags(self,source_vm,destination_vm):
            """
            Validates the presence of of tags that were provided as input to add to the destionation VM
            
            Args:
                source_vm       (vm_obj)   - Source VM object
                destination_vm  (vm_obj)   - Destination VM object

            Returns:
                (bool)  - True if the restored VM has all the tags that were provided as input else False
            """
            self.log.info("Validating if the restored VM has the tags {}".format(self.restore_validation_options['tags']))
            for tag_namespace in self.restore_validation_options['tags'].keys():
                for tag_key,tag_value in self.restore_validation_options['tags'][tag_namespace].items():
                    if tag_namespace not in destination_vm.instance_tags.keys() or tag_key not in destination_vm.instance_tags[tag_namespace].keys() or destination_vm.instance_tags[tag_namespace][tag_key] != tag_value:
                        self.log.error("Restored VM does have the tag %s:%s belonging to namespace %s",tag_key,tag_value,tag_namespace)
                        return False
            self.log.info("Restored VM has all the tags that were provided as input")
            return True
        
        def validate_cross_ad_restore(self,destination_vm):
            """
            Validates if the restored VM is the same AD as the one specified in the restore options and also ensures that that the restored VM's AD is different from Restored Proxy's AD

            Args:
                source_vm       (vm_obj)   - Source VM object

            Returns:
                (bool)  - True if the restored VM is in the same AD as the one specified in the restore options and different from the source VM AD else False
            """
            self.log.info("Validating Cross AD Restore")
            if destination_vm.availability_domain != self.restore_validation_options['CrossAD_AvailabilityDomain']:
                self.log.error("VM is restored to %s AD but the input AD is %s",destination_vm.availability_domain,self.restore_validation_options['CrossAD_AvailabilityDomain'])
                return False
            restore_proxy = OciVM(self.hvobj,self.restore_validation_options['Restore_Proxy'])
            if destination_vm.availability_domain == restore_proxy.availability_domain:
                self.log.error("Restored VM is in the same AD as the Restored Proxy")
                return False
            self.log.info("Restored VM belongs to AD %s and is different from the Restored Proxy's AD %s",destination_vm.availability_domain,restore_proxy.availability_domain)
            self.log.info("Successfully Validated Cross AD Restore")
            return True

    class VmConversionValidation(object):
        def __init__(self, vmobj, vm_restore_options):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.log = logger.get_log()

        def __eq__(self, other):

            """
            compares the restored vm properties after restore
            vm_restore_options - contains properties like Availability Domain , Shape, subnet, Compartment

            Return:
                value     (bool)- on successful validation return true
            """
            return (self.vm.compartment_name == self.vm_restore_options.compartment_name and
                    self.vm.datastore == self.vm_restore_options.datastore and
                    self.vm.subnet_id == self.vm_restore_options.subnet_id and
                    self.vm.no_of_cpu == self.vm_restore_options.disk_info
                    )
    
    def instance_power_state(self):
        """
        Get the power state of the instance 

        Returns:
            power_state     (str) - Power state of the instace 
        """
        if not self.instance_id:
            self.update_vm_info()
        return self.hvobj.instance_power_state(self.instance_id)

    def power_off(self):
        """
        Power off the instance using the instance id
        """
        self.log.info("Powering off the VM %s" % self.vm_name)
        if not self.instance_id:
            self.update_vm_info()
        try:
            self.hvobj.instance_action(self.instance_id, 'STOP')
            self.log.info("Successfully powered off the VM %s" % self.vm_name)
        except Exception as err:
            self.log.exception("Failed to power off the VM %s" % self.vm_name)
            raise Exception(err)

    def power_on(self):
        """
        Power off the instance using the instance id
        """
        self.log.info("Powering on the VM %s" % self.vm_name)
        if not self.instance_id:
            self.update_vm_info()
        try:
            self.hvobj.instance_action(self.instance_id, 'START')
            self.log.info("Successfully powered on the VM %s" % self.vm_name)
        except Exception as err:
            self.log.exception("Failed to power on the VM %s" % self.vm_name)
            raise Exception(err)

    def reboot(self):
        """
        Reboots(Not force Reboot) the instance using the instance id
        """
        self.log.info("Rebooting the VM %s" % self.vm_name)
        if not self.instance_id:
            self.update_vm_info()
        try:
            self.hvobj.instance_action(self.instance_id, 'SOFTRESET')
            self.log.info("Successfully rebooted the VM %s" % self.vm_name)
        except Exception as err:
            self.log.exception("Failed to reboot the VM %s" % self.vm_name)
            raise Exception(err)
    
    def clean_up(self):
        """
        Detach block volumes of an instance and delete the instance
        """
        self.log.info("Cleaning up the VM %s" % self.vm_name)
        try:
            self.log.info("Detaching and deleting block volumes of the VM %s" % self.vm_name)
            for volume_attachment_id in self.block_volume_info.keys():
                self.hvobj.detach_block_volume(volume_attachment_id)
                self.hvobj.delete_block_volume(self.block_volume_info[volume_attachment_id]['volume_id'])
            self.log.info("Terminating the VM %s" % self.vm_name)
            self.hvobj.terminate_instance(self.instance_id)
            self.log.info("Successfully cleaned up the VM %s" % self.vm_name)
        except Exception as err:
            self.log.exception("Failed to clean up the VM %s" % self.vm_name)
            raise Exception(err)

    def _set_credentials(self, os_name):
        """
        Overridden because root login is not possible in out of place restored OCI instance.
        """
        os_name = self.get_os_name(self.vm_hostname)
        if os_name.lower() == "windows":
            try:
                sections = eval('self.config.Virtualization.windows.creds')
                user_list = sections.split(",")
                incorrect_usernames = []
                for each_user in user_list:
                    self.user_name = each_user.split(":")[0]
                    self.password = VirtualServerUtils.decode_password(each_user.split(":")[1])
                    try:
                        vm_machine = machine.Machine(self.vm_hostname,
                                                     username=self.user_name,
                                                     password=self.password)
                        if vm_machine:
                            self.machine = vm_machine
                            self.guest_os = os_name.lower()
                            return
                    except:
                        incorrect_usernames.append(each_user.split(":")[0])
            except Exception as exp:
                self.log.error(str(exp))
                self.log.exception(f"Could not create Machine object! The following user names are "
                                   f"incorrect: {incorrect_usernames}")
                return

        else:
            try:
                sections = eval('self.config.Virtualization.oci.creds')
                keys = eval('self.config.Virtualization.oci.keys')
                try:
                    key_list = keys.split(",")
                except Exception as err:
                    key_list = keys
                self.user_name = sections
                if "," in sections:
                    self.user_name = sections.split(",")[0]
                    self.password = sections.split(",")[1]
                    vm_machine = machine.Machine(self.vm_hostname.strip(), username=self.user_name,
                                                 password=self.password)
                else:
                    self.user_name = sections
                    self.password = ''
                    vm_machine = machine.Machine(self.vm_hostname.strip(), username=self.user_name,
                                                 password=self.password, key_filename=key_list,
                                                 run_as_sudo=True)
                if vm_machine:
                    self.machine = vm_machine
                    self.guest_os = self.machine.os_flavour.lower()
                    return
            except Exception as err:
                self.log.error(str(err))
                self.log.exception("Could not create Machine object! The following user names are "
                                   "incorrect: {0}")
                return

    def _get_basic_vm_info(self):
        """
        Collect basic properties for VM
        
        Returns:
            vm_info     (dict) - All the VM properties of the VM
        """
        try:
            vm_info = self.hvobj.get_vm_properties(vm_name=self.vm_name)
            if not vm_info:
                try:
                    client = self.commcell.clients.get(self.vm_name)
                    ip = client.client_hostname
                    self.log.info("%s is a Commcell Client. Using IP %s to collect vm properties" % (self.vm_name, ip))
                    vm_info = self.hvobj.get_vm_properties(vm_ip=ip)
                except:
                    self.log.exception("Given VM is not a commcell client.Not trying to collect VM properties using IP")
            return vm_info
        except Exception as err:
            self.log.exception("Failed to Get all the VM Properties of the VM %s", self.vm_name)
            raise Exception(err)

    def update_vm_info(self, prop='Basic', os_info=False, force_update=False):
        """
        Update VM information
        Args:
            prop (str) - TBD
            os_info (bool) - Gets the OS information if set to True
            force_update (bool) - Force update the VM information
        """
        if os_info:
            if not self._basic_props_initialized:
                self._initialize_basic_instance_details()
            self.vm_guest_os = self.hvobj.ComputeClient.get_image(self.image_id).data.operating_system

        if self._all_vm_properties_initialized and not force_update:
            self.log.info('All VM properties are already initialized for %s' % self.vm_name)
            return

        if force_update:
            self._all_vm_properties_initialized = False
            self.log.info('Forcefully updating VM properties for %s' % self.vm_name)

        self._initialize_basic_instance_details()
        try:
            if self.power_state.lower() != 'running':
                self.log.info('Turning on the VM: %s' % self.vm_name)
                self.power_on()
                self._initialize_basic_instance_details()
        except Exception as err:
            self.log.exception('An expection occured while trying to power on the VM: %s' % self.vm_name)
            raise Exception(err)        
        try:
            self._initialize_network_info()
            self._initialize_volume_info()
            try:
                self.vm_guest_os = self.hvobj.ComputeClient.get_image(self.image_id).data.operating_system
            except Exception:
                for i in range(3):
                    self.log.exception('Failed to get OS information for {}. Attempt {} of 3 of rebooting and retrying'.format(self.vm_name, i+1))
                    try:
                        self.reboot()
                        self.vm_guest_os = self.hvobj.ComputeClient.get_image(self.image_id).data.operating_system
                        break
                    except Exception:
                        if i != 2:
                            self.log.exception("Attempt {} of 3 failed. Sleeping for 30 seconds before next attempt".format(i+1))
                            time.sleep(30)
            self._all_vm_properties_initialized = True
        except Exception as err:
            self.log.exception('An expection occured while trying to update VM Info for %s' % self.vm_name)
            raise Exception(err)

    def get_compartment_path(self, compartment_id):
        """
        Get the compartment path from the root(region) to the given compartment id

        Args:
            compartment_id     (str):  Compartment id
        
        Returns:
            compartment_path   (list):  Compartment path from root to the given compartment id
        """
        compartment_path =[]
        root_compartment_id = self.hvobj.get_compartment_details().data.id
        comp_id = compartment_id 
        while (comp_id != root_compartment_id):
            compartment_path.append(self.hvobj.get_compartment_details(compartment_id=comp_id).data.name)
            comp_id = self.hvobj.get_compartment_details(compartment_id=comp_id).data.compartment_id
        compartment_path.extend([self.hvobj.get_compartment_details().data.name,self.availability_domain,self.region])
        compartment_path.reverse()
        return compartment_path

    def _initialize_basic_instance_details(self):
        """
        Initalizes basic instance details like name, id, availability domain, shape, etc
        """
        self.log.info("Initializing basic VM properties for %s" % self.vm_name)
        basic_vm_info = self._get_basic_vm_info()
        if not basic_vm_info:
            raise Exception("Failed to get basic VM properties")
        self.instance_id = basic_vm_info.id
        self.instance_tags = basic_vm_info.defined_tags
        self.compartment_id = basic_vm_info.compartment_id
        self.compartment_name = self.hvobj.compartment_dict[self.compartment_id]
        self.availability_domain = basic_vm_info.availability_domain
        self.region = self.availability_domain.split(":")[1].replace('-AD','').lower()
        self.shape = basic_vm_info.shape
        self.image_id = basic_vm_info.image_id
        self.compartment_path = self.get_compartment_path(self.compartment_id)
        self.power_state = basic_vm_info.lifecycle_state
        self.no_of_cpu = basic_vm_info.shape_config.ocpus
        self.memory = basic_vm_info.shape_config.memory_in_gbs
        self._basic_props_initialized = True
        self.log.info("Successfully initialized basic VM properties for %s" % self.vm_name)

    def _initialize_network_info(self):
        """
        Initialize network details like IP, VCN, Subnet
        """
        self.log.info("Initializing network details for %s" % self.vm_name)
        network_reponse = self.hvobj.get_vnic_attachments(
            {'instance_id': self.instance_id,
             'availability_domain': self.availability_domain,
             'compartment_id': self.compartment_id})
        if not network_reponse:
            raise Exception("Failed to get network details")
        for vnic_attachment in network_reponse:
            vnic_response = self.hvobj.get_vnic_details(vnic_id = vnic_attachment.vnic_id)
            if not vnic_response:
                raise Exception("Failed to get VNIC details")
            self.vnic_info[vnic_response.id] = {'vnic_id': vnic_response.id,
                                                'subnet_id': vnic_response.subnet_id,
                                                'mac_address': vnic_response.mac_address,
                                                'is_primary': vnic_response.is_primary,
                                                'private_ip': vnic_response.private_ip,
                                                'public_ip': vnic_response.public_ip}
            
            subnet_response = self.hvobj.get_subnet_details(subnet_id = vnic_response.subnet_id)
            if not subnet_response:
                raise Exception("Failed to get subnet details")
            self.subnet_info[subnet_response.id] = {'subnet_id': subnet_response.id,
                                                    'display_name': subnet_response.display_name,
                                                    'compartment_id': subnet_response.compartment_id,
                                                    'vcn_id': subnet_response.vcn_id}

            vcn_response = self.hvobj.get_vcn_details(vcn_id =subnet_response.vcn_id)
            if not vcn_response:
                raise Exception("Failed to get VCN details")
            self.vcn_details[vcn_response.id] = {'vcn_id': vcn_response.id,
                                                'display_name': vcn_response.display_name,
                                                'compartment_id': vcn_response.compartment_id}
            
            if vnic_response.is_primary:
                self.ip = vnic_response.private_ip
                self.vcn = vcn_response.display_name
                self.subnet = subnet_response.display_name
        self.log.info("Successfully initialized network details for %s" % self.vm_name)
    
    def _initialize_volume_info(self):
        """
        Initalize boot and block volume details for the instance
        """
        self.log.info("Initializing volume details for %s" % self.vm_name)
        self._initialize_boot_volume_info()
        self._initialize_block_volume_info()
        self.disk_count = len(self.block_volume_info) + 1
        self.log.info("Successfully initialized volume details for %s" % self.vm_name)
    
    def _initialize_boot_volume_info(self):
        """
        Initialize boot volume details for the instance
        """
        self.log.info("Initializing boot volume details for %s" % self.vm_name)
        boot_volumes = self.hvobj.get_boot_volumes(
            {'instance_id':self.instance_id,
            'availability_domain':self.availability_domain,
            'compartment_id':self.compartment_id})
        boot_volume_response = self.hvobj.get_boot_volume_info(boot_volume_id=boot_volumes[0].boot_volume_id)
        if not boot_volume_response:
            raise Exception("Failed to get boot volume details")
        self.boot_volume_info = {'boot_volume_id': boot_volume_response.id,
                                'display_name': boot_volume_response.display_name,
                                'availability_domain': boot_volume_response.availability_domain,
                                'compartment_id': boot_volume_response.compartment_id,
                                'size': boot_volume_response.size_in_gbs,
                                'defined_tags': boot_volume_response.defined_tags}
        self.disk_dict['Boot_Volume'] = {'boot_volume_id': boot_volume_response.id,
                                         'display_name': boot_volume_response.display_name,
                                         'size': boot_volume_response.size_in_gbs}

    def _initialize_block_volume_info(self):
        self.log.info("Initializing block volume details for %s" % self.vm_name)
        self.disk_dict['Block_Volumes'] = dict()
        block_volume_attachments = self.hvobj.get_block_volume_attachments(
            {'instance_id':self.instance_id,
            'availability_domain':self.availability_domain,
            'compartment_id':self.compartment_id})
        for block_volume_attachment in block_volume_attachments:
            if block_volume_attachment.lifecycle_state == block_volume_attachment.LIFECYCLE_STATE_ATTACHED:
                block_volume_response = self.hvobj.get_block_volume_info(block_volume_id=block_volume_attachment.volume_id)
                if not block_volume_response:
                    raise Exception("Failed to get block volume details")
                self.block_volume_info[block_volume_attachment.id] = {'volume_id': block_volume_response.id,
                                                                      'display_name': block_volume_response.display_name,
                                                                      'availability_domain': block_volume_response.availability_domain,
                                                                      'compartment_id': block_volume_response.compartment_id,
                                                                      'size': block_volume_response.size_in_gbs,
                                                                      'defined_tags': block_volume_response.defined_tags}

                self.disk_dict['Block_Volumes'][block_volume_response.id] = {'volume_id': block_volume_response.id,
                                                                             'display_name': block_volume_response.display_name,
                                                                             'size': block_volume_response.size_in_gbs}