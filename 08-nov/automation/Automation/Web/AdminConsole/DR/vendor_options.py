from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.browse import RContentBrowse as RB


class _VendorOptionsCommon:
    """Common class for vendor options"""

    def __init__(self, admin_console, recovery_target: bool = False):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console : AdminConsole = admin_console
        self._driver = admin_console.driver

        self._admin_console.load_properties(self)
        self._labels = self._admin_console.props

        self._drop_down = DropDown(admin_console)
        self._modal_dialog = RModalDialog(admin_console)
        self._table = Rtable(admin_console)
        self._browse = RB(admin_console)
        self._wizard = Wizard(self._admin_console)

        self.component : RModalDialog | Wizard = self._wizard if recovery_target else self._modal_dialog
    
    def _select_dropdown_values(self, drop_down_id: str, values: list, partial_selection: bool = False, case_insensitive: bool = False):
        """Selects the values from the dropdown"""
        (self.component.select_dropdown_values(drop_down_id=drop_down_id,
                                               values=values,
                                               partial_selection=partial_selection,
                                               case_insensitive=case_insensitive)
         if self.component == self._modal_dialog
         else self.component.select_drop_down_values(id=drop_down_id,
                                                     values=values,
                                                     partial_selection=partial_selection,
                                                     case_insensitive_selection=case_insensitive))

    def _select_radio_by_id(self, radio_id: str):
        """Selects the radio button by id"""
        (self.component.select_radio_by_id(radio_id=radio_id) 
            if self.component == self._modal_dialog
            else self.component.select_radio_button(id=radio_id))


class _AWSOptions(_VendorOptionsCommon):
    """Class for editing AWS vm"""

    def __init__(self, admin_console, recovery_target: bool = False):
        super().__init__(admin_console, recovery_target)

    @PageService()
    def select_availability_zone(self, availibility_zone: str):
        """Selects the availibility zone"""
        # TODO : Update to click button once unique IDs are assigned
        parent_div_id = "azBrowseContainer"
        self._admin_console.click_by_xpath(f"//div[@id='{parent_div_id}']//*//button")
        self.__modal_dialog = RModalDialog(self._admin_console, title=self._labels["label.selectAvailabilityZone"])
        self._browse.select_path(availibility_zone, partial_selection=True, wait_for_element=True)
        self.__modal_dialog.click_submit()

    @PageService()
    def select_network_subnet(self, network_subnet: str):
        """Selects the network subnet"""
        # TODO : Update to click button once unique IDs are assigned
        parent_div_id = "nicsBrowseContainer"
        self._admin_console.click_by_xpath(f"//div[@id='{parent_div_id}']//*//button")
        self.__modal_dialog = RModalDialog(self._admin_console, title=self._labels["label.selectNetworkSettings"])
        self._browse.select_path(network_subnet, partial_selection=True, wait_for_element=True)
        self.__modal_dialog.click_submit()

    @PageService()
    def select_volume_type(self, volume_type: str):
        """Selects the volume type"""
        self._select_dropdown_values(
            drop_down_id="volumeType",
            values=[volume_type],
            partial_selection=True,
        )

    @PageService()
    def select_encryption_key(self, encryption_key: str):
        """Selects the encryption key"""
        self._select_dropdown_values(
            drop_down_id="encryptionKey",
            values=[encryption_key],
            partial_selection=True,
        )

    @PageService()
    def select_iam_role(self, iam_role: str):
        """Selects the IAM role"""
        self._select_dropdown_values(
            drop_down_id="IAMRole",
            values=[iam_role]
        )

    @PageService()
    def select_security_group(self, security_group: str):
        """Selects the security group"""
        self._select_radio_by_id(radio_id="custom")
        self._select_dropdown_values(
            drop_down_id="securityGroups",
            values=[security_group],
            partial_selection=True,
        )

    @PageService()
    def select_instance_type(self, instance_type: str):
        """Selects the instance type"""
        self._select_dropdown_values(
            drop_down_id="instanceType",
            values=[instance_type],
        )


