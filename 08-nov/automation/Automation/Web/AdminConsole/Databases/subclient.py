# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on
subclient/database group/table groups details page

SubClient:
----------
    get_subclient_general_properties()      --      Returns the subclient properties under
    general panel

    get_subclient_snapshot_properties()     --      Returns the Intellisnap details of the
    subclient
    displayed under Snapshot panel

    enable_backup()                         --      Enables the 'Data backup' toggle if it
    is disabled

    disable_backup()                        --      Disables the 'Data backup' toggle if it
    is enabled

    backup()                                --      Submits backup job from the subclient page

    access_restore()                        --      Clicks on the restore button below the
    recovery points in subclient page

    clear_all_selection()                   --      Clicks on clear all checkbox in browse
    page if present

    restore_folders()                       --      Clicks on the given items, analogous to
    folders in the browse page and submits restore. Also returns the object of restore panel
    class class corresponding to database_type argument

    restore_files_from_multiple_pages()     --      Clicks on items from multiple pages
    recursively in browse page and submits restore. Also returns the object of restore
    panel class corresponding to database_type argument

    is_snapshot_enabled()                   --      method to check if snapshot option is enabled
    for subclient

    get_snap_engine()                       --      method to get snap engine type

    enable_snapshot()                       --      method to enable snapshot option for subclient

    disable_snapshot()                      --      method to disable snapshot option for subclient

    delete_subclient()                      --      method to delete subclient

    is_blocklevel_backup_enabled()          --      method to check if block level backup for
    subclient is enabled

    enable_blocklevel_backup()              --      method to enable block level backup for
    subclient

    disable_blocklevel_backup()             --      method to disable cblock level backup for
    subclient

    get_items_in_browse_page()              --      Returns all the items shown in current browse

                                                    page for given column

    edit_content()                          --      Edits content of subclient to databases

    edit_streams()                          --      Edits number of streams for subclient

    return_to_instance()                    --      Returns to the instance/fileserver page from
                                                    subclient details page.

PostgreSQLSubclient:
--------------------
    enable_collect_objectlist()             --      method to enable collect object list option in
    postgreSQL subclient

    disable_collect_objectlist()            --      method to disable collect object list option in
    postgreSQL subclient

DB2Subclient:
------------
    db2_backup()        --      method to trigger backup job from subclient level page

MySQLSubclient:
----------------
    edit_content()              --      method to edit content of subclient

    validate_autodiscover()     --      Method to verify database in client
                                        is auto discovered by subclient

    database_group_autodiscovered_content() --   Method to get all the autodiscovered
                                                databases

    enable_standby_backup()     --      Method to enable standby backup option

    is_all_databases_in_content()--     Method to check if [All databases] in
                                        subclient content

InformixSubclient:
----------------
    edit_content()              --      Method to edit content for subclient

RDSSubclient:
----------------
    enable_replication()        --      Method to enable replication in Instance group page

    edit_region_mapping()       --      Method to add region mapping or
                                        to edit existing region mapping

    enable_cross_account_operations()-- Method to enable cross account
                                        operations in Instance group page

OracleSubclient:
----------------
    edit_backup_arguments()     --      Method to edit oracle subclient backup arguments
