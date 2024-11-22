

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Virtual Machines Section on the Restore Wizard of VSA Hypervisors

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
import re


class VirtualMachines:
    """
    class for handling virtual Machines section on restore wizard
    """
    def __init__(self, wizard, restore_options, admin_console):

        self.logger = None
        self.wizard = wizard
        self.__restore_options = restore_options
        self.__admin_console = admin_console
        self.log = admin_console.log
        self.config()

    def config(self):
        vms_table = Rtable(admin_console=self.__admin_console, id='FullVMRestoreVirtualMachine')
        vm_list = list(self.__restore_options.vm_info.keys())
        if self.__restore_options.type == HypervisorDisplayName.MS_VIRTUAL_SERVER:
            self.wizard.deselect_checkbox(checkbox_id='restoreToDefaultHost')
        if self.__restore_options.restore_type == 'Out of place':
            for vm in vm_list:
                vms_table.search_for(vm)
                if self.__restore_options.end_user:
                    self.edit_display_name(name=vm)
                    continue
                vms_table.select_all_rows()
                vms_table.access_toolbar_menu('Configure restore options')
                self.__restore_options.vm_info[vm]['name'] = vm
                self.configure_vm_restore_options(self.__restore_options.vm_info[vm])
                vms_table.clear_search()
        self.wizard.click_next()

    def configure_vm_restore_options(self, vm):
        """
        function to configure restore options for the vm
        Args:
            vm: (dict) restore options of the vm
        """
        self.log.info(f"In configure_vm_restore_options vm ==> {vm}")
        modal_title = 'Configure restore options for ' + vm.get('name')
        restore_options_dialog = RModalDialog(admin_console=self.__admin_console, title=modal_title)
        display_name = vm.get('name')
        if not getattr(self.__restore_options, 'restore_to_recovery_target', False):
            if self.__restore_options.prefix:
                display_name = self.__restore_options.prefix + vm.get('name')
            if self.__restore_options.suffix:
                display_name = display_name + self.__restore_options.suffix
            restore_options_dialog.fill_text_in_field(element_id='vmDisplayNameField', text=display_name)
        if self.__restore_options.type == HypervisorDisplayName.VIRTUAL_CENTER:
            if not self.__restore_options.restore_to_recovery_target:
                self.destination_host(restore_options_dialog, vm.get('host'))
                restore_options_dialog.select_dropdown_values(drop_down_id='storagePolicyDropdown',
                                                            values=[vm.get('vm_storage_policy')])
                restore_options_dialog.select_dropdown_values(drop_down_id='DataStoreDropdown',
                                                            values=[vm.get('datastore')])
                if vm.get('disk_ds_options') and vm.get('disk_ds_options').get(vm.get('name')):
                    self.disk_options(restore_options_dialog, vm.get('disk_ds_options').get(vm.get('name')))
                restore_options_dialog.select_dropdown_values(drop_down_id='resourcePoolDropdown',
                                                            values=[vm.get('respool')])
                self.destination_folder(restore_options_dialog, vm.get('Destination folder'))
                self.configure_network_settings(restore_options_dialog, vm.get('network'))
            if vm.get('custom_attributes_to_add'):
                self.configure_vmware_vm_custom_attributes(restore_options_dialog, vm.get('custom_attributes_to_add'), add=True)
            if vm.get('custom_attributes_to_remove'):
                self.configure_vmware_vm_custom_attributes(restore_options_dialog, vm.get('custom_attributes_to_remove'), add=False)
            if vm.get('tags_to_add'):
                self.configure_vmware_vm_tags(restore_options_dialog, vm.get('tags_to_add'), add=True)
            if vm.get('tags_to_remove'):
                self.configure_vmware_vm_tags(restore_options_dialog, vm.get('tags_to_remove'), add=False)
        elif self.__restore_options.type == HypervisorDisplayName.Alibaba_Cloud:
            self.availability_zone(restore_options_dialog=restore_options_dialog,
                                   availability_zone=vm.get('availability_zone', None))
            self.__admin_console.wait_for_completion()
            restore_options_dialog.select_dropdown_values(drop_down_id='instanceType', values=[vm.get('instance_type')])
            self.network(restore_dialog=restore_options_dialog, network=vm.get('network'))
            self.security_groups(restore_dailog=restore_options_dialog, security_groups=vm.get('security_groups'))
        elif self.__restore_options.restore_as == HypervisorDisplayName.Vcloud.value:
            self.vcloud_organization(restore_options_dialog, vm.get('organization', None))
            self.vcloud_org_vdc(restore_options_dialog, vm.get('org_vdc', None))
            if self.__restore_options.standalone:
                restore_options_dialog.toggle.enable(label='Restore as standalone VM')
            else:
                self.vcloud_vapp(restore_options_dialog, vm.get('vapp_name', None))
            restore_options_dialog.select_dropdown_values(drop_down_id='storagePolicyDropdown',
                                                          values=[vm.get('storage_profile')])
            if vm.get('owner', None):
                restore_options_dialog.select_dropdown_values(drop_down_id='usersDropdown',
                                                              values=[vm.get('owner')])
            if not vm.get('destination_network') == vm.get('source_network'):
                self.configure_network_settings(restore_options_dialog, {'destination': vm.get('destination_network')})

        elif self.__restore_options.type == HypervisorDisplayName.MS_VIRTUAL_SERVER:
            restore_options_dialog.select_dropdown_values(drop_down_id='hyperVDestination',
                                                          values=[vm.get('restore_host')],
                                                          case_insensitive=True)
            self.destination_folder(restore_options_dialog, vm.get('restore_path'))
            restore_options_dialog.select_dropdown_values(drop_down_id='hyperVNetworkAdapter', values=[vm.get('network')])

        elif self.__restore_options.type == HypervisorDisplayName.MICROSOFT_AZURE:
            self.log.info(f"selecting resource group : {vm.get('resource_group')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='resourceGroupDropdown',
                                                          values=[vm.get('resource_group')])

            self.log.info(f"selecting region : {vm.get('region')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='azureRegionDropdown', values=[vm.get('region')])

            self.log.info(f"selecting storage account : {vm.get('storage_account')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='storageAccountDropdown',
                                                          values=[vm.get('storage_account')])

            self.log.info(f"selecting security group : {vm.get('security_group')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='securityGroupDropdown',
                                                          values=[vm.get('security_group')],
                                                          partial_selection=True)

            self.log.info(f"selecting vm size : {vm.get('vm_size')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='vmSizeDropdown', values=[vm.get('vm_size')],
                                                          partial_selection=True)

            self.availability_zone(restore_options_dialog, vm.get('availability_zone'))
            self.edit_network_settings(vm.get('network_interface'), vm.get('create_public_ip'))

            self.log.info(f"selecting VM disk configuration options : {vm.get('storage_account')}, {vm.get('disk_option')}")
            self.azure_disk_options(vm.get('storage_account'), vm.get('disk_option'))

            self.enable_advanced_section(restore_options_dialog)

            if not vm.get('managed_vm', True):
                restore_options_dialog.disable_toggle(label="Restore as a managed VM")

            if vm.get('extension_restore_policy'):
                self.log.info(f"Selecting VM extenions restore policy : {vm.get('extension_restore_policy')}")
                restore_options_dialog.select_dropdown_values(drop_down_id='extensionRestorePolicy',
                                                          values=[vm.get('extension_restore_policy')])

            if vm.get('azure_key_vault', False):
                self.log.info(f"Selecting VM ADE Key vault : {vm.get('azure_key_vault')}")
                restore_options_dialog.select_dropdown_values(drop_down_id='keyVaultDropdown',
                                                              values=[vm.get('azure_key_vault')])
            else:
                self.log.info(f"Selecting VM disk encryption type : {vm.get('disk_encryption_type')}")
                restore_options_dialog.select_dropdown_values(drop_down_id='diskEncryptionTypeDropdown',
                                                          values=[vm.get('disk_encryption_type')])

            self.configure_tags(restore_options_dialog, vm.get('vm_tags'))

        elif self.__restore_options.type == HypervisorDisplayName.AMAZON_AWS:
            self.availability_zone(restore_options_dialog=restore_options_dialog,
                                   availability_zone=vm.get('availability_zone', None))
            restore_options_dialog.select_dropdown_values(drop_down_id='instanceType', values=[vm.get('Instancetype')])
            if vm.get('key_pair'):
                restore_options_dialog.select_dropdown_values(drop_down_id='keyPair', values=[vm.get('key_pair', 'No key pair')])
            if vm.get('restore_source_network', False):
                restore_options_dialog.toggle.enable(id='restoreSourceNetworkConfig')
            else:
                self.network(restore_dialog=restore_options_dialog, network=[vm.get('vpc').split('|')[0],
                                                                             vm.get('subnet').split('|')[0],
                                                                             vm.get('network_interface')])
                self.security_groups(restore_dialog=restore_options_dialog, security_groups=vm.get('security_group'))
            if not vm.get('volumeEdit'):
                self.log.info("No Volume Edit Options.")
            else:
                self.vm_disk_config(volumetype=vm.get('volumetype'), iops=vm.get('iops'), throughput=vm.get('throughput'), encryptionKey=vm.get('encryptionKey'))
            if vm.get('username') and vm.get('password'):
                self.specify_guest_credentials(restore_options_dialog, computer_name=vm.get('ip'),
                                               user_name=vm.get('username'), password=vm.get('password'))

        elif self.__restore_options.type == HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE:
            self.destination_host(restore_options_dialog, vm.get('compartment_path'))
            restore_options_dialog.select_dropdown_values(drop_down_id='availabilityDomain', values=[vm.get('availability_domain')])
            restore_options_dialog.select_dropdown_values(drop_down_id='vcn', values=[vm.get('vcn')])
            restore_options_dialog.select_dropdown_values(drop_down_id='subnet', values=[vm.get('subnet')])
            if vm.get('staging_bucket'):
                restore_options_dialog.select_dropdown_values(drop_down_id='stagingBucket', values=[vm.get('staging_bucket')])
            if vm.get('tags'):
                self.configure_oci_instance_tags(restore_options_dialog, vm.get('tags'))
        elif self.__restore_options.type == HypervisorDisplayName.FUSIONCOMPUTE:
            self.destination_host(restore_options_dialog, vm.get('destination_host'))
            restore_options_dialog.select_dropdown_values(drop_down_id='DataStoreDropdown',
                                                          values=[vm.get('datastore')])
            
        elif self.__restore_options.type == HypervisorDisplayName.Google_Cloud:
            self.log.info(f"Selecting Project and Zone : {vm.get('project_id')}, {vm.get('zone_name')}")
            self.project_and_zone(restore_options_dialog, vm.get("project_id"), vm.get("zone_name"))

            self.log.info(f"Selecting Machine Type : {vm.get('machine_type')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='machineTypeDropdown',
                                                          values=[vm.get("machine_type")])
            
            self.log.info(f"Selecting Network {vm.get('network')} and subnet : {vm.get('subnet')}")
            self.gcp_network_interface(restore_options_dialog, vm.get('network'), vm.get('subnet'))

            self.log.info(f"Selecting Service Account : {vm.get('service_account').get('displayName')}")
            restore_options_dialog.select_dropdown_values(drop_down_id='machineTypeDropdown',
                                                          values=[vm.get("service_account").get("displayName")],
                                                          partial_selection=True)
            
            self.log.info("Inserting Custom Metadata")
            self.gcp_advanced_options(restore_options_dialog, vm.get('custom_metadata'))

        elif self.__restore_options.type == HypervisorDisplayName.XEN_SERVER:
            self.configure_network_settings(restore_options_dialog, vm.get('network'))
        restore_options_dialog.click_submit()

    def gcp_advanced_options(self, restore_options_dialog, custom_metadata):
        """
        Select the advanced options
        Args:
           restore_options_dialog: (WebElement) : dailog model of the restore options
           custom_metadata: (str) : A dictionary of custom metadata  key and values

       """
        if custom_metadata:
            custom_metadata_list = [dict(item) for item in custom_metadata]
            self.enable_advanced_section(restore_options_dialog)
            restore_options_dialog.click_button_on_dialog(aria_label='Add', button_index=0)
            custom_metadata_modal = RModalDialog(self.__admin_console, title='Custom metadata')
            for custom_metadata_value in custom_metadata_list:
                custom_metadata_modal.fill_text_in_field(element_id="tagNameField", text=custom_metadata_value["name"])
                if custom_metadata_value.get("value"):
                    custom_metadata_modal.fill_text_in_field(element_id="tagValueField", text=custom_metadata_value["value"])
                custom_metadata_modal.click_button_on_dialog(text="Add")
            custom_metadata_modal.click_button_on_dialog(text="Save")

    def gcp_network_interface(self, restore_options_dialog, network, subnet):
        """
        Select the network_interface
        Args:
           restore_options_dialog: (WebElement) : dailog model of the restore options
           network (str) : Network name
           subnet  (str) : Subnet Name

        """
        if restore_options_dialog.check_if_button_exists(aria_label="Expand grid"):
            restore_options_dialog.click_button_on_dialog(aria_label="Expand grid")
        restore_options_dialog.click_button_on_dialog(text='Add', button_index=0)
        network_settings_modal = RModalDialog(self.__admin_console, title='Add network interface')
        network_settings_modal.click_button_on_dialog(button_index=1)
        self.__admin_console.wait_for_completion()
        network_interface_modal = RModalDialog(self.__admin_console, title="Network interface")
        network_tree_view = TreeView(self.__admin_console, xpath=network_interface_modal.base_xpath)
        network_tree_view.expand_path([network, subnet]) 
        network_interface_modal.click_button_on_dialog(text="Save")
        network_settings_modal.click_submit()


    def project_and_zone(self, restore_options_dialog, project_id, zone):
        """
        Select the project and zone
        Args:
           restore_options_dialog: (WebElement) : dailog model of the restore options
           project_id (str) : Destination Project Name
           zone  (str) : Destination zone Name

        """
        if not zone:
            self.log.info("Destination zone is not set")
        restore_options_dialog.click_button_on_dialog(button_index=1)
        self.__admin_console.wait_for_completion()
        restore_destination_modal = RModalDialog(admin_console=self.__admin_console, title='Select restore destination')
        destination_tree_view = TreeView(self.__admin_console, xpath=restore_destination_modal.base_xpath)
        destination_tree_view.expand_path([project_id, zone[0:-2], zone])
        restore_destination_modal.click_submit()

    def availability_zone(self, restore_options_dialog, availability_zone):
        """
        method to select availability zone on the page
        Args:
            restore_options_dialog: (Web Element) dialog modal
            availability_zone: (str) name of the zone
        """
        if not availability_zone:
            return
        if self.__restore_options.type == HypervisorDisplayName.MICROSOFT_AZURE:
            self.log.info(f"selecting availability zone : {availability_zone}")
            restore_options_dialog.select_dropdown_values(drop_down_id='availabilityZoneDropdown',
                                                          values=[availability_zone])
            return
        elif self.__restore_options.type == HypervisorDisplayName.AMAZON_AWS:
            current_zone = self.__admin_console.driver.find_element(By.ID, 'availabilityZone').get_attribute('value')
        else:
            current_zone = self.__admin_console.driver.find_element(By.ID, 'hostName').get_attribute('value')
        restore_options_dialog.click_button_on_dialog(aria_label='Browse')
        self.__admin_console.wait_for_completion()
        availability_zone_modal = RModalDialog(admin_console=self.__admin_console, title='Select availability zone')
        zone_tree_view = TreeView(self.__admin_console, xpath=availability_zone_modal.base_xpath)
        zone_tree_view.select_items(items=[availability_zone])
        if current_zone == availability_zone:
            availability_zone_modal.click_cancel()
        else:
            availability_zone_modal.click_submit()

    def destination_host(self, restore_options_dialog, destination_host):
        """
        select destination host for the given vm
        Args:
            restore_options_dialog: (object) dialog modal object
            destination_host: (str) destination host to be selected

        """
        if not destination_host:
            self.log.info("destination host is not set")
            return
        restore_options_dialog.click_button_on_dialog(aria_label='Browse')
        self.__admin_console.wait_for_completion()
        restore_destination_modal = RModalDialog(admin_console=self.__admin_console, title='Select restore destination')
        destination_tree_view = TreeView(self.__admin_console, xpath=restore_destination_modal.base_xpath)
        if isinstance(destination_host, list):
            destination_tree_view.expand_path(destination_host, partial_selection=True)
        else:
            destination_tree_view.select_items(items=[destination_host])
        restore_destination_modal.click_submit()

    def destination_folder(self, restore_options_dialog, destination_folder, button_index=0):
        """
        select destination folder for the given vm
        Args:
            destination_folder: (str) : path of the destination folder
            restore_options_dialog: (WebElement) : dailog model of the restore options
            button_index: (int) :   index of the browse button to be clicked

        """
        if not destination_folder:
            self.log.info("destination folder is not set")
            return
        if self.__restore_options.type == HypervisorDisplayName.MS_VIRTUAL_SERVER:
            restore_options_dialog.click_button_on_dialog(aria_label='browse', button_index=button_index)
            self.__admin_console.wait_for_completion()
            restore_destination_modal = RModalDialog(admin_console=self.__admin_console,
                                                     title='Select a path')
        else:
            restore_options_dialog.click_button_on_dialog(aria_label='Browse', button_index=button_index)
            self.__admin_console.wait_for_completion()
            restore_destination_modal = RModalDialog(admin_console=self.__admin_console,
                                                     title='Select restore destination')
        destination_tree_view = TreeView(admin_console=self.__admin_console, xpath=restore_destination_modal.base_xpath)
        path = list(filter(None, re.split(r"[/\\]", destination_folder)))
        destination_tree_view.expand_path(path=path)
        restore_destination_modal.click_submit()

    def disk_options(self, modal, disk_options):
        """
        Configure disk level options for the VM
        Args:
            modal : (WebElement) Restore options modal element
            disk_options :  (dict) disk options for the VM
        """
        self.log.info(f"selecting datastores for disks: {disk_options}")
        modal.enable_toggle(toggle_element_id='showDiskConfigToggle')
        vm_disks_table = Rtable(admin_console=self.__admin_console, id='VmDisks')
        table_data = vm_disks_table.get_table_data()
        disk_names = table_data['Disk name']
        disk_names = list(map(lambda x: x.lower(), disk_names))
        base_element = self.__admin_console.driver.find_element(By.XPATH, modal.base_xpath)
        dropdown = RDropDown(admin_console=self.__admin_console, base_element=base_element)
        for disk, ds in disk_options.items():
            if disk.lower() in disk_names:
                row_index = disk_names.index(disk.lower())
                dropdown.select_drop_down_values(index=row_index + 2, values=[ds], case_insensitive_selection=True)
            else:
                raise Exception('disk [{}] not found in the disk configuration options grid'.format(disk))

    def edit_display_name(self, name):
        """
        edit the display name for the vm on the wizard
        Args:
            name (str) : name of the vm to edit the display name for

        """
        self.wizard.click_icon_button_by_title(title='Edit Display Name')
        display_name = self.__restore_options.prefix + name + self.__restore_options.suffix
        self.wizard.fill_text_in_field(id='vmDisplayNameField', text=display_name)
        self.wizard.click_icon_button_by_title(title='Save Display Name')

    def configure_ip_address_settings(self):
        pass

    def network(self, restore_dialog, network):
        """
        method to select network for cloud hypervisors
        Args:
            restore_dialog: (WebElement) element of the modal
            network: (str) name of the network or
                    (list) [vpc, subnet, network_inteface]

        """
        if self.__restore_options.type == HypervisorDisplayName.Alibaba_Cloud:
            self.enable_advanced_section(restore_dialog)
        if self.__restore_options.type == HypervisorDisplayName.AMAZON_AWS:
            restore_dialog.click_button_on_dialog(aria_label='Browse', button_index=1)
        self.__admin_console.wait_for_completion()
        network_dailog = RModalDialog(admin_console=self.__admin_console, title='Select network interface')
        network_tree_view = TreeView(admin_console=self.__admin_console, xpath=network_dailog.base_xpath)
        if isinstance(network, list):
            network_tree_view.expand_path(path=network, partial_selection=True)
        else:
            network_tree_view.select_items(items=[network], partial_selection=True)
        network_dailog.click_submit()

    def security_groups(self, restore_dialog, security_groups):
        """
        method to select security group for cloud hypervisors
        Args:
            restore_dialog: (WebElement) element of the modal
            security_groups: (list) name of the security groups

        """
        self.log.info(f"selecting security groups : {security_groups}")
        if self.__restore_options.type == HypervisorDisplayName.AMAZON_AWS:
            if security_groups == '--Auto Select--':
                self.__admin_console.select_radio(value='autoAssign',name='Security groups')
                return
        else:
            self.enable_advanced_section(restore_dialog)
        restore_dialog.select_dropdown_values(drop_down_id='securityGroups', values=security_groups,
                                              partial_selection=True)

    def vm_disk_config(self, iops, throughput, volumetype, encryptionKey):
        """
        method to edit the volume options
        Args:
            vm: (WebElement) element of the modal
            iops: (dict) volume iops
            throughput: (dict) volume throughput
            volumetype: (dict) volume type
            encryptionKey: (dict) volume encryption key

        """
        volume_table = Rtable(admin_console=self.__admin_console, id="DiskOptionsGrid")
        volume_list = volume_table.get_column_data("Source volume ID")
        for volume in volume_list:
            volume_table.search_for(volume)
            self.__admin_console.driver.execute_script("window.scrollTo(document.body.scrollWidth, 0)")
            volume_table.select_all_rows()
            volume_table.access_toolbar_menu('Edit')
            self.configure_volume_edit_options(volume, iops, throughput, volumetype, encryptionKey)
            volume_table.clear_search()

    def configure_volume_edit_options(self, volumeID, iops, throughput, volumetype, encryptionKey):
        """
           function to edit options for the volume
           Args:
               volume: (dict) volume options
               iops: (dict) volume options
               throughput: (dict) volume options
               volumetype: (dict) volume options
               encryptionKey: (dict) volume options
        """
        modal_title = 'Modify options for volume'
        volume_options_dialog = RModalDialog(admin_console=self.__admin_console, title=modal_title)
        volume_name_field_value = volume_options_dialog.get_input_details(input_id='volumeName')
        if len(volume_name_field_value.strip()) == 0:
            display_name = self.__restore_options.prefix + volumeID
            volume_options_dialog.fill_text_in_field(element_id='volumeName', text=display_name)
        else:
            display_name = self.__restore_options.prefix + volume_name_field_value
            volume_options_dialog.fill_text_in_field(element_id='volumeName', text=display_name)

        volume_options_dialog.select_dropdown_values(drop_down_id='volumeType', values=[volumetype])
        try:
            if self.__admin_console.check_if_entity_exists("id","iops"):
                volume_options_dialog.fill_text_in_field(element_id='iops', text=iops)
        except Exception as exp:
            self.logger.error('IOPS Field is not Interactable', exp)
        try:
            if self.__admin_console.check_if_entity_exists("id","throughput"):
                volume_options_dialog.fill_text_in_field(element_id='throughput', text=throughput)
        except Exception as exp:
            self.logger.info('Throughput Field is not Interactable', exp)
        volume_options_dialog.select_dropdown_values(drop_down_id='encryptionKey', values=[encryptionKey])
        volume_options_dialog.click_button_on_dialog('Save')

    def configure_network_settings(self, restore_options_dialog, network_settings):
        """
        configure network settings for the vm
        Args:
            restore_options_dialog: (object) Rmodal Dialog class object
            network_settings: (dict) source and destination settings
        """
        self.enable_advanced_section(restore_options_dialog)
        self.delete_newtork_settings()
        self.add_network_settings(restore_options_dialog, network=network_settings)

    def add_network_settings(self, restore_options_dialog, network):
        """
        add network settings
        Args:
            restore_options_dialog: (object) Rmodal Dialog class instance
            network: (dict) containing source network and destination network
        """
        if (self.__restore_options.type == HypervisorDisplayName.XEN_SERVER or
                self.__restore_options.type == HypervisorDisplayName.Vcloud.value):
            index = 0
        else:
            index = 1
        restore_options_dialog.click_button_on_dialog(text='Add', button_index=index)
        network_settings_modal = RModalDialog(self.__admin_console, title='Add network settings')
        network_dropdown = RDropDown(admin_console=self.__admin_console)
        if network.get('source', None):
            network_dropdown.select_drop_down_values(drop_down_label='Source network', values=[network['source']])
        if network.get('destination', None):
            network_dropdown.select_drop_down_values(drop_down_label='Destination network',
                                                     values=[network['destination']])
        network_settings_modal.click_submit()

    def delete_newtork_settings(self, network=None):
        """
        deletes network settings configured
        by default if no network is provided it will delete all the existing networks configured
        Args:
            network (dict) : contain source and destination networks
        """
        network_table = Rtable(admin_console=self.__admin_console, id='networkSettingsTable')
        network_table.expand_grid()
        if not network:
            rows = network_table.get_total_rows_count()
            for i in range(rows):
                network_table.access_action_item_by_row_index(row_index=0, action_item='Delete')
                self.__admin_console.wait_for_completion()
        else:
            source_network = network_table.get_column_data(column_name='Source network')
            destination_network = network_table.get_column_data(column_name='Destination network')
            for i in range(len(source_network)):
                if source_network[i] == network['source_network'] and \
                        destination_network[i] == network['destination_network']:
                    network_table.access_action_item_by_row_index(row_index=i, action_item='Delete')
                    self.__admin_console.wait_for_completion()

    def enable_advanced_section(self, restore_options_dialog):
        """
        open advanced sections on the restore options dialog

        Args:
            restore_options_dialog (object): Rmodal Dialog class instance

        """
        self.log.info("enabling advanced section")
        toggle_id = 'advancedOptions'
        if not self._VirtualMachines__restore_options.type == HypervisorDisplayName.XEN_SERVER:
            restore_options_dialog.toggle.enable(id=toggle_id)
        if self.__admin_console.check_if_entity_exists('xpath', "//div[@id='networkSettingsTable']//button[@aria-label='Expand grid']"):
            self.__admin_console.click_by_xpath("//div[@id='networkSettingsTable']//button[@aria-label='Expand grid']")

    def vcloud_vapp(self, restore_options_dialog, vapp=None):
        """
        Set vcloud vapp

        Args:
            restore_options_dialog  (obj)   -       Restore Dialog object
            vapp                    (str)   -       Name of the vApp to select
        """
        if not vapp:
            self.log.info("No vApp set, restoring to in-place vApp.")
            return
        self.log.info("Setting vApp to {}".format(vapp))
        restore_options_dialog.fill_text_in_field(element_id='restoreToExistingInstance', text=vapp)

    def vcloud_org_vdc(self, modal, org_vdc=None):
        """
        Set vcloud org vdc

        Args:
            modal                   (obj)   -       Restore Dialog object
            org_vdc                 (str)   -       Name of the Organizational VDC
        """
        if not org_vdc:
            self.log.info("No org vdc set, restoring to default.")
            return
        self.log.info("Selecting Org VDC {}".format(org_vdc))
        modal.select_dropdown_values(drop_down_id="vcloudOrgVCDDropdown", values=[org_vdc])

    def vcloud_organization(self, modal, org=None):
        """
        Set vcloud organization

        Args:
            modal                   (obj)   -       Restore Dialog object
            org                     (str)   -       Name of the Organization
        """
        if not org:
            self.log.info("No org set, restoring in place.")
            return
        self.log.info("Selecting Org VDC {}".format(org))
        modal.select_dropdown_values(drop_down_id="vcloudOrgVCDDropdown", values=[org])

    def edit_network_settings(self, network_interface, create_public_ip):
        """
        Edit advance network setting
        Args:
            network_interface (str) : contain network interface
            create_public_ip (bool) : true if creating public, otherwise false
        """
        network_table = Rtable(admin_console=self.__admin_console, id='networkSettingsTable')
        network_table.expand_grid()
        rows = network_table.get_total_rows_count()
        for i in range(rows):
            network_table.access_action_item_by_row_index(row_index=0, action_item='Edit')
            self.__admin_console.wait_for_completion()
        network_settings_modal = RModalDialog(self.__admin_console, title='Edit network settings')
        network_dropdown = RDropDown(admin_console=self.__admin_console)
        if network_interface:
            network_dropdown.select_drop_down_values(drop_down_label='Virtual network/subnet',
                                                     values=[network_interface], partial_selection=True)
        if create_public_ip:
            network_settings_modal.toggle.enable(id="publicIPCheck")
        else:
            network_settings_modal.toggle.disable(id="publicIPCheck")
        network_settings_modal.click_submit()

    def configure_tags(self, restore_options_dialog, vm_tags):
        """
        Add tags to the VM
        Args:
            vm_tags (list) : list of vm tags
        """
        if vm_tags:
            restore_options_dialog.click_button_on_dialog(aria_label='Browse', button_index=0)
            vm_tags_modal = RModalDialog(self.__admin_console, title='VM tags')
            for vm_tag in vm_tags:
                vm_tags_modal.fill_text_in_field(element_id='tagNameField', text=vm_tag["name"])
                vm_tags_modal.fill_text_in_field(element_id='tagValueField', text=vm_tag["value"])
                vm_tags_modal.click_button_on_dialog(text='Add', button_index=0)
            vm_tags_modal.click_submit()

    def azure_disk_options(self, storage_account, storage_type):
        """
        method to edit the disk options
        Args:
            storage_account: (dict) disk storage account
            storage_type: (dict) disk storage type
        """
        if storage_type == self.__admin_console.props['label.original']:
            storage_type = "Standard HDD"
        disk_options_table = Rtable(admin_console=self.__admin_console, id="DiskOptionsGrid")
        disks_list = disk_options_table.get_column_data(self.__admin_console.props['header.rtName'])
        for disk in disks_list:
            self.__admin_console.driver.execute_script("window.scrollTo(document.body.scrollWidth, 0)")
            disk_options_table.select_rows([disk], True)
            disk_options_table.access_toolbar_menu(self.__admin_console.props['label.globalActions.edit'])
            self.configure_disk_edit_options(storage_account, storage_type)
            disk_options_table.clear_search()

    def configure_disk_edit_options(self, storage_account, storage_type):
        """
           function to edit options for the disk
           Args:
               storage_account: (dict) disk options
               storage_type: (dict) disk options
        """
        modal_title = self.__admin_console.props['title.modifyOptionsForDisk']
        disk_options_dialog = RModalDialog(admin_console=self.__admin_console, title=modal_title)
        disk_options_dialog.select_dropdown_values(drop_down_id='storageTypeDropdown', values=[storage_type])
        disk_options_dialog.select_dropdown_values(drop_down_id='storageAccountDropdown', values=[storage_account])
        disk_options_dialog.click_submit()


    def specify_guest_credentials(self,restore_options_dialog,computer_name,user_name,password):

        """
        Enables the Specify guest credentials toggle and enters IP, username and password of the source

        Args:
            restore_options_dialog (object): Rmodal Dialog class instance
            computer_name: IP of Source VM
            user_name: UserName of source
            password: Password of source
        """

        self.log.info("enabling guest credentials toggle")
        toggle_label = 'Specify guest credentials'
        restore_options_dialog.enable_toggle(label=toggle_label)
        restore_options_dialog.fill_text_in_field(element_id="computerName",text=computer_name)
        restore_options_dialog.fill_text_in_field(element_id="userName", text=user_name)
        restore_options_dialog.fill_text_in_field(element_id="instanceAdminPassword", text=password)



    def configure_oci_instance_tags(self, restore_options_dialog, tags):
        """
        Add the tags to an OCI Instance
        Args:
            restore_options_dialog   (object)    -   Restore Dialog object
            tags   (list of lists)  -- {tag_namespace: {tag_key: tag_value}}
        """
        restore_options_dialog.click_button_on_dialog(aria_label='Add', button_index=0)
        self.__admin_console.wait_for_completion()
        instance_tags_modal = RModalDialog(admin_console=self.__admin_console, title='Instance tags')
        instance_tags_modal.click_button_on_dialog(aria_label='Browse', button_index=0)
        self.__admin_console.wait_for_completion()
        tag_browse_modal = RModalDialog(admin_console=self.__admin_console, title='Browse tags')
        tag_browse_tree_view = TreeView(self.__admin_console, xpath=tag_browse_modal.base_xpath)
        for tag_namespace in tags:
            for tag_key, tag_value in tags[tag_namespace].items():
                tag_browse_tree_view.expand_path([tag_namespace, tag_key, tag_value])
        tag_browse_modal.click_save_button()
        instance_tags_modal.click_save_button()

    def configure_vmware_vm_custom_attributes(self, restore_options_dialog, custom_attributes, add = True):
        """
        Adds/Removes custom attributes to/from the VM
        Args:
            restore_options_dialog   (object)    -   Restore Dialog object (RModalDialog)
            custom_attributes   (dict)  -- {attribute_name: attribute_value}
            add (bool)  -- True if adding custom attributes, False if removing custom attributes
                           Default is True
        """
        custom_attributes_modal = RModalDialog(admin_console=self.__admin_console, title='VM custom attributes')
        values_to_deselect = []
        for attribute_name, attribute_value in custom_attributes.items():
            deselect_val = attribute_name + ":" if add else attribute_name + ":" + attribute_value
            values_to_deselect.append(deselect_val)
        if values_to_deselect:
            restore_options_dialog.deselect_dropdown_values(drop_down_id='attributesDropdown', values=values_to_deselect)
        if add:
            restore_options_dialog.click_button_on_dialog(aria_label='Add', button_index=1)
            for attribute_name, attribute_value in custom_attributes.items():
                custom_attributes_modal.fill_text_in_field(element_id='tagNameField', text=attribute_name)
                custom_attributes_modal.fill_text_in_field(element_id='tagValueField', text=attribute_value)
                custom_attributes_modal.click_button_on_dialog(text='Add', button_index=0)
            custom_attributes_modal.click_save_button()

    def configure_vmware_vm_tags(self, restore_options_dialog, tags, add = True):
        """
        Adds/Removes tags to/from VMware VM
        Args:
            restore_options_dialog   (object)    -   Restore Dialog object (RModalDialog)
            tags   (dict)  -- {tag_category: [tag1, tag2, tag3]}
            add (bool)  -- True if adding tags, False if removing tags
                           Default is True
        """
        if add:
            restore_options_dialog.click_button_on_dialog(aria_label='Add', button_index=0)
            self.__admin_console.wait_for_completion()
            vm_tags_modal = RModalDialog(admin_console=self.__admin_console, title='VM tags')
            vm_tags_modal.click_button_on_dialog(aria_label='Browse', button_index=0)
            self.__admin_console.wait_for_completion()
            tag_browse_modal = RModalDialog(admin_console=self.__admin_console, title='Browse tags')
            tag_browse_tree_view = TreeView(self.__admin_console, xpath=tag_browse_modal.base_xpath)
            for tag_category in tags:
                for tag in tags[tag_category]:
                    tag_browse_tree_view.expand_path([tag_category, tag])
            tag_browse_modal.click_save_button()
            vm_tags_modal.click_save_button()
            return
        values_to_deselect = []
        for tag_category in tags:
            for tag in tags[tag_category]:
                tag_category_tag_pair = tag_category + ":" + tag
                values_to_deselect.append(tag_category_tag_pair)
        if values_to_deselect:
            restore_options_dialog.deselect_dropdown_values(drop_down_id='tagsDropdown', values=values_to_deselect)
