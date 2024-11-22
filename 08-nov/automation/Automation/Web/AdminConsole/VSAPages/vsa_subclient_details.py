from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for all the actions that can be done of the Subclient Details page.


Classes:

    VsaSubclientDetails() ---> SubclientDetails() --->  AdminConsoleBase() ---> object()


VsaSubclientDetails  --  This class contains all the methods for action in a particular
                        subclient's page

Functions:

    subclient_storage_pool_info()   --  Gets the list of all storage pools

    schedule_info()     --  Gets the list of all schedules associated with the subclient

    manage_content()    --  Manages the collection content by adding or removing VMs and rules

    subclient_settings()-- Edits the no of readers assigned to the collection and the backup type
                            of the virtual machine

    subclient_summary() --  Gets the last backup time, last backup size, next backup time, etc

    get_plan() -- get the plan name associated to vmgroup

    snap_mount_esx_host() -- Sets the given ESX host as the snap mount ESX

    set_backup_validation() --  Enables and sets the credentials to run backup validation

    schedule_backup_validation()  --   Schedules Backup validation

    run_validate_backup()   --  Runs backup validation job

    update_access_node()  --  Updates given Access node at VM Group level

    azure_snapshot_settings()  --  Gets & Edits Snapshots settings for Azure  Hypervisors' VM Groups
    
    action_list_snapshots()  -- list the snaps of particular vmgroup at VMgroup or subclient level

