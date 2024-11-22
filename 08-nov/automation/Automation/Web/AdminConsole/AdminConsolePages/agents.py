# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
all the agents on the AdminConsole

Class:

    Agents()

Functions:

open_backupset_instance()        -- Opens the backupset or instance of the agent
"""
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService


class Agents:
    """
    This class provides the function or operations that can be performed on
    all the agents on the AdminConsole
    """

    def __init__(self, admin_console):
        self.__table = Table(admin_console)

    @PageService()
    def open_backupset_instance(self, name):
        """
        Opens the backupset or instance of the Agent

        Args:
            name (str): name of backupset or instance to open.

        Returns:
            None

        Raises:
            Exception:
                "There is no backupset/instance with the given name
        """
        self.__table.access_link(name)
