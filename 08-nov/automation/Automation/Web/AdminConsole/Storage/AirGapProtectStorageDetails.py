# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AirGapProtectStorageDetails page of the AdminConsole

AirGapProtectStorageDetails:

    __click_edit_symbol()           -- Click edits symbol for key management server

    __click_ok_symbol()             -- Click ok symbol for key management server

    edit_key_management_server()    -- Edits the existing key management server

    add_container()                 -- To add a new container to an existing air gap protect storage

    delete_container()              -- Deletes the container on air gap protect storage

    add_media_agent()               -- Add media agent to container on air gap protect storage

    encrypt_storage()               -- To encrypt the storage on the selected air gap protect


"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.table import Rtable, RDropDown
from Web.AdminConsole.Components.panel import (PanelInfo, DropDown)
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Storage.StorageDetails import StorageDetails
from Web.AdminConsole.Components.dialog import RModalDialog


class AirGapProtectStorageDetails(StorageDetails):
    """
    Class for AirGapProtectStorageDetails page
    """

    def __init__(self, admin_console):
        """
        Initialization method for AirGapProtectStorageDetails Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console, "AirGapProtect")
        self.__drop_down = DropDown(admin_console)
        self.__dropdown = RDropDown(admin_console)
        self.__bucket_rtable = Rtable(admin_console, id='cloud-overview-grid')

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
            f"//span[contains(text(),{self._admin_console.props['label.keyManagement']})]//parent::li//a[1]").click()

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
        self.__drop_down.select_drop_down_values(0, [key_management_server])
        self.__click_ok_symbol()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()

    @PageService()
    def add_container(self, media_agent, location, license=None, storage_class=None, replication=None):
        """
        To add a new container to an existing air gap protect storage

        Args:
            media_agent     (str)       -- Media agent used to add container

            license         (str)       -- Type of license used to add container

            location        (str)       -- Location of container

            storage_class   (str)       --  storage class to be associated with the container

            replication       (str)       -- replication associated with container

        **Note** MediaAgent should be installed prior
        """
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self.__bucket_rtable.access_toolbar_menu(self._props['action.add'])
        self.__dropdown.select_drop_down_values(drop_down_id='mediaAgent', values=[media_agent])
        if license:
            self.__dropdown.select_drop_down_values(drop_down_id='licenseType', values=[license])
        if storage_class:
            self.__dropdown.select_drop_down_values(drop_down_id='storageClass', values=[storage_class])
        self.__dropdown.select_drop_down_values(values=[location], drop_down_id='location')
        if replication:
            self.__dropdown.select_drop_down_values(drop_down_id='replication', values=[replication])
        self._admin_console.click_button(self._admin_console.props['action.save'])
        self._admin_console.check_error_message()

    @PageService()
    def add_media_agent(self, container, media_agent_list):
        """
        Add media agent to container on air gap protect storage

            Args:
                container   (str)   --  container on which given media agent will be added
                media_agent_list  (list)  --  list of media agents to be added
        """
        add_media_agent_dialog = RModalDialog(self._admin_console, title=self._props['title.addMediaAgent'])
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self.__bucket_rtable.access_action_item(container, self._props['title.addMediaAgent'])
        add_media_agent_dialog.select_items(media_agent_list)
        self._admin_console.click_button(self._admin_console.props['action.save'])
        self._admin_console.check_error_message()

    @PageService()
    def encrypt_storage(self, cipher=None, key_length=None, key_management_server=None):
        """
        To encrypt the storage on the selected air gap protect
            Args:
                cipher      (str)   -- Encryption method to be used

                key_length  (str)   -- Key length for the chosen cipher

                key_management_server   (str)   --  Key management server for the storage pool
        """
        self._admin_console.access_tab(self._admin_console.props['label.scaleOutConfiguration'])
        self._admin_console.wait_for_completion()
        if cipher and key_length:
            panel_info = PanelInfo(self._admin_console, self._admin_console.props['title.encryption'])
            panel_info.enable_toggle(self._admin_console.props['label.encrypt'])
            self.__drop_down.select_drop_down_values(0, [cipher])
            self.__drop_down.select_drop_down_values(1, [key_length])
            self._admin_console.click_button(self._admin_console.props['action.save'])
            self._admin_console.check_error_message()
        if key_management_server:
            self.edit_key_management_server(key_management_server)

