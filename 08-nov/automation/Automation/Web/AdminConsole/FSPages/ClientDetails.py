# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions or operations that can be performed on the
a selected client on the AdminConsole

Class:

    ClientDetails() -> AllClients() -> Server() -> _Navigator() --
        -> LoginPage() -> AdminConsoleBase() -> object()

Functions:

check_if_agent_exists()      -- check whether the agent exists or not
jobs()                       -- opens the jobs page of the client
action_add_backupset()       -- add a backup set to the client
action_add_instance()        -- add an instance for database agents
action_backup_history()      -- opens the backup history of the client
action_restore_history()     -- opens the restore history of the client
open_agent()                 -- opens the file system agent of the client
client_data_management()     -- enable or disable the client data management option
client_data_recovery()       -- enable or disable the client data recovery option
client_info()                -- displays the client information
add_client_security()        -- adds security associations to the client
oracle_instance()            -- Add an instance for database agents
action_add_oracle_instance() -- Adds an oracle instance
action_add_hana_instance()   -- Adds a new SAP HANA instance
add_client_security()        -- Adds security associations
release_license()            -- Releases license for the client
install_software_on_client() -- Install the selected packages on the currently open client
delete_client()              -- Deletes the client


"""

from Web.AdminConsole.Helper.Imports import *
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.ServerGroups import ServerGroups


class ClientDetails(Servers, ServerGroups):
    '''
    This class provides the functions or operations that can be performed on the
    a selected client on the AdminConsole
    '''
    @WebAction()
    def check_if_agent_exists(self, agent):
        """Checks if the agent exists.

            agent   : a string, name of the agent we want to check if exists
        """
        self.self.log.info("Checking if the agent exists")
        while True:
            if not self.check_if_entity_exists("link", agent):
                if self.cv_table_next_button_exists():
                    if self.driver.find_element(By.XPATH, 
                            "//button[@ng-disabled='cantPageForward()']").is_enabled():
                        self.cv_table_click_next_button()
                        self.wait_for_completion()
                        continue
                    else:
                        exp = "There is no agent named " + agent
                        self.log.error(exp)
                        raise Exception(exp)
                else:
                    exp = "There is no agent named " + agent
                    self.log.error(exp)
                    raise Exception(exp)

    @WebAction()
    def jobs(self):
        """Opens the jobs page of the client.
        """
        self.log.info("Opening jobs of client")
        self.driver.find_element(By.LINK_TEXT, "jobs").click()
        self.wait_for_completion()

    @WebAction()
    def action_add_backupset(self, backupset):
        """Adds a backupset to the client.

            backupset   : a string, name of the backupset we want to associate with a client
        """
        self.log.info("Adding new backupset to the file system agent")
        self.driver.find_element(By.XPATH, 
            "//a[text()='File System']/../../div[3]/div/a").click()
        if self.check_if_entity_exists("link", "Add BackupSet"):
            self.driver.find_element(By.XPATH, 
                "//a[text()='File System']/../../div[3]/div/ul/li[1]/a[\
                text()='Add BackupSet']").click()
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
    def action_add_instance(self, agent):
        '''
        Adds a new instance to the agent
        '''
        self.log.info("Adding a new instance to the agent")
        if self.check_if_entity_exists("link", agent):
            self.driver.find_element(By.XPATH, 
                "//a[contains(text(),'"+agent+"')]/../../div[3]/div/a/span").click()
            if self.check_if_entity_exists("link", "Add instance"):
                self.driver.find_element(By.XPATH, 
                    "//a[contains(text(),'"+agent+"')]/../../div[3]/div/ul/li[1]\
                    /a[contains(text(),'Add instance')]").click()
                self.wait_for_completion()


    @WebAction()
    def oracle_instance(
            self,
            instance,
            oracle_home,
            osusername,
            osuserpassword,
            dbusername,
            dbpassword,
            instance_name,
            db_storage_policy,
            log_storage_policy):
        """Add an instance for database agents.

            instance   : a string, instance to be added
        """
        self.log.info("Add an instance for the database agent")
        self.driver.find_element(By.ID, "instanceName").send_keys(instance)
        self.driver.find_element(By.ID, "oracleHome").send_keys(oracle_home)
        self.driver.find_element(By.ID, "osUserName").send_keys(osusername)
        if self.check_if_entity_exists("id", "osUserPassword"):
            self.driver.find_element(By.ID, 
                "osUserPassword").send_keys(osuserpassword)
        self.driver.find_element(By.ID, "dbUserName").send_keys(dbusername)
        self.driver.find_element(By.ID, "dbPassword").send_keys(dbpassword)
        self.driver.find_element(By.ID, 
            "dbInstanceName").send_keys(instance_name)
        Select(self.driver.find_element(By.ID, "DBStoragePolicy")
              ).select_by_visible_text(db_storage_policy)
        Select(self.driver.find_element(By.ID, "LogStoragePolicy")
              ).select_by_visible_text(log_storage_policy)
        self.driver.find_element(By.XPATH, 
            "//form/div[2]/button[contains(text(),'OK')]").click()
        self.wait_for_completion

    @WebAction()
    def action_add_oracle_instance(self,
                                   instance,
                                   oracle_home,
                                   osusername,
                                   osuserpassword,
                                   dbusername,
                                   dbpassword,
                                   instance_name,
                                   db_storage_policy,
                                   log_storage_policy):
        """Adds an oracle instance"""
        self.log.info("Add an oracle instance")
        ret = self.action_add_instance("Oracle")
        if ret:
            ret_val = self.oracle_instance(
                instance, oracle_home, osusername, osuserpassword,\
                dbusername, dbpassword, instance_name, db_storage_policy,\
                log_storage_policy)
            if not ret_val:
                return ret_val[0], ret_val[1], ret_val[2]
        else:
            exp = "There is no option to add an instance"
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def action_add_hana_instance(self,
                                 client_name,
                                 instance_name,
                                 instance_no,
                                 os_user,
                                 server,
                                 sql_loc,
                                 users,
                                 data_sp,
                                 log_sp,
                                 command_sp,
                                 store_key=None,
                                 db_user=None,
                                 db_password=None):

        """Adds a new SAP HANA instance"""

        self.log.info("Adding a new SAP HANA instance")
        ret_val = self.action_add_instance("SAP HANA")
        if ret_val[0]:
            ret = self.sap_hana_client(
                client_name,
                instance_name,
                instance_no,
                os_user,
                server,
                sql_loc,
                users,
                data_sp,
                log_sp,
                command_sp,
                store_key,
                db_user,
                db_password)
            if not ret[0]:
                return ret[0], ret[1], ret[2]
        else:
            exp = "There is no option to add an instance"
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def action_backup_history(self, client='File System'):
        """Opens the backup history.

            client   : a string, Attribute we want to open backup history of
                            default = 'File System'
        """
        self.log.info("opening the backup history of the client")
        self.driver.find_element(By.XPATH, 
            "//a[text()='" + client + "']/../../div[3]/div/a").click()
        if self.check_if_entity_exists("link", "Backup History"):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" +
                client +
                "']/../../div[3]/div/ul/li[2]/a[text()='Backup History']").click()
            self.wait_for_completion()

    @WebAction()
    def action_restore_history(self, client='File System'):
        """Opens the restore history.

            client   : a string, Attribute we want to open restore history of
                            default = 'File System'
        """
        self.log.info("opening the restore history of the client")
        self.driver.find_element(By.XPATH, 
            "//a[text()='" + client + "']/../../div[3]/div/a").click()
        if self.check_if_entity_exists("link", "Restore History"):
            self.driver.find_element(By.XPATH, 
                "//a[text()='" +
                client +
                "']/../../div[3]/div/ul/li[3]/a[text()='Restore History']").click()
            self.wait_for_completion()

    @WebAction()
    def open_agent(self, agent_type):
        """Opens the file system agent of the client.

            agent_type   : a string, agent we want to open of the client
        """
        self.log.info("Opening the file system agent")
        self.driver.find_element(By.LINK_TEXT, agent_type).click()
        self.wait_for_completion()

    @WebAction()
    def client_data_management(self):
        """Enables and disables the data management capability of the client.
        """
        self.log.info("Enable / Disable DataManagement in Client")
        self.driver.find_element(By.XPATH, 
            "//cv-tile-component/div/div/div/ul/li[1]/span[2]/span").click()
        self.wait_for_completion()

    @WebAction()
    def client_data_recovery(self):
        """Enables and disables the data recovery capability of the client.
        """
        self.log.info("Enable / Disable DataRecovery in Client")
        self.driver.find_element(By.XPATH, 
            "//cv-tile-component/div/div/div/ul/li[2]/span[2]/span").click()
        self.wait_for_completion()

    @WebAction()
    def client_info(self):
        """Gathers the information about the client like cient name,
            hostname, commserve hostname and whether it is physical/virtual client.
        """
        self.log.info("Getting the client information")
        client_info = {}
        items = self.driver.find_elements(By.XPATH, 
            "//div[1]/cv-tile-component[1]/div/div/div/ul/li")
        total = len(items)
        for index in range(1, total + 1):
            key = self.driver.find_element(By.XPATH, 
                "//div[1]/cv-tile-component[1]/div/div/div/ul/li["
                + str(index) + "]/span[1]").text
            val = self.driver.find_element(By.XPATH, 
                "//div[1]/cv-tile-component[1]/div/div/div/ul/li["
                + str(index) + "]/span[2]").text
            client_info[key] = val
        self.log.info(client_info)

    @WebAction()
    def add_client_security(self, userroles, owner, owner_group):
        """Adds security associations.

            userroles   : a string, roles we want to associate with the client
            owner       : a string, owner of the client
            owner_group  : a string, ownergroup this client belongs to
        """

        self.log.info("Adding security associations")

        if self.check_if_entity_exists("link", "Edit"):
            self.driver.find_element(By.LINK_TEXT, "Edit").click()
            self.wait_for_completion()
            for user in userroles.iterkeys():
                Select(self.driver.find_element(By.ID, 
                    "users")).select_by_visible_text(user)
                Select(self.driver.find_element(By.ID, "adduserId")
                      ).select_by_visible_text(userroles[user])
                self.driver.find_element(By.XPATH, 
                    "//div[2]/div[1]/div/cv-tabset-component/\
                    div/div[1]/div/div[1]/button").click()
            self.driver.find_element(By.XPATH, 
                "//body/div[8]/div/div/div[2]/div[1]/div/\
                cv-tabset-component/ul/li[2]/a").click()
            self.driver.find_element(By.ID, 
                "usersDescription").send_keys(owner)
            self.driver.find_element(By.ID, 
                "usersGroupDescription").send_keys(owner_group)
            self.driver.find_element(By.XPATH, 
                "//button[contains(text(),'Save')]").click()
            self.wait_for_completion()
            if self.check_if_entity_exists(
                    "xpath",
                    "//div[@class='ng-isolate-scope \
                    dr-notification-container bottom right']/div"):
                exp = self.driver.find_element(By.XPATH, 
                    "//div[2]/div/div[2]/div[2]/h3").text
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no option to edit the security associations"
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def delete_client(self):
        """
            Deletes the client
        """
        self.log.info("Deleting the client")
        if self.check_if_entity_exists("link", "Delete client"):
            self.driver.find_element(By.LINK_TEXT, "Delete client").click()
            self.wait_for_completion()
            self.driver.find_element(By.XPATH, 
                "//div/div[3]/button[contains(text(),'Yes')]").click()
            self.wait_for_completion()
            if self.check_if_entity_exists(
                    "xpath",
                    "//div[4]/div/div[@class='growl-item alert \
                    ng-scope alert-error alert-danger']"):
                exp = self.driver.find_element(By.XPATH, 
                    "//div[4]/div/div[\
                    @class='growl-item alert ng-scope alert-error alert-danger']/div/div").text
                self.log.error(exp)
                raise Exception(exp)
        else:
            exp = "There is no option to delete the client"
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def install_software_on_client(self, packages):
        """
            Install the selected packages on the currently open client
            packages    : list, contains the list of all packages to be installed on the client
        """
        self.log.info("Installing the given packages on the client")
        if self.check_if_entity_exists("link", "Install software"):
            self.driver.find_element(By.LINK_TEXT, 
                "Install software").click()
            self.wait_for_completion()
            for package in packages:
                self.driver.find_element(By.XPATH, 
                    "//div[@class='dlo-inline-wrapper']//label[\
                    contains(text(),'" + package + "')]").click()
            self.driver.find_element(By.XPATH, 
                "//form/div[@class='button-container']/button[2]").click()
            self.wait_for_completion()
        else:
            exp = "There is no option to install additional packages in the client"
            self.log.error(exp)
            raise Exception(exp)

    @WebAction()
    def release_license(self, packages):
        """
            Releases license for the client
            packages    : list, list of all packages whose license has to be released
        """
        self.log.info("Releasing license for the client")
        if self.check_if_entity_exists("link", "Release license"):
            self.driver.find_element(By.LINK_TEXT, 
                "Release license").click()
            self.wait_for_completion()
            for package in packages:
                self.driver.find_element(By.XPATH, 
                    "//div[@class='dlo-inline-wrapper']//label[\
                    contains(text(),'" + package + "')]").click()
            self.driver.find_element(By.XPATH, 
                "//form/div[@class='button-container']/button[2]").click()
            self.wait_for_completion()
        else:
            exp = "there is no option to release the license of the packages"
            self.log.error(exp)
            raise exp
