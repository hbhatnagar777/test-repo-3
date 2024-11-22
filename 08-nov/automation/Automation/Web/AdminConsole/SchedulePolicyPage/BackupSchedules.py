# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Backup Schedules Listing page on the AdminConsole

Class:

    BackupSchedules()

Functions:

    list_backup_schedules()                      --  lists all the schedule policy present in the page.
    delete_backup_schedule()                     --  Deletes a backup schedule.
    select_backup_schedule()                     --  Enters the details page for a backup schedule.
    create_backup_schedules()                    --  Created a Backup Schedule of type data protection.

"""


from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RDropDown, RPanelInfo, RModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog, RTags
from Web.AdminConsole.Components.content import RBackupContent
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.core import Toggle, Checkbox, BlackoutWindow, CalendarView, TreeView
from datetime import datetime
import time


class BackupSchedules:
    """
        Class for performing operations on backup policy listing page.
    """
    def __init__(self, admin_console: AdminConsole):
        """
        Method to initiate Backup Schedules class

        Args:
            admin_console   (Object) :   admin console object
        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__rmodal_panel = RModalPanel(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__navigator = self.__admin_console.navigator
        self.__rbackup_content = RBackupContent(self.__admin_console)
        self.__checkbox = Checkbox(self.__admin_console)
        self.__toggle = Toggle(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__rwizard = Wizard(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__calendar = CalendarView(self.__admin_console)
        self.__backup_window = BlackoutWindow(self.__admin_console)
        self.__rtags = RTags(self.__admin_console)
        self.__tree_view = TreeView(self.__admin_console)

    @PageService()
    def list_backup_schedules(self) -> list:
        """"
        Returns:
            The list of Backup Schedules Present
        """
        return self.__table.get_column_data(column_name='Name', fetch_all=True)

    @PageService()
    def delete_backup_schedule(self, policyName: str) -> str:
        """"
        Returns:
            Notification regarding the deletion operation.
        """
        self.__table.access_action_item(policyName, self.__admin_console.props['action.delete'])
        self.__rmodal_dialog.click_yes_button()
        notification_text = self.__admin_console.get_notification(wait_time=5)
        self.__admin_console.check_error_message()
        return notification_text

    @PageService()
    def select_backup_schedule(self, policyName):
        """
        Enters the Schedule policy Details page.
        Args:
            policyName (str) : name of the policy.
        """
        self.__admin_console.navigator.navigate_to_backup_schedules()
        self.__table.access_link(policyName)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def create_backup_schedules(
            self,
            policyName: str,
            schedules: list = None,
            agentType: list = None,
            associations: list = None
    ):
        """
        Creates a Backup Schedule of type Data Protection.
        Params >>>
        PolicyName (str) : Name of the policy you want.
        Schedules (list of dicts) : Schedules you want to add in your policy.
            eg:[{
                "name" : "SchedulePolicyAutomation",
                "backup_level": "Full",
                "frequency": "Daily"
            }]
        agentType (list) : Agent type names.
            eg: ["Active Directory", "Sharepoint"]
        associations (list) : list of associated server/ server group you want to add.
            eg: ["Servers", "Server groups"]
        """
        self.log.info("Adding Name and selecting Agent type for the Policy")
        self.__table.access_toolbar_menu("Add")
        self.__admin_console.fill_form_by_name("schedulePolicyName", policyName)

        if agentType:
            self.__tree_view.select_items(agentType)
        else:
            self.__tree_view.select_items(["Files"])
        self.log.info("Name and Agent Type configured successfully.")
        self.__wizard.click_next()
        # self.__admin_console.click_button(value="Next")

        for schedule in schedules:
            self.log.info(f"Adding Schedule Associations schedule name: {schedule['name']}.")
            self.__wizard.click_add_icon()
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
        self.log.info("Added all the schedules successfully.")
        self.__wizard.click_next()
        self.__admin_console.check_error_message()

        self.log.info("Adding Server Associations.")
        self.__table.access_toolbar_menu(self.__admin_console.props['Add'])
        if associations:
            self.__tree_view.select_items(associations)
        else:
            self.__tree_view.select_items(["Servers"])
        self.__admin_console.click_button(id="Save")
        self.__rwizard.click_submit()
        self.__admin_console.check_error_message()
        time.sleep(10)
        self.log.info("Successfully created the schedule policy.")
