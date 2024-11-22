# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
DiskBackupLocation page of the AdminConsole

DiskBackupLocation:

    enable_backup_location()    -- Enable a backup location on disk storage if disabled

    disable_backup_location()           -- Disable a backup location on disk storage if enabled

    enable_for_future_backups()         -- Enable a backup location for future backups on
                                            disk storage

    disable_for_future_backups()        -- Disable a backup location for future backups on disk storage

    enable_retire_backup_location()       --  Enable retirement of a backup location on disk storage

    disable_retire_backup_location()         -- Disable retirement of a backup location on disk storage

"""

from Web.AdminConsole.Storage.StorageMountPath import StorageMountPath
from Web.Common.page_object import PageService


class DiskBackupLocation(StorageMountPath):

    def __init__(self, admin_console):
        """
        Initialization method for Disk Backup location Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console)

    @PageService()
    def enable_backup_location(self):
        """
        Enable a backup location on disk storage if disabled
        """
        self.enable_mount_path()

    @PageService()
    def disable_backup_location(self):
        """
        Disable a backup location on disk storage if enabled
        """
        self.disable_mount_path()

    @PageService()
    def enable_backup_location_for_future_backups(self):
        """
        Enable a backup location for future backups on disk storage
        """
        self.enable_mount_path_for_future_backups()

    @PageService()
    def disable_backup_location_for_future_backups(self):
        """
        Disable a backup location for future backups on disk storage
        """
        self.disable_mount_path_for_future_backups()

    @PageService()
    def enable_retire_backup_location(self):
        """
        Enable retirement of a backup location on disk storage
        """
        self.enable_retire_mount_path()

    @PageService()
    def disable_retire_backup_location(self):
        """
        Disable retirement of a backup location on disk storage
        """
        self.disable_retire_mount_path()
