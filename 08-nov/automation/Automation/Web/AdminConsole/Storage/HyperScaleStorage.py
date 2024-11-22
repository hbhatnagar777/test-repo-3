# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Hyperscale storage page in AdminConsole
HyperScaleStorage : This class provides methods for disk storage related operations

HyperScaleStorage:

    add_hyperscale_storagepool()      --  adds a new hyperscale storagepool

    list_hyperscale_storagepool()     --  returns a list of all hyperscale storagepools

    access_hyperscale_storagepool()   --  opens a hyperscale storagepool

    delete_hyperscale_storagepool()   --  removes a hyperscale storagepool

    reconfigure_hyperscale_storagepool() -- reconfigure the storagepool

    storagepool_health_status() -- storagepool health check
"""

from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import DropDown
from Web.Common.page_object import PageService
from Web.Common.exceptions import CVWebAutomationException

class HyperScaleStorage:
    """
    This class provides the function or operations that can be
    performed on the HyperScale Storage Page of the Admin Console
    """

    def __init__(self, admin_console):
        """
        Initialization method for HyperScaleStorage Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__props = self.__admin_console.props
        self.__table = Table(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)
        self.__storagepool_table_details = None

    @PageService()
    def add_hyperscale_storagepool(self, hyperscale_storagepool_name, media_agents):
        """
        To add a new disk storage

        Args:
            hyperscale_storagepool_name (str)     -- Name of the disk storage to be created

            media_agents  (str)       -- Media agent to create storage on

        ** Note : Atleast three media Agent should present,
         MediaAgent should be available for pool creation
        """

        self.__admin_console.select_hyperlink(self.__props['action.add'])
        self.__admin_console.fill_form_by_id("storagePoolName", hyperscale_storagepool_name)
        self.__drop_down.select_drop_down_values(drop_down_id='MediaAgents', values=media_agents)
        self.__admin_console.click_button(self.__props['action.save'])
        self.__admin_console.check_error_message()

    @PageService()
    def list_hyperscale_storagepool(self):
        """
        Get the of all the HyperScale Storagepool in the form of a list

            Returns:
               list --  all HyperScale Storagepool
        """
        try:
            return self.__table.get_column_data(self.__props['Name'])
        except ValueError:
            return []

    @PageService()
    def access_hyperscale_storagepool(self, hyperscale_storagepool_name):
        """
        selects the HyperScale Storagepool with the given name

        Args:
            hyperscale_storagepool_name    (str)   -- Name of the HyperScale Storagepool to be accessed
        """
        self.__table.access_link(hyperscale_storagepool_name)

    @PageService()
    def delete_hyperscale_storagepool(self, hyperscale_storagepool_name):
        """
        Deletes the HyperScale Storagepool with the given name

        Args:
            hyperscale_storagepool_name (str) - name of the storagepool to be removed
        """
        self.__table.access_action_item(hyperscale_storagepool_name, self.__props['action.delete'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def reconfigure_hyperscale_storagepool(self,hyperscale_storagepool_name):
        """
                Reconfigure the HyperScale Storagepool with the given name

                Args:
                    hyperscale_storagepool_name (str) - name of the storagepool to get reconfigured
        """
        self.__table.access_action_item(hyperscale_storagepool_name, self.__props['action.reconfigure'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def storagepool_health_status(self, hyperscale_storagepool_name):
        """Checks storagepool is present iff present

        Args:
            hyperscale_storagepool_name (str) - name of the storagepool

        Return (str) : Status - online/offline
        """

        if not self.__table.is_entity_present_in_column('Name', hyperscale_storagepool_name):
            raise CVWebAutomationException(f"StoragePool : {hyperscale_storagepool_name} is not Present")

        self.__storagepool_table_details = self.__table.get_table_data()
        return self.__storagepool_table_details['Status'][self.__storagepool_table_details['Name'].index(hyperscale_storagepool_name)]



