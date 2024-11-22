# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper File for Database related operations.

This file consists of a class `DBResponse` for executing and parsing the Database query,
and its response.

A common Base class `Database` is defined to execute queries on any Database - MSSQL / MySQL, etc.

Another class `DBHelper` is defined to execute queries on the Commvault databases, like,

    CommServ Database   (CSDB)

    WFEngine Database   (WFDB)


Classes defined in this file:

    DBResponse:         Class for executing an SQL query, and parsing the response received

    Database:           Base class for all types of Databases - MSSQL / MySQL / SQLite, etc.

    MSSQL:              Derived class from the Database class, to perform operations, and queries
                            specific to Microsoft SQL Server Database

    Oracle:             Derived class from the Database class, to perform operations, and queries
                            specific to Oracle Database
        add_datafile            --  Add datafile for the given tablespace and location

        fetch_dbf_location      --  Fetchs the datafile location

        create_tablespace       --  Create Tablespace

        alter_tablespace        --  Alters the given tablespace

        drop_tablespace         --  Drops the given tablespace

        set_user_name           --  Set the user name

        create_user             --  Creates the user in default tablespace

        drop_user               --  Deletes the user

        create_table            --  Creates the table for given tablespace

        drop_table              --  Drops the given table for the specified user

        populate_table          --  Populates the data in the given table}

        tablespace_validate     --  Validates the given tables spaces

        table_validate          --  Validates the given table

        get_current_scn         --  Fetches current SCN

    MySQL:              Derived class from the Database class, to perform operations, and queries
                            specific MySQL Database

        __init__()                --  Constructor for creating a connection to MySQL Database

        _connect()                --  Establishes a connection to the MySQL Database using
        the details provided

        create_db()               --  Creates database with a given name in the specified
        mysql server

        drop_db()                 --  Drops the specified database

        check_if_db_exists()      --  Checks if the given databases exists or not

        get_db_list()             --  Gets the list of databases from a MySQL server

        start_slave()             --  Starts the slave in mysql server

        stop_slave()              --  Stops the slave in mysql server

        slave_status()            --  Checks the slave status in mysql server

        get_binary_logs()         --  fetches the binary log information from mysql server

    Informix:           Derived class from the Database class, to perform operations, and queries
                            specific to Informix Database

        __init__()                --  constructor for creating a connection to Informix Database

        _connect()                --  establishes a connection to the Informix Database using
        the details provided

        list_dbspace()            --  Lists all dbspaces in the server

        drop_database()           --  Drops a database if it exists

        get_database_list()       --  Gets all the database names in the server

        check_if_db_exists()      --  Checks if the specified database exists

        row_count()               --  Returns number of rows in the table specified

    SQLite:             Derived class from the Database class, to perform operations, and queries
                            specific a SQLite Database

    SAPHANA:            Derived class from the Database class, to perform operations, and queries
                            specific to a SAPHANA Database

    Db2 : Derived class from the Database class, to perform operations, and queries
                            specific to DB2 Database

        __init__()              --  constructor for creating a connection to db2 database

        _connect()              --  establishes connection to db2 database using the provided details

        connect_db2_instance()  --  establishes connection to db2 database at db2 instance level

        drop_table()            --  drops given table name from db2 database

        create_table_space()    --  creates a tablespace

        insert_data()           --  inserts data into given tables

        get_table_content()     --  get contents of a particular table

        exec_tablespace_query() --  executes give db2 query related to tablespaces

        get_tablespaces()       --  get number of tablespaces in database

        create_table()          --  creates table in given tablespace

    PostgreSQL:         Derived class from the Database class, to perform operations, and queries
                            specific to a PostgreSQL Database

        __init__()                --  Constructor for creating a connection to PostgreSQL Database

        _connect()                --  Connect to the PostGreSQL Server and return
        connection object

        create_db()               --  Creates database with a given name in
        the specified postgres server

        create_tablespace()       --  Creates tablespace in given location in the specified
        postgres server

        create_tablespace_db()    --  Creates database with a given name in the specified postgres server
        under the specified tablespace

        drop_db()                 --  Drops the specified database

        drop_tablespace()         --  Drops the specified tablespace

        check_if_db_exists()      --  Checks if the given databases exists or not

        get_db_list()             --  Gets the list of databases from a PostgreSQL server

    MariaDB:              Derived class from the Database class, to perform operations, and queries
                            specific MariaDB Database

        __init__()                --  Constructor for creating a connection to MariaDB Database

        _connect()                --  Establishes a connection to the MariaDB Database using
        the details provided

        create_db()               --  Creates database with a given name in the specified
        MariaDB server

        drop_db()                 --  Drops the specified database

        check_if_db_exists()      --  Checks if the given databases exists or not

        get_db_list()             --  Gets the list of databases from a MariaDB server


    DBHelper:           Base class for CommServ and WFEngine Database operations

    CommServDatabase:   Derived class from the DBHelper class to perform operations, and SELECT
                            queries on the CommServ Database

    WFEngineDatabase:   Derived class from the DBHelper class to perform operations, and SELECT
                            queries on the WFEngine Database

    CSDBOperations:     Base class for CommServ Database operations with execute access using MSSQL object

Usage
=====

- First create an object of the specific database, you want to connect to. (MSSQL in this case)

    >>> from AutomationUtils.database_helper import MSSQL
    >>> mssql = MSSQL(server, user, password, database, as_dict, autocommit)


- Executing a query:

    >>> db_response = mssql.execute('SELECT * FROM TABLE_NAME')


- Get list of columns:

    >>> db_response.columns


- Get the SQL Query that was executed:

    >>> db_response.query


- Get the count of rows returned in the response

    >>> db_response.rowcount


- Get the list of rows returned in the response

    >>> db_response.rows

"""

import re
import time

from AutomationUtils import logger
from AutomationUtils import machine
from AutomationUtils import defines
from . import cvhelper


class DBResponse(object):
    """Response received from Database upon running the SQL query.

        Creates a Cursor object using the connection object provided in the arguments, and
            runs the given query on the Database.

        Then it parses through the Database response, and updates the class attributes.

            columns:    list of columns of the table, the query was ran for

            rows:       list of rows returned

            rowcount:   no. of rows in the result

            query:      SQL query executed

            data:       data passed along with the query
    """

    def __init__(
            self,
            connection_object,
            query,
            data=None,
            commit=True,
            is_stored_procedure=False):
        """Creates a DBResponse object, after executing a SQL query on the Database.

            Args:
                connection_object   (object)    --  object of the Connection class to the Database

                query               (str)       --  string SQL query to be executed

                data                (sequence)  --  data to be passed to the query
                    default: None

                commit              (bool)      --  commit after executing the query
                    default: True

                is_stored_procedure (bool)      --  whether the query is a stored procedure
                    default: False
        """
        self._cursor = connection_object.cursor()
        self._query = query
        self._data = data
        self._commit = commit
        self._is_stored_procedure = is_stored_procedure
        self._columns = None
        self._rows = None
        self._rowcount = None
        self._update()

    def _get_columns(self):
        """Gets all the columns of the table for which SQL query was ran,
            and updates the columns attribute.
        """
        if self._cursor.description is None:
            return

        all_columns = self._cursor.description

        self._columns = []

        for column in all_columns:
            self._columns.append(column[0])

    def _update(self):
        """Executes the SQL query, and updates the class attributes with the response."""
        try:
            if self._is_stored_procedure is True:
                output = None
                if self.data:
                    # cursor.execute() using pyodbc requires lot of extra code to get return
                    # values from SP. Hence adding separate code path for pymssql cursor which has a
                    # support of callproc() function
                    try:
                        from pymssql import Cursor
                        if isinstance(self._cursor, Cursor):
                            output = self._cursor.callproc(procname=self.query, parameters=self.data)
                    except ImportError:
                        output = self._cursor.execute(self.query, self.data)
                else:
                    output = self._cursor.execute(self.query)

                if output:
                    self._rows = []
                    for out in output:
                        self._rows.append(out)
                    self._rowcount = len(self._rows)
                else:
                    self._rowcount = 0

            else:
                if self.data is None:
                    self._cursor.execute(self.query)
                else:
                    if isinstance(self.data, list):
                        self._cursor.executemany(self.query, self.data)
                    elif isinstance(self.data, (dict, tuple)):
                        self._cursor.execute(self.query, self.data)
                    else:
                        raise Exception(
                            'Data must of type list / tuple / dict')

            if self._commit is True:
                self._cursor.connection.commit()
        except Exception as excp:
            raise Exception(
                'Failed to execute the SQL query\nError: "{0}"'.format(excp))

        try:
            if self._rows is None:
                self._rows = self._cursor.fetchall()
            self._rowcount = len(self._rows)
        except Exception as e:
            # raises OperationalError Statement not executed or executed statement has no resultset
            # pass if it was an INSERT / UPDATE query
            pass

        self._get_columns()

        if self._is_stored_procedure is False:
            self._rowcount = self._cursor.rowcount

        self._cursor.close()

        del self._cursor

    @property
    def query(self):
        """Returns the SQL query executed on the Databse, for this response object."""
        return self._query

    @property
    def data(self):
        """Returns the input data for the SQL query."""
        return self._data

    @property
    def columns(self):
        """Returns the list consisting of columns of the Table the SQL query was ran on."""
        return self._columns

    @property
    def rows(self):
        """Returns the list of lists, consisting of the response from the SQL query,
            where each list represents a single SQL Table row.
        """
        return self._rows

    @property
    def rowcount(self):
        """Returns the number of rows in the response received."""
        return self._rowcount

    def get_column(self, row, column):
        """Returns the column value for the given row, column(s)

            Args:
                row             (tuple)         The row to get the column for

                column         (str/list)           The column name in the row to be retrieved

            Returns:
                (str/list)      --   The column value for the given row and column(s)

            Raises:
                 Exception when column name is invalid

            Example:
                get_row(row, 'name') -- Returns the value of name column

                get_row(row, ['name', 'age']) --  Returns a list of column values

        """

        # If multiple columns are requested, convert them into a list
        if isinstance(column, str):
            req_columns = [column]
        elif isinstance(column, list):
            req_columns = column
        else:
            raise Exception('Column to get value for should be a string or a list of columns')

        # Loop through every column, check if it is valid column name & get its value from the row
        column_values = []
        for col in req_columns:
            if col in self.columns:
                column_index = self.columns.index(col)
                column_values.append(row[column_index])
            else:
                raise Exception(
                    'Column "{0}" does not exist. Please check the column name'.format(col))

        # Return single column value if only one column was requested else return a list of values
        if isinstance(column, str):
            return column_values[0]
        else:
            return column_values

    def filter_response(self, column, value):
        """Filters out only the rows where column's value is equal to the input value."""

        if column not in self.columns:
            raise Exception(
                'Column does not exist. Please check the column name again')

        return filter(lambda x: x[column] == value, self.rows)


