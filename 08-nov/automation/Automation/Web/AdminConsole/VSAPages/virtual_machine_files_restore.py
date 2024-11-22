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

    VirtualMachineFilesRestore() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

VirtualMachineFilesRestore --  This class contains methods for submitting virtual files machine
                                restores.

Functions:

    vm_files_restore() -- Restores the virtual machine files of the backedup VM to the path
                            in the destination server. Same definition can be used for both vmware
                            and hyperV restore.

"""
from Web.AdminConsole.VSAPages.restore_select_vm import RestoreSelectVM
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.panel import DropDown


class VirtualMachineFilesRestore:
    """
    This class contains methods for submitting virtual files machine restores.
    """
    def __init__(self, admin_console):
        """"""
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.res_select_vm_obj = RestoreSelectVM(admin_console)

    @PageService()
    def vm_files_restore(
            self,
            vm_name,
            files,
            destination_server,
            path,
            over_write=False):
        """
        Restores the virtual machine files of the backedup VM to the path in the destination server.
        Same definition can be used for both vmware and hyperV restore.

        Args:
            vm_name             (str)    :  name of the VM whose files are to be restored

            files               (list)          :  list of VM files to restore

            destination_server  (str)    :  destination server to restore to

            path                (str)    :  path to restore the file to

            over_write          (bool)          :  if files are to be overwritten during restore

        Raises:
            Exception:
                if there is an error while submitting a virtual machine files restore

        Returns:
            job_id      (str)   :  the restore job ID

        """
        self.__admin_console.log.info("Submitting Virtual Machine files Restore to server %s", destination_server)
        if not self.__admin_console.check_if_entity_exists(
                "xpath", "//div[1]/ul/li[2]/span[contains(text(), '" + vm_name + "')]"):
            self.res_select_vm_obj.select_vm(vm_name)
        self.__admin_console.select_for_restore(files)
        self.__driver.find_element(By.XPATH, 
            "//span[@id='browseActions']/a").click()
        self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists('id', 'fileLevelRestore_isteven-multi-select_#4866'):
            drop_down_obj = DropDown(self.__admin_console)
            drop_down_obj.select_drop_down_values(drop_down_id="fileLevelRestore_isteven-multi-select_#4866",
                                                  values=[destination_server])
        else:
            self.__admin_console.select_value_from_dropdown("destinationServer", destination_server)
        self.__admin_console.fill_form_by_id("restorePath", path)
        if over_write:
            self.__admin_console.checkbox_select("overwrite")
        self.__admin_console.log.info("Submitting virtual  machines files restore")
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form(False)
        return self.__admin_console.get_jobid_from_popup()
