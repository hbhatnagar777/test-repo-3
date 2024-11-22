# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
recovery targets page of the AdminConsole

"""
from selenium.webdriver.common.by import By
from time import sleep
from abc import ABC
from abc import abstractmethod
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Components.panel import (PanelInfo, DropDown, ModalPanel, RPanelInfo, RDropDown)
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import RModalDialog, TagsDialog
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.table import (Table, Rtable)
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.browse import (ContentBrowse, CVAdvancedTree, RContentBrowse)
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName, hypervisor_type
from DROrchestration.DRUtils.DRConstants import Vendors_Complete
from Web.AdminConsole.DR.vendor_options import _AWSOptions, _AzureOptions, _HyperVOptions, _VMwareOptions


class TargetConstants:
    """Recovery target string constants"""
    # vendors
    AMAZON = hypervisor_type.AMAZON_AWS.value
    MICROSOFT_AZURE = "Microsoft Azure"
    MICROSOFT_HYPERV = "Microsoft Hyper-V"
    OPENSTACK = hypervisor_type.OPENSTACK.value
    ORACLE_CLOUD_INFRASTRUCTURE = hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value
    VMWARE_VCENTER = "VMware vCenter"

    # Application Type
    REPLICATION = "Replication"
    REGULAR = "Regular"


class _RecoveryTargetCommon(ABC):
    """All component on recovery targets class should inherit this class"""

    def __init__(self, admin_console, name, vendor, application_type):

        self._admin_console = admin_console
        self.__driver: admin_console.driver = admin_console.driver
        self.__recovery_target_name = name
        self.__vendor = vendor
        self.__application_type = application_type
        self._drop_down = DropDown(self._admin_console)
        self._modal_panel = ModalPanel(self._admin_console)
        self._table = Table(self._admin_console)
        self._browse = ContentBrowse(self._admin_console)
        self._wizard = Wizard(self._admin_console)
        self._rbrowse = RContentBrowse(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)
        self._rtable = Rtable(self._admin_console)
        self.general = _General(self._admin_console)
        self.test_failover = _Test_Failover_Options(self._admin_console)

    @property
    @abstractmethod
    def vendor(self):
        """Vendor name"""
        raise NotImplementedError

    @property
    def application_type(self):
        """Application type"""
        return self.__application_type

    @property
    def recovery_target_name(self):
        """Get recovery target name"""
        return self.__recovery_target_name

    @recovery_target_name.setter
    def recovery_target_name(self, recovery_target_name):
        self.__recovery_target_name = recovery_target_name

    @PageService()
    def set_recovery_target_name(self, name):
        """
        Set recovery target name
        Args:
            name =  Str
        """
        self._wizard.fill_text_in_field(id='name', text=name)

    @PageService()
    def select_vendor(self):
        """
        Select vendor from TargetConstants vendors
        """
        self._wizard.select_radio_button(label=self.vendor)

    @PageService()
    def select_application_type(self):
        """
        Select vendor type TargetConstants vendor type
        """
        self._rtable.access_menu_from_dropdown(self.application_type)

    @PageService()
    def add(self):
        """Click on add"""
        self._rtable.access_toolbar_menu('Add')

    @WebAction()
    def is_field_disabled(self, field_id: str) -> bool:
        """Checks if field is disabled"""
        if self._admin_console.check_if_entity_exists("xpath", f"//select[@name='{field_id}']//option"):
            return (bool([element for element in
                          self.__driver.find_elements(By.XPATH, f"//select[@name='{field_id}']//option")
                          if element.get_attribute("disabled") is not None]) or self.__driver.
                    find_element(By.XPATH, f"//select[@name='{field_id}']").get_attribute("disabled") is not None)
        if self._admin_console.check_if_entity_exists("xpath", f"//div[@id='{field_id}']//input"):
            return bool(self.__driver.find_element(By.XPATH, f"//div[@id='{field_id}']//input")
                        .get_attribute('disabled'))
        if self._admin_console.check_if_entity_exists("xpath", f"//*[@id='{field_id}']//button"):
            return bool(self.__driver.find_element(By.XPATH, f"//*[@id='{field_id}']//button")
                        .get_attribute('ng-disabled'))
        if self._admin_console.check_if_entity_exists("xpath", f"//input[@name='{field_id}']"):
            return bool(self.__driver.find_element(By.XPATH, f"//input[@name='{field_id}']")
                        .get_attribute('disabled'))
        if self._admin_console.check_if_entity_exists("xpath", f"//div[@id='{field_id}']"):
            return bool(self.__driver.find_element(By.XPATH, f"//div[@id='{field_id}']")
                        .get_attribute('aria-disabled'))
        raise CVWebAutomationException(f'In the edit VM, the field with id {field_id} does not exist')

    @PageService()
    def next(self):
        """ To click on next button """
        self._wizard.click_next()

    @PageService()
    def save(self):
        """Save target"""
        self._modal_panel.submit()

    @PageService()
    def cancel(self):
        """Save target"""
        self._modal_panel.cancel()

    @PageService()
    def submit(self):
        """ To click submit"""
        self._wizard.click_submit()


class _Test_Failover_Options:

    def __init__(self, admin_console):
        """ Initializing requirements"""
        self._admin_console = admin_console
        self._table = Rtable(self._admin_console)
        self._wizard = Wizard(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)
        self._rbrowse = RContentBrowse(self._admin_console)

    def set_expiration_time(self, expiration_time, expiration_unit=None):
        """
        set expiration time
        Args:
            expiration_time: expiration time integer
            expiration_unit: expiration unit days/hours
        """
        if expiration_unit:
            self.__select_expiration_unit(expiration_unit)
        self.__select_expiration_value(expiration_time)

    def __select_expiration_unit(self, unit):
        """Select Day(s) in expiration time"""
        self._wizard.select_drop_down_values("expirationTypeValue", values=[unit], case_insensitive_selection=True)

    def __select_expiration_value(self, expiration_time):
        """ Fills the expiration value"""
        self._wizard.fill_text_in_field(id="expirationTimeVal", text=expiration_time, delete_during_clear=False)


class _VMWareRecoveryTarget(_RecoveryTargetCommon, _Test_Failover_Options, _VMwareOptions):
    """Class for Recovery targets Page"""

    def __init__(self, admin_console, recovery_target_name, application_type):
        super().__init__(admin_console, recovery_target_name, self.vendor, application_type)
        super(_VMwareOptions, self).__init__(admin_console, recovery_target=True)

    @property
    def vendor(self):
        """Vendor name"""
        return TargetConstants.VMWARE_VCENTER

    @PageService()
    def select_destination_network(self, destination_network):
        """
        select destination network
        Args:
            destination_network(str): select destination network
        """
        drop_down_id = "VmwareDestNetwork"
        self._wizard.select_drop_down_values(id=drop_down_id, values=[destination_network])

    # -------------------  Test failover options --------------------------------------------------

    @PageService()
    def select_mediaagent(self, mediaagent):
        """
        Select media agent
        Args:
            mediaagent(str): specify the media agent to be selected
        """
        drop_down_id = 'mediaAgent'
        self._wizard.select_drop_down_values(id=drop_down_id, values=[mediaagent])

    @PageService()
    def select_configure_isolated_network(self):
        """Select configure isolated network"""
        self._wizard.select_radio_button(id="configureIsolatedNetwork")

    @PageService()
    def select_configure_existing_network(self, network):
        """Select configure existing network"""
        self._wizard.select_radio_button(id="configureExistingNetwork")
        self.__select_network(network)

    @PageService()
    def __set_gateway_template(self, name):
        """Set gateway template
        Args:
            name(str): Gateway template name
        """
        self._wizard.click_icon_button_by_title("Browse")
        self._rbrowse.select_path(name, wait_for_element=True)
        self._dialog.click_submit()

    @PageService()
    def __select_gateway_network(self, network):
        """
        Select gateway network
        Args:
            network(str):specify the gateway netwrok
        """
        drop_down_id = 'rTargetgatewayNetwork'
        self._wizard.select_drop_down_values(id=drop_down_id, values=[network])

    def __select_network(self, network):
        """
        select a network when 'Configure existing network is selected'
        Args:
            network(str): select network
        """
        drop_down_id = 'rTargetExistingNetwork'
        self._wizard.select_drop_down_values(id=drop_down_id, values=[network])

    def click_migrate_vms(self, toggle: bool = True):
        """ toggle= True   enables the toggle else disables the toggle """
        try:
            if toggle:
                self._wizard.enable_toggle("Migrate VMs")
            else:
                self._wizard.disable_toggle("Migrate VMs")
        except:
            raise CVWebAutomationException("Expiration units can not be in hours for migrate VM")

    def click_configure_gateway(self, path, value):
        """ To enable the toggle  and set path to gateway template and select value for gateway network """
        self._wizard.enable_toggle("Configure gateway")
        self.__set_gateway_template(path)
        self.__select_gateway_network(value)


class _EditVMWareRecoveryTarget(_VMWareRecoveryTarget):
    """Edit vmware recovery target"""

    def __init__(self, admin_console, recovery_target_name=None):
        super().__init__(admin_console, recovery_target_name, self.application_type)

    @property
    def vendor(self):
        """Vendor name"""
        # In recovery target edit panel, vendor is not editable field, so setting it as None so
        # that in base class(_VMWareRecoveryTarget) vendor selection should not be called
        return None

    @property
    def application_type(self):
        """Application type"""
        # In recovery target edit panel, vendor is not editable field, so setting it as None so
        # that in baseclass(_VMWareRecoveryTarget) application_type selection should not be called
        return None


class _AzureRecoveryTarget(_RecoveryTargetCommon, _Test_Failover_Options, _AzureOptions):
    """Class for creating a Azure Recovery Target in DR"""

    def __init__(self, admin_console: AdminConsole, recovery_target_name: str | None, application_type: str | None):
        """Initialises the recovery target class for Azure VMs
        application_type: Either 'Regular' or 'Replication'
        """
        super(_AzureRecoveryTarget, self).__init__(admin_console, recovery_target_name, self.vendor, application_type)
        super(_AzureOptions, self).__init__(admin_console, recovery_target=True)
        self._advanced_tree = CVAdvancedTree(admin_console)

        self._admin_console.load_properties(self, unique=True)
        self.__label = self._admin_console.props

    @property
    def vendor(self) -> str:
        """The vendor name of the recovery target"""
        return TargetConstants.MICROSOFT_AZURE

    @WebAction()
    def expand_options(self) -> bool:
        """Expands the additional options tab"""
        xpath = "//a[@role='button']//span//i[contains(@class, 'chevron-right')]"
        if self._admin_console.check_if_entity_exists("xpath", xpath):
            self._admin_console.driver.find_element(By.XPATH, xpath).click()
            return True
        return False

    @PageService()
    def restore_as_managed_vm(self, enable: bool):
        """Checks the box for restore as a managed VM, only applicable for 'Replication' application type"""
        if enable:
            self._admin_console.checkbox_select("restoreAsManagedVM")
        else:
            self._admin_console.checkbox_deselect("restoreAsManagedVM")

    @PageService()
    def select_templates(self, template_path):
        """Selects the template path from the template browser, only applicable for 'Regular' application type
        template_path   (list): List of strings delimited by '\' or '/' to be selected
        """
        self._advanced_tree.select_elements_by_full_path(template_path)


class _EditAzureRecoveryTarget(_AzureRecoveryTarget):
    """Class for editing a Azure Recovery Target"""

    def __init__(self, admin_console: AdminConsole, recovery_target_name: str = None):
        """Initialises the class for editing recovery target"""
        super(_EditAzureRecoveryTarget, self).__init__(admin_console, recovery_target_name, application_type=None)

    @property
    def vendor(self) -> None:
        """The vendor name is returned as None, as it is uneditable"""
        return

    def select_resource_group(self, resource_group: str):
        """Not editable"""
        raise NotImplementedError("Azure resource group is not editable")

    def select_region(self, region_name: str):
        """Not editable"""
        raise NotImplementedError("Region name is not editable")

    def select_storage_account(self, storage_name: str):
        """Not editable"""
        raise NotImplementedError("Storage account is not editable")


class _HyperVRecoveryTarget(_RecoveryTargetCommon, _Test_Failover_Options, _HyperVOptions):
    """Class for Recovery targets Page"""

    def __init__(self, admin_console, recovery_target_name, application_type):
        super().__init__(admin_console, recovery_target_name, self.vendor, application_type)
        super(_HyperVOptions, self).__init__(admin_console, recovery_target=True)
        self._admin_console.load_properties(self)

    @property
    def vendor(self):
        """Vendor name"""
        return TargetConstants.MICROSOFT_HYPERV

    @PageService()
    def set_destination_folder(self, path):
        """
        Set destination path
        Args:
            path(str): set destination path name
        """
        drop_down_id = "hyperVRestoreLocation"
        self._wizard.select_drop_down_values(id=drop_down_id, values=[self._admin_console.props['error.vmFolder']])
        self._wizard.click_icon_button_by_title('browse')
        self._rbrowse.select_path(path, wait_for_element=True, partial_selection=True)
        self._dialog.click_submit()


class _EditHyperVRecoveryTarget(_HyperVRecoveryTarget):
    """Edit Microsoft Hyper V recovery target"""

    def __init__(self, admin_console, recovery_target_name=None):
        super().__init__(admin_console, recovery_target_name, self.application_type)

    @property
    def vendor(self):
        """Vendor name"""
        # In recovery target edit panel, vendor is not editable field
        return None

    @property
    def application_type(self):
        """Application type"""
        # In recovery target edit panel, application Type is not editable field
        return None

    @PageService()
    def select_destination_hypervisor(self, name):
        """In recovery target edit panel, Not editable destination Hyper"""
        return None


class _AWSRecoveryTarget(_RecoveryTargetCommon, _Test_Failover_Options, _AWSOptions):
    """Class for creating a AWS Recovery Target in DR"""

    def __init__(self, admin_console: AdminConsole, recovery_target_name: str | None, application_type: str | None):
        """Initialises the recovery target class for AWS VMs
        application_type: Only 'Replication' suppported as of now
        """
        super(_AWSRecoveryTarget, self).__init__(admin_console, recovery_target_name, self.vendor, application_type)
        super(_AWSOptions, self).__init__(admin_console, recovery_target=True)
        self._admin_console.load_properties(self)

    @property
    def vendor(self) -> str:
        """The vendor name of the recovery target"""
        return TargetConstants.AMAZON


class _EditAWSRecoveryTarget(_AWSRecoveryTarget):
    """Class for editing an AWS Recovery Target"""

    def __init__(self, admin_console: AdminConsole, recovery_target_name: str = None):
        """Initialises the class for editing recovery target"""
        super(_EditAWSRecoveryTarget, self).__init__(admin_console, recovery_target_name, application_type=None)

    @property
    def vendor(self) -> None:
        """The vendor name is returned as None, as it is uneditable"""
        return

    def select_destination_hypervisor(self, name : str):
        """Not editable"""
        raise NotImplementedError("AWS destination hypervisor is not editable")


class TargetDetails:
    """Target details page operations"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__type_class_mapping = {
            Vendors_Complete.AZURE.value: _EditAzureRecoveryTarget,
            Vendors_Complete.AWS.value: _EditAWSRecoveryTarget,
            Vendors_Complete.HYPERV.value: _EditHyperVRecoveryTarget,
            Vendors_Complete.VMWARE.value: _EditVMWareRecoveryTarget,
        }

    @PageService()
    def get_target_summary(self):
        """Read recovery target summary panel"""
        summary_panel = RPanelInfo(self.__admin_console, 'Summary')
        return summary_panel.get_details()

    @PageService()
    def edit_target(self, name=None, hypervisor_type=Vendors_Complete.VMWARE.value):
        """
        Edit target
        Args:
            name(str): specify name to be updated
            hypervisor_type(str): The type of hypervisor to edit
        Returns:_EditVMWareRecoveryTarget object
        """
        summary_panel = RPanelInfo(self.__admin_console, 'Summary')
        summary_panel.edit_tile()
        self.__admin_console.wait_for_completion()

        self.target = self.__type_class_mapping.get(hypervisor_type)(self.__admin_console, recovery_target_name=name)
        return self.target