class Database(object):
    """Helper class for Database related operations."""

    def __init__(self):
        self._connection = None
        self._connect()
        self.log = logger.get_log()

    def __enter__(self):
        """Returns the current instance.

            Returns:
                object - the initialized instance referred by self
        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Closes the connection to the Database."""
        if self.connection:
            self.connection.close()
            self._connection = None

    def __del__(self):
        """Closes the connection to the Database."""
        if self.connection:
            self.connection.close()
            self._connection = None

    @property
    def connection(self):
        """Treats the database connection object as a read-only attribute."""
        return self._connection

    def _connect(self):
        raise NotImplementedError('Method not Implemented')

    def reconnect(self):
        """Re-establishes the connection to the database, if the connection is not alive."""
        try:
            cursor = self.connection.cursor()

            try:
                if isinstance(self, MSSQL):
                    cursor.execute('SELECT * FROM sys.databases')
                elif isinstance(self, MySQL):
                    cursor.execute('SHOW DATABASES')
                elif isinstance(self, SQLite):
                    cursor.execute('.databases')
                elif isinstance(self, SAPHANA):
                    cursor.execute('SELECT * FROM schemas')
                elif isinstance(self, SAPOracle):
                    cursor.execute('SELECT status from v$instance')
                elif isinstance(self, Oracle):
                    cursor.execute('SELECT open_mode from v$database')
                elif isinstance(self, PostgreSQL):
                    cursor.execute('select datname from pg_database')
            except Exception:
                self._connect()
        except Exception:
            self._connect()

    def execute(self, query, data=None, commit=True):
        """Executes the query on the Database and returns the results."""
        if self.connection:
            self.reconnect()
            return DBResponse(self.connection, query, data, commit)

    def execute_storedprocedure(self, procedure, parameters, commit=True):
        """Executes the query on the Database and returns the results."""
        if self.connection:
            self.reconnect()
            return DBResponse(
                self.connection,
                procedure,
                parameters,
                commit,
                is_stored_procedure=True)

    def execute_stored_procedure(self, procedure_name, parameters):
        """Executes the query on the Database and returns the results."""
        if self.connection:
            self.reconnect()
            return DBResponse(
                self.connection, procedure_name, parameters, is_stored_procedure=True
            )

    def close(self):
        """Closes the connection to the Database."""
        if self.connection:
            self.connection.close()
            self._connection = None


