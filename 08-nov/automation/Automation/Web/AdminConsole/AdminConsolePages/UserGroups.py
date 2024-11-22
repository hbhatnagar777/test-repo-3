# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
User Groups page on the AdminConsole

Class:

    UserGroups()

Functions:

__select_user_group_type       --  Method to select user group based on type given as input

add_user_group()               --  adds a new user to the admin console

add_external_group()           --  adds an external usergroup

open_user_group()              --  opens the user group with the specified name

action_delete_user_group()     --  deletes the user group with the specified name

active_directory_user_groups() --  Selects AD User Groups

all_user_groups()              --  Selects All User Groups

local_user_groups()            --  Selects Local User Groups

list_user_group()              --  displays the complete info of all the user groups

action_add_users()             --  Method to add users to user group

list_usergroups()              --  Method to return the list of usergroups

is_user_group_exists()         -- Method to check if usergroup exists
"""
import time
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RTransferOwnership, Form
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)


class UserSelection:
    """ Class to support add user action on user group and user group details page """

    def __init__(self, admin_page):
        self.__admin_console = admin_page
        self.__driver = admin_page.driver
        self.__table = Rtable(admin_page, id="userGroups_addusers")

    @WebAction()
    def __get_user_index(self, user):
        """ Method to get index out of displayed user """
        index = 0
        selected = []
        users_list = self.__driver.find_elements(By.XPATH,
                                                 "//tr[contains(@class,'k-master-row')]/td[2]/div")
        if not users_list:
            raise CVWebAutomationException(f"No user found with name {user}")
        elif len(users_list) == 1:
            return index, [user]
        for username in users_list:
            if user == username.text:
                selected.append(user)
                break

            index += 1
        return index, selected

    @WebAction()
    def __select_user_checkbox(self, index):
        """ Method to select user by checking corresponding checkbox using index given """
        xp = "//tr[contains(@class,'k-master-row')]/td[1]/input"
        checkbox = self.__driver.find_elements(By.XPATH, xp)
        checkbox[index].click()

    @PageService()
    def add_users(self, users):
        """
        Adds users to the given group

        Args:
            users (list)  :  list of users to be added to the group

        Returns:
            None
        """

        selected = []
        for user in users:
            self.__admin_console.log.info("adding user with username : %s", user)
            self.__table.search_for(user)
            index, selected_user = self.__get_user_index(user)
            selected.extend(selected_user)
            self.__select_user_checkbox(index)

        x_list = list(set(users) - set(selected))
        self.__admin_console.submit_form()
        if x_list:
            raise Exception("There are no users with the name or the user is already added " + str(x_list))


class UserGroups:
    """ class for user groups page """

    def __init__(self, admin_page):
        """ Initialization method for User Groups Class """

        self.__admin_console = admin_page
        self.__table = Rtable(admin_page)
        self.__transfer_owner = RTransferOwnership(admin_page)
        self.__user_selection = UserSelection(admin_page)
        self.__rdropdown = RDropDown(admin_page)
        self.__form = Form(admin_page)
        self.__driver = admin_page.driver
        self.__alert = Alert(self.__admin_console)
        self.wait_time = 8

    @PageService()
    def add_user_group(self,
                       group_name,
                       description=None,
                       quota=False,
                       quota_limit=None,
                       service_commcells=None):
        """
        Adds a new user group with the given name

        Args:
            group_name (str)         :   Name of the user group to be added

            description (str)        :   Description of the user group

            quota (bool)             :   To enable/disable quota

            quota_limit (int)        :   Size in GB of the group quota limit

            service_commcells (list) :  list of service commcell this user group has to be created on (GCM Feature)
        """
        self.__table.access_toolbar_menu(self.__admin_console.props['pageHeader.addUserGroup'])
        self.__form.fill_text_in_field("name", group_name)
        if description:
            self.__form.fill_text_in_field("description", description)
        if quota:
            self.__form.checkbox.check(id="enforceFSQuota")
            if quota_limit:
                self.__form.fill_text_in_field("quotaLimitInGB", quota_limit)
        else:
            self.__form.checkbox.uncheck(id="enforceFSQuota")

        if service_commcells:
            self.__rdropdown.select_drop_down_values(drop_down_id='GlobConfigInfoCommCellId', values=service_commcells)

        self.__form.click_save_button()
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def add_external_group(self,
                           group_name,
                           local_groups=None,
                           quota=False,
                           quota_limit=None):
        """
        Adds a new AD group with the given name

        Args:
            group_name (str)         :   Name of the external user group to be added

            local_groups (str/list)        :   Local user groups to match permisisons

            quota (bool)             :   To enable/disable quota

            quota_limit (int)        :   Size in GB of the group quota limit
        """
        self.__table.access_toolbar_menu(self.__admin_console.props['pageHeader.addUserGroup'])
        self.__form.select_radio_by_id('external')
        self.__admin_console.wait_for_completion()
        self.__rdropdown.search_and_select(group_name, id='adGroupName')
        time.sleep(5)

        if local_groups:
            if isinstance(local_groups, str):
                local_groups = [local_groups]
            self.__rdropdown.select_drop_down_values(values=local_groups, drop_down_id='localGroups')

        if quota:
            self.__form.toggle.enable(id="enforceFSQuota")
            if quota_limit:
                self.__form.fill_text_in_field("quotaLimitInGB", quota_limit)
        else:
            self.__form.toggle.disable(id="enforceFSQuota")
        self.__form.click_save_button()
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def open_user_group(self, user_group):
        """
        opens the user group with specified name
        """
        self.__table.access_link(user_group)

    @PageService()
    def delete_user_group(self, user_group, owner_transfer= None):
        """
        Deletes the user group with the given name

        Args:
            user_group (str)     :   Name of the user group to be deleted

            owner_transfer (str) :   a user or user group to transfer ownership to before deleting

        Raises:
            Exception:
                if unable to delete user group
        """
        self.__table.access_action_item(user_group, 'Delete')
        if owner_transfer:
            self.__transfer_owner.transfer_ownership(owner_transfer)
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button_using_text('Yes')
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def filter_active_directory_user_groups(self):
        """
        Selects AD User Groups

        Raises:
            Exception:
                if unable to apply filter AD on user groups
        """
        self.__table.view_by_title("Active Directory")
        self.__admin_console.wait_for_completion()

    @PageService()
    def filter_all_user_groups(self):
        """
        Selects All User Groups

        Raises:
            Exception:
                if unable to apply filter All on user groups
        """
        self.__table.view_by_title("All")
        self.__admin_console.wait_for_completion()

    @PageService()
    def filter_local_user_groups(self):
        """
        Selects Local User Groups

        Raises:
            Exception:
                if unable to apply filter local on user groups
        """
        self.__table.view_by_title("Local")
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_users_to_group(self, group_name, users):
        """
        Adds users to the given group

        Args:
            group_name (str)  :  Name of the group to which the users must be added

            users (list)  :  list of users to be added to the group

        Raises:
            Exception:
                if unable to users to given user group
        """
        self.__table.access_action_item(group_name, 'Add users')
        self.__user_selection.add_users(users)

    @PageService()
    def reset_filters(self):
        """Method to reset the filters applied on the page"""
        self.__table.reset_filters()
        
    @WebAction()
    def list_usergroups(self, company_name: str = str(), usergroup_type: str = str()):
        """
        Lists all the user groups

        Args:
            company_name       (str):      To filter/ fetch user groups of a particular company
            usergroup_type     (str):      To filter/ fetch user groups of a particular type

        Returns:
            user groups list
        """
        if company_name:
            self.__table.select_company(company_name)
        if usergroup_type:
            self.__table.view_by_title(usergroup_type)
        return self.__table.get_column_data(column_name='Group name', fetch_all=True)
    
    @PageService()
    def is_user_group_exists(self, group_name):
        """Checks if specified group name exists on user group page"""
        return self.__table.is_entity_present_in_column(column_name='Group name', entity_name=group_name)
