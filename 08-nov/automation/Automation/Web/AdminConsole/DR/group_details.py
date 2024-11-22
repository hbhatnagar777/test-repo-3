from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
specific replication page of the AdminConsole
"""
from time import sleep
from enum import Enum
from selenium.webdriver.common.keys import Keys
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    PageService, WebAction
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import (PanelInfo, DropDown, ModalPanel, RModalPanel, RPanelInfo)
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.table import Table, CVTable, Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.DR.monitor import ReplicationMonitor, ContinuousReplicationMonitor
from Web.AdminConsole.DR.virtualization_replication import (SOURCE_HYPERVISOR_AZURE,
                                                            SOURCE_HYPERVISOR_VMWARE,
                                                            SOURCE_HYPERVISOR_HYPERV,
                                                            SOURCE_HYPERVISOR_AWS,
                                                            _Content, _AzureVMOptions,
                                                            _VMwareVMOptions, _HyperVVMOptions, _AWSVMOptions,
                                                            _OverrideOptions)
from Web.AdminConsole.DR.test_failover_vms import TestFailoverVMs

from DROrchestration.DRUtils.DRConstants import TimePeriod, Vendors, Vendors_Complete

class _SummaryOperations:
    """Class to perform summary operations"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props
        self.__panel = RPanelInfo(admin_console, title=self.__label['label.replicationGroupsDetail'])
        self.__dialog = RModalDialog(admin_console)
        self.__alert = Alert(admin_console)

    @PageService()
    def get_summary_details(self):
        """Read summary information from summary tab page"""
        return self.__panel.get_details()

    @PageService()
    def enable_disable_replication_group(self, enable=True):
        """
        Enable or disable replication group.

        Args:
            enable (bool, optional): Whether to enable or disable the replication group. Defaults to True.
        """
        self.__panel.enable_disable_toggle(label=self.__admin_console.props["label.enableLiveSync"], enable=enable)

    @PageService()
    def enable_or_disable_warm_sync(self, enable=True):
        """
        Enables/disables Warm Sync
        """
        self.__panel.enable_disable_toggle(self.__label['label.deployVmDuringFailoverSummary'], enable)
        self.__dialog.click_submit(wait=False)
        retvalue = self.__alert.get_jobid_from_popup(hyperlink=True) if enable else self.__alert.get_content()
        return retvalue

    @PageService()
    def update_access_node(self, access_node: str):
        """
        Updates the access node (Orchestrated Replication)
        Args:
            access_node(str): Access node to be updated
        """
        self.__panel.edit_tile_entity(self.__label['label.accessNode'])
        self.__dialog.select_dropdown_values(drop_down_id="accessNodeDropdown",
                                             values=[access_node],
                                             partial_selection=False,
                                             case_insensitive=True)
        self.__dialog.click_submit()

