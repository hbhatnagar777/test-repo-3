# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Use this module to configure vitualization replication group.
"""

from abc import abstractmethod
from enum import Enum
from selenium.webdriver.common.by import By
from time import sleep

from AutomationUtils.logger import get_log
from DROrchestration.DRUtils.DRConstants import SiteOption, TimePeriod, Vendors, Vendors_Complete
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Storage.DiskStorage import DiskStorage
from Web.AdminConsole.DR.recovery_targets import _VMWareRecoveryTarget
from Web.AdminConsole.DR.vendor_options import _AWSOptions, _AzureOptions, _HyperVOptions, _VMwareOptions
from Web.Common.page_object import WebAction, PageService
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.browse import RContentBrowse as RB
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type, HypervisorDisplayName

SOURCE_HYPERVISOR_AZURE = HypervisorDisplayName.MICROSOFT_AZURE.value
SOURCE_HYPERVISOR_VMWARE = HypervisorDisplayName.VIRTUAL_CENTER.value
SOURCE_HYPERVISOR_HYPERV = HypervisorDisplayName.MS_VIRTUAL_SERVER.value
SOURCE_HYPERVISOR_AWS = hypervisor_type.AMAZON_AWS.value

class _ReplicationGroupCommonConfig:
    """
    Module for common methods
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console : AdminConsole = admin_console
        self._admin_console.load_properties(self)
        self._driver = admin_console.driver
        self._drop_down = DropDown(admin_console)
        self._table = Rtable(admin_console)
        self._wizard = Wizard(admin_console)
        self._browse = RB(admin_console)
        self._alert = Alert(admin_console)

    def _content_to_delimited_paths(self, content:dict, delimiter="/", prefix=""):
        """
        Converts a nested dictionary into a list of delimited strings.

        Args:
            content (dict): The nested dictionary to be converted.
            delimiter (str, optional): The delimiter used to separate the keys and values. Defaults to "/".

        Returns:
            list: A list of delimited strings representing the key-value pairs in the dictionary.
        """
        list_of_paths = []
        for key, value in content.items():
            _prefix = prefix + key + delimiter
            if isinstance(value, dict):
                list_of_paths.extend(self._content_to_delimited_paths(content=value, delimiter=delimiter, prefix=_prefix))
            elif isinstance(value, list):
                [list_of_paths.append(_prefix + str(x)) for x in value]
            else:
                list_of_paths.append(_prefix + str(value))
        return list_of_paths

    @PageService()
    def _select_from_tree(self, content : dict | list, expand_folder):
        """
        Select content from browse tree

        Args:
            paths
                (dict)    -   {"node_1" : ['leaf1', 'leaf2'], "node_2" : ['leaf_3']}
                (list)    -   List of paths to be selected

        """
        flattened_content = self._content_to_delimited_paths(content) if isinstance(content, dict) else content
        for path in flattened_content:
            self._browse.select_path(path, partial_selection=True, wait_for_element=True,  expand_folder=expand_folder)

