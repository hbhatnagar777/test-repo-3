from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for submitting full vm restore for all hypervisors

Classes:

    FullVMRestore() --- > _Navigator() ---> AdminConsoleBase() ---> Object()

FullVMRestore --  This class contains methods for submitting full vm restore.

Functions:

    full_vm_restore()       --  Submits a VMware full VM restore to a specified
                                destination server

    hv_full_vm_restore()    --  Submits a hyper V full VM restore to a hyperV server

    opc_full_vm_restore()   --  Submits a full VM restore of an Oracle Cloud instance

    ali_cloud_full_vm_restore() --  Submits a full VM restore of an Alibaba Cloud instance

    amazon_full_vm_restore() --  Submits a full VM restore of an Amazon Cloud instance

    select_availability_zone() -- Selects a given availability zone

"""

import re
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import logger
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from Web.AdminConsole.Components.panel import DropDown, ModalPanel, RPanelInfo
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.Common.page_object import (
    WebAction,
    PageService
)


class FullVMRestore:
    """
    This class contains methods for submitting full vm restore.
    """

    def __init__(self, admin_console):
        """ Init for FullVMRestore class"""
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__browse_obj = RBrowse(admin_console)
        self.__modal_panel_obj = ModalPanel(admin_console)
        self.__panel_info_obj = RPanelInfo(admin_console)
        self.log = logger.get_log()

    @WebAction()
    def __select_subnet(self, subnet_id):
        """
        Selects the subnet based on OCID of subnet
        :return: None
        """
        subnet_index = 1
        sn_xpath = f'//*[@id="subnetSettings"]/option[contains(@value,"{subnet_id}")]'
        while True:
            xpath_select = f'//*[@id="networkSettings"]/option[{subnet_index}]'
            if self.__admin_console.check_if_entity_exists("xpath", xpath_select):
                self.__driver.find_element(By.XPATH, xpath_select).click()
                self.__admin_console.wait_for_completion()
                if self.__admin_console.check_if_entity_exists("xpath", sn_xpath):
                    self.__driver.find_element(By.XPATH, sn_xpath).click()
                    break
            else:
                break
            subnet_index += 1

    @WebAction()
    def __check_restore_options_modal_exists(self):
        """Checks if entity exists for restore"""
        return self.__admin_console.check_if_entity_exists("xpath", '//div[@id="virtualizationBrowse"]'
                                                                    '//div[contains(@class, "wizard")]')

    @WebAction()
    def __click_restore(self):
        """Initiates restore process by clicking on restore"""
        self.__panel_info_obj.click_button(self.__admin_console.props['header.restore'])

    @WebAction()
    def __send_vm_name(self, vm_restore_name):
        """Enters the VM Restore Name in the input element
        Args:
                        vm_restore_name:     the name of the VM to restore
        Returns:
        """
        _xp = "//*[@id='perVmOptions']//label[@for='displayName']/input"
        self.__driver.find_element(By.XPATH, _xp).clear()
        self.__driver.find_element(By.XPATH, _xp).send_keys(vm_restore_name)

    @WebAction()
    def __select_vm_options(self, vm_name):
        """Selects VM by vm_name
                Args:
                                vm_name:     the name of the VM to restore
                Returns:
        """
        xpath = f"//a[text()='{vm_name}']"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __select_vm_from_list(self, vm_name):
        """Selects VM by vm_name
                Args:
                                vm_name:     the name of the VM to restore
                Returns:
        """
        xpath = f"//ul[@class='vm-full-restore-list']//a[contains(text(), '" + vm_name + "')]"
        self.__driver.find_element(By.XPATH, xpath).click()

    def submit_restore_from_react_screen(self, restore_options):
        """
        initiate the restore process and help flow the code
        Returns:
            restore job
        """
        from Web.AdminConsole.VSAPages.RestoreScreens import Destination, VirtualMachines, RestoreOptions, Summary
        restore_wizard = Wizard(self.__admin_console)
        restore_submitted = False
        job_id = None
        while not restore_submitted:
            current_restore_step = restore_wizard.get_active_step()
            if current_restore_step == 'Destination':
                Destination.Destination(restore_wizard, restore_options, self.__admin_console)
            elif current_restore_step == 'Virtual Machines':
                VirtualMachines.VirtualMachines(restore_wizard, restore_options, self.__admin_console)
            elif current_restore_step == 'Restore Options':
                RestoreOptions.RestoreOptions(restore_wizard, restore_options, self.__admin_console)
                if restore_options.end_user:
                    job_id = self.__admin_console.get_jobid_from_popup()
                    restore_submitted = True
            elif current_restore_step == 'Summary':
                Summary.Summary(restore_wizard)
                job_id = self.__admin_console.get_jobid_from_popup()
                restore_submitted = True
        return job_id

    @PageService()
    def full_vm_restore(
            self,
            vms_to_restore,
            inplace=False,
            restore_as="VMware vCenter",
            proxy=None,
            destination_server=None,
            vm_info=None,
            different_vcenter=False,
            different_vcenter_info={},
            disk_prov=None,
            transport_mode=None,
            power_on=True,
            over_write=True,
            live_recovery=False,
            live_recovery_options={},
            hv_restore_options={},
            restore_to_recovery_target=False,
            passkey=None,
            live_recovery_restore_type= False
    ):
        """
        Submits a VMware full VM restore to a specified destination server

        Args:
            vms_to_restore           (list)  --  list of all Vms to restore

            inplace                  (bool)  --  if the VM needs to be restored in place

            restore_as               (str)   --  the hypervisor to be restored to
                    default :   VMware vCenter

            proxy                    (str)   --  the proxy to be used for restore

            destination_server       (str)   --  the name of the destination hypervisor

            vm_info                  (dict)  --  dict containing each restore VM details
                        vm_info = { 'VM1':  {   'host':'abc', 'datastore':'ds1', 'respool':'rp1',
                                                'network': {'source': 'network1',
                                                            'destination':'nw2'},
                                                'IP': { 'sourceIP':'','sourceSubnet':'',
                                                        'sourceGateway':'',
                                                        'DHCP':False,
                                                        'destinationIP':'', 'desitnaionSubnet':'',
                                                        'destinationGateway':'',
                                                        'destinationPreDNS':'',
                                                        'destinationAltDNS':'',
                                                        'destinationPrefWins':'',
                                                        'destinationAltWins':''}

            different_vcenter        (bool)  --  True / False to create a new vcenter client

            different_vcenter_info   (dict)  --  dict containing the new vcenter info
                        different_vcenter_info = {  'vcenter_hostname':'newvCenter',
                                                    'vcenter_username':'username',
                                                    'vcenter_password':'password'   }

            disk_prov                (str) --  the disk provisioning of the restore vm disks

            transport_mode           (str)   --  the transport mode to be used for restore

            power_on                 (bool)  --  if the restored VM needs to be powered on

            over_write               (bool)  --  if the restored VM needs to be overwritten

            live_recovery            (bool)  --  if the restore needs to use live recovery

            live_recovery_options    (dict)  --  live recovery options
                        live_recovery_options = {   'redirect_datastore':'ds1',
                                                    'delay_migration':'2'   }

            hv_restore_options       (dict)  --  all the restore options needed to restore
                                                    VMware VM as Hyper-V VM

            restore_to_recovery_target  (bool) -- if restore has to be done to recovery target

            passkey                  (str)  --  Passkey for restore

            live_recovery_restore_type  (bool)  --  If live recovery restore is from the VM level restore option

        Returns:
            job_id      (str)   --  the restore job ID

        """
        self.__admin_console.wait_for_completion()
        if different_vcenter_info is None:
            different_vcenter_info = {}
        self.__admin_console.log.info("Selecting VMs for performing Full VM restore")
        vm_list = vms_to_restore

        if passkey:
            passkey_dialog = ModalDialog(self.__admin_console)
            self.__admin_console.fill_form_by_id("passkeyAuthInput", passkey)
            passkey_dialog.click_submit()
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()

        if not self.__check_restore_options_modal_exists():
            self.__browse_obj.select_files(file_folders=vm_list)
            self.__driver.execute_script("window.scrollTo(0,0)")
            self.__click_restore()
            self.__admin_console.wait_for_completion()
        from VirtualServer.VSAUtils.OptionsHelper import VMwareWebRestoreOptions
        vmware_options = VMwareWebRestoreOptions()
        vmware_options.vm_info = vm_info
        if inplace:
            vmware_options.restore_type = 'In place'
        else:
            vmware_options.restore_type = 'Out of place'
            vmware_options.restore_as = restore_as
            vmware_options.destination_hypervisor = destination_server
            vmware_options.prefix = vm_info[list(vm_info.keys())[0]].get('prefix')
        vmware_options.access_node = proxy
        vmware_options.power_on_after_restore = power_on
        vmware_options.unconditional_overwrite = over_write
        vmware_options.transport_mode = transport_mode
        vmware_options.disk_provisioning = disk_prov
        vmware_options.use_live_recovery = live_recovery
        vmware_options.live_recovery_restore_type = live_recovery_restore_type
        vmware_options.restore_to_recovery_target = restore_to_recovery_target
        vmware_options.different_vcenter = different_vcenter
        vmware_options.different_vcenter_info = different_vcenter_info
        if live_recovery:
            vmware_options.live_recovery_datastore = live_recovery_options.get('redirect_datastore', None)
            vmware_options.live_recovery_delay_migration = live_recovery_options.get('delay_migration', None)
        restore_job_id = self.submit_restore_from_react_screen(restore_options=vmware_options)
        return restore_job_id

    @PageService()
    def hv_full_vm_restore(
            self, instance_list, destination_client, destination_proxy,
            power_on, overwrite_instance, in_place=False,
            restore_prefix=None, restore_suffix=None,
            instance_options=None,
            use_live_recovery=False,
            register_during_failover=False,
            location=None,
            restore_network=None

    ):
        """
        Submits a hyper V full VM restore to a hyperV server

        Args:
            instance_list      (str)   --  the name of the VM to restore

            destination_client       (str)   --  the hypervisor server to restore to

            destination_proxy        (str)   --  the name of the proxy to be used for restore

            power_on     (bool)  --  if the restored VM has to be powered on

            overwrite_instance   (bool)  --  if the restored VM has to overwrite an existing VM

            in_place     (bool) --  Whether the restore will be in-place or out of place

            restore_prefix  (str)   -- Prefix to be prepended to the restored VM name

            restore_suffix  (str)   -- Suffix to be appended to the restored VM name

            instance_options    (dict):         restore options for each individual instanc


            use_live_recovery   (bool)  -- if the restore needs to use live recovery

            register_during_failover     (bool)  --  if the restored VM has to be registered to cluster

            restore_network      (str)   --  if a network card has to be attached to the VM

        Returns:
            job_id      (str)   --  the restore job ID


        """
        from VirtualServer.VSAUtils.OptionsHelper import HVWebRestoreOptions

        hv_restore_options = HVWebRestoreOptions()
        hv_restore_options.vm_info = instance_options

        if in_place:
            hv_restore_options.restore_type = 'In place'
        else:
            hv_restore_options.restore_type = 'Out of place'

            hv_restore_options.destination_hypervisor = destination_client
            if restore_prefix:
                hv_restore_options.prefix = restore_prefix
            if restore_suffix:
                hv_restore_options.suffix = restore_suffix

        hv_restore_options.access_node = destination_proxy
        hv_restore_options.power_on_after_restore = power_on
        hv_restore_options.unconditional_overwrite = overwrite_instance
        hv_restore_options.register_during_failover = register_during_failover
        hv_restore_options.use_live_recovery = use_live_recovery

        if not self.__admin_console.check_if_entity_exists("xpath", "//div[contains(@class, 'modal-dialog')]"
                                                                    "//h1[contains(text(),'Restore options')]"):
            self.__browse_obj.select_files(instance_list)
            self.__click_restore()
            self.__admin_console.wait_for_completion()
        restore_job_id = self.submit_restore_from_react_screen(restore_options=hv_restore_options)
        return restore_job_id

    @PageService()
    def opc_full_vm_restore(self, vm_list, proxy, server, power_on, restore_prefix,
                            user_account, shape, network_list=None,
                            security_groups=None, ssh_keys=None):
        """
        Full instance restore method for Oracle Public Cloud
        Args:
            vm_list             (list)  --  the list of all VMs to restore

            proxy               (str)   --  the proxy to be used for restore

            server              (str)   --  the oracle cloud server to restore to

            power_on            (bool)  --  True / False to power on the instance

            restore_prefix      (str)   --  The string to be prefixed to the VM name

            user_account        (str)   --  The user account where instances are to restored

            shape               (str)   --  The shape of the restore instances

            network_list        (list)  --  List of all networks to be associated to instances

            security_groups     (list)  --  List of all security groups to be associated

            ssh_keys            (list)  --  List of all ssh keys to be associated

        Returns:
            job_id  (str)   --  the restore job ID

        """
        if not self.__admin_console.check_if_entity_exists("xpath",
                                                           "//div[@class='modal fade ng-isolate-scope in']"):
            self.__browse_obj.select_files(file_folders=vm_list)
            self.__click_restore()
            self.__admin_console.wait_for_completion()

        self.__admin_console.select_value_from_dropdown("Destination hypervisor", server, search=True)
        if self.__admin_console.check_if_entity_exists("id", "destinationProxy"):
            self.__admin_console.select_value_from_dropdown("destinationProxy", proxy)

        if power_on:
            self.__admin_console.checkbox_select("powerOn")
        else:
            self.__admin_console.checkbox_deselect("powerOn")

        for vm_name in vm_list:
            restore_vm_name = restore_prefix + vm_name
            if len(vm_list) != 1:
                self.__driver.find_element(By.XPATH, "//ul[@class='vm-full-restore-list']//a["
                                                     "contains(text(),'" + vm_name + "')]").click()
                self.__admin_console.wait_for_completion()

                # Since there are multiple instances to restore, over writing the shape to Auto
                shape = "Auto"

            self.__driver.find_element(By.XPATH, "//*[@id='perVmOptions']//label["
                                                 "@for='displayName']/input").clear()
            self.__driver.find_element(By.XPATH, "//*[@id='perVmOptions']//label["
                                                 "@for='displayName']"
                                                 "/input").send_keys(restore_vm_name)
            self.__admin_console.wait_for_completion()

            self.__driver.find_element(By.XPATH,
                                       "//button[@class='btn btn-default browse-btn']").click()
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()

            self.__admin_console.select_destination_host(user_account)
            self.__admin_console.submit_form()
            self.__admin_console.log.info("User account selected")

            self.__admin_console.select_value_from_dropdown("instanceType", shape)
            self.__admin_console.log.info("Instance shape selected")

            if network_list:
                self.__admin_console.cvselect_from_dropdown('Network', network_list)
                self.__admin_console.log.info("Selected the networks")

            if security_groups:
                self.__admin_console.cvselect_from_dropdown('Security groups', security_groups)
                self.__admin_console.log.info("Selected the security groups")

            if ssh_keys:
                self.__admin_console.cvselect_from_dropdown('SSH keys', ssh_keys)
                self.__admin_console.log.info("Selected the ssh keys")

            self.__admin_console.log.info("Going to submit restore job")
            self.__admin_console.wait_for_completion()
            self.__driver.find_element(By.XPATH, "//div[@class='local-options']/form/div[2]/button["
                                                 "contains(text(),'Submit')]").click()

            return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def ali_cloud_full_vm_restore(self, instance_list, destination_client, destination_proxy,
                                  power_on, overwrite_instance, in_place=False,
                                  restore_prefix=None, restore_suffix=None,
                                  instance_options=None):
        """
        Performs a full instance restore to Ali Cloud

        Args:
            instance_list       (list):         list of all instances to restore

            destination_client  (str):   the destination client where instances are to
                                                be restored

            destination_proxy   (str):   the proxy to be used for restore

            power_on            (bool):         if the instances are to be powered on after restore

            overwrite_instance  (bool):         to overwrite existing instances

            restore_prefix      (str):   to prepend a prefix to source instance name

            restore_suffix      (str):   to append a suffix to a source instance name

            in_place            (bool):         to restore the instances in-place

            instance_options    (dict):         restore options for each individual instance

                    Sample dict:    {'instance1':   {   'availability_zone': '',
                                                        'instance_type: '',
                                                        'network':  '',
                                                        'security_groups':  ['group1', 'group2']
                                                    },
                                    'instance2':   {   'availability_zone': '',
                                                        'instance_type: '',
                                                        'network':  '',
                                                        'security_groups':  ['group1', 'group2']
                                                    }
                                    }

        Raises:
            Exception:
                if there is an error with submitting Ali Cloud Full instance restore

        Returns:
            job_id  (str):   the restore job ID

        """
        from VirtualServer.VSAUtils.OptionsHelper import AlicloudWebRestoreOptions
        alicloud_options = AlicloudWebRestoreOptions()
        alicloud_options.vm_info = instance_options
        if in_place:
            alicloud_options.restore_type = 'In place'
        else:
            alicloud_options.restore_type = 'Out of place'
            alicloud_options.destination_hypervisor = destination_client
            if restore_prefix:
                alicloud_options.prefix = restore_prefix
            if restore_suffix:
                alicloud_options.suffix = restore_suffix
        alicloud_options.access_node = destination_proxy
        alicloud_options.power_on_after_restore = power_on
        alicloud_options.unconditional_overwrite = overwrite_instance
        display_name = None

        if not self.__check_restore_options_modal_exists():
            self.__browse_obj.select_files(instance_list)
            self.__click_restore()
            self.__admin_console.wait_for_completion()

        restore_job_id = self.submit_restore_from_react_screen(restore_options=alicloud_options)
        return restore_job_id

    @PageService()
    def azure_full_vm_restore(self, vm_list, proxy, server, in_place, vm_info,
                              create_public_ip=False, over_write=False, power_on=False,
                              managed_vm=False, restore_prefix=None, extension_restore_policy="Restore VM extensions"):

        """
        Performs a full VM restore for Azure RM
        Args:
            instance_list    (list):        list of all instances to restore

            vm_list          (list):        the name of the VM to restore

            proxy            (str):         the name of the proxy to be used for restore

            power_on         (bool):        if the restored VM has to be powered on

            param over_write (bool):        if the restored VM has to overwrite an
                                            existing VM
            server           (str) :        server name with each restore to be done

            vm_info          (dict):        contains:azure_container,azure_vmsize,
                                            storageAccount,azure_vmnetwork

            extension_restore_policy(str):  specifies whether VM Extensions have to be restored at various levels

            managed_vm       (bool):      False

            create_public_ip (bool):      False

            restore_prefix   (str):     Restore prefix

            over_write       (bool):    False

            in_place         (bool):    True if you need in-place restore

        Returns:
            job_id  (str):   the restore job ID

        """
        self.__browse_obj.select_files(file_folders=vm_list)
        self.__click_restore()
        self.__admin_console.wait_for_completion()
        if not proxy:
            proxy = "Automatic"

        from VirtualServer.VSAUtils.OptionsHelper import AzureWebRestoreOptions
        azure_options = AzureWebRestoreOptions()
        azure_options.vm_info = vm_info

        if in_place:
            azure_options.restore_type = 'In place'
        else:
            azure_options.restore_type = 'Out of place'
            azure_options.prefix = restore_prefix
            azure_options.destination_hypervisor = server
            azure_options.access_node = proxy
            azure_options.power_on_after_restore = power_on
            azure_options.unconditional_overwrite = over_write
            azure_options.extension_restore_policy = extension_restore_policy

        restore_job_id = self.submit_restore_from_react_screen(restore_options=azure_options)
        return restore_job_id

    @PageService()
    def vcloud_full_vm_restore(self, vm_list, proxy, destination_server, in_place, vm_info, org_vdc,
                               power_on=True, overwrite=False, standalone=False,
                               restore_vapp=True, restore_prefix=None):

        """
        Performs a full VM restore for vCloud VM
        Args:
            vm_list                 (list):     the name of the VM to restore

            proxy                   (str):      the name of the proxy to be used for restore

            destination_server      (str) :     server name with each restore to be done

            in_place                (str):      the type of restore to be performed

            vm_info                 (list):     contains:vapp_name ,source network

            org_vdc                 (str) :     VDC name to be used for destination VM

            power_on                (bool):     if the restored VM has to be powered on

            overwrite               (bool):     if the restored VM has to overwrite an
                                                existing VM

           restore_prefix           (str):     Restore prefix

           restore_vapp             (bool):     True

           standalone                (bool):   Restores a Vm as a standalone Vm if set to True

        Returns:
            job_id  (str):   the restore job ID

        """

        self.__admin_console.wait_for_completion()

        if not self.__check_restore_options_modal_exists():
            self.__browse_obj.select_files(file_folders=vm_list)
            self.__driver.execute_script("window.scrollTo(0,0)")
            self.__click_restore()
            self.__admin_console.wait_for_completion()

        from VirtualServer.VSAUtils.OptionsHelper import VCloudWebRestoreOptions

        init_data = {
            "restore_type": 'In place' if in_place else 'Out of place',
            "prefix": restore_prefix,
            "destination_hypervisor": destination_server,
            "power_on_after_restore": power_on,
            "unconditional_overwrite": overwrite,
            "vm_info": vm_info,
            "org_vdc": org_vdc,
            "access_node": proxy,
            "standalone": standalone
        }

        vcd_options = VCloudWebRestoreOptions(init_data=init_data)
        return self.submit_restore_from_react_screen(restore_options=vcd_options)
    @PageService()
    def fusioncompute_full_vm_restore(self, vm_list, proxy, destination_server, in_place, vm_info, power_on, overwrite,
                                      restore_prefix):
        """
        Performs Full VM Restore for FusionCompute

        Args:
            ...
        """
        self.__admin_console.wait_for_completion()

        if not self.__check_restore_options_modal_exists():
            self.__browse_obj.select_files(file_folders=vm_list)
            self.__driver.execute_script("window.scrollTo(0,0)")
            self.__click_restore()
            self.__admin_console.wait_for_completion()

        from VirtualServer.VSAUtils.OptionsHelper import FusionComputeWebRestoreOptions

        init_data = {
            "restore_type": 'In place' if in_place else 'Out of place',
            "destination_hypervisor": destination_server,
            "power_on_after_restore": power_on,
            "unconditional_overwrite": overwrite,
            "vm_info": vm_info,
            "access_node": proxy,
            "prefix": restore_prefix
        }

        vcd_options = FusionComputeWebRestoreOptions(init_data=init_data)

        return self.submit_restore_from_react_screen(restore_options=vcd_options)

    @PageService()
    def oci_full_vm_restore(
            self,
            vms,
            proxy,
            destination_server,
            in_place,
            vm_restore_options,
            power_on=True,
            over_write=True,
            restore_as="Oracle Cloud Infrastructure",
            restore_prefix=None):
        """
                Performs a full VM restore for OCI VM
                Args:
                    vms                 (list/str):   List of all VMs to restore(For Parent Level Restore) or the name of the VM to restore(For VM Level Restore)

                    proxy                   (str):      the name of the proxy to be used for restore

                    destination_server      (str) :     Name of Destination Server - The Server to which the restore is to be done


                    in_place                (str):      the type of restore to be performed

                    vm_restore_options         (dict of dicts) : {VM1:{'availability_domain':'',
                                                                    'compartment_path':'',
                                                                    'shape':'',
                                                                    'vcn':'',
                                                                    'subnet':''
                                                                    }
                                                                }

                    power_on                (bool):     if the restored VM has to be powered on

                    over_write              (bool):     if the restored VM has to overwrite an existing VM
                    default : True

                    restore_prefix           (str):     Restore prefix

                    restore_as               (str):     the hypervisor to be restored to. Always 'Oracle Cloud Infrastructure' for oci_full_vm_restore
                Returns:
                    job_id  (str):   the restore job ID

                """
        from VirtualServer.VSAUtils.OptionsHelper import OCIWebRestoreOptions
        oci_options = OCIWebRestoreOptions()
        if in_place:
            oci_options.restore_type = 'In place'
        else:
            oci_options.restore_type = 'Out of place'
            oci_options.restore_as = restore_as
            oci_options.destination_hypervisor = destination_server
            if restore_prefix:
                oci_options.prefix = restore_prefix
        oci_options.access_node = proxy
        oci_options.power_on_after_restore = power_on
        oci_options.unconditional_overwrite = over_write
        if not self.__check_restore_options_modal_exists():
            oci_options.vm_info = vm_restore_options
            self.__browse_obj.select_files(file_folders=vms)
            self.__driver.execute_script("window.scrollTo(0,0)")
            self.__click_restore()
            self.__admin_console.wait_for_completion()
        else:
            oci_options.vm_info = {vms: vm_restore_options[vms]}
        restore_job_id = self.submit_restore_from_react_screen(restore_options=oci_options)
        return restore_job_id

    @PageService()
    def google_cloud_full_vm_restore(self,
                                     instance_list,
                                     destination_server,
                                     zone_name,
                                     project_id,
                                     subnet=None,
                                     network=None,
                                     restore_prefix=None,
                                     in_place=False,
                                     vm_info=None,
                                     proxy=None,
                                     power_on=True,
                                     overwrite_instance=False,
                                     restore_as='Google Cloud Platform', ):
        """
        Performs a full instance restore to Google Cloud.
        Args:
            instance_list       (list):         list of all instances to restore
            restore_prefix   (str):     Restore prefix
            in_place            (bool):         to restore the instances in-place
            proxy   (str):   the proxy to be used for restore
            power_on            (bool):         if the instances are to be powered on after restore
            overwrite_instance  (bool):         to overwrite existing instances
            instance_options    (dict):         restore options for each individual instance
                    Sample dict:    {'instance1':   {   'availability_zone': '',
                                                        'instance_type: '',
                                                        'network':  '',
                                                        'security_groups':  ['group1', 'group2']
                                                    },
                                    'instance2':   {   'availability_zone': '',
                                                        'instance_type: '',
                                                        'network':  '',
                                                        'security_groups':  ['group1', 'group2']
                                                    }
                                    }
        Raises:
            Exception:
                if there is an error with submitting Google Cloud Full instance restore
        Returns:
            job_id  (str):   the restore job ID
        """
        if not self.__admin_console.check_if_entity_exists("xpath",
                                                           "//div[@class='modal fade ng-isolate-scope in']"):
            self.__browse_obj.select_files(file_folders=instance_list)
            self.__click_restore()
            self.__admin_console.wait_for_completion()

        from VirtualServer.VSAUtils.OptionsHelper import GCPWebRestoreOptions
        gcp_options = GCPWebRestoreOptions()
        if in_place:
            gcp_options.restore_type = 'In place'
        else:
            gcp_options.restore_type = 'Out of place'
            gcp_options.restore_as = restore_as
            gcp_options.destination_hypervisor = destination_server
            gcp_options.prefix = restore_prefix 
        gcp_options.access_node = proxy
        gcp_options.power_on_after_restore = power_on
        gcp_options.unconditional_overwrite = overwrite_instance
        gcp_options.vm_info = vm_info
        gcp_options.zone_name = zone_name
        gcp_options.project_id_name = project_id
        gcp_options.instance_subnet = subnet
        gcp_options.instance_network = network
        gcp_options.suffix = ''

        print(f"gcp options : {gcp_options}")
        restore_job_id = self.submit_restore_from_react_screen(restore_options=gcp_options)
        return restore_job_id

    @PageService()
    def amazon_full_vm_restore(self,
                               vms_to_restore,
                               vm_info,
                               inplace=False,
                               restore_as=hypervisor_type.AMAZON_AWS.value,
                               proxy=None,
                               destination_server=None,
                               power_on=True,
                               over_write=True,
                               transport_mode=None,
                               restore_prefix='Del'):
        """
        Performs Amazon full VM restore
            Args:
                vms_to_restore  (list): VMs to restore
                vm_info         (dict): VM options used to restore
                inplace         (bool): True, if restore is in place
                restore_as      (string):Restored VM name
                proxy           (string): Access node to use
                destination_server  (string):   destination client
                power_on        (bool):True, if VM is to be powered ON
                over_write      (bool):True, if VM is to be overwritten
                transport_mode  (str): The transport mode to be used for restore
        Raises:
            Exception:
                if there is an error with submitting AWS Full instance restore
        Returns:
            job_id  (str):   the restore job ID
        """
        self.__admin_console.log.info("*" * 10 + "Performing full vm AWS restore" + "*" * 10)
        from VirtualServer.VSAUtils.OptionsHelper import AWSWebRestoreOptions
        aws_options = AWSWebRestoreOptions()
        aws_options.vm_info = vm_info
        if inplace:
            aws_options.restore_type = 'In place'
        else:
            aws_options.restore_type = 'Out of place'
            aws_options.restore_as = restore_as
            aws_options.destination_hypervisor = destination_server
            aws_options.prefix = restore_prefix
        if proxy:
            aws_options.access_node = proxy
        aws_options.transport_mode = transport_mode
        aws_options.power_on_after_restore = power_on
        aws_options.unconditional_overwrite = over_write
        self.__admin_console.log.info("Selecting VMs for performing Full VM restore")
        vm_list = vms_to_restore
        if not self.__check_restore_options_modal_exists():
            self.__browse_obj.select_files(file_folders=vm_list)
            self.__driver.execute_script("window.scrollTo(0,0)")
            self.__click_restore()
            self.__admin_console.wait_for_completion()
        else:
            aws_options.vm_info = {vm: aws_options.vm_info[vm] for vm in vm_list}
        restore_job_id = self.submit_restore_from_react_screen(restore_options=aws_options)
        return restore_job_id

    @WebAction()
    def __select_availability_zone(self, availability_zone):
        """
        Selects the given availability zone during restore

        availability_zone  (str) : Availability zone to select

        Returns: None
        """

        zones = self.__driver.find_elements(By.XPATH, '//span[@class="vsaIconLOADING vsaIconSERVERAMAZON"]')
        for zone in zones:
            if zone.find_element(By.XPATH, './../../span').text.strip() == availability_zone:
                zone.click()

    def fill_guest_credentials(self, vm_obj):
        """
        method to fill guest credentials for import based restores
        Args:
            vm_obj: instance of the backup vm
        """
        self.__admin_console.checkbox_select(checkbox_id='guestCredentials')
        self.__admin_console.fill_form_by_id(element_id='computerName', value=vm_obj['ip'])
        self.__admin_console.fill_form_by_id(element_id='userName', value=vm_obj['username'])
        self.__admin_console.fill_form_by_id(element_id='instanceAdminPassword', value=vm_obj['password'])

    @PageService()
    def xen_full_vm_restore(
            self,
            vm_list,
            inplace=False,
            proxy=None,
            destination_server=None,
            vm_info=None,
            power_on=True,
            over_write=True,
            dest_target=False
    ):
        """
        Submits a Xen full VM restore to the specified destination server

        Args:
            vms_list                    (list)  --  list of all VMs to restore

            inplace                     (bool)  --  if the VM needs to be restored in place

            proxy                       (str)   --  the proxy to be used for restore

            destination_server          (str)   --  the name of the destination hypervisor

            vm_info                     (dict)  --  dict containing each restore VM details
                                        vm_info = {
                                            "VM1": {
                                                "host": "xen_host",
                                                "datastore": "xen_SR",
                                                "prefix": "vm_prefix",
                                                "network": {
                                                    "destination": "dest_network"
                                                }
                                            }
                                        }

            power_on                    (bool)  --  if the restored VM needs to be powered on

            over_write                  (bool)  --  if the restored VM needs to be overwritten

            dest_target                 (bool) -- if restore has to be done to restore target

        Returns:
            job_id      (str)   --  the restore job ID
        """
        from VirtualServer.VSAUtils.OptionsHelper import XenWebRestoreOptions
        xen_restore_options = XenWebRestoreOptions()

        self.__browse_obj.select_files(file_folders=vm_list)
        self.__driver.execute_script("window.scrollTo(0,0)")
        self.__click_restore()
        self.__admin_console.wait_for_completion()

        if inplace:
            xen_restore_options.restore_type = 'In place'
        else:
            xen_restore_options.restore_type = 'Out of place'
            xen_restore_options.destination_hypervisor = destination_server
            xen_restore_options.prefix = vm_info[list(vm_info.keys())[0]].get('prefix')
        
        xen_restore_options.vm_info = vm_info
        xen_restore_options.access_node = proxy
        xen_restore_options.power_on_after_restore = power_on
        xen_restore_options.unconditional_overwrite = over_write

        restore_job_id = self.submit_restore_from_react_screen(restore_options=xen_restore_options)
        return restore_job_id

    @PageService()
    def nutanixahv_full_vm_restore(
            self, instance_list, destination_client, destination_proxy,
            power_on, overwrite_instance, in_place=False, instance_options=None,
            restore_network=None, storage_container=None, restore_prefix=None):
        """
        Submits a Nutanix AHV full VM restore to an AHV cluster

        Args:
            instance_list      (str)   --  the name of the VM to restore

            destination_client       (str)   --  the hypervisor server to restore to

            destination_proxy        (str)   --  the name of the proxy to be used for restore

            power_on     (bool)  --  if the restored VM has to be powered on

            overwrite_instance   (bool)  --  if the restored VM has to overwrite an existing VM

            in_place     (bool) --  Whether the restore will be in-place or out of place

            instance_options    (dict):         restore options for each individual instance

            restore_network      (str)   --  name of network card has to be attached to the VM

            storage_container    (str)   --  name of storage container to use for restored vm

            restore_prefix  (str)   -- Prefix to be prepended to the restored VM name

        Returns:
            job_id      (str)   --  the restore job ID


        """
        from VirtualServer.VSAUtils.OptionsHelper import NutanixAHVWebRestoreOptions

        ahv_restore_options = NutanixAHVWebRestoreOptions()
        ahv_restore_options.vm_info = instance_options

        if in_place:
            ahv_restore_options.restore_type = 'In place'
        else:
            ahv_restore_options.restore_type = 'Out of place'
            ahv_restore_options.destination_hypervisor = destination_client
            if restore_prefix:
                ahv_restore_options.prefix = restore_prefix

        ahv_restore_options.access_node = destination_proxy
        ahv_restore_options.power_on_after_restore = power_on
        ahv_restore_options.unconditional_overwrite = overwrite_instance
        ahv_restore_options.restore_network = restore_network
        ahv_restore_options.storage_container = storage_container
        ahv_restore_options.accessnode_partial_match = True

        if not self.__admin_console.check_if_entity_exists("xpath", "//div[contains(@class, 'modal-dialog')]"
                                                                    "//h1[contains(text(),'Restore options')]"):
            self.__browse_obj.select_files(instance_list)
            self.__click_restore()
            self.__admin_console.wait_for_completion()

        restore_job_id = self.submit_restore_from_react_screen(restore_options=ahv_restore_options)
        return restore_job_id
