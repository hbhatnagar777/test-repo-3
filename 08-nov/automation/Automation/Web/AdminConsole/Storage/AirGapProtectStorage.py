# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to air gap protect storage page in AdminConsole
AirGapProtectStorage : This class provides methods for air gap protect storage related operations

AirGapProtectStorage:

    add_air_gap_protect_storage()      --  adds a new air gap protect storage

    list_air_gap_protect_storage()     --  returns a list of all air gap protect storage

    access_air_gap_protect_storage()   --  opens  air gap protect storage

    delete_air_gap_protect_storage()   --  removes  air gap protect storage

    air_gap_protect_storage_status()   --  Retrieves the status of air gap protect storage

"""

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService


class AirGapProtectStorage:
    """
    This class provides the function or operations that can be
    performed on the Air Gap Protect Storage Page of the Admin Console
    """

    def __init__(self, admin_console):
        """
        Initialization method for AirGapProtectStorage Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.__props = self.__admin_console.props
        self.__table = Rtable(self.__admin_console)
        self.__dropdown = RDropDown(self.__admin_console)
        self.__panel = RPanelInfo(self.__admin_console)

    @PageService()
    def add_air_gap_protect_storage(self, storage_name, media_agent,
                                    region, storage_type=None, storage_class=None,
                                    deduplication_db_location=None):
        """
        To add a new Air Gap Protect storage

        Args:
            storage_name (str)     -- Name of the Air Gap Protect storage
                                                                to be created

            media_agent     (str)       -- Media agent to create storage on

            region (str)                -- Region / Location of storage

            storage_type     (str)      -- Cloud vendor type (eg- Microsoft Azure Storage)

            storage_class       (str)   -- storage class associated with the storage

            deduplication_db_location (str) -- local path for the deduplication db

        **Note** MediaAgent should be installed prior for storage.
        """

        self.__table.access_toolbar_menu(self.__props['action.add'])
        self.__admin_console.fill_form_by_id("metallicCloudStorageName", storage_name)
        self.__dropdown.select_drop_down_values(values=[media_agent], drop_down_id='mediaAgent')
        if storage_type:
            self.__dropdown.select_drop_down_values(drop_down_id='storageType', values=[storage_type])
        if storage_class:
            self.__dropdown.select_drop_down_values(drop_down_id='storageClass', values=[storage_class])
        self.__dropdown.select_drop_down_values(values=[region], drop_down_id='location')
        if deduplication_db_location:
            self.__admin_console.select_hyperlink(self.__props['action.add'])

            # Use DDB specific RModalDialogs
            select_ddb_dialog = RModalDialog(self.__admin_console, title=self.__props['label.ddbPartitionPath'])
            select_ddb_dialog.select_dropdown_values(values=[media_agent], drop_down_id='mediaAgent')
            available_ddb_locations = self.__dropdown.get_values_of_drop_down(drop_down_id='ddbPartitionPath')
            if deduplication_db_location not in available_ddb_locations:
                select_ddb_dialog.click_button_on_dialog(aria_label='Create new', button_index=1)
                add_ddb_dialog = RModalDialog(self.__admin_console, title=self.__props['action.addPartition'])
                add_ddb_dialog.fill_text_in_field('ddbDiskPartitionPath', deduplication_db_location)
                add_ddb_dialog.click_submit()
            select_ddb_dialog.select_dropdown_values(values=[deduplication_db_location],
                                                     drop_down_id='ddbPartitionPath')

            self.__admin_console.click_button('Add')
        else:
            self.__admin_console.click_by_xpath("//span[contains(text(), 'Use deduplication')]")
        self.__admin_console.click_button(self.__props['action.save'])
        self.__admin_console.check_error_message()

    @PageService()
    def list_air_gap_protect_storage(self):
        """
        Get list of all the air gap protect storage in the form of a list

            Returns:
               list --  all air gap protect storage
        """
        try:
            return self.__table.get_column_data(self.__props['Name'])
        except ValueError:
            return []

    @PageService()
    def access_air_gap_protect_storage(self, air_gap_protect_storage):
        """
        selects the air gap protect storage with the given name

        Args:
            air_gap_protect_storage    (str)   -- Name of the air gap protect storage to be opened
        """
        self.__table.access_link(air_gap_protect_storage)

    @PageService()
    def delete_air_gap_protect_storage(self, air_gap_protect_storage):
        """
        Deletes the air gap protect storage with the given name

        Args:
            air_gap_protect_storage (str) - name of the storage to be removed
        """
        self.__table.access_action_item(air_gap_protect_storage, self.__props['label.globalActions.delete'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

    @PageService()
    def air_gap_protect_storage_status(self, air_gap_protect_storage):
        """Retrieves the Status field value from table for air gap protect storage with the given name

            Args:
                air_gap_protect_storage (str)   -   name of the storage

            Returns:
                string                          -   Status of air gap protect storage
        """
        self.__table.search_for(air_gap_protect_storage)
        self.__table.reload_data()
        try:
            index = self.__table.get_column_data(self.__props['Name']).index(air_gap_protect_storage)
            return self.__table.get_column_data(self.__props['title.status'])[index]
        except (ValueError, IndexError):
            return None
