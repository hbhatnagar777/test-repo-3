from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions or operations to do a disk level restore.

Class:

    DiskLevelRestore() ---> _Navigator() ---> AdminConsoleBase() ---> object()

Functions:

    disk_level_restore()        -- Submits a VMware disk level restore for the chosen disk and
                                   attaches it to the specified VM

    aws_attach_disk_restore()       -- Attach volumes to instances restore
"""
from selenium.webdriver.support.ui import Select
from Web.AdminConsole.Components.panel import DropDown, RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.VSAPages.restore_select_vm import RestoreSelectVM
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.browse import RBrowse


class DiskLevelRestore:
    """
    This class provides method to do a disk level restore
    """

    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__rpanelinfo = RPanelInfo(admin_console)
        self.__treeview = TreeView(admin_console)
        self.__browse_obj = RBrowse(admin_console)
        self.__restore_dialog = RModalDialog(admin_console, "Restore options")
        self.res_select_vm_obj = RestoreSelectVM(admin_console)

    @PageService()
    def disk_level_restore(
            self,
            virtual_machine,
            disks,
            destination_proxy,
            destination_server,
            esx,
            vm_name,
            datastore,
            disk_prov='Original',
            transport_mode='Auto',
            respool=None,
            overwrite=True,
    ):
        """
        Disk level restore job will be submitted with the given values

        Args:
            virtual_machine         (str)   :   the virtual machine whose disks has
                                                        to be restored

            disks                   (list)         :   the list of disks to be restored

            destination_proxy       (str)   :   the proxy to be used for restore

            destination_server      (str)   :   the hypervisor where the destination
                                                        VM resides

            esx                     (str)   :   the esx in which the attach to VM resides

            vm_name                 (str)   :   the VM to which the disks are to be added

            datastore               (str)   :   the datastore where the disk is to
                                                        be restored

            disk_prov               (str)   :   the type of disk provisioning for the
                                                        restored disk

            transport_mode          (str)   :   the transport mode to be used for restore

            respool                 (list)         :   the resource pool in which the attach
                                                        VM resides

            overwrite               (bool)         :   if the restored disk has to be over written

        Raises:
            Exception:
                if there is any error while submitting disk level restore

        Returns:
            job_id  (int)   :   the restore job ID

        """
        self.__admin_console.log.info("Attaching disk to virtual_machine %s in server %s",
                                      str(vm_name), str(destination_server))

        self.__browse_obj.access_folder(virtual_machine)
        self.__browse_obj.select_files(disks)

        self.__browse_obj.submit_for_restore()

        self.__admin_console.select_value_from_dropdown("serverId", destination_server)
        self.__admin_console.select_value_from_dropdown("destinationProxy", destination_proxy)

        if overwrite:
            self.__admin_console.checkbox_select("overwrite")

        self.__admin_console.select_value_from_dropdown("diskProvOption", disk_prov)
        self.__admin_console.select_value_from_dropdown("transportMode", transport_mode)
        # disks = [disks[0]]
        # selecting the VM to attach the disk to
        self.__driver.find_element(By.XPATH,
            "//*[@id='per-disk-options']/div/span/button[contains(text(),'Browse')]").click()
        self.__admin_console.wait_for_completion()

        self.__admin_console.select_destination_host(esx)

        if respool:
            for resource_pool in respool:
                if self.__admin_console.check_if_entity_exists("xpath", "//span[contains(text(),'" +
                                                                        resource_pool + "')]"):
                    self.__driver.find_element(By.XPATH,
                        "//span[contains(text(),'" + resource_pool + "')]").click()
                    self.__admin_console.wait_for_completion()
            self.__admin_console.log.info("selected a resource pool %s", str(respool))

        if self.__admin_console.check_if_entity_exists("xpath", "//span[contains(text(),'" + vm_name + "')]"):
            self.__driver.find_element(By.XPATH,
                "//span[contains(text(),'" + vm_name + "')]").click()
            self.__admin_console.log.info("selected vm %s", str(vm_name))
        else:
            raise Exception("There is no VM with the given name to be used to attach disk")

        self.__admin_console.submit_form()

        Select(self.__driver.find_element(By.ID,
            "data-store")).select_by_visible_text(datastore)
        self.__admin_console.wait_for_completion()
        self.__admin_console.log.info("selected a datastore %s", str(datastore))

        self.__admin_console.submit_form(False)

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def vcloud_attach_disk_restore(self, source_vm, disk_list,destination_hypervisor,
                                   access_node, destination_vm_path, disk_storage_profile=None, end_user=False):
        """
        Perform attach disk restore to a destination VM

        Args:
            source_vm               (str)           Machine name for vm with disks
            destination_vm_path     (list)          Destination VM location options ("[org]/[vApp]/[VM Name]")
            disk_list               (list(str))     List of disk names to be restored
            destination_hypervisor  (str)           Destination Hypervisor for restore
            access_node             (Machine obj)   Access node for restore
            disk_storage_profile    (str)           Storage profile for the disk to be attached
            end_user                (bool)          True if end user restore

        Returns:
            job_id                  (str)           Job ID for attach disk restore
        """

        # Select source vm and disks
        self.__admin_console.log.info("Attach volume restore")
        if not end_user:
            self.__browse_obj.access_folder(source_vm)
        self.__browse_obj.select_files(disk_list)
        self.__browse_obj.submit_for_restore()
        self.__admin_console.wait_for_completion()

        # Input options
        if not end_user:
            self.__rdropdown.select_drop_down_values(values=[access_node.machine_name], drop_down_id='accessNodeDropdown')

            # Browse Destination VM
            self.__rpanelinfo.click_button("Browse")
            restore_destination_modal_dialog = RModalDialog(self.__admin_console, "Select restore destination")
            tree_view = TreeView(self.__admin_console, restore_destination_modal_dialog.base_xpath)
            tree_view.expand_path(destination_vm_path)
            restore_destination_modal_dialog.click_submit() # Submit form for VM browse

        for disk_index, disk_name in enumerate(disk_list):
            tab_xpath = f"//span[contains(text(), '{disk_name}')]/parent::button"
            self.__admin_console.driver.find_element(By.XPATH, tab_xpath).click()
            self.__admin_console.wait_for_completion()

            new_vol_name = 'del_{}'.format(disk_name)
            self.__rpanelinfo.fill_input('Disk name', new_vol_name)

            if not end_user:
                # Select disk storage policy -- this ID might change, change accordingly.
                self.__rdropdown.select_drop_down_values(drop_down_id="storageAccountDropdown", values=[disk_storage_profile])

        self.__rpanelinfo.click_button("Submit")  # Submit form for restore job

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def aws_attach_disk_restore(self, virtual_machine, disks, attach_vol_to,
                                vir_client, proxy, existing_instance=None, vol_prefix=None,
                                power_on=True, overwrite=False, inst_display_name=None, ami=None,
                                available_zone=None, auto_select_instance_type=True, ins_type=None,
                                network=None, auto_select_security_grp=True, security_group=None):
        """
        Attach volumes to instances restore

        Args:
            virtual_machine     (str)   :   name of the VM to be restored

            disks               (list)         :   list of disks to be restore

            attach_vol_to       (str)   : New Instance or existing instance

            vir_client          (str)   : virtualization client for restore

            proxy               (str)   : proxy for restore

            existing_instance   (str)   : Existing instance in case of restore to existing
                                                instance

            vol_prefix          (str)   : prefix to restore volumes

            power_on            (bool)         : restored vm should be powered on of off

            overwrite           (bool)         : restored vm should be overwritten or not

            inst_display_name   (str)   : Display name for restored instance

            ami                 (str)   : Ami to be selected for attaching disk

            available_zone      (str)   : Availability zone for restoring

            auto_select_instance_type(bool)    : Instance type should be auto selected or not

            ins_type            (str)   : If Instance type inst auto selected,then the instance type

            network             (str)   : Network for restoring

            auto_select_security_grp (bool)    : if auto select securtiy group or not

            security_group      (str)   : security group to be selected

        Raises:
            Exception:
                if there is any error while submitting attach disk restore

        Returns:
            job_id  (int)   :   the restore job ID

        """

        self.__admin_console.log.info("Attach volume restore")
        self.__browse_obj.access_folder(virtual_machine)
        self.__browse_obj.select_files(disks)
        self.__browse_obj.submit_for_restore()
        self.__admin_console.wait_for_completion()

        if attach_vol_to == 'Other Instance':
            self.__admin_console.click_button("Attach volume to", "Other instance")
            self.__restore_dialog.click_button_on_dialog(aria_label=self.__admin_console.props["label.browse"])
            self.__admin_console.log.info("Browse to select destination VM")
            self.__admin_console.wait_for_completion()
            vm_selector_modal = RModalDialog(self.__admin_console,
                                              self.__admin_console.props["label.selectExistingInstance"])
            self.__treeview.select_items([existing_instance])
            vm_selector_modal.click_submit()
            self.__admin_console.log.info("Selected Destination VM to attach disk")
        elif attach_vol_to == 'New Instance':
            self.__admin_console.click_button('New instance')
            self.__admin_console.log.info("Selected New instance as the Option")
            self.__restore_dialog.fill_text_in_field(element_id="vmDisplayNameField", text=inst_display_name)
            self.__admin_console.log.info("Entered the Instance name", str(inst_display_name))
            self.__admin_console.wait_for_completion()
            self.__restore_dialog.select_dropdown_values(drop_down_id="AMISelection", values=[ami])
            self.__admin_console.log.info("Selected the AMI from the list of AMI Drop down", str(ami))
            self.__admin_console.wait_for_completion()
            self.__restore_dialog.select_dropdown_values(drop_down_id="instanceType", values=[ins_type])
            self.__admin_console.log.info("User selected the instance type", str(ins_type))
            self.__admin_console.wait_for_completion()
            self.__restore_dialog.expand_accordion(id="volumeOptionsPanel")
            disk_list_xp = f"//div[contains(@role, 'tablist') and contains(@class, " \
                           f"'MuiTabs-flexContainerVertical')]//child::div"
            all_disks = self.__driver.find_elements(By.XPATH, disk_list_xp)
            for e, disk in enumerate(all_disks):
                disk.click()
                self.__admin_console.wait_for_completion()
                self.__restore_dialog.fill_text_in_field(f'diskName-{str(e)}',
                                                         vol_prefix + disk.get_attribute('aria-label'))
        else:
            self.__admin_console.click_button('My instance')
            disk_list_xp = f"//div[contains(@role, 'tablist') and contains(@class, " \
                           f"'MuiTabs-flexContainerVertical')]//child::div"
            all_disks = self.__driver.find_elements(By.XPATH, disk_list_xp)
            for e, disk in enumerate(all_disks):
                disk.click()
                self.__admin_console.wait_for_completion()
                self.__restore_dialog.fill_text_in_field(f'diskName-{str(e)}',
                                                         vol_prefix + disk.get_attribute('aria-label'))
            self.__admin_console.log.info("Selected the Same Instance for restore")

        self.__restore_dialog.click_submit()
        self.__admin_console.log.info("Successfully submitted the restore operation")
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def azure_attach_disk(self, azure_attach_disk_options):

        """
        Performs an attach disk  restore for Azure RM
        Args:
            azure_attach_disk_options  (dict) : It has parameters to restore an Azure Vm

        Returns:
            job_id  (str):   the restore job ID

        """
        self.__browse_obj.access_folder(azure_attach_disk_options['virtual_machine'])
        self.__browse_obj.select_files(azure_attach_disk_options['disks'])
        self.__browse_obj.submit_for_restore()
        self.__admin_console.wait_for_completion()

        if azure_attach_disk_options['attach_disks_to'] == 'Other virtual machine':
            self.__restore_dialog.access_tab(self.__admin_console.props["label.azureAttachDiskOtherVM"])

            self.__admin_console.log.info("Attaching disk to virtual_machine %s in server %s",
                                          str(azure_attach_disk_options['disk_name']), str(azure_attach_disk_options['destination_server']))

            self.__restore_dialog.select_dropdown_values(drop_down_id="hypervisorsDropdown",
                                                         values=[azure_attach_disk_options['destination_server']])
            self.__admin_console.log.info("Entered destination server name")

            self.__restore_dialog.select_dropdown_values(drop_down_id="accessNodeDropdown", values=[azure_attach_disk_options['destination_proxy']])
            self.__admin_console.log.info("Entered destination Proxy name")

            self.__restore_dialog.click_button_on_dialog(text=self.__admin_console.props["label.browse"])
            self.__admin_console.log.info("Browse to select destination VM")
            self.__admin_console.wait_for_compl0etion()

            vm_selector_modal = RModalDialog(self.__admin_console,
                                             self.__admin_console.props["label.selectRestoreDestination"])
            self.__treeview.select_items([azure_attach_disk_options['destination_vm']])
            vm_selector_modal.click_submit()
            self.__admin_console.log.info("Selected Destination VM to attach disk")

            disk_list_xp = f"//div[contains(@role, 'tablist') and contains(@class, " \
                           f"'MuiTabs-flexContainerVertical')]//child::div"
            all_disks = self.__driver.find_elements(By.XPATH, disk_list_xp)

            for e, disk in enumerate(all_disks):
                disk.click()
                self.__admin_console.wait_for_completion()

                self.__restore_dialog.fill_text_in_field(f'diskName-{str(e)}',
                                                         azure_attach_disk_options['disk_name'] + disk.get_attribute('aria-label'))

                self.__restore_dialog.select_dropdown_values('storageAccountDropdown', [azure_attach_disk_options['storage_account']])
                self.__admin_console.log.info("Entered storage account name")


        elif azure_attach_disk_options['attach_disks_to'] == 'New virtual machine' or azure_attach_disk_options['attach_disks_to'] == 'New instance':

            if azure_attach_disk_options['attach_disks_to'] == 'New virtual machine':
                self.__restore_dialog.access_tab(self.__admin_console.props["label.attachDiskNewVM"])
            else:
                self.__restore_dialog.access_tab(self.__admin_console.props["label.awsAttachVolumeNewInstance"])
                self.__admin_console.log.info("Selected New instance as the Option")

                self.__restore_dialog.select_dropdown_values(drop_down_id="restoreVmDestination",
                                                             values=[azure_attach_disk_options['restore_as']])

            self.__restore_dialog.select_dropdown_values(drop_down_id="hypervisorsDropdown",
                                                         values=[azure_attach_disk_options['destination_server']])
            self.__admin_console.log.info("Entered destination server name")

            self.__restore_dialog.select_dropdown_values(drop_down_id="accessNodeDropdown", values=[azure_attach_disk_options['destination_proxy']])
            self.__admin_console.log.info("Entered destination Proxy name")

            self.__restore_dialog.fill_text_in_field(element_id="vmDisplayNameField", text=azure_attach_disk_options['vm_display_name'])
            self.__admin_console.log.info("Entered the Virtual Machine name", str(azure_attach_disk_options['vm_display_name']))
            self.__admin_console.wait_for_completion()

            self.__restore_dialog.select_dropdown_values(drop_down_id="resourceGroupDropdown", values=[azure_attach_disk_options['resource_group']])
            self.__admin_console.log.info("Entered Resource Group")

            self.__restore_dialog.select_dropdown_values(drop_down_id="azureRegionDropdown",
                                                         values=[azure_attach_disk_options['region']])
            self.__admin_console.log.info("Entered Region")

            self.__restore_dialog.select_dropdown_values(drop_down_id="storageAccountDropdown",
                                                         values=[azure_attach_disk_options['storage_account']])
            self.__admin_console.log.info("Entered Storage Account")

            self.__restore_dialog.select_dropdown_values(drop_down_id="availabilityZoneDropdown",
                                                         values=[azure_attach_disk_options['availability_zone']])
            self.__admin_console.log.info("Entered Availability Zone")

            self.__restore_dialog.select_dropdown_values(drop_down_id="securityGroupDropdown",
                                                         values=[azure_attach_disk_options['security_group']])
            self.__admin_console.log.info("Entered Security Group")

            if azure_attach_disk_options['image_option']:
                self.__restore_dialog.select_dropdown_values(drop_down_id="azureImageDropdown",
                                                             values=[azure_attach_disk_options['image_option']])
                self.__admin_console.log.info("Entered Image Option")

            else:
                image_dialog = RModalDialog(self.__admin_console, title=self.__admin_console.props["label.Imageoption"])
                self.__restore_dialog.click_button_on_dialog(aria_label=self.__admin_console.props["label.azure.image.seeAllImages"])

                image_dialog.select_dropdown_values(drop_down_id="azureImageDropdown-visibility",
                                                    values=[azure_attach_disk_options['visibility_type']])
                self.__admin_console.log.info("Entered Visibility Type")

                if azure_attach_disk_options['visibility_type'] == "Marketplace":

                    image_dialog.select_dropdown_values(drop_down_id="azureImageDropdown-publishers",
                                                        values=[azure_attach_disk_options['publisher_type']])
                    self.__admin_console.log.info("Entered Publisher Type")

                    image_dialog.select_dropdown_values(drop_down_id="azureImageDropdown-offers",
                                                        values=[azure_attach_disk_options['offer_type']])
                    self.__admin_console.log.info("Entered Offer Type")

                    image_dialog.select_dropdown_values(drop_down_id="azureImageDropdown-skus",
                                                        values=[azure_attach_disk_options['plan_type']])
                    self.__admin_console.log.info("Entered Plan Type")

                    image_dialog.select_dropdown_values(drop_down_id="azureImageDropdown-version",
                                                        values=[azure_attach_disk_options['version']])
                    self.__admin_console.log.info("Entered Version of vm")

                elif azure_attach_disk_options['visibility_type'] == "Private":
                    image_dialog.select_dropdown_values(drop_down_id="azureImageDropdown-images",
                                                        values=[azure_attach_disk_options['image']])
                    self.__admin_console.log.info("Entered Image")

                image_dialog.click_save_button()

            self.__restore_dialog.fill_text_in_field(element_id="userName", text=azure_attach_disk_options['username'])
            self.__admin_console.log.info("Entered the username for Administrator account", str(azure_attach_disk_options['username']))
            self.__admin_console.wait_for_completion()

            self.__restore_dialog.fill_text_in_field(element_id="instanceAdminPassword", text=azure_attach_disk_options['password'])
            self.__admin_console.log.info("Entered the password for Administrator account")
            self.__admin_console.wait_for_completion()

        else:
            self.__restore_dialog.access_tab(self.__admin_console.props["label.azureAttachDiskMyVM"])
            disk_list_xp = f"//div[contains(@role, 'tablist') and contains(@class, " \
                           f"'MuiTabs-flexContainerVertical')]//child::div"
            all_disks = self.__driver.find_elements(By.XPATH, disk_list_xp)
            for e, disk in enumerate(all_disks):
                disk.click()
                self.__admin_console.wait_for_completion()
                self.__restore_dialog.fill_text_in_field(f'diskName-{str(e)}',
                                                         azure_attach_disk_options['disk_name'] + disk.get_attribute('aria-label'))
            self.__admin_console.log.info("Selected the Same Virtual machine for restore")

        self.__restore_dialog.click_submit()
        self.__admin_console.log.info("Successfully submitted the restore operation")
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def vmware_attach_disk_restore(self, virtual_machine, destination_vm, destination_server=None,
                                   destination_proxy=None, disks=None,
                                   destination_ds=None, end_user=False, over_write=True):

        """
        Performs attach disk  restore for VMware VM
        Args:
            virtual_machine    (str):     machine name for the source disk
            destination_server  (str):    VClient name
            destination_proxy   (str):    Proxy to be used for restore
            disks              (list):    disks to be attached
            destination_vm      (str):    Disks to be attached to the destination VM
            destination_ds     (str):    datastore to be used for attaching disk
            end_user        (bool):      Restore as end user
            over_write      (bool):     Overwrite restore

        Returns:
            job_id  (str):   the restore job ID

        """
        if not end_user:
            self.__browse_obj.access_folder(virtual_machine)
        if not disks:
            _disks_to_restore = self.__browse_obj.get_column_data()
            self.__browse_obj.select_files(select_all=True)
        else:
            _disks_to_restore = disks
            self.__browse_obj.select_files(disks)
        self.__browse_obj.submit_for_restore()
        self.__admin_console.wait_for_completion()

        if end_user:
            if self.__admin_console.check_if_entity_exists("xpath", '//*[text()="My virtual machine"]'):
                self.__restore_dialog.access_tab("My virtual machine")

        if not end_user:
            self.__restore_dialog.select_dropdown_values(drop_down_id="hypervisorsDropdown",
                                                         values=[destination_server])
            self.__restore_dialog.select_dropdown_values(drop_down_id="accessNodeDropdown", values=[destination_proxy])

            self.__restore_dialog.click_button_on_dialog(text=self.__admin_console.props["label.browse"])
            self.__admin_console.wait_for_completion()
            self.__treeview.select_items([destination_vm])
            vm_selector_modal = RModalDialog(self.__admin_console,
                                             self.__admin_console.props["label.selectRestoreDestination"])
            vm_selector_modal.click_submit()

        for disk_index, disk_name in enumerate(_disks_to_restore):
            tab_xpath = f"//span[contains(text(), '{disk_name}')]/parent::button"
            self.__admin_console.driver.find_element(By.XPATH, tab_xpath).click()
            self.__admin_console.wait_for_completion()
            new_disk_name = 'del_{}'.format(disk_name)
            self.__restore_dialog.fill_text_in_field(f'diskName-{str(disk_index)}', new_disk_name)
            if not end_user:
                self.__restore_dialog.select_dropdown_values('storageAccountDropdown', [destination_ds])

        if over_write:
            self.__restore_dialog.select_checkbox(checkbox_id="overWrite")
            RModalDialog(admin_console=self.__admin_console, title='Confirm overwrite option').click_submit()

        self.__restore_dialog.disable_notify_via_email()

        self.__restore_dialog.click_submit()
        return self.__admin_console.get_jobid_from_popup()
