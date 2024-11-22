# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file to perform AzureCompute Operations

AzureCompute:

    __init__()                    --  Initializes instance of AzureCompute class with azure App credentials

    get_all_virtual_machines()    --  Retrives the virtual machines list under a resource group

    get_virtual_machine_details() --  Retrives the virtual machine details

    get_virtual_machine_instance_details()  --  Retrives the virtual machine instance view details

    start_virtual_machine()           -- starts the virtual machine

    deallocate_virtual_machine()      -- Shuts down the virtual machine

    get_virtual_machine_status()      -- Retrives the virtual machine running status

    get_VM_scale_set_details()        -- Retrives the virtual machine scale set details

    get_VM_scale_set_instances_list() -- Retrives the virtual machine scale set instances list

    get_VM_scale_set_instances_ids()  -- Retrives the virtual machine scale set instances ids

    get_VM_scale_set_VM_instance_status() -- Retrives the provisioning status of virtual machine scale set instance

    compare_registry()                --    compares iDataAgent registry settings of Instance with co-ordinator machine registry

"""

from AutomationUtils.machine import Machine
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from AutomationUtils import logger

class AzureCompute:
    """ Helper class to perform Azure SDK common operations of Compute"""

    def __init__(self,tc_object):
        """ Initializes instance of AzureHelper class with azure App credentials """
        self.log = logger.get_log()
        self.tc_object = tc_object
        self.tc_inputs = self.tc_object.tcinputs
        self.subscription_id = self.tc_inputs['Azure_SubscriptionID']
        self.credential = None
        self.client = None

        try:
            self.credential = ClientSecretCredential(
                client_id=self.tc_inputs['Azure_ApplicationID'],
                client_secret=self.tc_inputs['Azure_ApplicationSecret'],
                tenant_id=self.tc_inputs['Azure_TenantID']
            )
            if self.subscription_id is not None:
                self.client = ComputeManagementClient(
                    self.credential, self.subscription_id)
                self.log.info("ComputeManagementClient Object creation successful.")
            else:
                raise Exception("Please provide valid Azure subscription ID")

        except Exception as exp:
            self.log.exception("ComputeManagementClient Object creation failed.")
            raise exp

    def _process_registry_response(self,registry):
        """
         processes the registry response and returns dictionary of registry key and value
         Args:
             registry(str) : registry
         """
        registry = registry.split("\r\n")
        registry = [x for x in registry if x!='']
        reg_list=[]
        j=0
        for x in registry:
            if not str(x).startswith(' '):
                reg_list.insert(j,x.strip())
                j+=1
            else:
                reg_list[j-1] = reg_list[j-1] + str(x.lstrip())
        reg_dict ={}
        for x in reg_list:
            temp_list = [i for i in x.split(':',1)]
            reg_dict[temp_list[0].rstrip()] = temp_list[1].lstrip()
        return reg_dict

    def __compare_registry_with_compute(self):
        """
         compares iDataAgent registry settings of Instance with co-ordinator machine registry.
         The iDataAgent registry file of coordinator should be provided as input.
        """
        reg_file=open(self.tc_inputs["registry_file_path"],encoding="utf-16")
        reg_list=[x for x in reg_file.read().split("\n") if x!='']
        reg_list=reg_list[2:]
        cord_reg_dict={}
        for item in reg_list:
            temp_list=item.split("=")
            if "dword" in temp_list[1]:
                sp_list=temp_list[1].split(":")
                val=int(sp_list[1],16)
                cord_reg_dict[temp_list[0].replace('"','')]=str(val)
            else:
                cord_reg_dict[temp_list[0].replace('"','')] = temp_list[1].replace('"','')

        extra_keys = ['PSChildName','PSProvider','PSParentPath','PSPath']
        ida_local_path_keys = ['sDocumentationLink','dCONFIGDIR', 'dHOME', 'sCCSDbPath']
        for key in ida_local_path_keys:
            cord_reg_dict.pop(key)
        extra_keys.append('RunspaceId')
        instance_list=self.get_VM_scale_set_instances_list(self.tc_inputs["VM_Scale_Set"])
        for instance in instance_list:
            instance_machine_obj = Machine(machine_name=instance,username=self.tc_inputs["domain_username"],password=self.tc_inputs["domain_password"])
            instance_machine_reg = instance_machine_obj.get_registry_entries_for_subkey(
                "REGISTRY::HKEY_LOCAL_MACHINE\\SOFTWARE\\CommVault Systems\\Galaxy\\Instance001\\iDataAgent", recurse=False)
            ins_reg_dict = self._process_registry_response(instance_machine_reg)
            for key in extra_keys:
                ins_reg_dict.pop(key)
            for key in ida_local_path_keys:
                ins_reg_dict.pop(key)
            if cord_reg_dict == ins_reg_dict:
                self.log.info('iDataAgent Registry Matched for %s instance',instance)
            else:
                raise Exception('iDataAgent Registry Not Matched for %s instance',instance)

    def __fetch_all_virtual_machines(self):
        """Retrives the virtual machines list under a resource group"""
        machine_list=[]
        response = self.client.virtual_machines.list(
            resource_group_name=self.tc_inputs["Azure_VM_Resource_Group_Name"],
        )
        page_iterator=response.by_page()
        for page in page_iterator:
            for machine in page:
                machine_list.append(machine.name)
        return machine_list

    def __fetch_virtual_machine_details(self,virtual_machine, instance_view=False):
        """
        Retrives the virtual machine details
        Args:
            virtual_machine(str) : name of virtual machine
        """
        if instance_view:
            response = self.client.virtual_machines.get(
                resource_group_name=self.tc_inputs["Azure_VM_Resource_Group_Name"],
                vm_name=virtual_machine,
                expand="instanceView"
            )
            return response.instance_view
        else:
            response = self.client.virtual_machines.get(
                resource_group_name=self.tc_inputs["Azure_VM_Resource_Group_Name"],
                vm_name=virtual_machine,
            )
            return response

    def __begin_start_virtual_machine(self, virtual_machine):
        """
        starts the virtual machine
        Args:
            virtual_machine(str) : name of virtual machine
        """
        response = self.client.virtual_machines.begin_start(
            resource_group_name=self.tc_inputs["Azure_VM_Resource_Group_Name"],
            vm_name=virtual_machine,
        )
        return response

    def __begin_deallocate_virtual_machine(self, virtual_machine):
        """
        Shuts down the virtual machine
        Args:
            virtual_machine(str) : name of virtual machine
        """
        response = self.client.virtual_machines.begin_deallocate(
            resource_group_name=self.tc_inputs["Azure_VM_Resource_Group_Name"],
            vm_name=virtual_machine,
        )
        return response

    def __fetch_VM_scale_set_details(self, scale_set):
        """
        Retrives the virtual machine scale set details
        Args:
            scale_set(str) : name of scale set
        """
        response = self.client.virtual_machine_scale_sets.get(
            resource_group_name=self.tc_inputs["Azure_Scale_Set_Resource_Group_Name"],
            vm_scale_set_name=scale_set,
        )
        return response

    def __fetch_VM_scale_set_instances_list(self, scale_set, instance_ids=False):
        """
        Retrives the virtual machine scale set instances list
        Args:
            scale_set(str) : name of scale set
        """
        if instance_ids:
            instance_ids = {}
            response = self.client.virtual_machine_scale_set_vms.list(
                resource_group_name=self.tc_inputs["Azure_Scale_Set_Resource_Group_Name"],
                virtual_machine_scale_set_name=scale_set,
            )
            page_iterator = response.by_page()
            for page in page_iterator:
                for machine in page:
                    instance_ids[machine.os_profile.computer_name] = machine.instance_id
            return instance_ids
        else:
            instance_list=[]
            response = self.client.virtual_machine_scale_set_vms.list(
                resource_group_name=self.tc_inputs["Azure_Scale_Set_Resource_Group_Name"],
                virtual_machine_scale_set_name=scale_set,
            )
            page_iterator = response.by_page()
            for page in page_iterator:
                for machine in page:
                    instance_list.append(machine.os_profile.computer_name)
            return instance_list

    def __fetch_VM_scale_set_VM_instance_status(self,scale_set, instance_id):
        """
        Retrives the virtual machine running status in VMSS
        Args:
            scale_set(str) : name of scale set
            instance_id(str) : instance id
        """
        response = self.client.virtual_machine_scale_set_vms.get_instance_view(
            resource_group_name=self.tc_inputs["Azure_VM_Resource_Group_Name"],
            vm_scale_set_name=scale_set,
            instance_id=instance_id
        )
        return response.statuses[0].display_status

    def get_all_virtual_machines(self):
        """Retrives the virtual machines list under a resource group"""
        return self.__fetch_all_virtual_machines()

    def get_virtual_machine_details(self,virtual_machine,instance_view=False):
        """
        Retrives the virtual machine details
        Args:
            virtual_machine(str) : name of virtual machine
        """
        return self.__fetch_virtual_machine_details(virtual_machine=virtual_machine,instance_view=instance_view)

    def start_virtual_machine(self,virtual_machine):
        """
         starts the virtual machine
            Args:
                virtual_machine(str) : name of virtual machine
        """
        return self.__begin_start_virtual_machine(virtual_machine)

    def deallocate_virtual_machine(self, virtual_machine):
        """
        Shuts down the virtual machine
        Args:
            virtual_machine(str) : name of virtual machine
        """
        return self.__begin_deallocate_virtual_machine(virtual_machine)

    def get_virtual_machine_status(self, virtual_machine):
        """
        Retrives the virtual machine running status
        Args:
            virtual_machine(str) : name of virtual machine
        """
        response = self.__fetch_virtual_machine_details(virtual_machine=virtual_machine,instance_view=True)
        return response.statuses[1].display_status

    def get_VM_scale_set_details(self, scale_set):
        """
        Retrives the virtual machine scale set details
        Args:
            scale_set(str) : name of scale set
        """
        return self.__fetch_VM_scale_set_details(scale_set)

    def get_VM_scale_set_instances_list(self, scale_set,instance_ids=False):
        """
        Retrives the virtual machine scale set instances list
        Args:
            scale_set(str) : name of scale set
        """
        return self.__fetch_VM_scale_set_instances_list(scale_set=scale_set,instance_ids=instance_ids)

    def get_VM_scale_set_VM_instance_status(self,scale_set, instance_id):
        """
        Retrives the virtual machine running status in VMSS
        Args:
            scale_set(str) : name of scale set
            instance_id(str) : instance id
        """
        self.__fetch_VM_scale_set_VM_instance_status(scale_set,instance_id)

    def compare_registry(self):
        """
         compares iDataAgent registry settings of Instance with co-ordinator machine registry.
         The iDataAgent registry file of coordinator should be provided as input.
        """
        return self.__compare_registry_with_compute()