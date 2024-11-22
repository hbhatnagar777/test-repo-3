# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Helper file to help with Oracle database specific operations

OracleHelper is the only class defined in this file

OracleHelper: Helper class to perform Oracle operations

OracleHelper:
    __init__()                  -- Constructor of the class

    __del__()                   -- Destructor of the class

    _execute_ddl_dml()          -- Executes DDL and DMLs including merge

    _execute_query()            -- Executes the query and gives the result

    set_oracle_db_username()    -- Sets oracle database username

    set_oracle_db_password()    -- Sets oracle database password

    db_connect()                -- Connects to the database

    db_execute()                -- Executes DDLs, DMLs and Queries on the database

    db_shutdown()               -- Shuts down database

    db_startup()                -- Starts up database
"""
import cx_Oracle

from AutomationUtils import logger
from AutomationUtils.database_helper import get_csdb
from AutomationUtils import cvhelper
from AutomationUtils.database_helper import Oracle


class OracleHelper(object):
    """
        Class to work on oracle databases
    """

    def __init__(self, commcell, db_host, instance):
        """Initializes an Oracle Helper Instance

        Args:
            commcell    (obj)   -- commcell object to connect to
            instance    (obj)   -- instance object to connect to
            db_host     (str)   -- hostname of the client connecting to
        """
        self.log = logger.get_log()
        self.log.info('  Initializing Oracle Helper ...')
        # Commented as these are not required by any methods as of now
        self.commcell = commcell
        # self.client = client
        # self.agent = agent
        self.instance = instance
        # self.subclient = subclient
        self.csdb = get_csdb()
        self.db_host = db_host
        self.ora_instance = instance.instance_name
        self.ora_service_name = instance.instance_name  # Service name defaults to instance name
        self.ora_port = 1521
        self.ora_sys_user = self.set_oracle_db_username()
        self.ora_sys_password = self.set_oracle_db_password()
        self.ora_version = None
        # Instantiate instance variables to hold oracle database object
        self.oradb = None

    def set_oracle_db_username(self):
        """Gets the db username of the instance from commcell database

        Returns:
            Oracle database username

        Raises:
            Exception:
                if failed to get the db username of the instance
        """
        try:
            query = ("Select attrVal from app_instanceprop where componentNameId = {0} and"
                     " attrName = 'SQL Connect'".format(self.instance.instance_id))

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                return cur[0]
            else:
                raise Exception("Failed to get the Oracle client name from database")
        except Exception as exp:
            self.log.exception('Failed to get sys user name for the database')
            raise Exception(str(exp))

    def set_oracle_db_password(self):
        """Gets the db password of the instance from the commcell database

        Returns:
            Oracle database password

        Raises:
            Exception:
                -- if failed to get the db password of the instance
        """
        try:
            query = ("Select attrVal from app_instanceprop where componentNameId = {0} and"
                     " attrName = 'SQL Connect Password'".format(self.instance.instance_id))

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                password = cur[0]
                return cvhelper.format_string(self.commcell, password)
            else:
                raise Exception("Failed to get the Oracle client name from database")
        except Exception as exp:
            self.log.exception('Failed to set oracle sys user password')
            raise Exception(str(exp))

    def db_connect(self):
        """TODO: Doc String for db_connect"""
        self.oradb = Oracle(self.db_host, self.ora_instance, self.ora_sys_password,
                            self.ora_sys_user, self.ora_port, self.ora_service_name)

    def db_execute(self, query, commit=False):
        """
        Method to execute DDL/DML/DCL in the database

        Args:
            commit (str)    -- whether this query should be committed
            query   (str)   -- string representing the DDL/DML/DCL to be executed
        """
        self.oradb.execute(query, commit)

    def db_shutdown(self, mode):
        """Shut down the database

        Args:
            mode    (str)   -- Mode of shutdown to be given to the database
                SHUT_TRANSACTION    : shutdown using TRANSACTIONAL
                SHUT_FINAL          : shutdown using FINAL
                SHUT_ABORT          : shutdown using ABORT
                SHUT_IMMEDIATE      : shutdown using IMMEDIATE

        Raises:
            ValueError:
                -- If the database connection wasn't established
                -- If the mode for shutdown is invalid
            DatabaseError:
                -- Exception in shutting the database down
        """
        if self.connection is None:
            self.log.exception('  Connection to database has not been established')
            raise ValueError('Database connection not established for shutdown')
        try:
            if mode == 'TRANSACTIONAL':
                self.connection.shutdown(mode=cx_Oracle.DBSHUTDOWN_TRANSACTIONAL)
            elif mode == 'FINAL':
                self.connection.shutdown(mode=cx_Oracle.DBSHUTDOWN_FINAL)
            elif mode == 'ABORT':
                self.connection.shutdown(mode=cx_Oracle.DBSHUTDOWN_ABORT)
            elif mode == 'IMMEDIATE':
                self.connection.shutdown(mode=cx_Oracle.DBSHUTDOWN_IMMEDIATE)
            else:
                raise ValueError('Unrecognized mode for shutdown detected: {0}'
                                 .format(mode))
        except cx_Oracle.DatabaseError as str_err:
            self.log.exception('Error shutting The database {0} down: {1}'
                               .format(self.ora_instance, str_err))
            raise
        except ValueError as str_err:
            self.log.exception('Unrecognized value {0} for shutting down the database: {1}'
                               .format(mode, str_err))
            raise

    def db_startup(self):
        """
        Method to start up the database.

        Raises:
            DatabaseError   -- If the remote connection is rejected
        """
        self.dsn_tns = cx_Oracle.makedsn(self.ora_host_name, self.ora_port, self.ora_instance)
        try:
            self.connection = cx_Oracle.Connection(self.ora_sys_user,
                                                   self.ora_sys_password, self.dsn_tns,
                                                   mode=cx_Oracle.SYSDBA | cx_Oracle.PRELIM_AUTH)
            self.connection.startup()
        except cx_Oracle.DatabaseError as str_err:
            self.log.exception('Startup is not supported for remote database connections: {0}'
                               .format(str_err))
            raise
