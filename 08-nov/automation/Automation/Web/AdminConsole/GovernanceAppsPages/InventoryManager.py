# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Inventory Manager page.


Classes:

    InventoryManager() ---> GovernanceApps() ---> object()


InventoryManager  --  This class contains all the methods for action in Inventory
    Manager page and is inherited by other classes to perform GDPR related actions

    Functions:

    add_inventory()          --  adds an inventory
    search_for_inventory()    -- Searches for an inventory
    navigate_to_inventory_details()    -- Navigates to inventory manager details page
    delete_inventory() -- Deletes a specific inventory
"""
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown


class InventoryManager(GovernanceApps):
    """
     This class contains all the methods for action in Inventory Manager page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__rtable = Rtable(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)

    @PageService()
    def add_inventory(self, inventory_name, index_server, name_server=None, guided_setup=False):
        """
        Adds an inventory

            :param inventory_name   (str)   --  Inventory name to be added
            :param index_server     (str)   --  Index Server to be selected
            :param name_server      (str)   --  Name server asset to be selected
            :param guided_setup     (bool)  --  True if it is a guided setup
                                                False if it is inventory manager page

            Raise:
                Exception if inventory addition failed
        """
        if not guided_setup:
            self.__rtable.access_toolbar_menu(self.__admin_console.props['label.inventorymanager.add'])
            self.__admin_console.wait_for_completion()
            self.__admin_console.fill_form_by_id("inventoryName", inventory_name)
            if name_server:
                self.__rdropdown.select_drop_down_values(drop_down_id="IdentityServersDropdown", values=[name_server])
            self.__rdropdown.select_drop_down_values(drop_down_id="IndexServersDropdown", values=[index_server])
        else:
            self.__admin_console.fill_form_by_id("inventoryName", inventory_name)
        self.__rmodal_dialog.click_submit()
        self.__admin_console.check_error_message()

    @WebAction()
    def search_for_inventory(self, inventory_name):
        """
        Searches for an inventory

            Args:
                inventory_name (str)  - Inventory name to be searched for

            Returns True/False based on the presence of the Inventory
        """
        return self.__rtable.is_entity_present_in_column(
            self.__admin_console.props['label.name'], inventory_name)

    @PageService()
    def navigate_to_inventory_details(self, inventory_name):
        """
        Navigates to inventory manager details page

            Args:
                inventory_name (str)  - Inventory name details to be navigated

        """
        self.__rtable.access_action_item(
            inventory_name, self.__admin_console.props['label.details'])

    @PageService()
    def delete_inventory(self, inventory_name):
        """
        Deletes an inventory

            Args:
                inventory_name (str)  - Inventory name to be deleted

            Raise:
                Exception if inventory deletion failed
        """
        self.__rtable.access_action_item(
            inventory_name, self.__admin_console.props['label.delete'])
        self.__rmodal_dialog.click_submit()
        self.__admin_console.check_error_message()
