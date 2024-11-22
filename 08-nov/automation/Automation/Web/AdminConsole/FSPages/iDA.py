from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
all the iDA on the AdminConsole

Class:

    iDA() -> ClientDetails() -> Clients() -> Server() --
            -> _Navigator() -> LoginPage() -> AdminConsoleBase() -> object()

Functions:

check_if_backupset_exists()      -- check whether the backup set exists or not
backup_history()                 -- display backup history
restore_history()                -- display restore history
ida_data_management()            -- enable or disable the data management option
ida_data_recovery()              -- enable or disable the data recovery option
add_security_associations()      -- add security associations to the agent
open_backupset_instance()        -- Opens the backupset or instance of the iDataAgent
action_bkp_set_backup_history()  -- Opens the backup history of the backupset.
action_bkp_set_restore_history() -- Opens the restore history of the backupse / instance.

"""

from Web.AdminConsole.Helper.Imports import *
from Web.AdminConsole.FSPages.ClientDetails import ClientDetails


class iDA(ClientDetails):
    '''
    This class provides the function or operations that can be performed on
    all the iDA on the AdminConsole
    '''

    @WebAction()
    def check_if_backupset_exists(self, backupset):
        """Checks if the backup set exists

            backupset   : a string, name of the backupset we want to check if exists
        """
        self.log.info("Checking if the backup set exists")
        while True:
            if not self.check_if_entity_exists("link", backupset):
                if self.cv_table_next_button_exists():
                    if self.driver.find_element(By.XPATH, 
                            "//button[@ng-disabled='cantPageForward()']").is_enabled():
                        self.cv_table_click_next_button()
                        self.wait_for_completion()
                        continue
                    else:
                        exp = "There is no backup set named " + backupset
                        self.log.error(exp)
                        raise Exception(exp)
                else:
                    exp = "There is no backup set named " + backupset
                    self.log.error(exp)
                    raise Exception(exp)

    @WebAction()
    def backup_history(self):
        """Opens the backup history of the iDA.
        """
        self.log.info("Opening backup history of file system iDA of client")
        self.driver.find_element(By.LINK_TEXT, "Backup History").click()
        self.wait_for_completion()

    @WebAction()
    def restore_history(self):
        """Opens the restore history of the iDA.
        """
        self.log.info("Opening restore history of file system iDA of the client")
        self.driver.find_element(By.LINK_TEXT, "Restore History").click()
        self.wait_for_completion

    @WebAction()
    def ida_data_management(self):
        """Enables and disables the Data Management capability of the File System iDA.
        """
        self.log.info("Enable / Disable DataManagement in iDA")
        self.driver.find_element(By.XPATH, 
            "//cv-tile-component/div/div/div/ul/li[1]/span[2]/span").click()
        self.wait_for_completion()

    @WebAction()
    def ida_data_recovery(self):
        """Enables and disables the data recovery capability of the File System iDA.
        """
        self.log.info("Enable / Disable DataRecovery in iDA")
        self.driver.find_element(By.XPATH, 
            "//cv-tile-component/div/div/div/ul/li[2]/span[2]/span").click()
        self.wait_for_completion()

    @WebAction()
    def add_security_associations(self, userroles):
        """Adding associations to the agent.

            userroles : a string, roles we want to associate with the subclients
        """
        self.log.info("Adding security associations for iDA and subclients")
        if self.check_if_entity_exists("link", "Edit"):
            self.driver.find_element(By.LINK_TEXT, "Edit").click()
            self.wait_for_completion()
            for user in userroles.iterkeys():
                Select(self.driver.find_element(By.ID, 
                    "users")).select_by_visible_text(user)
                Select(self.driver.find_element(By.ID, "adduserId")
                       ).select_by_visible_text(userroles[user])
                self.driver.find_element(By.XPATH, 
                    "//body/div[8]/div/div/div[2]/div[1]/div/div/div[1]/button").click()
                self.wait_for_completion()
            self.driver.find_element(By.XPATH, 
                "//body/div[8]/div/div/div[2]/div[2]/button[2]").click()
            self.wait_for_completion()
        else:
            exp = "There is no option to edit the security associations"
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def open_backupset_instance(self, name):
        '''
        Opens the backupset or instance of the iDataAgent
        '''
        self.log.info("Opening the backupset or instance of the iDataAgent")
        while True:
            if self.check_if_entity_exists("link", name):
                self.driver.find_element(By.LINK_TEXT, name).click()
                self.wait_for_completion()
                break
            else:
                if self.cv_table_next_button_exists:
                    if self.driver.find_element(By.XPATH, 
                            "//button[@ng-disabled='cantPageForward()']").is_enabled():
                        self.cv_table_click_next_button()
                        self.wait_for_completion()
                    else:
                        exp = "There is no backupset / instance by this name"
                        self.log.error(exp)
                        raise Exception(exp)
                else:
                    exp = "There is no backupset / instance by this name"
                    self.log.error(exp)
                    raise Exception(exp)

    @WebAction()
    def action_bkp_set_backup_history(self, backupset):
        """Opens the backup history of the backupset.

            client   : a string, name of the backupset we need to open the backup history of
        """
        self.log.info("opening the backup history of the client")
        if self.check_if_entity_exists("link", backupset):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" + backupset + "']/../../div[3]/div/a/span").click()
            if self.check_if_entity_exists("link", "Backup History"):
                self.driver.find_element(By.XPATH, 
                    "//a[text()='" +
                    backupset +
                    "']/../../div[3]/div/ul/li[2]/a[text()='Backup History']").click()
                self.wait_for_completion()
            else:
                exp = "There is no option to view the backup history of the client " + backupset
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no client with the name " + backupset
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def action_bkp_set_restore_history(self, backupset):
        """Opens the restore history of the backupse / instance.
           client   : a string, name of the backupset / instance
                        we need to open the restore history of
        """
        self.log.info("opening the restore history of the client")
        if self.check_if_entity_exists("link", backupset):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" + backupset + "']/../../div[3]/div/a/span").click()
            if self.check_if_entity_exists("link", "Restore History"):
                self.driver.find_element(By.XPATH, 
                    "//a[text()='" +
                    backupset +
                    "']/../../div[3]/div/ul/li[3]/a[text()='Restore History']").click()
                self.wait_for_completion()
            else:
                exp = "There is no option to view the restore history of\
                the client " + backupset
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no client with the name " + backupset
            self.log.error(exp)
            raise Exception(exp)
