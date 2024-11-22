# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
DiskStorageDetails page of the AdminConsole

DiskStorageDetails:

    __click_edit_symbol()           -- Click edits symbol for key management server

    __click_ok_symbol()             -- Click ok symbol for key management server

    edit_key_management_server()    -- Edits the existing key management server

    add_backup_location()           -- To add a new backup location to an existing disk storage

    add_media_agent()               -- Add media agent to backup location on disk storage

    encrypt_storage()               -- To encrypt the storage on the selected disk

    decrypt_storage()               -- To decrypt the storage on the selected disk

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Storage.StorageDetails import StorageDetails
from Web.AdminConsole.Components.dialog import RModalDialog


class DiskStorageDetails(StorageDetails):
    """
    Class for Disk Storage Details page
    """

    def __init__(self, admin_console):
        """
        Initialization method for DiskStorageDetails Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console, "Disk")
        self._admin_console = admin_console
        self._backup_loc_rtable = Rtable(self._admin_console, title='Backup locations')

    @WebAction()
    def __click_edit_symbol(self):
        """
            Click edits symbol for key management server
        """
        self._driver.find_element(By.XPATH,
                                    f"//span[contains(text(),{self._props['label.keyManagement']})]//parent::li//span[2]//a//i").click()

    @WebAction()
    def __click_ok_symbol(self):
        """
            Click ok symbol for key management server
        """
        self._driver.find_element(By.XPATH,
                                  f"//span[contains(text(),{self._props['label.keyManagement']})]//parent::li//a[1]").click()

    @PageService()
    def edit_key_management_server(self, key_management_server):
        """
        Edits the existing key management server

            Args:
                key_management_server (str)	-- New key management server
        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        self.__click_edit_symbol()
        self._admin_console.wait_for_completion()
        self._modal_dialog.select_dropdown_values(0, [key_management_server])
        self.__click_ok_symbol()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()

    @PageService()
    def add_backup_location(self, media_agent, backup_location, saved_credential_name=None,
                            username=None, password=None):
        """
        To add a new backup location to an existing disk storage

        Args:
            media_agent     (str)       -- Media agent to create storage on

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            backup_location (str)       -- local/network path for the backup

        **Note** MediaAgent should be installed prior, for creating a backup location for storage.
                To use saved credentials for network path it should be created prior using credential manager,
        """
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self._backup_loc_rtable.access_toolbar_menu(self._props['action.add'])
        self._modal_dialog.select_dropdown_values(drop_down_id='mediaAgent', values=[media_agent])
        if saved_credential_name:
            self._admin_console.select_radio(value=self._props['label.network'])
            self._modal_dialog.enable_toggle(toggle_element_id='useSavedCredentials')
            self._modal_dialog.select_dropdown_values(drop_down_id='savedCredential', values=[saved_credential_name])
        elif username and password:
            self._modal_dialog.disable_toggle(toggle_element_id='useSavedCredentials')
            self._modal_dialog.fill_text_in_field("credential.userName-custom-input", username)
            self._modal_dialog.fill_text_in_field("credential.password-custom-input", password)

        dialog = RModalDialog(self._admin_console,
                              xpath="//*[contains(@class,'mui-modal-title') and text()='Add backup location']"
                                    "//ancestor::div[contains(@class, 'mui-modal-dialog')]")
        dialog.fill_text_in_field("path", backup_location)
        dialog.click_submit()
        self._admin_console.check_error_message()

    @PageService()
    def add_media_agent(self, backup_location, media_agent_list):
        """
        Add media agent to backup location on disk storage

            Args:
                backup_location   (str)   --  backup location on which given media agent will be added
                media_agent_list  (list)  --  list of media agents to be added
        """
        add_media_agent_dialog = RModalDialog(self._admin_console, title=self._props['title.addMediaAgent'])
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self._backup_loc_rtable.access_action_item(backup_location, self._props['title.addMediaAgent'])
        add_media_agent_dialog.select_items(media_agent_list)
        self._admin_console.click_button(self._props['action.save'])
        self._admin_console.check_error_message()

    @PageService()
    def encrypt_storage(self, cipher=None, key_length=None, key_management_server=None):
        """
        To encrypt the storage on the selected disk

            Args:
                cipher      (str)   -- Encryption method to be used

                key_length  (str)   -- Key length for the chosen cipher

                key_management_server   (str)   --  Key management server for the storage pool
        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        if cipher and key_length:
            panel_info = RPanelInfo(self._admin_console, self._props['title.encryption'])
            panel_info.enable_toggle(self._props['label.encrypt'])
            self._modal_dialog.select_dropdown_values(drop_down_id='cipherDropdown', values=[cipher])
            self._modal_dialog.select_dropdown_values(drop_down_id='keyLengthDropdown', values=[key_length])
            self._admin_console.click_button(self._props['label.save'])
            self._admin_console.check_error_message()
        if key_management_server:
            self.edit_key_management_server(key_management_server)

    @PageService()
    def decrypt_storage(self):
        """
        To Decrypt the storage on the selected disk
        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['title.encryption'])
        panel_info.disable_toggle(self._props['label.encrypt'])
        self._admin_console.check_error_message()