class RecoveryPointStore:
    """Class for recovery point store configuration for continuous mode replication pairs"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__modal_panel = ModalPanel(admin_console)
        self.__drop_down = DropDown(admin_console)
        self.__browse = ContentBrowse(admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @WebAction()
    def __click_new_rpstore_button(self):
        """
        Click the hyperlink by finding using the title
        """
        title = self.__label['label.createRPStore']
        self.__driver.find_element(By.XPATH, f"//*[@title='{title}']").click()

    @WebAction()
    def __fill_form_password(self, value):
        """
        Enters the password for the network path
        Args:
            value (str): The password value for the network path access
        """
        element = self.__driver.find_element(By.XPATH, '//input[@type="password"]')
        element.clear()
        element.send_keys(value)

    @WebAction()
    def __click_interval_link(self):
        """Clicks the peak interval hyperlink to open the interval selection window"""
        self.__driver.find_element(By.XPATH, "//*[@class='backup-window-list']//li").click()

    @WebAction()
    def __get_all_intervals(self, day):
        """Returns all the interval elements for a day"""
        return self.__driver.find_elements(By.XPATH, "//a[contains(text(),'{}')]/../../"
                                                    "td[contains(@class, 'week-time')]".format(day))

    @WebAction()
    def __create_store_button_click(self):
        """Recovery Store Creation Page Create Button click"""
        self.__driver.find_element(By.XPATH, "//*[@id='addRPStore_button_#9443']").click()

    @WebAction()
    def __time_picker(self, picker, time):
        """
        Picks a time for an interval for the selected time picker
        picker        : Picker element produced by driver
        time        (str): Time interval for the picker
        """
        time, unit = time.split()
        picker.click()
        time_element = picker.find_element(By.XPATH, ".//div/div[@class='popover-inner']/div//div[2]/input")
        time_element.clear()
        time_element.send_keys(time)
        self.__drop_down.select_drop_down_values(
            values=[unit],
            drop_down_id="cvTimeRelativePicker_isteven-multi-select_#6209")
        picker.click()

    @PageService()
    def select_continuous_storage(self, storage_name):
        """
        Select the storage
        Args:
            storage_name(str):specify the storage name which will be used while
                              configuring continuous replication pair
        """
        self.__drop_down.select_drop_down_values(values=[storage_name], drop_down_id='storage')

    @PageService()
    def __peak_interval_selection(self, peak_interval):
        """
        Selects the intervals which are marked as peak for the recovery point store
        Args:
            peak_interval (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
                eg: {'Monday': [0,1,2,3], 'Tuesday': [0,1,2,3], 'Wednesday': [0,1,2,3]}
        """
        self.__click_interval_link()
        self.__admin_console.wait_for_completion()

        self.__admin_console.select_hyperlink("Clear")
        keys = peak_interval.keys()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            if day in keys:
                intervals = self.__get_all_intervals(day)
                for slot in peak_interval[day]:
                    if "selected" not in intervals[slot].get_attribute('class'):
                        intervals[slot].click()
        self.__modal_panel.submit()

    @PageService()
    def _pick_time(self, picker_id, time=None):
        """
        This page service is used to select a time picker on the basis of label or id and then pick the time
        Args:
            picker_id (str): ID of the picker
            time      (str): If time is given, the checkbox is selected(only for optional time pickers)
        """
        picker_xpath = "//*[@{}='{}']/../../div[2]/div"
        if self.__admin_console.check_if_entity_exists("xpath", picker_xpath.format("id", picker_id)):
            if not time:
                self.__admin_console.checkbox_deselect(picker_id)
                return
            self.__admin_console.checkbox_select(picker_id)
            picker = self.__driver.find_element(By.XPATH, picker_xpath.format("id", picker_id))
        elif self.__admin_console.check_if_entity_exists("xpath", picker_xpath.format("for", picker_id)):
            picker = self.__driver.find_element(By.XPATH, picker_xpath.format("for", picker_id))
        else:
            raise CVWebAutomationException("No time picker available with this ID")
        self.__time_picker(picker, time)

    @PageService()
    def select_recovery_type(self, recovery_type):
        """Selects the recovery type from the dropdown
        Args:
            recovery_type (int): 0 for latest recovery, 1 for point in time recovery
        """
        recovery_types = [self.__label['label.recoveryLive'], self.__label['label.recoveryGranular']]
        self.__drop_down.select_drop_down_values(
            values=[recovery_types[recovery_type]],
            drop_down_id="selectRecoveryOptions_isteven-multi-select_#1569")

    @PageService()
    def select_store(self, name):
        """
        Checks the recovery point store list to select the recovery point store
        Args:
            name (str): Name of the store
        """
        self.__drop_down.select_drop_down_values(
            values=[name],
            drop_down_id='selectRecoveryOptions_isteven-multi-select_#1717')

    @PageService()
    def create_recovery_store(self, name, media_agent, max_size, path, path_type='',
                              path_username=None, path_password=None, peak_interval=None):
        """
        Args:
            name            (str): name of the recovery point store
            media_agent     (str): name of the media agent on which the store will reside on
            max_size        (int): the maximum size of the recovery point store in GB
            path            (str): the path at which the store will be present
            path_type       (str): the path type as 'Local path' or 'Network path'
            path_username   (str): the path access username, only for network path
            path_password   (str): the path access password, only for network path
            peak_interval  (dict): the intervals at which recovery point store is marked at peak
                Must be a dict of keys as days, and values as list of date time ids(0-23)
        """
        self.__click_new_rpstore_button()
        self.__admin_console.wait_for_completion()

        self.__admin_console.fill_form_by_name("libraryName", name)
        self.__admin_console.select_value_from_dropdown('mediaAgent', media_agent)
        self.__admin_console.fill_form_by_name("maxThreshold", max_size)
        self.__admin_console.check_radio_button(path_type)

        if not path_type:
            path_type = self.__label['Local_Path']

        if path_type == self.__label['Local_Path']:
            self.__admin_console.click_button(self.__label['Browse'])
            self.__browse.select_path(path)
            self.__browse.save_path()
        elif path_type == self.__label['Network_Path']:
            self.__admin_console.fill_form_by_name("loginName", path_username)
            self.__fill_form_password(path_password)
            self.__admin_console.wait_for_completion()

        if peak_interval:
            self.__peak_interval_selection(peak_interval)
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()

        self.__create_store_button_click()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def configure_intervals(self, ccrp=None, acrp=None):
        """
        Configures the recovery point store interval options
        Args:
            ccrp      (str): Crash consistent recovery points interval '<time> <unit>'
                             unit -> ('seconds', 'minutes', 'days', 'hours')
            acrp      (str): Application Consistent recovery points interval '<time> <unit>'
                             unit -> ('seconds', 'minutes', 'days', 'hours')
        """
        if not (ccrp or acrp):
            raise CVWebAutomationException("Either CCRP or ACRP must be set")

        self._pick_time("useCcrp", ccrp)
        self._pick_time("useAcrp", acrp)

    @PageService()
    def configure_retention(self, retention, merge=False, merge_delay=None,
                            max_rp_interval=None, max_rp_offline=None, off_peak_only=False):
        """
        Args:
            retention            (str): Duration for which a recovery point is retained for
            merge               (bool): Whether to merge recovery points
            merge_delay          (str): Merge recovery points older than this interval
            max_rp_interval      (str): Recovery point max retention interval
            max_rp_offline       (str): After what time to switch to latest recovery if RPstore is offline
            off_peak_only       (bool): Whether to prune and merge only on non-peak time
        """
        self._pick_time("useRpRetention", retention)
        if merge:
            self.__admin_console.checkbox_select("useRpMerge")

            self._pick_time("useRpMergeDelay", merge_delay)
            self._pick_time("useMaxRpInterval", max_rp_interval)
        self._pick_time("useMaxRpStoreOfflineTime", max_rp_offline)
        if off_peak_only:
            self.__admin_console.checkbox_select("useOffPeakSchedule")
        else:
            self.__admin_console.checkbox_deselect("useOffPeakSchedule")


class RecoveryTargets:
    """Operations on recovery target react page"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver: admin_console.driver = admin_console.driver
        self.__table = Rtable(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__admin_console.load_properties(self)

        self.__type_class_mapping = {
            Vendors_Complete.AZURE.value: _AzureRecoveryTarget,
            Vendors_Complete.AWS.value: _AWSRecoveryTarget,
            Vendors_Complete.HYPERV.value: _HyperVRecoveryTarget,
            Vendors_Complete.VMWARE.value: _VMWareRecoveryTarget,

        }

    @PageService()
    def __configure_recovery_target(self, application_type, vendor, name):
        """ Configure recovery target common steps """
        self.__table.access_toolbar_menu("Add")
        self.__table.access_menu_from_dropdown(application_type)

        self.__wizard.select_radio_button(vendor)
        self.__wizard.click_next()
        self.__wizard.fill_text_in_field(id='name', text=name)

    @PageService()
    def configure_recovery_target(self, application_type, vendor, name):
        """
        Configures recovery target.

        Args:
            application_type (str): Regular/Replication.
            vendor (str): To select the vendor.
            name(str): To set the target name

        Returns:
            object: Recovery Target object.
        """
        self.__configure_recovery_target(application_type, vendor, name)
        recovery_target_object = self.__type_class_mapping.get(vendor)(
            self.__admin_console, recovery_target_name=name, application_type=application_type
        )
        return recovery_target_object

    @PageService()
    def access_target(self, target_name):
        """
        Access specified recovery target
        Args:
            target_name(Str): recovery target name
        Returns: TargetDetails object
        """
        if self.has_target(target_name):
            # TO DO when details page goes to react target = RtargetDetails(self.__admin_console)
            target = TargetDetails(self.__admin_console)
            self.__admin_console.select_hyperlink(target_name)
            self.__admin_console.wait_for_completion()
            return target
        raise CVWebAutomationException("Target [%s] does not exists" % target_name)

    @PageService()
    def has_target(self, target_name):
        """
        Check Recovery target exists
        Args:
            target_name(str): Specify recovery target name
        Returns(bool):True if target exists else returns false
        """
        return self.__table.is_entity_present_in_column('Name', target_name)

    @PageService()
    def delete_recovery_target(self, target_name):
        """Delete recovery target"""
        if self.has_target(target_name):
            self.__table.access_action_item(target_name, 'Delete')
            self.__admin_console.click_button('Yes')
            self.__admin_console.refresh_page()

    @PageService()
    def get_target_details(self, target_name):
        """
        Read specified recovery target all the column fields
        Args:
            target_name(str): Recovery target name
        Returns(dict): table content of specified recovery target
        """
        self.__admin_console.refresh_page()
        self.__table.apply_filter_over_column('Name', target_name)
        data = self.__table.get_table_data()
        if data['Name']:
            return data
        raise CVWebAutomationException("Recovery Target [%s] does not exists in Recovery "
                                       "Targets Page" % target_name)

    def validate_details(self, vendor, observed_values:dict, expected_values:dict):
        """
        Validates the details of a vendor's observed values against expected values.

        Args:
            vendor (str): The name of the vendor.
            observed_values (dict): A dictionary containing the observed values.
            expected_values (dict): A dictionary containing the expected values.
        """

        match vendor:
            case Vendors_Complete.AWS.value:
                assert_comparison_keys = {"application_type", "destination_hypervisor", "access_node",
                                          "drvm_name", "availability_zone", "encryption_key", "iam_role",
                                          "network", "security_group", "instance_type",
                                          "test_failover_expiration_time", "test_failover_network",
                                          "test_failover_security_group", "test_failover_instance_type"}
                assert_includes_keys = {"volume_type"}
            case Vendors_Complete.AZURE.value:
                assert_comparison_keys = {"drvm_name", "resource_group",  "region", "storage_account", "availability_zone",
                                           "virtual_network"}
                assert_includes_keys = {"vm_size", "security_group"}
            case Vendors_Complete.HYPERV.value:
                assert_comparison_keys = {"drvm_name", "network"}
                assert_includes_keys = set()
            case Vendors_Complete.VMWARE.value:
                assert_comparison_keys = {"drvm_name", "vm_storage_policy", "datastore", "resource_pool"}
                assert_includes_keys = {"destination_host"}
            case default:
                assert_comparison_keys = set()
                assert_includes_keys = set()
        for key in assert_comparison_keys:
            TestCaseUtils.assert_comparison(observed_values.get(key), expected_values.get(key))
        for key in assert_includes_keys:
            TestCaseUtils.assert_includes(observed_values.get(key), expected_values.get(key))


class _General:

    def __init__(self, admin_console):
        """ Initializes the variables"""
        self._admin_console = admin_console
        self._wizard = Wizard(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)

    def select_destination_hypervisor(self, name):
        """ To select destination Hypervisor"""
        drop_down_id = 'hypervisorsDropdown'
        self._wizard.select_drop_down_values(id=drop_down_id, values=[name])

    def _set_display_name(self, name):
        """Set display name"""
        self._wizard.fill_text_in_field(id="prefixSuffixDisplayName", text=name)

    def set_vm_display_name(self, name, value):
        """
        Set display name
        Args:
            name(str): Display name
            value(constant): Suffix/prefix/original
        """
        if value == self._admin_console.props['label.suffix']:
            self._wizard.select_radio_button(id='displayNameSuffix')
        elif value == self._admin_console.props['label.prefix']:
            self._wizard.select_radio_button(id='displayNamePrefix')
        else:
            self._wizard.select_radio_button(id='displayNameOriginal')
        self._set_display_name(name)

    def select_access_node(self, node):
        """ Access node selection"""
        drop_down_id = 'accessNodeDropdown'
        self._wizard.select_drop_down_values(id=drop_down_id, values=[node])

    def select_security(self, value):
        """ Selects security element """
        drop_down_id = 'targetUserAndGroups'
        self._wizard.select_drop_down_values(id=drop_down_id, values=[value])