class _Content(_ReplicationGroupCommonConfig):
    """use this module for configure replication group content page operations"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super().__init__(admin_console)
        self._modal_dialog = RModalDialog(self._admin_console)

    @PageService()
    def set_name(self, name):
        """
        Set name in content page
        Args:
            name      (str):   Name of the replication group

        """
        self._wizard.fill_text_in_field(id="name", text=name)

    @PageService()
    def select_production_site_hypervisor(self, source_hypervisor):
        """
        Selects the source/production site hypervisor
        Args:
            name      (str):   Name of the replication group

        """
        self._wizard.select_drop_down_values(
            id="Hypervisor", values=[source_hypervisor]
        )
    
    @PageService()
    def select_vm_group(self, vm_group, vm_info: dict | list, expand_folder: bool = True):
        """
        Selects the VM group
        Args:
            vm_group      (str):   Name of the VM group
            
            vm_info (dict | list): Information about the VMs to be selected.
                - If `vm_info` is a dictionary, it should be in the format:
                    {"region_1": ['vm_1', 'vm_2'], "region_2": ['vm_3']}
                - If `vm_info` is a list, it should be a list of paths to be selected.
            
            expand_folder (bool, optional): Whether to expand the folders in the browse tree. Defaults to True.
        """
        self._table.access_toolbar_menu("Add")
        self._admin_console.wait_for_completion()
        self._wizard.select_drop_down_values(
            id="VMGroupDropdown", values=[vm_group]
        )
        self._select_from_tree(vm_info, expand_folder)
        self._modal_dialog.click_submit()

    @PageService()
    def select_vm_from_browse_tree(self, vm_info: dict | list, view_mode: str = None, navigate: bool = True, expand_folder: bool = True, vm_group: str = None):
        """
        Select content for subclient from the browse tree

        Args:
            vm_info (dict | list): Information about the VMs to be selected.
                - If `vm_info` is a dictionary, it should be in the format:
                    {"region_1": ['vm_1', 'vm_2'], "region_2": ['vm_3']}
                - If `vm_info` is a list, it should be a list of paths to be selected.

            view_mode (str, optional): The view mode to be set (e.g., "Instance View", "Region View", "Tags View").
                Defaults to None.

            navigate (bool, optional): Whether to navigate to the browse tree. If True, it will access the toolbar menu
                and wait for completion. Defaults to True.

            expand_folder (bool, optional): Whether to expand the folders in the browse tree. Defaults to True.
        """
        if navigate:
            self._table.access_toolbar_menu("Add")
            self._admin_console.wait_for_completion()

        if view_mode:
            self._wizard.select_drop_down_values(
                id="vmBrowseView", values=[view_mode]
            )
        
        if vm_group:
            self._wizard.select_drop_down_values(
                id="VMGroupDropdown", values=[vm_group]
            )

        self._select_from_tree(vm_info, expand_folder)
        self._modal_dialog.click_submit()


class _RecoveryOptions(_ReplicationGroupCommonConfig):
    """use this module for configure replication group target page operations"""

    class SiteOption(Enum):
        """ENUM Class for Site Option to ID mapping"""

        HotSite = "HOT"
        WarmSite = "WARM"

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super().__init__(admin_console)
        self._advanced_options_label = "label.advanced.options"

    @PageService()
    def select_recovery_target(self, target):
        """
        Select recovery target
        Args:
            target              (str):   Specify the recovery target
        """
        self._wizard.select_drop_down_values(
            id="recoveryTargetDropdown", values=[target]
        )

    @PageService()
    def select_continuous_replication_type(self):
        """
        Click on continuous replication radio button
        """
        self._driver.find_element(
            By.XPATH, "(//input[@id='replicationType'])[2]"
        ).click()

    @PageService()
    def _set_frequency_number(self, number):
        """
        Select frequency number
        Args:
            number              (int):   frequency to be set
        """
        self._wizard.fill_text_in_field(id="time", text=number)

    @PageService()
    def _select_frequency_period(self, period):
        """
        Args:
            period             (str):   frequency period(Hours/Minutes/Days)
        """
        self._wizard.select_drop_down_values(id="option",
                                             values=[period],
                                             partial_selection=True,
                                             case_insensitive_selection=True)

    @PageService()
    def set_frequency(self, frequency_duration, frequency_period=TimePeriod.HOURS.value):
        """
        Set frequency
        Args:
            frequency_duration       (int):   frequency to be set
            frequency_period       (str):   frequency period(Hours/Minutes/Days)
        """
        self._set_frequency_number(frequency_duration)
        self._select_frequency_period(frequency_period)

    @PageService()
    def select_rto(self, site_option=SiteOption.HotSite.value):
        """
        Selects the desired Recovery Time Objective (RTO) for virtualization replication.

        Args:
            site_option (str): The site option to select (HotSite/WarmSite). Defaults to 'HotSite'.

        Returns:
            None
        """
        self._wizard.select_radio_button(id=site_option)

    @PageService()
    def replication_on_group_creation(self, enable=True):
        """
        Enable or disable replication on group creation
        """
        self._wizard.enable_disable_toggle(self._admin_console.props["label.enableReplicationAfterGroupCreation"], enable)

    @PageService()
    def select_access_node(self, access_node):
        """
        Select access node (Orchestrated Replication)
        Args:
            access_node              (str): Provide access node name
        """
        self._wizard.select_drop_down_values(
            id="accessNodeDropdown", values=[access_node]
        )


class _StorageOrCache(_ReplicationGroupCommonConfig):
    """use this module for configure replication group storage/cache page operations"""

    class RetentionPeriodConstants:
        """Retention Period constants"""

        CONSTANT_DAYS = "Day(s)"
        CONSTANT_WEEKS = "Week(s)"
        CONSTANT_MONTHS = "Month(s)"
        CONSTANT_YEARS = "Year(s)"
        CONSTANT_INFINITE = "Infinite"

    class Storage_Copy(Enum):
        """ENUM Class for Storage Copy to ID mapping"""

        Primary = "storageDropdownprimaryCopy"
        Secondary = "storageDropdownsecondaryCopy"
        Tertiary = "storageDropdowntertiaryCopy"

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super().__init__(admin_console)
        self.continuous_rpstore = RecoveryPointStore(self._admin_console)

    @PageService()
    def select_storage(self, storage_name, storage_copy=Storage_Copy.Primary.value):
        """
        Select storage
        Args:
            storage_name              (str): Provide storage name
        """
        # TODO : Copy for replication
        if storage_copy != self.Storage_Copy.Primary.value:
            self._wizard.click_button(name="Add copy")
        self._wizard.select_drop_down_values(
            id=storage_copy, values=[storage_name]
        )

    @PageService()
    def select_copy_for_replication(self, storage_name):
        """
        Select storage
        Args:
            storage_name              (str): Provide storage name
        """
        self._wizard.select_drop_down_values(id="replicationCopyDropdown",
                                             values=[storage_name],
                                             partial_selection=True)
    
    @PageService()
    def select_media_agent(self, media_agent):
        """
        Select media agent (Orchestrated Replication)
        Args:
            media_agent              (str): Provide media agent name
        """
        self._wizard.select_drop_down_values(
            id="mediaAgentDropdown", values=[media_agent]
        )

    @PageService()
    def select_continuous_storage(self, storage_name):
        """
        Select the storage
        Args:
            storage_name(str):specify the storage name which will be used while
                              configuring continuous replication pair
        """
        self._drop_down.select_drop_down_values(
            values=[storage_name], drop_down_id="storage"
        )

    @PageService()
    def replicate_using_snapshots(self, snapshot_engine: str = None, enable : bool = True):
        """
        Select/deselect use snapshot on source option
        Args:
            enable (bool): True/False to select/deselect
        """
        self._wizard.enable_disable_toggle(self._admin_console.props["label.replicateUsingSnapshots"], enable=enable)
        if snapshot_engine:
            self._wizard.select_drop_down_values(id="snapshotEngineDropdown",
                                                 values=[snapshot_engine],
                                                 partial_selection=True)


class _OverrideOptions(_ReplicationGroupCommonConfig):
    """use this module for configure replication group opverride options page operations"""

    def __init__(self, admin_console, hypervisor_type):
        """
        Args:
            admin_console   : adminconsole base object
            hypervisor_type : SOURCE_HYPERVISOR constants
        """
        super().__init__(admin_console)
        self._modal_dialog = RModalDialog(self._admin_console)
        self.__type = hypervisor_type
        self.__type_class_mapping = {
            Vendors.AWS.value: _AWSVMOptions,
            Vendors_Complete.AZURE.value: _AzureVMOptions,
            Vendors_Complete.HYPERV.value: _HyperVVMOptions,
            Vendors_Complete.VMWARE.value: _VMwareVMOptions
        }
        self.vm_options = None

    @PageService()
    def override_vms(self, source_vm=[], multi_vm_override=False):
        """
        Enable override vms toggle and edit virtual machine parameters
        Args:
            source_vm (str/list):
                1. VM name for single VM override
                2. list of VM names for multi-VM override (optional)
            multi_vm_override (bool):
                1. True/False for multi-VM/single-VM edit
        """
        self.vm_options = self.__type_class_mapping.get(self.__type, _EditVMCommon)(
            self._admin_console
        )

        if multi_vm_override:
            self._table.select_all_rows()
            self._table.access_toolbar_menu("Override replication options")
        else:
            self._table.access_action_item(source_vm, "Override replication options")

        self._admin_console.wait_for_completion()
        return self.vm_options

    @PageService()
    def deselect_vms(self, source_vm):
        """Deselects the vm row that is currently selected for override"""
        self._table.deselect_rows([source_vm])

    @PageService()
    def __get_field_value(self, field_id, use_value=False):
        """Gets the value of the field id"""
        #TODO : Deprecate method after reviewing logic vendors other than AWS
        if self._admin_console.check_if_entity_exists(
            "xpath", f"//select[@id='{field_id}' or @name='{field_id}']//option"
        ):
            options = [
                element
                for element in self._driver.find_elements(
                    By.XPATH,
                    f"//select[@id='{field_id}' or @name='{field_id}']//option",
                )
                if element.get_attribute("selected")
            ]
            return options[0].get_attribute("value") if use_value else options[0].text

        if self._admin_console.check_if_entity_exists(
            "xpath", f"//*[@id='{field_id}']//button"
        ):
            return self._driver.find_element(
                By.XPATH, f"//*[@id='{field_id}']//button//div[@class='buttonLabel']"
            ).text

        if self._admin_console.check_if_entity_exists(
            "xpath", f"//*[@name='{field_id}' or @id='{field_id}']"
        ):
            return self._driver.find_element(
                By.XPATH, f"//*[@name='{field_id}' or @id='{field_id}']"
            ).get_property("value")

        if self._admin_console.check_if_entity_exists(
            "xpath", f"//*[@name='{field_id}' or @id='{field_id}']/option"
        ):
            return self._driver.find_element(
                By.XPATH, f"//*[@name='{field_id}' or @id='{field_id}']/option"
            ).get_property("value")

        if self._admin_console.check_if_entity_exists(
            By.XPATH,
            f"//*[@name='{field_id}' or @id='{field_id}']"
            f"/ancestor::div[contains(@class, 'Dropdown-selectMenu')]",
        ):
            return self._driver.find_element(
                By.XPATH, f"//*[@name='{field_id}' or @id='{field_id}']"
            ).get_property("value")

        return None

    @PageService()
    def _get_vm_details(self, source_vm, field_ids=[]):
        """Get the VM details from the override options page"""
        self.override_vms(source_vm)
        self._admin_console.wait_for_completion()
        vm_details = self.vm_options.get_all_field_details() if len(field_ids) == 0 else {
            field_id: self.__get_field_value(field_id) for field_id in field_ids
        }
        self._modal_dialog.click_cancel()
        self._table.clear_search()
        return vm_details

    @PageService()
    def get_vmware_details(self, source_vm, field_ids=[]):
        """Get the VM details from the override options page"""
        return self._get_vm_details(source_vm, field_ids)

    @PageService()
    def get_azure_vm_details(self, source_vm, field_ids=[]):
        """Get the VM details from the override options page"""
        return self._get_vm_details(source_vm, field_ids)

    @PageService()
    def get_hyperv_details(self, source_vm, field_ids=[]):
        """Get the VM details from the override options page"""
        return self._get_vm_details(source_vm, field_ids)

    @PageService()
    def get_aws_vm_details(self, source_vm, field_ids=[]):
        """Get the VM details from the override options page"""
        #TODO : Convert to a vendor agnostic method
        return self._get_vm_details(source_vm, field_ids)


class _AdvancedOptions(_ReplicationGroupCommonConfig):
    """Module for configuring Advanced Options for replication group creation"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super().__init__(admin_console)

    @PageService()
    def validate_destination_vm(self, enable=True):
        """
        Select/deselect validate destination VM
        Args:
            enable                (bool): True/False to select/deselect
        """
        self._wizard.enable_disable_toggle(self._admin_console.props["label.powerOn.replication"], enable=enable)

    @PageService()
    def unconditionally_overwrite_vm(self, enable=True):
        """
        Select/Deselct Unconditionally overwrite vm
        Args:
            enable                (bool): True/False to select/deselect
        """
        self._wizard.enable_disable_toggle(self._admin_console.props["warning.overwriteVM"], enable=enable)

    @PageService()
    def continue_to_next_priority(self, enable=True):
        """
        Select/Deselct 'Continue to next priority on Failure'
        Args:
            enable                (bool): True/False to select/deselect
        """
        self._wizard.enable_disable_toggle(self._admin_console.props["label.continueOnFailure"], enable=enable)

    @PageService()
    def set_delay_between_priority(self, delay):
        """
        Enters the delay value (Product support is limited to minutes)
        Args:
            delay              (int):   delay to be set (in minutes)
        """
        self._wizard.fill_text_in_field(id="failoverDelay", text=delay, delete_during_clear=False)

    @PageService()
    def set_transport_mode(self, transportmode):
        """
        set Transport mode
        Args:
            Transport mode      (str) : name of mode to be set
        """
        self._wizard.select_drop_down_values(
            id="transportModeDropdown", values=[transportmode]
        )


