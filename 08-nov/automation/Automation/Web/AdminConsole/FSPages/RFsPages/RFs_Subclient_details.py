# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# When editing this file kindly either of the following people for review : Aravind Putcha , Rohan Prasad

"""
This module provides the function or operations that can be performed on
all the FS Subclient details page from Command Center.

"""

from selenium.webdriver.common.by import By
from Web.AdminConsole.AdminConsolePages.agents import Agents
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import ModalPanel, RModalPanel, RPanelInfo, RDropDown
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils, RRestorePanel
import os


class SubclientOverview:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.__rbrowse = RBrowse(admin_console)
        self.__driver = admin_console.driver
        self.__restore_panel = RRestorePanel(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.admin_console = admin_console
        self.__wizard = Wizard(admin_console)
        self.fsutils= FileServersUtils(admin_console)
    
    @PageService()
    def assign_plan(self, plan_name: str):
        """
        Change the plan from fssubclientdetails page

        Args:
            plan_name (str) : Name of the plan to be assigned
        """

        protection_summary_panel = RPanelInfo(self.admin_console, "Protection summary")

        protection_summary_panel.edit_tile_entity("Plan")

        plan_modal = RModalDialog(self.admin_console, "Plan")

        plan_modal.select_dropdown_values("subclientPlanSelection", [plan_name])

        plan_modal.click_submit()

    def enable_blocklevel(self, enable_blocklevel):
        """
            method to enable/Disable  blocklevel backup option
            Args:
                enable_blocklevel   (bool)     --  True/False

        Raises:
                Exception: When the email receiver list is emp

        """
        self.__rpanel = RPanelInfo(self.admin_console,title='Block level backup')
        if enable_blocklevel:
            self.__rpanel.enable_toggle('Block level backup')
        else:
            self.__rpanel.disable_toggle('Block level backup')

    @PageService()
    def edit_content(
        self, 
        add_content: list[str] = None, 
        del_content: list[str] = None,
        add_exclusions: list[str] = None, 
        del_exclusions: list[str] = None,
        add_exceptions: list[str] = None, 
        del_exceptions: list[str] = None,
        browse: bool = False
    ):
        """
        Method to edit subclient content.
        Args:
            add_content: List of strings to add backup content
            del_content: List of strings to remove from backup content
            add_exclusions: List of strings to add exclusions
            del_exclusions: List of strings to remove from exclusions
            add_exceptions: List of strings to add exceptions
            del_exceptions: List of strings to remove from exceptions
            browse : If content has to e selected using browse
        """

        rpanel = RPanelInfo(self.admin_console)
        
        rpanel.edit_tile(tile_label="Content") 

        self.admin_console.wait_for_completion()       

        self.fsutils.edit_content(add_content=add_content,
                                  del_content=del_content,
                                  add_exclusions=add_exclusions,
                                  del_exclusions=del_exclusions,
                                  add_exceptions=add_exceptions,
                                  del_exceptions=del_exceptions,
                                  browse=browse)

        self.__rmodal_dialog.click_submit()

    @PageService()
    def restore_from_calender(self,
                              calender,
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
        
        self.fsutils.restore_from_calender(calender, measure_time=measure_time)


        return self.fsutils.restore(
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
    def edit_access_nodes(self, access_nodes: list[str], access_node_type: str=None):
        """
        Method to change the access nodes for a NAS Subclient
        Args:
            access_node_type (str) : windows / linux
            access_nodes : List of strings each representing a node
        """

        access_node_panel = RPanelInfo(self.admin_console)
        access_node_panel.edit_tile(tile_label="Access nodes") 

        self.admin_console.wait_for_completion()

        access_node_dialog = RModalDialog(self.admin_console, "Edit access nodes")

        if access_node_type:
            if access_node_type.lower() == "windows":
                access_node_dialog.select_radio_by_id("windows")
            else:
                access_node_dialog.select_radio_by_id("linux")
        
        self.admin_console.wait_for_completion()

        access_node_dialog.select_dropdown_values(values=access_nodes,
                                                  drop_down_id="accessNodeDropdown")
        
        access_node_dialog.click_submit()

class Configuration:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.admin_console = admin_console


class FsSubclientAdvanceOptions:
    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.__rmodal_dialog = RModalDialog(admin_console)


    @PageService()
    def action_list_snaps(self):
        """
        Lists the snaps on client level page action menu
        """
        self.admin_console.access_page_action_menu_by_class("popup")
        self.admin_console.click_button_using_text(self.admin_console.props['action.listSnaps'])


    @PageService()
    def click_on_backup_history(self):
        """
        click on Backup history button in subclient details page
        """
        self.admin_console.click_button_using_text(self.admin_console.props['label.BackupHistory'])
    
    @PageService()
    def backup(self, backup_type: enumerate):
        """
        Backup subclient from subclient details page

        Args:
            backup_type: Backup.BackupType.FULL/INCR/SYNTH
        """
        
        self.admin_console.click_button_using_text(self.admin_console.props['header.backup'])

        self.admin_console.wait_for_completion()

        self.__rmodal_dialog.select_radio_by_id(radio_id=backup_type.value.upper())
        self.__rmodal_dialog.click_submit(wait=False)
        return self.admin_console.get_jobid_from_popup()

    @PageService()
    def delete_subclient(self):
        """
        Method to delete subclient from subclient details page
        """

        self.admin_console.access_page_action_menu_by_class("popup")
        self.admin_console.click_button_using_text(self.admin_console.props['label.globalActions.delete'])
        self.admin_console.wait_for_completion()

        delete_subclient_modal = RModalDialog(self.admin_console, "Delete subclient")

        delete_subclient_modal.fill_text_in_field("confirmText", "DELETE")

        delete_subclient_modal.click_submit()
