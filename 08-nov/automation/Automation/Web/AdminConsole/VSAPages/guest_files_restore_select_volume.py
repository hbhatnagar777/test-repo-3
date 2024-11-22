from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides method virtual files machine restores.


Classes:

    GuestFilesRestoreSelectVolume() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

    GuestFilesRestoreSelectVolume --  This class contains methods for submitting virtual
                                    files machine restores.

    Functions:

    select_volume() -- Opens the drives of the backed up VM to browse content

"""
from Web.Common.page_object import WebAction
from Web.AdminConsole.VSAPages.restore_select_vm import RestoreSelectVM
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.table import Rtable


class GuestFilesRestoreSelectVolume:
    """
    This class contains methods for submitting virtual files machine restores.
    """
    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__browse_obj = RBrowse(admin_console, "virtualizationBrowse")
        self.__table = Rtable(self.__admin_console, id="virtualizationBrowse")
        self.res_select_vm_obj = RestoreSelectVM(admin_console)

    @WebAction()
    def select_volume(self, vm_name, vol):
        """
        Opens the drives of the backed up VM to browse content

        Args:
            vm_name (str): vm name to be selected
            vol (str)    : volume to be selected
        """
        if self.__table.is_entity_present_in_column(
                column_name=self.__admin_console.props['label.name'], entity_name=vm_name):
            self.__browse_obj.access_folder(vm_name)
        self.__admin_console.log.info("Opening volume %s", vol)
        if "/" in vol:
            folder_to_browse = vol.split("/")[1:]
            if not folder_to_browse[0]:
                return
        else:
            folder_to_browse = [vol]
        if not self.__table.is_entity_present_in_column(
                    column_name=self.__admin_console.props['backupBrowse.tableColumn.name'], entity_name=vol):
            if ':' in vol:
                folder_to_browse = [vol.split(":")[0]]
            else:
                folder_to_browse = [vol+':']
        for folder in folder_to_browse:
            while True:
                if not self.__table.is_entity_present_in_column(
                        column_name=self.__admin_console.props['label.name'], entity_name=folder):
                    if self.__admin_console.cv_table_next_button_exists():
                        if self.__driver.find_element(By.XPATH,
                                "//button[@ng-disabled='cantPageForward()']").is_enabled():
                            self.__admin_console.cv_table_click_next_button()
                            continue
                    else:
                        raise Exception("Volume {} not found".format(vol))
                self.__browse_obj.access_folder(folder)
                break
