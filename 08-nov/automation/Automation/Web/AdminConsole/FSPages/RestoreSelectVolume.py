# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed
while selecting the restore volume on the AdminConsole

Class:

    RestoreSelectVolume() -> AdminConsole() -> AdminConsoleBase() -> object()

Functions:

select_volume()          -- select and open a volume

"""

from Web.Common.page_object import WebAction


class RestoreSelectVolume:
    """
    This class provides the function or operations that can be performed
    while selecting the restore volume on the AdminConsole
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console

    @WebAction()
    def select_volume(self, volume):
        """Opens the volume for further browsing.
            volume   : a string, volume label we want to select
        """
        self._admin_console.log.info("Selecting the volumes for restore")
        if self._admin_console.check_if_entity_exists("link", volume):
            self._admin_console.select_hyperlink(volume)
        else:
            raise Exception("There is no volume with the given name")