class Oracle(Database):
    """
        Helper class for Oracle Database related operations
        The helper is designed to operate idependently of the client side oracle home settings
    """
    CONN_SYSBACKUP = 'SYSBACKUP'
    CONN_SYSDBA = 'SYSDBA'
    CONN_DB_USER = 'DBUSER'
    SHUT_TRANSACTION = 'TRANSACTIONAL'
    SHUT_FINAL = 'FINAL'
    SHUT_ABORT = 'ABORT'
    SHUT_IMMEDIATE = 'IMMEDIATE'

    def __init__(self, client, instance_name, sys_password, sys_user=None,
                 port=1521, service_name=None, mode=None, host_name=None, rds=False):
        """ Constructor for creating the Oracle Database connection

            Args:
                client (obj)        -- Client object to connect to.

                instance_name (str) -- Name of the instance

                sys_password (str)  -- The SYS user password

                sys_user (str)      -- Backup user name
                    default -- SYS
                port (int)          -- port number for the listener.
                    default -- 1521
                service_name (str)  -- service name of the instance
                    default -- defaults to instance name
                mode (str)  -- role of the DBA connection
                    default -- SYSDBA
                host_name  (str) -- Public IP of the client
                    default -- None
                rds (bool) -- True if the database is RDS
                    default -- False
            Returns:
                object  -   connection object to the Oracle database

            Raises:
                Exception:
                    if module ``Oracle`` is not installed

                    if failed to connect to the database

        """

        # Instantiate instance variables to hold oracle specific properties
        self.rds = rds
        if self.rds is False:
            self.client_machine = machine.Machine(client)
            self.client = self.client_machine.machine_name
        self.ora_host_name = host_name or self.client_machine.ip_address
        self.ora_instance = instance_name
        self.ora_port = port
        self.ora_sys_password = sys_password
        self.ora_version = None
        # Service name defaults to instance name
        if service_name is None:
            self.ora_service_name = instance_name
        else:
            self.ora_service_name = service_name
        if sys_user is None:
            self.ora_sys_user = 'sys'
        else:
            self.ora_sys_user = sys_user
        self.dsn_tns = None
        # self._connect()
        if mode is None:
            self.mode = 'SYSDBA'
        else:
            self.mode = mode
        self.log = logger.get_log()
        super(Oracle, self).__init__()

    @property
    def connection(self):
        """Treats the database connection object as a read-only attribute."""
        return self._connection

    def _connect(self):
        """
        Method to establish a connection to the database

            Args:
                mode (str/enum) -- DBA role connection

            Raises:
                Exception: If the DSN conn cant be made

                ImportError: If the import fails

                AttributeError: If the mode specified is invalid

                OperationError: If the connection can't be established

        """
        try:
            import oracledb
        except ImportError:
            raise

        try:
            try:
                self.dsn_tns = oracledb.makedsn(self.ora_host_name, self.ora_port,
                                                 self.ora_instance)
            except Exception as err:
                self.dsn_tns = oracledb.makedsn(self.ora_host_name, self.ora_port,
                                                 service_name=self.ora_service_name)
        except Exception:  # DSN conn is must. Else raise exception. Let the caller handle it
            raise

        try:
            if self.mode == 'SYSDBA':
                self._connection = oracledb.connect(user=self.ora_sys_user, password=self.ora_sys_password,
                                                     dsn=self.dsn_tns, mode=oracledb.SYSDBA)
            elif self.mode == 'SYSBACKUP':
                self._connection = oracledb.connect(user=self.ora_sys_user, password=self.ora_sys_password,
                                                     dsn=self.dsn_tns, mode=oracledb.SYSBACKUP)
            elif self.mode == 'DBUSER':
                self._connection = oracledb.connect(user=self.ora_sys_user,
                                                     password=self.ora_sys_password, dsn=self.dsn_tns)
            else:
                raise AttributeError('Unrecognized mode to connect to database: {0}'
                                     .format(self.mode))
        except oracledb.OperationalError:
            raise
        else:
            self.ora_version = self.connection.version

    def add_datafile(self, tablespace_name, location, startnum=1, num_files=1):
        """
            Method to create a tablespace with the a specified number of datafiles

                Args:
                    tablespace_name (str)   --    Name given to the created tablespace

                    location    (str)   --  The datafiles path associated with the tablespace

                    startnum    (int)   --  no.of.files existing in the tablespace
                        default: 1

                    num_files   (int)   --  no.of.files to be added to the tablespace
                        default: 1

                Raises:
                    Exception:
                        If the datafiles can't be added

        """
        try:
            for i in range(startnum, startnum + num_files):
                self.log.info("adding the datafile in the location %s", location)
                if self.rds:
                    self.execute("alter tablespace {0} add datafile size 10M".format(
                        tablespace_name))
                else:
                    self.execute("alter tablespace {0} add datafile '{1}{2}.dbf' size 10M reuse".format(
                        tablespace_name,
                        self.client_machine.join_path(location, tablespace_name), str(i)))
                self.log.info("datafile added to the tablespace")
        except Exception as str_err:
            self.log.exception('Unable to add datafiles to the tablespace: %s', str_err)
            raise

    def get_current_scn(self):
        """
        Gets current SCN of database

        Returns:
                (int)     --  current SCN
        """
        try:
            result = self.execute("select current_scn from v$database")
            if result.rowcount != 0:
                result = result.rows[0][0]
                self.log.info("Current SCN : %s", result)

            else:
                raise Exception("no output")

            return result
        except Exception as err:
            self.log.exception("Exception caught: %s", err)
            raise

    def fetch_dbf_location(self):
        """
        Fetches default Oracle DBF location

        Returns:
                (str)     --  The default dbf location
        """
        try:
            sep = self.client_machine.os_sep
            query = "SELECT DISTINCT SUBSTR (file_name, 1, INSTR (file_name, '{0}', -1,1)) " \
                    "FROM DBA_DATA_FILES WHERE tablespace_name = 'SYSTEM'".format(sep)
            result = self.execute(query)
            if result.rowcount != 0:
                result = result.rows[0][0]
                self.log.info("Default DBF location : %s", result)

            return result
        except Exception as err:
            self.log.exception("Exception caught: %s", err)
            raise

    def create_tablespace(self, tablespace_name, location, num_files):
        """
        Method to create a tablespace with the a specified number of datafiles

            Args:
                tablespace_name (str)   --    Name given to the newly created tablespace

                location    (str)   --  The datafiles path associated with the tablespace

                num_files   (int)   --  No.of. files tablespace should have at the time of creation

            Raises:
                Exception:
                    If the tablespace can't be created

        """
        try:
            result = self.execute(
                "select tablespace_name from dba_tablespaces where tablespace_name = '{0}'".format(
                    tablespace_name.upper()))

            if result.rowcount != 0:
                tablespaces = result.rows[0][0]
                self.log.info("Tablespaces: %s", tablespaces)
                if str(tablespaces) == tablespace_name.upper():
                    self.execute(
                        "drop tablespace {0} including contents "
                        "and datafiles cascade constraints".format(tablespace_name))
                    if self.rds:
                        self.execute(
                            "create tablespace {0} datafile size 10M ".format(
                                tablespace_name))
                    else:
                        self.execute(
                            "create tablespace {0} datafile '{1}.dbf' size 10M ".format(
                                tablespace_name, self.client_machine.join_path(
                                    location, tablespace_name)))
                    self.log.info("dropped and created a new tablespace")
            else:
                if self.rds:
                    self.execute("create tablespace {0} datafile size 10M".format(
                        tablespace_name))
                else:
                    self.execute("create tablespace {0} datafile '{1}.dbf' size 10M reuse".format(
                        tablespace_name, self.client_machine.join_path(location, tablespace_name)))
                self.log.info("tablespace created")

            if not self.rds:
                self.add_datafile(tablespace_name, location, 1, num_files)

        except Exception as str_err:
            self.log.exception('Unable to create tablespace: %s', str_err)
            raise

    def alter_tablespace(self, tablespace_name, location, num_files):
        """
        Method to alter the tablespace by adding additional number of files

            Args:
                tablespace_name (str)   --    Name given to the newly created tablespace

                location    (str)   --  The datafiles path associated with the tablespace

                num_files   (int)   --  No.of. files to be added to the tablespace

            Raises:
                Exception:
                    If the table can't be altered/modified

        """
        try:

            result = self.execute(
                "select tablespace_name from dba_tablespaces where tablespace_name = '{0}'".format(
                    tablespace_name.upper()))
            if result.rowcount != 0:
                tablespaces = result.rows[0][0]
                self.log.info("Tablespaces: %s", tablespaces)
                if str(tablespaces) == tablespace_name.upper():
                    res = self.execute(
                        "select count(file_name) from dba_data_files "
                        "where tablespace_name = '{0}'".format(tablespace_name.upper()))
                    num_of_files = res.rows[0][0]
                    self.add_datafile(
                        tablespaces,
                        location,
                        num_of_files,
                        num_files)
                    self.log.info("altered the tablespace: '%s'", tablespaces)
            else:
                self.log.info("tablespace doesn't exist to alter")

        except Exception as str_err:
            self.log.exception('Unable to alter tablespace: %s', str_err)
            raise

    def is_cdb(self):
        """
        Returns true if the database is a CDB
        """
        try:
            cdb_res = self.execute("select cdb from v$database")
            if cdb_res.rowcount != 0:
                if cdb_res.rows[0][0] == 'YES':
                    return True
                return False
            else:
                raise Exception("No output returned for query")
        except Exception as err:
            self.log.exception("Exception caught: %s", err)
            raise

    def drop_tablespace(self, tablespace_name):
        """
        Method to drop tablespace and its datafiles
            Args:
                tablespace_name (str)   --    Name given to the newly created tablespace
            Raises:
                Exception:
                    If the tablespace can't be dropped
        """
        try:
            result = self.execute(
                "select tablespace_name from dba_tablespaces where tablespace_name = '{0}'".format(
                    tablespace_name.upper()))

            if result.rowcount != 0:
                tablespaces = result.rows[0][0]
                self.log.info("Tablespaces: %s", tablespaces)
                if str(tablespaces) == tablespace_name.upper():
                    self.execute(
                        "drop tablespace {0} including contents "
                        "and datafiles cascade constraints".format(tablespace_name))
                    self.log.info("dropped tablespace")

        except Exception as str_err:
            self.log.exception('Unable to drop tablespace: %s', str_err)
            raise

    def set_user_name(self, user):
        """
        Method to set the username in compliance with database type and version

            Args:
                user    (str)   --  The name of the newly create user/schema

            Returns:
                (str)   --  Modified username based on the db version convention
                Example:
                    For version 12c:
                        For CDB, username will be prefixed with c##

            Raises:
                Exception:
                    If the user name cannot be created
        """
        try:
            result = self.execute("select version from v$instance")

            if result.rowcount != 0:
                version = result.rows[0][0]
                self.log.info("Database version : %s", version)

                if version.split(".")[0] == '12':
                    if self.is_cdb():
                        self.log.info("Database -> CDB")
                        user = 'c##%s' % user

            return user
        except Exception as err:
            self.log.exception("Exception caught: %s", err)
            raise

    def create_user(self, user, default_tablespace):
        """
        Method to create a database user which a defualt tablespace mapping

            Args:
                user    (str)   --  The name of the newly create user/schema

                default_tablespace  (str)   --  The tablespace associated with the user

            Raises:
                Exception:
                    If the user cannot be created

        """
        try:
            users = ''
            user = self.set_user_name(user)
            result = self.execute(
                "select USERNAME from dba_users where USERNAME='{0}'".format(
                    user.upper()))

            if result.rowcount != 0:
                users = result.rows[0][0]
                self.log.info("Users: %s", users)
                if str(users.lower()) == user:
                    self.log.info("User found, dropping the user")
                    self.execute("drop user {0} cascade ".format(user))

            self.log.info("Creating new user: %s", user)
            self.execute(
                "create user {0} identified by {1} default tablespace {2} "
                "quota unlimited on {3}".format(
                    user, user, default_tablespace, default_tablespace))
            self.log.info("granting privileges to the user")
            self.execute("grant connect, resource to {0}".format(user))
        except Exception as str_err:
            self.log.exception('Unable to create user/schema %s', str_err)
            raise

    def drop_user(self, user):
        """
        Method to drop a database user

            Args:
                user    (str)   --  The name of the user to be dropped

            Raises:
                Exception:
                  -- If user is not found.
        """
        try:
            users = ''
            user = self.set_user_name(user).upper()
            result = self.execute(
                f"select USERNAME from dba_users where USERNAME='{user}'")
            if result.rowcount != 0:
                users = result.rows[0][0]
                self.log.info(f"Users: {users}")
                if str(users.lower()) == user:
                    self.log.info("User found, dropping the user")
                    self.execute(f"drop user {user} cascade")
        except Exception as str_err:
            self.log.exception(f"Unable to drop user {str_err}")
            raise

    def create_table(self, tablespace_name, table_prefix, user, number, row_limit=10):
        """
        Method to create a table and mapped to a tablespace and user

            Args:
                tablespace_name (str)   --  The tablespace associated with the tables

                table_prefix    (str)   --  The prefix associated with the tables
                    Sample: CV_TABLE

                user    (str)   --  The user/schema associated with the tablespace

                number  (int)   --  The number of tables to be created

                row_limit   (int)   -- The number of rows to be populated in each table

            Raises:
                Exception:
                    If existing table drop isn't possible

                    If Create table isn't possible

        """
        for count in range(1, number + 1):
            table_name = table_prefix + '{:02}'.format(count)
            # Drop table if it exists
            cmd = 'DROP TABLE {0}.{1} CASCADE CONSTRAINTS PURGE'.format(user, table_name)
            try:
                self.execute(cmd)
            except Exception as str_err:
                self.log.exception('Unable to drop table: %s', str_err)
                pass

            # Create the actual table
            cmd = 'CREATE TABLE {0}.{1} (ID NUMBER(5) PRIMARY KEY, NAME VARCHAR2(30))' \
                  ' TABLESPACE {2}'.format(user, table_name, tablespace_name)
            try:
                self.execute(cmd)
                self.log.info("table created")
                self.populate_table(table_prefix, user, count, row_limit)
            except Exception as str_err:
                message = 'Unable to execute command: {}'.format(str_err)
                self.log.exception(message)
                raise

    def drop_table(self, user, table_name):
        """
        Method to drop a table

            Args:
                user (str) -- The user/schema associated with the tablespace

                table_name (str) -- The table to be dropped

            Raises:
                Exception:
                    If the table can't be dropped

        """
        if user is None:
            cmd = 'DROP TABLE {0} CASCADE CONSTRAINTS PURGE'.format(table_name)
        else:
            cmd = 'DROP TABLE {0}.{1} CASCADE CONSTRAINTS PURGE'.format(user, table_name)
        try:
            self.execute(cmd)
            self.log.info('Table %s dropped successfully', table_name)
        except Exception as str_err:
            message = 'Unable to drop table: {0}'.format(str_err)
            self.log.exception(message)
            pass

    def populate_table(self, tblpref, user=None, number=1, row_limit=10):
        """
        Method to populate data in a table. Appends 10 records every time this  method is called

            Args:
                tblpref (str)   --  The prefix used at the time of creating tables

                user (str)  --  The user who has access to the tablespace and tables
                    default: None

                number (int)    --  Appended to tablepref to get the tablename to be populated
                    default: 1

                row_limit (int) --  Number of rows in each table
                    default: 10

            Raises:
                Exception:
                    If the table can't be modified

        """

        table_name = tblpref + '{:02}'.format(number)
        if user is None:
            cmd = 'select count(*) from {0}'.format(table_name)
        else:
            cmd = 'select count(*) from {0}.{1}'.format(user, table_name)
        try:
            result = self.execute(cmd)
            row_start = result.rows[0][0]
        except Exception as str_err:
            message = 'Unable to execute command: {0}'.format(str_err)
            self.log.exception(message)
            raise

        self.log.info('Populating table: %s...', table_name)
        for row_number in range(row_start + 1, row_start + row_limit + 1):
            if user is None:
                self.log.info("INSERT INTO %s VALUES ({%s, "
                              "'CV Automation - Test Case')", table_name, str(row_number))
                cmd = "INSERT INTO {0} VALUES ({1}, 'CV Automation - Test Case')".format(
                    table_name, str(row_number))
            else:
                self.log.info(
                    "INSERT INTO %s.%s VALUES (%s, "
                    "'CV Automation - Test Case')", user, table_name, str(row_number))
                cmd = "INSERT INTO {0}.{1} VALUES ({2}, 'CV Automation - Test Case')".format(
                    user, table_name, str(row_number))
            try:
                self.execute(cmd)
            except Exception as str_err:
                message = 'Unable to execute command: {0}'.format(str_err)
                self.log.exception(message)
                raise

    def tablespace_validate(self, tablespace_name):
        """
        Method to get the count of datafiles associated with a particular tablespace.

            Args:

                tablespace_name (str) -- The name of the tablespace we want to validate

            Returns:
                (str,int) -- tablespace name and the count of the datafiles in the tablespace

            Raises:
                Exception:
                    If the tablespace/datafiles fetch fails

        """
        try:
            result = self.execute(
                "select tablespace_name from dba_tablespaces where tablespace_name = '{0}'".format(
                    tablespace_name.upper()))
            tablespaces = result.rows[0][0]
            self.log.info("Tablespaces: %s", tablespaces)

            result = self.execute(
                "select count(file_name) from dba_data_files where tablespace_name = '{0}'".format(
                    tablespace_name.upper()))
            datafiles = result.rows[0][0]
            self.log.info("Datafiles: %s", datafiles)

            return tablespaces, datafiles
        except Exception as err:
            message = "Exception caught: {0}".format(err)
            self.log.exception(message)
            raise

    def table_validate(self, user, tablename):
        """
        Method to return the records in a particular table.

            Args:
                user (str) -- The user assocaited with the table

                tablename (str) -- The table we want to validate

            Returns:
                (int)     --  The number of records in the table

            Raises:
                Exception:
                    If the SQL cmd execution fails

        """
        try:
            if user is None:
                result = self.execute("select count(*) from {0}".format(tablename))
                tablerecords = result.rows[0][0]
                self.log.info("No of Rows in the table: %s", tablerecords)
            else:
                result = self.execute("select count(*) from {0}.{1}".format(user, tablename))
                tablerecords = result.rows[0][0]
                self.log.info("No of Rows in the table: %s", tablerecords)
            return tablerecords
        except Exception as err:
            message = "Exception caught: {0}".format(err)
            self.log.exception(message)
            raise


