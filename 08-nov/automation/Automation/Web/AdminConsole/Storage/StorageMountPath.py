# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
DiskBackupLocation/ CloudContainerLocation/ AirGapProtectContainer page of the AdminConsole

StorageMountPath:

    list_media_agent()           -- Get all the media agents that can access the backup location/container in the form
                                    of a list

    add_media_agent()             -- Add media agent to backup location/container on Disk/Cloud/AirGapProtect storage

    enable_mount_path()    -- Enable a backup location/container on Disk/Cloud/AirGapProtect storage if disabled

    disable_mount_path()           -- Disable a backup location/container on Disk/Cloud/AirGapProtect storage if enabled

    enable_for_future_backups()         -- Enable a backup location/container for future backups on
                                            Disk/Cloud/AirGapProtect storage

    disable_for_future_backups()        -- Disable a backup location/container for future backups on
                                            Disk/Cloud/AirGapProtect storage

    enable_retire_mount_path()       --  Enable retirement of a backup location/container on Disk/Cloud/AirGapProtect
                                            storage

    disable_retire_mount_path()         -- Disable retirement of a backup location/container on
                                            Disk/Cloud/AirGapProtect storage

    delete_access_path()               -- Deletes the media agent on a certain backup location/container

"""

from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService


class StorageMountPath:

    def __init__(self, admin_console):
        """
        Initialization method for Disk Backup location Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.__props = self.__admin_console.props
        self.__table = Rtable(self.__admin_console)
        self.__modal_dialog = RModalDialog(self.__admin_console)
        self.__panel_info = RPanelInfo(self.__admin_console)

    @PageService()
    def list_media_agent(self):
        """
        Get all the media agents that can access the backup location/container in the form of a list

            Returns:
                    MediaAgent_list    (list)  --  all Media agents
        """

        return self.__table.get_column_data(self.__props['label.mediaAgent'])

    @PageService()
    def add_media_agent(self, media_agent_list):
        """
        Add media agent to backup location/container on Disk/Cloud/AirGapProtect storage

            Args:
                media_agent_list  (list)  --  list of media agents to be added
        """
        add_media_agent_dialog = RModalDialog(self.__admin_console, title=self.__props['title.addMediaAgent'])
        self.__table.access_toolbar_menu(self.__props['title.addMediaAgent'])
        add_media_agent_dialog.select_items(media_agent_list)
        self.__admin_console.click_button(self.__props['action.save'])
        self.__admin_console.check_error_message()

    @PageService()
    def enable_mount_path(self):
        """
        Enable a backup location/container on Disk/Cloud/AirGapProtect storage if disabled

        """
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.scaleOutConfiguration'])
        panel_info.enable_toggle(self.__props['label.enable'])

    @PageService()
    def disable_mount_path(self):
        """
        Disable a backup location/container on Disk/Cloud/AirGapProtect storage if enabled
        """
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.scaleOutConfiguration'])
        panel_info.disable_toggle(self.__props['label.enable'])

    @PageService()
    def enable_mount_path_for_future_backups(self):
        """
        Enable a backup location/container for future backups on Disk/Cloud/AirGapProtect storage
        """
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.scaleOutConfiguration'])
        panel_info.disable_toggle(self.__props['label.preventNewWrites'])

    @PageService()
    def disable_mount_path_for_future_backups(self):
        """
        Disable a backup location/container for future backups on Disk/Cloud/AirGapProtect storage
        """
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.scaleOutConfiguration'])
        panel_info.enable_toggle(self.__props['label.preventNewWrites'])

    @PageService()
    def enable_retire_mount_path(self):
        """
        Enable retirement of a backup location/container on Disk/Cloud/AirGapProtect storage
        """
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.scaleOutConfiguration'])
        panel_info.enable_toggle(self.__props['label.prepareForRetirement'])

    @PageService()
    def disable_retire_mount_path(self):
        """
        Disable retirement of a backup location/container on Disk/Cloud/AirGapProtect storage
        """
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.scaleOutConfiguration'])
        panel_info.disable_toggle(self.__props['label.prepareForRetirement'])

    @PageService()
    def delete_access_path(self, media_agent):
        """
        Deletes the media agent on a certain backup location/container

            Args:
                media_agent (str)   --  name of the media agent to delete
        """
        self.__table.access_action_item(media_agent, self.__props['label.globalActions.delete'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def get_access_path_details(self):
        """
        Returns the access path table details

        """
        return self.__table.get_table_data()
