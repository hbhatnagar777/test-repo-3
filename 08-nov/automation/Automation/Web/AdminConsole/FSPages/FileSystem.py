# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
File System iDA on the AdminConsole

Class:

    FileSystem() -> iDA() -> ClientDetails() -> Clients() -> Server() --
            -> _Navigator() -> LoginPage() -> AdminConsoleBase() -> object()

Functions:

open_backupset()           -- select and open a backup set
add_backupset()            -- create and add a new backup set
action_add_subclient()      -- create and add a new subclient
browse_and_select_folder()   -- browser and select files and folders to associate with the subclient

"""

from Web.AdminConsole.Helper.Imports import *
from Web.AdminConsole.FSPages.iDA import iDA


class FileSystem(iDA):
    '''
    This class provides the function or operations that can be performed on the
    File System iDA on the AdminConsole
    '''

    @WebAction()
    def open_backupset(self, backupset):
        """Opens the backupset with the given name.

            backupset   : a string, name of the backupset we want to open
        """
        import Web.AdminConsole.Helper.FSHelper.Backupset as Backupset
        self.log.info("opening backupset " + backupset)
        if self.check_if_entity_exists("link", backupset):
            self.driver.find_element(By.LINK_TEXT, backupset).click()
            self.wait_for_completion()
            return True, Backupset.Backupset(self.driver)
        else:
            exp = "There is no backupset with the name " + backupset
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def add_backupset(self, backupset):
        """Adds a new backupset to the iDA.

            backupset   : a string, name of the backupset we want to add

        """
        self.log.info("Adding a new backupset")
        self.driver.find_element(By.LINK_TEXT, "Add BackupSet").click()
        self.wait_for_completion()
        self.driver.find_element(By.NAME, 
            "backupSetName").send_keys(backupset)
        self.driver.find_element(By.XPATH, 
            "//form/div/button[@class='btn btn-primary cvBusyOnAjax']").click()
        self.wait_for_completion()
        if self.check_if_entity_exists(
                "xpath", "//div/div[2]/form/span[@class='serverMessage  error']"):
            err_msg = self.driver.find_element(By.XPATH, 
                "//div/div[2]/form/span[@class='serverMessage  error']").text
            self.log.error(err_msg)
            self.driver.find_element(By.XPATH, 
                "//form/div/button[contains(text(),'Cancel')]").click()
            self.wait_for_completion()
            raise Exception(err_msg)

    @WebAction()
    def action_add_subclient(self, subclient, backupset, storage_policy, folders):
        """Adds a subclient with the specified content under the given backupset.

            subClient       : a string, name of the subclient we want to associate the backupset to
            backupset       : a string, name of the backupset we want to associate
            storage_policy   : a string, storage policy we want to associate to with this subclient
            folders         : a list,   list of files, folders to associate to this subclient
        """
        self.log.info(
            "Adding subclient " +
            subclient +
            " to the backupset " +
            backupset)
        self.driver.find_element(By.XPATH, 
            "//a[text()='" +
            backupset +
            "']/../../div[3]/div/a/span[@class='grid-action-icon']").click()
        if self.check_if_entity_exists("link", "Add Subclient"):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" +
                backupset +
                "']/../../div[3]/div/ul/li[1]/a[text()='Add Subclient']").click()
            self.wait_for_completion()
            self.driver.find_element(By.NAME, 
                "subclientName").send_keys(subclient)
            Select(self.driver.find_element(By.NAME, "storagePolicy")
                  ).select_by_visible_text(storage_policy)
            self.driver.find_element(By.LINK_TEXT, "Content").click()
            self.driver.find_element(By.XPATH, 
                "//form/cv-tabset-component/div/div[2]/div[2]/button[\
                contains(text(),'Add/Edit Content')]").click()
            self.driver.find_element(By.XPATH, 
                "//section/form/button[contains(text(),'Browse')]").click()
            self.wait_for_completion()
            self.browse_and_select_folder(folders)
            self.driver.find_element(By.XPATH, 
                "//section/form/div/button[contains(text(),'OK')]").click()
            # activity control
            self.driver.find_element(By.LINK_TEXT, 
                "Activity Control").click()
            if not self.driver.find_element(By.XPATH, 
                    "//label[contains(text(),'Enable Backup')]").is_enabled():
                self.driver.find_element(By.XPATH, 
                    "//label[contains(text(),'Enable Backup')]").click()
            self.driver.find_element(By.XPATH, 
                "//section/form/div/button[contains(text(),'Add')]").click()
            self.wait_for_completion()
            if self.check_if_entity_exists(
                    "xpath", "//div[2]/span[@class='error']"):
                exp = self.driver.find_element(By.XPATH, 
                    "//div[2]/span[@class='error']").text
                self.log.error(exp)
                self.driver.find_element(By.XPATH, 
                    "//form/div/button[contains(text(),'Cancel')]").click()
                self.wait_for_completion()
                raise Exception(exp)

    @WebAction()
    def browse_and_select_folder(self, folders):
        """Selects the folders and files to be given as  content to the subclient.

            folders : a list, list of files and folders we want to select to add
        """
        self.log.info("Selecting folders")
        while True:
            exit_flag = False
            if not folders:
                break
            collapsed_elements = self.driver.find_elements(By.XPATH, 
                "//button[@class='collapsed']")
            if not collapsed_elements:
                break
            for element in collapsed_elements:
                element.click()
                if self.check_if_entity_exists(
                        "xpath", "//span[contains(text(),'" + folders + "')]"):
                    self.driver.find_element(By.XPATH, 
                        "//span[contains(text(),'" + folders + "')]").click()
                    self.log.info(
                        "Added folder " +
                        folders +
                        " to the browse content")
                    exit_flag = True
            if exit_flag:
                break
        self.driver.find_element(By.XPATH, 
            "//div[10]/div/div/div[2]/div[2]/button[\
            contains(text(),'OK')]").click()
        self.wait_for_completion()
