# -*- coding: utf-8 -*-s

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
CredentialManager page on the AdminConsole

Class:
    CredentialManager()

Functions:

add_credential()                            -- adds a new credential on the credential manager page
edit_credential()                           -- edits the credential
update_security()                           -- Adds security association to the given name
action_remove_credential()                  -- Deletes the credential
extract_edit_pane_displayed_details()       -- Displays details on the edit pane
clear_automation_credentials()              -- Clears all credentials starting with the prefix - "automation-credential-<timestamp>"
"""

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown, RModalPanel, RPanelInfo
from Web.Common.exceptions import CVException
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.dialog import RModalDialog
from datetime import datetime, timedelta
from AutomationUtils import logger


class CredentialManager:
    """
    This class provides the function or operations that can be performed on the CredentialManager
     page on the AdminConsole
    """

    def __init__(self, admin_console):

        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.__rmodalpanel = RModalPanel(admin_console)
        self.__rtable = Rtable(admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rmodaldialog = RModalDialog(self.__admin_console)
        self.__panel_info = RPanelInfo(self.__admin_console, 'Security')
        self.log = logger.get_log()
        self.database_types = ['DB2', 'Informix', 'MySQL', 'Oracle', 'PostgreSQL', 'SAP HANA',
                               'SAP MAXDB', 'SAP Oracle', 'SQL Server Account', 'Sybase']

    @PageService()
    def add_credential(self,
                       account_type,
                       credential_name,
                       username,
                       password,
                       description=None,
                       vendor_type=None,
                       authentication_type=None,
                       database_type=None):
        """
        Adds a new credential to the commcell

        Args:
            account_type (str) : the account type of the credential

            credential_name (str) : the name of the domain

            username (str)        : the username of the domain

            password (str)        : the password of the domain


            description (str)     : description of the credential


            vendor_type (str)     : Vendor Type ( only applicable for account_type='Cloud Account')

            authentication_type ( str):  Authentication type for Cloud App credentials

            database_type   (str)   : Database Type (only applicable for account_type='Database Account')
                                      Accepted values ['DB2', 'Informix', 'MySQL', 'Oracle', 'PostgreSQL', 'SAP HANA',
                                      'SAP MAXDB', 'SAP Oracle', 'SQL Server Account', 'Sybase']

        """
        self.__rtable.access_toolbar_menu(self.__admin_console.props['label.add'])
        self.__rdropdown.select_drop_down_values(values=[account_type], drop_down_id='accountType')
        if account_type == "Cloud Account":
            if not authentication_type:
                raise CVException(
                    "authentication_type is a required argument for account_type='Cloud Account'")
            if not vendor_type:
                raise CVException(
                    "vendor_type is a required argument for account_type='Cloud Account'")
            self.__rmodaldialog.select_dropdown_values(values=[vendor_type], drop_down_id='vendorTypeList')
            self.__rmodaldialog.select_dropdown_values(values=[authentication_type],
                                                       drop_down_id='authenticationTypeList')

        if account_type == "Database Account":
            if database_type in self.database_types:
                self.__rdropdown.select_drop_down_values(values=[database_type], drop_down_id='databaseCredentialType')
            else:
                raise CVException(f"Invalid database type: {database_type}\n"
                                  f"Accepted database types: {self.database_types}")
        self.__rmodalpanel.fill_input(label='Credential name', text=credential_name, id='name')
        self.__rmodalpanel.fill_input(label='userAccount', text=username, id='userAccount')
        self.__rmodalpanel.fill_input(label='password', text=password, id='password')

        if description:
            self.__rmodalpanel.fill_input(text=description, id="description")

        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def edit_credential(self,
                        credential_name,
                        new_credential_name=None,
                        username=None,
                        password=None,
                        description=None):

        """
        Edits the credential with the given name

        Args:
            credential_name (string)     : the name of the credential which has to
                                                   be edited

            new_credential_name (string) : the new credential name,
                                                  pass None to leave it unchanged

            username (string)            : credential username

            password (string)            : credential password, pass None to leave
                                                  credential password unchanged


            description (str)     : description of the credential

        Returns:
            None
        """

        self.__rtable.access_action_item(credential_name, "Edit")

        if new_credential_name is not None:
            self.__rmodaldialog.fill_text_in_field("name", new_credential_name)

        if username is not None:
            self.__rmodaldialog.fill_text_in_field("userAccount", username)

        if password is not None:
            self.__rmodaldialog.fill_text_in_field("password", password)

        if description is not None:
            self.__rmodaldialog.fill_text_in_field("description", description)

        self.__rmodaldialog.click_submit()
        self.__admin_console.check_error_message()

    def update_security(self, credential_name, user_or_group, role):
        """
        Adds security association with the given name

        Args:
            credential_name (string)     : the name of the credential which has to
                                                   be added security association

            user_or_group (list)         : list of user/groups to be associated with the credential

            role (str)                   : role to be associated with the user_or_group

        Returns:
            None
        """
        self.__rtable.access_action_item(credential_name, "Update security")
        self.__panel_info.edit_tile()

        for entity in user_or_group:
            self.__rmodalpanel.search_and_select(entity, id="security_usersAndGroupsList")
            self.__rdropdown.select_drop_down_values(drop_down_id='rolesList', values=[role])
            self.__rmodaldialog.click_add()

        self.__rmodalpanel.save()
        self.__rmodaldialog.click_cancel()
        self.__admin_console.check_error_message()

    @PageService()
    def action_remove_credential(self, credential_name):
        """
        Deletes the credential with the given name

        Args:
            credential_name (str)    : Name of the credential which has to
                                                be deleted
        Returns:
            None
        """
        self.__rtable.access_action_item(credential_name, "Delete")
        self.__admin_console.click_button('Yes')

    @PageService()
    def extract_edit_pane_displayed_details(self, credential_name):
        """
        Method to extract and returns details displayed on the edit pane

        Args:
            credential_name(str) : Name of the credential whose details are to be fetched

        Returns:
            displayed_details_dict(dict) : Dictionary of the details displayed
        """

        displayed_details_dict = {}
        self.__rtable.access_action_item(credential_name, "Edit")
        account_types = self.__rdropdown.get_selected_values("accountType", expand=False)
        account_type = None
        for account in account_types:
            account_type = account
        displayed_details_dict["Account type"] = account_type
        displayed_details_dict["Credential name"] = self.__admin_console.get_element_value_by_id("name")
        displayed_details_dict["User name"] = self.__admin_console.get_element_value_by_id("userAccount")
        displayed_details_dict["description"] = self.__admin_console.get_element_value_by_id("description")

        self.__admin_console.wait_for_completion()

        self.__rmodaldialog.click_cancel()
        return displayed_details_dict

    @PageService()
    def check_if_credential_exists(self, credential_name):
        """ Method to check if credential exists
        Args:
            credential_name(str) : Name of the credential to find whether it exists or not

        Returns:
            boolean : True if credential exists else False
        """
        return self.__rtable.is_entity_present_in_column("Credential name", credential_name)

    @PageService()
    def clear_automation_credentials(self, hours):
        """
        Clears all credentials starting with the prefix - "automation-credential-<timestamp>"
        if the credential has been there for more than the input hours.

        Args:
            hours (int): The hours to compare with the credential timestamp.
        """
        time = datetime.now() - timedelta(hours=hours)
        credential_list = self.__rtable.get_column_data("Credential name", fetch_all=True)

        for credential in credential_list:
            if credential.startswith("automation-credential-"):
                timestamp_str = credential.split("-")[-1]
                timestamp = int(timestamp_str)
                cred_time = datetime.fromtimestamp(timestamp)

                if cred_time < time:
                    try:
                        self.action_remove_credential(credential)
                    except Exception as e:
                        self.log.info(f"Error occurred while removing credential {credential}: {str(e)}")
