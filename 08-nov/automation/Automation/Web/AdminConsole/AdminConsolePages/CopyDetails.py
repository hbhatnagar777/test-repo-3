# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Copydetails page on the AdminConsole

Steps to Reach Copydetails Page.
plans -> select plan -> backup destinations tab -> under back destinations table select any copy -> [Copy Details Page]

Classes:
    Configuration             : contains methods for all the operations under Configuration tab
    Jobs                      : contains methods for all the operations under jobs  tab
    CopyDetailsAdvanceOptions : Contains methods for Main Menu Bar Buttons by excluding configuration and jobs tabs
                                operations.

Functions:
    Configuration:  # add methods here which are under configuration tab
    Jobs:          # add methods here which are under Jobs tab
    CopyDetailsAdvanceOptions:
          action_list_snaps_copy_level() :  click list snapshots Button on Main Menu Bar of Copy details Page

"""
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.dialog import RSecurity, RModalDialog
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVWebAutomationException


class Configuration:
    """ Class for the Configuration tab in Copydetails page """

    def __init__(self, admin_console):
        """
        Method to initiate Configuration class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.admin_console = admin_console
        self.__rmodal_dialog = RModalDialog(self.admin_console)
        self._props = self.admin_console.props

    @PageService()
    def change_source_for_backupcopy(self):
        """
           This Method will check whether toggle is enabled or not. if not enabled, it will Enable change
           source for backupcopy toggle button
           Raise Exception:
            if toggle is already enabled it will raise exception else it will enable the toggle button
        """
        temp_panel = RPanelInfo(self.admin_console, title="Snapshot management")
        if temp_panel.get_toggle_element(label="Change source for backup copy"):
            if temp_panel.is_toggle_enabled(label="Change source for backup copy"):
                raise Exception(f"Failed: Toggle is already enabled for this copy, Disable it Manually")
            else:
                temp_panel.enable_toggle("Change source for backup copy")
        self.__rmodal_dialog.click_yes_button()

    @WebAction()    
    def enable_compliance_lock(self) -> None:
        """
        Enable Compliance Lock for the Copy
        """
        panel_info = RPanelInfo(self.admin_console, self._props['label.general'])
        element = panel_info.get_toggle_element(self._props['label.Compliancelock'])
        if panel_info.is_toggle_enabled(element):
            self.admin_console.log.info("Compliance Lock option is already enabled")
        else:
            panel_info.enable_toggle(self._props['label.Compliancelock'])
            self.admin_console.click_button(self._props['label.yes'])
            if not panel_info.is_toggle_enabled(element):
                raise CVWebAutomationException("failed to enable ComplianceLock")
        
    @WebAction()    
    def disable_compliance_lock(self) -> None:
        """
        Disable Compliance Lock for the Copy
        """
        panel_info = RPanelInfo(self.admin_console, self._props['label.general'])
        try:
            panel_info.disable_toggle(self._props['label.Compliancelock'])
        except Exception as e:
            self.admin_console.log.info("Disable Compliance Lock option failed with error: {}".format(e))
        element = panel_info.get_toggle_element(self._props['label.Compliancelock'])
        if not panel_info.is_toggle_enabled(element):
            raise CVWebAutomationException("Compliance Lock option is disabled, its a bug!")
        else:
            self.admin_console.log.info("Compliance Lock option is still enabled, we are good!")

    @WebAction()
    def enable_immutable_snap(self) -> None:
        """
        Enable Immutable snap for the Copy
        """
        panel_info = RPanelInfo(self.admin_console, self._props['label.general'])
        element = panel_info.get_toggle_element(self._props['label.ImmutableSnapshot'])
        if panel_info.is_toggle_enabled(element):
            self.admin_console.log.info("Immutable Snap option is already enabled")
        else:
            panel_info.enable_toggle(self._props['label.ImmutableSnapshot'])
            self.admin_console.click_button(self._props['label.yes'])
            if not panel_info.is_toggle_enabled(element):
                raise CVWebAutomationException("failed to enable Immutable Snapshot")
        
    @WebAction()    
    def disable_immutable_snap(self) -> None:
        """
        Disable immutable snap for the Copy
        """
        panel_info = RPanelInfo(self.admin_console, self._props['label.general'])
        try:
            panel_info.disable_toggle(self._props['label.ImmutableSnapshot'])
        except Exception as e:
            self.admin_console.log.info("Disable Immutable Snap option failed with error: {}".format(e))
        element = panel_info.get_toggle_element(self._props['label.ImmutableSnapshot'])
        if not panel_info.is_toggle_enabled(element):
            raise CVWebAutomationException("Immutable Snap option is disabled, its a bug!")
        else:
            self.admin_console.log.info("Immutable snap option is still enabled, we are good!")

class Jobs:
    """ Class for the Jobs tab in Copydetails page """
    def __init__(self, admin_console):
        """
        Method to initiate Jobs class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.admin_console = admin_console
        self.__rmodal_dialog = RModalDialog(self.admin_console)
        self.rtable = Rtable(self.admin_console)

    # add methods here which are under Jobs tab
    @WebAction()    
    def delete_job_on_locked_copy(self, jobid) -> None:
        """
        Method to verify delete job on the Compliance/Immutable locked Copy
        Args:
            jobid (str) : Job ID
    
        """
        self.rtable.search_for(jobid)
        self.rtable.apply_filter_over_column(column_name="Job ID", filter_term=jobid)
        self.rtable.select_all_rows()
        self.rtable.access_toolbar_menu("Delete job")
        self.__rmodal_dialog.type_text_and_delete(text_val="Delete", checkbox_id="onReviewConfirmCheck", wait=False)
        self.__rmodal_dialog.click_submit(wait=False)
        notification_text = self.admin_console.get_notification(wait_time=5)
        return notification_text


class CopyDetailsAdvanceOptions:

    """
     Class for the CopyDetailsAdvanceOptions
     Contains methods for Main Menu Bar Buttons

     """

    def __init__(self, admin_console):
        """
        Method to initiate CopyDetailsAdvanceOptions class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.admin_console = admin_console

    @PageService()
    def action_list_snaps_copy_level(self) -> None:

        """
        click list snapshots Button on Main Menu Bar of Copy details Page
        """
        self.admin_console.click_button_using_text(self.admin_console.props['action.listSnaps'])