class MSSQL(Database):
    """Class for connecting to Microsoft SQL Server Database."""

    def __init__(self, server, user, password, database,
                 as_dict=True, autocommit=True, use_pyodbc=True, unix_os=False, **kwargs):
        """Constructor for creating a connection to MSSQL Database.

            Args:
                server      (str)   --  sql server to connect

                user        (str)   --  database user to connect as

                password    (str)   --  user's password

                database    (str)   --  the database to connect to

                as_dict     (bool)  --  whether rows should be returned as dictionaries,
                                            instead of tuples
                    default: True

                autocommit  (bool)  --  whether to commit after a query automatically or not
                    default: True

                use_pyodbc  (bool)  --  Uses pyodbc

                    default: True

                unix_os     (bool)  --  True if SQL is hosted on unix OS

                    default: False

            Keyword Args:
                driver      (str)   --  SQL driver name (optional)

            Returns:
                object  -   connection object to the MSSQL server

            Raises:
                Exception:
                    if module ``pymssql`` is not installed

                    if failed to connect to the database

        """
        self.server = server
        self.user = user
        self.password = password
        self.database = database
        self.as_dict = as_dict
        self.autocommit = autocommit
        self.use_pyodbc = use_pyodbc
        self.unix_os = unix_os
        self.kwargs = kwargs

        super(MSSQL, self).__init__()

    def _connect(self):
        """Establishes a connection to the Microsoft SQL Server Database
            using the details provided.
        """
        try:
            if self.use_pyodbc:
                import pyodbc
                import platform
                driver_name = defines.unix_driver if self.unix_os else defines.driver
                # driver_name = self.kwargs["driver"] if "driver" in self.kwargs.keys() \
                #     else (defines.driver if platform.system().lower() == "windows" else defines.unix_driver)
                try:
                    connection = pyodbc.connect(driver=driver_name,
                                                server=self.server,
                                                database=self.database,
                                                user=self.user,
                                                password=self.password,
                                                as_dict=self.as_dict,
                                                autocommit=self.autocommit,
                                                login_timeout=2
                                                )
                except Exception as excp:
                    raise Exception(f"Failed to Connect {excp}")
            else:
                import pymssql
                try:
                    connection = pymssql.connect(
                        server=self.server,
                        user=self.user,
                        password=self.password,
                        database=self.database,
                        as_dict=self.as_dict,
                        autocommit=self.autocommit,
                        login_timeout=2
                    )
                except Exception as excp:
                    raise Exception(f"Failed to Connect {excp}")

        except Exception as excp:
            raise Exception(
                'Failed to connect to the Database\nError: {0}'.format(excp))

        if connection is not None:
            self._connection = connection

    def create_db(self, database):
        """
        Creates database with a given name in the specified mssql server

        Args:
            database (str): Database name to be created

        Returns:
            None:

        Raises:
            Exception: if unable to create database
        """
        try:
            if self.check_if_db_exists(database):
                self.drop_db(database)
            self.execute(f"CREATE DATABASE {database};")
        except Exception as exp:
            raise Exception(f"Unable to create db {database}") from exp

    def drop_db(self, database):
        """
        Drops the specified database

        Args:
            database (str): Database name which has to be dropped

        Returns:
            None:

        Raises:
            Exception: if unable to drop db
        """
        try:
            self.execute(f"DROP DATABASE {database};")
        except Exception as exp:
            raise Exception(f"Unable to drop db {database}") from exp

    def check_if_db_exists(self, database):
        """
        Checks if the given database exists

        Args:
            database (str): Name of the database to verify

        Returns:
            None:

        Raises:
            Exception: if unable to check whether database exists
        """
        return database in self.get_db_list()

    def get_db_list(self):
        """
        Gets the list of database from a MSSQL Server

        Returns:
            list[str]: list of databases

        Raises:
            Exception: if unable to get db list
        """
        response = self.execute("SELECT name FROM sys.databases;")
        db_list = [row[0] for row in response.rows]
        return db_list

    def execute(self, query, data=None, commit=True):
        """Executes the query on the Database and returns the results.

            Note: performing fetch all rows operation fail on unix after commit.
                So commit will be set to False for select queries on unix
        """
        import platform
        if platform.system().lower() == "linux" and query.lower().startswith('select '):
            commit = False

        return super(MSSQL, self).execute(query, data, commit)

    def get_version_info(self, client_name):
        """Queries the SQL Database for version info for Commvault Client.

            Args:
                client_name     (str)   --  name of the Client to get the version of

            Returns:
                dict    -   dict consisting of the version info for the client

        """
        version, service_pack, build = 'NA', 'NA', 'NA'
        return_value = {
            'version': version,
            'service_pack': service_pack,
            'build': build
        }

        sql_query = """
            SELECT APP_ClientProp.attrVal FROM APP_Client
            JOIN APP_ClientProp ON APP_Client.id = APP_ClientProp.componentNameId
            WHERE APP_ClientProp.attrName = 'Client Version' AND name = '{0}'
        """.format(client_name)

        db_response = self.execute(sql_query)

        if db_response.rows == []:
            return return_value

        response = db_response.rows[0]
        version = response['attrVal']

        version = re.search(r"(\d*)\((\w*\d*)\)", version)
        version, build = version.groups()[0], version.groups()[1]
        index = build.find('D')
        build = 'B' + build[index + 1:]

        if int(version) > 9:
            sql_query = """
                SELECT APP_ClientProp.attrVal FROM APP_Client
                JOIN APP_ClientProp on APP_Client.id = APP_ClientProp.componentNameId
                WHERE APP_ClientProp.attrName ='SP Version and Patch Info' and name='{0}'
            """.format(client_name)

            db_response = self.execute(sql_query)

            if db_response.rows != []:
                response = db_response.rows[0]
                service_pack = response['attrVal']
                search_response = re.search(r'[^\d]+[:](\d*\w?)', service_pack)
                if search_response is not None:
                    service_pack = search_response.groups()[0]

        return_value = {
            'version': version,
            'service_pack': service_pack,
            'build': build
        }
        return return_value

    def get_path(self, client_name):
        """Queries the SQL Database for the install location on the Client.

            Args:
                client_name     (str)   --  name fo the Client to get the install location of

            Returns:
                str     -   install location string for the client

        """
        install_location = None

        sql_query = """
            SELECT APP_ClientProp.attrVal FROM APP_Client
            JOIN APP_ClientProp ON APP_Client.id = APP_ClientProp.componentNameId
            WHERE APP_ClientProp.attrName = 'Patch Local Location' AND name = '{0}'
        """.format(client_name)

        db_response = self.execute(sql_query)

        if db_response.rows != []:
            response = db_response.rows[0]
            install_location = response['attrVal']

        return install_location


