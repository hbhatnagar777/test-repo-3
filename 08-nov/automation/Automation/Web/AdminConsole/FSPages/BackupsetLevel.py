# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
backup set / instance level of the all the iDAs on the AdminConsole

Class:

    BackupsetLevel() -> iDA() -> ClientDetails() -> Clients() --
        -> Server() -> _Navigator() -> LoginPage() -> AdminConsoleBase() -> object()

Functions:

check_if_subclient_exists()         -- check whether the subclient exists or not
action_bkp_set_backup_history()     -- opens the backup history of the backup set
action_bkp_set_restore_history()    -- opens the restore history of the backup set
add_subclient()                     -- add a subclient
open_subclient()                    -- open the subclient
action_backup()                     -- trigger the backup job for the subclient
job_id()                            -- returns the job id of the job started
submit_backup()                     -- submits a backup job of the specified type, full, incr, etc.
job_completion_status()             -- returns the status of job upon completion,
                                         completed, killed, etc.
subclient_restore()                 -- opens the subclient content for restore browse

"""
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Helper.Imports import *
from Web.AdminConsole.FSPages.iDA import iDA
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.page_object import PageService


class BackupsetLevel(iDA):
    '''
    This class provides the function or operations that can be performed on the
    backup set / instance level of the all the iDAs on the AdminConsole
    '''
    @WebAction()
    def check_if_subclient_exists(self, subclient):
        """Checks if the sub client exists.

            subclient   : a string, name of the subclient
        """
        self.log.info("Checking if the sub client exists")
        while True:
            if not self.check_if_entity_exists("link", subclient):
                if self.cv_table_next_button_exists():
                    if self.driver.find_element(By.XPATH, 
                            "//button[@ng-disabled='cantPageForward()']").is_enabled():
                        self.cv_table_click_next_button()
                        self.wait_for_completion()
                        continue
                    else:
                        exp = "There is no sub client named " + subclient
                        self.log.error(exp)
                        raise Exception(exp)
                else:
                    exp = "There is no sub client named " + subclient
                    self.log.error(exp)
                    raise Exception(exp)

    @WebAction()
    def action_backup_history(self, subclient):
        """Opens the backup history of the subclient.

            client   : a string, name of the subclient we need to open the backup history of
        """
        self.log.info("opening the backup history of the client")
        if self.check_if_entity_exists("link", subclient):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" + subclient + "']/../../div[3]/div/a/span").click()
            if self.check_if_entity_exists("link", "Backup History"):
                self.driver.find_element(By.XPATH, 
                    "//a[text()='" +
                    subclient +
                    "']/../../div[3]/div/ul/li[2]/a[text()='Backup History']").click()
                self.wait_for_completion()
            else:
                exp = "There is no option to view the backup history of the client " + subclient
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no client with the name " + subclient
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def action_restore_history(self, subclient):
        """Opens the restore history of the subclient.

            client   : a string, name of the subclient we need to open the restore history of
        """
        self.log.info("opening the restore history of the client")
        if self.check_if_entity_exists("link", subclient):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" + subclient + "']/../../div[3]/div/a/span").click()
            if self.check_if_entity_exists("link", "Restore History"):
                self.driver.find_element(By.XPATH, 
                    "//a[text()='" +
                    subclient +
                    "']/../../div[3]/div/ul/li[3]/a[text()='Restore History']").click()
                self.wait_for_completion()
            else:
                exp = "There is no option to view the restore history\
                of the client " + subclient
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no client with the name " + subclient
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def open_subclient(self, subclient):
        """Opens the subclient with the given name.

            Subclient   : a string, name of the subclient
        """
        self.log.info("Opening subclient " + subclient)
        if self.check_if_entity_exists("link", subclient):
            self.driver.find_element(By.LINK_TEXT, subclient).click()
            self.wait_for_completion()
        else:
            exp = "There is no subclient with the name " + subclient
            self.log.error(exp)
            raise Exception(exp)

    @PageService()
    def submit_backup(self, backup_type):
        """Submits a backup job of the given type.

            backup_type (BackupType)  :  type of backup to perform in Backup.BackupType enum

            Returns (int) : job id
        """
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @WebAction()
    def job_completion_status(self, job_id, retry=2):
        """This definition opens the job details page and keeps pinging the page,
            until the status of the job turns to completed, failed,
            completed w/ one or more errors or pending.

            job_id  : an int, id of the job we want to get the status of
            retry   : an int, number of times to retry before killing the job; default = 2
        """
        self.log.info("Checking for job status")
        self.navigate_to_jobs()
        job_obj = Jobs(self.driver)
        ret = job_obj.job_completion(job_id)
        status = ret[1]['Status']
        if status in [
                "Completed",
                "Failed",
                "Completed w/ one or more errors",
                "Pending",
                "Killed"]:
            if status in [
                    "Completed",
                    "Completed w/ one or more errors"]:
                return True, status, ret[1]
            elif status in ["Failed", "Killed"]:
                exp = "Status if failed or killed"
                raise Exception(exp)
        return True, status

    @WebAction()
    def subclient_restore(self, subclient):
        """Opens the subclient content for restore browse.

            subclient   : a string, name of the subclient=
        """
        self.log.info("Restoring the entire subclient " + subclient)
        if self.check_if_entity_exists("link", subclient):
            if self.check_if_entity_exists(
                    "xpath",
                    "//div/a[contains(text(),'" +
                    subclient +
                    "')]/ancestor::div[@class='ng-isolate-scope'\
                    ]/div[3]/span/a[contains(text(),'Restore')]"):
                self.driver.find_element(By.XPATH, 
                    "//div/a[contains(text(),'" +
                    subclient +
                    "')]/ancestor::div[@class='ng-isolate-scope'\
                    ]/div[3]/span/a[contains(text(),'Restore')]").click()
                self.wait_for_completion()
            else:
                exp = "The subclient " + subclient + " has not been backedup yet"
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no subclient with name " + subclient
            self.log.error(exp)
            raise Exception(exp)
