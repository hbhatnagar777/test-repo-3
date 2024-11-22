# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
Main file for performing SNMP Configuration related operations

Classes:

    SNMPConfiguration()

Functions:

    add_configuration                  -- Method to create SNMP configuration

    edit_configuration                 -- Method to modify SNMP configuration

    check_if_snmp_configuration_exists -- Method to check existence of SNMP Configuration

    delete_configuration               -- Method to delete existing SNMP configuration
"""

from Web.Common.page_object import PageService
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog, ModalDialog


class SNMPConfiguration:
    """ Class for the SNMP Configuration page """

    def __init__(self, admin_page):
        """
        Method to initiate SNMP Configuration class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__admin_console.load_properties(self)
        self.__driver = admin_page.driver
        self.__rtable = Rtable(self.__admin_console)
        self.__drop_down = RDropDown(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console,
                                            xpath="//div[contains(@class, 'mui-modal-dialog')]")

    @PageService()
    def add_configuration(
            self,
            config_name,
            encryption_algorithm,
            username,
            password,
            privacy_algorithm,
            privacy_password):
        """
        Method to create new SNMP Configuration

        Args:
            config_name             (str)     :   Name of the configuration to be created
            encryption_algorithm    (str)     :   value of encryption algorithm to be selected for SNMP
            username                (str)     :   username for configuration
            password                (str)     :   password for configuration
            privacy_algorithm       (str)     :   value of privacy algorithm to be selected for SNMP
            privacy_password        (str)     :   privacy password for configuration

        Returns:
            None

        Raises:
            Exception:
                -- if configuration already exists
                -- if failed to create SNMP configuration

        """
        self.__rtable.access_toolbar_menu("Add configuration")
        self.__rmodal_dialog.fill_text_in_field("hostName", config_name)
        self.__rmodal_dialog.select_dropdown_values(values=[encryption_algorithm], drop_down_id="authAlgoDropdown")
        self.__rmodal_dialog.fill_text_in_field("username", username)
        self.__rmodal_dialog.fill_text_in_field("password", password)
        self.__rmodal_dialog.fill_text_in_field("confirmPassword", password)

        if privacy_algorithm:
            self.__rmodal_dialog.select_dropdown_values(values=[privacy_algorithm], drop_down_id="privacyAlgoDropdown")
            self.__rmodal_dialog.fill_text_in_field("privacyPassword", privacy_password)
            self.__rmodal_dialog.fill_text_in_field("privacyConfirmPassword", privacy_password)

        self.__rpanel.click_button("Add")

    @PageService()
    def edit_configuration(
            self,
            old_config_name,
            new_config_name=None,
            new_encryption_algorithm=None,
            new_username=None,
            new_password=None,
            new_privacy_algorithm=None,
            new_privacy_password=None):
        """
        Method to edit an existing SNMP Configuration

        Args:
            old_config_name (str): IP address of the configuration to be modified
            new_config_name (str): IP address of the configuration to be created
            new_username (str): username for new configuration
            new_password (str): password for new configuration
            new_privacy_password (str): private password for new configuration
            new_encryption_algorithm (str): value of encryption algorithm to be updated for SNMP
            new_privacy_algorithm (str): value of privacy algorithm to be updated for SNMP

        Returns:
            None

        Raises:
            Exception:
                -- if failed to edit SNMP configuration

        """

        self.__rtable.access_link(old_config_name)

        if new_config_name:
            self.__rmodal_dialog.fill_text_in_field("hostName", new_config_name)

        if new_encryption_algorithm:
            self.__rmodal_dialog.select_dropdown_values(values=[new_encryption_algorithm],
                                                        drop_down_id="authAlgoDropdown")
            if new_username:
                self.__rmodal_dialog.fill_text_in_field("username", new_username)
                self.__rmodal_dialog.fill_text_in_field("password", new_password)
                self.__rmodal_dialog.fill_text_in_field("confirmPassword", new_password)

            if new_privacy_algorithm:
                self.__rmodal_dialog.select_dropdown_values(drop_down_id="privacyAlgoDropdown",
                                                            values=[new_privacy_algorithm])
                if new_privacy_password:
                    self.__rmodal_dialog.fill_text_in_field("privacyPassword", new_privacy_password)
                    self.__rmodal_dialog.fill_text_in_field("privacyConfirmPassword", new_privacy_password)

        self.__rpanel.click_button('Save')

    @PageService()
    def delete_configuration(self, config_name):
        """
        Method to delete SNMP Configuration

        Args:
            config_name (str): Name of the configuration to be deleted
        """
        self.__rtable.search_for(config_name)
        self.__rtable.access_action_item(config_name, 'Delete')
        self.__admin_console.click_button_using_text('Yes')

    @PageService()
    def configuration_details(self, configuration_name):
        """
        Method to get configuration details

        Args:
            configuration_name (str) : Configuration name, the details to be fetched for

        Returns:
            configuration_details (dict) : dictionary containing configuration values displayed in UI
                Eg. - configuration_details = {'Host name': ['Test'], 'User name': ['admin']}
        """
        self.__rtable.search_for(configuration_name)
        configuration_details = self.__rtable.get_table_data()
        return configuration_details
