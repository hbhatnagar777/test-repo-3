# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
User Details page on the AdminConsole

Class:

    UserDetails()

Functions:

    edit_user()         -- edits the email and group properties of a user with the specified username
    get_user_details()  -- displays the complete info of all the users
    open_user_group()   -- opens the given user group which is associated with this user
    add_membership()    -- method to add users to the given user group
    is_user_enabled()   -- method to check if the user is enabled
    get_usergroups()    -- method to get usergroups selected for user


Class:

    AccessToken()

Functions:
    _go_to_access_token_tab()   -- navigates to access token tab
    create_token()              -- create an access token with specified inputs
    edit_token()                -- edits the access token
    revoke_token()              -- revokes the access token

"""
import datetime

from Web.AdminConsole.Components.alert import Alert
from Web.Common.page_object import PageService
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.dialog import RModalDialog, ModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import CalendarView


class UserDetails:
    """ Class for user details page """

    def __init__(self, admin_page):
        """
        Method to initiate UserDetails class

        Args:
            admin_page  (Object)  :   _Navigator Class object
        """
        self.__driver = admin_page.driver
        self.__admin_console = admin_page
        self.__admin_console.load_properties(self)
        self.__panel_info = RPanelInfo(admin_page, 'User summary')
        self.__drop_down = RDropDown(admin_page)
        self.__page_container = PageContainer(self.__admin_console)
        self.__usergroup_table = Rtable(self.__admin_console, 'User groups')
        self.__alert = Alert(self.__admin_console)
        self.load_time = 5

    @PageService(react_frame=True)
    def edit_user(self,
                  email=None,
                  full_name=None,
                  user_name=None,
                  groups=None,
                  plan=None,
                  enabled=True,
                  password=None,
                  admin_password=None,
                  upn=None):
        """
        Modifies the user with given details

        Args:
            full_name    (str):   full name of the user

            user_name    (str):   the user name of the user

            email        (str):   the email ID of the user

            groups       (list)      :   list of user groups to be associated with the user

            plan         (list)      :   list of plans to be associated with the user

            enabled      (bool)      :   if the user should be enabled/ disabled

            password     (str):   Password to be set for the user

            current_user_password (str) : Password of the logged in user

        Returns:
            None
        """
        self.__panel_info.edit_tile()
        if full_name:
            self.__admin_console.fill_form_by_id("fullName", full_name)
        if user_name:
            self.__admin_console.fill_form_by_id("localUserName", user_name)

        if email:
            self.__admin_console.fill_form_by_id("localEmail", email)

        if upn:
            self.__admin_console.fill_form_by_id("userPrincipalName", upn)

        if password:
            self.__admin_console.fill_form_by_id("password", password)
            self.__admin_console.fill_form_by_id("confirmPassword", password)
            self.__admin_console.fill_form_by_id("currentPassword", admin_password)

        self.__admin_console.submit_form()
        self.__alert.check_error_message(self.load_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

        if groups:
            self.__admin_console.access_tab("User groups")
            self.add_membership(groups)
            self.__admin_console.wait_for_completion()

        if enabled and (not self.is_user_enabled()):
            self.__admin_console.access_page_action_menu("Enable")
            self.__admin_console.click_button_using_text('Yes')
        else:
            self.__admin_console.access_page_action_menu("Disable")
            self.__admin_console.click_button_using_text('Yes')

        self.__alert.check_error_message(self.load_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def get_user_details(self):
        """
        Displays all the details about the user like name, email, user group and plans

        Returns:
            user_details   (dict):  dict of users and their info
        """
        user_details = self.__panel_info.get_details()
        return user_details

    @PageService()
    def open_user_group(self, user_group):
        """
        Opens the user group associated with user

        Args:
            user_group  (str):   the name of the user group to open
        """
        self.__panel_info.open_hyperlink_on_tile(user_group)

    @PageService()
    def add_membership(self, user_groups):
        """
        Method to add user to user groups
        
        Args:
            user_groups (list):     list of user groups to add the user to
        """
        self.__admin_console.click_button_using_text('Add membership')
        self.__admin_console.wait_for_completion()
        self.__drop_down.select_drop_down_values(
            drop_down_id='userGroups',
            values=user_groups,
            case_insensitive_selection=True
        )
        self.__admin_console.submit_form()
        self.__alert.check_error_message(self.load_time)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def is_user_enabled(self):
        """Method to check if user is enabled"""
        return self.__page_container.check_if_page_action_item_exists("Disable")

    @PageService()
    def get_usergroups(self):
        """
        Page service to get the user groups given user is associated to

        Returns:
            list[str]    -   list of usergroup names
        """
        return self.__usergroup_table.get_column_data('Group name')


class AccessToken:
    """ class to help operation related to Access Token in Manage>Security>Users>Access Tokens"""
    def __init__(self, admin_console, username):
        """
        Method to initiate AccessToken class

        Args:
            admin_console  (Object)  :   AdminConsole Class object
        """
        self.username = username
        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__panel_info = RPanelInfo(admin_console)
        self.__r_modal_dialog = RModalDialog(self.__admin_console)
        self.__modal_dialog = ModalDialog(self.__admin_console)
        self.__r_table = Rtable(self.__admin_console)
        self.__cv = CalendarView(self.__admin_console)

        self.__navigator = self.__admin_console.navigator

    @PageService()
    def _go_to_access_token_tab(self):
        """navigates to access token tab of the user logged in"""
        self.__navigator.navigate_to_users()
        self.__r_table.access_link(self.username)
        self.__admin_console.access_tab("Access tokens")

    @PageService()
    def create_token(self, token_name=None, timedict=None, datedict=None, scope=None):
        """ Creates a new access token

         Args:
             token_name        (str)   --   Name of the token
             timedict          (dict)  --   Time value as dictionary
                                            Eg, {
                                                    'hour': 09,
                                                    'minute': 19,
                                                    'session': 'AM'
                                                }
             datedict          (dict)  --   Date value as dictionary
                                            Eg,
                                            {
                                                'year': 1999,
                                                'month': "March",
                                                'day': 21,
                                            }
             scope             (list)   --  Specify scope as list of API end points.
                                            Ex: ["/client", "/add"], ["/all"]

        Returns:
            token              (str)    -- value of the access token created
            token_name         (str)    -- name of the access token created
            timedict           (dict)   -- Time value as dictionary
                                        Eg, {
                                                'hour': 09,
                                                'minute': 19,
                                                'session': 'AM'
                                            }
        """

        self._go_to_access_token_tab()
        if token_name is None:
            token_name = "token_" + ('{date:%d-%m-%Y_%H_%M_%S}'.format(date=datetime.datetime.now()))

        if scope is None:
            scope = ["/all"]
        scope = ("\n".join(scope)).strip()
        if not self.__panel_info.check_if_button_exists("Add token"):
            raise CVWebAutomationException("Add token button does not exists")
        self.__panel_info.click_button("Add token")
        self.__r_modal_dialog.fill_text_in_field("tokenName", token_name)
        self.__r_modal_dialog.click_button_on_dialog(id="cv-calendar-button-renewableUntilTimestamp")
        if datedict:
            self.__cv.select_date(datedict, click_today=False)
        if timedict:
            self.__cv.select_time(timedict)
        self.__admin_console.click_button_using_text("Set")
        if scope.strip().lower() != "/all":
            self.__r_modal_dialog.select_dropdown_values("tokenTypesDropdown", ["Custom"])
            self.__r_modal_dialog.fill_text_in_field("customUrls", scope)

        self.__r_modal_dialog.click_submit()
        self.__admin_console.check_error_message()
        token_message = self.__modal_dialog.get_text().strip()
        self.__r_modal_dialog.click_close()
        if 'This user is disabled for AccessToken API request' in token_message:
            raise Exception('This user is disabled for AccessToken API request')
        token = token_message.split("\n")[-1]
        return token, token_name, timedict

    @PageService()
    def edit_token(self, current_token_name, field, value):
        """ Edits already created Access Token

         Args:
                     field        (str)   -- Field can be Name or Date or Time or Scope
                     value        (str)   -- For field Name
                                  (dict)  -- For field Date or Time
                                  (list)  -- Specify scope as list of API end points.
                                             Ex: ["/client", "/add"], ["all"]
             current_token_name   (str)   -- Name of the token to be edited

        Returns:
            None

        Raises:
            Exception("Field type dict expected, got type %s" % type(value))
            Raises above exception if the value type is other than expected.
        """
        self._go_to_access_token_tab()
        self.__r_table.access_action_item(current_token_name, "Edit")
        if field.strip().lower() == 'name':
            self.__r_modal_dialog.fill_text_in_field("tokenName", value)

        elif field.strip().lower() == 'date':
            if type(value) == dict:
                self.__r_modal_dialog.click_button_on_dialog("Expiry date", preceding_label=True)
                self.__cv.select_date(value)
                self.__admin_console.click_button_using_text("Set")
            else:
                raise Exception("Value type dict expected, got type %s" % type(value))
        elif field.strip().lower() == 'time':
            if type(value) == dict:
                self.__r_modal_dialog.click_button_on_dialog("Expiry date", preceding_label=True)
                self.__cv.select_time(value)
                self.__admin_console.click_button_using_text("Set")
            else:
                raise Exception("Field type dict expected, got type %s" % type(value))

        elif field.strip().lower() == "scope":
            if type(value) == list:
                value = ("\n".join(value)).strip()
                if value.strip().lower() != "/all":
                    self.__r_modal_dialog.select_dropdown_values("tokenTypesDropdown", ["Custom"])
                    self.__r_modal_dialog.fill_text_in_field("customUrls", value)
            else:
                raise Exception("Field type list expected, got type %s" % type(value))

        self.__r_modal_dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def revoke_token(self, token_name):
        """ Revokes an access token

                 Args:
                     token_name        (str)   -- Name of the token to be revoked
        """
        self._go_to_access_token_tab()
        self.__r_table.access_action_item(token_name, "Revoke")
        self.__admin_console.click_button_using_text("Yes")
        self.__admin_console.check_error_message()
