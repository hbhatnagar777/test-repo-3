# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
DiskStorageDetails/ CloudStorageDetails /AirGapProtectStorageDetails page of the AdminConsole

StorageDetails:

    storage_encryption_info()     --  To get the details of Disk/Cloud/AirGapProtect storage's encryption info

    storage_info()              --    To get the details of Disk/Cloud/AirGapProtect storage

    access_mount_path()         --    selects the mount_path with the given name

    list_mount_paths()          --    Get all the backup locations/containers on Disk/Cloud/AirGapProtect storage
                                      in the form of a list

    delete_mount_path()         --    Deletes the backup location/container on Disk/Cloud/AirGapProtect storage

    enable_mount_path()         --    Enable a backup location/container on Disk/Cloud/AirGapProtect storage

    disable_mount_path()        --    Disable a backup location/container on Disk/Cloud/AirGapProtect storage

    worm_storage_lock()         --    Enable WORM lock on disk/cloud storage

    compliance_lock()           --    Enable compliance lock on disk/cloud storage

    list_associated_plans()     --   Get all the associated plans to the Disk/Cloud/AirGapProtect storage
                                     in the form of a list

    is_compliance_lock_enabled()    --  Checks if compliance lock is enabled on Disk/Cloud/AirGapProtect storage
"""

from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService


class StorageDetails:

    def __init__(self, admin_console, storage_type=None):
        """
        Initialization method for Disk Backup location Class

            Args:
                admin_console (AdminConsole) -- AdminConsole object

                storage_type  (str) -- type of storage
        """
        self._admin_console = admin_console
        self._storage_type = storage_type
        self._admin_console.load_properties(self)
        self._driver = self._admin_console.driver
        self._props = self._admin_console.props
        self._modal_dialog = RModalDialog(self._admin_console)
        self._panel_info = RPanelInfo(self._admin_console)
        if self._storage_type == "Disk":
            self._table = Rtable(self._admin_console, title='Backup locations')
        elif self._storage_type == "Cloud":
            self._table = Rtable(self._admin_console, id='cloud-overview-grid')
        elif self._storage_type == "AirGapProtect":
            self._table = Rtable(self._admin_console, id='cloud-overview-grid')
        else:
            self._table = Rtable(self._admin_console)

    @PageService()
    def storage_encryption_info(self):
        """
        To get the details of Disk/Cloud/AirGapProtect storage's encryption info

            Returns:
                info    (dict)  -- details of Disk/Cloud/AirGapProtect storage
        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['title.encryption'])
        return panel_info.get_details()

    @PageService()
    def storage_info(self):
        """
        To get the details of Disk/Cloud/AirGapProtect storage

            Returns:
                info    (dict)  -- details of Disk/Cloud/AirGapProtect storage
        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['label.general'])
        return panel_info.get_details()

    @PageService()
    def access_mount_path(self, mount_path):
        """
        selects the mount_path with the given name

        Args:
            mount_path    (str)   -- Name of the mount_path to be accessed
        """
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self._table.access_link(mount_path)

    @PageService()
    def list_mount_paths(self):
        """
        Get all the backup locations/containers on Disk/Cloud/AirGapProtect storage in the form of a list

            Returns:
                    backup_location_list/containers_list    (list)  --  all backup locations/container on
                                                                        Disk/Cloud/AirGapProtect storage
        """

        self._admin_console.access_tab(self._props['label.backupLocations'])
        return self._table.get_column_data(self._props['Name'])

    @PageService()
    def delete_mount_path(self, mount_path):
        """
        Deletes the backup location/container on Disk/Cloud/AirGapProtect storage

            Args:
                mount_path (str)   --  name of the backup location/container to delete
        """
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self._table.access_action_item(mount_path, self._admin_console.props['label.globalActions.delete'])
        self._modal_dialog.click_button_on_dialog(self._admin_console.props['label.globalActions.delete'])
        self._admin_console.check_error_message()

    @PageService()
    def enable_mount_path(self, mount_path):
        """
        Enable a backup location/container on Disk/Cloud/AirGapProtect storage

            Args:
               mount_path  (str)   --  mount_path which needs to be enabled

        """
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self._table.access_action_item(mount_path, self._admin_console.props['label.enable'])

    @PageService()
    def disable_mount_path(self, mount_path):
        """
        Disable a backup location/container on Disk/Cloud/AirGapProtect storage

            Args:
               mount_path  (str)   --  mount_path which needs to be disabled

        """
        self._admin_console.access_tab(self._props['label.backupLocations'])
        self._table.access_action_item(mount_path, self._admin_console.props['label.disable'])

    @PageService()
    def worm_storage_lock(self, retention_period):
        """
        Enable WORM lock on disk/cloud storage

           Args:
                retention_period           (dict):     How long the retention is to be set
                    Format: {'period': 'day(s)','value': '365'}
                        'period' (str):Retention time period unit
                            Allowed values: 'day(s)' , 'month(s)', 'year(s)'
                    'value' (str):      Retain for that many number of time period

        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['label.WORM'])
        panel_info.enable_toggle(self._props['label.hardwareWORM'])
        if self._modal_dialog.title() == self._props['label.extended.retention.title']:
            self._modal_dialog.fill_text_in_field("retentionPeriodDays", retention_period['value'])
            self._modal_dialog.select_dropdown_values('retentionPeriodDaysUnit', [retention_period['period']])
            self._admin_console.click_button_using_text(self._props['action.ok'])
            self._admin_console.checkbox_select(checkbox_id='dependentCopy')
        self._admin_console.checkbox_select(checkbox_id='WORMStorage')
        self._admin_console.fill_form_by_id('confirmText', 'Confirm')
        self._admin_console.click_button(self._props['label.confirm'])
        self._admin_console.check_error_message()

    @PageService()
    def compliance_lock(self):
        """
        Enable compliance lock on disk/cloud storage

        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['label.WORM'])
        panel_info.enable_toggle(self._props['label.softwareWORM'])
        self._admin_console.click_button(self._props['label.yes'])

    @PageService()
    def list_associated_plans(self):
        """
        Get all the associated plans to the Disk/Cloud/AirGapProtect storage in the form of a list

            Returns:
                    plans_list    (list)  --  all associated plans to the cloud
        """
        self._admin_console.access_tab(self._props['label.associatedPlans'])
        self._admin_console.wait_for_completion()
        table = Rtable(self._admin_console)
        try:
            return table.get_column_data(self._props['Name'])
        except ValueError:
            return []

    @PageService()
    def is_compliance_lock_enabled(self):
        """Checks if compliance lock is enabled on Disk/Cloud/AirGapProtect storage

            Returns:
                bool    - True if compliance lock is enabled
                          False if compliance lock is not enabled
        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['label.WORM'])
        return panel_info.is_toggle_enabled(label=self._props['label.softwareWORM'])

    @PageService()
    def disable_compliance_lock(self):
        """
        Disable compliance lock on disk/cloud storage

        """
        self._admin_console.access_tab(self._props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self._admin_console, self._props['label.WORM'])
        panel_info.disable_toggle(self._props['label.softwareWORM'])
        self._admin_console.click_button(self._props['label.yes'])

