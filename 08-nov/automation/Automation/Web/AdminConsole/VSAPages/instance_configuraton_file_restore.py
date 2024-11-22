# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides method instance configuration files restores.


Classes:

    InstanceConfigurationFilesRestore() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

InstanceConfigurationFilesRestore --  This class contains methods for submitting instance configuration files restores.

Functions:

    vm_instance_configuration_files_restore() -- Restores the instance configuration files of the backedup VM to the
                                                path in the destination server. Same definition can be used for Amazon
                                                restore

"""
from Web.AdminConsole.VSAPages.restore_select_vm import RestoreSelectVM
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.panel import DropDown
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.wizard import Wizard


class InstanceConfigurationFilesRestore:
    """
    This class contains methods for submitting instance configuration files machine restores.
    """
    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.
        Args:
            admin_console  (Object) : Admin console class object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.res_select_vm_obj = RestoreSelectVM(admin_console)

    @PageService()
    def vm_instance_configuration_files_restore(self, vm, destination, path, over_write=False):
        """
        Restores the instance configuration files of the backedup VM to the path in the destination server.
        Same definition can be used for amazon restore.

        Args:
            vm                  (str)    :  name of the VM whose files are to be restored

            destination         (str)    :  name of the destination server to restore to

            path                (str)    :  path to restore the file to

            over_write          (bool)   :  if files are to be overwritten during restore

        Raises:
            Exception:
                if there is an error while submitting a instance configuration files  restore

        Returns:
            job_id      (str)   :  the restore job ID

        """
        self.__admin_console.log.info("Submitting Instance Configuration files restore to server %s", destination)
        if not self.__admin_console.check_if_entity_exists("xpath",
                                                           "//div[1]/ul/li[2]/span[contains(text(), '" + vm + "')]"):
            self.res_select_vm_obj.select_vm(vm)
        self.__admin_console.driver.find_element(By.XPATH,
                        "//div[contains(@aria-label,'NetworkConfig')]/ancestor::tr//input[@type='checkbox']").click()
        self.__admin_console.driver.find_element(By.XPATH,
                        "//div[contains(@aria-label,'InstanceConfig')]/ancestor::tr//input[@type='checkbox']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Restore']").click()
        restore_wizard = Wizard(self.__admin_console)
        restore_wizard.select_drop_down_values(id='restoreVMFilesDropdown', values=[destination])
        self.__admin_console.fill_form_by_id("destinationPath", path)
        self.__admin_console.log.info("Submitting virtual  machines files restore")
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form(False)
        return self.__admin_console.get_jobid_from_popup()


