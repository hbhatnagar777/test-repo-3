# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the Subclient Policies page in admin console

Class:
      SubclientPolicies()

Functions :

create_subclient_policy()  --- Method to add a new subclient policy

delete_subclient_policy()   --- Method to delete a subclient policy

select_subclient_policy()   --- Method to open a subclient policy

"""
import time

from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.table import Table
from selenium.webdriver.support.ui import Select
from Web.Common.page_object import PageService, WebAction


class SubclientPolicies:
    """ Class for Subclient Policies page """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)

    @WebAction()
    def create_subclient_policy(self,
                                subclient_policy_name,
                                agent_type,
                                storage_policy_name,
                                associations):
        """
        Method to create a subclient policy

        Args:

             subclient_policy_name (str) : Name of the subclient policy to be created
             agent_type (str)            : Type of subclient policy windows file system or unix file system
             storage_policy_name (str)   : Name of the storage policy to be associated with default subclient
             associations   (list)       : List of entities to be associated with this subclient policy
        Returns :
             None
        Raises:
            Exception :
             -- if fails to create a subclient policy
        """

        self._admin_console.log.info("Creating a subclient policy with name %s ", subclient_policy_name)
        self._admin_console.select_hyperlink("Add")
        self._admin_console.log.info("Populating subclient policy name")
        self._admin_console.fill_form_by_id("policyName", subclient_policy_name)
        self._admin_console.log.info("Selecting Agent type")
        self._admin_console.select_value_from_dropdown("Agent ", agent_type)
        self._admin_console.wait_for_completion()
        collapsed_items = self._admin_console.driver.find_elements(By.XPATH, "//span[@class='ng-binding']/i")
        for collapsed_elem in collapsed_items:
            if collapsed_elem.get_attribute('class') == 'glyphicon ng-scope glyphicon-chevron-right':
                collapsed_elem.click()
                self._admin_console.wait_for_completion()
        self._admin_console.log.info("Setting storage policy for default subclient")
        select = Select(self._admin_console.driver.find_element(By.XPATH, 
            "//span[contains(text(),'Default')]/../..//select "))
        select.select_by_visible_text(storage_policy_name)
        self._admin_console.log.info("Selecting the associations")
        while self._admin_console.check_if_entity_exists("xpath", "//span[@class='cv-tree-arrow collapsed']"):
            collapsed_elems = self._admin_console.driver.find_elements(By.XPATH, "//span[@class='cv-tree-arrow collapsed']")
            for elem in collapsed_elems:
                elem.click()
                time.sleep(2)
            self._admin_console.wait_for_completion()
        if associations['server_groups']:
            head = self._admin_console.driver.find_element(By.XPATH, 
                "//ul[@class='tree-view-wrapper ng-scope']/li")
            for value in associations['server_groups']:
                head.find_element(By.XPATH, 
                    "//label[contains(.,'" + value + "')]").click()
            self._admin_console.wait_for_completion()
        self._admin_console.log.info("Submitting the form")
        self._admin_console.submit_form()
        self._admin_console.check_error_message()

    @PageService()
    def delete_subclient_policy(self, new_subclient_policy_name):
        """
        Method to delete the subclient policy
        Args :
            new_subclient_policy_name (str): Name of the subclient policy to be deleted
        Returns:
            None
        Raises :
            if failed to delete the subclient policy

        """

        self._admin_console.log.info("Deleting the subclient policy")
        self.__table.access_action_item(new_subclient_policy_name, 'Delete')
        self._admin_console.click_button_using_text('Yes')
        notification = self._admin_console.get_notification()
        if notification == 'The policy was successfully deleted':
            self._admin_console.log.info("Subclient Policy was deleted successfully")
        else:
            raise Exception(notification)
        self._admin_console.check_error_message()

    @PageService()
    def select_subclient_policy(self, subclient_policy_name):
        """
        Method to open the subclient policy details

        Args:
          subclient_policy_name(str) : Name of the subclient policy to be opened

        Returns:
             None

        Raises :
            Exception :
             --- if failed to open the subclient policy details
        """

        self.__table.access_link(subclient_policy_name)
        self._admin_console.check_error_message()
