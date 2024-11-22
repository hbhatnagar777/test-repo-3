# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
User Group details page on the AdminConsole

Class:

 UserGroupDetails()

Functions:

edit_user_group()         -- edit the user group details
remove_associated_external_groups()  -- Removes external groups
add_users()               -- Adds users to the user group
remove_users()            -- Removes users from the group
list_users()              -- Lists all the users associated with the group

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.AdminConsolePages.UserGroups import UserSelection
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog


class UserGroupDetails:
    """
    Class for User Group Details
    """
    def __init__(self, admin_page):
        """Initialization method for UserGroupDetails Class"""

        self.__admin_console = admin_page
        self.__user_selection = UserSelection(admin_page)
        self.__driver = admin_page.driver
        self.__panel_info = RPanelInfo(admin_page)
        self.__table = Rtable(self.__admin_console)
        self.__drop_down = RDropDown(admin_page)
        self.__dialog = RModalDialog(admin_page)
        self.__page_container = PageContainer(admin_page)
        self.__alert = Alert(self.__admin_console)
        self.wait_time = 8

    @WebAction()
    def __click_remove(self, user):
        """ Method to click on remove option for given user in user group details page"""
        self.__table.access_action_item(user, "Remove")
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __check_checkbox(self, id):
        """select a checkbox"""
        checkbox = self.__driver.find_element(By.XPATH, f"//input[@id='{id}']")
        if not checkbox.is_selected():
            checkbox_element = checkbox.find_element(By.XPATH, "./ancestor::label/span")
            checkbox_element.click()

    @WebAction()
    def __uncheck_checkbox(self, id):
        """unselect a checkbox"""
        checkbox = self.__driver.find_element(By.XPATH, f"//input[@id='{id}']")
        if checkbox.is_selected():
            checkbox_element = checkbox.find_element(By.XPATH, "./ancestor::label/span")
            checkbox_element.click()

    @WebAction()
    def __enable_toggle(self, id):
        """Enables a toggle"""
        toggle = self.__driver.find_element(By.XPATH, f"//input[@id='{id}']")
        if not toggle.is_selected():
            toggle_element = toggle.find_element(By.XPATH, "./ancestor::label/span")
            toggle_element.click()

    @WebAction()
    def __disable_toggle(self, id):
        """Disables a toggle"""
        toggle = self.__driver.find_element(By.XPATH, f"//input[@id='{id}']")
        if toggle.is_selected():
            toggle_element = toggle.find_element(By.XPATH, "./ancestor::label/span")
            toggle_element.click()

    @PageService()
    def edit_user_group(self,
                        group_name=None,
                        description=None,
                        plan=None,
                        quota=False,
                        group_enabled=True,
                        laptop_admins=False,
                        quota_limit=None,
                        associated_external_groups=None):
        """
        Method to edit the user group details

        Args:
            quota_limit   (int)   :  the size in GB of the group quota

            group_name    (str)   :  the new name of the group

            plan         (list)  :  list of plans to be associated with user group

            group_enabled (bool)  :  enable / disable the group

            description   (str)   :  description of the user group

            quota         (bool)  :  enable / disable quota

            laptop_admins (bool)  :  enable / disable device activation

            associated_external_groups (list) : list of external groups to be associated

        Raises:
            Exception:
                if unable to edit user group
        """

        self.__panel_info.edit_tile()

        if group_name:
            self.__admin_console.fill_form_by_id("name", group_name)

        if description:
            self.__admin_console.fill_form_by_id("description", description)

        quote_toggle = self.__driver.find_element(By.XPATH, "//*[@id='enforceFSQuota']/ancestor::label/span")
        if quota:
            self.__enable_toggle("enforceFSQuota")
            if quota_limit:
                self.__admin_console.fill_form_by_id("quotaLimitInGB", quota_limit)

        else:
            self.__disable_toggle("enforceFSQuota")

        if group_enabled:
            self.__check_checkbox("enabled")
        else:
            self.__uncheck_checkbox("enabled")

        if laptop_admins:
            self.__check_checkbox("laptopAdmins")
        else:
            self.__uncheck_checkbox("laptopAdmins")

        if associated_external_groups:
            self.__drop_down.select_drop_down_values(drop_down_id="externalGroups", values=associated_external_groups)    
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form()
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def remove_associated_external_groups(self, associated_external_groups):
        """
        Removes associated external groups

        Args:
            associated_external_groups (list)   :   List of external groups to be removed

        Raises:
            Exception:
                if unable to remove external group
        """
        self.__panel_info.edit_tile()
        self.__drop_down.deselect_drop_down_values(drop_down_id="externalGroups", values=associated_external_groups)
        self.__admin_console.submit_form()
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService(react_frame=True)
    def add_users_to_group(self, users):
        """
        Adds new users to the group

        Args:
            users (list)   :   List of users to be added

        Raises:
            Exception:
                if unable to add user
        """
        self.__page_container.select_tab('Users')
        self.__admin_console.click_button_using_text("Add users")
        self.__admin_console.wait_for_completion()
        self.__user_selection.add_users(users)
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def remove_users_from_group(self, users):
        """
        Removes users from the group

        Args:
            users (list)  :  List of users to be removed
        """
        self.__page_container.select_tab('Users')
        self.__admin_console.wait_for_completion()
        for user in users:
            self.__table.search_for(user)
            self.__click_remove(user)
            self.__dialog.click_submit()
            self.__admin_console.check_error_message()

    @PageService()
    def get_user_group_details(self):
        """
        Fetches and displays all the details about the user group like name, description,
        enabled, plans and Username of users etc.

        Returns:
            group_details (dict) :  Dictionary of user group details

        Raises:
            Exception:
                if unable to get user group details
        """
        group_details = self.__panel_info.get_details()
        return group_details

    @PageService(react_frame=True)
    def list_users(self):
        """Lists details of all the users associated with the group

        Returns:
            users (list)  --  List of dictionaries with details for all users associated with the group

        Raises:
            Exception:
                if unable to list users
        """
        self.__page_container.select_tab('Users')
        self.__admin_console.wait_for_completion()
        users = self.__table.get_column_data("User name")
        return users
