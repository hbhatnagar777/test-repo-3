# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This module provides the function or operations related to Storage in AdminConsole
NASHelper : This class provides methods for NAS related operations

NASHelper
===========

__init__(admin_console obj, csdb obj)  --  initialize object of ArrayHelper class associated


    delete_client()                 --  Deletes NAS Client
    add_server()                    -- Add NAS server from Array Management
    reconfigure_server()            --  Reconfigures the NAS server after adding the server from array management
    delete_array()                  -- Deletes the array from array management
    retire_server()                 --  Retire server after it has been deleted
    validate_retire_and_delete_server() --  Validates retire and deletion of the client

"""

from AutomationUtils import logger
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays, Engine
from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.database_helper import get_csdb
from Web.AdminConsole.Components.table import Rtable


class Nashelper():
    """ Helper for handling function calls for Array operations from ArrayDetails."""

    def __init__(self, admin_console, csdb=None):

        """Initialize object for ArrayHelper class.

            Args:
               admin_console:  (obj)   --  browser object

               csdb :   (obj)   -- database object

        """

        self.csdb = csdb
        self.log = logger.get_log()
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__navigator = admin_console.navigator
        self.fs_server_obj = FileServers(self.__admin_console)
        self.engine_obj = Engine(self.__admin_console, self.csdb)
        self.array_obj = Arrays(self.__admin_console)
        self.nhelper_obj = NASHelper()
        self.table = Rtable(self.__admin_console)
        self.array_vendor = None
        self.server_name = None
        self.array_user = None
        self.array_password = None
        self.controllers = None
        self.client_name = None
        self.array_control_host = None
        self.control_host = None
        self.csdb = get_csdb()

    def navigate_to_file_servers(self, select_file_server_tab=False):
        """
        Navigates to File Servers page and click on "File servers tab" (Only for metallic)
        """
        self.__navigator.navigate_to_file_servers()
        if select_file_server_tab:
            self.__admin_console.access_tab("File servers")

    def add_engine(self):
        """Creates Storage Array"""

        self.__navigator.navigate_to_arrays()

        # Add Array
        self.engine_obj.add_engine(self.array_vendor,
                                   self.server_name,
                                   self.array_user,
                                   self.array_password,
                                   self.control_host,
                                   self.controllers)


    def reconfigure_server(self):

        """Reconfigures Nas server"""

        self.__navigator.navigate_to_file_servers()
        self.__admin_console.access_tab("File servers")
        self.table.reload_data()
        self.fs_server_obj.reconfigure_server(self.server_name)

    def action_delete_array(self, server_name):

        """Delete Storage Array"""

        # Select Array to delete
        self.__navigator.navigate_to_arrays()
        self.array_obj.action_delete_array(server_name)

    def retire_server(self, server_name):
        """Reconfigures Nas server"""

        self.__navigator.navigate_to_file_servers()
        self.__admin_console.access_tab("File servers")
        self.table.access_action_item(server_name, self.__admin_console.props['action.commonAction.retire'])
        self.__admin_console.fill_form_by_id("confirmText",
                                             self.__admin_console.props['action.commonAction.retire'].upper())
        self.__admin_console.click_button_using_text(self.__admin_console.props['action.commonAction.retire'])

    def delete_client(self, server_name):
        """Delete the client once it is retired"""

        self.__navigator.navigate_to_file_servers()
        self.__admin_console.access_tab("File servers")
        self.fs_server_obj.delete_client(server_name)
        self.__admin_console.refresh_page()

    def update_client(self, server_name):
        """
              This method is to update the NAS server name from ArrayHostAlias table once nas server is added from Array Management
              Args:
                  server_name: the name of the server

        """

        query = "SELECT NAME FROM APP_Client where ID = (select ClientId from SMControlHost where SMArrayID = '{0}')".format(
            server_name)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.client_name = result[0]
        self.server_name = self.client_name

    def validate_retire_and_delete_server(self, server_name, should_delete_server=False):
        """
        Retires the specified server

        Args:
            server_name (str) : Display Name of the nas_server
            should_delete_server (bool) : True to delete server after retiring
                                        False to reconfigure later
        Returns:
            None
        Raise Exception if client was not retired
        """

        self.table.reload_data()
        self.table.search_for(server_name)
        data = self.table.get_table_data()
        self.table.clear_search()
        actions_list = self.table.get_grid_actions_list(server_name)
        self.__admin_console.refresh_page()

        if 'Retire' in actions_list:
            self.log.info(f"Retiring Sever : {server_name}")

            self.retire_server(server_name)

            self.__admin_console.wait_for_completion()

            self.log.info("Checking if the server was backed up atleast once")

            # If the client was never backed up, we delete the client.
            if data['Last backup'][0].lower() == 'never backed up':
                if self.fs_server_obj.is_client_exists(server_name):
                    raise Exception(f"The client {server_name} was never backed up but was not deleted after retire.")
                self.log.info(f"{server_name} is not in the table.")
                self.log.info(f"{server_name} was never backed up and successully deleted.")

                # Client is deleted after retiring, dont need to delete the client again
                should_delete_server = False
            else:
                # If the client was backed up, then we deconfigure the client.
                self.log.info(
                    "The server was backed up atleast once. Checking the actions list available for the server")

                # Check backup panel should not be there and Restore, Reconfigure, Delete should be there
                actions_list = self.table.get_grid_actions_list(server_name)
                self.log.info(f"Actions list for {server_name} are : {actions_list}")

                if 'Backup' in actions_list and \
                        not (all(action in actions_list for action in ['Restore', 'Reconfigure', 'Delete'])):
                    raise Exception("Either Backup action was present in the actions list or "
                                    "[Restore, Reconfigure, Delete] were not present on the retired server")

                self.log.info("Succesfully retired the server and checked actions list values")
                self.__admin_console.refresh_page()

        if should_delete_server:
            self.log.info(f"Deleting the server {server_name}")
            self.delete_client(server_name)
            self.__admin_console.wait_for_completion()
            self.log.info("Checking if the client exists in the table after deletion")
            self.table.reload_data()
            if self.fs_server_obj.is_client_exists(server_name):
                raise Exception(f"The client {server_name} was deleted but still present in the table.")
            self.log.info(f"{server_name} is successfully deleted.")
