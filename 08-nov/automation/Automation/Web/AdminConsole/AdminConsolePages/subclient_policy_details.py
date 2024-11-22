# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the Subclient Policy details page in
admin console

Class:
      SubclientPolicyDetails()

Functions :

edit_subclient_policy_name()            --- Method to edit the subclient policy name

edit_subclient_policy_association()     --- Method to edit the subclient policy associations

add_subclient()                         --- Method to add subclient to the subclient policy

delete_subclient()                      --- Method to delete the subclient from subclient policy details page

open_subclient()                        --- Method to open a subclient details from subclient policy

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService, WebAction


class SubclientPolicyDetails:
    """Class for Subclient Policy Details page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)

    @WebAction()
    def edit_subclient_policy_name(self, subclient_policy_name, new_subclient_policy_name):
        """
        Method to change the subclient policy name

        Args:
         subclient_policy_name (str): subclient policy name to be changed
         new_subclient_policy_name (str):name of the subclient policy after modification

        Returns:
            None
        Raises :
             Exception:
              -- if failed to change the subclient policy name
        """

        self._admin_console.log.info("Editing the subclient policy name : %s", subclient_policy_name)
        if self._admin_console.check_if_entity_exists("xpath", "//h1[@id]"):
            name = self._admin_console.driver.find_element(By.XPATH, "//h1[@id]")
        else:
            raise Exception("Unable to edit the subclient policy name")
        name.click()
        name.clear()
        name.send_keys(new_subclient_policy_name)
        self._admin_console.driver.find_element(By.XPATH, "//cv-tile-component[@data-loader]/div/div[3]/span").click()
        self._admin_console.wait_for_completion()
        self._admin_console.log.info("Subclient policy name was edited successfully")
        self._admin_console.check_error_message()

    @WebAction()
    def edit_subclient_policy_association(self, new_associations):
        """
        Method to edit the subclient policy association
        Args:
            new_associations (list) : New list of entities to be associated with this subclient policy

        Returns:
            None
        Raises:
            Exception:
            -- if failed to edit the subclient policy association
        """

        self._admin_console.log.info("Editing the subclient policy associations")

        self._admin_console.driver.find_element(By.XPATH, "//a[@class='page-details-box-links ng-scope']").click()
        self._admin_console.wait_for_completion()
        self._admin_console.checkbox_select("dissociateBackupSet")
        self._admin_console.log.info("dissociate backup set check box option was selected successfully")
        self._admin_console.log.info("Setting the new associations")
        while self._admin_console.check_if_entity_exists("xpath", "//span[@class='cv-tree-arrow collapsed']"):
            collapsed_elems = self._admin_console.driver.find_elements(By.XPATH, "//span[@class='cv-tree-arrow collapsed']")
            for elem in collapsed_elems:
                elem.click()
                self._admin_console.wait_for_completion()
        if new_associations['server_groups']:
            head = self._admin_console.driver.find_element(By.XPATH, 
                "//ul[@class='tree-view-wrapper ng-scope']/li")
            for value in new_associations['server_groups']:
                head.find_element(By.XPATH, 
                    "//label[contains(.,'" + value + "')]").click()
            self._admin_console.wait_for_completion()
        self._admin_console.log.info("associations were set successfully")
        self._admin_console.checkbox_select("showSelected")
        self._admin_console.log.info("Show selected check box option was selected successfully")
        self._admin_console.click_button("Save")
        self._admin_console.log.info("Subclient policy association was edited successfully.")
        self._admin_console.check_error_message()

    @WebAction()
    def add_subclient(self, subclient_name, storage_policy_name, subclient_path):
        """
        Method to add a new subclient to the subclient policy
        Args:
             subclient_name (str)        : subclient name to be added newly to the subclient policy
             storage_policy_name(str):  Storage policy name to be associated with the new subclient
             subclient_path(str)        : path to the subclient
        Returns:
            None
        Raises :
           Exception:
             -- if failed to add a new subclient policy
        """

        self._admin_console.log.info("Adding a new subclient to this subclient policy")
        self._admin_console.select_hyperlink("Add")
        self._admin_console.fill_form_by_id("subclientName", subclient_name)
        self._admin_console.select_value_from_dropdown("primaryStorage", storage_policy_name)
        self._admin_console.select_hyperlink("Content")
        path = self._admin_console.driver.find_element(By.XPATH, "//input[@placeholder='Enter custom path']")
        path.clear()
        path.send_keys(subclient_path)
        self._admin_console.wait_for_completion()
        self._admin_console.driver.find_element(By.XPATH, "//i[@title='Add'][@data-ng-click='addCustomPath(0)']").click()
        self._admin_console.wait_for_completion()
        self._admin_console.click_button("Save")
        self._admin_console.log.info("Subclient was created successfully.")
        self._admin_console.check_error_message()

    @PageService()
    def delete_subclient(self, subclient_name):
        """
        Deletes the subclient policy from the subclient policy details page

        Returns:
            None

        Raises:
            Exception:
                -- if fails to delete the subclient policy
        """
        self._admin_console.log.info("Deleting the subclient from details page")
        self.__table.access_link_by_column(subclient_name, 'Delete')
        self._admin_console.type_text_and_save("DELETE")
        self._admin_console.check_error_message()

    @PageService()
    def open_subclient(self, subclient):
        """
        Opens the subclient with the given name  --- refer backupset page

        Args:
            subclient (str): name of the subclient

        Returns:
            None
        Raises:
            Exception:There is no subclient with the name

        """
        self.__table.access_link(subclient)
        self._admin_console.check_error_message()
