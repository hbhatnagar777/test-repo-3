# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods to perform actions on application.


Classes:


Applications  --  This class contains methods to perform actions on application like opening a
                  application, run backup/restore....

    Functions:

    open_application()                  --  Opens application with the given name

    open_appgroup_of_application()      --  Opens the application group corresponding to the application

    action_remove_application()         --  Removes the application from the list of backed up applications

    action_application_jobs()           --  Displays all the jobs of the given application

    action_application_backup()         --  Backups the given application

    action_application_restore()        --  Restores the given application

    run_validate_backup()               --  Runs backup validation job

"""
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import PageService


class Applications:
    """
     This class contains methods to perform actions on vm like opening a vm, opening a server of \
     vm, listing backup vms etc.
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(self)

    @PageService()
    def open_application(self, application_name):
        """
        Opens application with the given name

        Args:
            application_name     (str):   name of the Application to open

        """
        self.__table.access_link(application_name)

    @PageService()
    def open_appgroup_of_application(self, application_name):
        """
        Opens the application group corresponding to the provided application

        Args:
            application_name (str):  the name of the application whose application group has to be opened

        """
        self.__table.access_link_by_column(application_name, self._admin_console.props['label.applicationGroup'])

    @PageService()
    def action_remove_application(self, application_name):
        """
        Removes the application from the list of backed up Applications

        Args:
            application_name  (str):  the name of the application to remove

        """
        self.__table.access_action_item(application_name, self._admin_console.props['label.doNotBackup'])
        self._admin_console.click_button('Yes')

    @PageService()
    def action_application_jobs(self, application_name):
        """
        Displays all the jobs of the given application

        Args:
            application_name  (str):  the name of the application whose jobs to open

        """
        self.__table.access_action_item(application_name, self._admin_console.props['action.jobs'])

    @PageService()
    def action_application_backup(self, application_name):
        """
        Backups the given application

        Args:
            application_name  (str):      the name of the application to backup

        Returns:
            job_id  (int):  the backup job ID

        """
        self.__table.access_action_item(application_name, self._admin_console.props['action.backup'])
        backup = RBackup(self)
        return backup.submit_backup(backup.BackupType.INCR)

    @PageService()
    def action_application_restore(self, application_name):
        """
        Restores the given application

        Args:
            application_name  (str):  the name of the application to restore

        """
        self.__table.access_action_item(application_name, self._admin_console.props['label.restore'])
