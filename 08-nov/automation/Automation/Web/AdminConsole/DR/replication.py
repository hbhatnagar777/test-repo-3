# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
replication page of the AdminConsole

"""
from selenium.webdriver.common.by import By

from time import sleep

from Web.AdminConsole.DR.virtualization_replication import ConfigureVMWareVM, \
    ConfigureAzureVM, ConfigureHypervVM, ConfigureAWSVM
from Web.AdminConsole.DR.fs_replication import ConfigureBLR
from Web.AdminConsole.Components.dialog import (ModalDialog, RModalDialog)
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.table import (Table, Rtable)
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.DR.group_details import ReplicationDetails

from Web.AdminConsole.DR.virtualization_replication import SOURCE_HYPERVISOR_AWS, SOURCE_HYPERVISOR_AZURE, SOURCE_HYPERVISOR_HYPERV, SOURCE_HYPERVISOR_VMWARE

class ReplicationGroup:
    """Class for Replication Groups react Page"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__table = Rtable(self.__admin_console)
        self.__modal_dialog = RModalDialog(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.group_details = ReplicationDetails(self.__admin_console)

        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props

        self.__type_class_mapping = {
            SOURCE_HYPERVISOR_AWS: ConfigureAWSVM,
            SOURCE_HYPERVISOR_AZURE: ConfigureAzureVM,
            SOURCE_HYPERVISOR_HYPERV: ConfigureHypervVM,
            SOURCE_HYPERVISOR_VMWARE: ConfigureVMWareVM,
        }

    @WebAction()
    def __click_row_selection(self, name):
        """
        Clicks on the row selection menu for the given title
        Args:
            name: the title of the row selection menu in FS Replication Group creation
        """
        self.__driver.find_element(By.XPATH, "//*[contains(@class, 'row-selection-menu')]"
                                            "/div/div/h3[contains(text(),'{}')]".format(name)).click()

    @PageService()
    def configure_sql_server_replication_group(self):
        """Configures a SQL Server replication group"""
        self.__table.access_menu_from_dropdown(menu_id=self.__label['label.sql'],
                                               label=self.__label['label.addReplicationGroup'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def delete_group(self, group_name):
        """Deletes the given group
        Args:
            group_name  (str):  Name of the group to be deleted
        """
        self.__table.access_action_item(group_name, self.__label["action.delete"])
        self.__modal_dialog.fill_text_in_field(element_id="confirmText", text=self.__label["label.delete"].upper())
        self.__modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        sleep(30)
        self.__admin_console.refresh_page()
        if self.has_group(group_name) is False:
            return
        raise CVWebAutomationException(f"The group {group_name} still exists after deletion")

    @PageService()
    def access_group(self, group_name):
        """Access the given replication group
        Args:
            group_name(str):    Name of the group to be accessed
        """
        self.__table.access_link(group_name)

    @PageService()
    def has_group(self, group_name):
        """Returns True if group exists
        Args:
            group_name(str):    Name of the group
        """
        return self.__table.is_entity_present_in_column(self.__label['header.replicationGroup.name'], group_name)

    @PageService()
    def __configure_virtualization(self, source_vendor, destination_vendor, replication_type, **kwargs):
        """Configuring virtualization common steps"""
        is_metallic = kwargs.get("is_metallic", False)
        if is_metallic:
            self.__wizard.select_radio_button(id=replication_type)
            self.__wizard.click_next()

            # Source and Destination Vendor
            self.__wizard.select_drop_down_values(id='sourceVendorDropdown', values=[source_vendor])
            self.__wizard.select_drop_down_values(id='destinationVendorDropdown', values=[destination_vendor])
            self.__wizard.click_next()
        else:
            self.__table.access_toolbar_menu("Add")   

            # Virtual Machine
            self.__wizard.select_radio_button(id="VM")
            self.__wizard.click_next()
            
            # Source and Destination Vendor
            self.__wizard.select_drop_down_values(id='sourceVendorDropdown', values=[source_vendor])
            self.__wizard.select_drop_down_values(id='destinationVendorDropdown', values=[destination_vendor])
            self.__wizard.click_next()
            
            # Replication Type
            self.__wizard.select_radio_button(id=replication_type)
            self.__wizard.click_next()

    @PageService()
    def configure_virtualization(self, source_vendor, destination_vendor, replication_type, **kwargs):
        """
        Configures virtualization for replication.

        Args:
            source_vendor (str): The vendor of the source virtual machine.
            destination_vendor (str): The vendor of the destination virtual machine.
            replication_type (str): The type of replication.

        Returns:
            object: The destination virtual machine object.

        """
        is_metallic = kwargs.get("is_metallic", False)
        self.__configure_virtualization(source_vendor, destination_vendor, replication_type, is_metallic=is_metallic)
        destination_vm_object = self.__type_class_mapping.get(destination_vendor)(
            self.__admin_console
        )
        return destination_vm_object

    @PageService()
    def get_replication_group_details_by_name(self, name):
        """
        Read table content of replication group
        Args:
            name                     (str):   replication group name

        Returns                      (dict):  table content

        """
        group_name_label = self.__label['header.replicationGroup.name']
        if not self.__table.is_entity_present_in_column(group_name_label, name):
            raise CVWebAutomationException("Replication group [%s] not found in replications "
                                           "group page")
        self.__table.apply_filter_over_column(group_name_label, name)
        return self.__table.get_table_data()

    @staticmethod
    def get_schedule_name_by_replication_group(group_name):
        """
        Get schedule name by replication name
        Args:
            group_name               (str):  replication group name

        Returns                      (str):  Schedule name

        """
        return group_name + '_ReplicationPlan__ReplicationGroup'

    @PageService()
    def __configure_fs(self):
        """
        Selects configure File System under the Configure replication group
        """
        self.__table.access_menu_from_dropdown(menu_id=self.__label['label.fileServers'],
                                               label=self.__label['label.addReplicationGroup'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def configure_blr(self):
        """
        Configure a Block Level replication in the admin console
        """
        blr = ConfigureBLR(self.__admin_console)
        self.__configure_fs()
        self.__click_row_selection(self.__label['label.replication.fs.continuous'])
        self.__admin_console.wait_for_completion()
        return blr

    @PageService()
    def replicate(self, source, group_name):
        """
        Args:
            source(str): Source name
            group_name(str): replication group name
        """
        self.__table.apply_filter_over_column(self.__label['label.selectSource'], source)
        self.__table.apply_filter_over_column(self.__label['header.replicationGroupName'], group_name)

        self.__table.access_action_item(group_name, self.__label['action.runReplication'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def disable(self, group_name):
        """Disable a group"""
        self.__table.access_action_item(group_name, self.__label['action.disableReplication'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def enable(self, group_name):
        """enable a group"""
        self.__table.access_action_item(group_name, self.__label['action.enableReplication'])
        self.__admin_console.wait_for_completion()
