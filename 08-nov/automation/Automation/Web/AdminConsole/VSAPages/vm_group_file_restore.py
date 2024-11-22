from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for file search and restore from vm groups page.


Classes:

    VMGroupFileRestore() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

    VMGroupFileRestore   ---> This class contains methods for file searching and restoring/downloading
                              from VM Group Page.

Functions:

    __select_server()    ---> Selects the server from which files are to be restored.

    __select_file()      ---> Selects the file and returns its relative position in the list.

    __submit_restore     ---> Submits the retore for VM Group file restore.

    restore_file()       ---> Restores the virtual machine files of the backedup VM to the path
                              in the destination server. Same definition can be used for both vmware
                              and hyperV restore.

"""
import re

from Web.AdminConsole.VSAPages.vm_details import VMDetails
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.panel import DropDown, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import TreeView


class VMGroupFileRestore:
    """
    This class contains methods for file search and restore/download from the VM Group Page.
    """
    def __init__(self, admin_console):
        """"""
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__table = Rtable(admin_console)
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__rpanel_info_obj = RPanelInfo(admin_console)
        self.__vm_details_obj = VMDetails(admin_console)
        self.__logger = self.__admin_console.log

    @PageService()
    def __select_server(self, vm_name):
        """
        This selects the server from which files are to be restored.

        Args:
            vm_name     (basestring) -- The server name.
        """
        self.__rpanel_info_obj.checkbox.check(id = vm_name)
        self.__admin_console.wait_for_completion()
        self.__table.reload_data()
        self.__admin_console.wait_for_completion()

    @PageService()
    def __select_file(self, file_path, download=False):
        """
        This selects the file by the path and selects the action to be performed.

        Args:
            file_path       (basestring)  -- The file path of the file to be selected in the server.

            download        (bool)        -- Whether to download the file or restore it. Download if true.

        Raises:
            Exception:
                - If the file is not found.
        """
        action = "Download" if download else "Restore"
        self.__logger.info(f"Finding the item to submit for {action}")

        while True:
            if self.__table.is_entity_present_in_column("Path", file_path, False):
                self.__table.access_action_item(file_path, action, search = False)
                break
            elif self.__table.has_next_page():
                self.__table.go_to_page('next')
                continue
            else:
                raise Exception("Could not find the items " + str(file_path))

    @PageService()
    def __submit_restore(self, restore_proxy, restore_path, over_write=True):
        """
        Submits the restore for VM Group file restore.

        Returns:
             jobid           (integer) -- The Restore job's ID.
        """
        restore_modal = RModalDialog(self.__admin_console, title='Restore options')
        self.__admin_console.log.info("Selecting destination client")
        restore_modal.select_dropdown_values(drop_down_id='destinationClient', values=[restore_proxy])
        restore_modal.click_button_on_dialog(text='Browse')
        self.__admin_console.wait_for_completion()
        path_modal = RModalDialog(self.__admin_console, title='Select a path')
        browse_tree = TreeView(self.__admin_console, xpath=path_modal.base_xpath)
        browse_tree.expand_path(path=restore_path.split('\\'), partial_selection=True)
        path_modal.click_submit()
        if over_write:
            restore_modal.enable_toggle(toggle_element_id='overwrite')
        self.__admin_console.log.info("Submitting the file restore job")
        self.__admin_console.wait_for_completion()
        restore_modal.click_submit()
        return self.__admin_console.get_jobid_from_popup()

    def restore_file(self, vm_name, file_name, file_path, restore_proxy,
                     restore_path, over_write=True, download=False):
        """
        Restores files from the VM Group page.

        Args:
            vm_name          (basestring) -- The server name.

            file_name        (basestring) -- Name of the file to be restored.

            file_path        (basestring) -- The file path to restore.

            restore_proxy    (basestring) -- The destination client proxy.

            restore_path     (basestring) -- The path to restore the files to in destination client.

            over_write       (basestring) -- Whether to overwrite the existing files, if any, or not.

            download         (basestring) -- Whether to download the file or restore it. Download if true.

        Returns:
             jobid           (integer) -- The Restore job's ID.
        """
        if self.__admin_console.check_if_entity_exists("id", "fileAndFolderSearch") or\
            self.__admin_console.check_if_entity_exists("class", "searchInput"):
            self.__vm_details_obj.vm_search_content(file_name)
        else:
            input_element = self.__driver.find_element(By.XPATH, "//input[@class='global-file-search-input']")
            input_element.send_keys(u'\ue009' + 'a' + u'\ue003')
            input_element.send_keys(file_name)
            self.__admin_console.wait_for_completion()

        self.__select_server(vm_name)

        self.__select_file(file_path, download)
        return self.__submit_restore(restore_proxy, restore_path, over_write)
