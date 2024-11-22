from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
HyperScaleStorageDetails page of the AdminConsole

HyperScaleStorageDetails:

    __click_edit_symbol()           -- Click edits symbol for key management server

    __click_ok_symbol()             -- Click ok symbol for key management server

    add_nodes()                     -- To add a nodes to an existing HyperScaleStroagePool

    reconfigure_add_nodes()         -- add nodes operation reconfigure storagepool

    hyperscale_Library_info()       -- To get the details of hyperscale Library

    refresh_node()               -- refresh node of hyperscale storagepool

    list_nodes()                    -- Get all the nodes of  hyperscale storagepool in the form of a list

    nodes_health_status()           -- returns health status of a node

    access_hyperscale_node()        -- access the hyperscale node

    edit_key_management_server()    -- Edits the existing key management server

    encrypt_storage()               -- To encrypt the storage on the selected disk

    list_associated_plans()         -- Get all the associated plans to the hyperscale storagepool in the form of a list

"""

from Web.AdminConsole.Components.panel import (PanelInfo, DropDown)
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import (WebAction, PageService)
from Web.Common.exceptions import CVWebAutomationException

class HyperScaleStorageDetails:
    """
    Class for hyperscale storagepool Details page
    """

    def __init__(self, admin_console):
        """
        Initialization method for HyperScaleStorageDetails Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.__props = self.__admin_console.props
        self.__table = Table(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)
        self.__disk_lib = None
        self.__nodes_table_details = None

    @WebAction()
    def __click_edit_symbol(self):
        """
            Click edits symbol for key management server
        """
        self.__driver.find_element(By.XPATH, 
            f"//span[contains(text(),{self.__props['label.keyManagement']})]//parent::li//span[2]//a//i").click()

    @WebAction()
    def __click_ok_symbol(self):
        """
            Click ok symbol for key management server
        """
        self.__driver.find_element(By.XPATH, 
            f"//span[contains(text(),{self.__props['label.keyManagement']})]//parent::li//a[1]").click()

    @PageService()
    def add_nodes(self, nodes):
        """
        To add nodes to an existing hyperscale storagepool

        Args:
            nodes     (List)            -- List of nodes for scaleout

        **Note** Nodes we are adding should be available to join to the StoragePool,
        """

        self.__admin_console.select_hyperlink(self.__props['label.addNodes'])
        self.__drop_down.select_drop_down_values(drop_down_id='MediaAgents', values=nodes)
        self.__admin_console.click_button(self.__props['action.add'])
        self.__admin_console.check_error_message()

    @PageService()
    def reconfigure_add_nodes(self):
        """
            Reconfigure add nodes operation
        """

        self.__admin_console.select_hyperlink(self.__props['action.reconfigure'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def library_info(self, hyperscale_storagepool_name):
        """
        To get the details of hyperscale storagepool

            Returns:
                info    (dict)  -- details of Disk Library
        """
        self.__disk_lib = "DiskLib_" + hyperscale_storagepool_name
        panel_info = PanelInfo(self.__admin_console, self.__disk_lib)
        return panel_info.get_details()

    @PageService()
    def refresh_node(self, node):
        """
        Node Refresh on hyperscale node

            Args:
                node (str)   --  name of the node to refresh
        """

        self.__table.access_action_item(node, self.__props['action.refresh'], partial_selection=True)
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def list_nodes(self):
        """
        Get all the Nodes of  hyperscale storagepool in the form of a list

            Returns:
                    Nodes    (list)  --  all Nodes of a storagepool
        """

        return self.__table.get_column_data(self.__props['label.node'])

    @PageService()
    def node_health_status(self, node):
        """Checks nodes is present iff present return status : online/offline
        Args:
                node (str)   --  name of the node
        Returns  : Status(str) - online/offline
        """
        if not self.__table.is_entity_present_in_column(self.__props['label.node'], node):
            raise CVWebAutomationException(f"Node {node} is not Present")

        self.__nodes_table_details = self.__table.get_table_data()
        return self.__nodes_table_details['Status'][self.__nodes_table_details['Node'].index(node)]

    @PageService()
    def access_hyperscale_node(self, hyperscale_node):
        """
        selects the HyperScale Node with the given name

        Args:
            hyperscale_node    (str)   -- Name of the HyperScale node to be accessed
        """
        self.__table.access_link(hyperscale_node)

    @PageService()
    def edit_key_management_server(self, key_management_server):
        """
        Edits the existing key management server

            Args:
                key_management_server (str)	-- New key management server
        """
        self.__click_edit_symbol()
        self.__admin_console.wait_for_completion()
        self.__drop_down.select_drop_down_values(0, [key_management_server])
        self.__click_ok_symbol()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def encrypt_storage(self, cipher=None, key_length=None, key_management_server=None):
        """
        To encrypt the storage

            Args:
                cipher      (str)   -- Encryption method to be used

                key_length  (str)   -- Key length for the chosen cipher

                key_management_server   (str)   --  Key management server for the storage pool
        """
        self.__admin_console.access_tab(self.__props['label.scaleOutConfiguration'])
        self.__admin_console.wait_for_completion()

        if cipher and key_length:
            panel_info = PanelInfo(self.__admin_console, self.__props['title.encryption'])
            panel_info.enable_toggle(self.__props['label.encrypt'])
            self.__drop_down.select_drop_down_values(0, [cipher])
            self.__drop_down.select_drop_down_values(1, [key_length])
            self.__admin_console.click_button(self.__props['action.save'])
            self.__admin_console.check_error_message()
        if key_management_server:
            self.edit_key_management_server(key_management_server)

    @PageService()
    def list_associated_plans(self):
        """
        Get all the associated plans to the hyperscale storagepool in the form of a list

            Returns:
                    plans_list    (list)  --  all associated plans to the disk
        """
        self.__admin_console.access_tab(self.__props['label.associatedPlans'])
        self.__admin_console.wait_for_completion()
        table = Table(self.__admin_console)
        try:
            return table.get_column_data(self.__props['Name'])
        except ValueError:
            return []
