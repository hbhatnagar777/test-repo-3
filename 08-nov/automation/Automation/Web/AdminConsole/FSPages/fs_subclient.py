from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
subclient of the File System agent on the AdminConsole

Class:

    FsSubclient() -> SubclientDetails() ->  AdminConsole() -> AdminConsoleBase() -> object()

Functions:

backup_enabled()  -- enable or disable to backup option

select_schedule() -- selects and opens a schedule

edit_content()    -- edit the content of the subclient for backup

"""

from Web.AdminConsole.AdminConsolePages.subclient_details import SubclientDetails
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.Common.page_object import (
    WebAction,
    PageService
)


class FsSubclient(SubclientDetails):

    """
    This class provides the function or operations that can be performed on the
    subclient of the File System iDA on the AdminConsole
    """
    def __init__(self, admin_console):

        super(FsSubclient, self).__init__(admin_console)
        self.__modal_dialog = ModalDialog(self._admin_console)

    @PageService()
    def enable_backup(self):
        """
        Enable or disable the Backup Enabled toggle.

        Returns:
            None

        Raises:
            Exception:
                Toggle button not found

        """
        self._admin_console.toggle_enable('Data backup')

    @PageService()
    def select_schedule(self, schedule_name):
        """
        Opens the schedule with the given name.

        Args:
            schedule_name (str): name of the schedule we want to open

        Returns:
            None

        Raises:
            Exception:
                Schedule not found


        """
        self._admin_console.select_hyperlink(schedule_name)

    @WebAction()
    def edit_content(self):
        """
        Edits the content of the subclient by adding or removing files and folders.

        Returns:
            None

        Raises:
            Exception:
                There is no option to edit the content of the collection
        """
        if self._admin_console.check_if_entity_exists(
                "xpath", "//cv-tile-component[@data-title='Content']"
                         "//a[contains(text(),'Edit')]"):
            self._admin_console.driver.find_element(By.XPATH, 
                "//cv-tile-component[@data-title='Content']"
                "//a[contains(text(),'Edit')]").click()
            self._admin_console.wait_for_completion()
        else:
            raise Exception("There is no option to edit the content of the collection")

    @PageService()
    def delete_subclient(self):
        """
        Deletes the subclient

        Raises:
            Exception:
                if the subclient could not be deleted

        """
        self._admin_console.select_hyperlink("Delete")
        self.__modal_dialog.type_text_and_delete("DELETE")
        self._admin_console.check_error_message()
        self._admin_console.log.info("Sub client Deleted successfully.")

    @PageService()
    def enable_snapshot_engine(self, enable_snapshot, engine_name):
        """
        Sets the snapshot engine for the subclient
        Args:
            enable_snapshot (bool):     to enable / disable snap backups on the subclient

            engine_name     (str):   name of the snapshot engine

        Returns:

        """
        self._admin_console.tile_select_hyperlink("Snapshot engine", "Edit")
        if enable_snapshot:
            self._admin_console.checkbox_select("showSelected")
            self._admin_console.wait_for_completion()
            if not engine_name:
                raise Exception("The engine name is not provided")
            self._admin_console.select_value_from_dropdown("engine", engine_name)
        else:
            self._admin_console.checkbox_deselect("showSelected")
        self._admin_console.submit_form()
        self._admin_console.check_error_message()
