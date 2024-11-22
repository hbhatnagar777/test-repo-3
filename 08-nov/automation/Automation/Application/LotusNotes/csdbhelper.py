# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Helper for LN CSDB automation operations

    LNDOCHelper:
        __init__(testcase)          --  Initialize the csdbhelper object

        fetch_subclient_content     --  Gets the database names present in a subclient

"""

from AutomationUtils import database_helper
from .sql_queries import SQL_QUERY_DICT
from .constants import ATTR_TYPE


class CSDBHelper:
    """"Contains helper functions for LN Agent related automation tasks
    """

    def __init__(self, testcase):
        """"Initializes the LNDOC Helper class object

                Properties to be initialized:
                    tc          (object)    --  testcase object

                    dbhelper    (object)    --  object of CSDB

                    log         (object)    --  object of the logger class

        """
        self.tc = testcase
        self.dbhelper = database_helper.get_csdb()
        self.log = testcase.log

    def fetch_subclient_content(self):
        """"Gets the database names present in a subclient

            Returns:
                list    - list of database names

        """
        result = []
        query = SQL_QUERY_DICT['GetSubclientProperties'] % (
            self.tc.subclient.subclient_id,
            ATTR_TYPE[self.tc.agent.agent_name]
        )
        self.dbhelper.execute(query)
        for _ in self.dbhelper.fetch_all_rows():
            self.log.info(_[0])
            database = _[0].replace('\\', '', 1).replace('.nsf', '')
            if database[:1] == '/':
                database = database[1:]
            result.append(database)
        return result