class MySQL(Database):
    """Class for connecting to MySQL Database."""

    def __init__(self, hostname, user, password, port, database=None, ssl_ca=None, ssl_key=None, ssl_cert=None):
        """Constructor for creating a connection to MySQL Database.

            Args:
                host        (str)   --  mysql hostname to connect

                user        (str)   --  database user to connect as

                password    (str)   --  user's password

                port        (int)   --  mysql port number

                database    (str)   --  the database to connect to

                ssl_ca      (str)   --  SSL CA file

                ssl_cert    (str)   --  SSL Cert file

                ssl_key     (str)   --  SSL Key file

                    default: None

            Returns:
                object  -   connection object to the MySQL database

            Raises:
                Exception:
                    if module ``pymysql`` is not installed

                    if failed to connect to the database

        """

        self.host_name = hostname
        self.user = user
        self.password = password
        self.port = port
        self.database_name = database
        self.ssl_ca = ssl_ca
        self.ssl_key = ssl_key
        self.ssl_cert = ssl_cert
        super(MySQL, self).__init__()

    def _connect(self):
        """Establishes a connection to the MySQL Server using the details provided."""
        try:
            import pymysql.cursors
        except ImportError as error:
            raise Exception(
                'Failed to import pymysql\nError: "{0}"'.format(
                    error.msg))

        connection = None

        try:
            connection = pymysql.connect(
                host=self.host_name,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.database_name,
                ssl_ca=self.ssl_ca,
                ssl_cert=self.ssl_cert,
                ssl_key=self.ssl_key
            )

        except Exception as excp:
            raise Exception(
                'Failed to connect to the MySQL Server\nError: "{0}"'.format(excp))

        if connection is not None:
            self._connection = connection

    def create_db(
            self,
            database):
        """Creates database with a given name in the specified mysql server


        Args:

            database    (str)  -- Database name which has to be created


        Raises Exception:
            if unable create DB

        """

        try:
            if self.check_if_db_exists(database):
                self.drop_db(
                    database)
            if not database.replace("_", "").replace("-", "").isalnum() or database.count(" ") != 0:
                query = "create database `%s`;" % database
            else:
                query = "create database %s;" % database
            self.execute(query)
        except Exception:
            raise Exception("Unable to create db")

    def drop_db(
            self,
            database):
        """Drops the specified database


        Args:

            database    (str)  -- Database name which has to be dropped


        Raises Exception:
            if unable to drop DB

        """
        try:
            if not database.replace("_", "").replace("-", "").isalnum() or database.count(" ") != 0:
                query = "drop database `%s`;" % database
            else:
                query = "drop database %s;" % database
            self.execute(query)
        except Exception:
            raise Exception("Unable to drop db")

    def check_if_db_exists(
            self,
            database):
        """
        Checks if the given databases exists or not

        Args:
            database    (str)  -- Name of the database which needs to be checked


        Returns:
            Boolean - True if Db exists/ else returns False

        Raises Exception:
            if unable check if db exists

        """
        db_list = None
        try:
            db_list = self.get_db_list()
            if database not in db_list:
                return False

            return True
        except Exception:
            raise Exception("Unable to check the db existance")

    def get_db_list(self):
        """ Gets the list of databases from a MySQL server

            Returns:
                db_list     (list)  --  the list of databases in the given MySQL server

        """
        db_list = []
        query = "show databases;"
        postgres_response = self.execute(query)
        for row in postgres_response.rows:
            db_list.append(row[0])
        return db_list

    def start_slave(self):
        """
        Starts the slave in mysql server

        Raises:
            Exception:
                if unable to start the slave in mysql server

        """
        if not self.slave_status():
            self.execute("start slave;")
            self.log.info("Wait 60 seconds till the slave is up and running")
            time.sleep(60)
            if self.slave_status():
                self.log.info("Slave started")
            else:
                raise Exception("Unable to start the slave")

    def stop_slave(self):
        """
        Stops the slave in mysql server

        Raises:
            Exception:
                if unable to stop the slave in mysql server

        """
        if self.slave_status():
            self.execute("stop slave;")
            if not self.slave_status():
                self.log.info("Slave Stopped")
            else:
                raise Exception("Unable to stop the slave")

    def slave_status(self):
        """
        Checks the slave status in mysql server

        Returns:
            (bool)  --  True is slave is started
                        False if slave is not stopped

        Raises:
            Exception:
                if unable to check the slave status in mysql server

        """
        response = self.execute(
            "SELECT SERVICE_STATE FROM performance_schema.replication_connection_status;")
        if response:
            if response.rowcount != 0:
                return response.rows[0][0].strip().lower() == "on"
        raise Exception("Unable to check the slave status in mysql server")

    def get_binary_logs(self):
        """fetches the binary log information from mysql server

        Returns:
            (list)  --  list containing binary log information
                [log_list, number_of_logs, last_log_number]

        Raises:
            Exceptions:
                If unable to get the binary logs

        """
        response_object = self.execute("show binary logs;")
        if response_object:
            if response_object.rowcount != 0:
                last_log = int(re.split(r".*\.", response_object.rows[-1][0])[1])
                return [response_object.rows, response_object.rowcount, last_log]
            return [[], 0, 0]
        raise Exception("Unable to get the binary logs")


class Informix(Database):
    """Class for connecting to Informix Database."""

    def __init__(self, host_name, server, user_name, password, database, service, autocommit=True):
        """Constructor for creating a connection to Informix Database.

            Args:
                host_name   (str)   --  Hostname of remote machine

                server      (str)   --  Informix server to connect

                user_name   (str)   --  database user to connect as

                password    (str)   --  user's password

                database    (str)   --  the database to connect to

                service     (str)   --  services name to connect

                autocommit  (bool)  --  whether to commit after a query automatically or not
                    default: True

            Returns:
                object  -   connection object to the Informix server

            Raises:
                Exception:
                    if module ``pyodbc`` is not installed

                    if failed to connect to the database

        """
        self.server = server
        self.user_name = user_name
        self.password = password
        self.database = database
        self.host_name = host_name
        self.service = service
        self.autocommit = autocommit
        self._connection = None

        super(Informix, self).__init__()

    def _connect(self):
        """Establishes a connection to the Informix Database
            using the details provided.
        """
        try:
            import pyodbc
        except ImportError as error:
            raise Exception('Failed to import pyodbc\nError: "{0}"'.format(error.msg))

        connection = None

        try:
            connect_string = "DRIVER={IBM INFORMIX ODBC DRIVER (64-Bit)};\
            HOST=%s;SERVICE=%s;PROTOCOL=olsoctcp;DATABASE=%s;SERVER=%s;UID=%s;\
            PWD=%s" % (self.host_name,
                       self.service,
                       self.database,
                       self.server,
                       self.user_name,
                       self.password)
            pyodbc.pooling = False
            connection = pyodbc.connect(connect_string)

        except Exception as excp:
            raise Exception(
                'Failed to connect to the Database {0}'.format(excp))

        if connection is not None:
            self._connection = connection

    def list_dbspace(self):
        """ Lists all dbspaces in the server

            Returns:
                Returns list of dbspaces in server

            Raises:
                Exception:
                    if unable to list dbspaces

        """
        try:
            response_object = self.execute(
                "select name from sysdbspaces;", commit=False)
            rows = response_object.rows
            dbspace_list = []
            for i in rows:
                dbspace_list.append(i.name.strip())
            return dbspace_list

        except BaseException:
            raise Exception("Unable to fetch the dbspace list")

    def drop_database(self, database_name):
        """ Drops a database if it exists.

            Args:
                database_name   (str)   -- Database name to delete

            Returns:
                Returns True on success

            Raises:
                Exception:
                    if unable to drop Database

        """

        try:
            if not self.check_if_db_exists(database_name):
                return True
            query = "drop database {0};".format(database_name)
            self.execute(query)
            if not self.check_if_db_exists(database_name):
                return True
            raise Exception("Unable to drop the database")

        except BaseException:
            raise Exception("Unable to drop the database")

    def get_database_list(self):
        """ Gets all the database names in the server.

            Returns:
                Returns database list

            Raises:
                BaseException:
                    if unable get the database list

        """
        try:
            response_object = self.execute(
                "select * from sysdatabases;", commit=False)
            rows = response_object.rows
            database_list = []
            for i in rows:
                database_list.append(i.name.strip())
            return database_list

        except BaseException:
            raise Exception("Unable to fetch the db list")

    def check_if_db_exists(self, database):
        """ Checks if the specified database exist.

            Args:
                database     (str)   -- Database name to check

            Returns:
                Returns True if DB exists

                Returns False if DB doesn't exist

        """
        database_list = []
        database_list = self.get_database_list()
        if database in database_list:
            return True
        return False

    def row_count(self, table_name):
        """ Returns number of rows in the table specified.

            Args:
                table_name  (str)   -- Table name to count the rows

            Returns:
                Returns number of rows in the table

            Raises:
                BaseException:
                    if unable get row count of table

        """
        try:
            query = "select count(*) from %s;" % (table_name)
            response_object = self.execute(query, commit=False)
            return int(response_object.rows[0][0])
        except BaseException:
            raise Exception("Unable to get the row count")


