from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods to get the details about a vm.


Classes:

    VMDetails() --> VMsOwned() ---> _Navigator() ---> login_page --->
        AdminConsoleBase() ---> object()


VMDetails  --  This class contains methods to get details about a virtual machine like last backup,
               vmjobs, restore, etc.

    Functions:

    last_backup()        --  Opens the last backup job details

    vm_jobs()            --  Opens the jobs of the vm

    vm_restore()         --  Opens the restore options page for the vm

    do_not_backup()      --  Removes the VM from the subclient content

    vm_backup_now()      --  Backs up the VM

    vm_summary()         --  Returns the dictionary of all the  vm summary information listed

    vm_backup_details()  --  Returns the backup details of the VM in a dictionary

    recovery_point_restore() -- Restores the VM from the date and time selected from recovery point

    vm_search_content()  --  Searches the VM for files and folders

    backup_validation_results() --  Return the backup validation details of the vm
    
    action_list_snapshots()  --  list the snaps of particular vm at VM level

"""
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.panel import PanelInfo, RPanelInfo, RDropDown
from Web.AdminConsole.Components.panel import RPanelInfo as PanelInfo
from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import PageService,WebAction
from Web.AdminConsole.Components.table import Rtable
from VirtualServer.VSAUtils.VirtualServerConstants import VMBackupType
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.dialog import RModalDialog as ModalDialog
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails


class VMDetails:
    """
    This class contains methods to get details about a virtual machine like last backup,
    vm jobs, restore, etc.
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__tree_view = TreeView(admin_console)
        self.__RpanelInfo = RPanelInfo(self.__admin_console)
        self.__Rdrop_down = RDropDown(self.__admin_console)

    @PageService()
    def last_backup(self):
        """
        Opens the last backup job details
        """
        self.__admin_console.select_configuration_tab()
        self.__admin_console.select_hyperlink("Last backup")

    @PageService()
    def vm_jobs(self):
        """
        Opens the jobs of the vm
        """
        self.__admin_console.access_menu("Jobs")

    @PageService()
    def vm_restore(self, recovery_time=None):
        """
        Opens the restore options page for the vm

        Args:
            recovery_time (str): the backup date in 01-September-1960 format

        """
        self.__admin_console.select_overview_tab()
        if recovery_time:
            calender = {}
            calender['date'], calender['month'], calender['year'] = recovery_time.split("-")
            self.__admin_console.date_picker(calender)
        self.__admin_console.click_button(value=self.__admin_console.props['header.restore'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def do_not_backup(self):
        """
        Removes the VM from the backed up list

        Raises:
            Exception:
                if the VM is on the only content in the subclient

        """
        self.__admin_console.access_menu_from_dropdown("Do not back up")
        self.__admin_console.click_button('Yes')
        if self.__admin_console.check_if_entity_exists(
                "xpath",
                "//div[@class='modal-body text-danger ng-binding ng-scope']"):
            exp = self.__driver.find_element(By.XPATH, "//div[@class='"
                                                      "modal-body text-danger ng-binding "
                                                      "ng-scope']").text
            self.__admin_console.click_button("Close")
            raise Exception(exp)

    @PageService()
    def vm_backup_now(self, bkp_type):
        """
        Backs up the VM

        Args:
            bkp_type    (BackupType):    the backup level, among the type in Backup.BackupType enum

        Returns:
            job_id  (str):   the backup job ID

        """
        self.__admin_console.select_configuration_tab()
        self.__admin_console.access_menu("Back up")
        backup = Backup(self.__admin_console)
        return backup.submit_backup(bkp_type)

    @PageService()
    def vm_summary(self):
        """Returns the dictionary of all the  vm summary information listed

            Ex: {
                'Plan': '',
                'RPO status': '',
                'Last recovery point': '',
                'Oldest recovery point': '',
                'Server': '',
                'VM size': '',
                'Host': '',
                'OS': ''
            }
        """
        panel_details = RPanelInfo(self.__admin_console, self.__admin_console.props['label.summary'])
        return panel_details.get_details()

    @PageService()
    def vm_backup_details(self):
        """Returns the dictionary of all the  vm summary information listed

            Ex: {
                'VM Size (GB)': '',
                'Backup status': '',
                'Backup size (GB)': '',
                'Last backup time': '',
                'Server': '',
                'Guest size': '',
                'Total backup time': ''
            }
        """
        panel_details = PanelInfo(self.__admin_console)
        return panel_details.get_details()

    @PageService()
    def vm_search_content(self, search_value):
        """
        Searches the VM for files and folders and content

        Args:
            search_value    (str):   the folder or file to search for in the VM

        Raises:
            Exception:
                if the search box is not present

        """
        if self.__admin_console.check_if_entity_exists("id", "fileAndFolderSearch"):
            self.__admin_console.fill_form_by_id("fileAndFolderSearch", search_value)
            self.__driver.find_element(By.ID, "fileAndFolderSearch").send_keys(Keys.ENTER)
            self.__admin_console.wait_for_completion()
        elif self.__admin_console.check_if_entity_exists("class", "searchInput"):
            self.__admin_console.fill_form_by_class_name("searchInput", search_value)
            self.__driver.find_element(By.CLASS_NAME, "searchInput").send_keys(Keys.ENTER)
            self.__admin_console.wait_for_completion()
        elif self.__admin_console.check_if_entity_exists("id", "searchAndRestoreInput"):
            self.__admin_console.fill_form_by_id("searchAndRestoreInput", search_value)
            self.__driver.find_element(By.ID, "searchAndRestoreInput").send_keys(Keys.ENTER)
            self.__admin_console.wait_for_completion()
        else:
            exp = "The search option is not present for this Virtual Machine. Please ensure " \
                  "that the server has file indexing enabled and the data analytics job ran for" \
                  "the VM"
            raise Exception(exp)

    @PageService()
    def backup_validation_results(self):
        """Returns the dictionary of The backup validation results

        Ex: {
                'Boot status': '',
                'Last validation job ID': '',
                'Backup validated': '',
                'Backup completion date': ''
            }
        """
        self.__admin_console.select_overview_tab()
        panel_details = PanelInfo(self.__admin_console, self.__admin_console.props['label.backupValidationStats'])
        return panel_details.get_details()

    @PageService()
    def backup_validation_scripts(self):
        """Returns the Column name and script status of the scripts run"""

        table_obj = Rtable(self.__admin_console)
        table_data = table_obj.get_table_data()
        if table_data:
            table_content = list(table_data.values())
            num_rows = len(table_content[0])
            _table = [[] for _ in range(num_rows)]
            for column in table_content:
                for index, data in enumerate(column):
                    _table[index].append(data)
            return _table
        else:
            return []

    @PageService()
    def set_workload_region(self, region):
        """
        method to set workload region for a virtual machine

        Args:
            region(str) = name of the region to assign
        """
        self.__RpanelInfo.edit_tile_entity('Workload region')
        self.__Rdrop_down.select_drop_down_values(drop_down_id="regionDropdown_", values=[region])
        self.__RpanelInfo.click_button("Save")

    @PageService()
    def set_plan(self, plan):
        """
        Method to assign Plan to a virtual machine

        Args:
            plan(str) = plan name
        """
        self.__RpanelInfo.edit_tile_entity('Plan')
        self.__Rdrop_down.select_drop_down_values(drop_down_id="planListDropdown_nogroups", values=[plan])
        self.__RpanelInfo.click_button("Submit")

    @PageService()
    def set_vm_settings(self, vm_setting_options):
        """
        Sets the given input setting values on the Settings Tile

        Args:
            vm_setting_options    (dict):  Dictionary containing the input values for VM settings
                                            Ex : vm_setting_options =  {'vm_backup_type': "APP_CONSISTENT" }

        Raises:
            Exception:
                if failed to set the VM settings

        """
        self.__admin_console.select_configuration_tab()
        settings_panel = RPanelInfo(self.__admin_console, 'Options')
        settings_panel.edit_tile()
        edit_settings_modal = RModalDialog(self.__admin_console, title='Edit settings')

        if vm_setting_options.get('vm_backup_type', None):
            if vm_setting_options['vm_backup_type'] == VMBackupType.APP_CONSISTENT.name:
                self.__admin_console.select_radio(id='appConsistentRadio')
            elif vm_setting_options['vm_backup_type'] == VMBackupType.CRASH_CONSISTENT.name:
                self.__admin_console.select_radio(id='crashConsistentRadio')
            else:
                self.__admin_console.select_radio(id='inheritedRadio')

        edit_settings_modal.click_submit()

    @PageService()
    def set_vm_disk_filters(self, vm_disk_filter_options):
        """
        Sets the given input disk filters on the Disk Filters Tile

        Args:
            vm_disk_filter_options    (dict):  Dictionary containing the input values for VM disk filters
                                            Ex : To INHERIT filters from the VM group :
                                                vm_disk_filter_options = {'filters': None}

                                                To Include VM group disk filters along with VM level filters
                                                vm_disk_filter_options = {
                                                    'filters': [AutoVM1.vmdk,AutoVM1_1.vmdk],
                                                    'include_vm_group_disk_filters': True
                                                }

                                                To Override Disk Filters at the VM level
                                                vm_disk_filter_options = {
                                                    'filters': [AutoVM1.vmdk,AutoVM1_1.vmdk],
                                                    'include_vm_group_disk_filters': False
                                                }
        Raises:
            Exception:
                if failed to set the VM disk filters

        """
        settings_panel = RPanelInfo(self.__admin_console, 'Disk Filters')
        disk_filters_grid = Rtable(self.__admin_console)
        manage_disk_filters_modal = RModalDialog(self.__admin_console, title='Manage disk filters')
        browse_vm_disks_modal = RModalDialog(self.__admin_console, title='Browse virtual machine disks')

        self.__admin_console.select_configuration_tab()
        settings_panel.edit_tile()

        # CLear existing VM disk filters if any
        table_data = disk_filters_grid.get_table_data()
        if table_data:
            table_content = list(table_data.values())
            num_rows = len(table_content[0])
            if num_rows > 0:
                disk_filters_grid.select_all_rows()
                try:
                    disk_filters_grid.access_toolbar_menu('Delete')
                except Exception:
                    pass
        if vm_disk_filter_options.get('filters'):
            manage_disk_filters_modal.click_button_on_dialog('Browse')
            self.__admin_console.wait_for_completion()
            self.__tree_view.select_items(vm_disk_filter_options['filters'], partial_selection=True, skip_items=False)
            browse_vm_disks_modal.click_button_on_dialog('Ok')
            self.__admin_console.wait_for_completion()
        manage_disk_filters_modal.click_submit()

        merge_disk_filters_label = 'Include VM group disk filters'
        if vm_disk_filter_options.get('include_vm_group_disk_filters') is not None:
            if vm_disk_filter_options['include_vm_group_disk_filters']:
                settings_panel.enable_toggle(merge_disk_filters_label)
            else:
                settings_panel.disable_toggle(merge_disk_filters_label)

    @PageService()
    def run_validate_backup(self):
        """
        Runs Backup Validation jobs

        Returns:
            job_id  (str):   the job id of the backup validation
        """
        self.__admin_console.select_overview_tab()
        self.__admin_console.click_button(value="Validate")
        my_dialog = ModalDialog(self.__admin_console)
        my_dialog.click_submit(wait=False)
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    # Written only for OCI
    def edit_vm_details(self, vendor=None, proxy_list=None, tag_name=None, number_of_readers=None):
        """
        This definition edits the server credentials only for OCI

        Args:
            vendor                (str): Vendor type

            proxy_list               (str): proxy list

            tag_name                 (str): tag_name

            number_of_readers        (str):Number of readers

        Raises:
            Exception:
                if the VMGroup details could not be edited

        """
        try:
            self.__admin_console.select_overview_tab()
            if vendor == HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value:
                if proxy_list:
                    self.proxy_obj = VsaSubclientDetails(self.__admin_console)
                    self.proxy_obj.update_access_node(proxy_list)
                if tag_name:
                    self.tab_obj = VsaSubclientDetails(self.__admin_console)
                    self.tab_obj.update_tag_name(tag_name)
                if number_of_readers:
                    self.tab_obj = VsaSubclientDetails(self.__admin_console)
                    self.tab_obj.update_number_of_readers(number_of_readers)
            self.__admin_console.submit_form()
            self.__admin_console.check_error_message()

        except Exception as exp:
            raise Exception(f"Failed to edit VMGroup : {exp}")

    @PageService()
    def action_list_snapshots(self):
        """
        list the snaps of particular vm at VM level
        Args:
            vm_name  (str):  the name of the Particular VM for list of snapshots
        """
        self.__admin_console.access_page_action_menu_by_class("popup")
        self.__admin_console.click_button_using_text("List snapshots")