# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Module provides the methods to available for doing operations on UserGroups Page on Cloud Console.

GCMUserGroups: Helper class for performing UI operations related to UserGroups page on cloud console

Class:
    GCMUserGroups -> UserGroups

GCMUserGroups:
    __init__()                          --      Initialize instance of the GCMUserGroups class

"""

from Web.AdminConsole.AdminConsolePages.UserGroups import UserGroups
from Web.AdminConsole.adminconsole import AdminConsole


class GCMUserGroups(UserGroups):
    """Class to perform User group listing related operations from cloud console"""

    def __init__(self, admin_console: AdminConsole) -> None:
        """Method to initialize GCMUserGroups class
        Args:
            admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console)