class SQLite(Database):
    """Class for connecting to SQLite Database."""

    def __init__(self, database_file_path, check_same_thread=True):
        """Constructor for creating a connection to SQLite Database.

            Args:
                database_file_path  (str)   --  full path of the .db file

                check_same_thread   (bool)  --  decides if the thread which didn't create
                    the connection can access the DB connection or not.
                    Please refer https://docs.python.org/3/library/sqlite3.html

            Returns:
                object  -   connection object to the SQLite server

            Raises:
                Exception:
                    if module ``sqlite3`` is not installed

                    if failed to connect to the database

        """
        self.database_file_path = database_file_path
        self.check_same_thread = check_same_thread

        super(SQLite, self).__init__()

    def _connect(self):
        """Establishes a connection to a SQLite Database given at the path."""
        try:
            import sqlite3
        except ImportError as error:
            raise Exception(
                'Failed to import sqlite3\nError: "{0}"'.format(
                    error.msg))

        connection = None

        try:
            connection = sqlite3.connect(
                database=self.database_file_path,
                check_same_thread=self.check_same_thread
            )
        except Exception as excp:
            raise Exception(
                'Failed to connect to the Database\nError: {0}'.format(excp))

        if connection is not None:
            self._connection = connection


class SAPHANA(Database):
    """ Class for connecting to SAP HANA Database."""

    def __init__(self, host, port, user, password):
        """Constructor for creating a connection to SAP HANA Database.

            Args:
                host        (str)   --  sap hana hostname to connect

                port        (str)   --  port number to connect to the db

                user        (str)   --  database user to connect as

                password    (str)   --  user's password

            Returns:
                object  -   connection object to the SAP HANA database

            Raises:
                Exception:
                    if module ``hdbcli`` is not installed

                    if failed to connect to the database

        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        super(SAPHANA, self).__init__()

    def _connect(self):
        """Establishes a connection to the SAP HANA Database using the details provided."""
        try:
            from hdbcli import dbapi
        except ImportError as error:
            raise Exception(
                'Failed to import hdbcli\nError: "{0}"'.format(
                    error.msg))

        connection = None

        try:
            connection = dbapi.connect(
                address=self.host,
                port=int(self.port),
                user=self.user,
                password=self.password
            )
        except Exception as excp:
            raise Exception(
                'Failed to connect to the Database\nError: {0}'.format(excp))

        if connection is not None:
            self._connection = connection


class SAPOracle(Database):
    """ Class for connecting to SAP Oracle Database."""
    CONN_SYSDBA = 'SYSDBA'
    CONN_DB_USER = 'DBUSER'
    SHUT_TRANSACTION = 'TRANSACTIONAL'
    SHUT_FINAL = 'FINAL'
    SHUT_ABORT = 'ABORT'
    SHUT_IMMEDIATE = 'IMMEDIATE'

    def __init__(self, user, password, connectstring, hostname, port, mode=None):
        """Constructor for creating a connection to SAP Oracle Database.

            Args:


                user        (str)   --  database user to connect as

                password    (str)   --  user's password
                connectstring    (str)   --  oracle instance connectstring

            Returns:
                object  -   connection object to the SAP Oracle database

            Raises:
                Exception:
                    if module ``oraclddb`` is not installed

                    if failed to connect to the database

        """

        self.user = user
        self.password = password
        self.connectstring = connectstring
        self.hostname = hostname
        self.port = port
        if mode is None:
            mode = 'SYSDBA'

        super(SAPOracle, self).__init__()

    @property
    def connection(self):
        """Treats the database connection object as a read-only attribute."""
        return self._connection

    def _connect(self, mode=CONN_SYSDBA):
        """
        Method to establish a connection to the database

            Args:
                mode (str/enum) -- DBA role connection

            Raises:
                Exception: If the DSN conn cant be made

                ImportError: If the import fails

                AttributeError: If the mode specified is invalid

                OperationError: If the connection can't be established

        """
        self.log = logger.get_log()
        try:
            self.log.info("import oracledb")
            import oracledb

        except ImportError as error:
            raise Exception(
                'Failed to import oracledb\nError: "{0}"'.format(
                    error.msg))
        try:
                self.dsn_tns = oracledb.makedsn(self.hostname, self.port,
                                                 self.connectstring)
                self.log.info(self.dsn_tns)
        except Exception as err:
                self.dsn_tns = oracledb.makedsn(self.hostname, self.port,
                                                 service_name=self.connectstring)

        try:
            if mode == 'SYSDBA':
                self._connection = oracledb.connect(user=self.user, password=self.password,
                                                    dsn=self.dsn_tns, mode=oracledb.SYSDBA)
            elif mode == 'IMMEDIATE':
                    self._connection = oracledb.connect(user=self.user, password=self.password,
                                                        dsn=self.dsn_tns, mode=oracledb.DBSHUTDOWN_IMMEDIATE)
            else:
                raise AttributeError('Unrecognized mode to connect to database: {0}'
                                     .format(mode))
        except oracledb.OperationalError:
            raise
        else:
            self.sap_ora_version = self._connection.version


class PostgreSQL(Database):
    """ Class for connecting to PostgreSQL Database."""

    def __init__(self, host, port, user, password, database, autocommit=True,
                 ssl=False, ssl_ca=None, ssl_cert=None, ssl_key=None):
        """Constructor for creating a connection to PostgreSQL Database.

            Args:
                host        (str)       --  Postgres server hostname to connect

                port        (str)       --  port number to connect to the db

                user        (str)       --  database user to connect as

                password    (str)       --  user's password

                database    (str)       --  name of the database to connect

                autocommit  (Boolean)   --  commit after executing query (True/False)

                ssl         (Boolean)   --  True/False based on SSL status of the postgres instance

                ssl_ca      (str)       --  server CA file path if ssl is enabled

                ssl_cert    (str)       --  client cert file path if ssl is enabled

                ssl_key     (str)       --  client key file path if ssl is enabled

            Returns:
                object  -   connection object to the PostgreSQL database

            Raises:
                Exception:
                    if module ``psycopg2`` is not installed

                    if failed to connect to the database

        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.ssl = ssl
        self.ssl_ca = ssl_ca
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.autocommit = autocommit

        super(PostgreSQL, self).__init__()

    def _connect(self):
        """Connect to the PostGreSQL Server and return the connection object"""
        connection = None

        try:
            import psycopg2
        except ImportError as error:
            raise Exception(
                'Failed to import psycopg2\nError: "{0}"'.format(error.msg))

        try:
            if not self.ssl:
                connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.database
                )
            elif self.ssl is True and not self.ssl_ca:
                connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.database,
                    sslmode="require"
                )
            elif self.ssl_ca:
                connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.database,
                    sslmode="verify-ca",
                    sslrootcert=self.ssl_ca,
                    sslcert=self.ssl_cert,
                    sslkey=self.ssl_key
                )

        except Exception as excp:
            raise Exception(
                'Failed to connect to the Database\nError: {0}'.format(excp))

        if connection is not None:
            connection.autocommit = self.autocommit
            self._connection = connection

    def create_db(
            self,
            database):
        """Creates database with a given name in the specified postgres server


        Args:

            database            (str)  -- Database name which has to be created


        Raises Exception:
            if unable to create DB

        """

        try:
            if self.check_if_db_exists(database):
                self.drop_db(
                    database)
            query = "create database \"%s\";" % database
            self.execute(query)
        except Exception:
            raise Exception("Unable to create db")

    def create_tablespace(
            self,
            tablespace,
            location):
        """Creates tablespace in given location in the specified postgres server


        Args:
            tablespace     (str)  -- Database name which has to be created

            location       (str)  -- location where table space should be created


        Raises Exception:
            if unable create tablespace

        """
        try:
            query = "drop tablespace if exists \"%s\";" % tablespace
            self.execute(query)
            query = "create tablespace \"%s\" location '%s';" % (tablespace, location)
            self.execute(query)
        except Exception:
            raise Exception("Unable to create tablespace")

    def create_tablespace_db(
            self,
            database,
            tablespace):
        """Creates database with a given name in the specified postgres server
            under the specified tablespace


        Args:
            database          (str)  -- Database name which has to be created

            tableaspace       (str)  -- Tablespace name where db has to be created

        Raises Exception:
            if unable create DB with tablespace

        """

        try:
            if self.check_if_db_exists(database):
                self.drop_db(
                    database)
            query = "create database \"%s\" tablespace \"%s\";" % (
                database,
                tablespace)
            self.execute(query)
        except Exception:
            raise Exception("Unable to create db")

    def drop_db(
            self,
            database):
        """Drops the specified database


        Args:

            database            (str)  -- Database name which has to be dropped


        Raises Exception:
            if unable to drop DB

        """
        try:
            query = "drop database \"%s\";" % database
            self.execute(query)
        except Exception:
            raise Exception("Unable to drop db")

    def drop_tablespace(
            self,
            tablespace):
        """Drops the specified tablespace


        Args:
            tablespace     (str)  -- Tablespace name which has to be dropped

        Raises Exception:
            if unable drop tablespace

        """
        try:
            query = "drop tablespace if exists \"%s\";" % tablespace
            self.execute(query)
        except Exception:
            raise Exception("Unable to drop tablespace")

    def check_if_db_exists(
            self,
            database):
        """
        Checks if the given databases exists or not
        Returns True if database exists
        Returns False if database doesn't exist

        Args:
            database    (str)  -- Name of the database which needs to be checked


        Returns:
            Boolean - True if Db exists/ else returns False

        Raises Exception:
            if unable check if db exists

        """
        db_list = None
        try:
            db_list = self.get_db_list()
            if database not in db_list:
                return False

            return True
        except Exception:
            raise Exception("Unable to check the db existance")

    def get_db_list(self):
        """ Gets the list of databases from a PostgreSQL server

            Returns:
                List    (db_list)       --  the list of databases in the given postgres server

        """
        db_list = []
        query = "select datname from pg_database"
        postgres_response = self.execute(query)
        for row in postgres_response.rows:
            db_list.append(row[0])
        return db_list


