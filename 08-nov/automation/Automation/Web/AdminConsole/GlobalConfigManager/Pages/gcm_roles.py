# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Module provides the methods to available for doing operations on Roles Page on Cloud Console.

GCMRoles: Helper class for performing UI operations related to Roles page on cloud console

Class:
    GCMRoles -> Roles

GCMRoles:
    __init__()                          --      Initialize instance of the GCMRoles class

"""
from Web.AdminConsole.AdminConsolePages.Roles import Roles
from Web.AdminConsole.adminconsole import AdminConsole


class GCMRoles(Roles):
    """Class to perform Roles listing related operations from cloud console"""

    def __init__(self, admin_console: AdminConsole) -> None:
        """Method to initialize GCMRoles class
        Args:
            admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console)
