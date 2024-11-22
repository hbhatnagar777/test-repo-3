# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# When editing this file kindly either of the following people for review : Aravind Putcha , Rohan Prasad

"""
This module provides the function or operations that can be performed on
all the FS Agent Details from Command Center.

"""

from typing import Optional
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.AdminConsolePages.agents import Agents
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RModalPanel, RPanelInfo, RDropDown
from Web.AdminConsole.Components.browse import RBrowse
from selenium.webdriver.common.by import By
import os
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils, RRestorePanel
from Web.AdminConsole.FSPages.RFsPages.SNAP_Common_Helper import SnapUtils
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import AddWizard as Addwizard


class Overview:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.__rbrowse = RBrowse(admin_console)
        self.__driver = admin_console.driver
        self.__restore_panel = RRestorePanel(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__fsutils = FileServersUtils(admin_console)
        self.admin_console = admin_console

    @PageService()
    def restore_from_calender(self,
                              calender,
                              backupset_name="defaultBackupSet",
                              measure_time=True,
                              dest_client=None,
                              rest_path=None,
                              unconditional_overwrite=False,
                              search_pattern=None,
                              acl=True,
                              data=True,
                              restore_aux_copy=False,
                              storage_copy_name=None,
                              selected_files=[],
                              impersonate_user=None,
                              show_deleted_items=False,
                              deleted_items_path=[],
                              show_hidden_items=False,
                              hidden_items_path=[],
                              **kwargs
                              ):
        """
        Function to restore data from RPC Calender

        Args:
            calender (_type_): _description_
        """

        self.__fsutils.restore_from_calender(calender, backupset_name, measure_time)

        return self.__fsutils.restore(
            dest_client=dest_client,
            restore_acl=acl,
            restore_data=data,
            destination_path=rest_path,
            restore_aux_copy=restore_aux_copy,
            storage_copy_name=storage_copy_name,
            unconditional_overwrite=unconditional_overwrite,
            selected_files=selected_files,
            impersonate_user=impersonate_user,
            show_deleted_items=show_deleted_items,
            deleted_items_path=deleted_items_path,
            show_hidden_items=show_hidden_items,
            hidden_items_path=hidden_items_path,
            search_pattern=search_pattern,
            **kwargs
        )

    @PageService()
    def change_plan_from_protection_summary(self, new_plan_name: str):
        """
        Changes plan from protection summary panel

        Args:
            new_plan_name (str): Plan name to change to
        """
        temp_panel = RPanelInfo(self.admin_console, title="Protection summary")
        temp_panel.edit_tile_entity("Plan")
        self.__rdropdown.select_drop_down_values(
            drop_down_id="subclientPlanSelection", values=[new_plan_name]
        )
        self.__rmodal_dialog.click_submit()
        # TODO - Need to add change content part

    @PageService()
    def change_workload_from_general_card(self, new_workload_name: str) -> None:
        """
        Change the workload region from the general card

        Args:
            new_workload_name (str): Name of the new workload region to be changed to.
        """
        temp_panel = RPanelInfo(self.admin_console, title="General")
        temp_panel.edit_tile_entity("Workload region")
        self.__rdropdown.select_drop_down_values(
            drop_down_id="regionDropdown_", values=[new_workload_name]
        )
        self.__driver.find_element(By.ID, "tile-row-submit").click()

    @PageService()
    def verfiy_general_card_details(self):
        """
        Verfiy the UI details for general card
        """
        temp_panel = RPanelInfo(self.admin_console, title="General")
        details = temp_panel.get_details()
        # TODO - verify the detals from the backen

    @PageService()
    def is_ibmi_client_status_ready_under_overview_page(self):
        """Read the check readiness from IBMi client overview page"""
        protection_panel = RPanelInfo(self.admin_console, title="Protection summary")
        readiness = protection_panel.get_details()['Client readiness']
        if "Not Ready" in readiness:
            return False
        elif "Ready" in readiness:
            return True
        else:
            raise Exception("IBMi client check-readiness cannot be identified.")

    @PageService()
    def is_ibmi_client_status_ready_under_check_readiness_page(self):
        """Read the check readiness from IBMi page"""
        client_role = self.__rtable.get_column_data(column_name="Role", fetch_all=False)
        client_status = self.__rtable.get_column_data(column_name="Status", fetch_all=False)
        if client_status[client_role.index("IBM i")] == 'Ready.':
            return True
        else:
            return False

    @PageService()
    def modify_ibmi_plan_from_protection_summary(self, plan_name: str):
        """
        modify the plan of IBMi client from protection summary panel

        Args:
            plan_name (str): Plan name to change to
        """
        temp_panel = RPanelInfo(self.admin_console, title="Protection summary")
        temp_panel.edit_tile_entity("Plan")
        self.__rdropdown.select_drop_down_values(
            drop_down_id="subclientPlanSelection", values=[plan_name]
        )
        self.__rmodal_dialog.click_submit()

    @PageService()
    def verfiy_protection_card_details(self):
        """
        Verfiy the UI details for protection card
        """
        temp_panel = RPanelInfo(self.admin_console, title="Protection summary")
        details = temp_panel.get_details()

        # TODO :
        # {'Host Name': '172.16.65.36', 'Install date': 'May 31, 2:32 PM', 'Version': '11.34.6',
        # 'Company': 'cmvlt', 'Operating system': 'Unix', 'Workload region': 'Asia'}
        #  client.client_hostname
        # workloadRegionDisplayName
        # client.company_name
        # client
        # client.os_info
        #         >>> client.version
        # '11'
        # >>> client.service_pack
        # '34'
        # 'x86_64 Unix Linux  --  CentOS Linux 7
        # 'versionInfo': {'UpdateStatus': 1, 'IsBaselineComparedToClient': 0, 'releaseName': '2024', 'version': 'ServicePack:34.6
        #         >>> client.os_info
        # 'x86_64 Unix Linux  --  CentOS Linux 7'
        # >>> client.os_info
        # ' Any NAS  --  NAS Filer'


class Configuration:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.admin_console = admin_console

    # @PageService()
    def add_security_association(self):
        pass

    @PageService()
    def activity_control(
            self,
            enable_backup=None,
            disable_backup=None,
            enable_restore=None,
            disable_restore=None,
    ):
        """
        Enable / Disable Data backup / Restore operation
        """

        activity_control_panel_info = RPanelInfo(self.admin_console, title="Activity Control")

        if enable_backup:
            activity_control_panel_info.enable_toggle("Data backup")
        if disable_backup:
            activity_control_panel_info.disable_toggle("Data backup")
            self.__rmodal_dialog.click_submit()
        if enable_restore:
            activity_control_panel_info.enable_toggle("Data restore")
        if disable_restore:
            activity_control_panel_info.disable_toggle("Data restore")

    # @PageService()
    def edit_server_groups(self):
        pass

    @PageService()
    def toggle_snap_backup(
            self,
            enable_snap=None,
            disable_snap=None
    ):
        """
        Toggle to enable / disable snap backup
        """

        snap_panel_info = RPanelInfo(self.admin_console, title="Snapshot management")

        if enable_snap:
            snap_panel_info.enable_toggle("Enable snap backup")
        if disable_snap:
            snap_panel_info.disable_toggle("Enable snap backup")

        self.__rmodal_dialog.click_submit()

    # @PageService()
    def enable_content_indexing(self):
        pass

    @PageService()
    def edit_threat_analysis(self):
        """
        Edit the Data classification plan
        """

        temp_panel = RPanelInfo(self.admin_console, title="Threat analysis")

    @PageService()
    def edit_tags(
            self,
            add_tags=None,
            delete_tags=None,
            edit_tags=None
    ):
        """
        Method to Add / Remove tags

        Args:
            add_tags: dict(tag_name, tag_val)
            delete_tags: dict(tag_name, tag_val)
            edit_tags: dict(tuple(old_tag, old_val), tuple(new_tag, new_val))
        """

        tags_panel_info = RPanelInfo(self.admin_console, title="Tags")
        tags_panel_info.edit_tile()

        from Web.AdminConsole.Components.dialog import RTags

        rtags = RTags(self.admin_console)

        if add_tags:
            for tag in add_tags:
                rtags.add_tag(tag, add_tags[tag])

        if delete_tags:
            for tag in delete_tags:
                rtags.delete_tag(tag, delete_tags[tag])

        if edit_tags:
            for tag in edit_tags:
                rtags.modify_tag(tag, edit_tags[tag])

        self.__rmodal_dialog.click_submit()


class Subclient:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.__rbrowse = RBrowse(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__wizard = Wizard(admin_console)
        self.__checkbox = Checkbox(admin_console)
        self.__addwizard = Addwizard(admin_console)
        self.admin_console = admin_console
        self.__driver = admin_console.driver
        self.__fileserver_utils = FileServersUtils(admin_console)
        self.__snaputils = SnapUtils(admin_console)
        self.__page = PageContainer(admin_console)
        self.__restore_panel = RRestorePanel(admin_console)
        self.__props = self.admin_console.props

    @WebAction()
    def __switch_backupset(self, backupset_name: str) -> None:
        """Web Action to switch backupset"""

        if self.__rdropdown.is_dropdown_exists(drop_down_id="Backup sets"):
            self.__rtable.set_default_filter(
                filter_id="Backup sets", filter_value=backupset_name
            )

    @PageService()
    def select_backupset(self, backupset_name: str):
        """Web Action to switch backupset"""
        self.__switch_backupset(backupset_name)

    @PageService()
    def delete_backup_set(self, backupset_name: str) -> None:
        """
        Deletes the backup set with the given name

        Args:
            backupset_name (str): Name of the backup set to delete
        """
        self.__switch_backupset(backupset_name)
        btn_xpath = "//button[contains(.,'Delete backup set')]"
        if self.__driver.find_element(By.XPATH, btn_xpath).is_enabled():
            self.admin_console.click_button("Delete backup set")
            self.__rmodal_dialog.fill_text_in_field(
                element_id="confirmText", text="DELETE"
            )
            self.__rmodal_dialog.click_submit()
        else:
            self.admin_console.log.info("Delete backupset button is disabled")

    @PageService()
    def add_subclient(
            self,
            subclient_name: str,
            plan_name: str,
            contentpaths: list[str] = [],
            impersonate_user: dict = None,
            contentfilters: list[str] = [],
            contentexceptions: list[str] = [],
            backupset_name: str = "defaultBackupSet",
            define_own_content: bool = False,
            remove_plan_content: bool = True,
            disablesystemstate=False,
            pre_backup_process: str = "",
            post_backup_process: str = "",
            is_nas_subclient: bool = False,
            saved_credentials: str = None
    ) -> None:
        """
        Creates a new subclient with the given name

        Args:
            subclient_name (str): Name of the new subclient to be created
            plan_name (str): Plan to be assigned to the new subclient
            contentpaths (list[str], optional): Content to be backed up if required . Defaults to [].
            impersonate_user (dict, optional): Impersonating for NAS clients while adding content
            contentfilters (list[str], optional): Filters to be added if required. Defaults to [].
            contentexceptions (list[str], optional): Exceptions to be added if required. Defaults to [].
            backupset_name (str, optional): Nmae of the backupset to create the subclient in. Defaults to "defaultBackupSet".
            define_own_content (bool, optional): If want to define own contents. Defaults to False.
            disablesystemstate (bool, optional): If system state needs to be disabled for subclient. Defaults to False.
            pre_backup_process (str, optional): pre-backup-process script if required. Defaults to "".
            post_backup_process (str, optional): post-backup-process scrip if required. Defaults to "".
            is_nas_subclient (bool, optional): True to create a NAS subclient. Defaults to False
            saved_credentials (str): Impersonate using saved credential
        """

        self.admin_console.click_button("Add subclient")
        self.__wizard.fill_text_in_field(id="subclientName", text=subclient_name)

        if backupset_name != "defaultBackupSet":
            # Adding this if conditon because backupset dropdown is not visible if only one backup_set is present
            self.__wizard.select_drop_down_values(
                id="backupSetDropdown", values=[backupset_name]
            )
        self.__wizard.click_next()
        self.__addwizard.select_plan(planname=plan_name)

        if is_nas_subclient:
            define_own_content = True

        if define_own_content:
            # We can have plane without content defined. Hence we need to check if the toggle
            # to define own content is present
            # define_own_content should always be True for creating nas subclients
            if self.__checkbox.is_exists(id="overrideBackupContent") and (not is_nas_subclient):
                self.__wizard.enable_toggle("Define your own backup content")
                # Removing plan content if required. Can also act as override plan content
                if remove_plan_content:
                    self.__fileserver_utils.remove_plan_content()
                    self.__fileserver_utils.remove_plan_exceptions()
                    self.__fileserver_utils.remove_plan_exclusions()

            # define own content using content paths
            self.__addwizard.set_backup_content_filters(
                contentpaths, contentfilters, contentexceptions, disablesystemstate,
                impersonate_user=impersonate_user, is_nas_subclient=is_nas_subclient,
                saved_credentials=saved_credentials
            )
        else:
            self.__wizard.disable_toggle("Define your own backup content")
            self.__wizard.click_next()

        if pre_backup_process:
            self.__wizard.fill_text_in_field(
                id="backupPreProcessCommand", text=pre_backup_process
            )

        if post_backup_process:
            self.__wizard.fill_text_in_field(
                id="backupPostProcessCommand", text=post_backup_process
            )

        self.__wizard.click_button("Submit")
        self.admin_console.wait_for_completion()

    @PageService()
    def edit_content_for_subclient(
            self, subclient_name: str, backupset_name: str = "defaultBackupSet"
    ) -> None:
        """
        _summary_

        Args:
            subclient_name (str): _description_
            backupset_name (str, optional): _description_. Defaults to "defaultBackupSet".
        """
        # TODO
        self.__switch_backupset(backupset_name)
        subclient_name_xpath = f"//td//a[contains(text(),'{subclient_name}')]"
        if self.admin_console.check_if_entity_exists("xpath", subclient_name_xpath):
            pass
            # subclient_value = self._driver.find_element(By.XPATH,subclient_name_xpath)
            # subclient_row = subclient_value.find_element(By.XPATH,"./..")
            # subclient_row_expand_icon = subclient_row.find_element(By.XPATH,".//td[1]")
            # subclient_row_expand_icon.click()
            # parent = child.find_element(By.XPATH, "./..")

            # download_icon = parent.find_element(By.XPATH, ".//td[4]")

            # download_icon.click()

    @PageService()
    def delete_subclient(
            self, subclient_name: str, backupset_name: str = "defaultBackupSet"
    ) -> None:
        """
        Deletes the specified subclient for the given backup set.

        Args:
            subclient_name (str): Name of the subclient to delete
            backupset_name (str): Name of the backup_set
        Raises:
                Exception :
                 -- if fails to delete subclient
        """
        self.__switch_backupset(backupset_name)
        if self.is_subclient_exists(subclient_name, backupset_name):
            self.__rtable.access_action_item(subclient_name, "Delete")
            self.__rmodal_dialog.click_submit()

    @PageService()
    def is_subclient_exists(
            self, subclient_name: str, backupset_name: str = "defaultBackupSet"
    ) -> bool:
        """
        Verifies if the subclient exists or not

        Args:
            subclient_name (str): Name of the subclient to check
            backupset_name (str): Name of the backup_set

        Returns:
            bool: returns true if the subclient exists
        """
        self.__switch_backupset(backupset_name)
        subclient_list = self.__rtable.get_column_data("Name")
        for name in subclient_list:
            if name == subclient_name:
                return True
        return False

    @PageService()
    def access_subclient(
            self, subclient_name: str, backupset_name: str = "defaultBackupSet"
    ):
        """
        Naviages to the subclient details for the given subclient

        Args:
            subclient_name (str): Name of the subclient to be accessed
            backupset_name (str): Name of the backup_set
        """
        self.__switch_backupset(backupset_name)
        self.__rtable.access_link(subclient_name)

    @PageService()
    def backup_subclient(
            self,
            subclient_name: str,
            backup_type: enumerate,
            backupset_name: str = "defaultBackupSet",
    ) -> str:
        """
        Function to run a backup job for a subclient
           Args:
               subclient_name (str): Name of the subclient to backup
               backup_type (enum) : Type of backup (FULL, INCREMENTAL, SYNTHETIC_FULL)
               backupset_name (str) : Name of the backup_set
           Raises:
               Exception :
                -- if fails to run the backup
           Returns:
               Job Id (str) : Job id for the backup job
        """

        self.__switch_backupset(backupset_name)
        self.__rtable.access_action_item(subclient_name, self.admin_console.props['header.backup'])
        self.__rmodal_dialog.select_radio_by_id(radio_id=backup_type.value.upper())
        self.__rmodal_dialog.click_submit(wait=False)
        return self.admin_console.get_jobid_from_popup()

    @PageService()
    def restore_subclient(
            self,
            subclient_name: str,
            backupset_name: str = "defaultBackupSet",
            dest_client: Optional[str] = None,
            restore_acl: bool = True,
            restore_data: bool = True,
            destination_path: str = None,
            restore_aux_copy: bool = False,
            block_level=None,
            storage_copy_name: Optional[str] = None,
            unconditional_overwrite: bool = False,
            selected_files: Optional[list[str]] = None,
            modified_file: Optional[str] = None,
            version_nums: Optional[list[str]] = None,
            impersonate_user: Optional[dict] = None,
            job_id: Optional[str] = None,
            show_deleted_items: Optional[bool] = False,
            deleted_items_path: Optional[list[str]] = None,
            show_hidden_items: Optional[bool] = False,
            hidden_items_path: Optional[list[str]] = None,
            **kwargs
    ) -> str:

        """
        Restore the given subclient

        Returns:
            Job id(str): Returns the job id for the restore job
        """

        self.__switch_backupset(backupset_name)

        # Restore subclient by job
        if job_id:
            self.admin_console.access_tab("Jobs")
            self.__rtable.access_action_item(job_id, self.admin_console.props['label.globalActions.restore'])
        else:
            self.__rtable.access_action_item(subclient_name, self.admin_console.props['label.globalActions.restore'])

        self.admin_console.wait_for_completion()

        if block_level:
            if block_level == 'FILE_LEVEL':
                self.admin_console.click_by_xpath(
                    "//div[contains(@class, 'MuiGrid-root MuiGrid-container')]//div//a//div[contains(string(), 'File level restore')]")
            if block_level == 'VOLUME_LEVEL':
                self.admin_console.click_by_xpath(
                    "//div[contains(@class, 'MuiGrid-root MuiGrid-container')]//div//a//div[contains(string(), 'Volume level restore')]")

        return self.__fileserver_utils.restore(
            dest_client=dest_client,
            restore_acl=restore_acl,
            restore_data=restore_data,
            destination_path=destination_path,
            restore_aux_copy=restore_aux_copy,
            storage_copy_name=storage_copy_name,
            unconditional_overwrite=unconditional_overwrite,
            selected_files=selected_files,
            modified_file=modified_file,
            version_nums=version_nums,
            impersonate_user=impersonate_user,
            show_deleted_items=show_deleted_items,
            deleted_items_path=deleted_items_path,
            show_hidden_items=show_hidden_items,
            hidden_items_path=hidden_items_path,
            **kwargs
        )

    @PageService()
    def download_selected_items(self, subclient_name: str,
                                parent_dir=None,
                                backupset_name: str = "defaultBackupSet",
                                download_files: list[str] = None,
                                select_all: bool = False
                                ):
        """
        Method to download files/folders

        Args:
            subclient_name (str): Name of the subclient
            parent_dir (str) : Path from which the files / folders have to be downloaded
            backupset_name (str): Name of the backupset
            download_files list(str): List of files / folders to select for download
            select_all (bool) : True to select all content. False by default
        """

        self.__switch_backupset(backupset_name)
        self.__rtable.access_action_item(subclient_name, self.admin_console.props['label.globalActions.restore'])
        return self.__fileserver_utils.download_selected_items(parent_dir=parent_dir,
                                                               download_files=download_files,
                                                               select_all=select_all)

    @PageService()
    def backup_history_subclient(self, subclient_name: str, date_range: str):
        """
        Navigate to the backup history for the given subclient

        Args:
            subclient_name (str): Name of the subclient
            date_range (str): TODO: Which button for range do we want to select
        """
        # Date range bascially click it as button
        self.__rtable.access_action_item(subclient_name, "Backup history")

    @PageService()
    def enable_snapshot_engine(self, enable_snapshot, engine_name=None):
        """
        Sets the snapshot engine for the subclient
        Args:
            enable_snapshot (bool):     to enable / disable snap backups on the subclient

            engine_name     (str):   name of the snapshot engine

        Returns:
            None

        Raises:
            Exception:
                if not able to change snapshot
        """
        self.admin_console.access_tab(self.admin_console.props['header.configuration'])
        temp_panel = RPanelInfo(self.admin_console, title="Snapshot management")

        if temp_panel.get_toggle_element(label=self.admin_console.props['label.ConfirmEnableIntelliSnap']):
            if enable_snapshot:
                temp_panel.enable_toggle(self.admin_console.props['label.ConfirmEnableIntelliSnap'])
                self.__rdropdown.select_drop_down_values(
                    drop_down_id="enginesDropdown", values=[engine_name])
                if not engine_name:
                    raise Exception("The engine name is not provided")
            else:
                temp_panel.disable_toggle(self, self.admin_console.props['label.ConfirmEnableIntelliSnap'])

        self.__rmodal_dialog.click_submit()

    @PageService()
    def add_ibmi_backupset(self,
                           backupset_name,
                           plan_name,
                           mark_as_default_backupset=False):
        """
        Method to add a backupset from IBMi client page.
        Args:
            backupset_name (str) : Name of the backupset to be created
            plan_name (str) : Name of the plan to be used,
            mark_as_default_backupset: (bool) : Should mark as default backupset. Defaults to False

        """
        self.__page.access_page_action(self.admin_console.props['action.CreateNewBackupset'])
        backupset_modal = RModalDialog(self.admin_console, "Create new backup set")
        backupset_modal.fill_text_in_field("backupSetName", backupset_name)
        backupset_modal.select_dropdown_values("planSelection",
                                               [plan_name])
        if mark_as_default_backupset:
            backupset_modal.enable_toggle("isDefaultBackupSet")
        backupset_modal.click_submit()

    @PageService()
    def default_ibmi_subclients(self, backupset_name="defaultBackupSet"):
        """
            List of IBMi subclients of the backupSet
            :arg
                backupset_name: Name of BackupSet
            return: all the list of automatically created subclients
        """
        subclient_names = ['*SECDTA', '*CFG', '*IBM', '*ALLDLO', '*ALLUSR', '*LINK', '*HST log']
        if backupset_name == "defaultBackupSet":
            subclient_names.append('DR Subclient')
        return subclient_names

    @PageService()
    def is_ibmi_subclient_exists(self, subclient_name: str = "ALL",
                                 backupset_name: str = "defaultBackupSet") -> bool:
        """
        Verifies if the subclient exists or not

        Args:
            subclient_name (str): Name of the subclient to check
            backupset_name (str): Name of the backup_set

        Returns:
            bool: returns true if the subclient exists
        """
        self.__switch_backupset(backupset_name)
        subclient_list = self.__rtable.get_column_data("Name")
        subclient_names = self.default_ibmi_subclients(backupset_name=backupset_name)
        if subclient_name == "ALL":
            for each in subclient_names:
                if each not in subclient_list:
                    return False
            return True
        else:
            return subclient_name in subclient_list

    @PageService()
    def get_ibmi_subclient_plan_details(self, subclient_name: str = "ALL",
                                        backupset_name: str = "defaultBackupSet") -> bool:
        """
        Args:
            subclient_name (str): Name of the subclient to check
            backupset_name (str): Name of the backup_set
        Returns:
            protection summary panel details
        """
        if backupset_name != "defaultBackupSet":
            self.__switch_backupset(backupset_name)
        self.admin_console.select_hyperlink(subclient_name)
        self.admin_console.wait_for_completion()
        protection_panel = RPanelInfo(self.admin_console, title="Protection summary")
        assigned_plan = protection_panel.get_details()['Plan']
        return assigned_plan

    @PageService()
    def add_ibmi_subclient(
            self,
            subclient_name: str,
            plan_name: str,
            backupset_name: str = "defaultBackupSet",
            include_global_exclusions: bool = False,
            content_paths: list[str] = [],
            content_filters: list[str] = [],
            content_exceptions: list[str] = [],
            save_while_active: str = "*LIB",
            active_wait_time=0,
            pending_record: str = "*LOCKWAIT",
            other_pending_record: str = "*LOCKWAIT",
            synchronization_queue: str = "",
            synchronization_command: str = "",
            backup_spool_file: bool = False,
            pre_backup_process: str = "",
            post_backup_process: str = ""

    ) -> None:
        """
        Creates a new subclient with the given name

        Args:
            subclient_name (str): Name of the new subclient to be created
            plan_name (str): Plan to be assigned to the new subclient
            content_paths (list[str], optional): Content to be backed up if required . Defaults to [].
            content_filters (list[str], optional): Filters to be added if required. Defaults to [].
            content_exceptions (list[str], optional): Exceptions to be added if required. Defaults to [].
            backupset_name (str, optional): Nmae of the backupset to create the subclient in. Defaults to "defaultBackupSet".
            pre_backup_process (str, optional): pre-backup-process script if required. Defaults to "".
            post_backup_process (str, optional): post-backup-process scrip if required. Defaults to "".
            active_wait_time: Save while active wait duration in seconds
            save_while_active: Save while active options
            include_global_exclusions: Include global exclusions
            backup_spool_file: Backup spool file data
            synchronization_command: command to run once synchronization point is reached
            synchronization_queue: Message queue to receive messages about SWA synchronization
            other_pending_record: SWA option for other pending records
            pending_record: SWA option for pending records
        """
        # IBMi Subclient general options
        # self.__switch_backupset(backupset_name)
        self.admin_console.click_button("Add subclient")
        self.__wizard.fill_text_in_field(id="subclientName", text=subclient_name)

        if backupset_name != "defaultBackupSet":
            # Adding this if conditon because backupset dropdown is not visible if only one backup_set is present
            self.__wizard.select_drop_down_values(
                id="backupSetDropdown", values=[backupset_name]
            )
        self.__wizard.click_next()
        # Plan selection for IBMi Subclient
        self.__wizard.select_plan(plan_name=plan_name)
        self.__wizard.click_next()
        # Select content, filters, exceptions for the IBMi subclient
        if include_global_exclusions:
            self.__wizard.enable_toggle("Include global exclusions")
        self.__rdropdown.select_drop_down_values(drop_down_id="contentType", values=["Custom content"])

        self.__wizard.click_add_icon(index=0)
        self.admin_console.click_button(value='Custom path')
        for each_content in content_paths:
            self.__addwizard.add_path(each_content)

        if len(content_filters):
            self.__wizard.enable_toggle('Exclusions')
            self.__wizard.click_add_icon(index=1)
            self.admin_console.click_button(value='Custom path')
            for contentfilter in content_filters:
                self.__addwizard.add_path(contentfilter)

        if len(content_exceptions):
            self.__wizard.enable_toggle('Define exceptions')
            self.__wizard.click_add_icon(index=2)
            self.admin_console.click_button(value='Custom path')
            for contentexception in content_exceptions:
                self.__addwizard.add_path(contentexception)

        self.__wizard.click_next()
        # Select Save while active options for IBMi subclient
        if save_while_active != "*LIB":
            self.__rdropdown.select_drop_down_values(drop_down_id="saveWhileActive", values=[save_while_active])

        if active_wait_time != 0:
            self.__wizard.fill_text_in_field(
                id="activeWaitTime", text=str(active_wait_time)
            )

        if pending_record != "*LOCKWAIT":
            self.__rdropdown.select_drop_down_values(drop_down_id="pendingRecord", values=[pending_record])

        if other_pending_record != "*LOCKWAIT":
            self.__rdropdown.select_drop_down_values(drop_down_id="otherPendingRecord", values=[other_pending_record])

        if save_while_active == "*SYNCLIB":
            if synchronization_queue != "":
                self.__wizard.fill_text_in_field(
                    id="syncQueue", text=synchronization_queue
                )
            if synchronization_command != "":
                self.__wizard.fill_text_in_field(
                    id="commandToRun", text=synchronization_command
                )
        self.__wizard.click_next()
        # Select IBMi Advanced subclient options
        if backup_spool_file:
            self.__wizard.enable_toggle('Backup Spooled File Data')
        self.__wizard.click_next()

        # Select pre-post program/command for IBMi subclient
        if pre_backup_process:
            self.__wizard.fill_text_in_field(
                id="backupPreProcessCommand", text=pre_backup_process
            )
        if post_backup_process:
            self.__wizard.fill_text_in_field(
                id="backupPostProcessCommand", text=post_backup_process
            )
        self.__wizard.click_submit()
        self.admin_console.wait_for_completion()

    @PageService()
    def update_ibmi_subclient_details(self, subclient_name: str,
                                      backupset_name: str = "defaultBackupSet",
                                      plan_name: str = None,
                                      content_paths=None,
                                      content_filters=None,
                                      content_exceptions=None,
                                      include_global_exclusions=None,
                                      save_while_active=None,
                                      active_wait_time=None,
                                      pending_record = None,
                                      other_pending_record=None,
                                      synchronization_queue=None,
                                      synchronization_command=None,
                                      backup_spool_file=None
                                      ):
        """
        Update IBMi subclient details
        """
        if backupset_name != "defaultBackupSet":
            self.__switch_backupset(backupset_name)
        self.admin_console.select_hyperlink(subclient_name)
        if plan_name:
            protection_panel = RPanelInfo(self.admin_console, title="Protection summary")
            protection_panel.edit_tile_entity("Plan")
            self.__rdropdown.select_drop_down_values(
                drop_down_id="subclientPlanSelection", values=[plan_name]
            )
            self.__rmodal_dialog.click_submit()
        if content_paths or content_filters or content_exceptions:
            RPanelInfo(self.admin_console, 'Content').edit_tile()

            if include_global_exclusions:
                self.__rmodal_dialog.enable_toggle(label="Include global exclusions")

            if content_paths and content_paths[0] not in self.default_ibmi_subclients(backupset_name):
                self.__rdropdown.select_drop_down_values(drop_down_id="contentType", values=["Custom content"])
                self.__fileserver_utils.edit_ibmi_content(add_content=content_paths)

            if content_filters:
                self.__rmodal_dialog.enable_toggle(label="Exclusions")
                self.__fileserver_utils.edit_ibmi_content(add_exclusions=content_filters)

            if content_exceptions:
                self.__fileserver_utils.edit_ibmi_content(add_exceptions=content_exceptions)
            self.__rmodal_dialog.click_submit()

        if save_while_active or active_wait_time or pending_record or \
                other_pending_record or synchronization_queue or synchronization_command:
            self.admin_console.access_tab("Configuration")
            RPanelInfo(self.admin_console, 'Save while active').edit_tile()
            if save_while_active != "*LIB":
                self.__rdropdown.select_drop_down_values(drop_down_id="saveWhileActive", values=[save_while_active])

            if active_wait_time != 0:
                self.__rmodal_dialog.fill_text_in_field(
                    element_id="activeWaitTime", text=str(active_wait_time)
                )
            if pending_record and pending_record != "*LOCKWAIT":
                self.__rdropdown.select_drop_down_values(drop_down_id="pendingRecord", values=[pending_record])

            if other_pending_record and other_pending_record != "*LOCKWAIT":
                self.__rdropdown.select_drop_down_values(drop_down_id="otherPendingRecord",
                                                         values=[other_pending_record])
            if save_while_active == "*SYNCLIB":
                if synchronization_queue and synchronization_queue != "":
                    self.__rmodal_dialog.fill_text_in_field(
                        element_id="syncQueue", text=synchronization_queue
                    )
                if synchronization_command and synchronization_command != "":
                    self.__rmodal_dialog.fill_text_in_field(
                        element_id="commandToRun", text=synchronization_command
                    )
            self.__rmodal_dialog.click_submit()

        if backup_spool_file:
            self.admin_console.access_tab("Configuration")
            advanced_panel = RPanelInfo(self.admin_console, title="Advanced options")
            advanced_panel.enable_toggle("Backup Spooled File Data")
            self.__rmodal_dialog.click_yes_button()

    @PageService()
    def backup_ibmi_subclient(self,
                              subclient_name: str,
                              backup_type: str = "FULL",
                              backupset_name: str = "defaultBackupSet",
                              is_dr_subclient: bool = False,
                              notify_via_email: bool = False
                              ) -> str:
        """
        Function to run a backup job for an IBMi subclient from command center
           Args:
               subclient_name (str)     : Name of the subclient to trigger backup
               backup_type (str)        : Type of backup
                                            (FULL, INCREMENTAL, REBOOT, RESUME)
               backupset_name (str)     : Name of the backup_set
               is_dr_subclient (bool)   : is it DR subclient backup
               notify_via_email (bool)  : When the job completes, notify me via email
           Raises:
               Exception :
                -- if fails to run the backup
           Returns:
               Job id (str) : Job id for the backup job
        """
        if is_dr_subclient:
            if backup_type.upper() not in ["REBOOT", "RESUME"]:
                raise Exception("Backup Type for DR subclient is invalid...")
        else:
            if backup_type.upper() not in ["FULL", "INCREMENTAL"]:
                raise Exception("Backup Type for non-DR subclient is invalid...")

        self.__switch_backupset(backupset_name)
        self.__rtable.access_action_item(subclient_name, self.admin_console.props['header.backup'])
        self.__rmodal_dialog.select_radio_by_id(radio_id=backup_type.upper())

        # Choose if email notification is needed once the restore job is completed
        if notify_via_email is True:
            self.__checkbox.check(self.__props['label.notifyUserOnJobCompletion'])
        else:
            self.__checkbox.uncheck(self.__props['label.notifyUserOnJobCompletion'])

        self.__rmodal_dialog.click_submit(wait=False)

        return self.admin_console.get_jobid_from_popup()
    
    @PageService()
    def ibmi_restore_subclient(
            self,
            subclient_name: str,
            backupset_name: str = "defaultBackupSet",
            destination_client: Optional[str] = None,
            destination_path: str = None,
            unconditional_overwrite: bool = False,
            selected_files: Optional[list[str]] = None,
            show_deleted_items: Optional[bool] = False,
            deleted_items_path: Optional[list[str]] = None,
            job_id: Optional[str] = None,
            restore_spool_files: bool = False,
            notify_via_email: bool = False
    ) -> str:

        """
        Restore from given IBMi subclient

        Returns:
            Job id(str): Returns the job id for the restore job
        """

        self.admin_console.refresh_page()
        self.__switch_backupset(backupset_name)

        # Restore from IBMi subclient
        if job_id:
            self.admin_console.access_tab("Jobs")
            self.__rtable.access_action_item(job_id, self.admin_console.props['label.globalActions.restore'])
        else:
            self.__rtable.access_action_item(subclient_name, self.admin_console.props['label.globalActions.restore'])

        if show_deleted_items:
            parent_dir = os.path.dirname(deleted_items_path[0])
            self.__rbrowse.select_deleted_items_for_restore(content_path=parent_dir,
                                                            files_folders=deleted_items_path)
        # Browse and select the files to be restored
        paths = os.path.dirname(selected_files[0])
        self.__rbrowse.navigate_path(paths)
        select_files = [os.path.basename(file) for file in selected_files]
        self.__rbrowse.select_files(file_folders=select_files)
        self.__rbrowse.submit_for_restore()

        # Select the destination client if restoring to client other than the source client.
        if destination_client:
            self.__restore_panel.select_restore_destination_client(destination_client)

        # Destination path for OOP restore
        if destination_path:
            self.__restore_panel.add_destination_path_for_restore(destination_path)

        # Choose if restore needs to perform with unconditional overwrite
        if unconditional_overwrite:
            self.__restore_panel.toggle_unconditional_overwrite_checkbox(True)

        # Choose if restore needs to perform along with spool file data
        if restore_spool_files:
            self.__restore_panel.toggle_ibmi_spool_file_data(True)

        # Choose if email notification is needed once the restore job is completed
        if notify_via_email is True:
            self.__checkbox.check(self.__props['label.notifyUserOnJobCompletion'])
        else:
            self.__checkbox.uncheck(self.__props['label.notifyUserOnJobCompletion'])

        return self.__restore_panel.submit_restore()

    @PageService()
    def is_backupset_exists(self, backupset_name):
        """
        Check whether a backupset exists
        Args:
            backuspet_name (str): Name of the backupset
        Returns:
            True if the backupset exists else, Returns False
        """

        backupset_list = []

        if self.__rdropdown.is_dropdown_exists(drop_down_id="Backup sets"):
            backupset_list = self.__rdropdown.get_values_of_drop_down(drop_down_id="Backup sets")

        return backupset_name in backupset_list

    @PageService()
    def action_list_snaps(self, subclient_name: str) -> None:
        """
        Lists the snaps on subclient level with the given name

        Args :
            subclient_name   (str)   --  the name of the subclient whose snaps are to listed
        """
        self.admin_console.refresh_page()
        self.__rtable.access_action_item(subclient_name, self.admin_console.props['action.listSnaps'])

    @PageService()
    def run_offline_backup_copy(
            self,
            subclient_name: str,
            backupset_name: str = "defaultBackupSet",
    ):
        """
        Function to run a offline backupcopy job for a subclient
           Args:
               subclient_name (str): Name of the subclient to backup
               backupset_name (str) : Name of the backup_set
           Raises:
               Exception :
                -- if fails to run the offline backupcopy
        """
        self.__switch_backupset(backupset_name)
        self.__rtable.access_action_item(subclient_name, self.admin_console.props['action.backupCopy'])
        self.admin_console.click_button_using_text("Yes")

    @PageService()
    def mount_multiple_snap(self,
                            jobid: str,
                            mount_path: str,
                            copy_name: str,
                            plan_name: str,
                            clientname: str,
                            subclientname: str,
                            backupsetname: str = "defaultBackupSet",
                            ) -> str:
        """

            Args:
                jobid (str) : jobid
                mount_path(str) : mount path
                copy_name(str) : copy name
                plan_name(str) : plan name
                clientname(str) : client name
                subclientname(str) : subclient name
                backupsetname(str) : backupset name

            Returns:
                Mount_job_id : jobid of multiple mount snaps

            Note: Mounting multiple snaps at Subclient level with same jobid (if subclient has subclientcontent from Different volumes)
        """
        self.__switch_backupset(backupsetname)
        self.action_list_snaps(subclientname)
        mount_job_id = self.__snaputils.mount_multiple_snap(jobid, mount_path, copy_name, plan_name, clientname)
        return mount_job_id

    @PageService()
    def revert_snap(self, job_id: str, subclientname: str, backupsetname: str = "defaultBackupSet") -> str:
        """
        Args:
            job_id(str) : job id of snap
            backupsetname(str) : backupset name
            subclientname(str) : subclient name
        return:
            jobid: jobid of revert operation

        Note: if you have multiple volumes snap with same job id which occurs when subclient content has muliptle volumes
        locations then this revert will Reverts all the volumes.
        """
        self.__switch_backupset(backupsetname)
        self.action_list_snaps(subclientname)
        jobid = self.__snaputils.revert_snap(job_id)
        return jobid

    @PageService()
    def run_inline_backup_copy(self, subclientname: str, backupsetname: str = "defaultBackupSet") -> str:
        """
        Run inline backup copy at subclient

        Args:
               job_id(str) : job id of snap
               backupsetname(str) : backupset name
               subclientname(str) : subclient nam
        Return:
            Snap job id(str): jobid of snap
        """
        self.access_subclient(subclient_name=subclientname, backupset_name=backupsetname)
        self.admin_console.click_button(self.admin_console.props['header.backup'])
        self.__rmodal_dialog.select_radio_by_id("FULL")
        self.__rmodal_dialog.select_checkbox(checkbox_id="backupCopyImmediate")
        self.__rmodal_dialog.select_radio_by_id("backupCopyCurrJob")
        self.__rmodal_dialog.click_submit(wait=False)
        jobid = self.admin_console.get_jobid_from_popup()
        return jobid

    @PageService()
    def action_list_snaps_backupset_level(self) -> None:
        """
        Lists the snaps at backupset level
        """
        self.admin_console.click_button_using_text(self.admin_console.props['action.listSnaps'])

    @PageService()
    def restore_subclient_by_job(self, backupset_name, subclient_name, job_id,
                                 dest_client=None, restore_path=None,
                                 unconditional_overwrite=False, selected_files=None,
                                 impersonate_user=None, **kwargs):
        """ Restores the selected job in subclient

        Args:

             dest_client (str)      : Name of the destination client

             restore_path(str)      : The destination path to which content
                                      should be restored to

             job_id(str)            : job_id of the backup job to be restored

             backupset_name (str)   : backup set name of the client

             subclient_name (str)   : subclient name

             unconditional_overwrite(bool)  : To overwrite unconditionally
                                              on destination path

            selected_files (list)   : list of files or folders to be restored

            Available kwargs Options:
                 ndmp(bool, optional): for ndmp restore set it to True else False.
                 cifs(bool, optional): for cifs restore set it to True else False
                 nfs(bool, optional): for nfs restore set it to True else False
        Returns :
             job_id : job id of the restore

        Raises:
            Exception :
                -- if fails to find the job_id
                -- if fails to run the restore operation
        """
        self.admin_console.access_tab("Subclients")
        self.__switch_backupset(backupset_name)
        self.__rtable.access_action_item(subclient_name, "Backup history")
        rows_count = self.__rtable.get_total_rows_count(job_id)

        if rows_count != 0:
            self.__rtable.access_action_item(job_id, "Restore")

            return self.__fileserver_utils.restore(
                dest_client=dest_client,
                destination_path=restore_path,
                unconditional_overwrite=unconditional_overwrite,
                selected_files=selected_files,
                impersonate_user=impersonate_user,
                **kwargs
            )
        else:
            raise Exception("No such job_id found")


class Jobs:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.admin_console = admin_console

    def action_list_snaps_job(self, jobid):
        """
        list snapshots of a particular job in Jobs Tab
        args:
           jobid : jobid of partiular job
        """
        self.__rtable.access_action_item(jobid, self.admin_console.props['label.listSnapshots'])


class FsAgentAdvanceOptions:
    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.__page = PageContainer(admin_console)
        self.__fileserver_utils = FileServersUtils(admin_console)
        self.__checkbox = Checkbox(admin_console)
        self.__wizard = Wizard(admin_console)

    @PageService()
    def action_list_snaps(self):
        """
        Lists the snaps on client level page action menu
        """
        self.admin_console.access_page_action_menu_by_class("popup")
        self.admin_console.click_button_using_id("LIST SNAPS")

    @PageService()
    def retire_agent(self):
        """Performs retire action for the given server
        """
        self.__page.access_page_action(self.admin_console.props['action.commonAction.retire'])
        self.admin_console.fill_form_by_id("confirmText",
                                           self.admin_console.props['action.commonAction.retire'].upper())
        self.admin_console.click_button_using_text(self.admin_console.props['action.commonAction.retire'])
        return self.admin_console.get_jobid_from_popup()

    @PageService()
    def add_backupset(self, backupset_name,
                      plan_name,
                      content,
                      exclusions,
                      exceptions,
                      remove_plan_content=True,
                      define_own_content=False,
                      mark_as_default_backupset=False,
                      is_nas_backupset=False,
                      impersonate_user=None):
        """
        Method to add a backupset.
        Args:
            backupset_name (str) : Name of the backupset to be created
            plan_name (str) : Name of the plan to be used,
            content (list[str]) : List of Content paths
            exclusions (list[str]) : List of exclusions
            exceptions (list[str]) : List of exceptions
            remove_plan_content (bool) : Should remove existing plan content. Defaults to True
            define_own_content (bool) : Toggle define_own_content. Defaults to False
            mark_as_default_backup (bool) : Should mark as default backupset. Defaults to False
            is_nas_backupset (bool) : True for nas backupset.
        """

        self.admin_console.access_page_action_menu_by_class("popup")
        self.admin_console.click_button(value="Add backup set")
        backupset_modal = RModalDialog(self.admin_console, "Create new backup set")
        backupset_modal.fill_text_in_field("backupSetName", backupset_name)
        backupset_modal.select_dropdown_values("planSelection", [plan_name])
        if define_own_content or is_nas_backupset:
            # We can have plane without content defined. Hence we need to check if the toggle
            # to define own content is present
            # define_own_content should always be True for creating nas backupsets
            if self.__checkbox.is_exists(id="overrideBackupContent") and (not is_nas_backupset):
                self.__wizard.enable_toggle("Define your own backup content")
                # Removing plan content if required. Can also act as override plan content
                if remove_plan_content:
                    self.__fileserver_utils.remove_plan_content()
                    self.__fileserver_utils.remove_plan_exceptions()
                    self.__fileserver_utils.remove_plan_exclusions()
            self.__fileserver_utils.edit_content(add_content=content,
                                                 add_exclusions=exclusions,
                                                 add_exceptions=exceptions,
                                                 impersonate_user=impersonate_user)
        else:
            self.__wizard.disable_toggle("Define your own backup content")
        if mark_as_default_backupset:
            backupset_modal.enable_toggle("isDefaultBackupSet")
        backupset_modal.click_submit()
