# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" helper class for executing sqlite DB queries for tracking the automation progress

    DBQueryHelper:

        __init__()                  --  Initializes DB query helper

        execute_query               --  Executes a give SQL query against sqlite database and returns the result

"""

from AutomationUtils import logger
from AutomationUtils.database_helper import SQLite
from MetallicRing.Utils import Constants as cs


class SQLiteDBQueryHelper:
    """ helper class for executing sqlite DB queries for tracking the automation progress """

    def __init__(self):
        self.log = logger.get_log()
        self.sqlitedb = SQLite(cs.SQLLITE_DB_CONFIG_FILE_PATH)

    def execute_query(self, query):
        """
        Executes a given SQL query against sqlite database and returns the result
        Args:
            query(str)          -   Executes a given query against sqlite Database
        """
        self.log.info(f"Executing the following query - [{query}]")
        result = self.sqlitedb.execute(query)
        self.log.info(f"Result of query execution - [{result}]")
        return result
