# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to storage policies in AdminConsole
StoragePolicies : This class provides methods for storage policies related operations

StoragePolicies:

    select_storage_policy()     -- Selects the storage pool with the given name

    add_storage_policy()        -- To create a new storage policy

    delete_storage_policy()     -- To delete a storage policy

"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService, WebAction


class StoragePolicies:
    """
    This class provides the function or operations that can be
    performed on the Storage policies Page of the Admin Console
    """

    def __init__(self, admin_console):
        self.__table = Table(admin_console)
        self.admin_console = admin_console

    @PageService()
    def select_storage_policy(self, storage_policy):
        """
        selects the storage pool with the given name

        Args:
            storage_policy    (str)   -- Name of the storage policy to be selected

        """
        self.__table.access_link(storage_policy)

    @PageService()
    def add_storage_policy(
            self,
            policy_name=None,
            storage_pool=None,
            retention='30'):
        """
        To create a new storage policy

        Args:
            policy_name     (str)   --  Name for the storage policy to be created

            storage_pool    (str)   --  Storage pool for the storage policy

            retention       (str)   --  Retention period for the policy created (Infinite|Number of days)
                                            default: 30

        """
        self.admin_console.select_hyperlink('Add')
        self.admin_console.fill_form_by_id('hostName', policy_name)
        self.admin_console.select_value_from_dropdown('repeatSelect', storage_pool)

        if "infinite" in retention.lower():
            self.admin_console.checkbox_select('isInfiniteCheck')
        else:
            self.admin_console.fill_form_by_id('input', retention)

        self.admin_console.submit_form()
        self.admin_console.check_error_message()

    @WebAction()
    def delete_storage_policy(self, policy_name):
        """
        To delete a storage policy

        Args:
            policy_name     (str)   -- Name of the storage policy to be deleted

        """
        self.__table.access_action_item(policy_name, 'Delete')
        self.admin_console.driver.find_element(By.XPATH, "//button[text()='Yes'][@ng-click='yes()']").click()
        self.admin_console.check_error_message()
