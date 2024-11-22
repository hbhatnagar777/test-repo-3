# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on OCI """

import oci
import time
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from AutomationUtils import config
import time
from collections import deque

class OciHelper(Hypervisor):

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):

        super(OciHelper, self).__init__(server_host_name, user_name, password,
                                        instance_type, commcell, host_machine)

        self.oci_dict = user_name
        self.server_host_name = server_host_name
        self.oci_vm_ip = None
        self.oci_vm_guid = None
        self.oci_vm_vmsize = None
        self.oci_vm_vcn = None
        self.vm_details_dict = dict()
        self.instance_type = instance_type
        self.config = config.get_config()
        self.oci_config = {
            "user": self.oci_dict['oci_user_id'],
            "key_file": self.oci_dict['oci_private_key_file_path'],
            "fingerprint": self.oci_dict['oci_finger_print'],
            "tenancy": self.oci_dict['oci_tenancy_id'],
            "region": self.oci_dict['oci_region_name'],
            "pass_phrase": self.oci_dict['oci_private_key_password']
        }
        config_validator = oci.config.validate_config(self.oci_config)
        self.ComputeClient = oci.core.ComputeClient(self.oci_config)
        self.NetworkClient = oci.core.VirtualNetworkClient(self.oci_config)
        self.BlockStorageClient = oci.core.BlockstorageClient(self.oci_config)
        self.identity = oci.identity.IdentityClient(self.oci_config)
        self.resource_manager = oci.resource_manager.ResourceManagerClient(self.oci_config)
        self.composite_resource_manager = oci.resource_manager.ResourceManagerClientCompositeOperations(self.oci_config)
        if config_validator not in (None, "None"):
            raise Exception
        self.user = self.identity.get_user(self.oci_config["user"]).data
        self.proxies = dict()
        self.root_compartment_id = self.user.compartment_id
        self.compartment_dict = dict()
        self.initalize_compartment_dict() 

    def initalize_compartment_dict(self):
        """
        Initalizes compartment dictionary with {compartment_id: compartment_name}
        """
        if self.compartment_dict:
            return 
        self.log.info("Getting the list of all compartments in the OCI account")
        queue = deque([self.root_compartment_id])
        while queue:
            compartment_id = queue.popleft()
            response = oci.pagination.list_call_get_all_results(
                    self.identity.list_compartments,
                    compartment_id = compartment_id,
                    lifecycle_state = "ACTIVE",
                    retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
            for compartment in response.data:
                queue.append(compartment.id)
                self.compartment_dict[compartment.id] = compartment.name
        self.log.info("Collected the list of all compartments in the OCI account")

    def get_vm_properties(self, vm_name=None, vm_ip=None):
        """
        Gets the details of the instance using:
        1. vm_name if provided
        2. vm_ip if provided
        3. If both are provided, it will use the vm_name first to get the details. If not found, it will use the vm_ip

        Args:
            vm_name: (str) name of the instance
            vm_ip: (str) ip of the instance

        Returns:
            (dict) Returns a dictioanry of the instance details if found, else empty dict
        """
        if vm_name:
            self.log.info("Getting the details of the VM with name: %s" % vm_name)
            for compartment_id in self.compartment_dict.keys():
                try:
                    response = oci.pagination.list_call_get_all_results(
                        self.ComputeClient.list_instances,
                        compartment_id = compartment_id,
                        display_name = vm_name,
                        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
                    if response.data:
                        for instance_response in response.data:
                            if instance_response.lifecycle_state in ['RUNNING', 'STOPPED']:
                                return instance_response
                except Exception as err:
                    if isinstance(err, oci.exceptions.ServiceError):
                        if err.status == 404:
                            self.log.warning("Expection occured while searching comparmtent %s for vm %s" % (self.compartment_dict[compartment_id], vm_name))
                            self.log.warning(str(err))
                            continue
                    self.log.error("Expection occured while searching comparmtent %s for vm %s" % (self.compartment_dict[compartment_id], vm_name))
                    self.log.error(str(err))
            self.log.warning("VM with name: %s not found" % vm_name)
        if vm_ip:
            self.log.info("Getting the details of the VM with IP: %s" % vm_ip)
            for compartment_id in self.compartment_dict.keys():
                try:
                    response = oci.pagination.list_call_get_all_results(
                        self.ComputeClient.list_instances,
                        compartment_id = compartment_id,
                        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
                    for instance_response in response.data:
                        network_response = oci.pagination.list_call_get_all_results(
                            self.ComputeClient.list_vnic_attachments,
                            compartment_id = instance_response.compartment_id,
                            instance_id = instance_response.id,
                            retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
                        for network in network_response.data:
                            vnic_id = network.vnic_id
                            try:
                                vnic_response = self.get_vnic_details(vnic_id = vnic_id)
                                if  vnic_response.is_primary and vnic_response.private_ip == vm_ip:
                                    return instance_response
                            except Exception as err:
                                self.do_nothing()
                except Exception as err:
                    if isinstance(err, oci.exceptions.ServiceError):
                        if err.status == 404:
                            self.log.warning("Expection occured while searching comparmtent %s for vm %s" % (self.compartment_dict[compartment_id], vm_ip))
                            self.log.warning(str(err))
                            continue
                    self.log.error("Expection occured while searching comparmtent %s for vm %s" % (self.compartment_dict[compartment_id], vm_ip))
                    self.log.error(str(err))
            self.log.warning("VM with IP: %s not found" % vm_ip)
        return 


    def power_on_proxies(self, proxy_ips):
        """
        Power on the proxy machines which are provided from the input
        Args
            proxy_ips : dict() containing host-name as key and ip-address as values
        """
        if not isinstance(proxy_ips, dict):
            raise TypeError('proxy_ips must be dict contains hostname as key and ip-address as value')
        if not self.proxies:
            self.log.info("Searching for proxies with IP addresses: %s" % list(proxy_ips.values()))
            self.get_proxies(proxy_ips=proxy_ips)
        self.log.info("Powering on proxies with IP addresses: %s" % list(proxy_ips.values()))
        for proxy_id in self.proxies:
            self.instance_action(instance_id=proxy_id, action='START')            
            if self.instance_power_state(proxy_id) == 'RUNNING':
                self.log.info("Proxy with display_name: %s and IP: %s is running" % (self.proxies[proxy_id]['Display_Name'], self.proxies[proxy_id]['IP']))
            else:
                self.log.error("Could not power on the proxy with display_name: %s and IP: %s" % (self.proxies[proxy_id]['Display_Name'], self.proxies[proxy_id]['IP']))

    def power_off_proxies(self, proxy_ips):
        """
            Power off the proxy machines which are provided from the input
            proxy_ips : dict() containing host-name as key and ip-address as values
        """
        if not isinstance(proxy_ips, dict):
            raise TypeError('proxy_ips must be dict contains hostname as key and ip-address as value')
        if not self.proxies:
            self.log.info("Searching for proxies with IP addresses: %s" % list(proxy_ips.values()))
            self.get_proxies(proxy_ips=proxy_ips)
        self.log.info("Powering off proxies with IP addresses: %s" % list(proxy_ips.values()))
        for proxy_id in self.proxies:
            self.instance_action(instance_id=proxy_id, action='STOP')
            if self.instance_power_state(proxy_id) == 'STOPPED':
                self.log.info("Proxy with display_name: %s and IP: %s is stopped" % (self.proxies[proxy_id]['Display_Name'], self.proxies[proxy_id]['IP']))
            else:
                self.log.error("Could not power off the proxy with display_name: %s and IP: %s" % (self.proxies[proxy_id]['Display_Name'], self.proxies[proxy_id]['IP']))

    def instance_power_state(self,  instance_id):
        """
        get the power state of the instance

        Args:
            instance_id (str) : id of the instance
        """
        response = self.ComputeClient.get_instance(instance_id=instance_id)
        instance_info = response.data
        return instance_info.lifecycle_state

    def instance_action(self, instance_id, action='START'):
        """
        START/STOP the instance
        Args:
            instance_id (str): OCID of the instance
            action (str) : Action to be performored on the instance. Currently only START/STOP/SOFTRESET are supported
        """
        if action not in ['START', 'STOP', 'SOFTRESET']:
            raise ValueError('Invalid action. Only START/STOP/SOFTRESET are supported')
        if action == 'START' and self.instance_power_state(instance_id) == 'RUNNING':
            self.log.info("Instance with id %s is already running" % instance_id)
            return
        if action == 'STOP' and self.instance_power_state(instance_id) == 'STOPPED':
            self.log.info("Instance with id %s is already stopped" % instance_id)
            return
        try:
            self.ComputeClient.instance_action(instance_id, action),
            oci.wait_until(
                self.ComputeClient,
                self.ComputeClient.get_instance(instance_id),
                'lifecycle_state',
                'STOPPED' if action == 'STOP' else 'RUNNING',
                max_wait_seconds = 1000 if action == 'SOFTRESET' else 300,
                succeed_on_not_found=True
            )
        except Exception as err:
            self.log.error('Exception occurred while performing %s action on the instance with id: %s' % (action, instance_id))
            self.log.error(str(err))
    
    def terminate_instance(self, instance_id, preserve_boot_volume=False):
        """
        Terminate the instance
        Args:
            instance_id (str): OCID of the instance
            preserve_boot_volume (bool): If True, boot volume will not be deleted
        """
        try:
            self.log.info("Terminating the instance with id: %s" % instance_id)
            self.ComputeClient.terminate_instance(instance_id, preserve_boot_volume=preserve_boot_volume)
            oci.wait_until(
                self.ComputeClient,
                self.ComputeClient.get_instance(instance_id),
                'lifecycle_state',
                'TERMINATED',
                max_wait_seconds=300,
                succeed_on_not_found=True
            )
        except Exception as err:
            self.log.error('Exception occurred while terminating the instance with id: %s' % instance_id)
            self.log.error(str(err))
    
    def detach_block_volume(self, volume_attachment_id):
        """
        Detach the block volume
        Args:
            volume_attachment_id (str): OCID of the volume attachment
        """
        self.log.info("Detaching the block volume with id: %s" % volume_attachment_id)
        try:
            self.ComputeClient.detach_volume(volume_attachment_id)
            oci.wait_until(
                self.ComputeClient,
                self.ComputeClient.get_volume_attachment(volume_attachment_id),
                'lifecycle_state',
                'DETACHED',
                max_wait_seconds=300,
                succeed_on_not_found=True
            )
        except Exception as err:
            self.log.error('Exception occurred while detaching the block volume with id: %s' % volume_attachment_id)
            self.log.error(str(err))
    
    def delete_block_volume(self, volume_id):
        """
        Delete the block volume
        Args:
            volume_id (str): OCID of the volume
        """
        self.log.info("Deleting the block volume with id: %s" % volume_id)
        try:
            self.BlockStorageClient.delete_volume(volume_id)
            oci.wait_until(
                self.BlockStorageClient,
                self.BlockStorageClient.get_volume(volume_id),
                'lifecycle_state',
                'TERMINATED',
                max_wait_seconds=300,
                succeed_on_not_found=True
            )
        except Exception as err:
            self.log.error('Exception occurred while deleting the block volume with id: %s' % volume_id)
            self.log.error(str(err))

    def get_boot_volume_backups(self, compartment_ocid, source_boot_volume_backup_id=None):
        """
        this method gets the boot volumes backups in the compartment
        Args:
            compartment_ocid: ocid of the compartment in oci
            source_boot_volume_backup_id: id of the boot volume of source machine

        Returns:

        """
        try:
            response = oci.pagination.list_call_get_all_results(
                    self.BlockStorageClient.list_boot_volume_backups,
                    compartment_id=compartment_ocid,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            return response
        except Exception as err:
            self.log.error('Exception occurred while getting boot volume backup details')
            self.log.error(str(err))

    def terminate_vm(self, vm_id):
        """
        terminate the instance of the given id
        Args:
            vm_id: (str) ocid of the vm

        Returns:
            None
        """
        self.ComputeClient.terminate_instance(vm_id)
        oci.wait_until(
            self.ComputeClient,
            self.ComputeClient.get_instance(vm_id),
            'lifecycle_state',
            'TERMINATED',
            succeed_on_not_found=True
        )

    def get_all_vms_in_hypervisor(self):
        """
        Gets all the vms of the hypervisor
        Returns:
           vm_name_list (list) list of names of vms in the hypervisor
        """
        vm_name_list = []
        for compartment in self.compartment_dict.keys():
            try:
                response = oci.pagination.list_call_get_all_results(
                    self.ComputeClient.list_instances,
                    compartment_id=compartment,
                    retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
                for instance in response.data:
                    vm_name_list.append(instance.display_name)
            except Exception as err:
                self.do_nothing()
        return vm_name_list 

    def get_compartment_details(self, compartment_id=None, compartment_name=None):
        """
        Gets the details of the compartment using
        1. compartment_id if provied
        2. compartment_name if provided
        3. root compartment if neither of the above are provided
        4. If both are provided, it will use the compartment_id first to get the details. If not found, it will use the compartment_name

        Args:
            compartment_name: (str) name of the compartment
            compartment_id: (str) id of the compartment
        
        Returns:
            compartment details (dict)
        """
        if compartment_id:
            return self.identity.get_compartment(compartment_id)
        if compartment_name:
            pass #Not needed as of now. Will implement if needed
        return self.identity.get_compartment(self.root_compartment_id)

    def list_stacks(self,compartment_id, lifecycle_state='ACTIVE', display_name=None):
        """
        get the list of stacks in the account based on the filters provided
        lifecycle_state (str) : state of stack (optional)
        compartment_id (str): ocid of the compartment(optional)
        display_name (str): name of the stack (optional)
        """
        kwargs = dict()
        kwargs["lifecycle_state"] = lifecycle_state
        kwargs['compartment_id'] = compartment_id
        if display_name:
            kwargs['display_name'] = display_name
        stack_response = self.resource_manager.list_stacks(**kwargs)
        stack_list = []
        for stack in stack_response.data:
            stack_list.append(stack.id)
        return stack_list

    def create_stack(self, stack_creation_data, delete_previous_existing=False):
        """
        create the stack on the oci
        Args:
            stack_creation_data: (dict)
            delete_previous_existing : (bool) delete the stack with the name if there is any in the compartment
        Returns:
            stackinfo object of oci
        """
        if delete_previous_existing:
            self.log.info("checking for any previous existing stacks")
            stack_list = self.list_stacks(compartment_id=stack_creation_data['compartment_id'],
                                          display_name=stack_creation_data['display_name'])
            for stack in stack_list:
                self.delete_stack(stack_id=stack)
        self.log.info("waiting for a minute before stack creation")
        time.sleep(60)
        zipfiledetails = oci.resource_manager.models.CreateZipUploadConfigSourceDetails()
        zipfiledetails.config_source_type = 'ZIP_UPLOAD'
        zipfiledetails.zip_file_base64_encoded = stack_creation_data['encoded_file']

        createStackDetails = oci.resource_manager.models.CreateStackDetails()
        createStackDetails.display_name = stack_creation_data['display_name']
        createStackDetails.description = stack_creation_data['description']
        createStackDetails.config_source = zipfiledetails
        createStackDetails.terraform_version = '1.0.x'
        createStackDetails.compartment_id = stack_creation_data['compartment_id']
        createStackDetails.variables = stack_creation_data['variables']
        stack_info = self.resource_manager.create_stack(create_stack_details=createStackDetails)
        stack_info = stack_info.data
        self.log.info("waiting for stack creation")
        time.sleep(15)
        time_passed = 15
        while stack_info.lifecycle_state not in [stack_info.LIFECYCLE_STATE_ACTIVE]:
            if time_passed > 120:
                raise Exception("stack creation taking too long, please check on the OCI console")
            time.sleep(20)
            time_passed = time_passed + 20
            stack_info = self.get_stack_details(stack_id = stack_info.id)
        self.log.info("stack created successfully")
        return stack_info

    def delete_stack(self, stack_id, run_destory=True):
        """
        method to delete the stack
        Args:
            stack_id: (str) ocid of the stack

        Returns:
            None
        """
        self.log.info(f"deleting stack : {stack_id}")
        if run_destory:
            self.run_destroy_job_for_stack(stack_id=stack_id)
        self.resource_manager.delete_stack(stack_id=stack_id)
        self.log.info("deleted the stack successfully")

    def run_destroy_job_for_stack(self, stack_id):
        """
        run the destory job on the stack id
        Args:
            stack_id:(str) ocid of the stack on OCI

        Returns:
            None
        """
        self.log.info(f"running destroy job on the stack : {stack_id}")
        destroy_job_operation_details = oci.resource_manager.models.CreateDestroyJobOperationDetails()
        destroy_job_operation_details.operation = 'DESTROY'
        destroy_job_operation_details.execution_plan_strategy = 'AUTO_APPROVED'

        destroy_job_details = oci.resource_manager.models.CreateJobDetails()
        destroy_job_details.stack_id = stack_id
        destroy_job_details.job_operation_details = destroy_job_operation_details
        destroy_job_info = self.resource_manager.create_job(destroy_job_details)
        destroy_job_info = destroy_job_info.data
        self.log.info(f"waiting for the destroy job : {destroy_job_info.id} to complete")
        time.sleep(30)
        time_passed = 30
        while destroy_job_info.lifecycle_state not in [destroy_job_info.LIFECYCLE_STATE_SUCCEEDED]:
            if time_passed > 300:
                raise Exception("destroy job info failed , please check the OCI console for details ")
            time.sleep(60)
            time_passed = time_passed + 60
            destroy_job_info = self.get_job_details(destroy_job_info.id)
        self.log.info("destroy job completed successfully")
        return destroy_job_info

    def run_plan_job_for_stack(self, stack_id):
        """
        run the plan job on the stack id
        Args:
            stack_id:(str) ocid of the stack on OCI
        Returns:
            job object of oci
        """
        self.log.info(f"running plan job on the stack : {stack_id}")
        plan_job_operation_details = oci.resource_manager.models.CreatePlanJobOperationDetails()
        plan_job_operation_details.operation = 'PLAN'

        plan_job_details = oci.resource_manager.models.CreateJobDetails()
        plan_job_details.stack_id = stack_id
        plan_job_details.job_operation_details = plan_job_operation_details
        plan_job_info = self.resource_manager.create_job(plan_job_details)
        plan_job_info = plan_job_info.data
        self.log.info(f"waiting for the plan job : {plan_job_info.id} to complete")
        time.sleep(30)
        time_passed = 30
        while plan_job_info.lifecycle_state not in [plan_job_info.LIFECYCLE_STATE_SUCCEEDED]:
            if time_passed > 300:
                raise Exception("plan job info failed , please check the OCI console for details ")
            time.sleep(60)
            time_passed = time_passed + 60
            plan_job_info = self.get_job_details(plan_job_info.id)
        self.log.info("plan job completed successfully")
        return plan_job_info

    def run_apply_job_for_stack(self, stack_id, plan_job_id):
        """
        run apply job for the oci stack
        Args:
            stack_id: (str) ocid of the stack
            plan_job_id: (str) ocid of the plan job

        Returns:
            job object of the oci (apply job)
        """
        self.log.info(f"running apply job on the stack : {stack_id}")
        apply_job_operation_details = oci.resource_manager.models.CreateApplyJobOperationDetails()
        apply_job_operation_details.operation = 'APPLY'
        apply_job_operation_details.execution_plan_job_id = plan_job_id
        job_details = oci.resource_manager.models.CreateJobDetails()
        job_details.stack_id = stack_id
        job_details.job_operation_details = apply_job_operation_details
        apply_job_info = self.resource_manager.create_job(job_details)
        apply_job_info = apply_job_info.data
        self.log.info(f"waiting for the apply job : {apply_job_info.id} to complete")
        time.sleep(30)
        time_passed = 30
        while apply_job_info.lifecycle_state not in [apply_job_info.LIFECYCLE_STATE_SUCCEEDED]:
            if time_passed > 600:
                raise Exception("apply job info failed , please check the OCI console for details ")
            time.sleep(120)
            time_passed = time_passed + 120
            apply_job_info = self.get_job_details(apply_job_info.id)
        self.log.info("apply job completed successfully")
        return apply_job_info

    def get_stack_apply_job_output(self, apply_job_id):
        """
        output of resource job on the stack
        Args:
            apply_job_id: (str) ocid of the apply job

        Returns:
            output object of the job
        """
        import json
        apply_job_state = self.resource_manager.get_job_tf_state(apply_job_id)
        state_json = json.loads(apply_job_state.data.content.decode('utf-8'))
        return state_json

    def oci_user_details(self, username):
        """
        user details of the oci user
        Args:
            username: (str) name of the user

        Returns:
            userdetails obj of oci
        """
        oci_user_details = self.identity.list_users(compartment_id=self.config.Virtualization.oci.tenancy,
                                                           name=username).data[0]
        return oci_user_details

    def upload_api_key(self, oci_user, public_key_path):
        """
        upload a api key to the user on oci
        Args:
            oci_user: (obj) oci user object
            public_key_path: (str) file path of the public key

        Returns:
            (obj) api key data of oci
        """

        with open(public_key_path, 'rb') as f:
            public_key = f.read().strip()
        key_details = oci.identity.models.CreateApiKeyDetails(key=public_key.decode())
        key_response = self.identity.upload_api_key(oci_user.id, key_details)
        api_key_data = key_response.data
        return api_key_data

    def create_api_key_for_user_from_stack(self, apply_job_id):
        """
        create api key for the user form the stack
        Args:
            apply_job_id: (str) ocid of the apply job

        Returns:
            (obj) api key object of oci
        """
        import json
        apply_job_state = self.resource_manager.get_job_tf_state(apply_job_id)
        state_json = json.loads(apply_job_state.data.content.decode('utf-8'))
        stack_user = state_json['outputs']['metallic_user']['value']
        oci_user_details = self.identity.list_users(compartment_id=self.config.Virtualization.oci.tenancy,
                                                           name=stack_user).data[0]
        public_key_path = self.config.Virtualization.oci.public_key_file
        with open(public_key_path, 'rb') as f:
            public_key = f.read().strip()
        key_details = oci.identity.models.CreateApiKeyDetails(key=public_key.decode())
        key_response = self.identity.upload_api_key(oci_user_details.id, key_details)
        api_key_data = key_response.data
        return api_key_data

    def get_job_details(self, job_id):
        """
        job details of the oci stack job
        Args:
            job_id: (str) ocid of the job

        Returns:
            (obj) job object of oci
        """
        job_response = self.resource_manager.get_job(job_id=job_id)
        return job_response.data

    def get_stack_details(self, stack_id):
        """
        stack details of the oci stack
        Args:
            stack_id: (str) ocid of the stack

        Returns:
            (obj) stack object of oci
        """
        stack_details_response = self.resource_manager.get_stack(stack_id=stack_id)
        return stack_details_response.data

    def get_vnic_attachments(self, search_filter):
        """
        gets the vnic attachments in the given compartment_id
        can filter the vnic attachments based on the instance_id and availability_domain
        args:
            search_filter: (dict)
            {  
                'compartment_id': (str) ocid of the compartment (Required),
                'instance_id': (str) ocid of the instance (Optional),
                'availability_domain': (str) availability domain of the instance (Optional)
            }
        returns:
            response (response object): response object of the vnic attachments
        """
        response = oci.pagination.list_call_get_all_results(
                self.ComputeClient.list_vnic_attachments,
                **search_filter,
                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        return response.data

    def get_vnic_details(self, vnic_id):
        """
        Gets the VNIC details of the given vnic_id
        Args:
            vnic_id: (str) OCID of the VNIC
        Returns:
            response (Response Object): Response object of the VNIC details
        """
        try:
            response = self.NetworkClient.get_vnic(vnic_id = vnic_id)
            return response.data
        except Exception as err:
            if isinstance(err, oci.exceptions.ServiceError) and err.status == 404:
                self.do_nothing()
                return
            self.log.error('Exception occurred while getting VNIC details')
            self.log.error(str(err))
    
    def get_subnets(self, search_filter):
        """
        Gets the subnets in the given compartment_id
        Can filter the subnets based on the subnet_name and vcn_id
        Args:
            search_filter: (dict)
            {  
                'compartment_id': (str) OCID of the compartment (Required),
                'display_name': (str) name of the subnet (Optional),
                'vcn_id': (str) OCID of the VCN (Optional)
            }
        Returns:
            response (Response Object): Response object of the details of the subnets satisfying the search filter 
        """
        if 'compartment_id' not in search_filter:
            raise Exception("compartment_id is required in search_filter")
        try:
            response = oci.pagination.list_call_get_all_results(
                self.NetworkClient.list_subnets,
                **search_filter,
                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            return response.data
        except Exception as err:
            if isinstance(err, oci.exceptions.ServiceError)  and err.status == 404:
                self.do_nothing()
                return
            self.log.error('Exception occurred while getting subnet details')
            self.log.error(str(err))

    def get_subnet_details(self, subnet_id):
        """
        Gets the subnet details of the given subnet_id
        Args:
            subnet_id: (str) OCID of the subnet
        Returns:
            response (Response Object): Response object of the subnet details
        """
        try:
            response = self.NetworkClient.get_subnet(subnet_id = subnet_id)
            return response.data
        except Exception as err:
            self.log.error('Exception occurred while getting subnet details')
            self.log.error(str(err))

    def get_vcns(self, search_filter):
        """
        Gets the VCNs in the given compartment_id
        Can filter the VCNs based on the vcn_name
        Args:
            search_filter: (dict)
            {   
                'compartment_id': (str) OCID of the compartment (Required),
                'display_name': (str) name of the VCN (Optional)
            }
        Returns:
            response (Response Object): Response object of the details of the VCNs satisfying the search filter
        """
        if 'compartment_id' not in search_filter:
            raise Exception("compartment_id is required in search_filter")
        try:
            response = oci.pagination.list_call_get_all_results(
                self.NetworkClient.list_vcns,
                **search_filter,
                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            return response.data
        except Exception as err:
            if isinstance(err, oci.exceptions.ServiceError) and err.status == 404:
                self.do_nothing()
                return
            self.log.error('Exception occurred while getting VCN details')
            self.log.error(str(err))
        
    def get_vcn_details(self, vcn_id):
        """
        Gets the VCN details of the given vcn_id
        Args:
            vcn_id: (str) OCID of the VCN
        Returns:
            response (Response Object): Response object of the VCN details
        """
        try:
            response = self.NetworkClient.get_vcn(vcn_id = vcn_id)
            return response.data
        except Exception as err:
            self.log.error('Exception occurred while getting VCN details')
            self.log.error(str(err))

    def get_boot_volumes(self, search_filter):
        """
        Gets the boot volumes in the given availability domain and compartment_id
        Can filter the boot volumes based on the instance_id 
        Args:
            search_filter: (dict)
            { 
                'availability_domain': (str) Availability Domain of the instance (Required),
                'compartment_id': (str) OCID of the compartment (Required),
                'instance_id': (str) OCID of the instance (Optional)
            }
        Returns:
            response (Response Object): Response object of the boot volumes in the given availability domain and compartment_id that satisfies the search_filter    
        """
        if 'availability_domain' not in search_filter or 'compartment_id' not in search_filter:
            raise Exception("availability_domain and compartment_id are required in search_filter")
        try:
            response = oci.pagination.list_call_get_all_results(
                self.ComputeClient.list_boot_volume_attachments,
                **search_filter,
                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            return response.data
        except Exception as err:
            self.log.error('Exception occurred while getting boot volume details')
            self.log.error(str(err))
    
    def get_boot_volume_info(self, boot_volume_id):
        """
        Gets the boot volume details of the given boot_volume_id 
        Args:
            boot_volume_id: (str) OCID of the boot volume 
        Returns:
            (obj) Oci Boot Volume Object
        """
        self.log.info('Getting boot volume info for boot_volume id: %s' % boot_volume_id)
        response = self.BlockStorageClient.get_boot_volume(boot_volume_id)
        try:
            return response.data
        except Exception as err:
            self.log.error('Exception occurred while getting boot volume info')
            self.log.error(str(err))
            return 

    def get_block_volume_attachments(self, search_filter):
        """
        Gets the block volume attachments in a given compartment_id
        Can filter the block volumes based on the instance_id and availability_domain
        Args:
        search_filter: (dict) 
        {  
            'compartment_id': (str) OCID of the compartment (Required),
            'instance_id': (str) OCID of the instance (Optional),
            'availability_domain': (str) Availability Domain of the instance (Optional)
        }


        Returns:
            response (Response Object): Response object of the block volume attachment in the given compartment_id that satisfies the search_filter 
        """
        try:
            response = oci.pagination.list_call_get_all_results(
                self.ComputeClient.list_volume_attachments,
                **search_filter,
                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            return response.data
        except Exception as err:
            self.log.error('Exception occurred while getting block volume details')
            self.log.error(str(err))
    
    def get_block_volume_info(self, block_volume_id):
        """
        Gets the block volume details
        Args:
            block_volume_id: (str) OCID of the block volume

        Returns:
            (obj) Oci Block Volume Object
        """
        self.log.info('Getting block volume info for the instance with block volume id: %s' % block_volume_id)
        response = self.BlockStorageClient.get_volume(block_volume_id)
        try:
            return response.data
        except Exception as err:
            self.log.error('Exception occurred while getting block volume info for block volume id: %s' % block_volume_id)
            self.log.error(str(err))
            return 
    
    def get_proxies(self, proxy_ips):
        """
        Searches in the OCI Account for the Hypervisor Proxies with the given IP addresses
        Args:
            proxy_ips: (dict) containing host-name as key and ip-address as values
        """
        for compartment_id in self.compartment_dict.keys():
            try:
                response = oci.pagination.list_call_get_all_results(
                    self.ComputeClient.list_instances,
                    compartment_id = compartment_id,
                    retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
                for instance_response in response.data:
                    network_response = oci.pagination.list_call_get_all_results(
                        self.ComputeClient.list_vnic_attachments,
                        compartment_id = instance_response.compartment_id,
                        instance_id = instance_response.id,
                        retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY)
                    for network in network_response.data:
                        vnic_id = network.vnic_id
                        vnic_response = self.get_vnic_details(vnic_id = vnic_id)
                        if vnic_response and  vnic_response.is_primary and vnic_response.private_ip in proxy_ips:
                            self.proxies[instance_response.id] = {'IP': vnic_response.private_ip,
                                                                  'Display_Name': instance_response.display_name}
            except Exception as err:
                if isinstance(err, oci.exceptions.ServiceError) and err.status == 404:
                        self.log.warning("Exception occurred while searching comparmtent %s for proxies" % self.compartment_dict[compartment_id])
                        self.log.warning(str(err))
                        continue
                self.log.error("Exception occurred while searching comparmtent %s for proxies" % self.compartment_dict[compartment_id])
                self.log.error(str(err))

    def do_nothing(self):
        """
        Use this if you want to do nothing when there is an expection
        """
        return