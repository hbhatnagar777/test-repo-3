from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
subclient of the File System iDA on the AdminConsole

Class:

    Subclient() -> Backupset() -> FileSystem() -> ClientDetails() --
        -> Clients() -> Server() -> AdminConsole() -> AdminConsoleBase() -> object()

Functions:

backup_enabled()  -- enable or disable to backup option
edit_storage()    -- edit the storage policy
manage_schedule() -- create or delete backup shcedules
select_schedule() -- selects and opens a schedule
add_schedule()    -- creates a new backup schedule for backup
delete_schedule() -- deletes a schedule
backup_jobs()     -- displays all the backup jobs of the subclient
backup_now()      -- triggers the backup job for the subclient
content_info()    -- displays the content associated with the subclient
edit_content()    -- edit the content of the subclient for backup
restore()        -- triggers the restore job for the subclient

"""
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Helper.Imports import *
from Web.AdminConsole.FSPages.Backupset import Backupset
from Web.Common.page_object import PageService


class Subclient(Backupset):
    """
    This class provides the function or operations that can be performed on the
    subclient of the File System iDA on the AdminConsole
    """

    def __init__(self, admin_console):
        super().__init__(admin_console)

    @WebAction()
    def backup_enabled(self):
        """Enable or disable the Backup Enabled toggle.
        """
        self._admin_console.log.info("Enabling backup")
        if self._admin_console.check_if_entity_exists(
                "xpath",
                "//div[1]/cv-tile-component[1]//li[2]//span[\
                @class='manage-activity']"):
            if self._admin_console.driver.find_element(By.XPATH, 
                    "//div[1]/cv-tile-component[1]//li[2]//span[\
                    @class='manage-activity']").is_enabled():
                self._admin_console.driver.find_element(By.XPATH, 
                    "//div[1]/cv-tile-component[1]//li[2]//span[\
                    @class='manage-activity']").click()
                self._admin_console.wait_for_completion()
            else:
                exp = "There is no toggle for enabling backup"
                self._admin_console.log.error(exp)
                raise Exception(exp)

    @WebAction()
    def edit_storage(self, storage_policy):
        """Change the storage policy of the subclient to the given policy.

            storage_policy : a string, storage policy we want to associate to the subclient

        """
        self._admin_console.log.info("Changing the storage policy")
        self._admin_console.driver.find_element(By.XPATH, 
            "//div[2]/cv-tile-component[1]/div/div/div/div[1]/a[\
            contains(text(),'Edit')]").click()
        self._admin_console.wait_for_completion()
        Select(self._admin_console.driver.find_element(By.ID, "dataStoragePolicy")
              ).select_by_visible_text(storage_policy)
        self._admin_console.driver.find_element(By.XPATH, 
            "//div[2]/cv-tile-component[1]/div/div/div/div[2]/div[2]/button[\
            contains(text(),'OK')]").click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def manage_schedule(self):
        """Opens the schedule window that enables the creation,
            or deletion of backup schedules for the subclient.
        """
        self._admin_console.log.info("Managing schedules")
        if self._admin_console.check_if_entity_exists(
                "link", "Add schedule"):
            self._admin_console.driver.find_element(By.LINK_TEXT, "Add schedule").click()
            self._admin_console.wait_for_completion()
        else:
            exp = "There is no option to manage the schedules"
            self._admin_console.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def select_schedule(self, schedule_name):
        """Opens the schedule with the given name.

            schedule_name : a string, name of the schedule we want to open
        """
        self._admin_console.log.info("Opening schedule " + schedule_name)
        if self._admin_console.check_if_entity_exists("link", schedule_name):
            self._admin_console.driver.find_element(By.LINK_TEXT, schedule_name).click()
        else:
            exp = "There is no schedule by the name " + schedule_name
            self._admin_console.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def backup_jobs(self):
        """Lists all the backup jobs of the subclient.
        """
        self._admin_console.log.info("Opening Jobs for the subclient")
        if self._admin_console.check_if_entity_exists("link", "Jobs"):
            self._admin_console.driver.find_element(By.LINK_TEXT, "Jobs").click()
            self._admin_console.wait_for_completion()
        else:
            exp = "There is no link called Jobs"
            self._admin_console.log.error(exp)
            raise Exception(exp)

    @PageService()
    def backup_now(self, bkp_type):
        """Starts a backup for the subclient with the given type.

            bkp_type (BackupType) : type of backup we want to start, among the type in Backup.BackupType enum
        """
        self._admin_console.log.info("Backing up the subclient content")
        if self._admin_console.check_if_entity_exists("link", "Back up now"):
            self._admin_console.driver.find_element(By.LINK_TEXT, "Back up now").click()
            self._admin_console.wait_for_completion()
            backup = Backup(self._admin_console)
            return backup.submit_backup(bkp_type)
        else:
            exp = "Another backup job is running for the subclient"
            raise Exception(exp)

    @WebAction()
    def content_info(self):
        """Lists all the content of the subclient.
        """
        self._admin_console.log.info("The subclient content is ")
        content = []
        elements = self._admin_console.driver.find_elements(By.XPATH, 
            "//span/div[2]/div[2]/cv-tile-component[3]/div/div/div/ul/li")
        for elem in elements:
            content.append(elem.text)
        self._admin_console.log.info(content)

    @WebAction()
    def edit_content(self):
        """Edits the content of the subclient by adding or removing files and folders.

        """
        self._admin_console.log.info("Edit the content of the subclient")
        if self._admin_console.check_if_entity_exists(
                "xpath",
                "//div[2]/cv-tile-component[4]/div/div/div/div/a[\
                @data-ng-click='manageSubclientContent()']"):
            self._admin_console.driver.find_element(By.XPATH, 
                "//div[2]/cv-tile-component[4]/div/div/div/div/a[\
                @data-ng-click='manageSubclientContent()']").click()
            self._admin_console.wait_for_completion()
        else:
            exp = "There is no option to edit the content of the subclient"
            self._admin_console.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def restore(self):
        """If the subclient has been backed up then this option leads to restore options.

        """
        import Web.AdminConsole.FSPages.RestoreSelectVolume as RestoreSelectVolume
        self._admin_console.log.info("Going to restore the subclient content")
        if self._admin_console.check_if_entity_exists("link", "Restore"):
            self._admin_console.driver.find_element(By.LINK_TEXT, "Restore").click()
            self._admin_console.wait_for_completion()
            return True, RestoreSelectVolume.RestoreSelectVolume(
                self._admin_console)
        else:
            exp = "The subclient has not been backedup yet or there \
                  is no option to restore the subclient content"
            self._admin_console.log.error(exp)
            raise Exception(exp)
