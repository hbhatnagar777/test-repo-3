# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the Subclient Policy subclient details page in
admin console

Class:
      SubclientPolicySubclientDetails()

Functions :

edit_subclient_name()                   --- Method to edit the subclient name inside a subclient policy

edit_subclient_content()                --- Method to edit the subclient content associated to a subclient policy

"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import WebAction


class SubclientPolicySubclientDetails:
    """ Class for Subclient Policy subclient details page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console

    @WebAction()
    def edit_subclient_name(self, subclient_name, new_subclient_name):
        """
        Method to change the subclient policy name

        Args:
         subclient_name (str): subclient name to be changed
         new_subclient_name (str):name of the subclient after modification

        Returns:
            None
        Raises :
             Exception:
              -- if failed to change the subclient  name
        """
        self._admin_console.log.info("Editing the subclient  name: %s", subclient_name)
        if self._admin_console.check_if_entity_exists("xpath", "//h1[@id]"):
            name = self._admin_console.driver.find_element(By.XPATH, "//h1[@id]")
        else:
            raise Exception("Unable to edit the subclient name")
        name.click()
        name.clear()
        name.send_keys(new_subclient_name)
        self._admin_console.driver.find_element(By.XPATH, "//span[contains(@title,'Security')]").click()
        self._admin_console.wait_for_completion()
        self._admin_console.log.info("subclient name was edited successfully")
        self._admin_console.check_error_message()

    @WebAction()
    def edit_subclient_content(self, subclient_path, new_subclient_path):
        """
        Method to edit the subclient content

        Args:
            subclient_path (str): subclient path before modification
            new_subclient_path (str): subclient path after modification

        Returns:
            None
        Raises :
             Exception:
              -- if failed to change the subclient  name
        """
        self._admin_console.log.info("Editing the subclient  path: %s", subclient_path)
        self._admin_console.driver.find_element(By.XPATH, 
            "//a[@data-ng-click='manageSubclientContent()' and text()='Edit']").click()
        self._admin_console.select_hyperlink("Content")
        path = self._admin_console.driver.find_element(By.XPATH, "//input[@placeholder='Enter custom path']")
        path.clear()
        path.send_keys(new_subclient_path)
        self._admin_console.wait_for_completion()
        self._admin_console.driver.find_element(By.XPATH, "//i[@title='Add'][@data-ng-click='addCustomPath(0)']").click()
        self._admin_console.wait_for_completion()
        self._admin_console.click_button("OK")
        self._admin_console.log.info("Subclient content was edited successfully.")
        self._admin_console.check_error_message()

    @WebAction()
    def edit_storage_policy(self, storage_policy_name, new_storage_policy_name):
        """
        Method to change the storage policy name for subclient

         Args:
         storage_policy_name (str): storage policy name to be changed
         new_storage_policy_name (str):name of the storage policy after modification

        Returns:
            None
        Raises :
             Exception:
              -- if failed to change the subclient  name
        """
        self._admin_console.log.info("Changing the subclient storage policy from %s to %s", storage_policy_name,
                      new_storage_policy_name)
        self._admin_console.select_configuration_tab()
        self._admin_console.driver.find_element(By.XPATH, "//a[@data-ng-click='editPolicies()']").click()
        self._admin_console.cv_single_select('Storage policy', new_storage_policy_name)
        self._admin_console.click_button("Save")
        self._admin_console.log.info("Storage policy for the subclient is modified successfully")
        self._admin_console.check_error_message()
