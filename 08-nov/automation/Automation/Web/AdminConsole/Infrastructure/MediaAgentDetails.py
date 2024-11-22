# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to MediaAgent details page
under infratructure page

==============

MediaAgentDetails:

  move_ddb()        --    Perform DDB Move Operation

  create_ddb_disk() --    Create DDB disk

  get_num_partitions_for_path() -- Get the number of partitions from DDB partition table for provided path

"""

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.Common.page_object import PageService


class MediaAgentDetails:
    """
    Class for media agents page in Admin console
    """

    def __init__(self, admin_console):
        """ Initialize the MediaAgents obj

        Args:
            admin_console (AdminConsole): AdminConsole object

        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self._props = self.__admin_console.props
        self.__rtable = Rtable(self.__admin_console, id='ddbDisksManagement')
        self.__rdiag = RModalDialog(self.__admin_console)
        self.__rpanelinfo = RPanelInfo(self.__admin_console, title="Index Cache")

    @PageService()
    def move_ddb(self,
                 source_path,
                 dest_ma,
                 dest_path):
        """
        Perform DDB Move Operation

        Args:
            source_path (str)    : ddb source path to move
            dest_ma (str)        : destination media agent
            dest_path (str)      : destination ddb path on destination MA

        Raises:
            Exception if move job wasn't submitted successfully
        """
        self.__admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        self.__rtable.access_action_item(entity_name=source_path, action_item="Move")
        self.__rdiag.select_dropdown_values(drop_down_id="mediaAgent", values=[dest_ma])
        self.__rdiag.click_button_on_dialog(aria_label="Create new")

        rdiag = RModalDialog(self.__admin_console, title=self._props['action.addPartition'])
        rdiag.fill_text_in_field(element_id='ddbDiskPartitionPath', text=dest_path)
        rdiag.click_submit()
        self.__rdiag.click_button_on_dialog(aria_label="Refresh")

        self.__rdiag.click_submit(wait=False)
        alert = self.__admin_console.get_notification()

        if "Move partition job is submitted successfully" not in alert:
            raise Exception(alert)

    @PageService()
    def create_ddb_disk(self,
                        source_path):
        """
        Create DDB Disk
        Args:
            source_path (str)    : ddb source path to move
        Raises:
              Exception if alert is non-empty
        """
        self.__admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        self.__admin_console.click_button_by_id("addDDBDisk")
        self.__rdiag.fill_text_in_field(element_id='ddbDiskPartitionPath', text=source_path)
        self.__rdiag.click_submit(wait=False)
        alert = self.__admin_console.get_notification()

        if alert != '':
            raise Exception(alert)

    @PageService()
    def get_num_partitions_for_path(self, path):
        """
        Get the number of partitions from DDB partition table for provided path

        Args:
            path (str)           : ddb path to get number of parttitions

        Returns:
            num_partitions (int)  : number of partitions
        """
        self.__admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        self.__rtable.search_for(path)
        num_partitions = self.__rtable.get_column_data(self._props['label.ddbPartitionNumber'])
        self.__rtable.clear_search()

        return num_partitions

    def get_index_cache_details(self):
        """
        Get the Index cache details that are displayed in the command center
        """
        self.__admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        return self.__rpanelinfo.get_details().get('Index cache path')
