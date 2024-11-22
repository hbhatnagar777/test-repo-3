# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    SQLiteHelper is the only class in this file
"""
import os
import sqlite3
from AutomationUtils.machine import Machine


class SQLiteHelper:
    """
    Main file for performing queries on the SQLite (.dat) file

    SQLiteHelper:

    execute_dat_file_query()            --      Execute a query on the DAT file

    _copy_file_from_path()              --      Copy the SQLite (.dat) file from the remote machine to the local machine

    _execute_query()                    --      Execute read-only query on the given sqlite (.dat) file
    """
    def __init__(self, tc_object, proxy_machine=None, username=None, password=None, use_proxy=True):
        """
            Initializes the SQLiteHelper class

            Args:
                tc_object   (object)    -- Instance of the Test Case class

                proxy_machine (object)  -- Machine class object for the Proxy Machine

                username    (str)       -- Username of the Proxy Machine

                password    (str)       -- Password to log into the Proxy Machine
        """
        self.local_machine = Machine()
        self.tc_object = tc_object
        self.log = tc_object.log

        if use_proxy:
            if proxy_machine is None:
                # Create object with IP Address if your machine is not accessible with name
                self.proxy_machine_ip = self.tc_object.tcinputs["ProxyServerDetails"]["IpAddress"]
                self.username = self.tc_object.tcinputs["ProxyServerDetails"].get("Username", None)
                self.password = self.tc_object.tcinputs["ProxyServerDetails"].get("Password", None)

                self.proxy_machine = Machine(
                    self.proxy_machine_ip, tc_object.commcell, self.username, self.password
                )
            else:
                self.proxy_machine = proxy_machine
                self.username = username
                self.password = password

    def execute_dat_file_query(self, source_folder, file_name, query):
        """
            Execute the Query on the DAT file

            Args:
                source_folder   (str)   -- The folder in which dat file is present

                file_name       (str)   -- The name of the file

                query           (str)   -- The SQLite Query that is to be executed

            Returns:
                query-result    (list)  --  List of Rows returned by the query
        """
        dat_file_path = self.proxy_machine.join_path(source_folder, file_name)
        self.log.info("Using SQLite file: %s", dat_file_path)

        destination_path = os.getcwd()
        destination_file_path = self.local_machine.join_path(destination_path, file_name)
        self.log.info('Using destination path: %s', destination_file_path)

        if os.path.exists(destination_file_path):
            os.remove(destination_file_path)

        self._copy_file_from_path(dat_file_path, destination_path)

        self.log.info('Executing query: %s', query)
        results = self._execute_query(destination_file_path, query)

        self.log.info('Query returned results: %s', results)

        os.remove(destination_file_path)
        return results

    def _copy_file_from_path(self, dat_file_path, destination_path):
        """
            Function to copy a SQLite (.dat) file from the remote machine to the local machine

            Args:
                dat_file_path   (str)   -- The shared or local path where dat file is located

                destination_path (str)  -- Directory to copy the dat file to

            Returns:
                dat_file_local_path (str)   -- Complete local path to the dat file
        """
        if dat_file_path.startswith(r"\\"):
            self.log.info('Copying file from shared path: %s', dat_file_path)
        else:
            dat_file_path = self.proxy_machine.get_unc_path(path=dat_file_path)
            self.log.info('Copying file from unc path: %s', dat_file_path)

        self.local_machine.copy_from_network_share(
            dat_file_path, destination_path, self.username, self.password
        )

    def _execute_query(self, dat_file_path, query, is_read_only=True):
        """
        Execute read-only query on the given sqlite (.dat) file
        
        Args:
            dat_file_path (str)     -- Complete local path to the dat file

            query       (str)       -- Query that is to be executed

            is_read_only (bool)     -- Depends on the type of query you have passed
                                       If Query passed is to read the data [Select] then pass TRUE
                                       If Query passed is to write the data [Insert, Update] then pass FALSE
        Returns:
            Result of SQLite query
        """
        connection = sqlite3.connect(dat_file_path)

        cursor = connection.cursor()
        cursor.execute(query)

        if not is_read_only:
            connection.commit()

        results = cursor.fetchall()

        connection.close()
        return results

    def execute_query_locally(self, source_folder, file_name, query, is_read_only=True):
        """Execute query on local machine"""
        dat_file_path = self.local_machine.join_path(source_folder, file_name)
        self.log.info("Executing query %s", query)
        results = self._execute_query(dat_file_path, query, is_read_only)
        self.log.info("Results returned %s", results)
        return results