# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AirGapProtectContainerLocation page of the AdminConsole

AirGapProtectContainer:

    enable_container    -- Enable a container on air gap protect storage if disabled

    disable_container           -- Disable a container on air gap protect storage if enabled

    enable_container_for_future_backups()         -- Enable a container for future backups on
                                                        air gap protect storage

    disable_container_for_future_backups()        -- Disable a container for future backups on air gap protect storage

    enable_retire_container       --  Enable retirement of a container on air gap protect
                                            storage

    disable_retire_container         -- Disable retirement of a container on air gap protect storage

"""
from Web.AdminConsole.Storage.StorageMountPath import StorageMountPath
from Web.Common.page_object import PageService


class AirGapProtectContainer(StorageMountPath):

    def __init__(self, admin_console):
        """
        Initialization method for Air Gap Protect Container Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console)

    @PageService()
    def enable_container(self):
        """
        Enable a container on air gap protect storage if disabled

        """
        self.enable_mount_path()

    @PageService()
    def disable_container(self):
        """
        Disable a container on air gap protect storage if enabled
        """
        self.disable_mount_path()

    @PageService()
    def enable_container_for_future_backups(self):
        """
        Enable a container for future backups on air gap protect storage
        """
        self.enable_mount_path_for_future_backups()

    @PageService()
    def disable_container_for_future_backups(self):
        """
        Disable a container for future backups on air gap protect storage
        """
        self.disable_mount_path_for_future_backups()

    @PageService()
    def enable_retire_container(self):
        """
        Enable retirement of a container on air gap protect storage
        """
        self.enable_retire_mount_path()

    @PageService()
    def disable_retire_container(self):
        """
        Disable retirement of a container on air gap protect storage
        """
        self.disable_retire_mount_path()
        