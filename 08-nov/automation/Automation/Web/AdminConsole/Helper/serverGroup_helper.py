# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on server group page.

class:

    serverGroupMain()

functions:

    add_new_manual_server_group : calls method from main file to add manual serverGroups

    validate_listing_page_search : calls method from Rtable to validate if a server group is listed in listing page

    edit_serverGroup_name : method to rename a serverGroup

    edit_association : method to validate edit association action from action menu
"""
import time

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages import server_groups
from Web.AdminConsole.GlobalConfigManager import constants
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components import table, dialog


class ServerGroupMain:
    """
        Helper for server group page
    """

    def __init__(self, admin_console):
        """
        Initializes the server group helper module

            Args:
                admin_console  (object)   --  AdminConsole class object
        """
        self.driver = admin_console.driver
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__serverGroup = server_groups.ServerGroups(admin_console)
        self.__table = table.Rtable(self.__admin_console)
        self.__dialog = dialog.RModalDialog(self.__admin_console)
        self.serverGroup_name = f"ServerGroup{str(time.time()).split('.')[0]}"
        self.client_scope = None
        self.rules = [{"rule_for":"Agents Installed","matches_with":"any in","value":["Files","Protected files"]}]

        self.log = logger.get_log()
        self._server_name = None

    @property
    def serverGroup_name(self):
        """Get server group name"""
        return self._serverGroup_name

    @serverGroup_name.setter
    def serverGroup_name(self, value):
        """set server group name"""
        self._serverGroup_name = value

    @property
    def server_name(self):
        """get server name """
        return self._server_name

    @server_name.setter
    def server_name(self, value):
        """set server name"""
        self._server_name = value

    def add_new_manual_server_group(self):
        """ Method to add manual serverGroups"""
        self.__navigator.navigate_to_server_groups()
        self.__serverGroup.add_manual_server_group(self._serverGroup_name, self._server_name)

    def listing_page_search(self, name):
        """validate if a server group is listed"""
        self.__navigator.navigate_to_server_groups()
        if self.__serverGroup.is_serverGroup_exist(name):
            self.log.info('listing page search validation completed for the server group')
        else:
            raise CVWebAutomationException('server group not listed in listing page')

    def edit_serverGroup_name(self, new_name):
        """method to edit server group name"""
        self.__navigator.navigate_to_server_groups()
        self.__serverGroup.open_server_group(group_name=self.serverGroup_name)
        self.__admin_console.wait_for_completion()
        self.__serverGroup.edit_sg_name(new_name)

    def edit_association(self):
        """ function to add association """
        self.__navigator.navigate_to_server_groups()
        self.__serverGroup.edit_association(self._serverGroup_name, self._server_name)
        self.__admin_console.wait_for_completion()

    def add_automatic_server_group(self):
        """Helper method to add automatic server group"""
        self._serverGroup_name = 'Automatic' + self.serverGroup_name
        self.__navigator.navigate_to_server_groups()
        self.__serverGroup.add_automatic_server_group(
            self.serverGroup_name,
            self.client_scope,
            self.rules,
            self.service_commcells
        )

    def create_gcm(self, service_commcells: list = None) -> str:
        """Method to create server group from GCM"""
        self.serverGroup_name = 'GCM' + self.serverGroup_name
        if service_commcells:
            self.service_commcells = service_commcells
        else:
            self.service_commcells = ['All']

        self.client_scope = None
        self.add_automatic_server_group()
        return self.serverGroup_name + constants.GLOBAL_ENTITIES_EXT
