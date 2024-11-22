# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
backup set / instance level of FS agent on the AdminConsole

Class:

    fs_backupset -> Backupset --> AdminConsole() -> AdminConsoleBase() -> object()

Functions:

add_fs_subclient()                  -- Adds a new fs subclient

"""
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.FSPages.fs_agent import FSSubClient
from Web.AdminConsole.AdminConsolePages.backupset import Backupset
from Web.Common.page_object import PageService


class FsBackupset(Backupset):
    """
    This provides the function or operations that can be performed on the backupset of FS agent
    """

    def __init__(self, admin_console):

        super(FsBackupset, self).__init__(admin_console)
        self.__table = Table(admin_console)
        self.__modal_dialog = ModalDialog(self._admin_console)

    @PageService()
    def add_fs_subclient(self,
                         scname,
                         plan,
                         backup_data,
                         impersonate_user=None,
                         exclusions=None,
                         exceptions=None,
                         backup_system_state=False,
                         storage_policy=None,
                         schedule_policies=None,
                         file_system='Windows'):
        """
        Method to Add New Subclient

        Args:
            scname (string)       : Name of the new sub client to be added

            plan           (string)       : plan name to be used as policy for new sub client
                                            backup

            backup_data     (list(paths)) : Data to be backed up by new sub client created
                Eg. backup_data = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            impersonate_user (dict)        :  Username and passowrd for impersonate user

            exclusions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exclusions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            exceptions       (list(paths)) : Data to be backed up by new sub client created
                Eg. exceptions = ['C:\\TestBackupSet1', C:\\TestBackupSet2']

            backup_system_state (boolean)  :  boolean values to determine if syatem state to
                                            be backed up or not

            storage_policy   (string)      :  storage policy to be used by subclient

            schedule_policies   (list)       :  list containing schedule policies to be used
                                                by subclient

            file_system       (string)     :  file system of the client
                Eg. - 'Windows' or 'Unix'

        Returns:
            None

        Raises:
            Exception:
                -- if fails to initiate backup
        """
        self._admin_console.select_hyperlink("Add Subclient")
        fs_subclient = FSSubClient(self._admin_console)
        fs_subclient.add(scname, plan, backup_data, impersonate_user, exclusions, exceptions,
                         backup_system_state, storage_policy, schedule_policies, file_system)

    @PageService()
    def action_subclient_backup(self, subclient):
        """
        Opens the subclient content for backup

        Args:
            subclient (str):name of the subclient

        Returns:
            None

        Raises:
            Exception:
                The subclient has not been backed up yet.
        """
        self.__table.access_action_item(subclient, "Back up")

    @PageService()
    def action_subclient_backup_history(self, subclient):
        """
        Opens subclient backup history

        Args:
            subclient (str):name of the subclient

        Returns:
            None

        Raises:
            Exception:
                The subclient has not been backed up yet.
        """
        self._admin_console.log.info("Navigating to backup history for %s", subclient)
        self.__table.access_action_item(subclient, "Backup history")

    @PageService()
    def perform_fs_subclient_backup(self, subclient_name):
        """
        Method to Initiate Server Backup

        Args:
            subclient_name  (string)  : Name of the subclient for which backup is to be initiated

        Returns (int) : job id

        Raises:
            Exception:
                -- if fails to initiate backup
        """

        self.action_subclient_backup(subclient_name)
        backup = Backup(self._admin_console)
        return backup.submit_backup(backup.BackupType.FULL)

    @PageService()
    def initiate_content_based_subclient_restore(self, subclient_name):
        """
        Method to Initiate subclient restore

        Args:
            subclient_name   (string)       : Name of the subclient for which restore is to be
                                            initiated

        Returns:
            None

        Raises:
            Exception:
                -- if fails to initiate backup
        """
        table = Table(self._admin_console)
        table.access_link_by_column(subclient_name, 'Restore')

    @PageService()
    def delete_fs_subclient(self, subclient_name):
        """
        Method to delete a subclient

        Args:
           subclient_name  (string)    : Name of the subclient to be deleted

        Returns:
            None

        Raises:
            Exception:
                -- if fails to delete the subclient
        """

        self.__table.access_action_item(subclient_name, "Delete")
        self.__modal_dialog.type_text_and_delete("DELETE")
        self._admin_console.check_error_message()
        self._admin_console.log.info("Sub client Deleted successfully.")