class _AdvancedOptions_VMWare(_AdvancedOptions):
    """Class for configuring vmware recovery target options"""

    @PageService()
    def set_snapshots_to_retain_on_destination_vm(self, snapshots):
        """
        set snapshots to retain on destination vm
        Args:
            snapshots           (str): number of snapshots
        """
        self._wizard.fill_text_in_field(id="snapshotsToRetain", text=snapshots, delete_during_clear=False)

    @PageService()
    def set_disk_provisioning(self, disk_type):
        """
        set disk provisioning
        Args:
            disk provisioning           (str) : name of disk to be set
        """
        self._wizard.select_drop_down_values(id="diskProvisioningDropdown", values=[disk_type])


class _EditVMCommon(_ReplicationGroupCommonConfig):
    """Edit virtual machine parameters using this class"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self._modal_dialog = RModalDialog(self._admin_console)
        self._log = get_log()

    @WebAction()
    def __is_tab_open(self, tab_name) -> bool:
        """Checks to see if the tab is open or not"""
        return "Collapse" in (
            self._admin_console.driver.find_element(
                By.XPATH,
                f"//div[@class='grid-main-container']//h2[contains(text(), '{tab_name}')]"
                f"/ancestor::div[contains(@class,'grid-toolbar')]//button[contains(@class,'grid-toolbar')]",
            ).get_attribute("aria-label")
        )

    @WebAction()
    def __click_expand_tab(self, tab_name):
        """Clicks the expand tab"""
        self._admin_console.driver.find_element(
            By.XPATH,
            f"//div[@class='grid-main-container']//h2[contains(text(), '{tab_name}')]"
            f"/ancestor::div[contains(@class,'grid-toolbar')]//button[contains(@class,'grid-toolbar')]",
        ).click()

    @PageService()
    def expand_tab(self, tab_name):
        """Expands the additional optional tags"""
        if not self.__is_tab_open(tab_name):
            self.__click_expand_tab(tab_name)
            self._admin_console.wait_for_completion()

    @PageService()
    def set_vm_display_name(self, name):
        """
        Update display name
        Args:
            name(String): specify the vm display name
        """
        self._modal_dialog.fill_text_in_field(element_id="vmDisplayNameField", text=name)

    @PageService()
    def set_vm_affix(self, prefix=None, suffix=None):
        """
        Update Prefix or Suffix
        Applicable for multi-VM override
        Args:
            prefix(Str): specify the prefix
            suffix(Str): specify the suffix
        """
        if prefix:
            self._modal_dialog.enable_disable_toggle(id="prefix", enable=True)
            self._modal_dialog.fill_text_in_field(element_id="prefixDisplayName", text=prefix)
        if suffix:
            self._modal_dialog.enable_disable_toggle(id="suffix", enable=True)
            self._modal_dialog.fill_text_in_field(element_id="suffixDisplayName", text=suffix)

    @PageService()
    def cancel(self):
        """Click on cancel"""
        self._modal_dialog.click_cancel()

    @PageService()
    def save(self):
        """Click on save"""
        self._modal_dialog.click_submit()

    @WebAction()
    def get_selected_multi_select(self, multi_select_id: str) -> str:
        """Gets the current selected value from the multi-select"""
        return self._driver.find_element(
            By.XPATH, f"//*[@id='{multi_select_id}']//button"
        ).text

    @WebAction()
    def is_field_disabled(self, field_id: str) -> bool:
        """Checks if field is disabled and then waits for delay"""
        select_disabled = False
        select_option_disabled = False
        if self._admin_console.check_if_entity_exists(
            "xpath", f"//select[@name='{field_id}']"
        ):
            select_disabled = bool(
                self._driver.find_element(
                    By.XPATH, f"//select[@name='{field_id}']"
                ).get_attribute("data-ng-disabled")
            )
        # select with name, option -> disabled attribute
        if self._admin_console.check_if_entity_exists(
            "xpath", f"//select[@name='{field_id}']//option"
        ):
            select_option_disabled = bool(
                [
                    element
                    for element in self._driver.find_elements(
                        By.XPATH, f"//select[@name='{field_id}']//option"
                    )
                    if element.get_attribute("disabled") is not None
                ]
            )
        if select_disabled or select_option_disabled:
            return True
        self._log.info(f"Did not find disabled select with ID {field_id}")
        # ist-event-multiselect disabled check
        if self._admin_console.check_if_entity_exists(
            "xpath", f"//*[@id='{field_id}']//button"
        ):
            return bool(
                self._driver.find_element(
                    By.XPATH, f"//*[@id='{field_id}']//button"
                ).get_attribute("ng-disabled")
            )
        self._log.info(
            f"Did not find disabled ist-event-multiselect with ID {field_id}"
        )
        # input with name, parent cv-display-name-azure, parent div -> disabled attribute
        if self._admin_console.check_if_entity_exists(
            "xpath",
            f"//input[@name='{field_id}']/"
            f"ancestor::cv-display-name-azure/parent::div",
        ):
            disabled_attr = self._driver.find_element(
                By.XPATH,
                f"//input[@name='{field_id}']/"
                f"ancestor::cv-display-name-azure/parent::div",
            ).get_attribute("disabled")
            return bool(disabled_attr)
        self._log.info(f"Did not find cv-display-name-azure with ID {field_id}")
        if self._admin_console.check_if_entity_exists(
            "xpath", f"//input[@name='{field_id}']"
        ):
            # input with name -> disableEditing
            disabled_attr = self._driver.find_element(
                By.XPATH, f"//input[@name='{field_id}']"
            ).get_attribute("data-ng-disabled")
            # input with name -> readonly
            readonly = bool(
                self._driver.find_element(
                    By.XPATH, f"//input[@name='{field_id}']"
                ).get_attribute("readonly")
            )
            return disabled_attr == "disableEditing" or readonly
        raise CVWebAutomationException(
            f"In the edit VM, the field with id {field_id} does not exist"
        )

    @property
    def field_id_mapping(self):
        return self._field_id_mapping

    @PageService()
    def get_all_field_details(self, field_values: bool = True, field_statuses: bool = True):
        """Get the VM details from the override options page"""
        field_details = dict()
        field_details["field_values"] = {
            key: self._modal_dialog.get_input_details(input_id=value, ignore_exception=True)
            for key, value in self.field_id_mapping.items()
        } if field_values else dict()

        field_details["field_statuses"] = {
            key: self._modal_dialog.get_input_state(input_id=value, ignore_exception=True)
            for key, value in self.field_id_mapping.items()
        } if field_statuses else dict()

        return field_details

class _AWSVMOptions(_EditVMCommon, _AWSOptions):
    """Class for editing"""
    def __init__(self, admin_console):
        super(_EditVMCommon, self).__init__(admin_console)
        super(_AWSOptions, self).__init__(admin_console)

        self._field_id_mapping = {
            "drvm_name": "vmDisplayNameField",
            "availability_zone": "availabilityZone",
            "instance_type": "instanceTypeInput",
            "volume_type": "volumeTypeInput",
            "encryption_key": "encryptionKey",
            "iam_role": "IAMRole",
            "network": "networkInfo",
            "security_groups": "securityGroupsInput",
        }

    @property
    def field_id_mapping(self):
        return self._field_id_mapping

    @PageService()
    def get_all_field_details(self, field_values: bool = True, field_statuses: bool = True):
        """Get the VM details from the override options page"""
        field_details = dict()
        field_details["field_values"] = {
            key: self._modal_dialog.get_input_details(input_id=value, ignore_exception=True, paragraph_element_value=True)
            for key, value in self.field_id_mapping.items()
        } if field_values else dict()

        field_details["field_statuses"] = {
            key: self._modal_dialog.get_input_state(input_id=value, ignore_exception=True)
            for key, value in self.field_id_mapping.items()
        } if field_statuses else dict()

        return field_details


class _AzureVMOptions(_EditVMCommon, _AzureOptions):
    """Class for editing"""
    def __init__(self, admin_console):
        super(_EditVMCommon, self).__init__(admin_console)
        super(_AzureOptions, self).__init__(admin_console)

        self._field_id_mapping = {
            "drvm_name": "vmDisplayNameField",
            "storage_account": "storageAccountDropdownInput",
            "availability_zone": "availabilityZoneDropdownInput",
            "resource_group": "resourceGroupDropdownInput",
            "region": "azureRegionDropdown",
            "vm_size": "vmSizeDropdownInput",
            "virtual_network": "vmNetworksInput",
            "security_group": "securityGroupDropdown",
        }


class _HyperVVMOptions(_EditVMCommon, _HyperVOptions):
    """Class for editing"""
    def __init__(self, admin_console):
        super(_EditVMCommon, self).__init__(admin_console)
        super(_HyperVOptions, self).__init__(admin_console)

        self._field_id_mapping = {
            "drvm_name": "vmDisplayNameField",
            "network": "hyperVNetworkAdapterInput",
        }


class _VMwareVMOptions(_EditVMCommon, _VMwareOptions):
    """Class for editing VMware vm"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super(_EditVMCommon, self).__init__(admin_console)
        super(_VMwareOptions, self).__init__(admin_console)

        self._admin_console.load_properties(self, unique=True)
        self._label = self._admin_console.props[self.__class__.__name__]
        self.__dialog = RModalDialog(admin_console)

        self._field_id_mapping = {
            "drvm_name": "vmDisplayNameField",
            "destination_host": "destinationBrowse",
            "vm_storage_policy": "storagePolicyDropdownInput",
            "datastore": "DataStoreDropdownInput",
            "resource_pool": "resourcePoolDropdownInput"

        }

    @WebAction()
    def __click_link_by_title(self, title, index=0, network=True):
        """
        Click the link by title
        Args:
            title: (str) click the link by title
            index: (int) the index of the button to click
            network: (bool) whether to click in network tab or ip tab
        """
        parent_xp = (
            "//cv-vmware-network-settings"
            if network
            else "//cv-vmware-ipaddress-settings"
        )
        buttons = self._admin_console.driver.find_elements(
            By.XPATH, f"{parent_xp}//a[@title='{title}']"
        )
        buttons[index].click()

    @property
    @WebAction()
    def hostname(self):
        """Gets the hostname value"""
        return self._admin_console.driver.find_element(
            By.ID, "hostname"
        ).get_attribute("value")

    @PageService()
    def set_hostname(self, hostname: str):
        """Sets the hostname for the destination VM"""
        self.__dialog = RModalDialog(self._admin_console,
                                     title=self._admin_console.props['label.overrideReplicationOptions'])
        self.__dialog.fill_text_in_field("hostname", hostname)

    @PageService()
    def add_network(self):
        """Adds a network to the override options"""
        self._table = Rtable(self._admin_console, title=self._label["label.networkSettingsVMWare"])
        network_settings = _NetworkSettings(self._admin_console)
        self.expand_tab(self._label["label.networkSettingsVMWare"])
        self._table.access_toolbar_menu("Add")
        return network_settings

    @PageService()
    def edit_network(self, index=0):
        """
        Edits the network at the particular index
        Args:
            index: (int) index of the network row
        Returns:
        """
        self._table = Rtable(self._admin_console, title=self._label["label.networkSettingsVMWare"])
        network_settings = _NetworkSettings(self._admin_console)
        self.expand_tab(self._label["label.networkSettingsVMWare"])
        self._table.access_action_item_by_row_index(action_item="Edit", row_index=index)
        return network_settings

    @PageService()
    def remove_network(self, index=0):
        """
        Removes the network at the given index
        Args:
            index: (int) index of the network row
        """
        network_settings = _NetworkSettings(self._admin_console)
        self.expand_tab(self._label["label.networkSettingsVMWare"])
        self.__click_link_by_title(
            self._label["label.removeSetting"], index, network=True
        )
        return network_settings

    @PageService()
    def add_ip(self):
        """Adds an IP address to the override options"""
        self.__table = Rtable(self._admin_console, title=self._label["label.ipSettings"])
        ip_settings = _IpSettings(self._admin_console)
        self.expand_tab(self._label["label.addressSettings"])
        self.__table.access_toolbar_menu('Add')
        return ip_settings

    @PageService()
    def edit_ip(self, index=0):
        """
        Edits the ip at the particular index
        Args:
            index: (int) index of the ip row
        Returns:
        """
        self.__table = Rtable(self._admin_console, title=self._label["label.ipSettings"])
        ip_settings = _IpSettings(self._admin_console)
        self.expand_tab(self._label["label.addressSettings"])
        self.__table.access_action_item_by_row_index(action_item="Edit", row_index=0)
        return ip_settings

    @PageService()
    def remove_ip(self, index=0):
        """
        Removes the ip at the given index
        Args:
            index: (int) ip of the network row
        """
        ip_settings = _IpSettings(self._admin_console)
        self.expand_tab(self._label["label.addressSettings"])
        self.__click_link_by_title(
            self._label["label.removeSetting"], index, network=False
        )
        return ip_settings

    @PageService()
    def advance_options(self, enable=True):
        """ To enable toggle """
        label = self._label['label.advanced.options']
        if enable:
            self._modal_dialog.enable_toggle(label=label)
        else:
            self._modal_dialog.disable_toggle(label=label)


