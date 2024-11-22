# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Users page on the AdminConsole

Classes:

    Users()

Functions:

        filter_all_users()      -- Method to apply 'All Users' filter
        filter_laptop_users()   -- Method to apply 'Laptop Users' filter
        add_local_user          -- Method to add local user
        add_external_user       -- Method to add external user
        delete_user()           -- delete the user with the specified username
        list_users()            -- Method to return list of users
        is_user_exists()        -- Check if user exists
        open_user()             -- Opens user details page

"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import Toggle
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RTransferOwnership
from Web.AdminConsole.Components.panel import RDropDown, RModalPanel


class Users:
    """
    Class for users page
    """

    def __init__(self, admin_page):
        """
        Method to initiate Users class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__admin_console.load_properties(self)
        self.__table = Rtable(admin_page)
        self.__transfer_owner = RTransferOwnership(admin_page)
        self.__drop_down = RDropDown(admin_page)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__toggle = Toggle(self.__admin_console)
        self.__driver = admin_page.driver
        self.__alert = Alert(self.__admin_console)
        self.wait_time = 8

    @WebAction()
    def __append_username(self, username):
        """
        Method to enter username for external user

        Args:
            username  (str):   the username of the user
        """
        user_name = self.__driver.find_element(By.ID, "externalUserName")
        user_name.send_keys(Keys.END + username)

    @PageService()
    def filter_all_users(self):
        """
        Method to apply 'All Users' filter
        """
        self.__table.view_by_title("All")
        self.__table.select_company("All")
        self.__admin_console.wait_for_completion()

    @PageService()
    def filter_laptop_users(self):
        """
        Method to apply 'Laptop Users' filter
        """
        self.__table.view_by_title("Laptop users")
        self.__admin_console.wait_for_completion()

    @PageService(react_frame=True)
    def __fill_form(self,
                    email,
                    username=None,
                    name=None,
                    company=None,
                    groups=None,
                    system_password=False,
                    password=None,
                    invite_user=False,
                    upn=None):
        """Fills the user creation form"""

        if name:
            self.__admin_console.fill_form_by_id("fullName", name)
        if username:
            self.__admin_console.fill_form_by_id("localUserName", username)
        self.__admin_console.fill_form_by_id("localEmail", email)

        if not system_password:
            self.__toggle.disable(label='Use system generated password')
            self.__admin_console.fill_form_by_id("password", password)
            self.__admin_console.fill_form_by_id("confirmPassword", password)
        else:
            self.__toggle.enable(label='Use system generated password')

        if company:
            self.__drop_down.select_drop_down_values(
                drop_down_id='company',
                values=company,
                case_insensitive_selection=True
            )
        if groups:
            self.__drop_down.select_drop_down_values(
                drop_down_id='userGroups',
                values=groups,
                case_insensitive_selection=True
            )

        if invite_user:
            self.__driver.find_element(By.XPATH, "//*[@id = 'localInviteUser']").click()

        if upn is not None:
            self.__modal_panel.fill_input(id='userPrincipalName', text=upn)

        self.__admin_console.submit_form()
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def add_local_user(self,
                       email,
                       username=None,
                       name=None,
                       company=None,
                       groups=None,
                       system_password=False,
                       password=None,
                       invite_user=False,
                       upn=None):
        """
        Method to create new local user with the specified details

 

        Args:

            email               (str):   the email of the user

            username            (str):   the username of the user

            name                (str):   the display name of the user 

            groups               (str/List) :  one group name or list of user
                                                    groups to attach to

            company             (str):   the company name

            system_password     (bool):         if the system password needs to be used

            password            (str):   the password of the user

            invite_user         (bool):         if the users should be sent an email invite

            upn                 (str):  upn of the user

        Raises:
            Exception:
                if failed to create local user

        """
        self.__table.access_menu_from_dropdown("Single user")
        self.__admin_console.wait_for_completion()
        self.__fill_form(email, username, name, company, groups, system_password, password, invite_user, upn)

    @PageService(react_frame=True)
    def add_external_user(self,
                          external_provider,
                          username,
                          fullname=None,
                          email=None,
                          groups=None):
        """
        Method to create new External/AD user with the specified details

        Args:

            external_provider   (str):   if external user, then the provider name

            username            (str):   the username of the user

            email               (str):   the email of the user

            groups               (list) :  one group name or list of user
                                                    groups to attach to

        Raises:
            Exception:
                if failed to create AD/External user
        """

        self.__table.access_menu_from_dropdown("Single user")
        self.__admin_console.wait_for_completion()
        self.__admin_console.select_radio('external')
        self.__admin_console.wait_for_completion()
        self.__drop_down.select_drop_down_values(
            drop_down_id='provider',
            values=[external_provider],
            case_insensitive_selection=True
        )
        self.__append_username(username)
        
        if fullname:
            self.__admin_console.fill_form_by_id("fullName", email)

        if email:
            self.__admin_console.fill_form_by_id("externalEmail", email)

        if groups:
            self.__drop_down.select_drop_down_values(
                drop_down_id='userGroups',
                values=groups,
                case_insensitive_selection=True
            )

        self.__admin_console.submit_form()
        self.__alert.check_error_message(self.wait_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_user(self,
                    user_name,
                    owner_transfer=None):
        """
        Deletes the specified user

        Args:
            user_name       (str):   username of the user that needs to be deleted
            owner_transfer  (str):   a user or user group to transfer ownership to
        """
        self.filter_all_users()
        self.__table.access_action_item(user_name, 'Delete')
        if owner_transfer:
            self.__transfer_owner.transfer_ownership(owner_transfer)

        self.__admin_console.click_button_using_text('Yes')
        self.__admin_console.wait_for_completion()
        self.__admin_console.log.info('User : %s is deleted successfully', user_name)

    @WebAction()
    def list_users(self, company_name: str = str(), user_type: str = str()):
        """
        Lists all the users

        Args:
            company_name       (str):      To filter/ fetch users of a particular company
            user_type          (str):      To filter/ fetch users of a particular type

        Returns:
            users List
        """
        if company_name:
            self.__table.select_company(company_name)
        if user_type:
            self.__table.view_by_title(user_type)
        return self.__table.get_column_data(column_name='User name', fetch_all= True)

    def is_user_exist(self, user_name):
        """Checks if specified user exists on users page"""
        return self.__table.is_entity_present_in_column( column_name='User name', entity_name=user_name)

    @WebAction()
    def open_user(self, user_name):
        """
        Method to open user details page for given user

        Args:
            user_name   (str)   -   name of user
        """
        self.__table.access_link(user_name)
