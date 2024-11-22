from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides method for guest files restore.

Classes:

    EndUserGuestFilesRestoreSelectFolder() ---> _Navigator() ---> AdminConsoleBase() ---> Object()


Functions:

    __select_restore_or_download()           -- Selects either restore or download

    submit_this_vm_restore()     -- Submits a VMware guest files restore with the backed up VM as
                                    the destination server

"""

from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import PanelInfo, RDropDown
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.dialog import RModalDialog


class EndUserGuestFilesRestoreSelectFolder:
    """
    This class provides methods to perform guest files restore to same vm
    """

    def __init__(self, admin_console):
        # super(EndUserGuestFilesRestoreSelectFolder, self).__init__(driver)
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__panel_obj = PanelInfo(admin_console)
        self.__browse_obj = RBrowse(admin_console, "virtualizationBrowse")
        self.__dropdown_obj = RDropDown(admin_console)

    @WebAction()
    def __select_restore_or_download(self, action="Restore"):
        """
        Selects restore / download button

        Args:
            action  (str):   To Select restore or download button

        """
        self.__driver.execute_script("window.scrollTo(0,0)")
        if action == "Download":
            self.__browse_obj.submit_for_download()
        else:
            self.__browse_obj.submit_for_restore()

    @WebAction()
    def __verify_vm(self, vm_name):
        """
        Verify backup vm is selected by default under myVM

        Args:
        vm_name (base string) -- name of the backup vm

        Raises:
            Exception:
                If the VM name is different from the VM selected under myVM

        """

        if vm_name not in self.__dropdown_obj.get_selected_values('destinationClient', expand=False)[0]:
            raise Exception("The source backup VM was not selected by default.")

    @PageService()
    def enduser_files_restore(
            self,
            files,
            vm_name,
            vm_username,
            vm_password,
            path,
            over_write=True,
            all_files=False):
        """
        Submits a VMware guest files restore with the backed up VM as the destination server

        Args:
            files            (list)         :  the files to be restored

            vm_name          (str)   :  the VM to which the files are to be restored

            proxy            (str)   :  the proxy to be used for restore

            vm_username      (str)   :  the username of the destination VM

            vm_password      (str)   :  the password of the destination VM

            path             (str)   :  the path in the destination VM where files are
                                                to be restored

            over_write       (bool)         :  if files are to be overwritten during restore

            all_files        (bool)         :  if all the files are to be selected for restore

        Returns:
            job_id           (str)   :  the ID of the restore job submitted

        """
        self.__browse_obj.select_files(files, all_files)
        self.__admin_console.log.info("Files selected. Submitting restore")
        self.__select_restore_or_download()
        restore_modal_dialog = RModalDialog(self.__admin_console, "Restore options")

        self.__verify_vm(vm_name)

        if self.__admin_console.check_if_entity_exists("name", "userName"):
            self.__admin_console.log.info("Filling the vm creds")
            restore_modal_dialog.fill_text_in_field("userName", vm_username)
            restore_modal_dialog.fill_text_in_field("password", vm_password)

        self.__admin_console.log.info("Filling in the restore path")
        restore_modal_dialog.fill_text_in_field("selectedPath", path)

        if over_write:
            restore_modal_dialog.enable_toggle(toggle_element_id="overwrite")

        self.__admin_console.log.info("Submitting end user Guest files restore to the same VM")
        restore_modal_dialog.click_submit()

        return self.__admin_console.get_jobid_from_popup()
