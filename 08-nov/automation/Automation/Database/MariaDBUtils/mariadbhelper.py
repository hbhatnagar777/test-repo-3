# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing MariaDB operations

MariaDBHelper is the only class defined in this file

MariaDBHelper: Helper class to perform MariaDB operations

MariaDBHelper:
============
    __init__()                          --  initializes MariaDBHelper object

    _get_mysql_database_connection()    --  Method for database connection

"""
from AutomationUtils import database_helper
from Database.MySQLUtils.mysqlhelper import MYSQLHelper


class MariaDBHelper(MYSQLHelper):
    """Helper class to perform MariaDB operations"""

    def __init__(self, commcell, instance, subclient, user, port, ssl_ca):
        """Initializes MariaDBHelper object"""
        self.mysql_instance = instance
        self.ssl = self.mysql_instance.ssl_enabled

        super().__init__(commcell=commcell, subclient=subclient, instance=instance, user=user, port=port, ssl_ca=ssl_ca)

    def _get_mysql_database_connection(self, database=None):
        """
        Get the mariadb database connection
        Args:
                database    (str)  -- Database name
                            default value None
            Returns:
                MariaDB database connection object
        """
        mysql_db_connection_object = database_helper.MariaDB(self.host_name,
                                                             self.usr, self.pwd, self.mysql_port, database,
                                                             self.ssl)

        self.mysql_db_connection_object = mysql_db_connection_object

        return self.mysql_db_connection_object
