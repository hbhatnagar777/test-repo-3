# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
CloudStorageDetails page of the AdminConsole

CloudStorageDetails:

    __click_edit_symbol()           -- Click edits symbol for key management server

    __click_ok_symbol()             -- Click ok symbol for key management server

    edit_key_management_server()    -- Edits the existing key management server

    add_container()                 -- To add a new container to an existing cloud storage

    delete_container()              -- Deletes the container on cloud storage

    add_media_agent()               -- Add media agent to container on cloud storage

    encrypt_storage()               -- To encrypt the storage on the selected cloud


"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from Web.AdminConsole.Components.table import Rtable, RDropDown
from Web.AdminConsole.Components.panel import (PanelInfo, DropDown)
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Storage.StorageDetails import StorageDetails
from Web.AdminConsole.Components.dialog import RModalDialog


class CloudStorageDetails(StorageDetails):
    """
    Class for CloudStorageDetails page
    """

    def __init__(self, admin_console):
        """
        Initialization method for CloudStorageDetails Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console, "Cloud")
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
    def add_container(self, media_agent, server_host, container, storage_class=None, saved_credential_name=None,
                      username=None, password=None, auth_type=None):
        """
        To add a new container to an existing cloud storage

        Args:
            media_agent     (str)       -- Media agent to create storage on

            server_host     (str)       -- cloud server host name

            container       (str)       -- container to be associated with the storage

            storage_class   (str)       --  storage class to be associated with the container

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            auth_type       (str)       -- type of authentication

        **Note** MediaAgent should be installed prior, for creating a storage,
                To use saved credentials it should be created prior using credential manager.
        """

        self._admin_console.access_tab(self._props['label.backupLocations'])
        self.__bucket_rtable.access_toolbar_menu(self._props['action.add'])
        self.__dropdown.select_drop_down_values(drop_down_id='mediaAgent', values=[media_agent])

        self._admin_console.fill_form_by_id("serviceHost", server_host)
        if storage_class:
            self._admin_console.select_value_from_dropdown("storageClass", storage_class)
        if auth_type:
            self.__dropdown.select_drop_down_values(drop_down_id="authentication", values=[auth_type])
        if saved_credential_name:
            self.__dropdown.select_drop_down_values(drop_down_id='savedCredential',
                                                    values=[saved_credential_name])
        else:
            self._admin_console.fill_form_by_id("userName", username)
            self._admin_console.fill_form_by_id("password", password)

        self.__add_container_to_cloud_storage(container_name=container)
        self._admin_console.click_button(self._admin_console.props['action.save'])
        self._admin_console.check_error_message()

    @PageService()
    def add_media_agent(self, container, media_agent_list):
        """
        Add media agent to container on cloud storage

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
        To encrypt the storage on the selected cloud

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

    @WebAction()
    def __add_container_to_cloud_storage(self, container_name):
        """
            Method to fill in the container name and click on  add "<container>"

            Args:
                container_name (str)    :   Name of the container

        """
        self._admin_console.fill_form_by_id("mountPath", container_name)
        wait = WebDriverWait(self._driver, 30)
        add_container_locator = (By.ID, 'mountPath-option-0')
        # wait at most 30 sec to locate the add "<container>" element
        add_container_element = wait.until(ec.visibility_of_element_located(add_container_locator))
        add_container_element.click()

