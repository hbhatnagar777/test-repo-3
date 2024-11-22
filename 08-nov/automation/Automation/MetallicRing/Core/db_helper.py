# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" helper class for executing DB queries in Metallic Ring

    DBQueryHelper:

        __init__()                  --  Initializes DB query helper

        execute_select_query        --  Executes a given select SQL query against commserve database and
                                        returns the result

"""

from AutomationUtils import logger
from AutomationUtils.database_helper import CommServDatabase


class DBQueryHelper:
    """ helper class for executing DB queries in Metallic Ring """

    def __init__(self, commcell):
        self.log = logger.get_log()
        self.commcell = commcell
        self.sqlobj = None
        self.csdb = CommServDatabase(commcell)

    def execute_select_query(self, query):
        """
        Executes a given select SQL query against commserve database and returns the result
        Args:
            query(str)      -   Query to be executed against Commserve Database
        Returns:
            list            -   List of rows returned from the query execution
        """
        self.log.info(f"Executing the following query against CS DB [{query}]")
        self.csdb.execute(query)
        result = self.csdb.rows
        self.log.info(f"Result of query execution - [{result}]")
        return result