class _AzureOptions(_VendorOptionsCommon):
    """Class for editing azure vm"""

    def __init__(self, admin_console, recovery_target: bool = False):
        super().__init__(admin_console, recovery_target)

    @PageService()
    def select_resource_group(self, group):
        """
        Select resource group
        Args:
            group(String): specify the resource group name
        """
        drop_down_id = "resourceGroupDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[group], case_insensitive=True)

    @PageService()
    def select_region(self, region):
        """
        Select region
        Args:
            region(string): specify the region
        """
        drop_down_id = "azureRegionDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[region])

    @PageService()
    def select_storage_account(self, account):
        """
        Select storage account
        Args:
            account(string): specify the storage account
        """
        drop_down_id = "storageAccountDropdown"
        self._select_dropdown_values( drop_down_id=drop_down_id, values=[account])

    @PageService()
    def select_vm_size(self, size):
        """
        Select vm size
        Args:
            size(string): specify the vm size
        """
        drop_down_id = "vmSizeDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[size], partial_selection=True)

    @PageService()
    def select_availability_zone(self, availability_zone: str):
        """
        Selects the Availability Zone
        Args:
            availability_zone(string): specify the availability_zone
        """
        drop_down_id = "availabilityZoneDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[availability_zone])

    @PageService()
    def virtual_network(self, network):
        """
        Select virtual network
        Args:
            network(string): specify the virtual network
        """
        drop_down_id = "vmNetworks"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[network], partial_selection=True)

    @PageService()
    def select_security_group(self, group):
        """
        Select vm size
        Args:
            group(string): specify the security group name
        """
        drop_down_id = "securityGroupDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[group])

    @PageService()
    def create_public_ip(self, enable=True):
        """
        select/Deselect create public ip
        Args:
            enable(bool): True/False to select/deselect
        """
        self.component.enable_disable_toggle("Create public IP", enable)

    @PageService()
    def select_disk_type(self, disk_type: str):
        """Selects the disk type"""
        drop_down_id = "diskTypeDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[disk_type])

    @PageService()
    def restore_as_managed_vm(self, enable=True):
        """
        Select/Deselect restore as a managed vm
        Args:
            enable(bool): True/False to select/deselect
        """
        self.component.select_deselect_checkbox(checkbox_id="restoreAsManagedVM", select=enable)


class _HyperVOptions(_VendorOptionsCommon):
    """Class for editing HyperV vm"""

    def __init__(self, admin_console, recovery_target: bool = False):
        super().__init__(admin_console, recovery_target)

    def register_vm_with_failover(self, register=True):
        """ To select the checkbox """
        self.component.select_deselect_checkbox(checkbox_id="registerVMWithFailoverCluster",
                                                select=register)

    @PageService()
    def select_network(self, network):
        """
        Select network
        Args:
            network(str): network name
        """
        drop_down_id = "hyperVNetworkAdapter"
        self._select_dropdown_values(
            values=[network], drop_down_id=drop_down_id, partial_selection=True
        )


class _VMwareOptions(_VendorOptionsCommon):
    """ Class for editing VMware vm """

    def __init__(self, admin_console, recovery_target: bool = False):
        super().__init__(admin_console, recovery_target)

    @PageService()
    def set_destination_host(self, host):
        """
        Set destination host
        Args:
            host(str): set destination host name
        """
        parent_div_id = "destinationHost"
        self._admin_console.click_by_xpath(f"//div[@id='{parent_div_id}']//*//button")
        self.__modal_dialog = RModalDialog(self._admin_console, title=self._labels["label.selectRestoreDestination"])
        self._browse.select_path(host, wait_for_element=True)
        self.__modal_dialog.click_submit()

    @PageService()
    def select_datastore(self, datastore):
        """
        Select datastore
        Args:
            datastore(str): datastore name
        """
        drop_down_id = 'DataStoreDropdown'
        self._select_dropdown_values(values=[datastore], drop_down_id=drop_down_id)

    @PageService()
    def select_resource_pool(self, resource_pool_name):
        """
        Select resource pool
        Args:
            resource_pool_name(str): select resource pool name
        """
        drop_down_id = "resourcePoolDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[resource_pool_name])

    @PageService()
    def set_vm_folder(self, name):
        """Set vm folder
        Args:
            name(str): vm folder name
        """
        parent_div_id = "destinationFolder"
        self._admin_console.click_by_xpath(f"//div[@id='{parent_div_id}']//*//button")
        self.__modal_dialog = RModalDialog(self._admin_console, title=self._labels["label.selectRestoreDestination"])
        self._browse.select_path(name, wait_for_element=True)
        self.__modal_dialog.click_submit()

    @PageService()
    def select_vm_storage_policy(self, name):
        """ Selects storage policy for VM"""
        drop_down_id = "storagePolicyDropdown"
        self._select_dropdown_values(drop_down_id=drop_down_id, values=[name])