class _NetworkSettings:
    """Class for configuring the network settings in the VMWare override options"""

    def __init__(self, admin_console):
        """Initialises the class"""
        self._admin_console = admin_console
        self._drop_down = DropDown(self._admin_console)
        self.__dialog = RModalDialog(self._admin_console, title=self._admin_console.props['label.addNetworkSetting'])

    @PageService()
    def select_source_network(self, source_network: str):
        """Selects the network for the source VM"""
        self.__dialog.select_dropdown_values(drop_down_id="sourceNetwork", values=[source_network], partial_selection=True)

    @PageService()
    def select_destination_network(self, destination_network: str):
        """Selects the network for the destination VM"""
        self.__dialog.select_dropdown_values(drop_down_id="destinationNetwork", values=[destination_network], partial_selection=True)

    @PageService()
    def save(self):
        """Saves the network settings"""
        self.__dialog.click_submit()

    @PageService()
    def cancel(self):
        """Cancels the network setting form"""
        self.__dialog.click_cancel()


class _IpSettings:
    """Class for setting the IP settings for a VMware replication group"""

    def __init__(self, admin_console):
        """Initialises the page object"""
        self._admin_console = admin_console
        self._label = self._admin_console.props
        self.__dialog = RModalDialog(self._admin_console, title=self._label['label.addressSettings'])
        self._drop_down = DropDown(self._admin_console)

    @property
    @WebAction()
    def source_ip(self):
        """Gets the IP address settings for the source VM"""
        dict = {}
        ids = ["sourceIpAddress", "sourceSubnetMask", "sourceDefaultGateway"]
        base_ids = [[f"staticPrivateIP{idx}-sourceIP" for idx in range(4)],
             [f"staticPrivateIP{idx}-sourceSubnet" for idx in range(4)],
             [f"staticPrivateIP{idx}-sourceGateway" for idx in range(4)]]
        for idx in range(len(base_ids)):
            values = [self._admin_console.driver.find_element(By.ID, i).get_attribute('value') for i in base_ids[idx]]
            dict[ids[idx]] = ".".join(values)
        return dict

    @property
    @WebAction()
    def destination_ip(self):
        """Gets the destination IP settings"""
        dict={}
        ids = [
            "destinationIpAddress",
            "destinationSubnetMask",
            "destinationDefaultGateway",
            "destinationPrefDnsServer",
            "destinationAltDnsServer",
        ]
        base_ids =[[f"staticPrivateIP{idx}-destinationIP" for idx in range(4)],
                    [f"staticPrivateIP{idx}-destinationSubnet" for idx in range(4)],
                    [f"staticPrivateIP{idx}-destinationGateway" for idx in range(4)],
                    [f"staticPrivateIP{idx}-primaryDNS" for idx in range(4)],
                   [f"staticPrivateIP{idx}-alternateDNS" for idx in range(4)]]
        for idx in range(len(base_ids)):
            values = [self._admin_console.driver.find_element(By.ID, i).get_attribute('value') for i in base_ids[idx]]
            dict[ids[idx]] = ".".join(values)
        return dict

    @property
    @WebAction()
    def dhcp_enabled(self):
        """Returns true if DHCP is enabled"""
        return "Mui-checked" in self._admin_console.driver.find_element(
            By.XPATH, "//input[@id='useDHCP']/parent::span"
        ).get_attribute("class")

    @PageService()
    def set_source_ip(
        self, ip_address: str, subnet_mask: str = "", default_gateway: str = ""
    ):
        """Sets the IP address settings for the Source VM"""
        for idx, value in enumerate(ip_address.split('.')):
            self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-sourceIP", value)
        if subnet_mask:
            for idx, value in enumerate(subnet_mask.split('.')):
                self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-sourceSubnet", value)
        if default_gateway:
            for idx, value in enumerate(default_gateway.split('.')):
                self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-sourceGateway", value)

    @PageService()
    def toggle_dhcp(self, enable=False):
        """DCHP toggler"""
        if enable:
            self.__dialog.enable_toggle(label=self._label['label.useDHCP'])
        else:
            self.__dialog.disable_toggle(label=self._label['label.useDHCP'])

    @PageService()
    def set_destination_ip(
        self,
        ip_address: str,
        subnet_mask: str = "",
        default_gateway: str = "",
        primary_dns: str = "",
        secondary_dns: str = "",
        primary_wins: str = "",
        secondary_wins: str = "",
    ):
        """Sets the Destination IP settings for the Destination VM"""
        for idx, value in enumerate(ip_address.split('.')):
            self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-destinationIP", value)
        if subnet_mask:
            for idx, value in enumerate(subnet_mask.split('.')):
                self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-destinationSubnet", value)
        if default_gateway:
            for idx, value in enumerate(default_gateway.split('.')):
                self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-destinationGateway", value)
        if primary_dns:
            for idx, value in enumerate(primary_dns.split('.')):
                self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-primaryDNS", value)
        if secondary_dns:
            for idx, value in enumerate(secondary_dns.split('.')):
                self.__dialog.fill_text_in_field(f"staticPrivateIP{idx}-alternateDNS", value)
        if primary_wins:
            self._admin_console.fill_form_by_id(
                "destinationPrefWinsServer", primary_wins
            )
        if secondary_wins:
            self._admin_console.fill_form_by_id(
                "destinationAltWinsServer", secondary_wins
            )

    @PageService()
    def save(self):
        """Saves the IP settings"""
        self.__dialog.click_submit()

    @PageService()
    def cancel(self):
        """Cancels the IP setting form"""
        self.__dialog.click_cancel()


