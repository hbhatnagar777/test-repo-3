# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to disk storage page in AdminConsole
DiskStorage : This class provides methods for disk storage related operations

DiskStorage:

    add_disk_storage()      --  adds a new disk storage

    list_disk_storage()     --  returns a list of all disk storage

    access_disk_storage()   --  opens a disk storage

    delete_disk_storage()   --  removes a disk storage

"""

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import (WebAction, PageService)


class DiskStorage:
    """
    This class provides the function or operations that can be
    performed on the Disk Storage Page of the Admin Console
    """

    def __init__(self, admin_console):
        """
        Initialization method for DiskStorage Class

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
    def add_disk_storage(self, disk_storage_name, backup_location_details,
                         deduplication_db_location_details=None):
        """
        To add a new disk storage

        Args:
            disk_storage_name (str)     -- Name of the disk storage to be created

           backup_location_details (list): List of dictionaries containing backup location details to add multiple backup
           locations.
                E.g. - backup_location_details = [{'media_agent': "sample_media_agent1",
                                                    'backup_location': "sample_backup_location",
                                                    'saved_credential_name': "sample_saved_credential"},
                                                    {'media_agent': "sample_media_agent1",
                                                     'backup_location': "sample_backup_location",
                                                     'username': "sample_username",
                                                     'password': "sample_password}]


           deduplication_db_location_details (list): List of dictionaries containing DDB location details to add
           multiple deduplication db locations.
                E.g. - deduplication_db_location_details = [{'media_agent': "sample_media_agent",
                                                            'deduplication_db_location': "sample_ddb_location"}]


        **Note** MediaAgent should be installed prior, for creating a new backup location for storage.
                To use saved credentials for network path it should be created prior using credential manager,
        """

        self.__table.access_toolbar_menu(self.__props['action.add'])

        # Handle case where `Add` menu is of dropdown type, requiring an additional step of selecting menu item
        add_disk_storage_item_id = self.__props['label.diskStorage']    # `Disk storage`
        add_disk_storage_item_xpath = f"//li[contains(text(),'{add_disk_storage_item_id}') and @role='menuitem']"
        # NOTE - Above XPath taken from:
        # Automation/Web/AdminConsole/Components/table.py > Rtable > access_menu_from_dropdown()
        if self.__admin_console.check_if_entity_exists('xpath', add_disk_storage_item_xpath):
            self.__table.access_menu_from_dropdown(add_disk_storage_item_id)

        self.__admin_console.fill_form_by_id("name", disk_storage_name)

        for location in backup_location_details:
            self.__admin_console.select_hyperlink(self.__props['action.add'])
            self.__dropdown.select_drop_down_values(values=[location['media_agent']], drop_down_id='mediaAgent')
            if 'saved_credential_name' in location:
                self.__admin_console.select_radio(value=self.__props['label.network'])
                self.__admin_console.enable_toggle(index=0)
                self.__dropdown.select_drop_down_values(drop_down_id='credential',
                                                        values=[location['saved_credential_name']])
            elif 'username' in location and 'password' in location:
                self.__admin_console.select_radio(value=self.__props['label.network'])
                self.__admin_console.disable_toggle(index=0)
                self.__admin_console.fill_form_by_id("userName", location['username'])
                self.__admin_console.fill_form_by_id("password", location['password'])

            self.__admin_console.fill_form_by_id("path", location['backup_location'])
            self.__admin_console.click_button(self.__props['action.add'])

        if deduplication_db_location_details:
            for location in deduplication_db_location_details:
                self.__admin_console.select_hyperlink(self.__props['action.add'], 1)

                media_agent = location['media_agent']
                deduplication_db_location = location['deduplication_db_location']
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

                self.__admin_console.click_button(self.__props['action.add'])
        else:
            self.__admin_console.click_by_xpath("//span[contains(text(), 'Use deduplication')]")

        self.__admin_console.click_button(self.__props['action.save'])
        self.__admin_console.check_error_message()

    @PageService()
    def list_disk_storage(self, fetch_all=False):
        """
        Get the of all the disk storage in the form of a list

            Returns:
               list --  all disk storage
        """
        try:
            return self.__table.get_column_data(self.__props['Name'], fetch_all=fetch_all)
        except ValueError:
            return []

    @PageService()
    def access_disk_storage(self, disk_storage):
        """
        selects the disk storage with the given name

        Args:
            disk_storage    (str)   -- Name of the disk storage to be opened
        """
        self.__table.access_link(disk_storage)

    @PageService()
    def delete_disk_storage(self, disk_storage):
        """
        Deletes the disk storage with the given name

        Args:
            disk_storage (str) - name of the storage to be removed
        """
        self.__table.access_action_item(disk_storage, self.__props['label.globalActions.delete'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()

