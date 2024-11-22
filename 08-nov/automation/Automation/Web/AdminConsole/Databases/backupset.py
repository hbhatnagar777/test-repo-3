# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the Database
backupset page, the page that opens after selecting a backupset from instance page.

Backupset:
----------
    get_backupset_general_properties()  --  method to get properties of backupset

    list_subclients()                   --  Method returns the list of subclients/database
    groups under the backupset

    access_subclient()                  --  Clicks the given subclient

    access_restore()                    --  Clicks on the restore button below the recovery points

    access_clone()                      --  Clicks the clone restore button below recovery points

    restore_folders()                   --  Selects files and folders to restore

    delete_subclient()                  --  method to delete the subclient

    delete_backupset()                  --  method to delete the backupset

    list_backup_history()               --  Clicks on 'Backup history' from database details page

PostgreSQLBackupset:
--------------------
    add_subclient()                     --  method to add postgreSQL dumpbased subclient

DB2Backupset:
------------

    db2_backup()                        --  method to perform backup on backupset

    add_db2_subclient()                 --  method to add db2 subclient

"""
from enum import Enum
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.dialog import RBackup, RModalDialog
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import PageService
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.Instances.restore_panels import PostgreSQLRestorePanel
from Web.AdminConsole.Databases.Instances.instant_clone import PostgreSQLInstantClone
from Web.AdminConsole.Databases.Instances.restore_panels import DB2RestorePanel
from Web.AdminConsole.Databases.Instances.add_subclient import AddPostgreSQLSubClient
from Web.AdminConsole.Databases.Instances.add_subclient import AddDB2SubClient


class Backupset:
    """This class provides the function or operations to perform on backupset page
    """

    class SubclientTypes(Enum):
        """Enum to represent classes for adding subclient"""
        POSTGRES = "AddPostgreSQLSubClient"
        DB2 = "AddDB2SubClient"

    class RestorePanelTypes(Enum):
        """Enum to represent classes for implementing restore panel"""
        POSTGRES = "PostgreSQLRestorePanel"
        DB2 = "DB2RestorePanel"

    class InstantClonePanelTypes(Enum):
        """Enum to represent class for implementing instant clone panel"""
        POSTGRES = "PostgreSQLInstantClone"

    def __init__(self, admin_console: AdminConsole):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        self.__admin_console = admin_console
        self.__browse = RBrowse(self.__admin_console)
        self.__table = Rtable(self.__admin_console)
        self._panel_dropdown = RDropDown(self.__admin_console)
        self._panel_info = RPanelInfo(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.props = self.__admin_console.props
        self.__backupset_general_panel = None
        self._dialog = RModalDialog(self.__admin_console)
        self.page_container = PageContainer(self.__admin_console)
        self._restore_panel_map = {
            DBInstances.Types.POSTGRES: Backupset.RestorePanelTypes.POSTGRES,
            DBInstances.Types.DB2: Backupset.RestorePanelTypes.DB2,
            DBInstances.Types.DB2_MULTINODE: Backupset.RestorePanelTypes.DB2
        }
        self._add_subclient_map = {
            DBInstances.Types.POSTGRES: Backupset.SubclientTypes.POSTGRES,
            DBInstances.Types.DB2: Backupset.SubclientTypes.DB2
        }
        self._clone_panel_map = {
            DBInstances.Types.POSTGRES: Backupset.InstantClonePanelTypes.POSTGRES
        }

    @PageService()
    def get_backupset_general_properties(self):
        """method to get properties of backupset"""
        self.__backupset_general_panel = RPanelInfo(
            self.__admin_console, title=self.props['label.nav.general'])
        return self.__backupset_general_panel.get_details()

    @PageService()
    def list_subclients(self, subclients_tab_name="Subclients"):
        """Method returns the list of subclients/database groups under the backupset

        Args:
            subclients_tab_name  (str): Name of the subclients tab
                default: Subclients

            Accepted Values: Subclients/Database groups
        Returns:
            list of subclients under the backupset

        """
        self.__admin_console.access_tab(subclients_tab_name)
        self.__admin_console.wait_for_completion()
        return self.__table.get_column_data(self.props['label.name'])

    @PageService()
    def access_subclient(self, subclient_name):
        """Clicks the given subclient

        subclient_name (str):   name of the subclient to be deleted

        subclients_tab_name  (str): Name of the subclients tab
            default: Subclients

            Accepted Values: Subclients/Database groups

        """
        self.page_container.select_entities_tab()
        self.__table.access_link(subclient_name)

    @PageService()
    def access_restore(self):
        """Clicks on the restore button below the recovery points"""
        self._panel_info.click_button(self.props['label.globalActions.restore'])

    @PageService()
    def restore_folders(
            self, database_type, items_to_restore=None,
            all_files=False, from_time=None, to_time=None, copy=None, skip_selection=False):
        """ Selects files and folders to restore

        Args:
            database_type (Types):   Type of database should be one among the types defined
            in 'Types' enum in DBInstances.py file

            items_to_restore (list):  the list of files and folders to select for restore

                default: None

            all_files        (bool):  select all the files shown for restore / download

                default: False

            from_time   :   Time from when to backup
                format: %d-%B-%Y-%I-%M-%p
                        (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                        (01-January-2000-11-59-PM)

            to_time   :   Time till when to backup
                format: %d-%B-%Y-%I-%M-%p
                        (dd-Month-yyyy-hour(12 hour)-minutes-session(AM/PM))
                        (01-January-2000-11-59-PM)

            copy (str) : Name of the storage policy copy to use for restore

            skip_selection (bool): To skip selection of items to restore. 
                                 Content is auto selected after browse for some agents.
                                 Example: PostgreSQL FSBased restores.
                default: False

        Returns:
            object of relevant class in restore_panels file

        """
        if copy:
            self.__browse.select_storage_copy(copy, database=True)
        if to_time:
            self.__browse.show_latest_backups(database=True)
            self.__browse.show_backups_by_date_range(from_time=from_time, to_time=to_time, index=0)
        if not skip_selection:
            self.__browse.clear_all_selection()
            self.__browse.select_files(file_folders=items_to_restore, select_all=all_files)
        self.__browse.submit_for_restore()
        return globals()[self._restore_panel_map[database_type].value](self.__admin_console)

    @PageService()
    def access_clone(self, database_type):
        """Clicks on the Instant Clone button below the recovery points
        Returns:
            object of relevant class in instant_clone file """
        self._panel_info.click_button(self.props['label.clone'])
        return globals()[self._clone_panel_map[database_type].value](self.__admin_console)

    @PageService()
    def delete_subclient(self, subclient_name, subclients_tab_name="Subclients"):
        """
        method to delete the subclient

        Args:
            subclient_name (str):   name of the subclient to be deleted

            subclients_tab_name  (str): Name of the subclients tab
                default: Subclients

                Accepted Values: Subclients/Database groups

        """
        self.__admin_console.access_tab(subclients_tab_name)
        self.__table.access_action_item(subclient_name, 'Delete')
        self._dialog.type_text_and_delete('DELETE')
        self.__admin_console.wait_for_completion()

    @PageService()
    def delete_backupset(self):
        """Deletes the backupset"""
        self.page_container.access_page_action_from_dropdown('Delete')
        self._dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def list_backup_history(self):
        """Clicks on 'Backup history' from database details page"""
        self.page_container.access_page_action(self.__admin_console.props['label.BackupHistory'])


class PostgreSQLBackupset(Backupset):
    """This class provides the function or operations to perform on backupset page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(PostgreSQLBackupset, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.props = self.__admin_console.props

    @PageService()
    def add_subclient(self, subclient_name, number_backup_streams,
                      collect_object_list, plan, database_list):
        """
        method to add postgreSQL dumpbased subclient

        Args:
            subclient_name          (str):  Name of the subclient

            number_backup_streams   (int): number of streams used for backup

            collect_object_list     (bool): boolean value to specify if collect object
            list needs to be enabled

            plan                    (str):  plan name to be assigned to subclient

            database_list           (list): list of databases which needs to be part
            of subclient content

        """
        self.__admin_console.access_tab(self.props['label.DatabaseGroups'])
        self.__admin_console.wait_for_completion()
        self.__table.access_toolbar_menu(self.props['label.AddDatabaseGroup'])
        add_subclient_object = globals()[
            self._add_subclient_map[DBInstances.Types.POSTGRES].value](self.__admin_console)
        add_subclient_object.add_subclient(
            subclient_name, number_backup_streams, collect_object_list, plan, database_list)


class DB2Backupset(Backupset):
    """This class provides the function or operations to perform on backupset page
    """

    def __init__(self, admin_console):
        """Class constructor

            Args:
                admin_console   (obj)                 --  The admin console class object

        """
        super(DB2Backupset, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.props = self.__admin_console.props

    @PageService()
    def db2_backup(self, subclient_name, backup_type="incremental"):
        """
        Submits backup job from the subclient page
        Args:

            subclient_name              (str)               -- Subclient Name

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
        self.__table.access_action_item(subclient_name,
                                        self.__admin_console.props['action.commonAction.backup'])

        return RBackup(self.__admin_console).submit_backup(backup_type)

    @PageService()
    def add_db2_subclient(self, subclient_name, plan, number_data_streams=2, data_backup=True,
                          type_backup="online", exclude_logs=False, backup_logs=False, delete_logs=False,
                          partitioned_database=False):
        """
            Method to add DB2 subclient

        Args:
            subclient_name          (str):  Name of the subclient

            plan                    (str):  plan name to be assigned to subclient

            number_data_streams     (int): number of streams used for backup
                default: 2

            data_backup             (bool): boolean value to specify data backup
                default: True

            type_backup             (str): type of backup - online or offline
                default: online

            exclude_logs            (bool): To backup logs or not into backup image
                default: False

            backup_logs             (bool): Backup archived logs or not
                default: False

            delete_logs             (bool): Delete archived logs after backup or not
                default: False

            partitioned_database    (bool): If database is partitioned database or not
                default: False
        """
        self.__admin_console.access_tab(self.props['heading.Subclients'])
        self.__admin_console.wait_for_completion()
        self.__table.access_toolbar_menu(self.props['action.subclientCreation'])
        add_subclient_object = globals()[
            self._add_subclient_map[DBInstances.Types.DB2].value](self.__admin_console)
        add_subclient_object.add_subclient(
            subclient_name, plan, number_data_streams, data_backup, type_backup,
            exclude_logs, backup_logs, delete_logs, partitioned_database)