class _ConfigureCommon:
    """Class for configuring virtualization replication group"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console : AdminConsole = admin_console
        self._drop_down = DropDown(self._admin_console)
        self._modal_dialog = RModalDialog(self._admin_console)
        self._wizard = Wizard(self._admin_console)
        self._alert = Alert(self._admin_console)
        self.content = _Content(self._admin_console)
        self.storage_cache = _StorageOrCache(self._admin_console)
        self.recovery_options = _RecoveryOptions(self._admin_console)
        self.override_options = _OverrideOptions(admin_console, self.hypervisor_type)
        self.advanced_options = _AdvancedOptions(self._admin_console)
        self.__vm_type = self.hypervisor_type
        self._admin_console.load_properties(self, unique=True)
        self._label = self._admin_console.props[self.__class__.__name__]

    @property
    @abstractmethod
    def hypervisor_type(self):
        """Provide vm type"""
        raise NotImplementedError

    @PageService()
    @abstractmethod
    def add_default_group(self):
        """Create replication group with default options"""
        raise NotImplementedError

    @PageService()
    def next(self):
        """Click on next"""
        self._wizard.click_next()

    @PageService()
    def previous(self):
        """Click on previous"""
        self._wizard.click_previous()

    @PageService()
    def skip_to_summary(self):
        """Skip to Summary section"""
        self._wizard.click_button(self._admin_console.props["action.skipToSummary"])

    @PageService()
    def finish(self, group_name : str = ""):
        """click on finish"""
        self._wizard.click_submit()
        notification_text = self._alert.get_content(wait_time=120)
        expected_notification_text = f"{self._label['notification.replicationCreated'].replace('{0}', group_name)}"
        if not (expected_notification_text in notification_text):
            raise CVWebAutomationException(
                f"Recovery group creation failed with error: {notification_text}"
            )

    @PageService()
    def create_new_storage(
        self, storage_name, media_agent, storage_path, ddb_path: str = None
    ):
        """Creates a storage with the storage name for trial"""
        self._admin_console.select_hyperlink(self._label["label.createNew"])
        backup_location_details = [{"media_agent": media_agent,
                                    "backup_location": storage_path}]
        if ddb_path:
            deduplication_db_location_details = [{"media_agent": media_agent,
                                                  "deduplication_db_location": ddb_path}]
        else:
            deduplication_db_location_details = None

        DiskStorage(self._admin_console).add_disk_storage(storage_name, backup_location_details,
                                                          deduplication_db_location_details)


class ConfigureVMWareVM(_ConfigureCommon):
    """Class for configuring VMWare virtualization replication group"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super().__init__(admin_console)
        self.advanced_options = _AdvancedOptions_VMWare(admin_console)

    @PageService(hide_args=True)
    def create_new_hypervisor(
        self,
        vendor: str,
        hostname: str,
        name: str,
        username: str,
        password: str,
        proxy_list: list,
    ):
        """
        Creates a new hypervisor with the given settings
            vendor              (str): One of SOURCE_HYPERVISOR_*
            hostname            (str): Hostname of the hypervisor
            name                (str): Display name of the hypervisor in the CS
            username            (str): The username to use to connect
            password            (str): The password to use to connect
            proxy_list          (list): List of access nodes to select for the hypervisor
        """
        self._admin_console.select_hyperlink(self._label["label.createNew"])
        self._drop_down.select_drop_down_values(
            drop_down_id="addServerContent_" "isteven-multi-select_#8657",
            values=[vendor],
            partial_selection=True,
        )
        self._admin_console.wait_for_completion()
        sleep(5)
        self._admin_console.fill_form_by_id("hostname", hostname)
        self._admin_console.fill_form_by_id("serverName", name)

        self._admin_console.select_radio(id="user")
        self._admin_console.fill_form_by_id("uname", username)
        self._admin_console.fill_form_by_id("pass", password)
        self._drop_down.select_drop_down_values(
            drop_down_id="selectProxy_" "isteven-multi-select_#6148", values=proxy_list
        )
        self._modal_dialog.submit()

    @PageService()
    def create_new_target(self, target_name):
        """Creates a new target with the default values selected for trial"""
        self._admin_console.select_hyperlink(self._label["label.createNew"])
        return _VMWareRecoveryTarget(
            self._admin_console, target_name, application_type=None
        )

    @property
    def hypervisor_type(self):
        """VM type"""
        return SOURCE_HYPERVISOR_VMWARE

    @PageService()
    def add_default_group(
        self,
        replication_group_name,
        source_hypervisor,
        virtual_machines,
        recovery_target,
        storage,
        secondary_storage=None,
    ):
        """Create replication group with default options"""

        # set content fields
        self.content.set_name(replication_group_name)
        self.content.select_production_site_hypervisor(source_hypervisor)
        self.next()

        self.content.select_vm_from_browse_tree(virtual_machines,
                view_mode = self._label["groupingOption.vmware.vmsAndTemplates"])
        self.next()
        # set storage/cache fields
        self.storage_cache.select_storage(storage, storage_copy=self.storage_cache.Storage_Copy.Primary.value)
        if secondary_storage:
            self.storage_cache.select_storage(secondary_storage, storage_copy=self.storage_cache.Storage_Copy.Secondary.value)
        self.next()

        # Advanced Options
        self.recovery_options.select_recovery_target(recovery_target)
        self.recovery_options.select_rto(SiteOption.HotSite.value)
        self.next()

        # Prepost scripts
        self.next()

        # Override options
        self.next()

        # Test Failover Options
        self.next()

        # Advanced Options
        self.advanced_options.validate_destination_vm(False)
        self.advanced_options.unconditionally_overwrite_vm(True)
        self.next()

        #  Summary
        self.finish()