"""
from enum import Enum
from Web.Common.page_object import (
    PageService
)

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo, RModalPanel, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog, RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.Instances.restore_panels import DynamoDBRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import MySQLRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import RedshiftRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import DocumentDBRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import RDSRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import SybaseRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import InformixRestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import DB2RestorePanel
from Web.AdminConsole.Databases.Instances.restore_panels import DocumentDBRestorePanel


class SubClient:
    """Class for database subclients page"""

    class DBTypes(Enum):
        """Enum to represent supported database types"""
        DYNAMODB = "DynamoDBRestorePanel"
        MYSQL = "MySQLRestorePanel"
        RDS = "RDSRestorePanel"
        SYBASE = "SybaseRestorePanel"
        REDSHIFT = "RedshiftRestorePanel"
        DOCUMENTDB = "DocumentDBRestorePanel"
        INFORMIX = "InformixRestorePanel"
        DB2 = "DB2RestorePanel"

    def __init__(self, admin_console):
        """
            Args:
                admin_console (AdminConsole): Object of AdminConsole class
        """
        self._admin_console = admin_console
        self._browse = RBrowse(self._admin_console)
        self._table = Rtable(self._admin_console)
        self._admin_console.load_properties(self)
        self.props = self._admin_console.props
        self._subclient_general_panel = RPanelInfo(self._admin_console,
                                                   title=self.props['header.general'])
        self.databases_panel = RPanelInfo(self._admin_console, title='Databases')
        self.__subclient_snapshot_panel = RPanelInfo(
            self._admin_console, title=self.props['header.snapshotManagement'])
        self._panel = RModalPanel(self._admin_console)
        self._dialog = RModalDialog(self._admin_console)
        self._panel_info = RPanelInfo(self._admin_console)
        self._panel_dropdown = RDropDown(self._admin_console)
        self.page_container = PageContainer(
            self._admin_console, id_value='dbCollectionDetailInstance')
        self.__restore_panel_map = {
            DBInstances.Types.DYNAMODB: SubClient.DBTypes.DYNAMODB,
            DBInstances.Types.DOCUMENTDB: SubClient.DBTypes.DOCUMENTDB,
            DBInstances.Types.MYSQL: SubClient.DBTypes.MYSQL,
            DBInstances.Types.SYBASE: SubClient.DBTypes.SYBASE,
            DBInstances.Types.REDSHIFT: SubClient.DBTypes.REDSHIFT,
            DBInstances.Types.DOCUMENTDB: SubClient.DBTypes.DOCUMENTDB,
            DBInstances.Types.INFORMIX: SubClient.DBTypes.INFORMIX,
            DBInstances.Types.RDS: SubClient.DBTypes.RDS,
            DBInstances.Types.DB2: SubClient.DBTypes.DB2
        }

    @PageService()
    def get_subclient_general_properties(self):
        """Returns the subclient properties under general panel"""
        return self._subclient_general_panel.get_details()

    @PageService()
    def get_subclient_snapshot_properties(self):
        """Returns the Intellisnap details of the subclient
            displayed under Snapshot panel"""
        return self.__subclient_snapshot_panel.get_details()

    @PageService()
    def enable_backup(self):
        """Enables the 'Data backup' toggle if it is disabled"""
        self._subclient_general_panel.enable_toggle(
            self.props['label.enableBackup'])

    @PageService()
    def disable_backup(self):
        """Disables the 'Data backup' toggle if it is enabled"""
        self._subclient_general_panel.disable_toggle(
            self.props['label.enableBackup'])
        self._dialog.click_submit()

    @PageService()
    def backup(self, backup_type=RBackup.BackupType.INCR, enable_data_for_incremental=False, cumulative=False,
               immediate_backup_copy=False, purge_binary_log=True):
        """
        Submits backup job from the subclient page
        Args:
            backup_type                 (Backup.BackupType) -- backup type

            enable_data_for_incremental (bool)              -- flag to check if
            data needs to be backed up during incremental default: False
            immediate_backup_copy (bool) -- flag to enable immediate backup copy
            purge_binary_log(bool)      --   To enable purge binary logs
        Returns
            (str) -- Backup job id

        """
        self._admin_console.wait_for_completion()
        self.page_container.access_page_action(self.props['label.backup'])
        self._admin_console.wait_for_completion()
        return RBackup(self._admin_console).submit_backup(backup_type=backup_type,
                                                          incremental_with_data=enable_data_for_incremental,
                                                          cumulative=cumulative,
                                                          immediate_backup_copy=immediate_backup_copy,
                                                          purge_binary_log=purge_binary_log)

    @PageService()
    def access_restore(self):
        """Clicks on the restore button below the recovery points in subclient page"""
        self._panel_info.click_button(self.props['label.globalActions.restore'])

    @PageService()
    def clear_all_selection(self):
        """Clicks on clear all checkbox in browse page if present"""
        self._browse.clear_all_selection()

    @PageService()
    def restore_folders(self, database_type, items_to_restore=None, all_files=False,
                        copy=None, restore_items_from_previous_browse=False,
                        from_time=None, to_time=None):
        """Clicks on the given items, analogous to folders in the browse page and
        submits restore. Also returns the object of restore panel class
        corresponding to database_type argument

        Args:
            database_type (Types):   Type of database should be one among the types defined
                                      in 'Types' enum in DBInstances.py file

            items_to_restore (list) : list of files and folders to select for restore
                                    list of items analogous to folders in browse page

            all_files        (bool):  select all the files shown for restore / download

                default: False

            copy            (str):  The name of the copy to browse from
                                    Example- "Secondary" or "Copy-2"

            restore_items_from_previous_browse (bool): Use the same items to restore
                                                        as in previous browse request

                default: False

            from_time   :   Time from when to backup
                format: %d-%B-%Y-%I-%M-%p
                        (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                        (01-January-2000-11-59-PM)

            to_time   :   Time till when to backup
                format: %d-%B-%Y-%I-%M-%p
                        (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                        (01-January-2000-11-59-PM)

        Returns:
            Object (RestorePanelTypes): Object of class in RestorePanelTypes corresponding
                                        to database_type
        """
        if not restore_items_from_previous_browse:
            if copy:
                self._browse.select_storage_copy(copy, database=True)
            if to_time:
                self._browse.show_latest_backups(database=True)
                self._browse.show_backups_by_date_range(from_time=from_time, to_time=to_time, index=0)
            if all_files:
                self._browse.clear_all_selection()
                self._browse.select_files(select_all=all_files)
            else:
                self._browse.select_files(file_folders=items_to_restore)
            self._browse.submit_for_restore()
        else:
            self._browse.submit_for_restore()
        return globals()[self.__restore_panel_map[database_type].value](self._admin_console)

    @PageService()
    def restore_files_from_multiple_pages(self, database_type, mapping_dict,
                                          root_node, rds_agent=False, copy=None):
        """Clicks on items from multiple pages recursively in browse page
        and submits restore. Also returns the object of restore panel class
        corresponding to database_type argument

        Args:
            database_type (Types):   Type of database should be one among the types defined
                                      in 'Types' enum in DBInstances.py file

            mapping_dict (dict) : The dictionary containing the folder names as keys
                                and list of files to be selected under them as value

                                    Example:
                                        mapping_dict={
                                        'FOLDER1':['file1','file2','file3']
                                        'FOLDER2':['fileA','fileB','fileC']
                                        }

            root_node   (str):  The name of the subclient/instance on which browse operation
                                    was performed or the name of the root folder that
                                    appears on the browse page

            rds_agent  (Boolean):  Flag to indicate if browse is performed for RDS agent

                                   True if browsing from amazon RDS instance or subclient
                                   False for any other agent

            copy        (str):  The name of the copy to browse from
                                Example- "Secondary" or "Copy-2"
        Returns:
            Object (RestorePanelTypes): Object of class in RestorePanelTypes corresponding
                                        to database_type

        """
        if copy:
            self._browse.select_storage_copy(copy, database=True)
        for folder, file_list in mapping_dict.items():
            self._browse.select_path_for_restore(path=folder, file_folders=file_list)
        self._browse.submit_for_restore()
        return globals()[self.__restore_panel_map[database_type].value](self._admin_console)

    @PageService()
    def is_snapshot_enabled(self):
        """method to check if snapshot option is enabled for subclient
        """
        toggle_element = self.__subclient_snapshot_panel.get_toggle_element(
            self.props['label.ConfirmEnableIntelliSnap'])
        return self.__subclient_snapshot_panel.is_toggle_enabled(toggle_element)

    @PageService()
    def get_snap_engine(self):
        """method to get snap engine type
        """
        if self.is_snapshot_enabled:
            panel_info = self.__subclient_snapshot_panel.get_details()
            return panel_info[self.props['label.engineName']]
        return None

    @PageService()
    def get_proxy_node(self):
        """method to get proxy node name"""
        if self.is_snapshot_enabled:
            panel_info = self.__subclient_snapshot_panel.get_details()
            return panel_info.get("Separate access node for backup copy", "None")
        return None

    @PageService()
    def enable_snapshot(self, snap_engine, proxy_node=None, rman_image_copy=None,
                        backup_copy_interface=None, snap_proxy=None, use_source=False):
        """method to enable snapshot option for subclient

        Args:
            snap_engine             (str)   --  Snap engine name to be selected

            proxy_node              (str)   --  proxy/access node to be used for backup copy

                default: None

            rman_image_copy         (str)   --  RMAN image copy path

                default: None

            backup_copy_interface   (str)   --  "File System"/"RMAN"/"Volume copy"

                default: None

            snap_proxy              (str)   --  proxy node to be used for snap operations

                default: None

            use_source              (bool)  --  Use source if access node is unreachable toggle

                default: False

        """
        bci_mapping = {"file system": "bciFileSystem", "rman": "bciRman",
                       "volume copy": "bciVolumeCopy"}
        self.__subclient_snapshot_panel.enable_toggle(self.props['label.ConfirmEnableIntelliSnap'])
        self._dialog.select_dropdown_values(values=[snap_engine], drop_down_id='enginesDropdown')
        if proxy_node or rman_image_copy or backup_copy_interface or snap_proxy:
            self._dialog.expand_accordion(id='accordionPanel')
        if proxy_node:
            self._dialog.select_dropdown_values(values=[proxy_node], drop_down_id='availableProxyBackup')
        if snap_proxy:
            self._dialog.select_dropdown_values(values=[proxy_node], drop_down_id='availableProxyMA')
        if rman_image_copy:
            self._admin_console.checkbox_select("snapImageCopy")
            self._admin_console.fill_form_by_id("imageCopyDir", rman_image_copy)
        if backup_copy_interface:
            self._dialog.select_dropdown_values(values=[backup_copy_interface], drop_down_id='backupCopyInterface')
        if use_source:
            self._dialog.enable_toggle(label="Use source if access node is unreachable")
        self._dialog.click_submit()

    @PageService()
    def disable_snapshot(self):
        """method to disable snapshot option for subclient

        """
        self.__subclient_snapshot_panel.disable_toggle(self.props['label.ConfirmEnableIntelliSnap'])

    @PageService()
    def delete_subclient(self):
        """Deletes the subclient"""
        self.page_container.access_page_action_from_dropdown('Delete')
        self._dialog.type_text_and_delete(text_val='DELETE')
        self._admin_console.wait_for_completion()

    @PageService()
    def is_blocklevel_backup_enabled(self):
        """
        method to check if block level backup for subclient is enabled

        """
        toggle_element = self._panel_info.get_toggle_element(
            self.props['label.blockLevelOption'])
        return self._panel_info.is_toggle_enabled(toggle_element)

    @PageService()
    def enable_blocklevel_backup(self):
        """
        method to enable block level backup for subclient

        """
        self._panel_info.enable_toggle(self.props['label.blockLevelOption'])

    @PageService()
    def disable_blocklevel_backup(self):
        """
        method to disable cblock level backup for subclient

        """
        self._panel_info.disable_toggle(self.props['label.blockLevelOption'])

    @PageService()
    def get_items_in_browse_page(self, column_name):
        """Returns all the items shown in current browse page for given column
        Args:
            column_name (str):  The name of the column to get data

        Returns:
            list    : List of items under given column
        """
        return self._browse.get_column_data(column_name)

    @PageService()
    def edit_content(self, database_list):
        """
        Edits content of subclient to databases
        Args:
            database_list: list of databases to be in database group
        """
        self._panel_info.click_button(self.props['label.viewOrEdit'])
        self._admin_console.wait_for_completion()
        self._browse.clear_all_selection()
        self._browse.select_files(database_list)
        self._panel.submit()

    @PageService()
    def edit_no_of_streams(self, streams):
        """ Edits number of streams for subclient
        Args:
            streams     (int)   - No of streams
        """
        self._panel_info.edit_and_save_tile_entity(self.props['label.numberBackupStreams'], streams)

    @PageService()
    def return_to_instance(self, instance_name):
        """
        Returns to instance/File Server Page from Subclient page

        Args:
            instance_name   (str):  the name of the corresponding instance/fileserver.

        """
        self._admin_console.select_hyperlink(instance_name)
        self._admin_console.wait_for_completion()


class PostgreSQLSubclient(SubClient):
    """

    This class provides the function or operations to perform on
    postgreSQL subclient page

    """

    @PageService()
    def enable_collect_objectlist(self):
        """
        method to enable collect object list option in postgreSQL subclient

        """
        self._panel_info.enable_toggle(self.props['label.CollectObjectList'])

    @PageService()
    def disable_collect_objectlist(self):
        """
        method to disable collect object list option in postgreSQL subclient

        """
        self._panel_info.disable_toggle(self.props['label.CollectObjectList'])


class DB2Subclient(SubClient):
    """

    This class provides the function or operations to perform on
    DB2 subclient page

    """

    @PageService()
    def db2_backup(self, backup_type="incremental"):
        """
        Submits backup job from the subclient page
        Args:
            backup_type                 (str)               -- backup type
                default: incremental

        Returns
            (str) -- Backup job id

        """
        backup_map = {
            "full": RBackup.BackupType.FULL,
            "incremental": RBackup.BackupType.INCR,
            "differential": RBackup.BackupType.DIFF
        }
        backup_type = backup_map[backup_type]

        self._admin_console.access_menu(self.props['label.globalActions.backup'])

        return RBackup(self._admin_console).submit_backup(backup_type)


class MySQLSubclient(SubClient):
    """Class for MySQL subclient"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__subclient_databases_panel = RPanelInfo(self._admin_console,
                                                      title=self.props['pageHeader.databases'])

    @PageService()
    def validate_autodiscover(self, database_list):
        """
        Method to verify database in client is auto discovered by subclient
        Args
            database_list: list of databases to verify are in database group
        """
        content = self.database_group_autodiscovered_content()
        if not all(database in content for database in database_list):
            raise Exception("Auto discover validation failed..!!")

    @PageService()
    def database_group_autodiscovered_content(self):
        """
        Method to get the auto discovered databases in subclient
        Returns:
            List of databases
        """
        self.databases_panel.click_button(self.props['label.viewOrEdit'])
        self._admin_console.wait_for_completion()
        content = self._table.get_column_data(column_name="Database name", fetch_all=True)
        self._dialog.click_cancel()
        return content

    @PageService()
    def enable_standby_backup(self):
        """Method to enable standby backup in subclient details page"""
        self._subclient_general_panel.enable_toggle(
            self.props['label.EnableStandbyBackup'])
        self._admin_console.wait_for_completion()

    @PageService()
    def is_all_databases_in_content(self):
        """ Checks if subclient content is set to all databases"""
        tile_xp = f"//span[contains(@class, 'MuiCardHeader-title') and normalize-space()='{self.props['pageHeader.databases']}']/ancestor::div[contains(@class, 'MuiCard-root')]"
        return self._admin_console.check_if_entity_exists('xpath',
                                                          tile_xp + "//p[contains(text(), 'All databases')]")


class InformixSubclient(SubClient):
    """Class for Informix subclient"""

    @PageService()
    def edit_content(self, bkp_mode):
        """
        Method to edit informix subclient content
        Args:
            bkp_mode(str)       : Backup mode as in command center with no space between words
                Accepted values = 'Entireinstance', 'Wholesystem', 'Selective',
                                  'Fulllogicallogs' and 'Fullandcurrentlogicallogs'
        """
        self._panel_info.click_button(self.props['label.viewOrEdit'])
        self._admin_console.wait_for_completion()
        backuptypes = {
            'entireinstance': 'label.entireInstance',
            'wholesystem': 'label.wholeSystem',
            'selective': 'label.selective',
            'fulllogicallogs': 'label.fullLogicalLogs',
            'fullandcurrentlogicallogs': 'label.fullCurrentLogicalLogs'
        }
        self._dialog.select_dropdown_values(values=[self.props[backuptypes[bkp_mode.lower()]]],
                                            drop_down_id='backupMode')
        self._dialog.click_save_button()


class RDSSubclient(SubClient):
    """Class for RDS subclient"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__subclient_snapshot_panel = RPanelInfo(self._admin_console,
                                                     title=self.props['label.snapshot'])

    @PageService()
    def enable_replication(self, source_region, destination_region):
        """Method to enable replication in Instance group page and add region mapping
            Args:
                    source_region: Source region for replication
                    destination_region: Destination region for replication
            Returns: Details in the snapshot panel of the subclient page as dict
        """
        if self.__subclient_snapshot_panel.is_toggle_enabled(
                self.__subclient_snapshot_panel.get_toggle_element(
                    self.props['header.label.replication'])):
            self.edit_region_mapping(source_region, destination_region)
        else:
            self.__subclient_snapshot_panel.enable_toggle(self.props['header.label.replication'])
            self._dialog.select_dropdown_values(values=[source_region],
                                                drop_down_id='sourceRegion')
            self._dialog.select_dropdown_values(values=[destination_region],
                                                drop_down_id='destinationRegion')
            self._dialog.click_save_button()
        return self.__subclient_snapshot_panel.get_details()

    @PageService()
    def edit_region_mapping(self, source_region, destination_region):
        """Method to add region mapping or to edit existing region mapping
            Args:
                source_region: Source region for replication
                destination_region: Destination region for replication
        """
        if len(self._table.get_table_data()) == 0 or \
                source_region not in self._table.get_column_data('Source region'):
            self.__subclient_snapshot_panel.click_button(self.props['action.add'])
            self._dialog.select_dropdown_values(values=[source_region],
                                                drop_down_id='sourceRegion')
            self._dialog.select_dropdown_values(values=[destination_region],
                                                drop_down_id='destinationRegion')
            self._dialog.click_save_button()
        elif dict(zip(self._table.get_column_data('Source region'),
                      self._table.get_column_data(
                          'Destination region')))[source_region] != destination_region:
            self._table.access_action_item(source_region, self.props['action.edit'])
            self._dialog.select_dropdown_values(values=[destination_region],
                                                drop_down_id='destinationRegion')
            self._dialog.click_save_button()

    @PageService()
    def enable_cross_account_operations(self, destination_account):
        """Method to enable cross account operations in Instance group page
            Args:
                destination_account(str)       : Name of the destination account  to be used for
                                                cross account operations
        """
        self.__subclient_snapshot_panel.enable_toggle(
            self.props['label.crossAccountOperations'])
        self._panel_dropdown.select_drop_down_values(values=[destination_account],
                                                     drop_down_id='accountList')
        self._admin_console.submit_form()


class OracleSubclient(SubClient):
    """Class for Oracle subclient"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__backup_arguments_panel = RPanelInfo(self._admin_console,
                                                   title=self.props['label.backupArguments'])

    @PageService()
    def edit_backup_arguments(self, backup_args=None, get_values=False):
        """Method to edit oracle subclient backup arguments
            Args:
                backup_args         (dict)  :   Dict containing backup args
                    Eg.
                        {'Number of data streams': '1',
                         'Maximum number of open files': '8',
                         'Data files (BFS)': '8',
                         'Archive files (BFS)': '32',
                         'RMAN Backup piece size': 'Maximum size 0 MB'}
                    default: None
                get_values          (bool)  :   True if initial backup arguments are to be returned
        """
        existing_backup_args = None
        if get_values:
            existing_backup_args = self.__backup_arguments_panel.get_details()
        self.__backup_arguments_panel.click_button('Edit')
        streams = backup_args.get('Number of data streams')
        if streams:
            self._admin_console.fill_form_by_id('numberOfStreams', streams)
        data_files = backup_args.get('Data files (BFS)')
        if data_files:
            self._admin_console.fill_form_by_id('dataFilesPerBFS', data_files)
        archive_files = backup_args.get('Archive files (BFS)')
        if archive_files:
            self._admin_console.fill_form_by_id('archiveFilesPerBFS', archive_files)
        max_open_files = backup_args.get('Maximum number of open files')
        if max_open_files:
            self._admin_console.fill_form_by_id('maxOpenFiles', max_open_files)
        backup_piece_size = backup_args.get('RMAN Backup piece size')
        if backup_piece_size:
            size_type, size, value, mode = backup_piece_size.split()
            self._panel_dropdown.select_drop_down_values(drop_down_id='sizeType', values={size_type + ' ' + size})
            self._admin_console.fill_form_by_id('sizeValue', value)
            self._panel_dropdown.select_drop_down_values(drop_down_id='sizeMode', values={mode})
        self._admin_console.submit_form()
        return existing_backup_args