class MariaDB(Database):
    """ Class for connecting to MariaDB Database."""

    def __init__(self, hostname, user, password, port, database=None, ssl=False):
        """Constructor for creating a connection to MariaDB Database.

            Args:
                hostname     (str)   --  mariadb hostname to connect

                user        (str)   --  database user to connect as

                password    (str)   --  user's password

                port        (int)   --  mariadb port number

                database    (str)   --  the database to connect to

                ssl         (bool)   --  True/False based on SSL status
                    default: None

            Returns:
                object  -   connection object to the MariaDB database

            Raises:
                Exception:
                    if module ``mariadb`` is not installed

                    if failed to connect to the database

        """

        self.host_name = hostname
        self.user = user
        self.password = password
        self.port = port
        self.database_name = database
        self.ssl = ssl
        super(MariaDB, self).__init__()

    def _connect(self):
        """Establishes a connection to the MariaDB Server using the details provided."""

        connection = None

        try:
            import mariadb.cursors
        except ImportError as error:
            raise Exception(
                'Failed to import mariadb\nError: "{0}"'.format(
                    error.msg))

        try:
            connection = mariadb.connect(
                host=self.host_name,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.database_name,
                ssl=self.ssl
            )

        except Exception as excp:
            raise Exception(
                'Failed to connect to the MariaDB Server\nError: "{0}"'.format(excp))

        if connection is not None:
            self._connection = connection

    def create_db(
            self,
            database):
        """Creates database with a given name in the specified mariadb server

        Args:

            database    (str)  -- Database name which has to be created


        Raises Exception:
            if unable create DB

        """

        try:
            if self.check_if_db_exists(database):
                self.drop_db(
                    database)
            query = "create database %s;" % database
            self.execute(query)
        except Exception:
            raise Exception("Unable to create db")

    def drop_db(
            self,
            database):
        """Drops the specified database


        Args:

            database    (str)  -- Database name which has to be dropped


        Raises Exception:
            if unable to drop DB

        """
        try:
            query = "drop database %s;" % database
            self.execute(query)
        except Exception:
            raise Exception("Unable to drop db")

    def check_if_db_exists(
            self,
            database):
        """
        Checks if the given databases exists or not

        Args:
            database    (str)  -- Name of the database which needs to be checked


        Returns:
            Boolean - True if Db exists/ else returns False

        Raises Exception:
            if unable check if db exists

        """
        db_list = None
        try:
            db_list = self.get_db_list()
            if database not in db_list:
                return False

            return True
        except Exception:
            raise Exception("Unable to check the db existance")

    def get_db_list(self):
        """ Gets the list of databases from a MySQL server

            Returns:
                db_list     (list)  --  the list of databases in the given MySQL server

        """
        db_list = []
        query = "show databases;"
        postgres_response = self.execute(query)
        for row in postgres_response.rows:
            db_list.append(row[0])
        return db_list


class DBHelper(object):
    """Base class to handle Database operations"""

    def __init__(self, commcell, db_name):
        """Initializes the dbhelper object

            Args:
                commcell    (object)    --  commvault sdk commcell object

                db_name     (str)       --  database name
        """
        self._db_name = db_name
        self._commcell = commcell
        self._output = None
        self._query = None
        self._columns = None
        self._rows = None
        self._executed_query = None

    def _get_columns(self):
        """Gets the column names of the table for which SQL query was ran,
            and updates the columns attribute.
        """
        if self._query is None:
            raise Exception('No query was executed to get list of columns')

        if self._executed_query != self._query:
            # store the query which for which we are retrieving the table
            # columns
            self._executed_query = self._query

            query = self._query.replace("'", "''")

            get_columns_query = "SELECT name FROM sys.dm_exec_describe_first_result_set \
                                ('{0}', NULL, 0)".format(query)

            output = cvhelper.execute_query(
                self._commcell, self._db_name, get_columns_query)
            self._columns = []

            for row in output:
                self._columns.append(row[0].strip('\r'))

    @property
    def columns(self):
        """Returns the list consisting of columns of the Table the SQL query was ran on."""
        self._get_columns()
        return self._columns

    @property
    def query(self):
        """Returns the SQL query executed on the Databse, for this response object."""
        return self._query

    @property
    def rows(self):
        """Returns the list of lists, consisting of the response from the SQL query,
            where each list represents a single SQL Table row.
        """
        return self._rows

    @property
    def result_dict(self):
        """Returns list of dicts, representing the table rows"""
        columns = self.columns
        return [
            {col: val for col, val in zip(columns, row)}
            for row in self._rows
        ]

    def execute(self, query):
        """Executes the query on specified database

            Args:
                query   (str)   --  database query to execute
        """
        self._rows = None
        # Store the query we are about to execute
        self._query = query
        self._rows = cvhelper.execute_query(
            self._commcell, self._db_name, query)

    def fetch_one_row(self, named_columns=False):
        """Returns the first row from output

            Args:
                named_columns   (bool)  --  If set to True, returns the result as a dictionary where column names are
                assigned to the rows. Otherwise returns a list of row values.

            Returns:
                (list)     --  The first row from the output.

        """

        if not named_columns:
            return self._rows[0]
        else:
            columns = self.columns
            if len(self._rows[0]) == len(columns):
                return [dict(zip(columns, self._rows[0]))]
            else:
                return self._rows[0]

    def fetch_all_rows(self, named_columns=False):
        """Returns all the rows from output

            Args:
                named_columns   (bool)  --  Returns a list of dictionary where columns names are assigned to the
                rows in key-value pair. Example: [ {column1: value1, column2: value2}, ... ]

            Returns:
                (list)  --  Rows of the executed output

        """

        if not named_columns:
            return self._rows
        else:
            columns = self.columns
            if len(self._rows[0]) == len(columns):
                return [dict(zip(columns, row)) for row in self._rows]
            else:
                return self._rows

    def filter_response(self, column, value):
        """Filters out only the rows where column's value is equal to the input value."""
        if column not in self.columns:
            raise Exception(
                'Column does not exist. Please check the column name again')

        column_index = self._columns.index(column)

        return filter(lambda x: x[column_index].replace(
            "\r", "") == value, self.rows)


class CommServDatabase(DBHelper):
    """Class to handle commserv database operations"""

    def __init__(self, commcell_object):
        """Initializes the commserv database object"""
        super(CommServDatabase, self).__init__(commcell_object, "CommServ")


class WFEngineDatabase(DBHelper):
    """Class to handle wfengine database operations"""

    def __init__(self, commcell_object):
        """Initializes the commserv database object"""
        super(WFEngineDatabase, self).__init__(commcell_object, "WFEngine")


COMMSERV_DB = None


def set_csdb(db_object):
    """Sets the global CS DB object

        Args:
            db_object   (object)    --  CommServDatabase object

        Raises:
            Exception:
                if type of db_object is not CommServDatabase
    """
    global COMMSERV_DB
    if not isinstance(db_object, CommServDatabase):
        raise Exception("Invalid type for csdb")

    COMMSERV_DB = db_object


def get_csdb():
    """Returns the global csdb object

        Returns:
            (object)    -   CommServDatabase object

        Raises:
            Exception:
                if csdb value is not set to instance of CommServDatabase
    """
    if not COMMSERV_DB:
        raise Exception("csdb value not set to instance of CommServDatabase")
    return COMMSERV_DB