class ConfigureAzureVM(_ConfigureCommon):
    """Class for configuring azure virtualization replication group"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        super().__init__(admin_console)

    @property
    def hypervisor_type(self):
        """VM type"""
        return SOURCE_HYPERVISOR_AZURE

    @PageService()
    def add_default_group(
        self,
        name,
        source_hypervisor,
        virtual_machines,
        recovery_target,
        storage,
        secondary_storage=None,
    ):
        """Create replication group with default options"""

        # Target fields
        self.content.set_name(name)
        self.content.select_vm_from_browse_tree(
            source_hypervisor, {self._label["groupingOption.vms"]: virtual_machines}
        )
        self.next()

        # set target fields
        self.recovery_options.select_recovery_target(recovery_target)

        self.recovery_options.unconditionally_overwrite_vm(True)
        self.recovery_options.deploy_vm_during_failover()
        self.next()

        # set storage/cache fields
        self.storage_cache.select_storage(storage)
        if secondary_storage:
            self.storage_cache.select_secondary_storage(secondary_storage)
        self.next()

        #  Override options
        self.next()

        #  Summary
        self.finish()


class ConfigureHypervVM(_ConfigureCommon):
    """Class for configuring HyperV virtualization replication group"""

    @property
    def hypervisor_type(self):
        """VM type"""
        return SOURCE_HYPERVISOR_HYPERV

    @PageService()
    def add_default_group(
        self,
        replication_group_name,
        source_hypervisor,
        virtual_machines,
        recovery_target,
        storage,
        secondary_storage=None,
    ):
        """Create replication group with default options"""
        self.content.set_name(replication_group_name)
        self.content.select_vm_from_browse_tree(
            source_hypervisor, {self._label["groupingOption.vms"]: virtual_machines}
        )
        self.next()

        # set target fields
        self.recovery_options.select_recovery_target(recovery_target)
        self.recovery_options.unconditionally_overwrite_vm(True)
        self.next()

        # set storage/cache fields
        self.storage_cache.select_storage(storage)
        if secondary_storage:
            self.storage_cache.select_secondary_storage(secondary_storage)
        self.next()

        #  Override options
        self.next()

        #  Summary
        self.finish()


class ConfigureAWSVM(_ConfigureCommon):
    """Class for configuring AWS virtualization replication group"""

    def __init__(self, admin_console):
        super().__init__(admin_console)

    @property
    def hypervisor_type(self):
        """VM type"""
        return SOURCE_HYPERVISOR_AWS

    @PageService()
    def add_default_group(
        self,
        name,
        source_hypervisor,
        virtual_machines: list,
        recovery_target,
        storage,
        secondary_storage=None,
    ):
        """Create replication group with default options"""

        # Content tab
        self.content.set_name(name)
        for vm_name in virtual_machines:
            # TODO : change  'Search instances' to 'Search VMs' in UI (Ref:AdminConsoleBase.py ; fxn - search_vm)
            self.content.select_vm_from_browse_tree(
                source_hypervisor, {"By region": [vm_name]}
            )
        self.next()

        # Target tab
        self.recovery_options.select_recovery_target(recovery_target)
        self.recovery_options.validate_destination_vm(True)
        self.recovery_options.unconditionally_overwrite_vm(True)
        self.next()

        # Storage/cache tab
        self.storage_cache.select_storage(storage)
        if secondary_storage:
            self.storage_cache.select_secondary_storage(secondary_storage)
        self.next()

        # Override tab
        self.next()

        # Summary tab
        sleep(5)
        self.finish()