"""

import re
import time
from collections import OrderedDict
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import ModalPanel, RPanelInfo as PanelInfo, RDropDown as DropDown
from Web.AdminConsole.Components.dialog import RBackup, RModalDialog as ModalDialog
from Web.AdminConsole.Components.core import TreeView, Toggle
from Web.Common.page_object import (
    PageService, WebAction
)


class VsaSubclientDetails:
    """
    This class contains all the methods for action in a particular subclient's page
    """

    def __init__(self, admin_console):
        """ """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self, unique=True)
        self.__driver = admin_console.driver
        self.__panel_info_obj = PanelInfo(admin_console)
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__page_container_obj = None

    @PageService()
    def subclient_storage_pool_info(self):
        """
        Displays the storage pool info of the subclient

        Returns:
            pool_info   (list):  lists the storage pool info

        """
        self.__admin_console.select_configuration_tab()
        elements = self.__driver.find_elements(By.XPATH, "//cv-tile-component[@data-title='"
                                                        "Storage pool']/div/div[3]/div/div[2]/ul/li")
        pool_info = {}
        for element in elements:
            pool_info[element.find_element(By.XPATH,
                "./span[1]").text] = element.find_element(By.XPATH, "./span[2]").text
        self.__admin_console.log.info("The storage pool associated with plan of the subclient is %s",
                                      str(pool_info))
        return pool_info

    @PageService()
    def schedule_info(self):
        """
        Displays all the schedules associated with the subclient

        Returns:
            schedules  (list):  list of all schedules associated to the subclient

        """
        self.__admin_console.select_configuration_tab()
        elements = self.__driver.find_elements(By.XPATH, "//cv-tile-component[@data-title="
                                                        "'Schedules']/div/div[3]/div/div[2]/ul")
        schedules = []
        for element in elements:
            schedules.append(element.find_element(By.XPATH, "./li").text)
        self.__admin_console.log.info("The schedules associated with the subclient are %s", str(schedules))
        return schedules

    @PageService()
    def restore(self, recovery_time=None):
        """
        Opens the select restore page

        Args:
            recovery_time   (str):   the backup date in 01-September-1960 format

        Raises:
            Exception:
                if there is no option to restore

        """
        self.__admin_console.select_overview_tab()
        if recovery_time:
            calender = {}
            calender['date'], calender['month'], calender['year'] = recovery_time.split("-")
            self.__admin_console.date_picker(calender)
        self.__admin_console.click_button(value=self.__admin_console.props['header.restore'])

    @PageService()
    def backup_now(self, bkp_type):
        """
        Starts a backup job for the collection

        Args:

            bkp_type (BackupType): the backup level, among the type in Backup.BackupType enum

        Returns:
            Job ID of backup job

        """
        self.__admin_console.select_overview_tab()
        self.__driver.execute_script("window.scrollTo(0,0)")
        self.__driver.find_element(By.XPATH, "//button[@id='BACKUP']").click()
        backup = RBackup(self.__admin_console, title='Backup options')
        return backup.submit_backup(bkp_type)

    @PageService()
    def manage_content(self):
        """
        Manages the collection content by adding or removing VMs and rules

        Raises:
            Exception:
                if there is no link to Manage the subclient content

        """
        self.__admin_console.select_content_tab()
        self.__driver.find_element(By.XPATH, "//div[@id='vmgroups-overview-content']//button[@title='Edit']").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def subclient_settings(self, reader=2, collect_file_details=False, bkp_type=None, cbt=True,
                           auto_detect_owner=False, transport_mode=None,
                           free_space=None, ds_free_space_check=True, snapshot_rg=None):
        """
        Edits the no of readers assigned to the collection and the backup type
        of the virtual machine

        Args:
            reader                   (int):         the number of readers

            collect_file_details     (bool):        to enable or disable metadata collection

            bkp_type                 (str):  app / crash consistent backup

            cbt                      (bool):        enable / disable CBT

            auto_detect_owner        (bool):        to auto detect the owner of the VM

            transport_mode           (str):  the transport mode to be used for backup

            free_space               (int):         the amount of free space to be set

            ds_free_space_check      (bool):        to enable / disable datastore freespace check

            custom_rg                (string):      to set Custom RG for snapshot

        Raises:
            Exception:
                when the subclient setting could not be edited or
                when there is an error while updating the settings

        """
        self.__admin_console.select_configuration_tab()
        panel_elements = self.__panel_info_obj.get_list()

        if cbt:
            self.__panel_info_obj.enable_toggle("Use changed block tracking")
        else:
            self.__panel_info_obj.disable_toggle("Use changed block tracking")

        if auto_detect_owner:
            self.__panel_info_obj.enable_toggle("Auto detect VM Owner")
        else:
            self.__panel_info_obj.disable_toggle("Auto detect VM Owner")

        if "Collect file details" in panel_elements:
            if collect_file_details:
                self.__panel_info_obj.enable_toggle("Collect file details")
            else:
                self.__panel_info_obj.disable_toggle("Collect file details")

        if snapshot_rg:
            self.__driver.find_element(By.XPATH, "//a[@data-ng-click='editRg()']").click()
            self.__admin_console.wait_for_completion()
            self.__panel_dropdown_obj.select_drop_down_values(values=[snapshot_rg],
                                                              drop_down_id="configureRgForServer_isteven-multi-select_#6301")
            self.__panel_info_obj.save_dropdown_selection("Custom resource group for disk snapshots")
            self.__admin_console.wait_for_completion()

        if self.__panel_info_obj.check_if_hyperlink_exists_on_tile("Edit"):
            self.__admin_console.tile_select_hyperlink("Settings", "Edit")
            self.__admin_console.fill_form_by_id("noOfReaders", reader)

            if bkp_type:
                self.__driver.find_element(By.XPATH,
                    "//div[@class='frequency']//span[contains("
                    "text(),'" + bkp_type + "')]").click()

            if transport_mode:
                self.__admin_console.select_value_from_dropdown("transportMode", transport_mode)

            if self.__admin_console.check_if_entity_exists("xpath", "//input[@id='datastoreFreespaceCheckCB']"):
                if not ds_free_space_check:
                    self.__admin_console.checkbox_deselect("datastoreFreespaceCheckCB")
                else:
                    self.__admin_console.checkbox_select("datastoreFreespaceCheckCB")
                    if free_space:
                        self.__admin_console.fill_form_by_id("datastoreFreespaceRequired", free_space)

            self.__admin_console.submit_form()
            self.__admin_console.check_error_message()
        else:
            raise Exception("There is no option to edit the subclient properties")

    @PageService()
    def subclient_summary(self):
        """
        Provides the summary info of the subclient like last backup time, next backup time

        Returns:
            summary_info    (dict): info about the subclient

        """
        panel_info = PanelInfo(self.__admin_console, title=self.__admin_console.props['label.summary'])
        return panel_info.get_details()

    @PageService()
    def get_plan(self):
        """
        Gets the  plan associated with the vmgroup

        Returns:
            plan name  (basestring):   the plan name associated with the vmgroup

        """
        self.__admin_console.select_overview_tab()
        plan = list(self.__driver.find_elements(By.XPATH, "//*[@id='vmgroups-overview-summary']//a"))
        if plan.__len__() >= 2:
            self.__admin_console.log.info("The Plan associated with the subclient is %s",
                                          str(plan[1].text))
            return plan[1].text
        else:
            policy = self.get_storage_policy()
            return policy

    @PageService()
    def snap_mount_esx_host(self, esx_host):
        """
        Sets the given ESX host as the snap mount ESX

        Args:
            esx_host (str):      the esx host to set as snap mount esx

        """
        self.__admin_console.select_configuration_tab()
        self.__admin_console.tile_select_hyperlink("Snap mount esx", "Edit")
        self.__admin_console.select_destination_host(esx_host)
        self.__admin_console.submit_form()

    @PageService()
    def get_storage_policy(self):
        """
        Gets the storage policy or plan associated with the subclient

        Returns:
            storage_policy  (str):   the storage policy associated with the subclient

        # """
        self.__admin_console.select_overview_tab()
        policy = self.__driver.find_elements(By.XPATH, "//*[@id='storagePolicyRowVMGroup']/div[2]/div")
        self.__admin_console.log.info("The storage policy associated with the vmgroup is %s",
                                      str(policy[0].text))
        return policy[0].text

    @PageService()
    def run_file_indexing(self):
        """
        Runs the file indexing job for the subclient

        Returns:
            job_id  (str):   the job id of the content indexing job

        """
        xpath = '//*[@id="cv-tab"]//a'
        self.__admin_console.driver.find_element(By.XPATH, xpath).click()
        self.__admin_console.driver.find_element(By.XPATH, "//span[contains(text(), 'Run file indexing')]").click()
        self.__admin_console.click_button("Yes")
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def set_backup_validation(self, backup_validation_options):
        """
        Sets backup Validation details

        Args:
            backup_validation_options    (dict):     Credential details of the user

        Returns:

        """
        self.__admin_console.select_configuration_tab()
        panel_details = PanelInfo(self.__admin_console, self.__admin_console.props['label.backupValidation'])
        if not panel_details.is_toggle_enabled(label=self.__admin_console.props['label.enableBackupValidation']):
            panel_details.enable_toggle(self.__admin_console.props['label.enableBackupValidation'])
        else:
            panel_details.edit_tile()
        edit_app_validation_base_xp = f"//*[@class='mui-modal-title' and " \
                                      f"text()='{self.__admin_console.props['label.editBackUpValidation']}']" \
                                      f"//ancestor::div[contains(@class, 'modal-dialog')]"
        edit_app_validation_modal = ModalDialog(self.__admin_console, xpath=edit_app_validation_base_xp)
        script_details_modal = ModalDialog(self.__admin_console, title='Custom validation script')
        drop_details = DropDown(self.__admin_console)

        # Copy selection is available only if snap is enabled for the vm group
        if backup_validation_options.get('snap_copy') is not None:
            copy_xp = "//div[@id='sourceCopyDropdown']//ancestor::div[contains(@class, 'dd-wrapper')]"
            if self.__admin_console.check_if_entity_exists("xpath", copy_xp):
                drop_details.select_drop_down_values(values=[backup_validation_options['copy_name']],
                                                     drop_down_id='sourceCopyDropdown',
                                                     case_insensitive_selection=True)
            else:
                raise Exception("Source copy selection is missing for application validation configuration")

        if not backup_validation_options.get('snap_copy'):
            if backup_validation_options.get('recovery_target'):
                edit_app_validation_modal.disable_toggle(toggle_element_id='liveMountUsingSourceEsx')
                drop_details.select_drop_down_values(values=[backup_validation_options['recovery_target']],
                                                     drop_down_id='recoveryTargetsDropdown')
            else:
                edit_app_validation_modal.enable_toggle(toggle_element_id='liveMountUsingSourceEsx')

            if backup_validation_options.get('recovery_target'):
                if backup_validation_options.get('retain_vms'):
                    edit_app_validation_modal.enable_toggle(toggle_element_id='runAsDevTestGroup')
                else:
                    edit_app_validation_modal.disable_toggle(toggle_element_id='runAsDevTestGroup')

        if backup_validation_options.get('schedule', False):
            self.schedule_backup_validation()
        else:
            edit_app_validation_modal.disable_toggle(toggle_element_id='backupValidationSchedule')

        if backup_validation_options.get('snap_copy'):
            edit_app_validation_modal.click_submit()
            return

        # custom validation
        self.__admin_console.scroll_into_view("//div[@id='customAppPanel']")
        edit_app_validation_modal.expand_accordion(id='customAppPanel')
        add_script_xpath = "//*[text()='{0}']/parent::div//button[@aria-label='Add']"

        win_script_text = 'Windows script'
        win_add_script_xp = add_script_xpath.format(win_script_text)
        win_add_script_exists = self.__admin_console.check_if_entity_exists('xpath', win_add_script_xp)

        unix_script_text = 'Unix script'
        unix_add_script_xp = add_script_xpath.format(unix_script_text)
        unix_add_script_exists = self.__admin_console.check_if_entity_exists('xpath', unix_add_script_xp)

        if backup_validation_options.get('path_win') or backup_validation_options.get('path_unix'):
            if backup_validation_options.get('path_win'):
                if not win_add_script_exists:
                    # Click on Edit from dropdown
                    edit_app_validation_modal.click_action_item("Edit", preceding_label=win_script_text)
                else:
                    edit_app_validation_modal.click_button_on_dialog(win_script_text, preceding_label=True)
                script_details_modal.fill_text_in_field('path', backup_validation_options.get('path_win'))
                if backup_validation_options.get('script_argument_win'):
                    script_details_modal.fill_text_in_field('arguments',
                                                            backup_validation_options.get('script_argument_win'))
                script_details_modal.click_submit()

            if backup_validation_options.get('path_unix'):
                if not unix_add_script_exists:
                    # Click on Edit from dropdown
                    edit_app_validation_modal.click_action_item("Edit", preceding_label=unix_script_text)
                else:
                    edit_app_validation_modal.click_button_on_dialog(unix_script_text, preceding_label=True)
                script_details_modal.fill_text_in_field('path', backup_validation_options.get('path_unix'))
                if backup_validation_options.get('script_argument_unix'):
                    script_details_modal.fill_text_in_field('arguments',
                                                            backup_validation_options.get('script_argument_unix'))
                script_details_modal.click_submit()
        else:
            self.__admin_console.log.info("Clearing custom scripts, if any")
            if not win_add_script_exists:
                edit_app_validation_modal.click_action_item("Delete", preceding_label=win_script_text)
            if not unix_add_script_exists:
                edit_app_validation_modal.click_action_item("Delete", preceding_label=unix_script_text)

        # Guest credentials
        self.__admin_console.scroll_into_view("//div[@id='guestCredPanel']")
        edit_app_validation_modal.expand_accordion(id='guestCredPanel')
        edit_app_validation_modal.checkbox.uncheck('Saved credentials')
        edit_app_validation_modal.fill_text_in_field("userName", backup_validation_options.get('user', ''))
        edit_app_validation_modal.fill_text_in_field("password", backup_validation_options.get('password', ''))
        edit_app_validation_modal.click_submit()

    def schedule_backup_validation(self, only_schedule=False, after_time=None):
        """
        Scheduling backup validation
        Args:
            only_schedule           (bool): If we are only editing the schedule of the backup validation

            after_time:             (integer): set the schedule after number of seconds

        """
        # can be used schedules.py to enhance this
        if only_schedule:
            self.__admin_console.select_configuration_tab()
            panel_details = PanelInfo(self.__admin_console, self.__admin_console.props['label.backupValidation'])
            if not panel_details.is_toggle_enabled(label=self.__admin_console.props['label.enableBackupValidation']):
                panel_details.enable_toggle(self.__admin_console.props['label.enableBackupValidation'])
            else:
                panel_details.edit_tile()
        edit_app_validation_base_xp = f"//*[@class='mui-modal-title' and " \
                                      f"text()='{self.__admin_console.props['label.editBackUpValidation']}']" \
                                      f"//ancestor::div[contains(@class, 'modal-dialog')]"
        edit_app_validation_modal = ModalDialog(self.__admin_console, xpath=edit_app_validation_base_xp)
        edit_schedule_pattern = ModalDialog(self.__admin_console, title="Edit schedule pattern")

        inline_schedule_button_xp = "//div[contains(@class, 'inline-time-fields')]//button"
        if self.__admin_console.check_if_entity_exists("xpath", inline_schedule_button_xp):
            self.__admin_console.click_by_xpath(inline_schedule_button_xp)
        else:
            edit_app_validation_modal.enable_toggle(toggle_element_id='backupValidationSchedule')
        edit_schedule_pattern.fill_text_in_field("name", self.__admin_console.driver.session_id)
        edit_schedule_pattern.select_dropdown_values("scheduleFrequency", ["Daily"])
        current_time = time.time()
        # adding 3 hours in the schedule
        if not after_time:
            after_time = 3 * 60 * 60
        schedule_time = current_time + after_time
        input_time = time.strftime("%I:%M %p", time.localtime(schedule_time))
        schedule_time_xp = "//div[@id='scheduleTime']//input"
        self.__admin_console.fill_form_by_xpath(xpath=schedule_time_xp, value=input_time)
        edit_schedule_pattern.click_submit()
        if only_schedule:
            edit_app_validation_modal.click_submit()

    @PageService()
    def run_validate_backup(self, recovery_point=None):
        """
        Runs Backup Validation jobs

        Returns:
            job_id  (str):   the job id of the backup validation

            recovery_point   (str):   the recovery point to be selected from calendar for validation
                                        Format : HH:MM <AM/PM>
                                                 01:30 PM
        """
        self.__admin_console.select_overview_tab()
        panel_details = PanelInfo(self.__admin_console, self.__admin_console.props['header.recoveryPoints'])
        if recovery_point:
            rp_xp = f"//div[text()='{recovery_point}']"
            self.__admin_console.scroll_into_view(rp_xp)
            panel_details.click_button(recovery_point)
        panel_details.click_button(self.__admin_console.props['label.validateBackup'])
        my_dialog = ModalDialog(self.__admin_console)
        my_dialog.click_submit(wait=False)
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def update_storage_plan(self, plan_name=None):
        """
        Updates storage plan at VM group Level

        Args:
            plan_name  (str): Name of the storage plan node to be edited
        """

        vmg_summary_panel = PanelInfo(self.__admin_console, 'Summary')
        dropdown = DropDown(self.__admin_console)
        vmg_summary_panel.edit_tile_entity(entity_name='Plan')
        self.__admin_console.log.info("Editing Storage Plan: {} at VM Group level".format(plan_name))
        dropdown.select_drop_down_values(drop_down_id='plan', values=[plan_name])
        vmg_summary_panel.click_button('Submit')

    @PageService()
    def update_access_node(self, proxy_name=None):
        """
        Updates access nodes at VM group Level

        Args:
            proxy_name      (str): Name of the access node to be added
        """
        acnode_panel = PanelInfo(self.__admin_console, 'Access nodes')
        acnode_modal = ModalDialog(self.__admin_console, 'Edit access nodes')
        acnode_tree = TreeView(self.__admin_console)
        self.__admin_console.select_configuration_tab()

        self.__admin_console.log.info("Setting access node: {} at VM Group level".format(proxy_name))
        acnode_panel.click_action_item("Edit")
        self.__admin_console.log.info("Clearing all previous selected access nodes")
        acnode_tree.clear_all_selected()

        acnode_tree.select_items([proxy_name])
        acnode_modal.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def update_number_of_readers(self, number_of_readers=None):
        """
        Updates number_of_readers

        Args:
            number_of_readers      (str): Number of readers to be added
        """
        acnode_panel = PanelInfo(self.__admin_console, 'Options')
        acnode_modal = ModalDialog(self.__admin_console, 'Edit options')
        self.__admin_console.select_configuration_tab()
        acnode_panel.edit_tile()
        self.__admin_console.fill_form_by_id("noOfReaders", number_of_readers)
        acnode_modal.click_submit()
        self.__toggle_obj = Toggle(self.__admin_console)
        self.__toggle_obj.enable('Index files after backup')
        self.__admin_console.wait_for_completion()

    @PageService()
    def update_frel(self, frel=None):
        """
        Updates frel

        Args:
            frel      (str): Enables file recovery
        """
        acnode_panel = PanelInfo(self.__admin_console, 'Options')
        acnode_modal = ModalDialog(self.__admin_console, 'Edit file recovery node')
        self.__admin_console.select_configuration_tab()
        acnode_panel.edit_tile()
        self.__panel_dropdown_obj.select_drop_down_values(drop_down_id='fbrUnixMA',values=[frel])
        acnode_modal.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_no_of_readers_info(self):
        """
        Gets the no_of_readers info

        Returns Number of readers
        """
        Readers_detail = {}
        acnode_panel = PanelInfo(self.__admin_console, 'Options')
        acnode_modal = ModalDialog(self.__admin_console, 'Edit options')
        self.__admin_console.select_configuration_tab()
        acnode_panel.edit_tile()
        Readers_detail['number_of_readers'] = self.__admin_console.get_element_value_by_id("noOfReaders")
        acnode_modal.click_submit()
        self.__admin_console.wait_for_completion()
        return Readers_detail

    @PageService()
    def get_frel_info(self):
        """
        Gets the frel info

        Returns frel value
        """
        FREL_detail = {}
        acnode_panel = PanelInfo(self.__admin_console, 'Options')
        acnode_modal = ModalDialog(self.__admin_console, 'Edit file recovery node')
        self.__admin_console.select_configuration_tab()
        acnode_panel.edit_tile()
        FREL_detail['frel'] = self.__admin_console.get_element_value_by_id("fbrUnixMA")
        acnode_modal.click_submit()
        self.__admin_console.wait_for_completion()
        return FREL_detail

    @PageService()
    def get_tag_name_info(self):
        """
        Gets the tag_name info

        Returns tag_name value
        """
        tag_name_detail = {}
        acnode_panel = PanelInfo(self.__admin_console, 'Tags')
        hypervisor_details_dialog = ModalDialog(self.__admin_console, title='Manage tags')
        self.__admin_console.select_configuration_tab()
        acnode_panel.edit_tile()
        tag_name_detail['tag_name'] = self.__admin_console.get_element_value_by_id("tagname")
        hypervisor_details_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        return tag_name_detail

    @PageService()
    def update_tag_name(self, tag_name=None):
        """
        Updates tag_name

        Args:
            tag_name      (str): Name of the tag to be added
        """
        acnode_panel = PanelInfo(self.__admin_console, 'Tags')
        acnode_modal = ModalDialog(self.__admin_console, 'Manage tags')
        self.__admin_console.select_configuration_tab()
        acnode_panel.edit_tile()
        self.__admin_console.fill_form_by_id("tagname", tag_name)
        acnode_modal.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def azure_snapshot_settings(self, snapshot_tags={}, custom_snapshot_rg=None, get_settings=False):
        """

        Args:
            snapshot_tags       (dict)  : list of tags to be added on snapshot [key-value pair]
            custom_snapshot_rg  (str)   : name of custom resource group for azure snapshot creation
            get_settings        (bool)  : True if only value of settings is required

        Returns:
            settings_details    (dict)  : dict with defined values of  all settings

        Raises:
            Exception:
                if unable to complete given operation
        """
        self.__admin_console.select_configuration_tab()
        snapshot_setting_panel = PanelInfo(self.__admin_console, "Azure snapshot settings")

        if get_settings:
            return snapshot_setting_panel.get_details()

        if snapshot_tags:
            pass

        if custom_snapshot_rg:
            snapshot_setting_panel.edit_tile_entity(entity_name="Custom resource group for disk snapshots")
            self.__panel_dropdown_obj.select_drop_down_values(drop_down_id="guid", values=[custom_snapshot_rg])
            snapshot_setting_panel.click_button("Submit")

    @PageService()
    def get_vm_group_content(self, content_rule=False):
        """
        Args:
            content_rule : (boolean) - Whether content is VM based or rule based
                            False : content is VM based
                            True : content is rule based
        returns dict of VM group content

        """
        if not content_rule:
            from Web.AdminConsole.VSAPages.manage_content import ManageContent
            self.manage_content()
            manage_content_obj = ManageContent(self.__admin_console)
            return manage_content_obj.preview().keys()
        else:
            self.__admin_console.select_content_tab()
            return self.get_content_rule()

    @PageService()
    def get_content_rule(self):
        """
        Fetches the content rule of a VM group

        Returns the rules in the form of ordered dict:

        {
            Rule : {
                [
                    {
                        rule_type: {
                            rule_operator : rule_value
                        }
                    }
                ]
            }
        }

        """

        Operator = "AND | OR"
        Condition = "equals | does not equal | contains | does not contain | starts with | ends with"

        final_rule = []
        rule_group = self.__driver.find_element(By.XPATH, "//div[@id = 'vmgroups-overview-content']//div[@id = 'contentRuleText']//"
                                                           "*[contains(@class, 'content-doc-icon')]/following-sibling::div")
        rule_string = rule_group.text.partition('.')[0] + ' ' + rule_group.get_attribute('aria-label')
        rule_list = re.split(Operator, rule_string)
        for each_rule in rule_list:
            each_rule = each_rule.strip()
            parts = re.split(f"({Condition})", each_rule)
            rule_type = parts[0].strip()
            rule_operator = parts[1].strip()
            rule_name = parts[2].strip()
            final_rule.append(OrderedDict([(rule_type, OrderedDict([(rule_operator, rule_name)]))]))

        return OrderedDict([("Rule", final_rule)])


    @PageService()
    def fetch_vmgroup_details(self, content_rule=False):
        """
        Fetches the VM group detail

        Returns dict of vm group details
        """
        self.__admin_console.log.info("Fetching VM group name and details")
        self.__admin_console.select_overview_tab()
        general_info = self.subclient_summary()
        hypervisor_name = general_info['Hypervisor name']
        plan = general_info['Plan']
        vmgroup_title = self.vmgroup_name()
        vm_group_content = self.get_vm_group_content(content_rule=content_rule)
        tag_name_detail = self.get_tag_name_info()
        Readers_detail = self.get_no_of_readers_info()
        self.__admin_console.select_configuration_tab()
        config_panel_obj = PanelInfo(self.__admin_console, title=self.__admin_console.props['heading.proxyNodes'])
        access_nodes = [*config_panel_obj.get_details()]
        return {"vmgroup_name": vmgroup_title,
                "hypervisor_name": hypervisor_name,
                "plan": plan,
                "vm_group_content": vm_group_content,
                "tag_name": tag_name_detail,
                "number_of_readers":Readers_detail,
                "proxy_list":access_nodes}

    @WebAction()
    def vmgroup_name(self):
        """
        Gets the current vm group name

        returns (str)   name of the vmgroup
        """
        self.__page_container_obj = PageContainer(self.__admin_console)
        return self.__page_container_obj.fetch_title()

    @PageService()
    def action_list_snapshots(self):
        """
        list the snaps of particular vmgroup at VMgroup or subclient level
        Args:
            vm_name  (str):  the name of the Particular VMgroup for list of snapshots
        """
        self.__admin_console.access_page_action_menu_by_class("popup")
        self.__admin_console.click_button_using_text("List snapshots")