class _RPOOperations:
    """Class to perform RPO operations"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props

        self.__dialog = RModalDialog(admin_console)
        self.__alert = Alert(admin_console)

        self.__title = self.__label['label.rpo']
        self.__panel = RPanelInfo(admin_console, title=self.__title)

    @PageService()
    def get_rpo_details(self):
        """Read RPO information from configuration tab page"""
        return self.__panel.get_details()

    @PageService()
    def edit_replication_frequency(self, frequency_duration : int, frequency_unit : str = TimePeriod.HOURS.value):
        """
        Edit replication frequency
        Args:
            frequency(int): frequency to set
        """
        self.__panel.edit_tile_entity(self.__label['label.replicationFrequency'])
        self.__dialog.fill_text_in_field(element_id="time", text=frequency_duration)
        self.__dialog.select_dropdown_values(drop_down_id="option",
                                             values=[frequency_unit],
                                             partial_selection=True,
                                             case_insensitive=True)
        self.__dialog.click_submit()

        notification = self.__alert.get_content()
        if notification != self.__label['msg.RGSuccessfulUpdate']:
            raise CVWebAutomationException(f"Expected notification - [{self.__label['msg.RGSuccessfulUpdate']}] ; Observed notification - [{notification}]")

    @PageService()
    def edit_replication_window(self, interval):
        """Edits the replication window and assign it values
        Args:
         interval (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
                eg: {'Monday': [0,1,2,3], 'Tuesday': [0,1,2,3], 'Wednesday': [0,1,2,3]}
        """
        #TODO : Update implementation
        self.__click_window_edit_hyperlink()
        self.__admin_console.wait_for_completion()
        self.__interval_selection(interval)

class _StorageOperations:
    """Class to perform storage operations"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props

        self.__dialog = RModalDialog(admin_console)
        self.__table = Rtable(admin_console)

        self.__title = self.__label['label.storage']
        self.__panel = RPanelInfo(admin_console, title=self.__title)

    @PageService()
    def get_storage_names(self):
        """Returns the details of the storage from the configuration tab"""
        return self.__table.get_column_data(self.__label['label.storagePool'].title())

    @PageService()
    def get_storage_details(self):
        """Returns the details of the storage from the configuration tab"""
        return self.__table.get_rows_data()

    @PageService()
    def add_storage(self, storage_name: str, storage_pool: str, retention=2, retention_type="Week(s)"):
        """Add storage
        Args:
            storage_name            (str):   storage name to be added
            storage_pool            (str):   storage pool name to be selected
            retention               (int):   retention period- by default 2
            retention_type          (string):  retention is by default in weeks, use enum class RetentionType
        """
        self.__dialog = RModalDialog(self.__admin_console, title=self.__label['label.addStorage'])
        self.__admin_console.click_button(id="tile-action-btn")
        self.__dialog.fill_text_in_field(element_id="backupDestinationName", text=storage_name)
        self.__dialog.select_dropdown_values(drop_down_id='storageDropdown', values=[storage_pool])
        self.__dialog.fill_text_in_field(element_id='retentionPeriodDays', text=str(retention))
        self.__dialog.select_dropdown_values(drop_down_id="retentionPeriodDaysUnit", values=[retention_type])
        self.__dialog.click_submit()

    @PageService()
    def change_copy_for_replication(self, copy_name: str):
        """Change the copy for replication in the configuration tab"""
        self.__dialog = RModalDialog(self.__admin_console, title=self.__label['label.copyForReplication'])
        self.__panel.edit_tile_entity(self.__label['label.copyForReplication'])
        self.__dialog.select_dropdown_values(values=[copy_name], drop_down_id='replicationCopyDropdown')
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def delete_storage(self, copy_name: str):
        """Delete the storage in the configuration tab"""
        self.__table.access_action_item_inline(copy_name, self.__label['label.delete'])
        self.__dialog.click_yes_button()
        self.__admin_console.wait_for_completion()

class _AdvancedOptionsOperations:
    """Class to perform advanced options operations"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__label = self.__admin_console.props

        self.__panel = RPanelInfo(self.__admin_console, title=self.__label["title.advancedOptions"])

    @PageService()
    def get_advanced_options_details(self):
        """Get the value of an advanced option"""
        return self.__panel.get_details()

    @PageService()
    def reset_advanced_option(self, option_name: str):
        """Reset the value of an advanced option"""
        #TODO : Update implementation
        self.__panel.edit_tile_entity(self.__label['label.advancedOptions'])
        self.__admin_console.fill_form_by_id('optionName', option_name)
        self.__admin_console.click_button_by_id('resetOption')
        self.__panel.confirm()
        self.__admin_console.wait_for_completion()

class _CustomizationScripts:
    """Class for customization scripts"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__label = self.__admin_console.props

        self.__panel = RPanelInfo(self.__admin_console, title=self.__label["label.customizationScripts"])

class OverviewTab:
    """Class for overview tab of the group details page"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console

        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props

        self._summaryOperations = _SummaryOperations(admin_console)
        self._storageOperations = _StorageOperations(admin_console)
        self._rpoOperations = _RPOOperations(admin_console)

    @property
    def summaryOperations(self):
        return self._summaryOperations

    @property
    def storageOperations(self):
        return self._storageOperations

    @property
    def rpoOperations(self):
        return self._rpoOperations

    @PageService()
    def get_recovery_target(self):
        """
        Return Recovery Target
        """
        return self.summaryOperations.get_summary_details()[self.__label['label.replicationTargetDestination']]

class ConfigurationTab:
    """Class for configuration tab of the group details page"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console, id="repConfigRGDetails")
        self.__dropdown = DropDown(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__modal_panel = PanelInfo(self.__admin_console)
        self.__type_class_mapping = {
            Vendors_Complete.VMWARE.value: EditVMwareVirtualMachine,
            Vendors_Complete.AZURE.value: EditAzureVirtualMachine,
            Vendors_Complete.HYPERV.value: EditHyperVVirtualMachine,
            Vendors.AWS.value: EditAWSVirtualMachine
        }
        self.__vendor_vm = None

        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props

    @property
    def vendor_vm(self):
        return self.__vendor_vm
    
    @vendor_vm.setter
    def vendor_vm(self, vm_obj):
        self.__vendor_vm = vm_obj

    @WebAction()
    def __click_window_edit_hyperlink(self):
        """Clicks on the replication window edit hyperlink"""
        label_name = self.__label['label.replicationWindow']
        elem_xpath = (f"//div[contains(@text, '{label_name}')]"
                      f"/following-sibling::div[contains(@class, 'pageDetailColumn')]//a")
        self.__admin_console.driver.find_element(By.XPATH, elem_xpath).click()

    @WebAction()
    def __click_recoveryoptions_edit(self):
        """Clicks on the confirm frequency button to make it work"""
        PanelInfo(self.__admin_console, "Recovery options").edit_tile()
        self.__admin_console.wait_for_completion()

    @PageService()
    def edit_recovery_options(self):
        """Clicks recovery options edit button"""
        self.__click_recoveryoptions_edit()

    @WebAction()
    def __get_all_intervals(self, day):
        """Returns all the interval elements for a day"""
        return (self.__admin_console.driver.
                find_elements(By.XPATH, "//a[contains(text(),'{}')]/../../"
                                       "td[contains(@class, 'week-time')]".format(day)))

    @PageService()
    def __interval_selection(self, interval):
        """
        Selects the intervals which are marked
        Args:
         interval (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
                eg: {'Monday': [0,1,2,3], 'Tuesday': [0,1,2,3], 'Wednesday': [0,1,2,3]}
        """
        self.__admin_console.select_hyperlink("Clear")
        keys = interval.keys()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            if day in keys:
                intervals = self.__get_all_intervals(day)
                for slot in interval[day]:
                    if "selected" not in intervals[slot].get_attribute('class'):
                        intervals[slot].click()
        self.__modal_panel.submit()

    @PageService()
    def deselect_vms(self, vm_names):
        """
        vm_names (list): names of vms to be deselected
        """
        self.__table.deselect_rows(vm_names)

    @PageService()
    def get_advanced_options_details(self):
        """Get advanced options details"""
        # label = 'Advanced options' in below line
        panel = PanelInfo(self.__admin_console, self.__label['label.advanced.options'])
        return panel.get_details()

    @PageService()
    def get_recovery_options(self):
        """
        Returns recovery options for the VSA continuous replication configuration tab
        """
        recovery_options_panel = PanelInfo(self.__admin_console, title='Recovery options')
        return recovery_options_panel.get_details()

    @PageService()
    def get_all_vm_details(self):
        """
        Retrieves all the details of the virtual machines in the group.

        Returns:
            A list of dictionaries containing the details of each virtual machine.
        """
        return self.__table.get_rows_data()

    @PageService()
    def get_vm_details(self, vm_name : str):
        """Returns the replication VMs and their configuration from the table
            List with a dict for each row as {""}
            Use new classes to fetch the information
        """
        table_data = self.__table.get_table_data()

        row_num = [idx for idx, name in enumerate(table_data.get(self.__label['header.source']))
                   if name == vm_name]
        if not row_num:
            raise CVWebAutomationException(f"Cannot find the VM with the name {vm_name}")
        return {col: row[row_num[0]] for col, row in table_data.items() if row}

    @PageService()
    def toggle_validate_destination_vm(self, enable=True):
        """Toggles the validate destination VM to flag"""
        panel = PanelInfo(self.__admin_console, self.__label['label.advanced.options'])
        toggle_name = self.__label['label.powerOn.replication']
        if enable:
            panel.enable_toggle(toggle_name)
        else:
            panel.disable_toggle(toggle_name)

    @PageService()
    def toggle_unconditional_overwrite(self, enable=True):
        """Toggles the validate destination VM to flag"""
        panel = PanelInfo(self.__admin_console, self.__label['label.advanced.options'])
        toggle_name = self.__label['warning.overwriteVM']
        if enable:
            panel.enable_toggle(toggle_name)
        else:
            panel.disable_toggle(toggle_name)

    @WebAction()
    def _add_virtual_machine(self, vendor_name):
        """Clicks on the add virtual machines and returns the particular AddVMMachineClass"""
        add_vm = _AddVirtualMachine(self.__admin_console, vendor_name)
        self.__table.access_toolbar_menu(menu_id=self.__label["label.addVirtualMachines"])
        return add_vm

    @PageService()
    def add_virtual_machines(self, source_vms: dict | list, vendor_name: str = Vendors_Complete.VMWARE.value, view_mode=None):
        """
        Adds virtual machines to the group.

        Args:
            source_vms
                (dict): {"region_1" : ['vm_1', 'vm_2'], "region_2" : ['vm_3']}
                (list): List of virtual machines to add
            vendor_name (str, optional): The type of virtual machine. Defaults to Vendors_Complete.VMWARE.value.

        Returns:
            None
        """
        add_vm: _AddVirtualMachine = self._add_virtual_machine(vendor_name)
        add_vm.add_vm(source_vms, view_mode=view_mode)

    @PageService()
    def edit_virtual_machines(self, source_vm: str, vm_type: str):
        """
        Edit virtual machine
        Args:
            source_vm         (str):   source virtual machine
            vm_type           (str):   Source hypervisor name as a constant from
                                       Virtualization_replication.py

        Returns       (object): object of VirtualMachine
        """
        self.vendor_vm = self.__type_class_mapping.get(vm_type)(self.__admin_console)
        self.__table.access_action_item(source_vm, self.__label['label.overrideReplicationOptions'])
        self.__admin_console.wait_for_completion()
        return self.vendor_vm

    @PageService()
    def get_vm_override_details(self, source_vm: str, vm_type: str,
                                field_values: bool = True, field_statuses: bool = True):
        """
        Retrieves the override details for a virtual machine.

        Args:
            source_vm (str): The name of the source virtual machine.
            vm_type (str): The type of the virtual machine.
            field_status (bool, optional): Flag to indicate whether to retrieve field statuses or field values. 
                Defaults to False.

        Returns:
            dict: A dictionary containing the override details for the virtual machine.
        """
        self.edit_virtual_machines(source_vm, vm_type)
        field_details = self.vendor_vm.get_all_field_details(field_values=field_values,
                                                             field_statuses=field_statuses)
        self.vendor_vm.cancel()
        return field_details

    @PageService()
    def remove_virtual_machines(self, vm_name: str):
        """Removes the virtual machines from the replication group"""
        self.__table.select_rows([vm_name])
        self.__table.access_toolbar_menu('Delete')
        self.__dialog.click_submit()

class MonitorTab:
    """Class for monitor tab of the group details page"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props

        self._monitor = ReplicationMonitor(self.__admin_console)
        self._continuous_monitor = ContinuousReplicationMonitor(self.__admin_console)

    @PageService()
    def get_replication_group_details(self, vm_name):
        """Returns the replication VMs and their configuration from the table"""
        return self.__table.get_row_data(vm_name)

    @PageService()
    def get_sync_status(self, source):
        """
        Returns Sync Status for source
        Args:
            source(string): source name
        """
        return self._monitor.get_replication_group_details(source)[self.__label['header.syncStatus']]

    @PageService()
    def get_failover_status(self, source):
        """
        Returns: failover status
        Args:
            source(string): source name
        """
        return (self._monitor.get_replication_group_details(source)[self.__label['header.failoverStatus']])

    @PageService()
    def get_vm_details(self, vm_name):
        """Returns the replication VMs and their configuration from the table"""
        table_data = self._monitor.get_replication_group_details(vm_name)
        if not table_data or self.__label['header.clientName'] not in table_data.keys():
            raise CVWebAutomationException("Get VM details for overview tab is called "
                                           "from configuration tab or the column does not exist")
        return table_data

    @PageService()
    def remove_virtual_machines(self, source_vms: str | list, delete_destination=True):
        """Removes the virtual machines from the replication group"""
        return self._monitor.delete(source_vms, replication_group=None, delete_destination=delete_destination)


class AdvancedTab:
    """Class for advanced tab of the group details page"""

    def __init__(self, admin_console: AdminConsole):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)

        self._advanced_options = _AdvancedOptionsOperations(admin_console)
        self._customisation_scripts = _CustomizationScripts(admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__label = self.__admin_console.props
        self.__modal_panel = RPanelInfo(self.__admin_console)

    @property
    def advanced_options(self):
        return self._advanced_options

    @property
    def customization_scripts(self):
        return self._customisation_scripts

    @PageService()
    def edit_transport_mode(self, mode):
        """
        Change transport mode
        Args:
            mode            (str):   transport mode to be selected
        """
        self.__modal_panel = RPanelInfo(self.__admin_console, title=self.__label['label.advanced.options'])
        self.__modal_panel.edit_tile_entity(self.__label['header.transportMode'])
        self.__dialog.select_dropdown_values(drop_down_id="transportModeDropdown", values=[mode])
        self.__dialog.click_submit()

        notification = self.__admin_console.get_notification()
        if notification != self.__label['msg.RGSuccessfulUpdate']:
            raise CVWebAutomationException("Expected notification [%s], "
                                           "found:[%s]" %
                                           (self.__label['msg.RGSuccessfulUpdate'], notification))

    @PageService()
    def edit_snapshots(self, snapshots):
        """
        Edit snapshots to retain on destination vm
        Args:
            snapshots            (str):   number of snapshots
        """
        self.__modal_panel = RPanelInfo(self.__admin_console, title=self.__label['label.advanced.options'])
        self.__modal_panel.edit_tile_entity(self.__label['label.noOfRecoveryPoints'])
        self.__modal_panel.fill_input(self.__label['label.noOfRecoveryPoints'], snapshots)
        self.__modal_panel.submit()


class ReplicationDetails:
    """Class for virtualiztion Replication Group details Page"""

    def __init__(self, admin_console):
        self.__admin_console : AdminConsole = admin_console
        self.__alert = Alert(admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)

        self.overview = OverviewTab(self.__admin_console)
        self.monitorTab = MonitorTab(self.__admin_console)
        self.configuration = ConfigurationTab(self.__admin_console)
        self.advancedTab = AdvancedTab(self.__admin_console)

        self.__admin_console.load_properties(self.__admin_console.navigator)
        self.__admin_console.load_properties(self)
        self.__label = self.__admin_console.props
        self.__admin_console.load_properties(self, unique=True)
        self.__unique_labels = self.__admin_console.props[self.__class__.__name__]

    @WebAction()
    def __edit_replication_group_name(self, group_name):
        """
        Edit the replication group name
        Args:
            group_name(string): New name of the replication group
        """
        element = self.__admin_console.driver.find_element(By.XPATH, 
            "//h1[contains(@id,'changeNameTitle')]")
        element.send_keys(Keys.CONTROL, 'a', Keys.DELETE)
        element.send_keys(group_name, '\n')

    @PageService()
    def edit_replication_group_name(self, group_name):
        """
        Edit the replication group name
        Args:
            group_name(string): New name of the replication group
        """
        self.__edit_replication_group_name(group_name)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def get_replication_group_name(self):
        """Return replication name"""
        return self.__admin_console.driver.find_element(By.XPATH, 
            "//h1[contains(@id,'changeNameTitle')]").text

    @WebAction()
    def replicate_now(self):
        """
        click on replicate now
        """
        self.__page_container.access_page_action_from_dropdown(self.__label['label.replicate'])
        self.__dialog.click_submit(wait=False)
        return self.__alert.get_jobid_from_popup()

    @WebAction()
    def view_test_failover_vms(self, source_vms: list):
        """
        Click on view test failover VMs
        """
        self.__page_container.access_page_action_from_dropdown(self.__label['label.viewTestFailoverVMs'])
        self.__admin_console.wait_for_completion()
        return TestFailoverVMs(self.__admin_console).get_all_vms_info(source_vms)

    @PageService()
    def _perform_group_level_dr_operation(self, operation_label, checkbox_id=None, select=False):
        """
        Perform DR operation
        Args:
            operation_label(string): label of the operation to be performed
            checkbox_id(string): id of the checkbox to be selected/deselected
            select(bool): select/deselect the checkbox
        """
        self.__page_container.click_action_item_from_menu(
            self.__unique_labels['label.failover'], operation_label, case_insensitive_selection=True)
        self.__dialog.select_deselect_checkbox(
            checkbox_id=checkbox_id, select=select) if checkbox_id else None
        self.__dialog.click_submit(wait=False)
        return self.__alert.get_jobid_from_popup()

    @PageService()
    def unplanned_failover(self, retain_disk_snapshots=True):
        """Performs unplanned failover (group level)"""
        job_id = self._perform_group_level_dr_operation(self.__label['label.unplannedFailover']) if retain_disk_snapshots else self._perform_group_level_dr_operation(
            self.__label['label.unplannedFailover'], 'retainDiskSnapShot', retain_disk_snapshots)
        return job_id

    @PageService()
    def planned_failover(self, retain_disk_snapshots=True):
        """Performs planned failover (group level)"""
        job_id = self._perform_group_level_dr_operation(self.__label['label.plannedFailover']) if retain_disk_snapshots else self._perform_group_level_dr_operation(
            self.__label['label.plannedFailover'], 'retainDiskSnapShot', retain_disk_snapshots)
        return job_id

    @PageService()
    def undo_failover(self):
        """Performs undo failover (group level)"""
        job_id = self._perform_group_level_dr_operation(
            self.__label['label.failback'], 'discardChanges', True)
        return job_id

    @PageService()
    def failback(self):
        """Performs failback (group level)"""
        job_id = self._perform_group_level_dr_operation(
            self.__label['label.failback'])
        return job_id

    @PageService()
    def test_failover(self):
        """Performs Test Failover (group level)"""
        job_id = self._perform_group_level_dr_operation(
            self.__label['label.testFailover'])
        return job_id

    @PageService()
    def resume(self):
        """Perform resume (group level)"""
        self.__admin_console.access_page_action_menu(self.__label['label.undoFailover'])

    @PageService()
    def access_overview_tab(self):
        """Access overview tab"""
        self.__page_container.select_tab(self.__label["header.overview"])

    @PageService()
    def access_monitor_tab(self):
        """Access configuration tab"""
        self.__page_container.select_tab(self.__label["label.monitor"])

    @PageService()
    def access_configuration_tab(self):
        """Access configuration tab"""
        self.__page_container.select_tab(self.__label["header.configuration"])

    @PageService()
    def access_advanced_tab(self):
        """Access advanced tab"""
        # TODO : Update to label once the corresponding label is available
        self.__page_container.select_tab("Advanced")

class EditVMwareVirtualMachine(_VMwareVMOptions):
    """Edit virtual machine parameters using this class"""

    def __init__(self, admin_console):
        _VMwareVMOptions.__init__(self, admin_console)
        self.__disabled_fields = ["drvm_name", "destination_host",
                                  "vm_storage_policy", "datastore", "resource_pool"]

    @property
    def expected_disabled_fields(self):
        return {field: True for field in self.__disabled_fields}

    @WebAction()
    def __is_general_settings_editable(self):
        """
        If parameters are editable then return true otherwise false
        Returns  (Boolean): True if the General settings is editable otherwise false
        """
        xp = "//div[contains(text(), 'General settings')]/..//div[contains(@data-ng-disabled, " \
             "'repTarget')]"
        parameters = self._admin_console.driver.find_elements(By.XPATH, xp)
        # status below will be listof 'true' if its disabled
        status = [each_param.get_attribute('disabled') for each_param in parameters]
        if [each_status for each_status in status if each_status != 'true']:
            # if disabled is not 'true' then its editable, so returning True
            return True
        return False

    @PageService()
    def is_general_settings_editable(self):
        """
        Returns  (Boolean): True if the General settings is editable otherwise false
        """
        return self.__is_general_settings_editable()

    @PageService()
    def edit_network_settings(self, source_network, destination_network):
        """
        Edit network setting
        Args:
            source_network                (str): specify the source network
            destination_network           (str): specify the destination network
        """
        network_settings = self.edit_network()
        network_settings.select_source_network(source_network)
        network_settings.select_destination_network(destination_network)
        network_settings.save()

    @WebAction()
    def __get_network_settings(self):
        """
        Read network settings information
        Returns          (list): table content
        """
        xp = "//*[@accordion-label='label.networkSettingsVMWare']//span[@title]"
        return [each_element.text for each_element in
                self._admin_console.driver.find_elements(By.XPATH, xp)]

    @PageService()
    def get_network_settings(self):
        """
        Read network settings
        Returns(list): list of column data
        """
        self.expand_tab(self._label['label.networkSettingsVMWare'])
        return self.__get_network_settings()

    @PageService()
    def set_vm_display_name(self, name):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Field VM display name is disabled")

    @PageService()
    def set_destination_host(self, host):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Field Destination host is disabled")

    @PageService()
    def select_datastore(self, datastore):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Field datastore is disabled")

    @PageService()
    def select_resource_pool(self, resource_pool_name):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Field resource pool is disabled")

    @PageService()
    def set_vm_folder(self, name):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Field Vm folder is disabled")


class EditAzureVirtualMachine(_AzureVMOptions):
    """Edit the Azure virtual machine options using this class"""

    def __init__(self, admin_console: AdminConsole):
        """Initialises the components required for functions"""
        super().__init__(admin_console)
        self.__driver = self._admin_console.driver
        self.__modal_panel = ModalPanel(admin_console)
        self.__disabled_fields = ["drvm_name", "resource_group", "region", "storage_account"]

    @property
    def expected_disabled_fields(self):
        return {field: True for field in self.__disabled_fields}

    @WebAction()
    def __get_selected_dropdown_option(self, select_id: str) -> str or None:
        """Gets the current value from the select"""
        options = self.__driver.find_elements(By.XPATH, f"//*[@id='{select_id}']//option")
        for option in options:
            if option.get_attribute("selected") is not None:
                return option.text
        return None

    @WebAction()
    def __get_checkbox_value(self, checkbox_id: str) -> bool:
        """Gets the value of the given checkbox"""
        return (self.__driver.
                find_element(By.XPATH, f"//input[@type='checkbox' and @id='{checkbox_id}']").
                is_selected())

    @property
    @PageService()
    def vm_size(self) -> str:
        """Returns the selected VM size from the panel"""
        return self.__get_selected_dropdown_option('azureVmSize')

    @property
    @PageService()
    def availability_zone(self) -> str:
        """Returns the selected availability_zone from the panel"""
        return self.__get_selected_dropdown_option('azureAvailabilityZone')

    @property
    @PageService()
    def virtual_network(self) -> str:
        """Returns the current value of virtual network"""
        return self.get_selected_multi_select(
            'selectVirtualNetworkAzure_isteven-multi-select_#2554')

    @property
    @PageService()
    def security_group(self) -> str:
        """Returns the current security group"""
        return self.get_selected_multi_select('azureSecurityGroup_isteven-multi-select')

    @property
    @PageService()
    def public_ip(self) -> bool:
        """Returns the value of the checkbox create public IP"""
        return self.__get_checkbox_value('createPublicIp')

    @property
    @PageService()
    def restore_managed_vm(self) -> bool:
        """Returns the value of the checkbox restore as a managed VM"""
        return self.__get_checkbox_value('restoreAsManagedVM')

    @PageService()
    def select_virtual_network(self, virtual_network: str):
        """Selects the virtual network from the options"""
        _AzureVMOptions.virtual_network(self, virtual_network)

    @PageService()
    def select_public_ip(self, enabled: bool):
        """Checks/unchecks the box for create public IP option"""
        _AzureVMOptions.create_public_ip(self, enabled)


class EditHyperVVirtualMachine(_HyperVVMOptions):
    """Edit virtual machine parameters using this class"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__driver = self._admin_console.driver
        self.__modal_panel = ModalPanel(admin_console)
        self.__disabled_fields = ["drvm_name"]

    @property
    def expected_disabled_fields(self):
        return {field: True for field in self.__disabled_fields}

    @PageService()
    def set_vm_display_name(self, name):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Vm display name is disabled")

    @property
    @PageService()
    def network(self) -> str:
        """Returns the current value of network"""
        return self.get_selected_multi_select('networkName')


class EditAWSVirtualMachine(_AWSVMOptions):
    """Edit virtual machine parameters using this class"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__driver = self._admin_console.driver
        self.__modal_panel = ModalPanel(admin_console)
        self.__disabled_fields = ["drvm_name", "availability_zone"]

    @property
    def expected_disabled_fields(self):
        return {field: True for field in self.__disabled_fields}

    @WebAction()
    def get_value(self, input_field_name: str) -> str:
        """Gets the current selected value from the multi-select"""
        return self.__driver.find_element(By.XPATH, f"//*[@name='{input_field_name}']").get_property('value')

    @PageService()
    def set_vm_display_name(self, name: str):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Vm display name is disabled")

    @PageService()
    def select_availability_zone(self, availibility_zone: str):
        """Not implemented for editing since field is disabled"""
        raise NotImplementedError("Availability Zone is disabled")

    @property
    @PageService()
    def network(self) -> str:
        """Returns the current value of network"""
        return self.get_value('networkSettings')

    @property
    @PageService()
    def volume_type(self) -> str:
        """Returns the current value of volume type"""
        return self.get_selected_multi_select('volumeTypes_isteven-multi-select')

    @property
    @PageService()
    def encryption_key(self) -> str:
        """Returns the current value of encryption key"""
        return self.get_selected_multi_select('encryptionKeys_isteven-multi-select')

    @property
    @PageService()
    def iam_role(self) -> str:
        """Returns the current value of IAM role"""
        return self.get_selected_multi_select('iamRole')

    @property
    @PageService()
    def security_group(self) -> str:
        """Returns the current value of security group"""
        return self.get_selected_multi_select('securityGroups')

    @property
    @PageService()
    def instance_type(self) -> str:
        """Returns the current value of instance type"""
        return self.get_selected_multi_select('instanceTypes_isteven-multi-select_#7669')


class _AddVirtualMachine:
    """Class to introduce common functionality for adding cross-platform VMs"""

    def __init__(self, admin_console: AdminConsole, vm_type: Vendors_Complete.VMWARE.value):
        """Add content options from virtualization_replication"""
        self._admin_console = admin_console
        self._modal_panel = RModalPanel(admin_console)
        self._dialog = RModalDialog(admin_console)
        self.vm_type = vm_type
        self.content = _Content(admin_console)
        self.override_options = _OverrideOptions(self._admin_console, vm_type)

    def add_vm(self, source_vms: dict | list, view_mode=None):
        """
        Adds virtual machines to the group with default options.

        Args:
            source_vms (dict | list): A dictionary or list of virtual machines to be added.

        Returns:
            None
        """
        expand_folder = True
        if self.vm_type in Vendors_Complete.HYPERV.value:
            expand_folder = False
        self.content.select_vm_from_browse_tree(source_vms, view_mode=view_mode, navigate=False, expand_folder=expand_folder)
        # TODO: Override support, if required
        self._modal_panel.submit()
