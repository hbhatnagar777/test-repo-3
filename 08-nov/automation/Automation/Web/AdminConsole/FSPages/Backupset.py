# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
backup set  of the File System iDA on the AdminConsole

Class:

    Backupset() -> FileSystem() -> ClientDetails() -> Clients() --
        -> Server() -> _Navigator() -> LoginPage() -> AdminConsoleBase() -> object()

Functions:

add_fs_subclient()                  -- Adds a new subclient
check_if_subclient_exists()         -- check whether the subclient exists or not
action_bkp_set_backup_history()     -- opens the backup history of the backup set
action_bkp_set_restore_history()    -- opens the restore history of the backup set
add_subclient()                     -- add a subclient
open_subclient()                    -- open the subclient
action_backup()                     -- trigger the backup job for the subclient
job_id()                            -- returns the job id of the job started
submit_backup()                     -- submits a backup job of the specified type, full, incr, etc.
job_completion()                    -- returns the status of job upon completion, completed,
                                        killed, etc.
subclient_restore()                 -- opens the subclient content for restore browse

"""
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Helper.Imports import *
from Web.AdminConsole.FSPages.BackupsetLevel import BackupsetLevel
from Web.Common.page_object import PageService


class Backupset(BackupsetLevel):

    '''
    This class provides the function or operations that can be performed on the
    backup set  of the File System iDA on the AdminConsole
    '''

    @WebAction()
    def add_fs_subclient(self, scname, storage_policy, folders):
        """Adds a new subclient with the given name for the given storage policy
            with the specified content.

            scname          : a string, name of the subclient we need to add
            storage_policy   : a string, storage policy we want to associate with the client
            folders         : a file/folder, the files and folders,
                                we want to associate with this client
        """
        self.log.info("Creating a new subclient " + scname)
        if self.check_if_entity_exists("link", "Add subclient"):
            self.driver.find_element(By.LINK_TEXT, 
                "Add subclient").click()
            self.wait_for_completion()
            self.driver.find_element(By.NAME, 
                "subclientName").send_keys(scname)
            self.driver.find_element(By.XPATH, 
                "//span[@class='multiSelect inlineBlock']/button").click()
            (k, v), = storage_policy.items()
            self.driver.find_element(By.XPATH, 
                "//span[contains(text(), '" + v + "')]").click()
            self.wait_for_completion()
            self.driver.find_element(By.LINK_TEXT, 
                "Content").click()
            self.fill_form_by_id(
                "customPath", folders)
            self.driver.find_element(By.XPATH, 
                "//*[@id='subclient-content-tab']/div[1]/div[1]/div/i").click()
            self.wait_for_completion()
            self.driver.find_element(By.XPATH, 
                "//*[@id='createSubclientForm']/div[2]/button[2]").click()
            self.wait_for_completion()
        else:
            exp = "The Add Subclient option is not visible"
            self.log.error(exp)
            raise Exception(exp)

    @PageService()
    def action_backup(self, subclient, bkp_type):
        """Performs the given backup on the subclient.

            subclient : a string, name of the subclient
            bkp_type (BackupType) : type of backup to perform on this subclient,
                                         among the type in Backup.BackupType enum
        """
        self.log.info("Going to backup subclient " + subclient)
        self.driver.find_element(By.XPATH, 
            "//a[contains(text(),'" +
            subclient +
            "')]/../../div[4]/div/a[@class='dropdown-toggle']/span").click()
        if self.check_if_entity_exists("link", "Backup"):
            self.driver.find_element(By.XPATH, 
                "//a[contains(text(),'" +
                subclient +
                "')]/../../div[4]/div/ul/li[1]/a[contains(text(),'Backup')]").click()
            self.wait_for_completion()
            backup = Backup(self)
            retcode = backup.submit_backup(bkp_type)
            if not retcode[0]:
                return retcode[0], retcode[1], retcode[2]
            else:
                return True, retcode[1]
        else:
            exp = "There is no option to backup the collection"
            raise Exception(exp)

    @PageService()
    def submit_backup(self, backup_type):
        """Submits a backup job of the given type.

            backup_type (BackupType) : type of backup to perform, among the type in Backup.BackupType enum
        """
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @WebAction()
    def subclient_restore(self, subclient):
        """Opens the subclient content for restore browse.

            subclient   : a string, name of the subclient
        """
        self.log.info("Restoring the entire subclient " + subclient)
        if self.check_if_entity_exists("link", subclient):
            if self.check_if_entity_exists(
                    "xpath",
                    "//div/a[contains(text(),'" +
                    subclient +
                    "')]/ancestor::div[@class='ng-isolate-scope']/div[3]/span/a[\
                    contains(text(),'Restore')]"):
                self.driver.find_element(By.XPATH, 
                    "//div/a[contains(text(),'" +
                    subclient +
                    "')]/ancestor::div[@class='ng-isolate-scope']/div[3]/span/a[\
                    contains(text(),'Restore')]").click()
                self.wait_for_completion()
            else:
                exp = "The subclient " + subclient + " has not been backedup yet"
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no subclient with name " + subclient
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def delete_subclient(self, subclient_name):
        """
            Delete FS Subclient

            subclient_name : a string, name of the subclient
        """
        self.driver.find_element(By.LINK_TEXT, subclient_name).click()
        self.wait_for_completion()
        self.driver.find_element(By.XPATH, "//a[contains(text(), 'Delete')]").click()
        self.wait_for_completion()
        self.driver.find_element(By.XPATH, 
            "//input[@type='text']").send_keys("DELETE")
        self.driver.find_element(By.XPATH, 
            "//button[text() = 'Save']").click()
        self.wait_for_completion()

