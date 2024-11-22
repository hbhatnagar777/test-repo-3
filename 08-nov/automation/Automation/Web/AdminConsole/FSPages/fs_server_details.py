# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions or operations that can be performed on the
a selected client on the AdminConsole

Class:

    FsServerDetails() -> ServerDetails() -> _Navigator() -> AdminConsoleBase() -> object()

Functions:

action_add_backupset()  -- add a backup set to the client

"""

from Web.AdminConsole.AdminConsolePages.server_details import ServerDetails
from Web.Common.page_object import PageService


class FsServerDetails(ServerDetails):
    """
    This class provides the functions or operations that can be performed on the
    a selected client on the AdminConsole
    """

    @PageService()
    def action_add_backupset(self, backupset, plan):
        """
        Add backupset of file system type.
        Args:
            backupset (str):name of the backupset we want to associate with a FS server

        Returns:
            None

        Raises:
            Exception:
                The error message displayed

        """
        self.__table.access_action_item('File System', "Add BackupSet")
        self.fill_form_by_id("backupSetName", backupset)
        self.cvselect_from_dropdown("Plan", plan)
        self.submit_form()
        self.check_error_message()