class Db2(Database):
    """Class for connecting to Db2 Database."""

    def __init__(self, database, hostname, port, protocol, db_user, db_password):
        """Constructor for creating a connection to Db2 Database.

            Args:
                database    (str)       --  the database to connect to

                hostname    (str)       --  hostame of server

                port        (str)       --  the database port

                protocol    (str)       --  TCPIP protocol

                db_user     (str)       --  database user to connect as

                db_password (str)       --  user's password

            Returns:
                object  -   connection object to the DB2 server

            Raises:
                Exception:
                    if module ``DB2`` is not installed

                    if failed to connect to the database

        """
        self.database = database
        self.hostname = hostname
        self.password = db_password
        self.port = port
        self.protocol = protocol
        self.user = db_user
        self.log = logger.get_log()

        super(Db2, self).__init__()

    def _connect(self):
        """
        Establishes a connection to the DB2 Database using the details provided.
        Raises:
            Exception:
                If ibm_db import fails
        """
        try:
            import ibm_db
        except ImportError as error:
            raise Exception(
                'Failed to import db2\nError: "{0}"'.format(
                    error.msg))

        connection = None
        self._ibm_db = ibm_db
        self.log.info("trying db2 database connection")
        try:
            connection = ibm_db.connect("DATABASE=" + self.database
                                        + ";HOSTNAME=" + self.hostname
                                        + ";PORT=" + self.port
                                        + ";PROTOCOL=" + self.protocol
                                        + ";UID=" + self.user
                                        + ";PWD=" + self.password
                                        + ";", "", "")
        except Exception as excp:
            try:
                connection = ibm_db.connect("DATABASE=" + self.database
                                            + ";HOSTNAME=" + self.hostname
                                            + ";PORT=" + self.port
                                            + ";PROTOCOL=" + self.protocol
                                            + ";UID=" + self.user
                                            + ";PWD=" + self.password
                                            + ";AUTHENTICATION=SERVER", "", "")
            except Exception as excp2:
                raise Exception(
                    'Failed to connect to the Database\nError: {0}'.format(excp2))

        if connection is not None:
            self._connection = connection
            self.log.info(self._connection)

    def drop_table(self, tbl_name):
        """
        Drops given table name from DB2 database

        Args:
            tbl_name    (str)       -- table name that need to be dropped

        Raises:
              Exception:
               If any issue occurs while dropping the table
        """
        cmd = "drop table {0}".format(tbl_name)
        self.log.info(cmd)
        stmt = self._ibm_db.exec_immediate(self._connection, cmd)
        if stmt is None:
            raise Exception("Exception in drop_table")

    def create_table_space(self, tbl_space_name, data_file):
        """
        Creates a table space. Will drop already existing table space and create new one.

        Args:
            tbl_space_name  (str)       --  name of the tablespace
            data_file       (str)       --  location of datafile which can be used in create tablespace command

        Raises:
            Exception:
                If tablespace creation fails

        """

        try:
            cmd = "select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name = '{0}'".format(
                tbl_space_name)
            self.log.info(cmd)
            stmt = self._ibm_db.exec_immediate(self._connection, cmd)
            tablespaces = self._ibm_db.fetch_assoc(stmt)
            if tablespaces:
                cmd = "drop table space " + tbl_space_name
                self.log.info(cmd)
                output = self._ibm_db.exec_immediate(self._connection, cmd)
                if not output:
                    raise Exception("table space not dropped successfully")
            cmd = (
                "CREATE TABLESPACE {0} MANAGED BY DATABASE USING (FILE '{1}' 100M ) AUTORESIZE NO".format(
                    tbl_space_name, data_file))
            self.log.info(cmd)
            output = self._ibm_db.exec_immediate(self._connection, cmd)
            if not output:
                raise Exception("table space is not created successfully ")
        except Exception as excp:
            raise Exception("Exception in create_table_space: {0}".format(excp))

    def insert_data(self, tbl_name, num_rows):
        """
        Inserts data into given tables.

        Args:
            tbl_name (str)      --  table name in which data need to be inserted

            num_rows (int)      --  number of rows to be added

        Raises:
            Exception:
                If any issue occurs while inserting data

        """

        try:
            for count in range(1, num_rows):
                cmd = ("insert into {0} values({1}, 'cvlt', {1})".format(tbl_name, count))
                output = self._ibm_db.exec_immediate(self._connection, cmd)
                cmd = "commit"
                output = self._ibm_db.exec_immediate(self._connection, cmd)

            if not output:
                raise Exception("rows are not Inserted into table successfully")

        except Exception as excp:
            raise Exception("Exception in insert_data: {0}".format(excp))

    def get_table_content(self, tbl_name):
        """
        Returns:
            (str)   -   result list of the data in given table.
        Args:
            tbl_name (str)      -- table name

        Raises:
            Exception:
                If any issue occurs while retrieving table content
        """

        try:
            cmd = "select * from {0}".format(tbl_name)
            self.log.info(cmd)
            stmt = self._ibm_db.exec_immediate(self._connection, cmd)
            content = self._ibm_db.fetch_assoc(stmt)
            result_list = []
            while (content):
                result_list.append(str(content))
                content = self._ibm_db.fetch_assoc(stmt)
            return (result_list)

        except Exception as excp:
            raise Exception("Exception in get_table_content: {0}".format(excp))

    def exec_tablespace_query(self, cmd):
        """
        Method to execute tablespace related queries

        Args:
            cmd     (str)   --      db2 select query on tablespaces

        Returns:
                    (list)  --      list of tablespaces based on different select query combinations and conditions
        Raises:
            Exception:

                If any issue while executing tablespace query

        """

        try:
            output = self._ibm_db.exec_immediate(self._connection, cmd)
            result = self._ibm_db.fetch_both(output)
            self.log.info(result)
            result_list = []
            while result:
                self.log.info("Result from table space query: %s ", result[0])
                result_list.append(str(result[0]))
                result = self._ibm_db.fetch_both(output)
            self.log.info(result_list)
            return result_list
        except Exception as excp:
            raise Exception("exception in exec_tablespace_query: {0}".format(excp))

    def get_tablespaces(self, tbl_space_name1=None, tbl_space_name2=None):
        """
        Returns number of table spaces and result list of table space names.

        Args:

            tbl_space_name1     (str)   --      name of 1st tablespace
                default: None
            tbl_space_name2     (str)   --      name of 2nd tablespace
                default: None
        Returns:

            (list) - list of tablespaces based on different select query combinations and conditions

        Raises:
            Exception:
                if any issue occurs while retrieving tablespace information

        """

        try:

            if tbl_space_name1 is None and tbl_space_name2 is None:
                cmd = (
                    "select count(*) from sysibmadm.tbsp_utilization where tbsp_name NOT LIKE '%TEMP%' and "
                    "tbsp_name NOT LIKE '%TMP%' and tbsp_name NOT LIKE '%TOOL%'")
                self.log.info(cmd)
                count = self._ibm_db.exec_immediate(self._connection, cmd)
                output = self._ibm_db.fetch_tuple(count)
                count = output[0]
                self.log.info("count is : %s", count)
                cmd = (
                    "select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name NOT LIKE '%TEMP%' and"
                    " tbsp_name NOT LIKE '%TMP%' and tbsp_name NOT LIKE '%TOOL%'")
                self.log.info(cmd)
                result_list = self.exec_tablespace_query(cmd)
                return (result_list, count)

            elif tbl_space_name1 is not None and tbl_space_name2 is not None:
                count = 2
                cmd = ("select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name = '{0}' "
                       "or tbsp_name = '{1}'".format(tbl_space_name1, tbl_space_name2))
                self.log.info(cmd)
                result_list = self.exec_tablespace_query(cmd)
                return (result_list, count)

            elif tbl_space_name1 is not None:
                count = 1
                cmd = "select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name = '{0}'".format(
                    tbl_space_name1)
                self.log.info(cmd)
                result_list = self.exec_tablespace_query(cmd)
                return (result_list, count)

            else:
                count = 1
                cmd = "select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name = '{0}'".format(
                    tbl_space_name2)
                self.log.info(cmd)
                result_list = self.exec_tablespace_query(cmd)
                return (result_list, count)
        except Exception as excp:
            raise Exception("exception in get_tablespaces: {0}".format(excp))


class CSDBOperations:
    """
    CSDB wrapper class to perform feature related DB operations with execute permission
    Inherit this class in your feature helper file and abstract away the DB setup code
    """

    def __init__(self, commcell, db_username: str = None, db_password: str = None, **kwargs) -> None:
        """
        Initialize the DBops class of WebRoutingHelper

        Args:
            commcell    (Commcell)          -   Commcell sdk object for commcell
            db_username (str)               -   username to access db
            db_password (str)               -   password to access db
            kwargs:
                commcell_machine    -   Machine class object of commcell machine
                                        (if db creds needs to be read from registry)
        """
        self.log = logger.get_log()
        sql_instancename = commcell.commserv_hostname.lower()
        driver = defines.unix_driver
        if 'unix' not in commcell.commserv_client.os_info.lower():
            sql_instancename += "\\commvault"
            driver = defines.driver
        self.log.info(f"> getting db object for {sql_instancename}, using {driver}")
        self.log.info(f'creds read -> {db_username}, {db_password}')
        if db_username and db_password:
            self.log.info(f"using given db creds -> {db_username}")
        elif cs_machine := kwargs.get('commcell_machine'):
            self.log.info("using sqladmin_cv accounting by fetching pwd from reg key")
            db_username = 'sqladmin_cv'
            encrypted_password = cs_machine.get_registry_value(r"Database", "pAccess")
            db_password = cvhelper.format_string(commcell, encrypted_password).split("_cv")[1]
        else:
            raise Exception("Cannot get execute level csdb access without DB credentials or Machine registry access!")

        self.log.info("attempting db connectivity")
        self.csdb = MSSQL(
            server=sql_instancename,
            user=db_username,
            password=db_password,
            database='commserv',
            as_dict=False,
            driver=driver
        )
        self.log.info("> db object setup successfully!")
