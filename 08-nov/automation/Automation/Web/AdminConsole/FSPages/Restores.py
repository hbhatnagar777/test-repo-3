from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
restores page of the file System iDA on the AdminConsole

Class:

    Restores() -> AdminConsole() -> AdminConsoleBase() -> object()

Functions:

open_folder()        -- open a folder to browser contents
select_for_restore() -- select the files and folders for restore
submit_restore()     -- submit a restore job

"""

import os

from Web.AdminConsole.Components.browse import Browse
from Web.Common.page_object import PageService, WebAction


class Restores:
    """
    This class provides the function or operations that can be performed on the
    restores page of the File System iDA on the AdminConsole
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console


    @PageService()
    def access_folder(self, folder_name):
        """Access the folder in the panel

        Args:
            folder_name(str) : name of the folder

        """
        browse = Browse(self._admin_console)
        browse.access_folder(folder_name)

    @PageService()
    def submit_restore(self,  destination, items=None, in_place=True,
                       restore_path=None, overwrite=False, select_all=False):
        """Submits a restore job of the given items.

            destination : a string,  destination server we want to restore to
            items       : a list,    list of files and folders we want to select to restore
            in_place    : a boolean, to restore the files and folders to the original folder
            restore_path : a string,  path of the directory we want to restore to
            overwrite   : a boolean, to decide whether to overwrite the files or not;
            select_all  : a boolean, if all files need to be selected for restore
        """
        browse = Browse(self._admin_console)
        browse.select_for_restore(items, select_all)
        self._admin_console.driver.find_element(By.XPATH, 
            "//a[@class='ng-binding'][contains(text(),'Restore')]").click()
        self._admin_console.wait_for_completion()

        self.__enter_details_for_restore(destination, restore_path, in_place, overwrite)

        self._admin_console.submit_form(wait=False)
        return self._admin_console.get_jobid_from_popup()

    @WebAction()
    def __enter_details_for_restore(self,
                                    client_name,
                                    restore_path,
                                    inplace_restore,
                                    overwrite_backup):
        """
        Method to enter details for restore

        Args:
            client_name      (string)       : Name of the client containg subclient to
                                            be restored

            restore_path     (string(Path)) : Path to which the dat is to be restored
                Eg. - 'C:\\TestRestore'

            inplace_restore  (boolean)      : in place restore to be allowed or not

            overwrite_backup (boolean)      : backup to be overwritten or not

        Returns:
            None

        Raises:
            Exception:
                -- if fails to enter details for restore
        """

        self._admin_console.log.info("Entering details for restore")
        self._admin_console.select_value_from_dropdown("destinationServer", client_name)

        if inplace_restore:
            self._admin_console.checkbox_select("inplace")
        else:
            self._admin_console.checkbox_deselect("inplace")
            self._admin_console.fill_form_by_id("restorePath", restore_path)

        if overwrite_backup:
            self._admin_console.checkbox_select("overwrite")
        else:
            self._admin_console.checkbox_deselect("overwrite")

        self._admin_console.log.info("Details entered successfully.")

