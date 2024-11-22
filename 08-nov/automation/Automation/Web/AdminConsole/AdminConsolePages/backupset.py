# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
backupset page of any agent on the AdminConsole

Class:

    Backupset()

Functions:

open_subclient()        -- open the server group

action_subclient_restore() -- Opens the subclient content for restore browse

"""
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService


class Backupset:
    """
    This class provides the function or operations that can be performed on the
    backup set / instance level of all agents on the AdminConsole
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)
        self.driver = self._admin_console.driver

    @PageService()
    def open_subclient(self, subclient):
        """
        Opens the subclient with the given name

        Args:
            subclient (str): name of the subclient

        Returns:
            None

        Raises:
            Exception:There is no subclient with the name

        """
        self.__table.access_link(subclient)

    @PageService()
    def action_subclient_restore(self, subclient):
        """
        Opens the subclient content for restore browse.
        Args:
            subclient (str):name of the subclient

        Returns:
            None

        Raises:
            Exception:
                The subclient has not been backed up yet.
        """
        self.__table.access_action_item(subclient, "Restore")
