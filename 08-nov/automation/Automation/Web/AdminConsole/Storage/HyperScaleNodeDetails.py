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

    node_disk_info()        -- return dict of disk details

    node_server_info()      -- return dict of server info

    replace_brick()         -- to replace a brick in a node

    list_bricks()           -- returns the list of bricks present in a node

    brick_health_status()   -- return status of a brick

"""

from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import  PageService
from Web.Common.exceptions import CVWebAutomationException

class HyperScaleNodeDetails:
    """
    Class for hyperscale Node Details page
    """

    def __init__(self, admin_console):
        """
        Initialization method for HyperScaleStorageDetails Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__props = self.__admin_console.props
        self.__table = Table(self.__admin_console)
        self.__brick_table_details = None

    @PageService()
    def node_disk_info(self):
        """
        To get the details of Disks

            Returns:
                info    (dict)  -- details of Node Disks
        """
        panel_info = PanelInfo(self.__admin_console, self.__props['title.diskInformation'])
        return panel_info.get_details()

    @PageService()
    def node_server_info(self):
        """
        To get the details of hardware usage

            Returns:
                info    (dict)  -- details of Node hardware usage
        """
        panel_info = PanelInfo(self.__admin_console, self.__props['title.serverInformation'])
        return panel_info.get_details()

    @PageService()
    def replace_brick(self, brick):
        """
        Replace brick action on a disk

            Args:
                brick (str)   --  name of the brcik to replace
        """

        self.__table.access_action_item(brick, self.__props['action.replace'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def list_bricks(self):
        """
        Get all the bricks  of  hyperscale Node in the form of a list

            Returns:
                    Nodes    (list)  --  all Bricks of a Node
        """

        return self.__table.get_column_data(self.__props['label.mountPath'])

    @PageService()
    def brick_health_status(self, brick):
        """Checks brick is present iff present return status
           Return (str) : Status of a brick
        """

        if not self.__table.is_entity_present_in_column(self.__props['label.mountPath'], brick):
            raise CVWebAutomationException(f"Brick : {brick} is not Present")

        self.__brick_table_details = self.__table.get_table_data()
        return self.__brick_table_details['Disk status'][self.__brick_table_details['Mount path'].index(brick)]
