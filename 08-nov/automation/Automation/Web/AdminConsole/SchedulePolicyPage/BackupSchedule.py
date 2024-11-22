# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing schedule-related operations for BackupSchedule class.

BackupSchedule:
    __init__(admin_console)                   --  Initializes the BackupSchedule class.

    edit_policy_name(new_name)                --  Edits the policy name.

    enable_policy()                           --  Enables a policy.

    disable_policy()                          --  Disables a policy.

    get_information()                         --  Retrieves information from the general tab.

    navigate_to_schedules()                   --  Navigates to the schedules tab.

    add_schedule(schedule)                    --  Adds a new schedule.

    delete_schedule(schedule_name)            --  Deletes the schedule.

    navigate_to_associations()                --  Navigates to the associations page of a schedule policy.

    remove_all_associations()                 --  Removes all associations from the page.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.Components.panel import PanelInfo, ModalPanel, DropDown, RPanelInfo, RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RSecurity, RModalDialog, RTags, SLA
from Web.AdminConsole.Components.core import BlackoutWindow
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.content import RBackupContent
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.core import Toggle, TreeView
from Web.AdminConsole.AdminConsolePages.CopyDetails import Configuration, Jobs
from Web.AdminConsole.SchedulePolicyPage.BackupSchedules import BackupSchedules


class BackupSchedule:
    """
    Class for performing operations related to Backup Schedules.
    """

    def __init__(self, admin_console):
        """
        Args:
        admin_console (Object): Admin console object to interact with the UI.
        """

        self.__admin_console = admin_console
        self.__props = self.__admin_console.props
        self.__driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__plans = Plans(self.__admin_console)
        self.__panel_dropdown_obj = DropDown(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__rsecurity = RSecurity(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rtags = RTags(self.__admin_console)
        self.__toggle = Toggle(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rpanel_info = RPanelInfo(self.__admin_console)
        self.__rpo = RPO(self.__admin_console)
        self.__backup_window = BlackoutWindow(self.__admin_console)
        self.__sla = SLA(self.__admin_console)
        self.__treeview = TreeView(self.__admin_console)
        self.navigator = self.__admin_console.navigator

    @PageService()
    def edit_policy_name(self, new_name):
        """
        Edits the policy name.

        Args:
            new_name (str): The new name for the policy.
        """
        self.__page_container.edit_title(new_name)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def enable_policy(self):
        """
        Method to enable a policy.
        """
        self.__rpanel_info.enable_toggle(self.__admin_console.props['label.enabled'])

    @PageService()
    def disable_policy(self):
        """
        Method to disable a policy.
        """
        self.__rpanel_info.disable_toggle(self.__admin_console.props['label.enabled'])

    @PageService()
    def get_general_information(self) -> dict:
        """
        Retrieves information from the general tab.
        eg: {'Type': 'Data protection', 'Enabled': False, 'Agent type': 'All agents'}
        """
        return self.__rpanel_info.get_details()

    @PageService()
    def navigate_to_schedules(self):
        """
        Method to navigate to schedules tab.
        """
        self.__admin_console.access_tile('schedulesInSchedulesPolicy')

    @WebAction()
    def add_schedule(self, schedule: dict):
        """
        Adds a new schedule.

        Args:
            schedule (dict): Dictionary containing schedule details (name, frequency, etc.).
            eg.
            {
                "name" : "SchedulePolicyAutomation",
                "backup_level": "Full",
                "frequency": "Daily"
            }
        """
        self.log.info(f"Adding Schedule Associations schedule name: {schedule['name']}.")
        self.__page_container.click_button(value=self.__admin_console.props['label.add'])
        self.__rmodal_dialog.fill_text_in_field("name", schedule["name"])
        if schedule["backup_level"] in ["Full", "SynthFull", "Cleanup", "Incremental", "Differential",
                                        "TransactionLog"]:
            self.__rmodal_dialog.select_radio_by_id(radio_id=f"bt{schedule['backup_level']}")
        if schedule["frequency"] in ["Daily", "Weekly", "Continuous", "Monthly"]:
            self.__rdropdown.select_drop_down_values(
                values=[schedule["frequency"]], drop_down_id='scheduleFrequency')
            if schedule["frequency"] == "Weekly":
                self.__rdropdown.select_drop_down_values(
                    values=schedule["Days"], drop_down_id='daysOfWeek')
        self.__rmodal_dialog.click_save_button()
        self.__admin_console.check_error_message()
        self.log.info(f"successfully added the schedule.")

    @WebAction()
    def delete_schedule(self, schedule_name) -> str:
        """
        Deletes the schedule.

        Args:
            schedule_name (str): Name of the schedule to be deleted.

        Returns:
            message regarding the operation status.
        """
        self.__table.access_action_item(schedule_name, self.__admin_console.props['action.delete'])
        self.__rmodal_dialog.click_yes_button()
        notification_text = self.__admin_console.get_notification(wait_time=5)
        self.__admin_console.check_error_message()
        return notification_text

    @PageService()
    def navigate_to_associations(self):
        """
        Method to navigate to associations page of a schedule policy.
        """
        self.__admin_console.access_tile('schedulePolicyDetailsAssociations')

    @PageService()
    def remove_all_associations(self):
        """
        Removes all the associations from the page.
        """
        self.__page_container.click_button(value=self.__admin_console.props['label.add'])
        self.__treeview.clear_all_selected()
